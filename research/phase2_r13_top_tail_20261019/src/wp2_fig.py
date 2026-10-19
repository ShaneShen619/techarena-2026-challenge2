"""WP2 figures from wp2/*.csv and cache/traces.npz (written by run_wp2.py). Usage: python3 -B wp2_fig.py <study_dir>"""
import os, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tail  # noqa: E402

ST = sys.argv[1]
W2 = os.path.join(ST, "wp2")
INK, INK2, MUTED, GRID, AXIS, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
SER = {"M4": "#2a78d6", "M2": "#eb6834", "M1": "#6250d6", "M3": "#1baf7a"}
RAMP = ["#86b6ef", "#2a78d6", "#104281"]          # blue ordinal ramp (validated)
plt.rcParams.update({"font.family": "sans-serif", "font.size": 9, "axes.edgecolor": AXIS, "axes.labelcolor": INK2,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.spines.top": False,
                     "axes.spines.right": False, "legend.frameon": False, "text.color": INK})

fits = pd.read_csv(os.path.join(W2, "fits.csv"))
tails = pd.read_csv(os.path.join(W2, "tails.csv"))
pairs = pd.read_csv(os.path.join(W2, "pairs.csv"))
ts = pd.read_csv(os.path.join(W2, "top_state.csv"))
tsl = pd.read_csv(os.path.join(W2, "top_state_slopes.csv"))
tr = np.load(os.path.join(ST, "cache", "traces.npz"))
fa = fits[fits.type == "A"].copy(); fa["anchor"] = fa.anchor.astype(float).astype(int)


def params(r):
    return [float(getattr(r, n)) for n in tail.PARAM_NAMES[r.model]]


# ---- Figure 1: CV current of every anchor with each admitted model's fit (solid) and extrapolation (dashed)
fig, axs = plt.subplots(2, 4, figsize=(13, 6.2), sharex=True, sharey=True)
XMAX = 2400.0
for ax, k in zip(axs.flat, range(8)):
    ev = fa[fa.anchor == k].event_id.iloc[0]
    t, I = tr[f"{ev}_t"], tr[f"{ev}_I"]
    for lvl, lab in ((5.1, "5.1 A (anchor end)"), (2.55, "C2 2.55 A"), (1.02, "C3 1.02 A"), (0.51, "C4 0.51 A")):
        ax.axhline(lvl, color=AXIS, lw=0.8, ls=":", zorder=1)
        if k == 0:
            ax.text(XMAX * 0.98, lvl * 1.06, lab, ha="right", va="bottom", fontsize=7, color=MUTED)
    ax.axvline(t[-1], color=AXIS, lw=0.8, zorder=1)
    ax.scatter(t, I, s=14, color=AXIS, zorder=2, label="observed CV current", linewidths=0)
    for r in fa[(fa.anchor == k) & fa.admitted].itertuples():
        p = params(r)
        tw = np.linspace(0, t[-1], 200); te = np.linspace(t[-1], XMAX, 300)
        ax.plot(tw, tail.current(r.model, p, tw), color=SER[r.model], lw=1.6, zorder=5, label=f"{r.model} fit (admitted)")
        ax.plot(te, tail.current(r.model, p, te), color=SER[r.model], lw=2, ls="--", zorder=3, label=f"{r.model} extrapolation")
    na = ",".join(fa[(fa.anchor == k) & ~fa.admitted].model)
    ax.set_title(f"anchor {k}" + (" (45 °C, excluded)" if k == 0 else "") + f"\nnot admitted: {na or '–'}",
                 fontsize=8.5, color=INK, loc="left")
    ax.set_yscale("log"); ax.set_ylim(0.3, 25); ax.set_xlim(0, XMAX)
for ax in axs[1]:
    ax.set_xlabel("time from CV start (s)")
for ax in axs[:, 0]:
    ax.set_ylabel("current (A, log)")
h, l = [], []
for ax in axs.flat:
    for hh, ll in zip(*ax.get_legend_handles_labels()):
        if ll not in l:
            h.append(hh); l.append(ll)
fig.legend(h, l, loc="lower center", ncol=5, fontsize=8)
fig.suptitle("Anchor CV current with each admitted tail model: fit over the CV window (solid), extrapolation beyond the 5.1 A end (dashed)",
             fontsize=10, color=INK, x=0.01, ha="left")
fig.tight_layout(rect=(0, 0.05, 1, 0.96))
fig.savefig(os.path.join(W2, "fig_cv_fits.png"), dpi=150); plt.close(fig)

