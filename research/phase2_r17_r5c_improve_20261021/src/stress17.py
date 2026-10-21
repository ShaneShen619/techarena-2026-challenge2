"""Round-17 stress-table extensions (EXECUTION_PROMPT.md WP0 F1/F2, WP2 designs B0/S/O2).

* ``soc_series``   causal pack SOC per operation row: Ah below the latest CV end (reset at every
                   ``events._cv_ends`` event; rows before a segment's first CV end use that CV end),
                   SOC = 1 - Ah_below / Q_ref, Q_ref = latest visible anchor capacity (Q_CK0 before any).
* ``stress_table17`` = ``stress.stress_table`` plus
    - ``ck_class`` on every hidden 25 C row: ``true_ck`` (interval contains a CK date) or ``switch``;
    - ``switch_fix``: switch rows get kind "switch" and the mean of the bounding rows' cell temperatures;
    - ``soc``/``w`` columns (time-weighted SOC and time-weighted w(SOC)) when ``wfun`` is given, with the
      registered rules for hidden rows (switch = SOC at the last row of the earlier segment; true_ck =
      entry SOC / 0 % split by ``ck_soc``; seg_gap / extrapolated = mean over the last visible 45 C segment).
With ``switch_fix=False`` and ``wfun=None`` the rows equal ``stress.stress_table`` exactly (checked in WP0).
"""
import numpy as np
import pandas as pd

from events import _cv_ends, segment_arrays
from smodel import Q_CK0, anchors
from stress import DAY_S, _uniform, segment_summary, visible_rules

NOM = 102.0


def contains_ck_day(ck, t0, t1):
    """A CK date is a calendar day: the interval holds it if [t0, t1] overlaps [CK, CK + 1 day)."""
    ck = pd.DatetimeIndex(ck)
    return bool(((ck <= t1) & (ck + pd.Timedelta(days=1) > t0)).any())


def soc_series(op, fc, ck):
    """SOC per row of ``op`` (same order); NaN only if a segment has no visible CV end."""
    anc = anchors(fc, pd.DatetimeIndex(ck))
    at = sorted((v[0], v[1]) for v in anc.values())
    a_t = np.array([pd.Timestamp(t).value for t, _ in at], dtype=np.int64)
    a_q = np.array([q for _, q in at], float)
    out = np.full(len(op), np.nan)
    pos = 0
    for seg, g in op.groupby("segment", sort=True):
        idx = op.index.get_indexer(g.index)
        _, cur, ah = segment_arrays(g)
        pack = g["pack_voltage_V"].to_numpy(float)
        ends = _cv_ends(cur, pack)
        below = np.full(len(g), np.nan)
        if len(ends):
            ref = np.searchsorted(ends, np.arange(len(g)), side="right") - 1
            ref_idx = np.where(ref >= 0, ends[np.clip(ref, 0, None)], ends[0])
            below = ah[ref_idx] - ah
        tv = g["timestamp"].to_numpy().astype("datetime64[ns]").astype(np.int64)
        j = np.searchsorted(a_t, tv, side="right") - 1
        qref = np.where(j >= 0, a_q[np.clip(j, 0, None)] if len(a_q) else Q_CK0, Q_CK0)
        out[idx] = np.clip(1.0 - below / qref, 0.0, 1.0)
        pos += len(g)
    return out


def _observed17(op, wfun):
    """``stress._observed`` plus time-weighted soc and w(soc) per hourly bin."""
    out = []
    for seg, g in op.groupby("segment", sort=True):
        if len(g) < 2:
            continue
        t = g["timestamp"].to_numpy()
        ts = g["elapsed_s"].to_numpy(float)
        temp = g["temp_mean_C"].to_numpy(float)
        ctr = (g["charge_Ah_cum"] + g["discharge_Ah_cum"]).to_numpy(float)
        dt = np.diff(ts)
        thr = np.clip(np.diff(ctr), 0.0, None)
        tm = 0.5 * (temp[1:] + temp[:-1])
        tstart = pd.DatetimeIndex(t[:-1])
        b = tstart.floor("h")
        cols = {"bin": b, "dt": dt, "thr": thr, "Tdt": tm * dt, "Tthr": tm * thr}
        if wfun is not None:
            s = g["soc"].to_numpy(float)
            sm = 0.5 * (s[1:] + s[:-1])
            ok = np.isfinite(sm)
            cols.update(sdt=np.where(ok, sm * dt, 0.0), wdt=np.where(ok, wfun(np.nan_to_num(sm)) * dt, 0.0),
                        okdt=np.where(ok, dt, 0.0))
        agg = pd.DataFrame(cols).groupby("bin", sort=True).sum()
        first_t = pd.Series(tstart).groupby(b.values).min()
        t1 = list(first_t.iloc[1:]) + [pd.Timestamp(t[-1])]
        pos = agg["dt"] > 0
        T_time = np.where(pos, agg["Tdt"] / np.where(pos, agg["dt"], 1), np.nan)
        T_thr = np.where(agg["thr"] > 0, agg["Tthr"] / np.where(agg["thr"] > 0, agg["thr"], 1), T_time)
        d = dict(t0=list(first_t), t1=t1, days=agg["dt"].to_numpy() / DAY_S, T_time=T_time, T_thr=T_thr,
                 thr_Ah=agg["thr"].to_numpy(), segment=seg, setpoint=int(g["chamber_temperature_C"].iloc[0]),
                 kind="observed", ck_class="")
        if wfun is not None:
            okd = agg["okdt"].to_numpy()
            d["soc"] = np.where(okd > 0, agg["sdt"] / np.where(okd > 0, okd, 1), np.nan)
            d["w"] = np.where(okd > 0, agg["wdt"] / np.where(okd > 0, okd, 1), np.nan)
        out.append(pd.DataFrame(d))
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def _row(t0, t1, T, thr, kind, ck_class, soc=np.nan, w=np.nan):
    r = _uniform(t0, t1, T, thr, kind)
    r.update(ck_class=ck_class, soc=soc, w=w)
    return r


