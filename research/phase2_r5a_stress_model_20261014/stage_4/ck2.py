"""Stage 4: CK2 analysis (descriptive, exposed). Nothing here is tuned."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
from common5a import H  # noqa: E402
from smodel import MAIN, StressFit, anchors  # noqa: E402
from stress import cumulative, horizon_lag_days, stress_table  # noqa: E402

OUT = os.path.join(HERE, "outputs")
os.makedirs(OUT, exist_ok=True)
CK = H.CK
k = 2
delta = 0.4
eps = H.EPS0 + delta

op = H.cut_op(k)
fc = H.full_charges(op)
q, info = StressFit().run(op, fc, CK, CK[k], eps)
anc = anchors(fc, CK)
t1 = anc[1][0]
L = horizon_lag_days(fc, CK, CK[k])
hz = CK[k] + pd.Timedelta(days=L)
tab = stress_table(op, CK[k], CK, horizon=hz)
Ea = MAIN["Ea_kJ"] * 1e3


def loss_between(tab, ta, tb, A_cal, A_cyc, z=MAIN["z"]):
    tau, ah = cumulative(tab, Ea, t_eval=[ta, tb])
    return A_cal * (tau[1] ** z - tau[0] ** z) + A_cyc * (ah[1] - ah[0]), tau, ah


A_cal, A_cyc = info["A_cal"], info["A_cyc"]
t_seg2_end = op["timestamp"].max()
ext = tab[tab["kind"] == "extrapolated"]
t_ext_end = ext["t1"].max() if len(ext) else t_seg2_end
parts = {}
for name, (a, b) in {"segment 2 observed (anchor 1 -> seg 2 end)": (t1, t_seg2_end),
                     "segment 3 extrapolated (seg 2 end -> est. month end)": (t_seg2_end, t_ext_end),
                     "checkup interval (est. month end -> horizon)": (t_ext_end, hz)}.items():
    l, tau, ah = loss_between(tab, a, b, A_cal, A_cyc)
    parts[name] = dict(t0=str(a), t1=str(b), loss_Ah=float(l), d_tau_eff=float(tau[1] - tau[0]),
                       d_ah_eff=float(ah[1] - ah[0]))

# what segment 3 really contained (visible only after CK2; measures the extrapolation rule only)
full = H.full_op()
tab_full = stress_table(full, full["timestamp"].max(), CK)
seg3 = tab_full[tab_full["kind"] == "seg_gap"]
true_seg3 = dict(t0=str(seg3["t0"].min()), t1=str(seg3["t1"].max()), days=float(seg3["days"].sum()),
                 Ah=float(seg3["thr_Ah"].sum()))
ext_seg3 = dict(t0=str(ext["t0"].min()), t1=str(ext["t1"].max()), days=float(ext["days"].sum()),
                Ah=float(ext["thr_Ah"].sum()))
# same fitted parameters, stress of the true interval [anchor 1, horizon] from the full table
l_true, tau_t, ah_t = loss_between(tab_full, t1, hz, A_cal, A_cyc)
l_pred = sum(p["loss_Ah"] for p in parts.values())

pred = pd.read_csv(os.path.join(STUDY, "stage_3", "outputs", "S3_per_checkup_d04.csv"), index_col=0)
row = pred.loc["CK2"]
table = {"S_main": row["S_main"], "S z = 1 (G4)": row["G4_z1"], "S z free (G1)": row["G1_zfree"],
         "S z = 0.5 (report only)": row["X_z05"], "S prior only": row["X_prior_only"], "V2": row["V2"],
         "D1 (round 3)": -1.427, "D2 (round 3)": -1.049}
out = dict(ck2_errors_pp_delta04=table, S_main_prediction_Ah=q, fitted=dict(A_cal=A_cal, A_cyc=A_cyc, o45=info["o45"]),
           horizon=str(hz), loss_decomposition=parts, predicted_month_loss_Ah=l_pred,
           segment3_extrapolated=ext_seg3, segment3_true=true_seg3,
           loss_with_true_stress_same_params_Ah=float(l_true),
           extrapolation_effect_on_prediction_pp=float((l_true - l_pred) / H.NOM * 100),
           note="Exposed, single point. The true segment-3 stress is used only to measure the extrapolation rule.")
json.dump(out, open(os.path.join(OUT, "S4_ck2.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
