"""WP3 driver: apply the registered rules (decide.py) to the WP2 statistics, combine with round 13 if available,
build wp3/SOH_variants.csv with the copied round 11 drift.py (leaderboard-only, never scored), and write
wp3/decision.json and wp3/R14_RESULT.json. Calls only registered functions."""
import hashlib, importlib.util, json, os
import numpy as np
import pandas as pd
import data14 as D
import decide as DC
import stats14 as SS
from wp2_measure import jsonable

ST = D.ST
W2, W3 = os.path.join(ST, "wp2"), os.path.join(ST, "wp3")


def load_drift():
    spec = importlib.util.spec_from_file_location("drift", os.path.join(ST, "sources", "r11", "drift.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def main():
    stats = json.load(open(os.path.join(W2, "stats.json")))
    p1, p1b, p2 = stats["P1"], stats["P1b"], stats["P2"]
    dec = DC.decide(stats["sigma_TT"]["sigma_tt25_gate"], p1, p1b)
    m = p1["main"]
    d_path, d_lo, d_hi = m["d"], m["loo_range_d"][0], m["loo_range_d"][1]

    # round 13 combination (reported; decides nothing)
    r13p = os.path.join(ST, "sources", "r13", "R13_RESULT.json")
    top = None
    if os.path.exists(r13p):
        r13 = json.load(open(r13p))
        dt = r13["d_tail"]
        tail_med, tail_rng = dt["median_without_C1"], [dt["min_over_A"], dt["max_over_A"]]
        top = DC.combine_top(d_path, [d_lo, d_hi], tail_med, tail_rng)
        top.update({"d_tail_median": tail_med, "d_tail_range": tail_rng, "r13_outcome": f"{r13['outcome']} {r13['label']}",
                    "r13_mapping": "median = d_tail.median_without_C1 (round 13's own candidate rule); range = "
                                   "[d_tail.min_over_A, d_tail.max_over_A]",
                    "r13_sha256": hashlib.sha256(open(r13p, "rb").read()).hexdigest()})

    # SOH variants (leaderboard-only)
    drift = load_drift()
    sub = pd.read_csv(os.path.join(ST, "wp0", "SUB_SOH.csv"))
    cks = sub["checkup"].tolist()
    var = [("SUB", 0.0), ("SUB + d_path (median)", d_path), ("SUB + d_path (LOO low)", d_lo),
           ("SUB + d_path (LOO high)", d_hi)]
    if top is not None:
        var += [("SUB + d_top (median)", top["d_top"]), ("SUB + d_top (low)", top["d_top_range"][0]),
                ("SUB + d_top (high)", top["d_top_range"][1])]
    rows = []
    for name, d in var:
        s = drift.add_drift(sub["SOH_est"].to_numpy(), d)
        rows.append({"variant": name, "d_Ah_per_Ah": round(d, 6), **{c: round(float(v), 3) for c, v in zip(cks, s)},
                     "CK7_minus_SUB_pp": round(float(s[-1] - sub["SOH_est"].iloc[-1]), 3)})
    sv = pd.DataFrame(rows)
    sv.to_csv(os.path.join(W3, "SOH_variants.csv"), index=False)

    # per-anchor table
    t3 = pd.read_csv(os.path.join(W2, "term3.csv"))
    p3 = pd.read_csv(os.path.join(W2, "p3_memory.csv"))
    sc = pd.read_csv(os.path.join(W2, "explore_same_cycle_term3.csv"))
    per = t3[["anchor", "segment", "setpoint", "Q_fc", "fade", "days_since_ck0", "lambda", "lambda_source", "term3",
              "term3_excluded", "term3b", "term3_gap_bridged", "dV_pack_mV", "P2_pack_Ah"]].merge(
        p3[["anchor", "o_A3", "o_dvdq", "abs_shift_A3", "dCV_Ah_A_minus_T1", "dCV_s_A_minus_T1", "dI_end_A_minus_T1"]],
        on="anchor", how="left").merge(sc[["anchor", "lambda_same_cycle_45C", "term3_same_cycle"]], on="anchor", how="left")
    per = per.rename(columns={"lambda_same_cycle_45C": "EXPLORATORY_lambda_same_cycle_45C",
                              "term3_same_cycle": "EXPLORATORY_term3_same_cycle"})
    per.to_csv(os.path.join(W3, "per_anchor.csv"), index=False)

    ex = json.load(open(os.path.join(W2, "explore.json")))
    lo2, hi2 = p2["main"]["loo_range_E"]; lo1, hi1 = m["loo_range_E"]
    result = {
        "round": 14, "source": "exp/phase2-r14-path-drift-20261019", "protocol_commit": "46f3c26",
        "protocol_sha256": open(os.path.join(ST, "wp1", "protocol.sha256")).read().split()[0],
        "outcome": dec["outcome"].split(" ")[0] if dec["outcome"].startswith("O") else dec["outcome"],
        "label": dec["outcome"], "reason": dec["reason"], "checks": dec["checks"],
        "d_path": {"median": d_path, "loo_range": [d_lo, d_hi], "E_CK7_Ah": m["E"], "E_loo_range_Ah": m["loo_range_E"],
                   "E_loo_width_Ah": m["loo_width_E"], "n": m["n"], "anchors": p1["labels"],
                   "loo_by_dropped_anchor": m["loo"], "days_slope_Ah_per_day": p1["days"]["d"],
                   "days_slope_loo_range": p1["days"]["loo_range_d"], "excluded": {"3": "recording gaps in A->T1",
                                                                                 "7": "recording gap in A->T1"}},
        "bic": p1["bic"], "outliers": p1["outliers"],
        "noise": stats["sigma_TT"],
        "P1b": {"estimable": False, "n": p1b["main"]["n"], "anchors": p1b["labels"],
                "term3b_minus_term3": stats["p1b_identity"],
                "agreement": "not estimable (2 points); where it exists Term3' = Term3 exactly (single TT pair per segment)"},
        "P2": {"d": p2["main"]["d"], "E_CK7_Ah": p2["main"]["E"], "E_loo_range_Ah": p2["main"]["loo_range_E"],
               "bic": p2["bic"], "s_top_V_per_Ah": stats["s_top_V_per_Ah"],
               "agreement_with_P1": {"same_sign": bool(np.sign(p2["main"]["E"]) == np.sign(m["E"])),
                                     "loo_ranges_overlap": bool(max(lo1, lo2) <= min(hi1, hi2)),
                                     "median_E_difference_Ah": m["E"] - p2["main"]["E"]},
               "per_cell_dV_trend_mV_per_Ah_fade": {k: v["theil_sen_mV_per_Ah_fade"] for k, v in ex["p2_per_cell"].items()},
               "note": "P2 in Ah is 2.5-15x the Ah-chain level (s_top dominated by cell 3): sign and trend only"},
        "S_gap_descriptive": {"d": stats["S_gap"]["main"]["d"], "E_CK7_Ah": stats["S_gap"]["main"]["E"],
                              "E_loo_range_Ah": stats["S_gap"]["main"]["loo_range_E"], "n": stats["S_gap"]["main"]["n"]},
        "anchor0_45C": stats["anchor0_45C"],
        "d_top": top if top is not None else "not available",
        "EXPLORATORY_not_registered": {
            "finding": "lambda (TT N/thr) is stable within a segment but steps between checkup cycles (45 C: -0.94, "
                       "-1.42, -1.44, -1.69, -2.49, -2.82 e-3); the only 25 C TT pairs (Jul/Aug) sit on the same track, so "
                       "the pooled 25 C lambda over-corrects anchors 2-4 by +0.29..+0.39 Ah. This produces the registered "
                       "P1 trend.",
            "same_cycle_lambda_term3": ex["same_cycle_fits"]["same_cycle_gap_free"]["values"],
            "same_cycle_d_gap_free_4pts": ex["same_cycle_fits"]["same_cycle_gap_free"]["theil_sen_d"],
            "same_cycle_E_gap_free_4pts": ex["same_cycle_fits"]["same_cycle_gap_free"]["E"],
            "same_cycle_d_incl_gap_bridged_5pts": ex["same_cycle_fits"]["same_cycle_incl_gap_bridged"]["theil_sen_d"],
            "same_cycle_E_incl_gap_bridged_5pts": ex["same_cycle_fits"]["same_cycle_incl_gap_bridged"]["E"],
            "same_cycle_transfer_error_Ah_per_block": [t["difference_Ah_per_block"] for t in ex["same_cycle_transfer_check"]],
            "lambda_segments": ex["lambda_segments"]},
        "per_anchor": per.to_dict(orient="records"),
        "soh_variants": sv.to_dict(orient="records"),
        "recommendation": "SUB unchanged. No candidate (outcome O3). The registered d_path (E = -0.97 Ah at CK7) is not "
                          "identifiable (LOO width 0.59 Ah) and is explained by a month-specific Ah-chain lambda, not by the "
                          "pack's tops; the lambda-free voltage check P2 gives -0.28 Ah from cell 3 alone, and a same-cycle "
                          "lambda (exploratory) gives no trend (-0.11..+0.04 Ah). Do not use SUB + d_path or SUB + d_top.",
        "for_round_15": ["any Ah-chain term must use a lambda from the same checkup cycle (lambda steps up to 0.8e-3, "
                         "about 0.3 Ah per block, between cycles); round 12's Term3 with the pooled 25 C lambda has the same "
                         "exposure",
                         "register a same-cycle lambda rule (45 C segment of the same cycle; 25 C transfer error -0.03/+0.18 "
                         "Ah per block) before re-estimating d_path; anchors 1 and 7 have no same-cycle 45 C segment",
                         "the pack-native path drift is then at most a few tenths of an Ah at CK7; combined with round 13's "
                         "tail bound [0, +0.41] Ah the open variable stays the checkup's CV termination and charge rate"],
        "no_proxy_statement": "No rule or output used P_k or any proxy error.",
    }
    json.dump(jsonable(dec), open(os.path.join(W3, "decision.json"), "w"), indent=1)
    json.dump(jsonable(result), open(os.path.join(W3, "R14_RESULT.json"), "w"), indent=1, default=str)
    print(json.dumps(jsonable(dec), indent=1))
    print(json.dumps(jsonable(top), indent=1))
    print(sv.to_string(index=False))


if __name__ == "__main__":
    main()