def _ck_rows(t0, t1, T, thr, kind, ck_soc, s_entry, wfun):
    """A true-checkup interval; with a SOC model split into halves (entry SOC first, then 0 %)."""
    if wfun is None:
        return [_row(t0, t1, T, thr, kind, "true_ck")]
    socs = {"half": (s_entry, 0.0), "entry": (s_entry, s_entry), "zero": (0.0, 0.0)}[ck_soc]
    tm = t0 + (t1 - t0) / 2
    return [_row(t0, tm, T, thr / 2, kind, "true_ck", socs[0], float(wfun(socs[0]))),
            _row(tm, t1, T, thr / 2, kind, "true_ck", socs[1], float(wfun(socs[1])))]


def stress_table17(op, until, ck, horizon=None, checkup_Ah=0.0, rate_days=7.0, T_checkup=25.0,
                   switch_fix=False, wfun=None, ck_soc="half"):
    ck = pd.DatetimeIndex(ck)
    horizon = pd.Timestamp(until if horizon is None else horizon)
    k_cut = int((ck <= pd.Timestamp(until)).sum()) - 1
    obs = _observed17(op, wfun)
    seg = segment_summary(op)
    ends = op.groupby("segment").agg(Tl=("temp_mean_C", "last"), Tf=("temp_mean_C", "first"))
    if wfun is not None:
        lastsoc = op.groupby("segment")["soc"].agg(lambda s: s.dropna().iloc[-1] if s.notna().any() else np.nan)
        s45 = seg[seg["sp"] == 45].index.max()
        o = obs[obs["segment"] == s45]
        okd = o["days"].where(o["w"].notna(), 0.0)
        gap_soc = float((o["soc"].fillna(0) * okd).sum() / max(okd.sum(), 1e-12))
        gap_w = float((o["w"].fillna(0) * okd).sum() / max(okd.sum(), 1e-12))
    else:
        lastsoc, gap_soc, gap_w = None, np.nan, np.nan
    rules = visible_rules(op, ck, max(k_cut, 0), rate_days)
    rows = []
    segs = list(seg.index)
    for a, b in zip(segs[:-1], segs[1:]):
        ta, tb = seg.loc[a, "t1"], seg.loc[b, "t0"]
        jump = (seg.loc[b, "c0"] - seg.loc[a, "c1"]) + (seg.loc[b, "d0"] - seg.loc[a, "d1"])
        s_a = float(lastsoc.loc[a]) if lastsoc is not None else np.nan
        if b == a + 1:
            thr = checkup_Ah if seg.loc[a, "sp"] == 45 else 0.0
            has_ck = contains_ck_day(ck, ta, tb)
            if has_ck:
                rows += _ck_rows(ta, tb, T_checkup, thr, "checkup", ck_soc, s_a, wfun)
            else:
                T = 0.5 * (ends.loc[a, "Tl"] + ends.loc[b, "Tf"]) if switch_fix else T_checkup
                rows.append(_row(ta, tb, T, thr, "switch" if switch_fix else "checkup", "switch", s_a,
                                 float(wfun(s_a)) if wfun is not None else np.nan))
        else:
            m = int((ck < tb).sum()) - 1
            t_end = ck[m] + pd.Timedelta(hours=rules["end_off_h"])
            t_end = min(max(t_end, ta), tb)
            rows.append(_row(ta, t_end, 45.0 + rules["offset45"], jump, "seg_gap", "", gap_soc, gap_w))
            rows += _ck_rows(t_end, tb, T_checkup, checkup_Ah, "checkup", ck_soc, gap_soc, wfun)
    t_last = op["timestamp"].max()
    if horizon > t_last:
        m_next = int((ck < t_last).sum())
        if m_next < len(ck):
            t_mend = ck[m_next] + pd.Timedelta(hours=rules["end_off_h"])
            t_mend = min(max(t_mend, t_last), horizon)
        else:
            t_mend = horizon
        if t_mend > t_last:
            d = (t_mend - t_last).total_seconds() / DAY_S
            rows.append(_row(t_last, t_mend, 45.0 + rules["offset45"], rules["rate45"] * d, "extrapolated", "",
                             gap_soc, gap_w))
        if horizon > t_mend:
            thr = checkup_Ah if m_next < len(ck) else 0.0
            # entry state of the hidden checkup: the extrapolated 45 C month end
            rows += _ck_rows(t_mend, horizon, T_checkup, thr, "checkup", ck_soc, gap_soc, wfun)
    tab = pd.concat([obs, pd.DataFrame(rows)], ignore_index=True) if rows else obs
    tab = tab.sort_values("t0").reset_index(drop=True)
    tab = tab[tab["t0"] < horizon].copy()
    over = tab["t1"] > horizon
    if over.any():
        f = ((horizon - tab.loc[over, "t0"]).dt.total_seconds() /
             (tab.loc[over, "t1"] - tab.loc[over, "t0"]).dt.total_seconds().clip(lower=1e-9))
        tab.loc[over, "days"] *= f
        tab.loc[over, "thr_Ah"] *= f
        tab.loc[over, "t1"] = horizon
    tab["t0"] = pd.to_datetime(tab["t0"]).dt.as_unit("ns")
    tab["t1"] = pd.to_datetime(tab["t1"]).dt.as_unit("ns")
    tab.attrs["rules"] = rules
    return tab


