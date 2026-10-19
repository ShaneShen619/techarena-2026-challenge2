"""Round 13 registered implementation of wp1/protocol.json.

CV tail models M1-M4 (least squares on I(t) over the CV phase), admission, checkup-termination scenarios C1-C7,
tail drift slopes (Theil-Sen + leave-one-anchor-out), top-state estimators T2/T3, top-up monthly series,
CK0 top-cell comparison and the decision rules. No function here reads P_k or any proxy.
"""
import os
import numpy as np
import pandas as pd
from scipy import optimize, stats

MODELS = ("M1", "M2", "M3", "M4")
SCENARIOS = ("C1", "C2", "C3", "C4", "C5", "C6", "C7")
I_CUT = {"C2": 2.55, "C3": 1.02, "C4": 0.51}
HOLD_S = {"C5": 1800.0, "C6": 3600.0, "C7": 7200.0}
RMSE_MAX, LAST_THIRD_MAX = 0.15, 0.10
FADE_CK7 = 8.2                       # Ah, pack fade CK0 -> CK7 (round 11 convention)
ANCHORS = (1, 2, 3, 4, 5, 6, 7)
REF = 1
CELLS = ("cell1", "cell2", "cell3", "cell4")
S_TOP_MAIN, S_TOP_SENS = (0.5, 2.0), ((0.25, 1.0), (1.0, 3.0))
SEG_TO_MONTH = {2: 1, 4: 2, 6: 3, 8: 4, 10: 5, 12: 6, 14: 7}
I_PULSE_REF = 5.1                    # A, C/20 current used in T3
TOL = 1e-9

# ---------------------------------------------------------------- models
# Each model: current(p, t) [A], integral(p, a, b) [A*s], t_cut(p, Ic) -> time where I = Ic (0 if already below at t = 0)
# or None if the model never reaches Ic. Parameters are in natural form (M4: A1, tau1, A2, tau2).


def current(m, p, t):
    t = np.asarray(t, float)
    if m == "M1":
        return p[0] * np.exp(-t / p[1])
    if m == "M2":
        return p[0] + p[1] * np.exp(-t / p[2])
    if m == "M3":
        return p[0] / np.sqrt(np.maximum(t + p[1], 1e-9))
    if m == "M4":
        return p[0] * np.exp(-t / p[1]) + p[2] * np.exp(-t / p[3])
    raise ValueError(m)


def integral(m, p, a, b):
    """Integral of the model current from a to b (s), in A*s."""
    if m == "M1":
        return p[0] * p[1] * (np.exp(-a / p[1]) - np.exp(-b / p[1]))
    if m == "M2":
        return p[0] * (b - a) + p[1] * p[2] * (np.exp(-a / p[2]) - np.exp(-b / p[2]))
    if m == "M3":
        return 2.0 * p[0] * (np.sqrt(max(b + p[1], 1e-9)) - np.sqrt(max(a + p[1], 1e-9)))
    if m == "M4":
        return (p[0] * p[1] * (np.exp(-a / p[1]) - np.exp(-b / p[1]))
                + p[2] * p[3] * (np.exp(-a / p[3]) - np.exp(-b / p[3])))
    raise ValueError(m)


def t_cut(m, p, ic):
    if float(current(m, p, 0.0)) <= ic:
        return 0.0
    if m == "M1":
        return p[1] * np.log(p[0] / ic)
    if m == "M2":
        if p[0] >= ic:
            return None
        return p[2] * np.log(p[1] / (ic - p[0]))
    if m == "M3":
        return max((p[0] / ic) ** 2 - p[1], 0.0)
    if m == "M4":
        hi = 1.0
        while float(current(m, p, hi)) > ic:
            hi *= 2.0
            if hi > 1e13:
                return None
        return optimize.brentq(lambda x: float(current(m, p, x)) - ic, 0.0, hi, xtol=1e-9, rtol=1e-14, maxiter=500)
    raise ValueError(m)


def q_tail(m, p, t_end, scen):
    """Q_tail in Ah from the anchor's CV end t_end to the scenario's end; (value, defined)."""
    if scen == "C1":
        return 0.0, True
    if scen in HOLD_S:
        return float(integral(m, p, t_end, t_end + HOLD_S[scen]) / 3600.0), True
    tc = t_cut(m, p, I_CUT[scen])
    if tc is None:
        return np.nan, False
    return float(integral(m, p, t_end, max(t_end, tc)) / 3600.0), True


# ---------------------------------------------------------------- fitting

