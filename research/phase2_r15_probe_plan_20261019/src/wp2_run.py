"""WP2 driver (not registered code; it only calls the registered src/grid15.py and src/variants.py).

1. checks the registered hashes; 2. rebuilds SUB, EX and the eligible probe(s) through the package CLI and checks
them against round 12 / EXPECTED_SOH; 3. surviving set, delta-s per probe x grid x hypothesis x metric, readability,
ranking and the registered selection; descriptive (ineligible) variants are scored in a separate table.
Run: python3 -B src/wp2_run.py
"""
import hashlib
import json
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import grid15 as G  # noqa: E402
import variants as V  # noqa: E402

ST = G.ST
WT = os.path.abspath(os.path.join(ST, "..", ".."))
OUT = os.path.join(ST, "wp2")
EXPECTED_SUB = {"CK0": 98.441, "CK1": 95.984, "CK2": 94.507, "CK3": 93.600, "CK4": 92.821, "CK5": 92.015,
                "CK6": 91.426, "CK7": 90.765}
ELIGIBLE = ["P_A3fix"]


def check_hashes():
    bad = []
    for line in open(os.path.join(ST, "wp1", "protocol.sha256")):
        h, p = line.split()
        if hashlib.sha256(open(os.path.join(WT, p), "rb").read()).hexdigest() != h:
            bad.append(p)
    assert not bad, f"registered files changed: {bad}"
    return "all registered hashes match"


def r12_row(name):
    r = pd.read_csv(os.path.join(G.SRC, "r12", "wp4_SOH_variants.csv")).set_index("variant").loc[name]
    return {f"CK{k}": float(r[f"CK{k}"]) for k in range(8)}


