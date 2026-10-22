import os, sys
R5C = "/Users/shane/Desktop/Arena_1015_r5c_stressfix/research/phase2_r5c_stress_fix_20261015"
sys.path[:0] = [os.path.join(R5C, "src"), os.path.join(R5C, "stage_1"), os.path.join(R5C, "stage_2")]
from common5c import H
from runner5c import COLD, PSEUDO, run
import run_3
sys.path.insert(0, "/Users/shane/Desktop/Arena_1013_model/research/phase2_v3_20261015/src")
from v3 import v3
import pandas as pd

def v2sqrt(ctx):
    return v3(ctx["fc"], ctx["steps"][ctx["step"]], ctx["a4"][ctx["a4s"]], ctx["ck"], ctx["k"], ctx["eps"],
              use_sqrt=True, beta_cap=float("inf"), median=False)[0]

P = {"V2": run_3.P["V2"], "V2+sqrt (submitted)": v2sqrt, "R3_TD_w0.75 (r5c)": run_3.P["R3_TD_w0.75"]}
df = run(P, ("real",) + PSEUDO + COLD)
df.to_csv("compare_long.csv", index=False)
met = H.metrics(df)
m = met[(met.step == "main") & (met.a4s == 2.0)]
pd.set_option("display.width", 220)
print(m.pivot_table(index=["scenario"], columns=["model", "delta"], values="MAE").round(3).to_string())
r = df[(df.scenario == "real") & (df.step == "main") & (df.a4s == 2.0) & (df.delta == 0.4)]
print(r.pivot_table(index="model", columns="checkup", values="err_pp").round(3).to_string())
