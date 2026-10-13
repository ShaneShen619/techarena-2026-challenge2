"""Stage D step 1: evaluate D0-D3 on PG1/PG2 (and PC5/PC10) only, then write the selection.

No real-data (CK1-CK7) prediction is computed here.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))
import harness as H  # noqa: E402
import gapx  # noqa: E402

preds = {r: gapx.make(r) for r in gapx.RULES}
df = H.run(preds, scenarios=("PG1", "PG2", "PC5", "PC10"), deltas=(0.4,))
df.to_csv(os.path.join(HERE, "outputs", "D_pseudo_long.csv"), index=False)
pg = df[df["scenario"].isin(["PG1", "PG2"])]
mae = {r: float(pg[pg["model"] == r]["err_pp"].abs().mean()) for r in gapx.RULES}
pc = {s: {r: float(df[(df["scenario"] == s) & (df["model"] == r)]["err_pp"].abs().mean()) for r in gapx.RULES}
      for s in ("PC5", "PC10")}
selectable = ["D0", "D1", "D2"]
best = min(selectable, key=lambda r: mae[r])
chosen = best if (best != "D0" and mae["D0"] - mae[best] >= 0.10) else "D0"
sel = dict(PG_MAE=mae, PC_MAE=pc, best_selectable=best, chosen=chosen,
           rule="lowest PG1+PG2 MAE among D0/D1/D2; must beat D0 by >=0.10 pp")
json.dump(sel, open(os.path.join(HERE, "selection.json"), "w"), indent=1)
print(json.dumps(sel, indent=1))
print(df.pivot_table(index=["scenario", "checkup"], columns="model", values="err_pp").round(3))
print(df[df.model.isin(["D1", "D2", "D3"])].pivot_table(index=["scenario", "checkup"], columns="model",
      values="extrap_Ah").round(3))
