"""Stage 1 evaluation: S1 (Theil-Sen month-end line) and variants vs V2; gates."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))
from common4 import H  # noqa: E402
import endfit as E  # noqa: E402

OUT = os.path.join(HERE, "outputs")
P = {"M4": H.m4_pred, "V2": H.v2_pred, "S1": E.pred,
     "S1_ols": lambda c: E.pred(c, method="ols"), "S1_last3": lambda c: E.pred(c, last3=True),
     "S1_atlast_rate": lambda c: E.pred(c, at_last_plus_rate=True), "S1_beta1": lambda c: E.pred(c, beta_one=True)}
main3 = {n: P[n] for n in ("M4", "V2", "S1")}
df = H.run(P, scenarios=("real", "PG1", "PG2", "PC5", "PC10"))
dv = H.run(main3, scenarios=("real",), variants=H.VARIANTS, deltas=(0.4,))
ds = H.run({"V2": H.v2_pred, "S1": E.pred}, scenarios=("real",), smooths=(1.0, 3.0), deltas=(0.4,))
df = pd.concat([df, dv[dv.step != "main"], ds], ignore_index=True)
df.to_csv(os.path.join(OUT, "S1_long.csv"), index=False)
met = H.metrics(df)
met.to_csv(os.path.join(OUT, "S1_metrics.csv"), index=False)
pck = H.per_ck(df)
g = H.gates_vs_v2(met, pck, "S1", variants_met=met)
# G-pseudo: PG1, PG2 (k=4..7), PC5, PC10 restricted to k>=3
ps = df[(df.scenario.isin(["PG1", "PG2", "PC5", "PC10"])) & (df.k >= 3) & (df.delta == 0.4) & (df.step == "main") & (df.a4s == 2.0)]
pm = ps.groupby(["scenario", "model"])["err_pp"].apply(lambda e: e.abs().mean()).unstack()
g["G-pseudo"] = dict(S1=float(pm["S1"].mean()), V2=float(pm["V2"].mean()),
                     passed=bool(pm["S1"].mean() <= pm["V2"].mean() + 0.02))
sm = met[(met.scenario == "real") & (met.delta == 0.4) & (met.step == "main")].set_index(["model", "a4s"])["MAE"]
g["A4_smoothing_MAE"] = {f"{m}_{a}": float(sm.loc[(m, a)]) for m in ("V2", "S1") for a in (1.0, 2.0, 3.0)}
g["all_common_gates_passed"] = bool(g["G-proxy"] and g["G-epsfree"]["passed"] and g["G-robust"]["passed"]
                                    and g["G-pseudo"]["passed"] and g["G-regress"]["passed"])
json.dump(g, open(os.path.join(OUT, "S1_gates.json"), "w"), indent=1, default=float)
pd.set_option("display.width", 220)
print(pck.round(3))
r = df[(df.scenario == "real") & (df.delta == 0.4) & (df.step == "main") & (df.a4s == 2.0) & (df.model == "S1")]
print(r[["checkup", "s1_branch", "s1_beta", "slope_cur", "slope_prev", "sd_cur", "sd_prev", "n_cur", "err_pp"]].round(4).to_string(index=False))
m = met[(met.step == "main") & (met.a4s == 2.0)]
print(m[m.scenario == "real"].pivot_table(index="model", columns="delta", values=["MAE", "MAX", "CK2_7_MAE"]).round(3))
print(pm.round(3))
print(met[(met.scenario == "real") & (met.delta == 0.4) & (met.a4s == 2.0)].pivot_table(index="step", columns="model", values="MAE").round(3))
print(json.dumps(g, indent=1, default=float))
