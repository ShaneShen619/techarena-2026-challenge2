"""Stage C: evaluate the state-space fusion model and its variants; gates."""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))
import harness as H  # noqa: E402
import statespace as S  # noqa: E402

OUT = os.path.join(HERE, "outputs")
preds = {"M4": H.m4_pred, "V2": H.v2_pred,
         "SS": S.make(),
         "SS_tau3": S.make(tau=3.0), "SS_tau8": S.make(tau=8.0),
         "SS_beta1": S.make(beta=1.0),
         "SS_rw01": S.make(rw=0.01), "SS_rw04": S.make(rw=0.04)}
main_only = {n: f for n, f in preds.items() if n in ("M4", "V2", "SS")}
df = H.run(preds, scenarios=("real", "PG1", "PG2", "PC5", "PC10"))
dv = H.run(main_only, scenarios=("real",), variants=H.VARIANTS, deltas=(0.4,))
dv = dv[dv["step"] != "main"]
import pandas as pd  # noqa: E402
df = pd.concat([df, dv], ignore_index=True)
df.to_csv(os.path.join(OUT, "C_long.csv"), index=False)
met = H.metrics(df)
met.to_csv(os.path.join(OUT, "C_metrics.csv"), index=False)
pck = H.per_ck(df)
g = H.gates_vs_v2(met, pck, "SS", variants_met=met)
r = df[(df.scenario == "real") & (df.delta == 0.4) & (df.step == "main") & (df.model == "SS")]
z = (r["err_pp"] / (r["pred_sd"] / H.NOM * 100)).to_numpy()
g["calibration_descriptive"] = dict(mean_abs_z=float(np.mean(np.abs(z))), frac_within_2sd=float(np.mean(np.abs(z) <= 2)))
json.dump(g, open(os.path.join(OUT, "C_gates.json"), "w"), indent=1, default=float)
pd.set_option("display.width", 220)
print(r[["checkup", "err_pp", "pred_sd", "beta", "delta_fit", "A_last", "r25_last", "r45_last"]].round(3).to_string(index=False))
print(pck.round(3))
m = met[(met.step == "main") & (met.delta == 0.4)]
print(m.pivot_table(index="model", columns="scenario", values="MAE").round(3))
print(met[(met.scenario == "real") & (met.step == "main")].pivot_table(index="model", columns="delta", values=["MAE", "MAX", "CK2_7_MAE"]).round(3))
print(met[(met.scenario == "real") & (met.delta == 0.4)].pivot_table(index="step", columns="model", values="MAE").round(3))
for s in ("PG1", "PG2", "PC5", "PC10"):
    print(s, H.per_ck(df, scenario=s)[["M4", "V2", "SS"]].round(3).to_dict())
print(json.dumps(g, indent=1, default=float))
