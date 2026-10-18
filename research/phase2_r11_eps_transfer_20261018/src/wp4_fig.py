"""WP4 figure. Usage: python3 -B wp4_fig.py <study_dir>"""
import os, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
ST = sys.argv[1]
p = pd.read_csv(os.path.join(ST, "wp4/pack_drivers.csv")); m = p[p.anchor >= 1]
l = pd.read_csv(os.path.join(ST, "wp2/lic_terms.csv")); l = l[l.op_ch_Ah.notna()]
fig, ax = plt.subplots(2, 3, figsize=(13, 6.5))
for a, (pc, lc, lab) in zip(ax.T, [("CV_Ah", "op_ch_CV_Ah", "CV Ah"), ("I_end", "op_ch_I_end", "end current (A)"),
                                    ("V_pack_30min", "op_ch_V_after_rest", "relaxed top voltage (V)")]):
    a[0].plot(m.anchor, m[pc], "o-"); a[0].set_title(f"pack anchors 1-7: {lab}", fontsize=9); a[0].set_xlabel("anchor")
    a[1].plot(l.k, l[lc], "s-", color="C1"); a[1].set_title(f"LIC first 1C charge: {lab}", fontsize=9); a[1].set_xlabel("RPT k")
fig.tight_layout(); fig.savefig(os.path.join(ST, "wp4/pack_vs_lic_drivers.png"), dpi=130)
