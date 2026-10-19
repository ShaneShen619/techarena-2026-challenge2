"""WP2: bottom section — start audit (B1), charge-side step locators and trend (B2), CK0 split (B3), gates.

Uses the registered modules src/locators.py and src/ahchain.py unchanged (protocol v1, wp1/protocol.sha256).
Run: python3 -B src/wp2_run.py b1|b2|b3|gates"""
import json, os, sys
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

import data12 as D
import locators as L
import ahchain as AC

OUT = os.path.join(D.ST, "wp2")
CK0_DATE = D.CK_DATES[0]
RELAXED_SLOPE_MV_H = 6.0


def events():
    return pd.read_csv(os.path.join(D.ST, "wp0", "events.csv"),
                       parse_dates=["t_charge_start", "t_cv_start", "t_cv_end", "t_prepulse"])


def anchors():
    return events().query("type == 'A'").sort_values("anchor_k").reset_index(drop=True)


def jdump(obj, name):
    json.dump(obj, open(os.path.join(OUT, name), "w"), indent=1, default=lambda x: None if x is None else
              (float(x) if isinstance(x, (np.floating, float)) else (int(x) if isinstance(x, np.integer) else str(x))))


def t_days(ts):
    return (pd.Timestamp(ts) - CK0_DATE).total_seconds() / 86400.0


# ---- B1 ----------------------------------------------------------------------------------------------------
def b1():
    S = D.segments()
    cw = pd.read_csv(os.path.join(D.ST, "wp0", "checkup_windows.csv"))
    rows = []
    for _, a in anchors().iterrows():
        g = S[a["segment"]]
        el = g["elapsed_s"].to_numpy(float); i = g["current_A"].to_numpy(float)
        u = g["pack_voltage_V"].to_numpy(float); V = g[D.CELLS].to_numpy(float); T = g["temp_mean_C"].to_numpy(float)
        s = int([x for x in np.where(g["timestamp"].to_numpy() == np.datetime64(a["t_charge_start"]))[0] if i[x] > 0.5][0])
        k = s - 1
        while k >= 0 and abs(i[k]) <= 0.5:
            k -= 1
        idx = np.arange(k + 1, s)
        h = (el[idx] - el[idx[0]]) / 3600.0
        last30 = idx[el[idx] >= el[s - 1] - 1800.0]
        h30 = (el[last30] - el[last30[0]]) / 3600.0
        slope30 = 1000.0 * np.polyfit(h30, u[last30], 1)[0]
        w = cw[cw["checkup"] == f"CK{int(a['anchor_k'])}"].iloc[0]
        row = dict(anchor_k=int(a["anchor_k"]), segment=int(a["segment"]), setpoint=int(a["setpoint"]),
                   checkup=w["checkup"], window_days=w["window_days"], window_known=bool(w["window_known"]),
                   window_from=w["t_last"], segment_start=g["timestamp"].iloc[0], charge_start=a["t_charge_start"],
                   rest_h=(el[s - 1] - el[idx[0]]) / 3600.0, rest_from_segment_start=bool(idx[0] == 0),
                   days_since_window_start=(pd.Timestamp(a["t_charge_start"]) - pd.Timestamp(w["t_last"])).total_seconds() / 86400.0,
                   pack_V_rest_first=u[idx[0]], pack_V_start=u[s - 1])
        for c in range(4):
            row[f"cell{c + 1}_V_start"] = V[s - 1, c]
        row.update(slope_last30_mV_h=slope30, slope_whole_rest_mV_h=1000.0 * np.polyfit(h, u[idx], 1)[0],
                   slope_window_h=min(0.5, row["rest_h"]),
                   temp_start_C=T[s - 1], temp_rest_first_C=T[idx[0]],
                   temp_trend_K_h=float(np.polyfit(h, T[idx], 1)[0]),
                   spread_start_V=V[s - 1].max() - V[s - 1].min(), spread_rest_first_V=V[idx[0]].max() - V[idx[0]].min(),
                   lowest_cell_start=D.CELLS[int(np.argmin(V[s - 1]))][:5],
                   relaxed=bool(slope30 <= RELAXED_SLOPE_MV_H))
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(OUT, "start_audit.csv"), index=False, float_format="%.6g")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
    print(out.T.to_string())


