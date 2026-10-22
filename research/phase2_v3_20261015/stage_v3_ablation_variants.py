"""Supplement (after main evaluation): each change on all six step-detection variants, delta 0.4."""
import os
import pandas as pd
import stage_v3_eval as E

E.ALL_VARIANTS = ("V2", "V3", "V2+1", "V2+2", "V2+3", "V2+1+3")
pred = E.predictions(models=list(E.ALL_VARIANTS))
data = os.path.join(E.ROOT, "data")
qfc = E.full_charges(E.load_dataset(data).operation).sort_values("t_end")["Q_Ah"].to_numpy()
pred["proxy_Q"] = [qfc[k] + 100.41 - qfc[0] + de for k, de in zip(pred["k"], pred["eps_offset"])]
pred["err_pp"] = (pred["Q"] - pred["proxy_Q"]) / E.NOM * 100
met = E.metrics(pred)
met.to_csv(os.path.join(E.OUT, "V3_ablation_by_variant.csv"), index=False)
m = met[(met["eps_offset"] == 0.4) & (met["a4s"] == 2.0)]
pd.set_option("display.width", 200)
for col in ("MAE", "CK3_7_MAE", "MAX"):
    print(col); print(m.pivot_table(index="model", columns="step", values=col).round(3).to_string())
