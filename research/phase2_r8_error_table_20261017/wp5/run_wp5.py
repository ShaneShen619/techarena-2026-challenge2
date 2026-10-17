"""WP5: registered slicing (protocol.json) -> outputs/slice_summary.csv, H1 diagnostics, H6/H7/H9 tables.
Figures and the worst-20 % dossier: plot_wp5.py."""
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
from common8 import H  # noqa: E402
import slicestats as S  # noqa: E402

OUT = os.path.join(HERE, "outputs")
PROTO = os.path.join(HERE, "protocol.json")
assert hashlib.sha256(open(PROTO, "rb").read()).hexdigest() == open(os.path.join(HERE, "protocol.sha256")).read().split()[0]
P0 = json.load(open(PROTO, encoding="utf-8"))
P = dict(seed=P0["seed"], n_boot=P0["n_boot"], n_perm=P0["n_perm"], exact_perm_max_n=P0["exact_perm_max_n"])
B = P0["bins"]
CELLS = ["cell1_V", "cell2_V", "cell3_V", "cell4_V"]


def load():
    c = pd.read_csv(os.path.join(STUDY, "outputs", "table_cases.csv"))
    c = c[(c.model == "SUB") & (c.delta == 0.4)].reset_index(drop=True)
    c["abs_inc_resid"] = c["inc_resid_Ah"].abs()
    c["fade_pct"] = 100 * c["cum_fade_at_anchor_Ah"] / H.NOM
    c["fade_bin"] = S.bin_of(c["fade_pct"], B["fade_pct"]["edges"], B["fade_pct"]["labels"])
    c["gap_bin"] = S.bin_of(c["gap_days"], B["gap_days"]["edges"], B["gap_days"]["labels"])
    c["dak_bin"] = S.bin_of(c["days_anchor_to_ck"], B["days_anchor_to_ck"]["edges"], B["days_anchor_to_ck"]["labels"])
    c["flag"] = c["uses_first_post_anchor_program"].astype(bool)
    e = pd.read_csv(os.path.join(STUDY, "outputs", "table_events.csv"))
    e["cum_fade_Ah"] = H.Q_CK0 - e["Q_interp_Ah"] - H.EPS0
    e["fade_pct"] = 100 * e["cum_fade_Ah"] / H.NOM
    e["fade_bin"] = S.bin_of(e["fade_pct"], B["fade_pct"]["edges"], B["fade_pct"]["labels"])
    e["switch_bin"] = S.bin_of(e["days_since_switch"], B["days_since_switch"]["edges"], B["days_since_switch"]["labels"])
    e["dT_bin"] = None
    for sp in (25, 45):
        m = e.setpoint == sp
        e.loc[m, "dT_bin"] = S.bin_of(e.loc[m, "dT_at45"], B["dT_at45"]["edges_by_setpoint"][str(sp)], B["dT_at45"]["labels"])
    pk = e.unit == "pack_mean"
    e.loc[pk, "sharp_bin"] = S.bin_of(e.loc[pk, "sharp_height_mV_per_Ah"], B["sharpness_pack"]["edges"], B["sharpness_pack"]["labels"])
    e.loc[~pk, "sharp_bin"] = S.bin_of(e.loc[~pk, "sharp_height_mV_per_Ah"], B["sharpness_cell"]["edges"], B["sharpness_cell"]["labels"])
    e["month_group"] = S.bin_of(e["month"], B["month_group"]["edges"], B["month_group"]["labels"])
    e["R_anc_b"] = r_anc_b(e)
    e["abs_R_seg"] = e["R_seg"].abs()
    a = pd.read_csv(os.path.join(STUDY, "outputs", "table_anchors.csv"))
    y = pd.read_csv(os.path.join(STUDY, "outputs", "table_cycles.csv"))
    return c, e, a, y


def r_anc_b(e):
    """Registered secondary residual: leave-month-out OLS depth = a_25*I25 + a_45*I45 + b*Q_interp, per unit."""
    out = pd.Series(np.nan, index=e.index)
    ok = e["Q_interp_Ah"].notna()
    for unit, g in e[ok].groupby("unit"):
        for i in g.index:
            o = g[g["month"] != g.loc[i, "month"]]
            X = np.column_stack([(o.setpoint == 25).astype(float), (o.setpoint == 45).astype(float), o["Q_interp_Ah"]])
            coef = np.linalg.lstsq(X, o["depth_main"].to_numpy(float), rcond=None)[0]
            x = np.array([g.loc[i, "setpoint"] == 25, g.loc[i, "setpoint"] == 45, g.loc[i, "Q_interp_Ah"]], float)
            out[i] = g.loc[i, "depth_main"] - x @ coef
    return out