# ---- B2 ----------------------------------------------------------------------------------------------------
CL = ["CL1", "CL2", "CL3", "CL4", "CL5"]


def anchor_locators():
    """{k: dict(q_fc, t, cells=[variant dicts], comb, cell_values, per_loc)} for the eight anchors."""
    S = D.segments()
    out = {}
    for _, a in anchors().iterrows():
        q, V, qfc = L.anchor_charge(S[a["segment"]], a["t_charge_start"], a["t_cv_end"])
        cells = [L.charge_variants(q, V[:, c]) for c in range(len(L.CELLS))]
        comb, cv, per = L.combine(cells)
        out[int(a["anchor_k"])] = dict(q_fc=qfc, t=t_days(a["t_charge_start"]), cells=cells, comb=comb,
                                       cell_values=cv, per_loc=per, segment=int(a["segment"]))
    return out


def b2():
    A = anchor_locators()
    r8 = pd.read_csv(os.path.join(D.ST, "sources", "r8", "table_anchors.csv")).set_index("anchor")
    rows, r8c = [], {}
    for k, a in A.items():
        chk = L.r8_check([c["CL1"] for c in a["cells"]], float(r8.loc[k, "bottom_to_step"]))
        r8c[k] = chk
        for c, d in enumerate(a["cells"]):
            rows.append(dict(anchor_k=k, unit=L.CELLS[c][:5], **d, value=a["cell_values"][c], Q_fc=a["q_fc"],
                             t_days=a["t"]))
        rows.append(dict(anchor_k=k, unit="pack", **a["per_loc"], value=a["comb"], Q_fc=a["q_fc"], t_days=a["t"],
                         Q_bot=a["comb"], Q_top=a["q_fc"] - a["comb"], r8_bottom_to_step=chk["r8"],
                         cl1_rounded_mean=chk["cl1_rounded_mean"], r8_diff=chk["diff"], r8_pass=chk["passed"]))
    tab = pd.DataFrame(rows)
    tab.to_csv(os.path.join(OUT, "bottom_locators.csv"), index=False, float_format="%.6g")
    rel = list(L.RELAXED_ANCHORS)
    x = np.array([A[k]["t"] for k in rel]); y = np.array([A[k]["comb"] for k in rel])
    b, a0 = L.theil_sen(x, y)
    gsb = L.g_sb(x, y, rel)
    resid_in = {k: float(A[k]["comb"] - (a0 + b * A[k]["t"])) for k in A}
    a3 = L.anomaly(x, y, A[3]["t"], A[3]["comb"])
    a0rel = L.anomaly(x, y, A[0]["t"], A[0]["comb"])
    per_trend, a3_loc, a0_loc = {}, {}, {}
    for n in CL:
        yl = np.array([A[k]["per_loc"][n] for k in rel])
        ok = np.isfinite(yl)
        if ok.sum() >= 3:
            bl, al = L.theil_sen(x[ok], yl[ok])
            per_trend[n] = dict(slope=bl, intercept=al, n=int(ok.sum()))
            a3_loc[n] = L.anomaly(x[ok], yl[ok], A[3]["t"], A[3]["per_loc"][n])
            a0_loc[n] = L.anomaly(x[ok], yl[ok], A[0]["t"], A[0]["per_loc"][n])
        else:
            per_trend[n] = dict(slope=np.nan, intercept=np.nan, n=int(ok.sum())); a3_loc[n] = a0_loc[n] = np.nan
    ga3 = L.g_a3(a3, a3_loc, gsb["sigma_LOO"])
    sa = pd.read_csv(os.path.join(OUT, "start_audit.csv")).set_index("anchor_k")
    rv = [resid_in[k] for k in rel]
    rho_v = spearmanr(rv, [sa.loc[k, "pack_V_start"] for k in rel])
    rho_s = spearmanr(rv, [sa.loc[k, "spread_start_V"] for k in rel])
    res = dict(
        Q_bot={k: A[k]["comb"] for k in A}, Q_fc={k: A[k]["q_fc"] for k in A},
        Q_top={k: A[k]["q_fc"] - A[k]["comb"] for k in A}, t_days={k: A[k]["t"] for k in A},
        per_locator={k: A[k]["per_loc"] for k in A},
        trend=dict(anchors=rel, slope_Ah_per_day=b, intercept_Ah=a0, in_sample_residuals=resid_in),
        G_SB=gsb, a3_rel=a3, a3_rel_per_locator=a3_loc, G_a3=ga3,
        a0_rel_diagnostic=dict(combined=a0rel, per_locator=a0_loc,
                               note="extrapolated to t_0 and confounded by 45 degC; diagnostic only"),
        per_locator_trend=per_trend, r8_check=r8c, r8_check_all_pass=bool(all(v["passed"] for v in r8c.values())),
        descriptive=dict(residual_vs_start_V=dict(spearman_rho=float(rho_v.statistic), p=float(rho_v.pvalue)),
                         residual_vs_bottom_spread=dict(spearman_rho=float(rho_s.statistic), p=float(rho_s.pvalue)),
                         table=[dict(anchor_k=k, resid=resid_in[k], start_V=float(sa.loc[k, "pack_V_start"]),
                                     spread_V=float(sa.loc[k, "spread_start_V"]),
                                     slope_mV_h=float(sa.loc[k, "slope_last30_mV_h"])) for k in A]),
        protocol="v1 (wp1/protocol.sha256)")
    jdump(res, "b2_results.json")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
    print(tab.to_string())
    print(json.dumps({k: v for k, v in res.items() if k not in ("per_locator",)}, indent=1, default=float))