# ---- Figure 2: Delta_tail(k) (M4, all scenarios) and -dF^A_V(k) (T2) against fade
a = tails[(tails.type == "A") & tails.anchor.notna()].copy(); a["anchor"] = a.anchor.astype(float).astype(int)
a = a[a.anchor.between(1, 7)]
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.6), sharey=True)
sty = {"C2": (RAMP[0], "-"), "C3": (RAMP[1], "-"), "C4": (RAMP[2], "-"), "C5": (RAMP[0], "--"), "C6": (RAMP[1], "--"), "C7": (RAMP[2], "--")}
desc = {"C2": "cutoff 2.55 A", "C3": "cutoff 1.02 A", "C4": "cutoff 0.51 A", "C5": "hold 30 min", "C6": "hold 60 min", "C7": "hold 120 min"}
for c, (col, ls) in sty.items():
    g = a[(a.model == "M4") & (a.scenario == c)].sort_values("fade_Ah")
    e = pairs[(pairs.model == "M4") & (pairs.scenario == c)].effect_CK7_Ah.iloc[0]
    ax1.plot(g.fade_Ah, g.Delta_tail_Ah, color=col, ls=ls, lw=2, marker="o", ms=4,
             label=f"M4 {c} ({desc[c]}): d·8.2 = {e:+.3f} Ah")
ax1.axhline(0, color=AXIS, lw=1)
ax1.set_title("Tail drift Δ_tail(k), M4 (the only model admitted on anchors 1–7)", fontsize=9.5, loc="left")
ax1.set_xlabel("fade_k = Q_fc,1 − Q_fc,k (Ah)"); ax1.set_ylabel("Δε contribution (Ah), relative to anchor 1")
ax1.legend(fontsize=7.5, loc="upper left", bbox_to_anchor=(0, -0.14), ncol=2)

t2 = ts[(ts.estimator == "T2") & (ts.unit == "pack")]
t3 = ts[ts.estimator == "T3"]
eff = lambda est, unit, win: tsl[(tsl.estimator == est) & (tsl.unit == unit) & (tsl.window == win)].iloc[0]
m4c4 = a[(a.model == "M4") & (a.scenario == "C4")].sort_values("fade_Ah")
series = [
    (t2[t2.window == "main"].sort_values("fade_Ah"), "#eb6834", "-", "o",
     f"T2 −ΔF_V, pack, s_top [0.5, 2.0] Ah (member of A): d·8.2 = {eff('T2', 'pack', 'main').effect_CK7_Ah:+.3f} Ah"),
    (t2[t2.window == "w025_1"].sort_values("fade_Ah"), "#eb6834", ":", "s",
     f"T2 −ΔF_V, pack, s_top [0.25, 1.0] Ah (sensitivity): d·8.2 = {eff('T2', 'pack', 'w025_1').effect_CK7_Ah:+.3f} Ah"),
    (t3.sort_values("fade_Ah"), "#6250d6", "-", "^", f"T3 resistance (check only): d·8.2 = {eff('T3', 'pack', 'main').effect_CK7_Ah:+.3f} Ah"),
]
for g, col, ls, mk, lab in series:
    ax2.plot(g.fade_Ah, g.d_eps_Ah, color=col, ls=ls, lw=2, marker=mk, ms=4, label=lab)
e4 = pairs[(pairs.model == "M4") & (pairs.scenario == "C4")].effect_CK7_Ah.iloc[0]
ax2.plot(m4c4.fade_Ah, m4c4.Delta_tail_Ah, color=RAMP[2], lw=2, marker="o", ms=4, label=f"M4 C4 for reference: d·8.2 = {e4:+.3f} Ah")
ax2.axhline(0, color=AXIS, lw=1)
ax2.set_title("Top-state estimators: −ΔF^A_V(k) (T2) and T3, against fade", fontsize=9.5, loc="left")
ax2.set_xlabel("fade_k = Q_fc,1 − Q_fc,k (Ah)")
ax2.legend(fontsize=7.5, loc="upper left", bbox_to_anchor=(0, -0.14))
fig.tight_layout()
fig.savefig(os.path.join(W2, "fig_drift_vs_fade.png"), dpi=150); plt.close(fig)

# ---- Figure 3 (supporting): residuals of all four models for anchors 1 and 7
fig, axs = plt.subplots(1, 2, figsize=(11, 3.6), sharey=True)
for ax, k in zip(axs, (1, 7)):
    ev = fa[fa.anchor == k].event_id.iloc[0]
    t, I = tr[f"{ev}_t"], tr[f"{ev}_I"]
    ax.axhspan(-0.10, 0.10, color=GRID, alpha=0.6, lw=0, zorder=0)
    ax.axvline(2 * t[-1] / 3, color=AXIS, lw=0.8, ls=":")
    for r in fa[fa.anchor == k].itertuples():
        res = tail.current(r.model, params(r), t) - I
        ax.plot(t, res, color=SER[r.model], lw=2 if r.admitted else 1.2, ls="-" if r.admitted else "--",
                label=f"{r.model} RMSE {r.rmse:.3f} A, last third {r.last_third_mean_resid:+.3f} A" + (" (admitted)" if r.admitted else ""))
    ax.axhline(0, color=AXIS, lw=1)
    ax.set_title(f"anchor {k}: residual I_model − I_obs (band ±0.10 A; dotted line = start of last third)", fontsize=8.5, loc="left")
    ax.set_xlabel("time from CV start (s)"); ax.legend(fontsize=7, loc="lower right")
axs[0].set_ylabel("residual (A)")
fig.tight_layout()
fig.savefig(os.path.join(W2, "fig_residuals_anchor1_7.png"), dpi=150); plt.close(fig)
print("figures written")
