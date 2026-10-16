"""WP3: pooling, registered recommendation, SUB + drift SOH tables and grid scores (protocol.json).
Run eps_yagci.py first (python3 -I -B)."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
sys.path.insert(0, os.path.join(STUDY, "sources", "v3"))
sys.path.insert(0, os.path.join(STUDY, "wp1"))
from common6 import H  # noqa: E402
import grid7 as G  # noqa: E402
from run_wp1 import ov_targets  # noqa: E402

OUT = os.path.join(HERE, "outputs")
EXT = {"LIC": -0.035, "Gotion": -0.031}

if __name__ == "__main__":
    byc = json.load(open(os.path.join(OUT, "wp3_yagci_d_by_cell.json")))
    grp = {}
    for T in (35, 50):
        ds = [v["eps_main"]["d"] for v in byc.values() if v["T_C"] == T]
        grp[f"Yagci{T}"] = float(np.mean(ds))
    pool = {**EXT, **grp}
    vals = np.array(list(pool.values()))
    loo = {k: float(np.median([v for kk, v in pool.items() if kk != k])) for k in pool}
    y = [grp["Yagci35"], grp["Yagci50"]]
    if all(-0.05 <= v <= -0.015 for v in y):
        rec, d_rec = "keep_minus_0p031", -0.031
    elif all(-0.015 < v < 0.01 for v in y):
        rec, d_rec = "recommend_minus_0p020", -0.020
    elif any(v > 0.01 for v in y):
        rec, d_rec = "sign_not_robust", -0.031   # d unchanged (round-6 value); probe ordering changes
    else:
        rec, d_rec = "mixed", float(np.clip(np.median(vals), -0.035, -0.015))
    # SOH tables and grid
    p6 = pd.read_csv(os.path.join(G.R6, "wp1", "outputs", "wp1_predictions.csv"))
    p6 = p6[(p6.scenario == "real") & (p6.step == "main") & (p6.a4s == 2.0)][["scenario", "k", "model", "Q"]]
    sub = p6[p6.model == "SUB"]
    add = []
    for d in sorted({-0.031, -0.020, d_rec, round(float(np.median(vals)), 4)}):
        x = sub.copy()
        x["Q"] = x["Q"] + d * np.maximum(0.0, 100.41 - x["Q"])
        x["model"] = f"SUB+drift{d}"
        add.append(x)
    pred = pd.concat([p6] + add, ignore_index=True)
    soh = pred[pred.model.str.startswith("SUB")].assign(SOH=lambda t: t["Q"] / H.NOM * 100,
                                                       checkup=lambda t: [H.CK_NAMES[k] for k in t["k"]])
    soh_t = soh.pivot_table(index="model", columns="checkup", values="SOH")
    soh_t.round(3).to_csv(os.path.join(OUT, "wp3_SUB_drift_SOH.csv"))
    tab = pd.read_csv(os.path.join(STUDY, "wp1", "outputs", "anchor_state_table.csv"))
    ovt, _ = ov_targets(tab, "median")
    tg = {**G.targets6(), **ovt}
    sc = G.scores(pred, tg)
    cand = [m for m in sc.model.unique() if m != "EX"]
    s = sc.pivot_table(index="h", columns="model", values="s")[cand]
    t_all, _ = G.decision(s)
    t6, _ = G.decision(s.loc[list(G.targets6())], G.round6_weights(list(G.targets6())))
    dec = t_all.join(t6, rsuffix="_r6grid").sort_values("max_regret")
    dec.to_csv(os.path.join(OUT, "wp3_grid_decision.csv"))
    out = dict(groups=grp, pooled=pool, pooled_median=float(np.median(vals)), pooled_range=[float(vals.min()), float(vals.max())],
               leave_one_dataset_out_median=loo, recommendation=rec, d_recommended=d_rec,
               note="35 C group positive mainly through checkup 0 (initial RPT vs first operating charge, eps0 -1.9 / -3.5 Ah)",
               SUB_drift_rows=[m for m in soh_t.index])
    json.dump(out, open(os.path.join(OUT, "wp3_pooling.json"), "w"), indent=1)
    # figure
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    e = pd.read_csv(os.path.join(OUT, "wp3_yagci_eps.csv"))
    fig, ax = plt.subplots(figsize=(6.5, 4.3))
    for c, g in e.groupby("cell"):
        ax.plot(g["L"], g["eps_main"], "o-", label=f"{c} ({int(g['T_C'].iloc[0])} C), d={byc[c]['eps_main']['d']:+.3f}")
    xs = np.linspace(0, 21, 10)
    for k, v in EXT.items():
        ax.plot(xs, v * xs, "--", lw=1, label=f"{k} slope {v}")
    ax.set_xlabel("fade L (Ah, 102 Ah scale)")
    ax.set_ylabel("eps = C_RPT - first operating charge (Ah, 102 Ah scale)")
    ax.legend(fontsize=7)
    ax.set_title("WP3: eps drift on Yagci cycling cells")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "wp3_eps_vs_fade.png"), dpi=130)
    pd.set_option("display.width", 220)
    print(json.dumps(out, indent=1))
    print(soh_t.round(3).to_string())
    print(dec.round(4).to_string())
