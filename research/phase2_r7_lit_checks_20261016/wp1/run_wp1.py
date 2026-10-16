"""WP1: is the post-anchor offset an overhang state effect? (protocol.json incl. amendment_1)."""
import itertools
import json
import math
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
sys.path.insert(0, os.path.join(STUDY, "sources", "v3"))
from common6 import H  # noqa: E402
import audits6 as A  # noqa: E402
import grid7 as G  # noqa: E402
from v2 import anchors_by_checkup  # noqa: E402

OUT = os.path.join(HERE, "outputs")
PROTO = json.load(open(os.path.join(HERE, "protocol.json")))


def spearman_exact(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    rx, ry = pd.Series(x).rank().to_numpy(), pd.Series(y).rank().to_numpy()
    rho = float(np.corrcoef(rx, ry)[0, 1])
    perms = [float(np.corrcoef(rx, np.array(p))[0, 1]) for p in itertools.permutations(ry)]
    p_two = float(np.mean(np.abs(perms) >= abs(rho) - 1e-12))
    p_pos = float(np.mean(np.array(perms) >= rho - 1e-12))
    p_neg = float(np.mean(np.array(perms) <= rho + 1e-12))
    return dict(rho=rho, p_two_sided=p_two, p_upper=p_pos, p_lower=p_neg, n=len(x))


def table():
    full = H.full_op()
    fc = H.full_charges(full).sort_values("t_end").reset_index(drop=True)
    anc = anchors_by_checkup(fc, H.CK)
    a3 = A.table_3a().set_index("anchor")
    c3 = A.table_3c()
    a4 = H.charge_step_split(full, fc, smooth_Ah=2.0)
    rows = []
    for j in range(8):
        a = anc[j]
        before = full[full["timestamp"] < H.CK[j]]
        if len(before):
            last = before.iloc[-1]
            dwell = (a["t_start"] - last["timestamp"]).total_seconds() / 3600
            end_state = dict(end_pack_V=float(last["pack_voltage_V"]), end_I_A=float(last["current_A"]),
                             end_setpoint=int(last["chamber_temperature_C"]), end_time=str(last["timestamp"]))
        else:
            dwell = (a["t_start"] - H.CK[j]).total_seconds() / 3600
            end_state = dict(end_pack_V=np.nan, end_I_A=np.nan, end_setpoint=np.nan, end_time="campaign start")
        cj = c3[c3["anchor_t_end"].astype(str) == str(a["t_end"])]
        off = {f"off_{v}": float(cj[cj.variant == v]["adj_offset"].iloc[0]) for v in H.STEP_VARIANTS if (cj.variant == v).any()}
        main = cj[cj.variant == "main"]
        # second vs third program (same segment), trend-free: only where >= 3 programs
        st = H.step_programs(full).dropna(subset=["step_mean"]).sort_values("t_cv_end").reset_index(drop=True)
        idx = np.where(st["t_cv_end"] >= a["t_end"] - pd.Timedelta(minutes=10))[0]
        second = np.nan
        if len(idx) >= 3:
            seg = st.loc[idx[0], "segment"]
            same = st[(st["segment"] == seg) & (st.index >= idx[0])]
            if len(same) >= 4:
                d = np.diff(same["step_mean"].to_numpy())
                trend = float(np.median(-d[2:])) if len(d) >= 3 else 0.0
                second = float(same["step_mean"].iloc[1] - same["step_mean"].iloc[2]) - trend
            elif len(same) == 3:
                second = float(same["step_mean"].iloc[1] - same["step_mean"].iloc[2])
        sp = a4[a4["segment"] == a["segment"]].iloc[0]
        rows.append(dict(anchor=j, checkup=H.CK_NAMES[j], ck_date=str(H.CK[j].date()), anchor_start=str(a["t_start"]),
                         setpoint=int(a["setpoint_C"]), Q_fc=float(a["Q_Ah"]), dwell_h=dwell, **end_state,
                         rest_before_h=float(a3.loc[j, "rest_before_h"]), pack_rest_V=float(a3.loc[j, "pack_rest_V"]),
                         r_upper=float(a3.loc[j, "r_upper"]), r_half=float(a3.loc[j, "r_half"]),
                         off_median=float(np.median(list(off.values()))), **off,
                         n_programs_after=int(main["n_after"].iloc[0]) if len(main) else 0,
                         first_program_setpoint=int(main["setpoint"].iloc[0]) if len(main) else np.nan,
                         second_offset=second,
                         bottom_to_step=float(sp["bottom_to_step_mean"]), step_to_top=float(sp["step_to_top_mean"])))
    return pd.DataFrame(rows)


def ov_targets(tab, b0_mode):
    b = dict(zip(tab["anchor"], tab["off_median"]))
    b0 = float(np.median([b[k] for k in range(1, 8)])) if b0_mode == "median" else float(b[0])
    out = {}
    for D in (0.0, 0.4, 0.8):
        for d in (0.0, -0.031):
            tk = {}
            for k in range(1, 8):
                p = H.QFC[k] + H.EPS0
                L = max(0.0, 100.41 - p)
                tk[k] = p + D + (b[k] - b0) + d * L
            out[f"OVafter_{b0_mode}_D{D}_d{d}"] = tk
    return out, b0


if __name__ == "__main__":
    tab = table()
    tab.to_csv(os.path.join(OUT, "anchor_state_table.csv"), index=False)
    t17 = tab[tab.anchor >= 1]
    res = {"P1_rho_offset_vs_r_upper": spearman_exact(t17["off_median"], t17["r_upper"]),
           "P2_rho_offset_vs_dwell": spearman_exact(t17["off_median"], t17["dwell_h"]),
           "P3_rho_offset_vs_bottom_to_step": spearman_exact(t17["off_median"], t17["bottom_to_step"])}
    # robustness: per step variant
    for v in H.STEP_VARIANTS:
        col = f"off_{v}"
        res[f"by_variant_{v}"] = {k: round(spearman_exact(t17[col], t17[c])["rho"], 3)
                                  for k, c in (("P1", "r_upper"), ("P2", "dwell_h"), ("P3", "bottom_to_step"))}
    P1 = res["P1_rho_offset_vs_r_upper"]["rho"] >= 0.5
    P2 = res["P2_rho_offset_vs_dwell"]["rho"] >= 0.5
    P3 = res["P3_rho_offset_vs_bottom_to_step"]["rho"] <= -0.5
    ev = t17["second_offset"].dropna()
    P4 = "not evaluable" if len(ev) < 4 else bool((ev <= 0.15).sum() >= min(5, len(ev)))
    n_hold = int(P1) + int(P2) + int(P3)
    cls = "supported" if (P1 and (P2 or P3)) else ("partly_supported" if n_hold == 1 else
                                                   ("not_supported" if n_hold == 0 else "partly_supported"))
    # physical discussion numbers
    AF = math.exp(64500 / 8.314 * (1 / 298.15 - 1 / 318.15))
    end_hi = int((t17["end_pack_V"] > 13.0).sum())
    order_main = "before" if end_hi >= 5 else "equal_weight"
    # grid
    p6 = pd.read_csv(os.path.join(G.R6, "wp1", "outputs", "wp1_predictions.csv"))
    p6 = p6[(p6.scenario == "real") & (p6.step == "main") & (p6.a4s == 2.0)][["scenario", "k", "model", "Q"]]
    sub = p6[p6.model == "SUB"]
    add = []
    for d in (-0.031, -0.020):
        x = sub.copy()
        x["Q"] = x["Q"] + d * np.maximum(0.0, 100.41 - x["Q"])
        x["model"] = f"SUB+drift{d}"
        add.append(x)
    pred = pd.concat([p6] + add, ignore_index=True)
    grids = {}
    for mode in ("median", "measured"):
        ovt, b0 = ov_targets(tab, mode)
        tg = {**G.targets6(), **ovt}
        sc = G.scores(pred, tg)
        cand = [m for m in sc.model.unique() if m != "EX"]
        s = sc.pivot_table(index="h", columns="model", values="s")[cand]
        t_all, _ = G.decision(s)
        t_ov, _ = G.decision(s.loc[list(ovt)])
        t6, _ = G.decision(s.loc[list(G.targets6())], G.round6_weights(list(G.targets6())))
        grids[mode] = dict(b0=b0, all=t_all, ov=t_ov, r6=t6, s=s)
        s.to_csv(os.path.join(OUT, f"wp1_s_by_h_b0{mode}.csv"))
        t_all.join(t_ov, rsuffix="_OVonly").to_csv(os.path.join(OUT, f"wp1_grid_decision_b0{mode}.csv"))
    # prior update over f on the round-6 grid
    fw = {"supported": {0.0: 0.7, 0.5: 0.2, 1.0: 0.1}, "partly_supported": {0.0: 0.6, 0.5: 0.3, 1.0: 0.1},
          "not_supported": {0.0: 0.5, 0.5: 0.3, 1.0: 0.2}}[cls]
    hs = list(G.targets6())
    w = pd.Series([fw[h["f"]] * {0.0: 0.5, -0.031: 0.5}[h["d"]] / 3.0 for h in G.HYP6], index=hs)
    s6 = grids["median"]["s"].loc[hs]
    E_upd = s6.T.dot(w / w.sum())
    E_r6 = grids["median"]["r6"]["E_diagnosis"]
    prior = pd.DataFrame({"E_diagnosis_round6": E_r6, "E_diagnosis_updated": E_upd}).sort_values("E_diagnosis_updated")
    prior.to_csv(os.path.join(OUT, "wp1_prior_update.csv"))
    out = dict(classification=cls, P1=bool(P1), P2=bool(P2), P3=bool(P3), P4=P4, n_P4_evaluable=int(len(ev)),
               stats=res, exchange_AF_45_vs_25_Ea64p5=AF, segment_end_above_13V=f"{end_hi}/7", order_main=order_main,
               b0_median=grids["median"]["b0"], b0_measured=grids["measured"]["b0"],
               anchor0=tab[tab.anchor == 0][["off_median", "dwell_h", "r_upper", "bottom_to_step", "step_to_top"]].iloc[0].to_dict(),
               f_weights_updated=fw,
               grid_main_SUB=dict(max_regret_all=float(grids["median"]["all"].loc["SUB", "max_regret"]),
                                  max_regret_OV=float(grids["median"]["ov"].loc["SUB", "max_regret"]),
                                  worst_all=float(grids["median"]["all"].loc["SUB", "worst_s"])),
               lowest_max_regret_all=str(grids["median"]["all"]["max_regret"].idxmin()),
               lowest_max_regret_OV=str(grids["median"]["ov"]["max_regret"].idxmin()),
               lowest_E_updated=str(E_upd.idxmin()))
    json.dump(out, open(os.path.join(OUT, "wp1_predictions_P.json"), "w"), indent=1, default=str)
    # plots
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(14, 4.2))
    for a, col, lab in ((ax[0], "r_upper", "3a residual r_j upper (Ah)"), (ax[1], "dwell_h", "dwell before anchor (h)"),
                        (ax[2], "bottom_to_step", "anchor bottom->step (Ah)")):
        a.scatter(t17[col], t17["off_median"], c="C0")
        a.scatter(tab[tab.anchor == 0][col], tab[tab.anchor == 0]["off_median"], c="C3", marker="s", label="anchor 0 (45 C)")
        for _, r in tab.iterrows():
            a.annotate(str(int(r["anchor"])), (r[col], r["off_median"]), fontsize=8, xytext=(3, 3), textcoords="offset points")
        a.set_xlabel(lab)
        a.set_ylabel("first-program offset, median of 6 variants (Ah)")
    ax[0].legend(fontsize=8)
    fig.suptitle("WP1: post-anchor offset vs anchor state (anchors 1-7 blue)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "wp1_offset_vs_state.png"), dpi=130)
    pd.set_option("display.width", 250)
    print(tab.round(3).to_string())
    print(json.dumps(out, indent=1, default=str))
    print(grids["median"]["all"].join(grids["median"]["ov"], rsuffix="_OV").round(4).sort_values("max_regret").to_string())
    print(prior.round(4).to_string())
