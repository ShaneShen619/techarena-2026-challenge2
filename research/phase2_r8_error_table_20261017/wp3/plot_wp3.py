"""WP3 descriptive figure: anchor quantities against anchor index (no case errors)."""
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
from plotstyle import INK2, SP_COLOR, SP_MARKER, setup  # noqa: E402

plt = setup()
t = pd.read_csv(os.path.join(STUDY, "outputs", "table_anchors.csv"))
panels = [("Q_fc", "Q_fc (Ah)"), ("dQ_fc_next", "ΔQ_fc to next anchor (Ah)"), ("cv_Ah", "CV charge (Ah)"),
          ("dQ_cut6A", "Q_fc(6 A cut) − Q_fc (Ah)"), ("r_upper", "start residual r_upper (Ah)"),
          ("R_mean_mOhm", "pulse R, cell mean (mΩ)"), ("step_to_top_spread_Ah", "step→top spread over cells (Ah)"),
          ("cv_end_spread_V", "cell spread at CV end (V)")]
fig, axs = plt.subplots(2, 4, figsize=(12, 5.4))
for ax, (c, lab) in zip(axs.flat, panels):
    ax.plot(t["anchor"], t[c], color=INK2, linewidth=1.0, zorder=1)
    for sp in (45, 25):
        s = t[t["setpoint"] == sp]
        ax.scatter(s["anchor"], s[c], color=SP_COLOR[sp], marker=SP_MARKER[sp], s=40, zorder=2,
                   edgecolor="#fcfcfb", linewidth=1.5, label=f"{sp} °C anchor")
    ax.set_title(lab)
    ax.set_xticks(range(8))
    ax.set_xlabel("anchor j (after CK_j)")
axs.flat[0].legend(loc="upper right")
fig.suptitle("Anchor table (descriptive; anchor 0 is the 45 °C campaign-start charge)")
fig.tight_layout()
os.makedirs(os.path.join(HERE, "figures"), exist_ok=True)
fig.savefig(os.path.join(HERE, "figures", "wp3_anchor_overview.png"))
