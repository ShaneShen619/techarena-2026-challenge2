"""Stage 5: ageing-law figure (CK7-cutoff parameters) and the leaderboard-only SOH table."""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
from common5a import H  # noqa: E402
from smodel import MAIN, StressFit, anchors  # noqa: E402
from stress import cumulative, stress_table  # noqa: E402

OUT = os.path.join(HERE, "outputs")
os.makedirs(OUT, exist_ok=True)
CK = H.CK

# parameters fitted at the CK7 cutoff (anchors 0..6), Delta 0.4
op7 = H.cut_op(7)
q7, info = StressFit().run(op7, H.full_charges(op7), CK, CK[7], H.EPS0 + 0.4)
full = H.full_op()
tab = stress_table(full, full["timestamp"].max(), CK)
anc = anchors(H.full_charges(full), CK)
t0 = anc[0][0]
grid = pd.date_range(t0, tab["t1"].max(), freq="6h")
tau, ah = cumulative(tab, MAIN["Ea_kJ"] * 1e3, t_eval=grid)
Lcal = info["A_cal"] * np.power(tau, MAIN["z"])
Lcyc = info["A_cyc"] * ah
i0 = 0
M = Lcal + Lcyc
Q_model = H.Q_CK0 - (M - M[i0])

fig, ax = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
a = ax[0]
a.plot(grid, Q_model / H.NOM * 100, color="C3", lw=1.6, label="S law from CK0 (CK7-cutoff parameters)")
pj = [(anc[j][0], (anc[j][1] + H.EPS0 + 0.4) / H.NOM * 100) for j in range(1, 8)]
a.plot([p[0] for p in pj], [p[1] for p in pj], "ko", ms=5, label="proxy at anchors 1-7 (exposed, Δ = 0.4)")
a.plot([t0], [H.Q_CK0 / H.NOM * 100], "ks", ms=6, mfc="w", label="CK0 label at anchor 0")
for c in CK:
    a.axvline(c, color="0.85", lw=0.8, zorder=0)
a.set_ylabel("SOH (% of 102 Ah)")
a.legend(fontsize=8)
a.set_title("Stress-history ageing law (illustration; parameters fitted at the CK7 cutoff)", fontsize=10)
b = ax[1]
b.stackplot(grid, Lcal - Lcal[i0], Lcyc - Lcyc[i0], labels=["calendar term A_cal·τ_eff^z", "cycle term A_cyc·ah_eff"],
            colors=["C0", "C1"], alpha=0.7)
for c in CK:
    b.axvline(c, color="0.85", lw=0.8, zorder=0)
b.set_ylabel("cumulative loss since anchor 0 (Ah)")
b.legend(fontsize=8, loc="upper left")
fig.autofmt_xdate()
fig.tight_layout()
fig.savefig(os.path.join(OUT, "S5_ageing_law.png"), dpi=120)

# leaderboard-only table (Delta 0.4, main step, A4 2 Ah)
df = pd.read_csv(os.path.join(STUDY, "stage_3", "outputs", "S3_real_predictions.csv"))
s = df[(df["scenario"] == "real") & (df["delta"] == 0.4) & (df["step"] == "main") & (df["a4s"] == 2.0) &
       df["model"].isin(["S_main", "ENS50", "V2"])]
lb = s.pivot_table(index="checkup", columns="model", values="SOH").round(3)
lb.to_csv(os.path.join(OUT, "S5_leaderboard_only_SOH.csv"))
json.dump(dict(ck7_cut_params=info), open(os.path.join(OUT, "S5_figure_params.json"), "w"), indent=1)
print(lb.to_string())
print(info)
