"""Stress-history extraction for the round-5A ageing model (EXECUTION_PROMPT.md stage 1).

``stress_table(op, until, ck)`` returns one row per interval [t0, t1) with time-weighted and
throughput-weighted cell temperature, throughput and a kind flag. Only rows of ``op`` (already
cut to the visible prefix) are used. Hidden intervals are filled by registered rules:

* ``observed``      consecutive rows of one segment (recording gaps included; counters carry
                    their throughput, temperature is the mean of the two bounding rows);
* ``checkup``       segment end -> next segment start between months: 25 C, zero throughput
                    (main) or ``checkup_Ah`` spread uniformly (variant);
* ``seg_gap``       a missing 45 C segment once the following segment is visible: its counter
                    jump spread uniformly, temperature 45 C + offset;
* ``extrapolated``  from the last visible row to the estimated month end at 45 C + offset with
                    the median Ah/day of the last 7 visible 45 C days; then ``checkup`` to the
                    horizon.

Throughput is total Ah = d(charge_Ah_cum) + d(discharge_Ah_cum) (the counters keep integrating
across recording gaps and the missing segment; checkups are not counted by the cycler).
"""
import numpy as np
import pandas as pd

HOUR = pd.Timedelta(hours=1)
DAY_S = 86400.0


def _observed(op):
    """Hourly bins of observed rows: t0, t1, days, T_time (C), T_thr (C), thr_Ah, segment, setpoint."""
    out = []
    for seg, g in op.groupby("segment", sort=True):
        t = g["timestamp"].to_numpy()
        ts = g["elapsed_s"].to_numpy(float)
        temp = g["temp_mean_C"].to_numpy(float)
        ctr = (g["charge_Ah_cum"] + g["discharge_Ah_cum"]).to_numpy(float)
        if len(g) < 2:
            continue
        dt = np.diff(ts)
        thr = np.clip(np.diff(ctr), 0.0, None)
        tm = 0.5 * (temp[1:] + temp[:-1])
        tstart = pd.DatetimeIndex(t[:-1])
        b = tstart.floor("h")
        df = pd.DataFrame({"bin": b, "dt": dt, "thr": thr, "Tdt": tm * dt, "Tthr": tm * thr})
        agg = df.groupby("bin", sort=True).sum()
        t0 = agg.index
        # bin end = start of the next bin's first row, or the segment end for the last bin
        first_t = pd.Series(tstart).groupby(b.values).min()
        t1 = list(first_t.iloc[1:]) + [pd.Timestamp(t[-1])]
        days = agg["dt"].to_numpy() / DAY_S
        T_time = np.where(agg["dt"] > 0, agg["Tdt"] / np.where(agg["dt"] > 0, agg["dt"], 1), np.nan)
        T_thr = np.where(agg["thr"] > 0, agg["Tthr"] / np.where(agg["thr"] > 0, agg["thr"], 1), T_time)
        out.append(pd.DataFrame({"t0": list(first_t), "t1": t1, "days": days, "T_time": T_time,
                                 "T_thr": T_thr, "thr_Ah": agg["thr"].to_numpy(), "segment": seg,
                                 "setpoint": int(g["chamber_temperature_C"].iloc[0]), "kind": "observed"}))
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def _uniform(t0, t1, T, thr, kind, segment=-1, setpoint=-1):
    days = max((t1 - t0).total_seconds(), 0.0) / DAY_S
    return dict(t0=t0, t1=t1, days=days, T_time=T, T_thr=T, thr_Ah=thr, segment=segment,
                setpoint=setpoint, kind=kind)


def segment_summary(op):
    g = op.groupby("segment").agg(t0=("timestamp", "min"), t1=("timestamp", "max"),
                                  sp=("chamber_temperature_C", "first"),
                                  c0=("charge_Ah_cum", "first"), c1=("charge_Ah_cum", "last"),
                                  d0=("discharge_Ah_cum", "first"), d1=("discharge_Ah_cum", "last"),
                                  Tm=("temp_mean_C", "mean"), Tc=("chamber_temperature_C", "mean"))
    return g.sort_index()


