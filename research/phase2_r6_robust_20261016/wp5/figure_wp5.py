"""WP5 interpretability figure: break-in / calendar / cycle decomposition of the two-term stress law (S_A, prior2),
fitted at the CK7 cutoff, plus the SOH it implies against the anchors (exposed proxies) and SUB.
Palette: dataviz reference categorical slots 1-3 (validated; slot 3 needs direct labels -> provided)."""
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
from common6 import H  # noqa: E402
from smodel import anchors  # noqa: E402
from smodel5c import LawFit, load_prior2  # noqa: E402
from stress import cumulative, stress_table  # noqa: E402

OUT = os.path.join(STUDY, "report_material")
os.makedirs(OUT, exist_ok=True)
C_BREAK, C_CAL, C_CYC = "#2a78d6", "#eb6834", "#1baf7a"
SURFACE, INK, MUTED, GRID = "#fcfcfb", "#1f1f1e", "#6b6a64", "#e4e3de"

GAP = dict(law="two", steps=True, steps_mode="gap_endpoint", beta_mode="one", sigma_s=0.10)
op7 = H.cut_op(7)
fc7 = H.full_charges(op7)
st7 = H.step_programs(op7)
q7, info = LawFit(GAP).run(op7, fc7, H.CK, H.CK[7], H.EPS0 + 0.4, steps=st7)
p2 = load_prior2()
A_b, A_cal, A_cyc = np.exp(info["logA_b"]), np.exp(info["logA_cal"]), np.exp(info["logA_cyc"])
tau_b = np.exp(p2["logtau_b"][0])
full = H.full_op()
tab = stress_table(full, full["timestamp"].max(), H.CK)
anc = anchors(H.full_charges(full), H.CK)
t0 = anc[0][0]
grid = pd.date_range(t0, tab["t1"].max(), freq="6h")
tau, ah = cumulative(tab, 37.3e3, t_eval=grid)
tau, ah = tau - tau[0], ah - ah[0]
L_b = A_b * (1 - np.exp(-tau / tau_b))
L_c = A_cal * np.sqrt(tau)
L_y = A_cyc * ah
soh_law = (H.Q_CK0 - (L_b + L_c + L_y)) / H.NOM * 100

sub = pd.read_csv(os.path.join(STUDY, "wp0", "outputs", "wp0_example_and_submitted_class.csv"))
proxy = [(anc[j][0], (anc[j][1] + H.EPS0 + 0.4) / H.NOM * 100) for j in range(1, 8)]

plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED, "text.color": INK, "font.family": "DejaVu Sans"})
fig, ax = plt.subplots(2, 1, figsize=(10, 7.4), sharex=True, gridspec_kw={"height_ratios": [1, 1.1]},
                       facecolor=SURFACE)
for a in ax:
    a.set_facecolor(SURFACE)
    a.grid(axis="y", color=GRID, lw=0.8)
    a.spines[["top", "right"]].set_visible(False)
    for c in H.CK[1:]:
        a.axvline(c, color=GRID, lw=0.8, zorder=0)
a = ax[0]
a.stackplot(grid, L_b, L_c, L_y, colors=[C_BREAK, C_CAL, C_CYC], edgecolor=SURFACE, linewidth=2)
xe = grid[-1] + pd.Timedelta(days=3)
ys = np.cumsum([L_b[-1], L_c[-1], L_y[-1]])
for y0, y1, lab, val in zip([0, ys[0], ys[1]], ys, ["break-in", "calendar (√t)", "cycle"], [L_b[-1], L_c[-1], L_y[-1]]):
    a.text(xe, (y0 + y1) / 2, f"{lab}  {val:.2f} Ah", va="center", fontsize=9, color=INK)
a.set_ylabel("cumulative loss since anchor 0 (Ah)")
a.set_title("Two-term stress law fitted at the CK7 cutoff: what the loss is made of", loc="left", fontsize=11)
a = ax[1]
a.plot(grid, soh_law, color=C_BREAK, lw=2, label="stress law from CK0 (no re-anchoring)")
a.plot([p[0] for p in proxy], [p[1] for p in proxy], "o", ms=8, color=INK, mec=SURFACE, mew=2,
       label="anchor proxy (exposed, Δ = 0.4)")
a.plot(H.CK[1:], sub["SOH_submitted_class"].iloc[1:], "s", ms=8, color=C_CAL, mec=SURFACE, mew=2,
       label="submitted model SUB at checkup dates")
a.plot([t0], [H.Q_CK0 / H.NOM * 100], "D", ms=8, color=MUTED, mec=SURFACE, mew=2, label="CK0 label (released)")
a.set_ylabel("SOH (% of 102 Ah)")
a.legend(frameon=False, fontsize=9, loc="upper right")
for c, n in zip(H.CK[1:], H.CK_NAMES[1:]):
    a.text(c, a.get_ylim()[0] + 0.05, n, fontsize=8, color=MUTED, ha="center", va="bottom")
fig.autofmt_xdate()
fig.tight_layout()
fig.subplots_adjust(right=0.82)
fig.savefig(os.path.join(OUT, "fig_stress_law_decomposition.png"), dpi=150, facecolor=SURFACE)
tbl = pd.DataFrame({"component": ["break-in A_b(1-exp(-tau/tau_b))", "calendar A_cal*sqrt(tau)", "cycle A_cyc*ah"],
                    "parameter": [f"A_b={A_b:.3f} Ah, tau_b={tau_b:.0f} eff. d", f"A_cal={A_cal:.4f} Ah/d^0.5",
                                  f"A_cyc={A_cyc:.2e} per Ah"],
                    "loss_to_campaign_end_Ah": [L_b[-1], L_c[-1], L_y[-1]]})
tbl.to_csv(os.path.join(OUT, "fig_stress_law_decomposition_table.csv"), index=False)
json.dump(dict(fit_info={k: (float(v) if isinstance(v, (int, float, np.floating)) else v) for k, v in info.items()},
               tau_b=float(tau_b)), open(os.path.join(OUT, "fig_stress_law_params.json"), "w"), indent=1)
print(tbl.to_string())
