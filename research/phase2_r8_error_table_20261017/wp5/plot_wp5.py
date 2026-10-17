"""WP5 figures, worst-20 % dossier and enrichment (protocol.json 'worst_set'); exploratory-unregistered extras."""
import json
import math
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
sys.path.insert(0, HERE)
from common8 import H  # noqa: E402
import eventcurves as EC  # noqa: E402
from plotstyle import INK2, SERIES, SP_COLOR, SP_MARKER, setup  # noqa: E402
import run_wp5 as R  # noqa: E402

plt = setup()
FIG = os.path.join(HERE, "figures")
DOS = os.path.join(HERE, "dossier")
OUT = os.path.join(HERE, "outputs")
BR_COLOR = {"fallback": SERIES[0], "phase": SERIES[1], "sqrt_gap": SERIES[2]}
BR_MARK = {"fallback": "s", "phase": "o", "sqrt_gap": "D"}
CELL_LS = ["-", "--", "-.", ":"]


def worst(df, col):
    a = df[col].abs()
    n = math.ceil(0.2 * a.notna().sum())
    cut = a.sort_values(ascending=False).iloc[n - 1]
    return df[a >= cut - 1e-12].assign(abs_res=a).sort_values("abs_res", ascending=False)


def enrichment(df, worst_idx, cats, label):
    rows = []
    w = df.index.isin(worst_idx)
    for c in cats:
        for lev in sorted(df[c].dropna().astype(str).unique()):
            x = df[c].astype(str) == lev
            t = [[int((x & w).sum()), int((~x & w).sum())], [int((x & ~w).sum()), int((~x & ~w).sum())]]
            odds, p = fisher_exact(t)
            rows.append(dict(set=label, category=c, level=lev, worst_n=int(w.sum()), worst_in_level=t[0][0],
                             worst_share=t[0][0] / max(1, w.sum()), base_n=len(df), base_in_level=int(x.sum()),
                             base_share=float(x.mean()), odds_ratio=odds, fisher_p_two_sided=p))
    return rows


def scatter_resid(ax, d, x, y, label_col="month", by="setpoint"):
    for sp in (25, 45):
        s = d[d[by] == sp]
        ax.scatter(s[x], s[y], color=SP_COLOR[sp], marker=SP_MARKER[sp], s=30, edgecolor="#fcfcfb", linewidth=1,
                   label=f"{sp} °C", zorder=2)
    for _, r in d.iterrows():
        if np.isfinite(r[x]) and np.isfinite(r[y]):
            ax.annotate(str(r[label_col]), (r[x], r[y]), fontsize=6, color=INK2, xytext=(3, 2), textcoords="offset points")
    ax.axhline(0, color=INK2, linewidth=0.8, zorder=1)
    ax.set_xlabel(x)
    ax.set_ylabel(y + " (Ah)")