def run_slices(c, e, y):
    rows, verd = [], {}

    def add(h, resid, items, subset, slice_, d, ycol, xcol, labcol, hi, lo, block, stratum, expected, thr, orient=1):
        r, s = S.assess(d, ycol, xcol, labcol, hi, lo, block, stratum, expected, thr, P, orient,
                        tag=dict(hypothesis=h, residual=resid, items=items, subset=subset, slice=slice_))
        rows.extend(r)
        verd[(h, resid, subset, slice_)] = r[0]["verdict"]
        return r[0]

    # H1
    cc = c.copy()
    cc["flag_lab"] = cc["flag"].map({True: "flag", False: "other"})
    cc["flag_x"] = cc["flag"].astype(float)
    add("H1", "inc_resid", "cases", "all", "uses_first_post_anchor_program", cc, "inc_resid_Ah", "flag_x", "flag_lab",
        {"flag"}, {"other"}, "k", "branch", -1, 0.10)
    cr = cc[cc.scenario == "real"]
    add("H1", "inc_resid", "cases", "real (descriptive)", "uses_first_post_anchor_program", cr, "inc_resid_Ah", "flag_x",
        "flag_lab", {"flag"}, {"other"}, "k", "branch", -1, 0.10)
    # H2
    pk = e[e.unit == "pack_mean"].copy()
    for sp, sub, d in ((45, "45C direct_switch (primary)", pk[(pk.setpoint == 45) & (pk.switch_kind == "direct_switch")]),
                       (25, "25C (confounded with first program)", pk[pk.setpoint == 25])):
        for resid in ("R_seg", "R_anc", "R_anc_b"):
            if d[resid].notna().sum() < 3:
                continue
            add("H2", resid, "events_pack", sub, "days_since_switch", d, resid, "days_since_switch", "switch_bin",
                {"0-2"}, {">5"}, "month", "setpoint", 1, 0.10, orient=-1)
    # H3
    for resid in ("R_anc", "R_anc_b"):
        add("H3", resid, "events_pack", "pooled, terciles per set point", "dT_at45", pk, resid, "dT_at45", "dT_bin",
            {"high"}, {"low"}, "month", "setpoint", 1, 0.10)
    # H4
    h4 = {}
    add("H4", "inc_resid", "cases", "all", "fade_pct", c, "inc_resid_Ah", "fade_pct", "fade_bin", {">6"}, {"0-3"},
        "k", "branch", -1, 0.10)
    h4["cases"] = S.ols_slope_ci(c, "inc_resid_Ah", "cum_fade_at_anchor_Ah", "k", P)
    h4["cases_without_CK1_anchor0"] = S.ols_slope_ci(c[c.anchor_used > 0], "inc_resid_Ah", "cum_fade_at_anchor_Ah", "k", P)
    for resid in ("R_anc", "R_anc_b"):
        d = pk[pk[resid].notna()]
        add("H4", resid, "events_pack", "all", "fade_pct", d, resid, "fade_pct", "fade_bin", {">6"}, {"0-3"},
            "month", "setpoint", -1, 0.10)
        h4[f"events_{resid}"] = S.ols_slope_ci(d, resid, "cum_fade_Ah", "month", P)
    # H5
    for items, d in (("events_pack", pk), ("events_cell", e[e.unit != "pack_mean"])):
        d = d[d["R_seg"].notna()].copy()
        d["low_lab"] = np.where(d["sharp_bin"] == "low", "low", "mid+high")
        add("H5", "|R_seg|", items, "segments with R_seg", "sharpness", d, "abs_R_seg", "sharp_height_mV_per_Ah",
            "low_lab", {"low"}, {"mid+high"}, "month", "setpoint", 1, 0.10, orient=-1)
    # H8
    for slice_, lab, hi, lo in (("gap_days", "gap_bin", ">10", "0-5"), ("days_anchor_to_ck", "dak_bin", ">30", "0-25")):
        add("H8", "|inc_resid|", "cases", "pooled", slice_, c, "abs_inc_resid", slice_, lab, {hi}, {lo}, "k", "branch", 1, 0.10)
        for br, g in c.groupby("branch"):
            if g[lab].eq(hi).any() and g[lab].eq(lo).any():
                add("H8", "|inc_resid|", "cases", f"branch {br}", slice_, g, "abs_inc_resid", slice_, lab, {hi}, {lo},
                    "k", "branch", 1, 0.10)
            else:
                rows.append(dict(hypothesis="H8", residual="|inc_resid|", items="cases", subset=f"branch {br}", slice=slice_,
                                 bin="EFFECT not computable (one bin only: " + ",".join(sorted(map(str, g[lab].unique()))) + ")",
                                 n=len(g), n_months=g["k"].nunique(), verdict="inconclusive"))
    # H10 / H10b
    ev = e[e.unit == "pack_mean"].sort_values("t_cv_end").reset_index(drop=True)
    first_blocks = {i + 1 for i, f in enumerate(ev["is_first_after_anchor"]) if f}
    y = y.copy()
    y["first_block_lab"] = np.where(y["program_block"].isin(first_blocks), "first_after_anchor", "other")
    y["first_block_x"] = (y["first_block_lab"] == "first_after_anchor").astype(float)
    y["seg_bin"] = S.bin_of(y["hours_since_segment_start"], B["hours_since_segment_start"]["edges"],
                            B["hours_since_segment_start"]["labels"])
    for h, col, thr, exp in (("H10", "R_cyc_slot_top_Ah_rel_last_cv_end", 0.10, 1), ("H10b", "R_cyc_slot_V_bottom_pack", 0.005, -1)):
        add(h, col, "cycles", "all", "first block after anchor", y, col, "first_block_x", "first_block_lab",
            {"first_after_anchor"}, {"other"}, "month", "setpoint", exp, thr)
        y45 = y[y.setpoint == 45]
        add(h, col, "cycles", "45C segments", "hours_since_segment_start", y45, col, "hours_since_segment_start", "seg_bin",
            {"0-48h"}, {">48h"}, "month", "setpoint", exp, thr, orient=-1)
    return rows, verd, h4


