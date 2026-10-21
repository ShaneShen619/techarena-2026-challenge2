"""WP2 step 2: paired causal check for the designs that moved in the screen (causal scenarios only)."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
from designs17 import predictors  # noqa: E402
from eval17 import CAUSAL, H, noninferior_rule, paired, pass_rule, run  # noqa: E402

OUT = os.path.join(HERE, "outputs")
NOISE = json.load(open(os.path.join(STUDY, "wp0", "outputs", "noise.json")))
DELTA = NOISE["delta"]
scr = pd.read_csv(os.path.join(OUT, "screen_summary.csv"))
moving = scr[scr["moves"]]["model"].tolist()
main_moving = [m for m in moving if m in ("B0", "S", "C", "O1", "O2", "D")]
sens_moving = [m for m in moving if m not in main_moving]

P = predictors(names=moving, with_ens=True, sens=True)
assert "real" not in CAUSAL
df = run(P, scenarios=CAUSAL, variants=("main",), smooths=(2.0,))
sub = pd.read_csv(os.path.join(STUDY, "sources", "r10_wp1_predictions.csv"))
sub = sub[(sub["model"] == "A3") & (sub["step"] == "main") & sub["scenario"].isin(CAUSAL)].assign(model="SUB")
df = pd.concat([df, sub[df.columns.intersection(sub.columns)]], ignore_index=True)
df.to_csv(os.path.join(OUT, "paired_predictions.csv"), index=False)


def strip(st):
    return {k: v for k, v in st.items() if k != "cases"}


res = {"delta_pp": DELTA, "main_moving": main_moving, "sens_moving": sens_moving, "designs": {}}
for m in main_moving + sens_moving:
    st = {d: paired(df, m, "R3_T", delta=d) for d in (0.0, 0.4, 0.8)}
    sq = {d: paired(df, m + "_ens", "REF", delta=d) for d in (0.0, 0.4, 0.8)}
    if m == "D":
        ok, crit = noninferior_rule(st[0.4], DELTA)
    else:
        ok, crit = pass_rule(st[0.4], sq[0.4], st[0.0], st[0.8], DELTA)
    s04 = df[(df["delta"] == 0.4)]
    perk = s04[s04["model"].isin([m, "R3_T", "V2", "SUB"])].pivot_table(index="k", columns="model", values="err_pp",
                                                                       aggfunc="mean")
    # demeaned error correlation (rule 6): remove the per-(scenario, k) mean over {R3_T, V2, SUB, X}
    w = s04[s04["model"].isin([m, "R3_T", "V2", "SUB"])].pivot_table(index=["scenario", "k"], columns="model",
                                                                    values="err_pp")
    dm = w.sub(w.mean(axis=1), axis=0)
    res["designs"][m] = dict(
        role="main" if m in main_moving else "sensitivity (report only)",
        p={str(d): strip(v) for d, v in st.items()}, q={str(d): strip(v) for d, v in sq.items()},
        passes=bool(ok) if m in main_moving else None, criteria={k: bool(v) for k, v in crit.items()},
        per_k_signed=perk.round(4).to_dict(orient="index"),
        demeaned_corr_vs_V2=float(dm[m].corr(dm["V2"])), raw_corr_vs_V2=float(w[m].corr(w["V2"])),
        scen_mae=s04[s04["model"].isin([m, m + "_ens", "R3_T", "REF", "V2", "SUB"])]
        .groupby(["model", "scenario"])["err_pp"].apply(lambda e: float(e.abs().mean())).unstack().round(4)
        .to_dict(orient="index"))
    st[0.4]["cases"].to_csv(os.path.join(OUT, f"paired_p_{m}.csv"), index=False)
json.dump(res, open(os.path.join(OUT, "paired.json"), "w"), indent=1)
for m, r in res["designs"].items():
    print(m, r["role"], "passes", r["passes"], r["criteria"])
    for d in ("0.0", "0.4", "0.8"):
        p, q = r["p"][d], r["q"][d]
        print(f"  d={d} p mean {p['mean']:+.4f} neg {p['share_neg']:.2f} blocks {dict((k, round(v, 3)) for k, v in p['block_means'].items())} "
              f"maxLOKO {p['max_loko']:+.4f} worst {p['worst']:+.3f} | q mean {q['mean']:+.4f}")
    print("  per-k", r["per_k_signed"], "corr dm", round(r["demeaned_corr_vs_V2"], 3))
