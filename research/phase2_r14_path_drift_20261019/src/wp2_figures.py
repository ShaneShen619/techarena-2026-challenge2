"""WP2 figures (static PNG): fig1 Term3 / Term3' / P2 (Ah) vs fade with Theil-Sen line and LOO band;
fig2 P3 path memory vs month; fig3 (exploratory) lambda by segment over time and Term3 with a same-cycle lambda."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import data14 as D

ST = D.ST
OUT = os.path.join(ST, "wp2")
# reference palette (validated all-pairs for 3 slots, light surface); text tokens for all text
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3de", "#fcfcfb"
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
                     "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
                     "text.color": INK, "font.size": 10, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
                     "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 2})


def band(ax, x, st, color, label):
    """Theil-Sen line and the LOO band (envelope of the leave-one-out lines, each with intercept median(y - b x))."""
    m = st["main"]
    xs = np.linspace(min(x) - 0.2, max(x) + 0.2, 50)
    vals = st["values"]
    lab = list(map(int, vals.keys()))
    xv = np.array(x); yv = np.array(list(vals.values()))
    lines = []
    for k, b in m["loo"].items():
        keep = np.array([l != int(k) for l in lab])
        a = np.median(yv[keep] - b * xv[keep])
        lines.append(a + b * xs)
    lines = np.array(lines)
    ax.fill_between(xs, lines.min(0), lines.max(0), color=color, alpha=0.13, linewidth=0)
    ax.plot(xs, m["intercept"] + m["d"] * xs, color=color, linewidth=2, label=label)


def fig1(t3, stats):
    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    q = t3[t3["anchor"] >= 1]
    p1 = q[np.isfinite(q["term3"])]
    gb = q[~np.isfinite(q["term3"])]
    p1b = q[np.isfinite(q["term3b"])]
    band(ax, p1["fade"], stats["P1"], BLUE,
         f"P1 Theil–Sen: d = {stats['P1']['main']['d']:+.3f} Ah/Ah, E = {stats['P1']['main']['E']:+.2f} Ah "
         f"(LOO {stats['P1']['main']['loo_range_E'][0]:+.2f} … {stats['P1']['main']['loo_range_E'][1]:+.2f})")
    band(ax, q["fade"], stats["P2"], AQUA,
         f"P2 Theil–Sen: d = {stats['P2']['main']['d']:+.3f} Ah/Ah, E = {stats['P2']['main']['E']:+.2f} Ah "
         f"(LOO {stats['P2']['main']['loo_range_E'][0]:+.2f} … {stats['P2']['main']['loo_range_E'][1]:+.2f})")
    ax.plot(p1["fade"], p1["term3"], "o", ms=9, color=BLUE, mec=SURF, mew=2, label="P1 Term3 (registered, gap-free)")
    ax.plot(gb["fade"], gb["term3_gap_bridged"], "o", ms=9, mfc="none", mec=BLUE, mew=2,
            label="Term3 across a recording gap (descriptive S_gap)")
    ax.plot(p1b["fade"], p1b["term3b"], "s", ms=14, mfc="none", mec=ORANGE, mew=2,
            label="P1b Term3' (2 points; = Term3 exactly)")
    ax.plot(q["fade"], q["P2_pack_Ah"], "^", ms=9, color=AQUA, mec=SURF, mew=2, label="P2 pack, ΔV / |s_top| (Ah)")
    for _, r in q.iterrows():
        y = r["term3"] if np.isfinite(r["term3"]) else r["term3_gap_bridged"]
        ax.annotate(f"k={int(r['anchor'])}", (r["fade"], y), xytext=(6, 6), textcoords="offset points",
                    fontsize=8, color=INK2)
    ax.axhline(0, color=INK2, linewidth=0.8)
    ax.set_xlabel("fade_k = Q_fc,1 − Q_fc,k  (Ah)")
    ax.set_ylabel("top of first top-up − top of anchor  (Ah)")
    ax.set_title("Path signal vs fade (25 °C anchors 1–7); shaded: leave-one-anchor-out band", loc="left", fontsize=11)
    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), frameon=False, fontsize=8.5)
    ax.set_ylim(-0.15, 1.75)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig1_term3_vs_fade.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig2(p3):
    q = p3[p3["anchor"] >= 1].copy()
    x = np.arange(len(q)); labels = [f"{m}\nk={k}" for m, k in zip(q["month"], q["anchor"])]
    fig, axs = plt.subplots(2, 2, figsize=(10, 6.4), sharex=True)
    ax = axs[0, 0]
    ax.plot(x, q["o_A3"], "-o", color=BLUE, ms=8, mec=SURF, mew=2, label="o_k (A3 step)")
    ax.plot(x, q["o_dvdq"], "--s", color=ORANGE, ms=8, mec=SURF, mew=2, label="o_k (dV/dQ variant, 0.25 Ah grid)")
    ax.plot(x, q["abs_shift_A3"], ":^", color=AQUA, ms=8, mec=SURF, mew=2, label="o_k + Term3 (A3; registered Term3)")
    ax.plot(x, q["abs_shift_A3_gap_bridged"], "^", mfc="none", mec=AQUA, ms=8, mew=2)
    ax.set_title("First-program offset (Ah)", loc="left", fontsize=10)
    ax.legend(frameon=False, fontsize=8)
    for ax, col, title in [(axs[0, 1], "dCV_Ah_A_minus_T1", "CV Ah: anchor − T1 (Ah)"),
                           (axs[1, 0], "dCV_s_A_minus_T1", "CV duration: anchor − T1 (s)"),
                           (axs[1, 1], "dI_end_A_minus_T1", "End current: anchor − T1 (A)")]:
        ax.plot(x, q[col], "-o", color=BLUE, ms=8, mec=SURF, mew=2)
        ax.set_title(title, loc="left", fontsize=10)
    for ax in axs[1]:
        ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8)
    axs[1, 1].set_ylim(-0.02, 0.02)
    fig.suptitle("P3 path memory by month (descriptive; anchors 1–7)", x=0.01, ha="left", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig2_p3_vs_month.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig3(pairs, sc):
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.4))
    ax = axs[0]
    tt = pairs[(pairs["type"] == "TT") & pairs["gap_free"]].copy()
    tt["t_mid"] = pd.to_datetime(tt["t_i"]) + (pd.to_datetime(tt["t_j"]) - pd.to_datetime(tt["t_i"])) / 2
    for sp, color, mk in [(45, BLUE, "o"), (25, ORANGE, "s")]:
        g = tt[tt["setpoint"] == sp]
        ax.plot(g["t_mid"], 1000 * g["ratio"], mk, color=color, ms=8, mec=SURF, mew=2, linestyle="none",
                label=f"TT pairs, {sp} °C")
    at = pairs[pairs["type"] == "AT1"].copy()
    at["t_mid"] = pd.to_datetime(at["t_i"]) + (pd.to_datetime(at["t_j"]) - pd.to_datetime(at["t_i"])) / 2
    pooled = 1000 * sc.loc[sc["lambda_source_registered"] == "pooled_25", "lambda_registered"].iloc[0]
    ax.axhline(pooled, color=ORANGE, linewidth=1.2, linestyle="--")
    ax.annotate("pooled 25 °C λ used for anchors 1–4, 7", (tt["t_mid"].min(), pooled), xytext=(0, -14),
                textcoords="offset points", fontsize=8, color=INK2)
    for t in at.loc[at["anchor"] >= 1, "t_mid"]:
        ax.axvline(t, color=GRID, linewidth=1.5, zorder=0)
    ax.set_ylabel("λ = N / thr  (×10⁻³)")
    ax.set_title("Loss rate λ steps between checkup cycles\n(grey: anchor → T1 windows)", loc="left", fontsize=10)
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    ax.tick_params(axis="x", labelrotation=30)
    ax = axs[1]
    ax.plot(sc["fade"], sc["term3_gap_bridged"], "o", ms=9, color=BLUE, mec=SURF, mew=2,
            label="registered λ (gap-bridged for k = 3, 7)")
    ax.plot(sc["fade"], sc["term3_same_cycle"], "D", ms=8, color=AQUA, mec=SURF, mew=2,
            label="same-cycle 45 °C λ (exploratory)")
    for _, r in sc.iterrows():
        ax.annotate(f"k={int(r['anchor'])}", (r["fade"], r["term3_gap_bridged"]), xytext=(5, 5),
                    textcoords="offset points", fontsize=8, color=INK2)
    ax.axhline(0, color=INK2, linewidth=0.8)
    ax.set_xlabel("fade_k (Ah)"); ax.set_ylabel("Term3 (Ah)")
    ax.set_title("Term3 with the registered vs a same-cycle λ", loc="left", fontsize=10)
    ax.legend(frameon=False, fontsize=8)
    fig.suptitle("EXPLORATORY — not registered, decides nothing", x=0.01, ha="left", fontsize=11, color=INK2)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig3_explore_lambda.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    t3 = pd.read_csv(os.path.join(OUT, "term3.csv"))
    stats = json.load(open(os.path.join(OUT, "stats.json")))
    p3 = pd.read_csv(os.path.join(OUT, "p3_memory.csv"))
    pairs = pd.read_csv(os.path.join(OUT, "pairs.csv"))
    sc = pd.read_csv(os.path.join(OUT, "explore_same_cycle_term3.csv"))
    fig1(t3, stats); fig2(p3); fig3(pairs, sc)
    print("figures written")


if __name__ == "__main__":
    main()