def h1_diagnostics(c, a):
    """Diagnostic-only counterfactual increments for cases with uses_first_post_anchor_program (never scored)."""
    from runner5c import SCEN, scenario_tables
    off = a.set_index("anchor")["off_main"]
    out = []
    spec = {(s, k): sp for s in SCEN for k, sp in SCEN[s]}
    for _, r in c[c.flag].iterrows():
        op, fc, st, a4, key = scenario_tables(int(r.k), spec[(r.scenario, int(r.k))])
        s = st["main"].dropna(subset=["step_mean"])
        s = s[s["t_cv_end"] >= pd.Timestamp(r.anchor_t_end)].sort_values("t_cv_end")["step_mean"].to_numpy()
        inc0 = float(s[-1] - s[0])
        assert abs(inc0 - r.increment_pred) < 1e-9
        inc_a = float(s[-1] - s[1]) if len(s) >= 3 else np.nan
        inc_b = float(s[-1] - (s[0] - off[int(r.anchor_used)]))
        inc_c = inc0 / 0.745
        obs = r.increment_obs
        out.append(dict(scenario=r.scenario, k=int(r.k), anchor_used=int(r.anchor_used), n_after=len(s),
                        inc_resid_original=inc0 - obs, inc_resid_a_second_program=inc_a - obs,
                        inc_resid_b_first_minus_3c_offset=inc_b - obs, offset_3c_used=float(off[int(r.anchor_used)]),
                        inc_resid_c_divided_by_b=inc_c - obs, label="diagnostic-only"))
    return pd.DataFrame(out)