# ------------------------------------------------------------------ clocks
R_GAS = 8.314462618


def _interp_cum(tab, d, t_eval):
    """Cumulative of per-row increments ``d`` at times ``t_eval`` (linear inside a row)."""
    t0 = tab["t0"].astype("int64").to_numpy() / 1e9
    t1 = tab["t1"].astype("int64").to_numpy() / 1e9
    c = np.r_[0.0, np.cumsum(d)]
    te = np.atleast_1d(pd.DatetimeIndex(t_eval).as_unit("ns").asi8 / 1e9)
    out = []
    for x in te:
        i = np.searchsorted(t1, x, side="left")
        if i >= len(t1):
            out.append(c[-1]); continue
        f = min(max((x - t0[i]) / max(t1[i] - t0[i], 1e-9), 0.0), 1.0)
        out.append(c[i] + f * d[i])
    return np.array(out)


def clock(tab, Ea_J, t_eval, weight=None, T_ref_K=298.15):
    """Arrhenius-weighted (on time) days, optionally times a per-row weight, at ``t_eval``."""
    aT = np.exp(-Ea_J / R_GAS * (1.0 / (tab["T_time"].to_numpy(float) + 273.15) - 1.0 / T_ref_K))
    days = tab["days"].to_numpy(float)
    d = np.where(days > 0, days * np.nan_to_num(aT, nan=1.0), 0.0)
    if weight is not None:
        d = d * weight
    return _interp_cum(tab, d, t_eval)


def overhang_state(tab, t_eval, soc0, soc_op, ea_tau_J, t_full_ref_d, T_full_ref_C, x0=0.0, tau_div=3.0):
    """Unit-amplitude overhang state X(t): dX/dt = (xe - X)/tau(T), xe = (soc - soc0)/(soc_op - soc0).

    tau(T) = t_full(T)/tau_div with t_full(T) = t_full_ref exp(Ea/R (1/T - 1/T_ref)). Exact exponential
    update per row; linear-in-time interpolation of the exponential inside the row at evaluation times.
    """
    T = tab["T_time"].to_numpy(float)
    T = np.where(np.isfinite(T), T, 25.0)
    tau = t_full_ref_d * np.exp(ea_tau_J / R_GAS * (1 / (T + 273.15) - 1 / (T_full_ref_C + 273.15))) / tau_div
    soc = tab["soc"].to_numpy(float)
    soc = np.where(np.isfinite(soc), soc, soc_op)
    xe = (soc - soc0) / (soc_op - soc0)
    days = tab["days"].to_numpy(float)
    X = np.empty(len(tab) + 1)
    X[0] = x0
    for i in range(len(tab)):
        X[i + 1] = xe[i] + (X[i] - xe[i]) * np.exp(-max(days[i], 0.0) / tau[i])
    t0 = tab["t0"].astype("int64").to_numpy() / 1e9
    t1 = tab["t1"].astype("int64").to_numpy() / 1e9
    te = np.atleast_1d(pd.DatetimeIndex(t_eval).as_unit("ns").asi8 / 1e9)
    out = []
    for x in te:
        i = np.searchsorted(t1, x, side="left")
        if i >= len(t1):
            out.append(X[-1]); continue
        f = min(max((x - t0[i]) / max(t1[i] - t0[i], 1e-9), 0.0), 1.0)
        out.append(xe[i] + (X[i] - xe[i]) * np.exp(-f * max(days[i], 0.0) / tau[i]))
    return np.array(out)