# ---- B3 ----------------------------------------------------------------------------------------------------
DLN = ["DL1", "DL2", "DL3", "DL4", "DL5"]


def cv_index(seg, t):
    i = seg["current_A"].to_numpy(float)
    return int([x for x in np.where(seg["timestamp"].to_numpy() == np.datetime64(t))[0] if i[x] > 0.5][-1])


def package_steps(S):
    """{CV-end timestamp: A3 robust step depth} from the package's own _step_depths (unchanged)."""
    sys.path.insert(0, D.PKG)
    from my_model import model_template as mt
    out = {}
    for _, g in S.items():
        for t, _, dep, _ in mt._step_depths(g.reset_index(drop=True)):
            out[pd.Timestamp(t)] = dep
    return out


def b3():
    S = D.segments(); ev = events().sort_values("t_cv_end").reset_index(drop=True); A = anchor_locators()
    c = D.ck0_curve()
    q = c["discharged_Ah"].to_numpy(float)
    d_cells = [L.discharge_variants(q, c[x].to_numpy(float)) for x in L.CELLS]
    c_cells = A[0]["cells"]
    pairs = AC.build_pairs(ev, S, D.CK_DATES)
    tm = AC.terms(pairs)
    t3 = tm[tm["term"] == "Term3"].set_index("k")
    a3 = package_steps(S)
    rows = []
    for k in L.H_ANCHORS:
        a = ev[(ev["type"] == "A") & (ev["anchor_k"] == k)].iloc[0]
        seg = S[a["segment"]]
        nxt = ev[(ev["segment"] == a["segment"]) & (ev["t_cv_end"] > a["t_cv_end"])].iloc[0]
        d1_a3 = a3.get(pd.Timestamp(a["t_cv_end"]), np.nan)
        d2_a3 = a3.get(pd.Timestamp(nxt["t_cv_end"]), np.nan)
        d1_dl, d1_cells = L.program_dl1(seg, cv_index(seg, a["t_cv_end"]))
        d2_dl, d2_cells = L.program_dl1(seg, cv_index(seg, nxt["t_cv_end"]))
        c_top = A[k]["q_fc"] - A[k]["comb"]
        term3 = float(t3.loc[k, "value_main"]) if k in t3.index else np.nan
        rows.append(dict(anchor_k=k, anchor_event=a["event_id"], T2_event=nxt["event_id"], C_top=c_top,
                         D1_A3=d1_a3, D1_DL1=d1_dl, D2_A3=d2_a3, D2_DL1=d2_dl,
                         Term3_FT2_minus_FA=term3, AT_admissible=bool(k in t3.index),
                         h1_A3=d1_a3 - c_top, h1_DL1=d1_dl - c_top,
                         h2_A3=d2_a3 - c_top - term3, h2_DL1=d2_dl - c_top - term3,
                         **{f"D1_DL1_cell{i + 1}": v for i, v in enumerate(d1_cells)},
                         **{f"D2_DL1_cell{i + 1}": v for i, v in enumerate(d2_cells)}))
    ht = pd.DataFrame(rows)
    ht.to_csv(os.path.join(OUT, "h_table.csv"), index=False, float_format="%.6g")
    meds = {(h, v): L.median_over_k(ht[f"{h}_{v}"].tolist()) for h in ("h1", "h2") for v in ("A3", "DL1")}
    h = L.h_interval(meds)
    split = L.ck0_split(d_cells, c_cells, A[0]["q_fc"], h)
    d_top, d_cv, d_loc = L.combine(d_cells)
    c_bot, c_cv, c_loc = L.combine(c_cells)
    cross = [(L.CK0_Q_AH - d_loc[i]) - c_loc[j] for i in DLN for j in CL]
    # exploratory, NOT registered: h1 from anchor 0's own first program (45 degC top), same arithmetic
    a0e = ev[(ev["type"] == "A") & (ev["anchor_k"] == 0)].iloc[0]
    seg0 = S[a0e["segment"]]
    ct0 = A[0]["q_fc"] - A[0]["comb"]
    d10 = dict(A3=a3.get(pd.Timestamp(a0e["t_cv_end"]), np.nan), DL1=L.program_dl1(seg0, cv_index(seg0, a0e["t_cv_end"]))[0])
    expl = dict(note="exploratory, not registered, not used in any gate or budget: h1_0 = D1_0 - C_top,0 from anchor 0's "
                     "own first program (45 degC), carrying the first-program offset like h1",
                C_top0=ct0, D1_0=d10, h1_0={v: d10[v] - ct0 for v in d10},
                a0_with_h1_0={v: -split["Dbot_minus_Cbot"] - (d10[v] - ct0) for v in d10},
                h_25C_minus_h1_0={v: h["point"] - (d10[v] - ct0) for v in d10})
    res = dict(
        protocol="v1 (wp1/protocol.sha256)",
        D_top_cells=dict(zip([x[:5] for x in L.CELLS], d_cv)), D_top_per_locator=d_loc,
        D_top_variants_by_cell={x[:5]: d for x, d in zip(L.CELLS, d_cells)},
        C_bot_cells=dict(zip([x[:5] for x in L.CELLS], c_cv)), C_bot_per_locator=c_loc,
        Q_fc0=A[0]["q_fc"], eps0_check=dict(eps0=split["eps0"], expected=L.CK0_Q_AH - A[0]["q_fc"]),
        h_medians={f"{a}_{b}": v for (a, b), v in meds.items()}, h=h,
        n_finite_k={f"{a}_{b}": int(np.isfinite(ht[f"{a}_{b}"]).sum()) for a in ("h1", "h2") for b in ("A3", "DL1")},
        split={k: v for k, v in split.items() if k not in ("h",)},
        a0=split["a0"], a0_interval=[split["a0_lo"], split["a0_hi"]], G_B3=split["G_B3"],
        top_split=dict(point=split["top_split"], interval=[split["top_split_lo"], split["top_split_hi"]]),
        descriptive_cross_range_Dbot_minus_Cbot=[float(np.nanmin(cross)), float(np.nanmax(cross))],
        exploratory_not_registered=expl,
        caveats=["CK0 discharges at 5.1 A while the programs' step band is ~10 A",
                 "the checkup temperature is unknown", "anchor 0 charged at 45 degC",
                 "h1 carries the first-program offset; h2 carries Term3 (F^T2 - F^A_k)",
                 "dV/dQ variants are quantisation-limited (wp1/synthetic_resolution.json)"])
    jdump(res, "ck0_split.json")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
    print(ht.drop(columns=[x for x in ht.columns if "_cell" in x]).round(3).to_string())
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    {"b1": b1, "b2": b2, "b3": b3}[sys.argv[1]]()