def h6(e):
    cells = e[e.unit != "pack_mean"].copy()
    rows = []
    for u, g in cells.groupby("unit"):
        mean = float(g["R_cell"].mean())
        exp = int(np.sign(mean))
        lo, hi, _ = S.block_boot(g, lambda q: float(q["R_cell"].mean()), "month", P["n_boot"], P["seed"])
        bm = g.groupby("month")["R_cell"].mean()
        share = float((np.sign(bm) == exp).mean())
        # block sign-flip test on month means (D5.1)
        vals = bm.to_numpy()
        flips = np.array(np.meshgrid(*[[-1, 1]] * len(vals))).T.reshape(-1, len(vals))
        p = float(np.mean(np.abs((flips * vals).mean(axis=1)) >= abs(vals.mean()) - 1e-12))
        rows.append(dict(hypothesis="H6a", residual="R_cell", items="events_cell", subset=u, slice="per-cell sign",
                         bin="EFFECT mean R_cell", n=len(g), n_months=g["month"].nunique(), mean=mean,
                         median=float(g["R_cell"].median()), ci_lo=lo, ci_hi=hi, sign_agree=int((np.sign(bm) == exp).sum()),
                         sign_n=len(bm), sign_mode="month block means", perm_p=p, perm_mode="block sign-flip exact",
                         expected_sign=exp, threshold=0.10,
                         verdict=S.verdict(mean, lo, hi, share, exp, 0.10) + " [residual seen before registration]"))
    sp = cells.groupby("event_id").agg(spread=("depth_main", lambda s: s.max() - s.min()), month=("month", "first"),
                                       setpoint=("setpoint", "first"))
    sp["mg"] = S.bin_of(sp["month"], B["month_group"]["edges"], B["month_group"]["labels"])
    r, _ = S.assess(sp.reset_index(), "spread", "month", "mg", {"m6-7"}, {"m0-2"}, "month", "setpoint", 1, 0.10, P,
                    tag=dict(hypothesis="H6b", residual="cell depth spread (max-min)", items="events_cell", subset="all",
                             slice="month_group"))
    wk = e[e.unit == "pack_mean"].groupby(["month", "weakest_cell_maxdepth"]).size().unstack(fill_value=0)
    return rows + r, wk, sp


def h7(a, e):
    a1 = a[a.anchor >= 1]
    t1 = S.spearman_exact(a1["anchor"], a1["R_mean_mOhm"])
    t2 = S.spearman_exact(a1["R_mean_mOhm"], a1["cv_Ah"])
    t3 = S.spearman_exact(a1["R_mean_mOhm"], -a1["dQ_cut6A"])
    fit = np.polyfit(a1["R_mean_mOhm"], a1["cv_Ah"], 1)
    cv_change = float(fit[0] * (a1["R_mean_mOhm"].max() - a1["R_mean_mOhm"].min()))
    ev = e[e.unit == "pack_mean"].copy()
    sl = {}
    for sp, g in ev.groupby("setpoint"):
        st = lambda q: S.theil_sen_slope(q["t_days"], q["R_mean_mOhm"])  # noqa: E731
        lo, hi, _ = S.block_boot(g, st, "month", P["n_boot"], P["seed"])
        sl[str(sp)] = dict(theil_sen_mOhm_per_day=st(g), ci90=[lo, hi], n=len(g))
    ok = all(r[0] > 0 and r[1] <= 0.05 for r in (t1, t2, t3)) and cv_change >= 0.10
    v = "systematic" if ok else ("not systematic" if t1[1] > 0.2 else "inconclusive")
    res = dict(spearman_R_vs_anchor=dict(rho=t1[0], p_exact=t1[1], n_perm=t1[2]),
               spearman_cvAh_vs_R=dict(rho=t2[0], p_exact=t2[1]), spearman_minus_dQcut6A_vs_R=dict(rho=t3[0], p_exact=t3[1]),
               cv_Ah_change_across_R_range=cv_change, events_R_trend=sl, verdict=v)
    row = dict(hypothesis="H7", residual="pulse R / CV Ah", items="anchors", subset="anchors 1..7", slice="R_mean_mOhm",
               bin="EFFECT Spearman(R, anchor)", n=len(a1), n_months=len(a1), mean=t1[0], perm_p=t1[1], perm_mode="exact",
               expected_sign=1, threshold=0.10, verdict=v)
    return res, row