def descriptive(sub):
    out = {}
    d = -0.031
    out["P_drift_r6"] = {c: round((v * 1.02 + d * max(0.0, G.Q_CK0 - v * 1.02)) / 1.02, 3) for c, v in sub.items()}
    r13 = pd.read_csv(os.path.join(G.SRC, "r13", "wp3_SOH_variants.csv")).set_index("variant")
    r14 = pd.read_csv(os.path.join(G.SRC, "r14", "wp3_SOH_variants.csv")).set_index("variant")
    out["R13_d_tail_median"] = {f"CK{k}": float(r13.loc["SUB + d_median (median over A without C1 = d_tail)", f"CK{k}"])
                                for k in range(8)}
    out["R14_d_top_median"] = {f"CK{k}": float(r14.loc["SUB + d_top (median)", f"CK{k}"]) for k in range(8)}
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    log = {"hashes": check_hashes()}
    # ---- 1. probe vectors through the CLI ----
    sub, _, _ = V.soh("SUB")
    ex, _, ex_init = V.soh("EX")
    a3, a3_diff, _ = V.soh("P_A3fix")
    assert sub == EXPECTED_SUB, sub
    ref = r12_row("SUB_A3fix")
    log["P_A3fix_reproduces_round12"] = a3 == ref
    log["P_A3fix_diff"] = a3_diff
    log["EX_switch_diff"] = ex_init
    eligible = {"P_A3fix": a3} if a3 == ref else {}
    desc = descriptive(sub)
    rows = [dict(variant="SUB", role="submission (base 6525edf)", **sub),
            dict(variant="EX", role="ExampleModel (normaliser)", **ex),
            dict(variant="P_A3fix", role="eligible probe" if eligible else "dropped (rebuild mismatch)", **a3)]
    rows += [dict(variant=k, role="descriptive only (not eligible)", **v) for k, v in desc.items()]
    soh = pd.DataFrame(rows)
    for k in range(1, 8):
        soh[f"dCK{k}_pp"] = (soh[f"CK{k}"] - sub[f"CK{k}"]).round(3)
    soh.to_csv(os.path.join(OUT, "probe_soh.csv"), index=False)
    # ---- 2. scores, delta-s, readability, ranking ----
    models = {"SUB": sub, **eligible, **desc}
    long, rank_rows, surv = [], [], {}
    for g in G.GRIDS:
        sc = G.score_table(models, ex, g)
        hs, note = G.surviving(sc, [], g)        # no observations at WP2 (log has no rows)
        surv[g] = dict(n=len(hs), note=note)
        for p in [m for m in models if m != "SUB"]:
            dt = G.delta_table(sc, p)
            dt.insert(2, "eligible", p in eligible)
            hyp = dt["h"].map({G.hname(h): h for h in G.GRIDS[g]})
            dt["Delta"], dt["f"], dt["d"] = hyp.map(lambda h: h["Delta"]), hyp.map(lambda h: h["f"]), hyp.map(lambda h: h["d"])
            long.append(dt)
            r = G.readability(dt, hs)
            s = G.summary(dt, hs)
            rank_rows.append(dict(probe=p, eligible=p in eligible, grid=g, role=G.GRID_ROLE[g], n_surviving=len(hs),
                                  agree_fraction=r["agree_fraction"], readable=r["readable"],
                                  detectable_fraction=r["detectable_fraction"], **s))
    dl = pd.concat(long, ignore_index=True)
    dl.to_csv(os.path.join(OUT, "delta_s_long.csv"), index=False)
    rk = pd.DataFrame(rank_rows)
    # registered selection (eligible probes only; G_main decides, G_r11 gates)
    sel_rows = []
    for p in models:
        if p == "SUB":
            continue
        m = rk[(rk.probe == p) & (rk.grid == "G_main")].iloc[0]
        r11 = rk[(rk.probe == p) & (rk.grid == "G_r11")].iloc[0]
        sel_rows.append(dict(probe=p, eligible=p in eligible, readable_main=bool(m["readable"]),
                             readable_r11=bool(r11["readable"]), key1_max_E=float(m["key1_max_E"]),
                             key2_max_worst=float(m["key2_max_worst"])))
    chosen = G.choose(sel_rows)
    ranked = [x["probe"] for x in sorted([x for x in sel_rows if x["eligible"]],
                                         key=lambda x: (x["key1_max_E"], x["key2_max_worst"]))]
    rk["rank_among_eligible"] = rk["probe"].map(lambda p: ranked.index(p) + 1 if p in ranked else None)
    rk["chosen"] = rk["probe"].isin(chosen)
    rk.to_csv(os.path.join(OUT, "ranking.csv"), index=False)
    descr_choice = G.choose([dict(r, eligible=True) for r in sel_rows if not r["eligible"]])
    # predicted board scores of every package whose SOH vector is known (lookup for the surviving-set rule, WP4)
    inv = pd.read_csv(os.path.join(ST, "wp0", "existing_packages.csv"))
    known = {f"zip:{r['name']}": {f"CK{k}": float(r[f"CK{k}"]) for k in range(8)} for _, r in inv.iterrows()}
    known.update({"SUB": sub, **eligible})
    pd.concat([G.score_table(known, ex, g) for g in ("G_main", "G_r11")], ignore_index=True).to_csv(
        os.path.join(OUT, "predicted_scores.csv"), index=False)
    out = dict(log, surviving=surv, selection_inputs=sel_rows, chosen=chosen,
               plan="no probe; keep SUB" if not chosen else f"probe(s): {chosen}",
               descriptive_would_qualify_if_eligible=descr_choice,
               SOH={"SUB": sub, "EX": ex, "P_A3fix": a3})
    json.dump(out, open(os.path.join(OUT, "selection.json"), "w"), indent=1, default=str)
    pd.set_option("display.width", 250)
    cols = ["probe", "eligible", "grid", "agree_fraction", "readable", "detectable_fraction", "E_s", "E_nMAE",
            "E_nRMSE", "E_nMAX", "key1_max_E", "key2_max_worst", "wins_all_metrics_beyond_tol"]
    print(soh.to_string())
    print(rk[cols].round(4).to_string())
    print(json.dumps({k: out[k] for k in ("hashes", "P_A3fix_reproduces_round12", "chosen", "plan",
                                           "descriptive_would_qualify_if_eligible")}, indent=1))


if __name__ == "__main__":
    main()
