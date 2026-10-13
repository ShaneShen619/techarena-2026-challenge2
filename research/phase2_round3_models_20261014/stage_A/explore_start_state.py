"""Stage A exploratory (NOT pre-registered): start state of the anchor charges.

Converts each anchor's per-cell start rest voltage into 'Ah above the empty end'
with the CK0 C/20 loaded tail (an upper-bound conversion, see V1 report), and compares
it with the registration bottom-section change and with Q_fc residuals."""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))
import harness as H  # noqa: E402
from events import CELLS  # noqa: E402
from framework.data import load_reference_discharge  # noqa: E402

ref = load_reference_discharge(H.DATA)
d = ref["discharged_Ah"].to_numpy(float)
q_end = d.max()


def tail_ah(v0, c):
    v = ref[c].to_numpy(float)
    below = np.where(v <= v0)[0]
    return q_end - d[below[0]] if len(below) else 0.0


fc = H.full_charges(H.full_op()).sort_values("t_end").reset_index(drop=True)
rows = []
for j, r in fc.iterrows():
    tails = [tail_ah(r[f"start_{c}"], c) for c in CELLS]
    rows.append(dict(anchor=j, segment=int(r["segment"]), setpoint=int(r["setpoint_C"]), Q_fc=r["Q_Ah"],
                     pack_start_V=r["pack_start_V"], start_cell_mean_V=np.mean([r[f"start_{c}"] for c in CELLS]),
                     tail_Ah_mean=float(np.mean(tails)), tail_Ah_min=float(np.min(tails)),
                     tail_Ah_max=float(np.max(tails)), rest_h=r["rest_before_h"]))
t = pd.DataFrame(rows)
split = pd.read_csv(os.path.join(HERE, "outputs", "A_split.csv"))
t = t.merge(split[["anchor", "dbottom"]], on="anchor", how="left")
a25 = t[t.setpoint == 25].copy()
# residual of Q_fc around a sqrt(t) trend over the 25 C anchors (descriptive)
days = (fc.loc[a25.index, "t_end"] - H.CK[0]).dt.total_seconds().to_numpy() / 86400
coef = np.polyfit(np.sqrt(days), a25["Q_fc"], 1)
a25["Qfc_resid_sqrt"] = a25["Q_fc"] - np.polyval(coef, np.sqrt(days))
a25["tail_rel_Ah"] = a25["tail_Ah_mean"] - a25["tail_Ah_mean"].mean()
pd.set_option("display.width", 200)
print(a25.round(3).to_string(index=False))
print("corr(tail_rel, Qfc_resid) =", round(np.corrcoef(a25.tail_rel_Ah, a25.Qfc_resid_sqrt)[0, 1], 3))
s = a25.dropna(subset=["dbottom"])
print("corr(start_cell_mean_V, dbottom) =", round(np.corrcoef(s.start_cell_mean_V, s.dbottom)[0, 1], 3))
print("slope Qfc_resid on tail_rel:", np.round(np.polyfit(a25.tail_rel_Ah, a25.Qfc_resid_sqrt, 1), 3))
a25.to_csv(os.path.join(HERE, "outputs", "A_start_state_exploratory.csv"), index=False)
