"""WP2 driver: compute P1, P1b, P2, P3 and the descriptive S_gap with the registered code (signals, ahchain,
stats14), apply the registered statistics, and write wp2/pairs.csv, lambda.csv, term3.csv, p2_voltage.csv,
p3_memory.csv, stats.json and the round 12 cross-check. Calls only registered functions."""
import importlib.util, json, os
import numpy as np
import pandas as pd
import data14 as D
import signals as SG
import stats14 as SS

ST = D.ST
OUT = os.path.join(ST, "wp2")


def jsonable(o):
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def series(t3, col, k_from=1):
    s = t3[(t3["anchor"] >= k_from) & np.isfinite(t3[col])]
    return s["anchor"].astype(int).tolist(), s["fade"].to_numpy(), s["days_since_ck0"].to_numpy(), s[col].to_numpy()


def r12_crosscheck(segs, ev, pairs, ck):
    """Descriptive: N of the shared AT/TT pairs from round 12's registered ahchain.py vs ours (|dN| <= 0.001 Ah)."""
    path = os.path.join(ST, "sources", "r12", "ahchain.py")
    if not os.path.exists(path):
        return None
    spec = importlib.util.spec_from_file_location("r12_ahchain", path)
    r12 = importlib.util.module_from_spec(spec); spec.loader.exec_module(r12)
    e = ev.copy()
    e["event_id"] = [f"S{s:02d}_{o}" for s, o in zip(e["segment"], e["order"])]
    e["type"] = e["kind"]; e["anchor_k"] = e["anchor"]; e["t_cv_end"] = pd.to_datetime(e["t_cv_end"])
    rp = r12.build_pairs(e[["event_id", "segment", "setpoint", "type", "anchor_k", "t_cv_end"]], segs, ck)
    rp = rp[rp["type"].isin(["AT", "TT"])].copy()
    rp["key"] = [f"{a}|{b}" for a, b in zip(rp["t_i"].astype(str), rp["t_j"].astype(str))]
    ours = pairs[pairs["type"].isin(["AT1", "TT"])].copy()
    ours["key"] = [f"{a}|{b}" for a, b in zip(ours["t_i"].astype(str), ours["t_j"].astype(str))]
    m = ours.merge(rp[["key", "type", "N", "thr", "admissible", "reason"]].rename(
        columns={"type": "r12_type", "N": "r12_N", "thr": "r12_thr", "admissible": "r12_admissible",
                 "reason": "r12_reason"}), on="key", how="outer")
    m["dN"] = m["N"] - m["r12_N"]
    m["dthr"] = m["thr"] - m["r12_thr"]
    m["N_agree_0p001"] = np.abs(m["dN"]) <= 0.001
    m["admissible_agree"] = m["gap_free"] == m["r12_admissible"]
    return m[["pair_id", "type", "r12_type", "t_i", "t_j", "N", "r12_N", "dN", "thr", "r12_thr", "dthr",
              "gap_free", "r12_admissible", "r12_reason", "N_agree_0p001", "admissible_agree"]]