def visible_rules(op, ck, k_cut, rate_days=7.0):
    """Causal rule parameters from the visible prefix (all registered in stage 1).

    offset45  mean(cell - chamber) of the last visible 45 C segment (K);
    rate45    median Ah/day over the last ``rate_days`` visible days at 45 C;
    end_off   median (last row of month m's 45 C segment - CK_{m+1} date) over complete
              visible months (both the 45 C segment and the next month's first segment visible);
              0 h if none;
    """
    seg = segment_summary(op)
    s45 = seg[seg["sp"] == 45]
    last45 = s45.index.max()
    g = op[op["segment"] == last45]
    offset45 = float((g["temp_mean_C"] - g["chamber_temperature_C"]).mean())
    # daily throughput in the last rate_days days of visible 45 C operation
    o45 = op[op["chamber_temperature_C"] == 45]
    tend = o45["timestamp"].max()
    w = o45[o45["timestamp"] > tend - pd.Timedelta(days=rate_days)]
    ctr = (w["charge_Ah_cum"] + w["discharge_Ah_cum"])
    day = (tend - w["timestamp"]).dt.total_seconds() // DAY_S
    per_day = ctr.groupby(day.values).agg(lambda x: x.max() - x.min())
    span = w["timestamp"].groupby(day.values).agg(lambda x: (x.max() - x.min()).total_seconds() / DAY_S)
    full = span > 0.9
    rate45 = float(np.median(per_day[full] / span[full])) if full.any() else float(np.median(per_day / span.clip(lower=1e-6)))
    offs = []
    for m in range(0, k_cut):
        if m + 1 >= len(ck):
            break
        sm = s45[(s45["t0"] > ck[m]) & (s45["t0"] < ck[m + 1])]
        nxt = seg[seg["t0"] > ck[m + 1]]
        if len(sm) and len(nxt):
            offs.append((sm["t1"].iloc[0] - ck[m + 1]).total_seconds() / 3600.0)
    end_off_h = float(np.median(offs)) if offs else 0.0
    return dict(offset45=offset45, rate45=rate45, end_off_h=end_off_h, last45=int(last45))


def horizon_lag_days(fc, ck, at_date):
    """Median visible lag (CK_j date -> anchor j start), j >= 1; 3 days if none."""
    from v2 import anchors_by_checkup
    anc = anchors_by_checkup(fc, ck) if len(fc) else {}
    lags = [(r["t_start"] - ck[j]).total_seconds() / DAY_S for j, r in anc.items()
            if j >= 1 and r["t_start"] < at_date]
    return float(np.median(lags)) if lags else 3.0


