"""WP3 figure: (a) chain terms by event and month, (b) Term2 vs idle hours, (c) Term2 vs E2 jump vs E3 per switch."""
import json, os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import data12 as D

OUT = os.path.join(D.ST, "wp3")
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e0"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"     # categorical slots 1-3 (validated, all pairs)


def style(ax):
    ax.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=9)
    ax.grid(color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def main():
    tm = pd.read_csv(os.path.join(OUT, "terms.csv"))
    e = pd.read_csv(os.path.join(OUT, "e2_e3.csv"))
    T = json.load(open(os.path.join(OUT, "T_top.json")))
    ex = pd.DataFrame(T["exploratory_not_registered"]["rows"]).set_index("pair")
    fig, (ax, bx, cx) = plt.subplots(1, 3, figsize=(15, 5.4), gridspec_kw=dict(width_ratios=[1.25, 0.8, 1.15]))
    fig.patch.set_facecolor(SURFACE)
    # (a) terms by month
    style(ax)
    spec = [("Term3", BLUE, "Term3_k = F^T25 − F^A_k", -0.12), ("Term2", ORANGE, "Term2_j = F^T45 − F^T25", 0.0),
            ("Term1", AQUA, "Term1 = F^A0 − F^T45", 0.12)]
    for name, col, lab, dx in spec:
        d = tm[tm["term"] == name]
        x = d["month"].to_numpy() + dx
        ax.scatter(x, d["value_main"], s=90, color=col, edgecolor=SURFACE, linewidth=1.5, zorder=4, label=lab + " (registered λ)")
        ax.scatter(x, ex.loc[d["pair"], "value"], s=48, facecolor="none", edgecolor=col, linewidth=1.5, zorder=3)
        tp = T["terms"][name]
        ax.hlines(tp["point"], -0.4, 6.6, color=col, lw=1.5, linestyle=(0, (4, 3)), alpha=0.9)
        ax.annotate(f"{name} {tp['point']:+.2f}", (6.65, tp["point"]), fontsize=8.5, color=INK, va="center")
        for xi, (_, r) in zip(x, d.iterrows()):
            if name == "Term3":
                ax.annotate(f"k={int(r['k'])}", (xi, r["value_main"]), xytext=(-4, 6), textcoords="offset points",
                            fontsize=7.5, color=INK2, ha="right")
    ax.scatter([], [], s=48, facecolor="none", edgecolor=INK2, linewidth=1.5, label="○ exploratory time-matched λ (not registered)")
    ax.set_xlim(-0.5, 7.6)
    ax.set_xticks(range(7))
    ax.set_xlabel("month (index of the last checkup before the pair)", color=INK2, fontsize=10)
    ax.set_ylabel("Ah (charge content)", color=INK2, fontsize=10)
    ax.set_title(f"(a) Chain terms by event; dashed: registered medians\nT_top = {T['T_top']['point']:.2f} "
                 f"[{T['T_top']['interval'][0]:.2f}, {T['T_top']['interval'][1]:.2f}] Ah — G_T not identified",
                 loc="left", fontsize=10.5, color=INK)
    ax.legend(loc="upper right", fontsize=8, frameon=False, labelcolor=INK)
    ax.set_ylim(-0.1, 1.05)
    # (b) Term2 vs idle hours
    style(bx)
    t2 = tm[tm["term"] == "Term2"].merge(e[["switch", "idle_h"]], left_on="pair", right_on="switch")
    bx.scatter(t2["idle_h"], t2["value_main"], s=90, color=ORANGE, edgecolor=SURFACE, linewidth=1.5, zorder=3)
    for r in t2.itertuples():
        bx.annotate(f"m{int(r.month)}", (r.idle_h, r.value_main), xytext=(6, 2), textcoords="offset points", fontsize=8, color=INK2)
    d = T["descriptive"]["Term2_vs_idle_h"]
    bx.set_title(f"(b) Term2_j vs chamber-switch idle\nSpearman ρ = {d['spearman_rho']:+.2f}, "
                 f"Theil–Sen {1000 * d['theil_sen_slope_Ah_per_h']:+.0f} mAh/h (n = 5)", loc="left", fontsize=10.5, color=INK)
    bx.set_xlabel("idle hours (25 → 45 °C)", color=INK2, fontsize=10)
    bx.set_ylabel("Term2_j, Ah", color=INK2, fontsize=10)
    bx.set_ylim(0.3, 0.8)
    # (c) Term2 vs J vs Term2_E3
    style(cx)
    x = np.arange(len(e))
    cx.vlines(x - 0.15, e["Term2_lam45"], e["Term2_lam25"], color=ORANGE, lw=1.4, alpha=0.6)
    cx.scatter(x - 0.15, e["Term2"], s=90, color=ORANGE, edgecolor=SURFACE, linewidth=1.5, zorder=3,
               label="Term2_j (λ̄; bar: λ25 … λ45)")
    cx.scatter(x + 0.05, e["J_DL1"], s=56, color=INK, marker="s", zorder=3, label="J_j, DL1 (r45-corrected)")
    cx.scatter(x + 0.2, e["J_A3"], s=56, facecolor="none", edgecolor=INK, marker="s", linewidth=1.5, zorder=3,
               label="J_j, A3 (r45-corrected)")
    g = T["gates"]["G_E2"]
    cx.hlines(g["median_Term2"], -0.5, len(e) - 0.5, color=ORANGE, lw=1.5, linestyle=(0, (4, 3)))
    cx.hlines(g["median_J_dvdq"], -0.5, len(e) - 0.5, color=INK, lw=1.5, linestyle=(0, (4, 3)))
    for xi, r in zip(x, e.itertuples()):
        cx.annotate(f"E3 {r.Term2_E3:.1f}\n[{r.Term2_E3_lo:.0f}, {r.Term2_E3_hi:.1f}]", (xi, 1.32), ha="center",
                    fontsize=7.5, color=INK2)
    cx.set_xticks(x); cx.set_xticklabels([f"{s}\n(m{m})" for s, m in zip(e["switch"], e["month"])], fontsize=8)
    cx.set_ylim(0.0, 1.5)
    cx.set_ylabel("Ah", color=INK2, fontsize=10)
    cx.set_title(f"(c) Term2 vs step jump J; E3 as text (off scale)\nG_E2: |med J_DL1 − med Term2| = "
                 f"{abs(g['diff']):.2f} ≤ 0.20: consistent", loc="left", fontsize=10.5, color=INK)
    cx.legend(loc="lower left", fontsize=8, frameon=False, labelcolor=INK)
    fig.tight_layout()
    p = os.path.join(OUT, "wp3_top.png")
    fig.savefig(p, dpi=150, facecolor=SURFACE)
    print("wrote", p)


if __name__ == "__main__":
    main()
