"""WP2 figure: LIC terms vs fade. Usage: python3 -B wp2_fig.py <study_dir>"""
import os, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
ST = sys.argv[1]
d = pd.read_csv(os.path.join(ST, "wp2/lic_terms.csv"))
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
for term, mk in [("T_CE", "o"), ("T_path", "s"), ("eps_total", "^")]:
    ax[0].plot(d.fade, d[term], mk + "-", label=term, ms=5)
f = d[d.flag]
ax[0].plot(f.fade, f.T_path, "kx", ms=9, label="flagged (MAD / audit)")
ax[0].axvline(0.5 * (d.fade[4] + d.fade[5]), color="grey", ls=":", lw=1)
ax[0].set_xlabel("fade (Ah, LIC 280 Ah)"); ax[0].set_ylabel("Ah"); ax[0].legend(fontsize=8); ax[0].set_title("LIC: eps = T_CE + T_path")
o = d[d.op_ch_Ah.notna()]
ax[1].plot(o.op_ch_CV_Ah, o.T_path, "s")
for _, r in o.iterrows():
    ax[1].annotate(str(int(r.k)), (r.op_ch_CV_Ah, r.T_path), fontsize=7)
ax[1].set_xlabel("CV Ah of the first 1C operating charge"); ax[1].set_ylabel("T_path (Ah)"); ax[1].set_title("T_path vs the top-state driver")
fig.tight_layout(); fig.savefig(os.path.join(ST, "wp2/lic_terms.png"), dpi=130)
