"""Figure: Challenge 1 relative loss vs days with the joint fit (stage 2 diagnostic)."""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from fit_prior import CELLS, NOM, model_L, prepare  # noqa: E402

pr = json.load(open(os.path.join(HERE, "prior.json")))
th = [pr["c1_joint"][k] for k in ("logA_cal", "logA_cyc", "z", "Ea_kJ")]
fig, ax = plt.subplots(2, 3, figsize=(12, 6.5), sharey=True)
for a, c in zip(ax.ravel(), CELLS):
    s = prepare(c)
    d = (s["t0"] - s["t0"].iloc[0]).dt.total_seconds() / 86400
    a.plot(d, NOM * (1 - s["r"]), ".", ms=1, color="0.6", label="measured")
    a.plot(d, model_L(th, s), "-", color="C3", lw=1.5, label="joint fit")
    a.set_title(c.replace("102Ah_", ""), fontsize=9)
    a.set_xlabel("days")
a = ax[0, 0]
a.set_ylabel("loss (Ah on 102 Ah)")
ax[1, 0].set_ylabel("loss (Ah on 102 Ah)")
a.legend(fontsize=8)
fig.tight_layout()
os.makedirs(os.path.join(HERE, "outputs"), exist_ok=True)
fig.savefig(os.path.join(HERE, "outputs", "S2_c1_joint_fit.png"), dpi=120)
