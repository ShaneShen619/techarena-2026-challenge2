"""Create report figures from frozen CSV outputs."""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

TASK = Path(__file__).resolve().parents[1]
OUT = TASK / "outputs"
FIG = OUT / "figures"
FIG.mkdir(exist_ok=True)
plt.rcParams.update({"font.family": "Arial", "font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 160})
navy, teal, orange, gray = "#17324D", "#0A7E8C", "#D97B29", "#B8C2CC"

# Core D1 metrics and targets.
d = pd.read_csv(OUT / "method_comparison.csv")
d = d.loc[(d.route == "R0_recompute") & d.method.isin([
    "within_cell_ratio_ridge", "TCN_finetune", "prefix_temperature_MLP"])].copy()
d["label"] = d.method.map({"within_cell_ratio_ridge": "Simple baseline",
                             "TCN_finetune": "TCN average choice",
                             "prefix_temperature_MLP": "Temperature MLP"})
metrics = [("macro_MAE_pp", "Macro MAE", 1.0), ("worst_cell_MAE_pp", "Worst-cell MAE", 2.0),
           ("max_abs_error_pp", "Maximum error", 5.0)]
fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.2))
for ax, (column, title, target) in zip(axes, metrics):
    values = d[column].to_numpy()
    ax.bar(np.arange(len(d)), values, color=[gray, navy, teal])
    ax.axhline(target, color=orange, linewidth=1.8, linestyle="--", label="Target")
    ax.set_title(title)
    ax.set_xticks(np.arange(len(d)), d.label, rotation=24, ha="right")
    ax.set_ylabel("SOH percentage points")
    for i, value in enumerate(values):
        ax.text(i, value + max(values) * .025, f"{value:.2f}", ha="center", fontsize=9)
axes[0].legend(frameon=False, loc="upper right")
fig.suptitle("D1 v1.5 performance remains above the absolute targets", fontsize=13, color=navy, weight="bold")
fig.tight_layout()
fig.savefig(FIG / "d1_targets.png", bbox_inches="tight")
plt.close(fig)

# R1 paired ablations.
r1 = pd.read_csv(OUT / "r1_condition_comparison.csv")
labels = {"full": "Full", "no_voltage": "No voltage", "meta_only": "Metadata only",
          "no_temperature": "Original no-temp*", "no_temperature_strict": "Strict no-temp",
          "full_tail_weight2": "Tail weight x2"}
r1["label"] = r1.condition.map(labels)
fig, ax = plt.subplots(figsize=(8.2, 3.8))
x = np.arange(len(r1))
ax.bar(x - .18, r1.macro_MAE_pp, width=.36, label="Macro MAE", color=navy)
ax.bar(x + .18, r1.late_macro_MAE_pp, width=.36, label="Late macro MAE", color=orange)
ax.set_xticks(x, r1.label, rotation=18, ha="right")
ax.set_ylabel("SOH percentage points")
ax.set_title("Paired TCN ablations: temperature trades average for tail risk", color=navy, weight="bold")
ax.legend(frameon=False, ncol=2)
fig.tight_layout()
fig.savefig(FIG / "r1_ablations.png", bbox_inches="tight")
plt.close(fig)

# Official-prefix trajectories without hidden truth.
off = pd.read_csv(OUT / "official_prefix_diagnostics.csv")
fig, ax = plt.subplots(figsize=(8.2, 3.8))
for name, color, marker in [("ck0_hold", navy, "o"), ("exploratory_fallback", orange, "s")]:
    q = off.loc[off.candidate == name]
    ax.plot(q.checkup, q.SOH_est_pp, color=color, marker=marker, linewidth=2, label=name)
ax.scatter(["CK0"], [98.441176], color=teal, s=75, zorder=5, label="Only visible capacity truth")
ax.axvspan(0.5, 7.5, color=gray, alpha=.15, label="Hidden CK1–CK7 truth")
ax.set_ylim(70, 101)
ax.set_ylabel("Predicted SOH (%)")
ax.set_title("Official replay is causal, but CK1–CK7 accuracy is unverified", color=navy, weight="bold")
ax.legend(frameon=False, ncol=2, fontsize=9)
fig.tight_layout()
fig.savefig(FIG / "official_prefix.png", bbox_inches="tight")
plt.close(fig)

print(FIG)