def stress_table(op, until, ck, horizon=None, checkup_Ah=0.0, rate_days=7.0, T_checkup=25.0):
    """Interval table from the visible prefix up to ``horizon`` (default: ``until``).

    ``op`` must already be cut. ``until`` is the cutoff (CK date or pseudo-cut date used for the
    month-end estimate); ``horizon`` is where the integration stops (e.g. t*_k).
    """
    ck = pd.DatetimeIndex(ck)
    horizon = pd.Timestamp(until if horizon is None else horizon)
    k_cut = int((ck <= pd.Timestamp(until)).sum()) - 1   # index of the CK date at/just before until
    obs = _observed(op)
    seg = segment_summary(op)
    rules = visible_rules(op, ck, max(k_cut, 0), rate_days)
    rows = []
    segs = list(seg.index)
    for a, b in zip(segs[:-1], segs[1:]):
        ta, tb = seg.loc[a, "t1"], seg.loc[b, "t0"]
        jump = (seg.loc[b, "c0"] - seg.loc[a, "c1"]) + (seg.loc[b, "d0"] - seg.loc[a, "d1"])
        if b == a + 1:
            rows.append(_uniform(ta, tb, T_checkup, checkup_Ah if seg.loc[a, "sp"] == 45 else 0.0,
                                 "checkup"))
        else:
            # missing 45 C segment(s) between a and b, then a checkup before b
            m = int((ck < tb).sum()) - 1          # checkup just before segment b
            t_end = ck[m] + pd.Timedelta(hours=rules["end_off_h"])
            t_end = min(max(t_end, ta), tb)
            rows.append(_uniform(ta, t_end, 45.0 + rules["offset45"], jump, "seg_gap"))
            rows.append(_uniform(t_end, tb, T_checkup, checkup_Ah, "checkup"))
    # hidden tail: last visible row -> estimated month end (45 C) -> checkup -> horizon
    t_last = op["timestamp"].max()
    if horizon > t_last:
        m_next = int((ck < t_last).sum())           # next checkup at/after the last visible row
        if m_next < len(ck):
            t_mend = ck[m_next] + pd.Timedelta(hours=rules["end_off_h"])
            t_mend = min(max(t_mend, t_last), horizon)
        else:
            t_mend = horizon
        if t_mend > t_last:
            d = (t_mend - t_last).total_seconds() / DAY_S
            rows.append(_uniform(t_last, t_mend, 45.0 + rules["offset45"], rules["rate45"] * d,
                                 "extrapolated"))
        if horizon > t_mend:
            rows.append(_uniform(t_mend, horizon, T_checkup, checkup_Ah if m_next < len(ck) else 0.0,
                                 "checkup"))
    tab = pd.concat([obs, pd.DataFrame(rows)], ignore_index=True) if rows else obs
    tab = tab.sort_values("t0").reset_index(drop=True)
    tab = tab[tab["t0"] < horizon].copy()
    # clip the interval crossing the horizon (observed rows beyond horizon do not exist in a cut op)
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


def cumulative(tab, Ea_J, T_ref_K=298.15, t_eval=None):
    """Cumulative Arrhenius-weighted effective days and throughput at times ``t_eval``.

    Returns (tau_eff_days, ah_eff) arrays; interpolation inside an interval is linear.
    """
    R = 8.314462618
    aT_time = np.exp(-Ea_J / R * (1.0 / (tab["T_time"].to_numpy(float) + 273.15) - 1.0 / T_ref_K))
    aT_thr = np.exp(-Ea_J / R * (1.0 / (tab["T_thr"].to_numpy(float) + 273.15) - 1.0 / T_ref_K))
    days = tab["days"].to_numpy(float)
    thr = tab["thr_Ah"].to_numpy(float)
    dtau = np.where(days > 0, days * np.nan_to_num(aT_time, nan=1.0), 0.0)
    dah = np.where(thr > 0, thr * np.nan_to_num(aT_thr, nan=1.0), 0.0)
    t0 = pd.to_datetime(tab["t0"]).dt.as_unit("ns").astype("int64").to_numpy() / 1e9
    t1 = pd.to_datetime(tab["t1"]).dt.as_unit("ns").astype("int64").to_numpy() / 1e9
    ctau = np.r_[0.0, np.cumsum(dtau)]
    cah = np.r_[0.0, np.cumsum(dah)]
    if t_eval is None:
        return ctau[-1], cah[-1]
    te = np.atleast_1d(pd.DatetimeIndex(t_eval).as_unit("ns").asi8 / 1e9)
    out_tau, out_ah = [], []
    for x in te:
        i = np.searchsorted(t1, x, side="left")   # first interval ending at/after x
        if i >= len(t1):
            out_tau.append(ctau[-1]); out_ah.append(cah[-1]); continue
        span = max(t1[i] - t0[i], 1e-9)
        f = min(max((x - t0[i]) / span, 0.0), 1.0)
        out_tau.append(ctau[i] + f * dtau[i]); out_ah.append(cah[i] + f * dah[i])
    return np.array(out_tau), np.array(out_ah)