def _setup(m, t, I, i_end):
    i0 = float(I[0])
    if m == "M1":
        lb, ub = [0.0, 1.0], [1e4, 1e6]
        starts = [[i0, tau] for tau in (100.0, 300.0, 1000.0)]
        to_nat = lambda x: list(x)
    elif m == "M2":
        lb, ub = [0.0, 0.0, 1.0], [max(i_end, 1e-12), 1e4, 1e6]
        starts = [[f * i_end, max(i0 - f * i_end, 0.0), tau] for f in (0.0, 0.5, 0.9) for tau in (50.0, 150.0, 400.0)]
        to_nat = lambda x: list(x)
    elif m == "M3":
        lb, ub = [0.0, 0.0], [1e6, 1e7]
        starts = [[i0 * np.sqrt(t0), t0] for t0 in (1.0, 30.0, 300.0, 3000.0)]
        to_nat = lambda x: list(x)
    elif m == "M4":
        lb, ub = [0.0, 1.0, 0.0, 0.0], [1e4, 1e5, 1e4, 1e6]
        starts = [[f * i0, tau1, (1 - f) * i0, (r - 3.0) * tau1]
                  for tau1 in (10.0, 30.0, 100.0) for r in (3.0, 10.0, 30.0) for f in (0.3, 0.5, 0.7)]
        to_nat = lambda x: [x[0], x[1], x[2], 3.0 * x[1] + x[3]]
    else:
        raise ValueError(m)
    return np.array(lb), np.array(ub), starts, to_nat


def fit(m, t, I, i_end=None):
    """Least-squares fit of model m to (t, I). Returns a dict with natural parameters, RMSE, last-third residual,
    convergence and admission."""
    t = np.asarray(t, float); I = np.asarray(I, float)
    i_end = float(I[-1]) if i_end is None else float(i_end)
    lb, ub, starts, to_nat = _setup(m, t, I, i_end)

    def res(x):
        return current(m, to_nat(x), t) - I

    best = None
    for x0 in starts:
        x0 = np.clip(np.asarray(x0, float), lb, ub)
        try:
            r = optimize.least_squares(res, x0, bounds=(lb, ub), method="trf", x_scale="jac",
                                       ftol=1e-12, xtol=1e-12, gtol=1e-12, max_nfev=20000)
        except Exception:
            continue
        if best is None or r.cost < best.cost:
            best = r
    if best is None:
        return dict(model=m, params=None, rmse=np.nan, last_third=np.nan, converged=False, admitted=False)
    p = to_nat(best.x)
    r = current(m, p, t) - I
    rmse = float(np.sqrt(np.mean(r ** 2)))
    lt = float(np.mean(r[t >= (2.0 / 3.0) * t[-1]]))
    conv = bool(best.status > 0)
    adm = conv and round(rmse, 9) <= RMSE_MAX and round(abs(lt), 9) <= LAST_THIRD_MAX
    return dict(model=m, params=[float(v) for v in p], rmse=rmse, last_third=lt, converged=conv, admitted=bool(adm),
                at_bound=bool(np.any(np.isclose(best.x, lb, rtol=0, atol=1e-9) | np.isclose(best.x, ub, rtol=1e-9, atol=0))))


PARAM_NAMES = {"M1": ("A", "tau"), "M2": ("Iinf", "A", "tau"), "M3": ("A", "t0"), "M4": ("A1", "tau1", "A2", "tau2")}

# ---------------------------------------------------------------- slopes and decision