def figures(c, e, y):
    os.makedirs(FIG, exist_ok=True)
    pk = e[e.unit == "pack_mean"]
    # events: each residual against each registered slice variable
    xs = ["days_since_switch", "dT_at45", "fade_pct", "sharp_height_mV_per_Ah"]
    for res in ("R_seg", "R_anc", "R_anc_b"):
        fig, axs = plt.subplots(1, 4, figsize=(14, 3.6))
        for ax, x in zip(axs, xs):
            scatter_resid(ax, pk, x, res)
        axs[0].legend(loc="best")
        fig.suptitle(f"{res} (pack mean) vs registered slice variables; labels = month (anchor index)")
        fig.tight_layout()
        fig.savefig(os.path.join(FIG, f"events_{res}_vs_slices.png"))
        plt.close(fig)
    # cases: inc_resid vs slice variables, coloured by anchor set point, marker by branch, label = checkup
    fig, axs = plt.subplots(1, 4, figsize=(14, 3.8))
    for ax, x in zip(axs, ["fade_pct", "gap_days", "days_anchor_to_ck", "uses_first_post_anchor_program"]):
        xv = c[x].astype(float) + (np.random.default_rng(0).uniform(-0.08, 0.08, len(c)) if x.startswith("uses") else 0)
        for br in ("fallback", "phase", "sqrt_gap"):
            m = c.branch == br
            ax.scatter(xv[m], c.loc[m, "inc_resid_Ah"], color=BR_COLOR[br], marker=BR_MARK[br], s=28, edgecolor="#fcfcfb",
                       linewidth=1, label=br, zorder=2)
        for i, r in c[c.scenario == "real"].iterrows():
            ax.annotate("real " + r["checkup"], (xv[i], r["inc_resid_Ah"]), fontsize=6, color=INK2, xytext=(3, 2),
                        textcoords="offset points")
        ax.axhline(0, color=INK2, linewidth=0.8)
        ax.set_xlabel(x)
        ax.set_ylabel("inc_resid (Ah)")
    axs[0].legend(loc="best")
    fig.suptitle("Cases (SUB, Δ-free inc_resid, all scenarios); colour/marker = branch")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "cases_inc_resid_vs_slices.png"))
    plt.close(fig)
    # per-branch inc_resid bars for every scenario
    scens = ["real", "PG1", "PG2", "PC5", "PC10", "CS", "CSE", "PC5_all", "PC10_all"]
    fig, axs = plt.subplots(3, 3, figsize=(12, 8), sharey=True)
    for ax, s in zip(axs.flat, scens):
        d = c[c.scenario == s].sort_values("k")
        ax.bar(d["k"], d["inc_resid_Ah"], color=[BR_COLOR[b] for b in d["branch"]], width=0.7, edgecolor="#fcfcfb",
               linewidth=2)
        for _, r in d.iterrows():
            ax.annotate(r["branch"][0], (r["k"], r["inc_resid_Ah"]), ha="center", fontsize=7, color=INK2,
                        xytext=(0, 3 if r["inc_resid_Ah"] >= 0 else -9), textcoords="offset points")
        ax.axhline(0, color=INK2, linewidth=0.8)
        ax.set_title(s)
        ax.set_xticks(range(1, 8))
        ax.set_xlabel("checkup k")
    axs[0, 0].set_ylabel("inc_resid (Ah)")
    handles = [plt.Rectangle((0, 0), 1, 1, color=BR_COLOR[b]) for b in BR_COLOR]
    fig.legend(handles, [f"{b} ({b[0]})" for b in BR_COLOR], loc="upper right", ncol=3)
    fig.suptitle("SUB inc_resid per scenario and checkup, by branch")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(os.path.join(FIG, "cases_inc_resid_by_branch_bars.png"))
    plt.close(fig)
    # cells: R_cell over time, small multiples (H6)
    cl = e[e.unit != "pack_mean"]
    fig, axs = plt.subplots(1, 4, figsize=(14, 3.4), sharey=True)
    for ax, (u, g) in zip(axs, cl.groupby("unit")):
        scatter_resid(ax, g, "t_days", "R_cell")
        ax.set_title(u)
    axs[0].legend(loc="best")
    fig.suptitle("R_cell (cell depth minus pack median) over the campaign; labels = month")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "events_R_cell_by_cell.png"))
    plt.close(fig)
    # cycles (H10/H10b)
    fig, axs = plt.subplots(1, 2, figsize=(12, 3.6))
    tt = pd.to_datetime(y["t_top"])
    for ax, col, unit in ((axs[0], "R_cyc_slot_top_Ah_rel_last_cv_end", "Ah"), (axs[1], "R_cyc_slot_V_bottom_pack", "V")):
        for sp in (25, 45):
            m = y.setpoint == sp
            ax.scatter(tt[m], y.loc[m, col], color=SP_COLOR[sp], marker=SP_MARKER[sp], s=10, label=f"{sp} °C")
        ax.axhline(0, color=INK2, linewidth=0.8)
        ax.set_ylabel(f"{col} ({unit})")
        ax.tick_params(axis="x", rotation=30)
    axs[1].set_ylim(-0.06, 0.06)
    axs[0].legend()
    fig.suptitle("Cycles: phase-matched residuals (V panel clipped to ±60 mV)")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "cycles_R_cyc_slot.png"))
    plt.close(fig)


def event_panel(p, title, info, path):
    d, band = p["depth"], p["band"]
    e, stop = p["e"], p["stop"]
    V = p["V"][e:e + stop]
    fig, axs = plt.subplots(1, 4, figsize=(15, 3.4))
    grid = np.arange(14.0, 52.0, 0.25)
    for ci, c in enumerate(EC.CELLS):
        v = EC.curve_on_grid(d[band], V[band, ci], grid)
        axs[0].plot(grid, v, color=SERIES[0], linestyle=CELL_LS[ci], linewidth=1.2, label=c[:-2])
        h, w, pkk = EC.sharpness(d[band], V[band, ci])
        vg = np.interp(EC.GRID, grid[np.isfinite(v)], v[np.isfinite(v)])
        vs = np.convolve(vg, np.ones(8) / 8, mode="same")
        inner = (EC.GRID >= 20.0) & (EC.GRID <= 44.0)   # away from the moving-average edges
        axs[1].plot(EC.GRID[inner], (-np.gradient(vs, EC.GRID) * 1000)[inner], color=SERIES[1], linestyle=CELL_LS[ci],
                    linewidth=1.2, label=c[:-2])
    axs[0].set_xlabel("depth below CV end (Ah)")
    axs[0].set_ylabel("cell V (band samples)")
    axs[0].legend(fontsize=7)
    axs[1].set_xlabel("depth (Ah)")
    axs[1].set_ylabel("−dV/dQ (mV/Ah), 2 Ah smoothing")
    axs[2].plot(d, p["cur"][e:e + stop], color=SERIES[0], linewidth=1)
    axs[2].set_xlabel("depth (Ah)")
    axs[2].set_ylabel("current (A)")
    axs[3].plot(d, p["g"]["temp_mean_C"].to_numpy(float)[e:e + stop], color=SERIES[1], linewidth=1)
    axs[3].set_xlabel("depth (Ah)")
    axs[3].set_ylabel("measured T (°C)")
    fig.suptitle(title, fontsize=9)
    fig.text(0.01, 0.01, info, fontsize=7, color=INK2, family="monospace")
    fig.tight_layout(rect=(0, 0.1, 1, 0.94))
    fig.savefig(path)
    plt.close(fig)