def h9(a):
    a1 = a[(a.anchor >= 1) & (a.anchor <= 6)].copy()
    j = a1["anchor"].to_numpy(float)

    def scatter(dq):
        return dq - np.polyval(np.polyfit(j, dq, 1), j)
    nxt = a.set_index("anchor")
    dq = a1["dQ_fc_next"].to_numpy(float)
    dq_cut = a1["dQ_fc_cut6A_next"].to_numpy(float)
    rh = nxt["r_half"]
    dq_rs = dq + np.array([rh[int(k) + 1] - rh[int(k)] for k in j])
    ru = nxt["r_upper"]
    dr = np.array([ru[int(k) + 1] - ru[int(k)] for k in j])
    r0, rc, rs = scatter(dq), scatter(dq_cut), scatter(dq_rs)
    v0 = float(np.var(r0, ddof=1))
    g = float(np.polyfit(dr, r0, 1)[0])
    rf = r0 - g * dr
    loo = []
    for i in range(len(j)):
        m = np.arange(len(j)) != i
        gi = np.polyfit(dr[m], r0[m], 1)[0]
        loo.append(r0[i] - gi * dr[i])
    rho, p, _ = S.spearman_exact(dr, r0)
    ratios = dict(cut6A=float(np.var(rc, ddof=1) / v0), start_state_r_half=float(np.var(rs, ddof=1) / v0),
                  cut6A_plus_r_half=float(np.var(scatter(dq_cut + (dq_rs - dq)), ddof=1) / v0),
                  start_state_fitted_insample=float(np.var(rf, ddof=1) / v0),
                  start_state_fitted_loo=float(np.var(loo, ddof=1) / v0))
    fixed = min(ratios["cut6A"], ratios["start_state_r_half"], ratios["cut6A_plus_r_half"])
    v = ("systematic" if fixed <= 0.5 else "inconclusive" if (fixed <= 0.8 or ratios["start_state_fitted_loo"] <= 0.5)
         else "not systematic")
    res = dict(pairs=[f"{int(k)}->{int(k) + 1}" for k in j], dQ_fc=dq.tolist(), dQ_fc_cut6A=dq_cut.tolist(),
               d_r_upper=dr.tolist(), scatter_sd_before=float(np.sqrt(v0)), g_fitted=g, variance_ratios=ratios,
               spearman_dr_vs_scatter=dict(rho=rho, p_exact=p), pair_0_1=dict(dQ_fc=float(nxt.loc[0, "dQ_fc_next"]),
                                                                          dQ_fc_cut6A=float(nxt.loc[0, "dQ_fc_cut6A_next"])),
               verdict=v)
    row = dict(hypothesis="H9", residual="dQ_fc scatter", items="anchors", subset="25C pairs 1->2..6->7", slice="corrections",
               bin="EFFECT min fixed variance ratio", n=len(j), n_months=len(j), mean=fixed, perm_p=p, perm_mode="exact (Spearman dr)",
               verdict=v)
    return res, row


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    c, e, a, y = load()
    rows, verd, h4 = run_slices(c, e, y)
    r6, weakest, spread = h6(e)
    res7, row7 = h7(a, e)
    res9, row9 = h9(a)
    summary = pd.DataFrame(rows + r6 + [row7, row9])
    summary.to_csv(os.path.join(OUT, "slice_summary.csv"), index=False)
    d1 = h1_diagnostics(c, a)
    d1.to_csv(os.path.join(OUT, "h1_counterfactuals_diagnostic_only.csv"), index=False)
    weakest.to_csv(os.path.join(OUT, "h6_weakest_cell_by_month.csv"))
    spread.to_csv(os.path.join(OUT, "h6_cell_spread_by_event.csv"))
    eps = P0["hypotheses"]["H4"]["eps_drift_slope"]
    h4o = {k: dict(slope=v[0], ci90=[v[1], v[2]], contains_eps_drift=bool(v[1] <= eps <= v[2]),
                   label=("indistinguishable from eps drift, invisible to proxies" if v[1] <= eps <= v[2] else ""))
           for k, v in h4.items()}
    extra = dict(H4_slopes_Ah_per_Ah=h4o, H7=res7, H9=res9)
    json.dump(extra, open(os.path.join(OUT, "wp5_extra.json"), "w"), indent=1, default=float)
    # residual columns added in WP5 (R_anc_b, bins) for the figures and the dossier
    keep = ["event_id", "unit", "R_anc_b", "cum_fade_Ah", "fade_pct", "fade_bin", "switch_bin", "dT_bin", "sharp_bin", "month_group"]
    e[keep].to_csv(os.path.join(OUT, "events_wp5_columns.csv"), index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_rows", 300)
    eff = summary[summary["bin"].astype(str).str.startswith("EFFECT")]
    print(eff[["hypothesis", "residual", "items", "subset", "slice", "n", "n_months", "mean", "ci_lo", "ci_hi", "sign_agree",
               "sign_n", "perm_p", "verdict"]].round(4).to_string())
    print(json.dumps(extra, indent=1, default=float))
    print(d1.round(3).to_string())
    print(weakest)