def theil_sen(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    if len(x) < 2:
        return np.nan
    return float(stats.theilslopes(y, x)[0])


def slope_loo(x, y):
    """Theil-Sen slope and its leave-one-out range [min, max]."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    s = theil_sen(x, y)
    loo = [theil_sen(np.delete(x, i), np.delete(y, i)) for i in range(len(x))]
    return s, float(np.nanmin(loo)), float(np.nanmax(loo))


def decide(members):
    """members: {name: {"slope", "loo_min", "loo_max"}} in Ah/Ah, including "C1" and "T2". Registered rules."""
    v = {n: round(m["slope"] * FADE_CK7, 9) for n, m in members.items()}
    lo = {n: round(m["loo_min"] * FADE_CK7, 9) for n, m in members.items()}
    hi = {n: round(m["loo_max"] * FADE_CK7, 9) for n, m in members.items()}
    env = round(max(v.values()) - min(v.values()), 9)
    others = [n for n in members if n != "C1"]
    d_tail = float(np.median([members[n]["slope"] for n in others])) if others else 0.0
    med_abs = float(np.median([abs(v[n]) for n in others])) if others else 0.0
    out = dict(envelope_Ah=env, identifiable=bool(env <= 0.30), d_tail=d_tail, median_abs_effect_Ah_without_C1=med_abs,
               effects_Ah=v, loo_Ah={n: [lo[n], hi[n]] for n in members})
    if env > 0.30:
        return dict(out, outcome="O3", label="not identifiable")
    if all(abs(x) <= 0.10 for x in v.values()) and all(lo[n] >= -0.15 and hi[n] <= 0.15 for n in members):
        return dict(out, outcome="O1", label="tail drift small")
    same = others and (all(v[n] > 0 for n in others) or all(v[n] < 0 for n in others))
    if same and med_abs > 0.10:
        return dict(out, outcome="O2", label="tail drift material")
    return dict(out, outcome="O3", label="inconclusive")


# ---------------------------------------------------------------- data access

class Segments:
    """Lazy reader of the operating segment files."""

    def __init__(self, data_dir):
        self.dir = os.path.join(data_dir, "operation"); self.cache = {}

    def get(self, seg):
        if seg not in self.cache:
            f = [x for x in os.listdir(self.dir) if x.startswith(f"segment_{seg:02d}_")][0]
            self.cache[seg] = pd.read_csv(os.path.join(self.dir, f))
        return self.cache[seg]


def cv_trace(segs, row):
    """(t, I) of a catalogue row's CV phase: samples with CV start <= elapsed <= CV end that belong to the charge step."""
    d = segs.get(int(row.segment))
    m = (d.elapsed_s >= row.elapsed_cv_start_s) & (d.elapsed_s <= row.elapsed_cv_end_s) & (d.current_A >= 1.0)
    w = d[m]
    return (w.elapsed_s.to_numpy(float) - float(row.elapsed_cv_start_s)), w.current_A.to_numpy(float)


def pulse_cells(segs, row):
    """Per-cell voltages at the first sample of the 20 A pulse after the +30 min rest (10 s into the pulse)."""
    d = segs.get(int(row.segment))
    after = d[d.elapsed_s > row.elapsed_cv_end_s]
    k = np.flatnonzero(after.current_A.to_numpy(float) < -15.0)
    if len(k) < 2:
        return {c: np.nan for c in CELLS}
    r = after.iloc[k[1]]
    return {c: float(r[f"{c}_V"]) for c in CELLS}


def s_top(data_dir, window, col="voltage_V"):
    ck = pd.read_csv(os.path.join(data_dir, "checkups", "CK0_reference_discharge.csv.gz"))
    m = (ck.discharged_Ah >= window[0]) & (ck.discharged_Ah <= window[1])
    return float(-np.polyfit(ck.discharged_Ah[m], ck[col][m], 1)[0])


def fade_table(study_dir):
    p = pd.read_csv(os.path.join(study_dir, "sources", "r11_wp4_pack_drivers.csv"))
    p = p[p.anchor.isin(ANCHORS)].set_index("anchor")
    return (p.Q_fc.loc[REF] - p.Q_fc).rename("fade")


# ---------------------------------------------------------------- measurements (WP2)

def fit_all(study_dir, data_dir):
    """Fit M1-M4 to every full charge in wp0/cv_catalogue.csv. Returns (fits, tails, traces)."""
    cat = pd.read_csv(os.path.join(study_dir, "wp0", "cv_catalogue.csv"))
    segs = Segments(data_dir)
    fits, tails, traces = [], [], {}
    for row in cat.itertuples():
        t, I = cv_trace(segs, row)
        traces[row.event_id] = (t, I)
        t_end = float(t[-1])
        for m in MODELS:
            f = fit(m, t, I, i_end=row.I_cv_end)
            rec = dict(event_id=row.event_id, segment=row.segment, setpoint_C=row.setpoint_C, type=row.type,
                       anchor=row.anchor, model=m, n_cv=len(t), t_end_s=t_end, I_end=row.I_cv_end, rmse=f["rmse"],
                       last_third_mean_resid=f["last_third"], converged=f["converged"], at_bound=f.get("at_bound", False),
                       admitted=f["admitted"])
            for i, nm in enumerate(PARAM_NAMES[m]):
                rec[nm] = f["params"][i] if f["params"] is not None else np.nan
            if m == "M1" and f["params"] is not None:
                rec["Iend_x_tau_Ah"] = float(row.I_cv_end * f["params"][1] / 3600.0)
            fits.append(rec)
            for c in SCENARIOS:
                q, ok = q_tail(m, f["params"], t_end, c) if f["params"] is not None else (np.nan, False)
                tails.append(dict(event_id=row.event_id, segment=row.segment, setpoint_C=row.setpoint_C, type=row.type,
                                  anchor=row.anchor, model=m, scenario=c, admitted=f["admitted"], defined=ok,
                                  usable=bool(f["admitted"] and ok), Q_tail_Ah=q))
    return pd.DataFrame(fits), pd.DataFrame(tails), traces


def anchor_drift(tails, fade):
    """Delta_tail per anchor and the (M, C) drift slopes. Returns (tails with Delta_tail, pair table)."""
    a = tails[(tails.type == "A") & tails.anchor.notna()].copy()
    a["anchor"] = a.anchor.astype(float).astype(int)
    a = a[a.anchor.isin(ANCHORS)]
    rows, deltas = [], []
    for (m, c), g in a.groupby(["model", "scenario"], sort=False):
        g = g.set_index("anchor").sort_index()
        ref_ok = bool(g.usable.get(REF, False))
        use = [k for k in ANCHORS if bool(g.usable.get(k, False))]
        n26 = len([k for k in use if k != REF])
        q1 = g.Q_tail_Ah.loc[REF] if ref_ok else np.nan
        for k in ANCHORS:
            deltas.append(dict(model=m, scenario=c, anchor=k, Delta_tail_Ah=(g.Q_tail_Ah.loc[k] - q1) if (ref_ok and k in use) else np.nan))
        member = ref_ok and n26 >= 5
        x = fade.loc[use].to_numpy(float); y = (g.Q_tail_Ah.loc[use] - (q1 if ref_ok else 0.0)).to_numpy(float)
        s, lo, hi = slope_loo(x, y) if len(use) >= 3 else (np.nan, np.nan, np.nan)
        # sensitivity without the anchor-1 requirement (slope of Q_tail on fade over all usable anchors)
        rows.append(dict(model=m, scenario=c, member_of_A=bool(member) if c != "C1" else False, ref_admitted_defined=ref_ok,
                         n_usable_2_7=n26, usable_anchors=",".join(map(str, use)), slope=s if member or c == "C1" else np.nan,
                         loo_min=lo if member or c == "C1" else np.nan, loo_max=hi if member or c == "C1" else np.nan,
                         slope_sensitivity_no_ref_req=s, effect_CK7_Ah=(s * FADE_CK7) if (member or c == "C1") else np.nan))
    d = pd.DataFrame(deltas)
    return a.merge(d, on=["model", "scenario", "anchor"], how="left"), pd.DataFrame(rows)


def top_state(study_dir, data_dir):
    """T2 (pack and per cell, three windows) and T3 per anchor 1..7, plus their slopes."""
    cat = pd.read_csv(os.path.join(study_dir, "wp0", "cv_catalogue.csv"))
    a = cat[cat.type == "A"].copy(); a["anchor"] = a.anchor.astype(int)
    a = a[a.anchor.isin(ANCHORS)].set_index("anchor").sort_index()
    fade = fade_table(study_dir).loc[list(ANCHORS)]
    wins = {"main": S_TOP_MAIN, "w025_1": S_TOP_SENS[0], "w1_3": S_TOP_SENS[1]}
    units = {"pack": ("V_pack_30", "voltage_V")}
    units.update({c: (f"{c}_30", f"{c}_V") for c in CELLS})
    rows, slopes, s_vals = [], [], {}
    for u, (vcol, ccol) in units.items():
        for wn, w in wins.items():
            s = s_top(data_dir, w, ccol); s_vals[(u, wn)] = s
            dF = (a[vcol] - a[vcol].loc[REF]) / s
            de = -dF
            for k in ANCHORS:
                rows.append(dict(estimator="T2", unit=u, window=wn, s_top_V_per_Ah=s, anchor=k, fade_Ah=fade.loc[k],
                                 V30=a[vcol].loc[k], dF_Ah=dF.loc[k], d_eps_Ah=de.loc[k]))
            sl, lo, hi = slope_loo(fade.to_numpy(float), de.to_numpy(float))
            slopes.append(dict(estimator="T2", unit=u, window=wn, s_top_V_per_Ah=s, slope=sl, loo_min=lo, loo_max=hi,
                               effect_CK7_Ah=sl * FADE_CK7, member_of_A=bool(u == "pack" and wn == "main")))
    s = s_vals[("pack", "main")]
    R = a.R_pulse_mOhm_r8_pack / 1000.0
    dF = -I_PULSE_REF * (R - R.loc[REF]) / s
    de = -dF
    for k in ANCHORS:
        rows.append(dict(estimator="T3", unit="pack", window="main", s_top_V_per_Ah=s, anchor=k, fade_Ah=fade.loc[k],
                         R_pack_mOhm=a.R_pulse_mOhm_r8_pack.loc[k], dF_Ah=dF.loc[k], d_eps_Ah=de.loc[k]))
    sl, lo, hi = slope_loo(fade.to_numpy(float), de.to_numpy(float))
    slopes.append(dict(estimator="T3", unit="pack", window="main", s_top_V_per_Ah=s, slope=sl, loo_min=lo, loo_max=hi,
                       effect_CK7_Ah=sl * FADE_CK7, member_of_A=False))
    top = pd.DataFrame(dict(anchor=list(ANCHORS),
                            top_cell_end=[a.top_cell_end.loc[k] for k in ANCHORS],
                            top_cell_30=[a.top_cell_30.loc[k] for k in ANCHORS]))
    return pd.DataFrame(rows), pd.DataFrame(slopes), top


def topup_monthly(tails, fade):
    """Median Q_tail over each month's admitted, defined 25 C top-ups, and a descriptive slope against fade."""
    t = tails[(tails.type == "T") & (tails.setpoint_C == 25) & tails.usable].copy()
    t["month"] = t.segment.map(SEG_TO_MONTH)
    med = t.groupby(["model", "scenario", "month"]).agg(Q_tail_median_Ah=("Q_tail_Ah", "median"),
                                                         n_topups=("Q_tail_Ah", "size")).reset_index()
    sl = []
    for (m, c), g in med.groupby(["model", "scenario"], sort=False):
        g = g[g.month.isin(ANCHORS)].sort_values("month")
        if len(g) >= 3:
            s, lo, hi = slope_loo(fade.loc[g.month].to_numpy(float), g.Q_tail_median_Ah.to_numpy(float))
        else:
            s = lo = hi = np.nan
        sl.append(dict(model=m, scenario=c, n_months=len(g), slope=s, loo_min=lo, loo_max=hi, effect_CK7_Ah=s * FADE_CK7))
    return med, pd.DataFrame(sl)


def ck0_comparison(study_dir, data_dir):
    cat = pd.read_csv(os.path.join(study_dir, "wp0", "cv_catalogue.csv"))
    segs = Segments(data_dir)
    ck = pd.read_csv(os.path.join(data_dir, "checkups", "CK0_reference_discharge.csv.gz")).iloc[0]
    rows = [dict(case="CK0 first C/20 sample (5.1 A)", anchor="", **{c: float(ck[f"{c}_V"]) for c in CELLS})]
    for row in cat[cat.type == "A"].itertuples():
        rows.append(dict(case="anchor CV end (5.1 A, 14.0 V)", anchor=int(row.anchor), **{c: getattr(row, f"{c}_end") for c in CELLS}))
        rows.append(dict(case="anchor +30 min rest", anchor=int(row.anchor), **{c: getattr(row, f"{c}_30") for c in CELLS}))
        rows.append(dict(case="anchor 20 A pulse, first sample", anchor=int(row.anchor), **pulse_cells(segs, row)))
    d = pd.DataFrame(rows)
    v = d[list(CELLS)].to_numpy(float)
    d["top_cell"] = [CELLS[int(np.nanargmax(r))] for r in v]
    d["top_minus_second_mV"] = [float((np.sort(r)[-1] - np.sort(r)[-2]) * 1000) for r in v]
    return d


def admitted_set(pairs, t2_slopes):
    """Members of A: usable (M, C) pairs, T2 (pack, main window), C1."""
    mem = {"C1": dict(slope=0.0, loo_min=0.0, loo_max=0.0)}
    t2 = t2_slopes[(t2_slopes.estimator == "T2") & t2_slopes.member_of_A].iloc[0]
    mem["T2"] = dict(slope=float(t2.slope), loo_min=float(t2.loo_min), loo_max=float(t2.loo_max))
    for r in pairs[pairs.member_of_A].itertuples():
        mem[f"{r.model}/{r.scenario}"] = dict(slope=float(r.slope), loo_min=float(r.loo_min), loo_max=float(r.loo_max))
    return mem
