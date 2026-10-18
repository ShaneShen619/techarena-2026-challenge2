"""WP3 figure. Usage: python3 -B wp3_fig.py <study_dir>"""
import os, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
ST = sys.argv[1]
y = pd.read_csv(os.path.join(ST, "wp3/yagci_terms.csv")); g = pd.read_csv(os.path.join(ST, "wp3/gotion_terms.csv"))
fig, ax = plt.subplots(1, 3, figsize=(13, 4))
for i, term in enumerate(("T_CE", "T_path")):
    for c, d in y.groupby("cell"):
        ax[i].plot(d.L, d[term], "o-", label=f"{c[-2:]} ({int(d.T_C.iloc[0])} C)")
    ax[i].set_title(f"Yagci {term} (102 Ah scale; point at L=0 is the formation checkup)"); ax[i].set_xlabel("fade L (Ah)"); ax[i].legend(fontsize=7)
ax[2].plot(g.fade, g.eps_total, "s-"); ax[2].set_title("Gotion cell eps_total (0.1 Ah calibration)"); ax[2].set_xlabel("fade (Ah, 53 Ah cell)")
for a in ax: a.set_ylabel("Ah"); a.title.set_fontsize(8)
fig.tight_layout(); fig.savefig(os.path.join(ST, "wp3/ext_terms.png"), dpi=130)
