"""WP4: the single real run (after WP3 is committed). Real numbers are exposed and never select."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
from designs17 import predictors  # noqa: E402
from eval17 import H, run  # noqa: E402

OUT = os.path.join(HERE, "outputs")
os.makedirs(OUT, exist_ok=True)

P = predictors(names=["B0", "S", "C", "O1", "O2", "D"], with_ens=True, sens=False)
df = run(P, scenarios=("real",), variants=H.VARIANTS, smooths=(2.0,))
sub = pd.read_csv(os.path.join(STUDY, "sources", "r10_wp1_predictions.csv"))
sub = sub[(sub["model"] == "A3") & (sub["scenario"] == "real") & (sub["step"] == "main")].assign(model="SUB")
df = pd.concat([df, sub[df.columns.intersection(sub.columns)]], ignore_index=True)
df.to_csv(os.path.join(OUT, "real_predictions.csv"), index=False)

main = df[(df["step"] == "main") & (df["a4s"] == 2.0)]
met = H.metrics(df)
models = [m for m in df["model"].unique()]
rows = {}
for m in models:
    r = {}
    for d in (0.0, 0.4, 0.8):
        e = main[(main["model"] == m) & (main["delta"] == d)].set_index("k")["err_pp"].sort_index()
        r[f"MAE_{d}"] = float(e.abs().mean())
        r[f"MAX_{d}"] = float(e.abs().max())
        if d == 0.4:
            r["ck"] = e.round(4).to_dict()
            r["MAE_noCK1"] = float(e.drop(1).abs().mean())
            r["MAE_noCK2"] = float(e.drop(2).abs().mean())
            r["MAE_noCK12"] = float(e.drop([1, 2]).abs().mean())
            soh = main[(main["model"] == m) & (main["delta"] == d)].set_index("k")["SOH"].sort_index()
            ssub = main[(main["model"] == "SUB") & (main["delta"] == d)].set_index("k")["SOH"].sort_index()
            r["level_vs_SUB_CK1_7"] = float((soh - ssub).mean())
            r["level_vs_SUB_CK2_7"] = float((soh - ssub).drop(1).mean())
    rows[m] = r

# exposed-CK labels: share of the real MAE gain over REF (delta 0.4) coming from CK1 / CK2
ref_ck = pd.Series(rows["REF"]["ck"])
for m, r in rows.items():
    if m in ("REF", "SUB", "V2"):
        continue
    ck = pd.Series(r["ck"])
    gain = ref_ck.abs() - ck.abs()        # positive = better than REF
    tot = gain.sum()
    lab = []
    if tot > 0:
        for kk in (1, 2):
            if gain.loc[kk] / tot >= 0.5:
                lab.append(f"exposed-CK{kk}")
    r["real_gain_vs_REF_sum_pp"] = float(tot)
    r["labels"] = lab

# r5c real gates vs V2 (information only); SUB has only the main variant, so no G-robust for it
pck = H.per_ck(df[df["model"] != "SUB"])
gates = {}
for m in models:
    if m in ("V2", "SUB"):
        continue
    gates[m] = H.gates_vs_v2(met, pck, m, variants_met=met)
res = dict(models=rows, gates=gates,
           leaderboard_readings="truth about 1 pp below SUB, or CK2-7 about +0.65 pp above SUB (2026-10-20 note)")
json.dump(res, open(os.path.join(OUT, "real.json"), "w"), indent=1, default=float)
order = ["SUB", "V2", "R3_T", "REF", "B0", "S", "C", "O1", "O2", "D",
         "B0_ens", "S_ens", "C_ens", "O1_ens", "O2_ens", "D_ens"]
tab = pd.DataFrame({m: {k: v for k, v in rows[m].items() if k not in ("ck", "labels")} for m in order}).T
print(tab.round(4).to_string())
print(pd.DataFrame({m: rows[m]["ck"] for m in order}).T.round(3).to_string())
for m in order:
    if m in gates:
        g = gates[m]
        print(m, "G-proxy", g["G-proxy"], "G-epsfree", g["G-epsfree"]["passed"], "G-robust", g["G-robust"],
              "G-regress", round(g["G-regress"]["max_abs_err_increase_pp"], 3), g["G-regress"]["passed"], rows[m].get("labels"))