def case_panel(r, progs, ev_index, a, path):
    fig, axs = plt.subplots(1, 3, figsize=(14, 3.6))
    used = [(k, r[k]) for k in ("ev_E_prev", "ev_E_cur", "ev_after_first", "ev_after_last") if isinstance(r[k], str) and r[k]]
    grid = np.arange(14.0, 52.0, 0.25)
    for n, (k, ts) in enumerate(used):
        p = progs[ev_index[pd.Timestamp(ts)]]
        d, band = p["depth"], p["band"]
        vm = p["V"][p["e"]:p["e"] + p["stop"]].mean(axis=1)
        v = EC.curve_on_grid(d[band], vm[band], grid)
        axs[0].plot(grid, v, color=SERIES[n % 4], linewidth=1.4, label=f"{k[3:]} {ts[:10]}")
        vg = np.interp(EC.GRID, grid[np.isfinite(v)], v[np.isfinite(v)])
        inner = (EC.GRID >= 20.0) & (EC.GRID <= 44.0)
        axs[1].plot(EC.GRID[inner], (-np.gradient(np.convolve(vg, np.ones(8) / 8, mode="same"), EC.GRID) * 1000)[inner],
                    color=SERIES[n % 4], linewidth=1.4, label=k[3:])
    if used:
        axs[0].legend(fontsize=7)
        axs[1].legend(fontsize=7)
    else:
        axs[0].text(0.5, 0.5, "sqrt_gap: no step event used", ha="center", transform=axs[0].transAxes)
    axs[0].set_xlabel("depth (Ah)")
    axs[0].set_ylabel("cell-mean V")
    axs[1].set_xlabel("depth (Ah)")
    axs[1].set_ylabel("−dV/dQ (mV/Ah)")
    ax = axs[2]
    ax.plot(a["anchor"], a["Q_fc"], color=INK2, linewidth=1)
    ax.scatter(a["anchor"], a["Q_fc"], color=SERIES[0], s=20, zorder=2)
    ax.scatter([r["k"]], [r["Q_fc_anchor_used"] + r["increment_pred"]], color=SERIES[1], marker="^", s=50, zorder=3,
               label="anchor + increment_pred")
    ax.scatter([r["anchor_used"]], [r["Q_fc_anchor_used"]], facecolor="none", edgecolor=SERIES[1], s=80, zorder=3,
               label="anchor used")
    ax.set_xlabel("anchor / checkup index")
    ax.set_ylabel("Q_fc (Ah)")
    ax.legend(fontsize=7)
    fig.suptitle(f"case {r['scenario']} CK{r['k']} ({r['branch']}): inc_resid {r['inc_resid_Ah']:+.3f} Ah", fontsize=9)
    info = (f"anchor {r['anchor_used']} ({r['anchor_setpoint']} °C)  increment_pred {r['increment_pred']:+.3f}  "
            f"increment_obs {r['increment_obs']:+.3f}  beta_used {r['beta_used']}  gap_days {r['gap_days']:.1f}  "
            f"days_anchor_to_ck {r['days_anchor_to_ck']:.1f}  fade {r['fade_pct']:.2f} %  first_prog {r['flag']}")
    fig.text(0.01, 0.01, info, fontsize=7, color=INK2, family="monospace")
    fig.tight_layout(rect=(0, 0.08, 1, 0.94))
    fig.savefig(path)
    plt.close(fig)