def main():
    segs = D.segments()
    ck, names = D.checkup_dates()
    ref = D.load_dataset(D.DATA).reference_discharge
    ev = SG.events(segs)
    ch = SG.chain(segs, ev)
    pairs = ch["pairs"]
    t3 = SG.term3_table(ev, pairs, ck[0])
    st = SG.s_top(ref)
    p2 = SG.p2_table(segs, ev, st)
    p3 = SG.p3_table(segs, ev, t3)
    t3 = t3.merge(p2[["anchor", "P2_pack_Ah", "P2_cellmean_Ah", "dV_pack_mV"]], on="anchor", how="left")

    ev.to_csv(os.path.join(OUT, "events.csv"), index=False)
    pairs.to_csv(os.path.join(OUT, "pairs.csv"), index=False)
    lam = pd.DataFrame([{"segment": s, "setpoint": int(ev.loc[ev["segment"] == s, "setpoint"].iloc[0]),
                         "lambda": v[0], "source": v[1],
                         "n_TT_gap_free": int(((pairs["segment"] == s) & (pairs["type"] == "TT") & pairs["gap_free"]).sum())}
                        for s, v in ch["lambda"].items()])
    lam.to_csv(os.path.join(OUT, "lambda.csv"), index=False)
    t3.to_csv(os.path.join(OUT, "term3.csv"), index=False)
    p2.to_csv(os.path.join(OUT, "p2_voltage.csv"), index=False)
    p3.to_csv(os.path.join(OUT, "p3_memory.csv"), index=False)

    stats = {"sigma_TT": {"reduced": ch["sigma_reduced"], "full": ch["sigma_full"],
                          "sigma_tt25_gate": ch["sigma_tt25_gate"], "sigma_tt45": ch["sigma_tt45"]},
             "s_top_V_per_Ah": st}
    for name, col in [("P1", "term3"), ("P1b", "term3b"), ("P2", "P2_pack_Ah"), ("S_gap", "term3_gap_bridged"),
                      ("P2_cellmean", "P2_cellmean_Ah")]:
        labels, fade, days, y = series(t3, col)
        stats[name] = SS.analyze(labels, fade, days, y)
        stats[name]["values"] = dict(zip(labels, map(float, y)))
    a0 = t3[t3["anchor"] == 0].iloc[0]
    stats["anchor0_45C"] = {"term3": a0["term3"], "lambda": a0["lambda"], "lambda_source": a0["lambda_source"],
                            "P2_pack_Ah": a0["P2_pack_Ah"], "dV_pack_mV": a0["dV_pack_mV"]}
    stats["p1b_identity"] = {int(r["anchor"]): float(r["term3b"] - r["term3"])
                             for _, r in t3.iterrows() if np.isfinite(r["term3b"]) and np.isfinite(r["term3"])}
    # P3 descriptive summaries (k = 1..7)
    q = p3[p3["anchor"] >= 1]
    stats["P3"] = {c: {"median": float(np.nanmedian(q[c])), "min": float(np.nanmin(q[c])), "max": float(np.nanmax(q[c]))}
                   for c in ["o_A3", "o_dvdq", "abs_shift_A3", "abs_shift_dvdq", "abs_shift_A3_gap_bridged",
                             "dCV_Ah_A_minus_T1", "dCV_s_A_minus_T1", "dI_end_A_minus_T1"]}

    src = json.load(open(os.path.join(ST, "cache", "wp2_sources.json")))
    stats["r12_pairs_csv"] = src["files"].get("wp3/pairs.csv")
    cc = r12_crosscheck(segs, ev, pairs, ck)
    if cc is not None:
        cc.to_csv(os.path.join(OUT, "r12_ahchain_crosscheck.csv"), index=False)
        both = cc.dropna(subset=["N", "r12_N"])
        stats["r12_ahchain_crosscheck"] = {"n_shared": len(both), "max_abs_dN": float(np.abs(both["dN"]).max()),
                                           "n_N_agree_0p001": int(both["N_agree_0p001"].sum()),
                                           "n_admissible_agree": int(both["admissible_agree"].sum()),
                                           "only_ours": int(cc["r12_N"].isna().sum()), "only_r12": int(cc["N"].isna().sum())}
    json.dump(jsonable(stats), open(os.path.join(OUT, "stats.json"), "w"), indent=1)
    show = ["anchor", "setpoint", "fade", "AT1_N", "AT1_thr", "lambda", "lambda_source", "term3", "term3b",
            "term3_gap_bridged", "P2_pack_Ah", "P2_cellmean_Ah"]
    print(t3[show].to_string(index=False))
    print(lam.to_string(index=False))
    for k in ("P1", "P1b", "P2", "S_gap", "P2_cellmean"):
        m = stats[k]["main"]
        print(k, {kk: m[kk] for kk in ("n", "estimable", "d", "E", "loo_range_E", "loo_width_E") if kk in m},
              stats[k].get("bic"), stats[k].get("outliers"))
    print(json.dumps(jsonable({k: stats[k] for k in ("sigma_TT", "s_top_V_per_Ah", "anchor0_45C", "p1b_identity",
                                                     "r12_pairs_csv")}), indent=1))
    print(json.dumps(jsonable(stats.get("r12_ahchain_crosscheck")), indent=1))


if __name__ == "__main__":
    main()
