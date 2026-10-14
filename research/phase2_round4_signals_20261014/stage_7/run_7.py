"""Stage 7 evaluation: SS_fixed and V2_startcorr vs V2; gates."""
import json
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))
from common4 import H  # noqa: E402
import leads as L  # noqa: E402

OUT = os.path.join(HERE, "outputs")
P = {"M4": H.m4_pred, "V2": H.v2_pred, "SS_fixed": L.ss_fixed,
     "SS_fixed_tau5": lambda c: L.ss_fixed(c, tau=5.0), "SS_fixed_tau3": lambda c: L.ss_fixed(c, tau=3.0),
     "V2_startcorr": L.v2_startcorr, "V2_startcorr_noshrink": lambda c: L.v2_startcorr(c, tau=0.0)}
mains = {n: P[n] for n in ("M4", "V2", "SS_fixed", "V2_startcorr")}
df = H.run(P, scenarios=("real", "PG1", "PG2", "PC5", "PC10"))
dv = H.run(mains, scenarios=("real",), variants=H.VARIANTS, deltas=(0.4,))
df = pd.concat([df, dv[dv.step != "main"]], ignore_index=True)
df.to_csv(os.path.join(OUT, "S7_long.csv"), index=False)
met = H.metrics(df)
met.to_csv(os.path.join(OUT, "S7_metrics.csv"), index=False)
pck = H.per_ck(df)
ps = df[(df.scenario.isin(["PG1", "PG2", "PC5", "PC10"])) & (df.k >= 3) & (df.delta == 0.4) & (df.step == "main")]
pm = ps.groupby(["scenario", "model"])["err_pp"].apply(lambda e: e.abs().mean()).unstack()
gates = {}
for name in ("SS_fixed", "V2_startcorr"):
    g = H.gates_vs_v2(met, pck, name, variants_met=met)
    g["G-pseudo"] = dict(model=float(pm[name].mean()), V2=float(pm["V2"].mean()), passed=bool(pm[name].mean() <= pm["V2"].mean() + 0.02))
    g["all_common_gates_passed"] = bool(g["G-proxy"] and g["G-epsfree"]["passed"] and g["G-robust"]["passed"]
                                        and g["G-pseudo"]["passed"] and g["G-regress"]["passed"])
    gates[name] = g
json.dump(gates, open(os.path.join(OUT, "S7_gates.json"), "w"), indent=1, default=float)
pd.set_option("display.width", 220)
print(pck.round(3))
m = met[(met.step == "main") & (met.scenario == "real")]
print(m.pivot_table(index="model", columns="delta", values=["MAE", "MAX", "CK2_7_MAE"]).round(3))
print(pm.round(3))
print(met[(met.scenario == "real") & (met.delta == 0.4)].pivot_table(index="step", columns="model", values="MAE").round(3))
r = df[(df.scenario == "real") & (df.delta == 0.4) & (df.step == "main") & (df.model.isin(["SS_fixed", "V2_startcorr"]))]
print(r[["model", "checkup", "o_fit", "beta_sc", "c", "err_pp"]].round(3).to_string(index=False))
print(json.dumps(gates, indent=1, default=float))
