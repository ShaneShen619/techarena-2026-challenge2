"""WP2 figure: (a) Q_bot trend of the relaxed anchors with the anomalies, (b) CK0 vs anchor-0 step positions."""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import data12 as D

OUT = os.path.join(D.ST, "wp2")
SURFACE, INK, INK2, GRID, BAND = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e0", "#efeee9"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"     # categorical slots 1-3 (validated, all pairs)
CL = ["CL1", "CL2", "CL3", "CL4", "CL5"]
DL = ["DL1", "DL2", "DL3", "DL4", "DL5"]


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
    b2 = json.load(open(os.path.join(OUT, "b2_results.json")))
    b3 = json.load(open(os.path.join(OUT, "ck0_split.json")))
    g = json.load(open(os.path.join(OUT, "gates.json")))
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(13, 5.2), gridspec_kw=dict(width_ratios=[1.25, 1]))
    fig.patch.set_facecolor(SURFACE)
    # (a) trend
    style(ax)
    t = {int(k): v for k, v in b2["t_days"].items()}
    q = {int(k): v for k, v in b2["Q_bot"].items()}
    per = {int(k): v for k, v in b2["per_locator"].items()}
    slope, icpt = b2["trend"]["slope_Ah_per_day"], b2["trend"]["intercept_Ah"]
    thr = g["G_SB"]["threshold"]
    xx = np.linspace(0, 240, 50)
    ax.fill_between(xx, icpt + slope * xx - thr, icpt + slope * xx + thr, color=BAND, lw=0,
                    label=f"trend ± max(2σ_LOO, 0.15) = ±{thr:.2f} Ah")
    ax.plot(xx, icpt + slope * xx, color=INK2, lw=2, label=f"Theil–Sen trend, relaxed anchors ({slope * 30:+.2f} Ah/month)")
    for k in sorted(q):
        col = AQUA if k == 0 else (ORANGE if k == 3 else BLUE)
        vals = [per[k][n] for n in CL if per[k][n] is not None and np.isfinite(per[k][n])]
        ax.plot([t[k], t[k]], [min(vals), max(vals)], color=col, lw=1.2, alpha=0.55, solid_capstyle="round")
        lab = {0: "anchor 0 (45 °C, unrelaxed)", 3: "anchor 3 (unrelaxed start)", 1: "relaxed 25 °C anchors"}.get(k)
        ax.scatter(t[k], q[k], s=70, color=col, edgecolor=SURFACE, linewidth=2, zorder=3, label=lab)
        txt = f"{k}"
        if k in g["G_SB"]["failed_anchors"]:
            txt += f"  LOO {g['G_SB']['loo_residuals'][str(k)]:+.2f} (G_SB fail)"
        if k == 3:
            txt += f"  a₃ʳᵉˡ = {b2['a3_rel']:+.2f} (G_a3 pass)"
        if k == 0:
            txt += f"  a₀ʳᵉˡ = {b2['a0_rel_diagnostic']['combined']:+.2f} (diagnostic)"
        dy = -0.42 if k in (5, 4) else 0.22
        ax.annotate(txt, (t[k], q[k]), xytext=(6, 0), textcoords="offset points", fontsize=8.5, color=INK,
                    va="bottom" if dy > 0 else "top")
    ax.set_xlabel("days since CK0 (anchor charge start)", color=INK2, fontsize=10)
    ax.set_ylabel("Q_bot: Ah from charge start to the charge-side step", color=INK2, fontsize=10)
    ax.set_title(f"(a) Bottom section of the anchors (σ_LOO = {g['G_SB']['sigma_LOO']:.2f} Ah)\n"
                 "dots: combined Q_bot; bars: range over CL1–CL5", loc="left", fontsize=10.5, color=INK)
    ax.set_xlim(-5, 300)
    hd, lb = ax.get_legend_handles_labels()
    keys = ["relaxed 25", "anchor 3", "anchor 0", "Theil", "trend ±"]
    order = [next(i for i, z in enumerate(lb) if z.startswith(k)) for k in keys]
    ax.legend([hd[i] for i in order], [lb[i] for i in order], loc="upper right", bbox_to_anchor=(1.0, 0.84),
              fontsize=8, frameon=False, labelcolor=INK)
    # (b) step positions from the bottom
    style(bx)
    dcells = [100.41 - v for v in b3["D_top_cells"].values()]
    dloc = [100.41 - b3["D_top_per_locator"][n] for n in DL]
    ccells = list(b3["C_bot_cells"].values())
    cloc = [b3["C_bot_per_locator"][n] for n in CL]
    rows = [(1.0, dcells, dloc, b3["split"]["D_bot"], INK2, "CK0 C/20 discharge (5.1 A): D_bot"),
            (0.0, ccells, cloc, b3["split"]["C_bot"], AQUA, "anchor 0 charge (20.4 A, 45 °C): C_bot")]
    for y, cells, loc, med, col, lab in rows:
        bx.scatter(cells, [y + 0.08] * 4, s=64, color=col, edgecolor=SURFACE, linewidth=2, zorder=3, label=lab + " (cells)")
        bx.scatter(loc, [y - 0.08] * 5, s=40, facecolor="none", edgecolor=col, linewidth=1.5, marker="D", zorder=3)
        bx.plot([med, med], [y - 0.22, y + 0.22], color=col, lw=2.5, solid_capstyle="round")
        bx.annotate(f"median {med:.2f}", (med, y - 0.36), ha="center", fontsize=8.5, color=INK)
    db, cb = b3["split"]["D_bot"], b3["split"]["C_bot"]
    bx.annotate("", xy=(db, 0.5), xytext=(cb, 0.5), arrowprops=dict(arrowstyle="<->", color=INK, lw=1.2))
    bx.annotate(f"D_bot − C_bot = {db - cb:+.2f} Ah", ((db + cb) / 2, 0.55), ha="center", fontsize=9, color=INK)
    h = b3["h"]
    note = (f"a₀ = −(D_bot − C_bot) − h = {b3['a0']:+.2f} [{b3['a0_interval'][0]:.2f}, {b3['a0_interval'][1]:.2f}] Ah, "
            f"G_B3 not identified\nh from 25 °C anchors = {h['point']:.2f} [{h['lo']:.2f}, {h['hi']:.2f}] Ah; "
            f"exploratory h₁ from anchor 0 (45 °C) ≈ {b3['exploratory_not_registered']['h1_0']['A3']:.2f} → a₀ ≈ "
            f"{b3['exploratory_not_registered']['a0_with_h1_0']['A3']:.2f}")
    bx.text(0.0, -0.17, note, transform=bx.transAxes, fontsize=8.3, color=INK2, va="top")
    bx.set_yticks([0, 1]); bx.set_yticklabels(["anchor 0", "CK0"], fontsize=9, color=INK)
    bx.set_ylim(-0.5, 1.5)
    bx.set_xlabel("Ah from the bottom (C/20 end, resp. anchor charge start) to the step", color=INK2, fontsize=10)
    bx.set_title("(b) CK0 vs anchor-0 step positions\ndots: cells; ◇: per-locator values; bar: median", loc="left", fontsize=10.5, color=INK)
    bx.legend(loc="upper left", fontsize=8, frameon=False, labelcolor=INK)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    p = os.path.join(OUT, "wp2_bottom.png")
    fig.savefig(p, dpi=150, facecolor=SURFACE)
    print("wrote", p)


if __name__ == "__main__":
    main()