def dossier(c, e, a):
    os.makedirs(DOS, exist_ok=True)
    progs = EC.programs(H.full_op())
    ev_index = {pd.Timestamp(p["t_cv_end"]): i for i, p in enumerate(progs)}
    pk = e[e.unit == "pack_mean"].copy()
    pk["switch_bin"] = pk["switch_bin"].astype(str)
    wc = worst(c, "inc_resid_Ah")
    wa = worst(pk[pk.R_anc.notna()], "R_anc")
    ws = worst(pk[pk.R_seg.notna()], "R_seg")
    lists = []
    for _, r in wc.iterrows():
        f = f"case_{r['scenario']}_CK{r['k']}.png"
        case_panel(r, progs, ev_index, a, os.path.join(DOS, f))
        lists.append(dict(set="cases |inc_resid|", item=f"{r['scenario']} CK{r['k']}", residual=r["inc_resid_Ah"], file=f))
    for lab, w, col in (("events |R_anc|", wa, "R_anc"), ("events |R_seg|", ws, "R_seg")):
        for _, r in w.iterrows():
            f = f"event_{r['event_id']}_{col}.png"
            info = (f"{r['event_id']} seg {r['segment']} {r['setpoint']} °C month {r['month']} prog#{r['program_index']} "
                    f"first={r['is_first_after_anchor']}  {col} {r[col]:+.3f}  R_anc_b {r['R_anc_b']:+.3f}  "
                    f"days_since_switch {r['days_since_switch']:.1f} ({r['switch_kind']})  dT45 {r['dT_at45']:+.2f}  "
                    f"sharp {r['sharp_height_mV_per_Ah']:.2f} mV/Ah  fade {r['fade_pct']:.2f} %")
            event_panel(progs[ev_index[pd.Timestamp(r["t_cv_end"])]], f"{lab}: {r['event_id']} ({r['t_cv_end']})", info,
                        os.path.join(DOS, f))
            lists.append(dict(set=lab, item=r["event_id"], residual=r[col], file=f))
    pd.DataFrame(lists).to_csv(os.path.join(DOS, "worst_sets.csv"), index=False)
    cc = c.copy()
    cc["uses_first_post_anchor_program"] = cc["flag"]
    rows = enrichment(cc, wc.index, ["scenario", "branch", "anchor_setpoint", "uses_first_post_anchor_program", "fade_bin",
                                     "gap_bin"], "cases |inc_resid|")
    ecats = ["setpoint", "is_first_after_anchor", "switch_bin", "sharp_bin", "month_group", "switch_kind"]
    rows += enrichment(pk[pk.R_anc.notna()], wa.index, ecats, "events |R_anc|")
    rows += enrichment(pk[pk.R_seg.notna()], ws.index, ecats, "events |R_seg|")
    enr = pd.DataFrame(rows)
    enr.to_csv(os.path.join(DOS, "enrichment.csv"), index=False)
    # H5 registered enrichment: Fisher (greater) of the lowest-sharpness share in the worst 20 % by |R_seg|
    h5 = {}
    for items, d in (("events_pack", pk[pk.R_seg.notna()]), ("events_cell", e[(e.unit != "pack_mean") & e.R_seg.notna()])):
        w = worst(d, "R_seg").index
        x = d["sharp_bin"] == "low"
        ww = d.index.isin(w)
        t = [[int((x & ww).sum()), int((~x & ww).sum())], [int((x & ~ww).sum()), int((~x & ~ww).sum())]]
        h5[items] = dict(table=t, odds_ratio=fisher_exact(t, alternative="greater")[0],
                         p_greater=fisher_exact(t, alternative="greater")[1])
    return wc, wa, ws, enr, h5


def exploratory(y):
    """exploratory-unregistered: H10/H10b restricted to complete program blocks (12 swings)."""
    full = y.groupby("program_block").size()
    yy = y[y.program_block.isin(full[full == 12].index)]
    out = {}
    for col in ("R_cyc_slot_top_Ah_rel_last_cv_end", "R_cyc_slot_V_bottom_pack"):
        out[col] = dict(n=int(yy[col].notna().sum()), abs_q50=float(yy[col].abs().median()),
                        abs_q90=float(yy[col].abs().quantile(0.9)), abs_max=float(yy[col].abs().max()))
    return out


if __name__ == "__main__":
    c, e, a, y = R.load()
    figures(c, e, y)
    wc, wa, ws, enr, h5 = dossier(c, e, a)
    ex = exploratory(y)
    json.dump(dict(H5_enrichment=h5, exploratory_unregistered_H10_complete_blocks=ex),
              open(os.path.join(OUT, "wp5_dossier_extra.json"), "w"), indent=1, default=float)
    pd.set_option("display.width", 250)
    print(wc[["scenario", "k", "branch", "inc_resid_Ah"]].to_string())
    print(wa[["event_id", "setpoint", "month", "R_anc"]].to_string())
    print(ws[["event_id", "setpoint", "month", "R_seg"]].to_string())
    print(enr[enr.fisher_p_two_sided < 0.1].round(3).to_string())
    print(json.dumps(dict(h5=h5, ex=ex), indent=1, default=float))
