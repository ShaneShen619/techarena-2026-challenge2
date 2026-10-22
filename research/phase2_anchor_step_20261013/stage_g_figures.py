"""Figures for FINAL_REPORT.md."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT, FIG = os.path.join(HERE, "outputs"), os.path.join(HERE, "figures")

st = pd.read_csv(os.path.join(OUT, "A2_step_programs_all_variants.csv"), parse_dates=["t_cv_end"])
st = st[st["variant"] == "main"]
fc = pd.read_csv(os.path.join(OUT, "A1_full_charges.csv"), parse_dates=["t_end"])
e = pd.read_csv(os.path.join(OUT, "D_errors_per_checkup.csv"))
dates = pd.to_datetime(["2025-02-08", "2025-03-11", "2025-04-14", "2025-05-16", "2025-06-16", "2025-07-25", "2025-08-28"])

fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
for t, mk in ((25, "o"), (45, "s")):
    g = st[st["setpoint_C"] == t]
    ax[0].plot(g["t_cv_end"], g["step_mean"], mk, ms=4, label=f"step depth below CV end, {t} °C")
ax[0].set_ylabel("Ah below CV end"); ax[0].set_title("Graphite step depth on the 5-day program")
ax0b = ax[0].twinx()
ax0b.plot(fc["t_end"], fc["Q_Ah"], "k^-", label="post-checkup full charge Q")
ax0b.set_ylabel("full charge Ah")
for d in dates:
    ax[0].axvline(d, color="0.85", lw=0.8, zorder=0)
ax[0].legend(loc="lower left", fontsize=8); ax0b.legend(loc="upper right", fontsize=8)
ax[0].tick_params(axis="x", rotation=30)

g = e[e["eps_offset"] == 0.4]
proxy = g[g["model"] == "M0_ExampleModel"]["proxy_SOH"].to_numpy()
ax[1].fill_between(dates, proxy - 0.39, proxy + 0.39, color="0.85", label="proxy (eps range)")
ax[1].plot(dates, proxy, "k-", label="proxy, eps0+0.4")
for m, lab in (("M0_ExampleModel", "ExampleModel"), ("M1_B", "B prior"), ("M3", "anchor + sqrt t"),
               ("M4_main_b1.0_last1", "anchor + step (M4)")):
    ax[1].plot(dates, g[g["model"] == m]["pred_SOH"], "o-", ms=4, label=lab)
ax[1].set_ylabel("SOH %"); ax[1].set_title("Causal predictions vs proxy (not hidden truth)")
ax[1].legend(fontsize=8); ax[1].tick_params(axis="x", rotation=30)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "overview.png"), dpi=150)
print("ok")
