"""Prefix-only current integration. Counters never silently replace current."""
from __future__ import annotations
import numpy as np
import pandas as pd

TEMPERATURES = np.arange(81, dtype=float)
RATES = np.array([.01, .025, .05, .1, .2, .5, 1., 2.])
GRID_T = np.repeat(TEMPERATURES, len(RATES))
GRID_C = np.tile(RATES, len(TEMPERATURES))
N_BINS = len(GRID_T)


def intervals(frame, *, time_col="timestamp", segment_col="segment",
              temp_col="temp_mean_C", fallback_temperature=25., max_gap_s=60.):
    required = {time_col, "current_A"}
    if frame.empty or not required <= set(frame):
        return pd.DataFrame(columns=["start_ns", "end_ns", "dN", "temperature_C", "rate_C", "bin", "temp_missing"]), {"rows":len(frame)}
    f = frame.copy()
    f[time_col] = pd.to_datetime(f[time_col], errors="coerce")
    f = f.loc[f[time_col].notna()].sort_values(time_col, kind="stable").reset_index(drop=True)
    ts = f[time_col].astype("int64").to_numpy()
    dt = np.diff(ts, prepend=ts[0]) / 1e9
    current = pd.to_numeric(f.current_A, errors="coerce").to_numpy(float)
    seg = f[segment_col].to_numpy() if segment_col in f else np.zeros(len(f))
    positive = np.isfinite(current) & (current > 0.)
    if "step_type" in f:
        positive &= f.step_type.ne("cc_discharge").to_numpy()
    same_seg = seg == np.r_[seg[0], seg[:-1]]
    prev_positive = np.r_[False, positive[:-1]]
    valid = positive & prev_positive & same_seg & (dt > 0) & (dt <= max_gap_s)
    # Stable run's median uses only its current visible rows. Segment boundaries
    # and current sign/gaps split runs before any median is computed.
    starts = positive & (~prev_positive | ~same_seg | (dt <= 0) | (dt > max_gap_s))
    groups = np.cumsum(starts)
    med = (pd.Series(current[positive]).groupby(groups[positive], sort=False)
           .expanding().median().reset_index(level=0, drop=True).sort_index())
    rates = np.full(len(f), np.nan)
    rates[positive] = med.to_numpy() / 102.
    t = pd.to_numeric(f[temp_col], errors="coerce").to_numpy(float) if temp_col in f else np.full(len(f), np.nan)
    missing = ~np.isfinite(t)
    if "chamber_temperature_C" in f:
        fallback = pd.to_numeric(f.chamber_temperature_C, errors="coerce").to_numpy(float)
        fallback = np.where(np.isfinite(fallback), fallback, fallback_temperature)
    else:
        fallback = np.full(len(f), fallback_temperature)
    t = np.where(missing, fallback, t)
    ti = np.clip(np.rint(t), 0, 80).astype(int)
    ci = np.argmin(abs(rates[:,None]-RATES[None,:]), axis=1)
    dN = np.where(valid, current * dt / (3600.*102.), 0.)
    inds = np.flatnonzero(valid)
    out = pd.DataFrame({"start_ns":ts[inds-1], "end_ns":ts[inds], "dN":dN[inds],
                        "temperature_C":t[inds], "rate_C":rates[inds],
                        "bin":ti[inds]*len(RATES)+ci[inds], "temp_missing":missing[inds]})
    diag = {"rows":len(f), "charge_EFC":float(dN.sum()),
            "valid_charge_intervals":int(valid.sum()), "duplicate_time_steps":int((dt[1:]==0).sum()),
            "long_gap_steps":int((dt>max_gap_s).sum()),
            "positive_segment_switches":int((positive & prev_positive & ~same_seg).sum()),
            "temperature_missing_charge_fraction":float(dN[missing].sum()/max(dN.sum(),1e-12)),
            "temperature_binning_C":1., "rate_binning":"nearest preregistered stable-run rate bin"}
    return out, diag


def histograms_at(ledger, timestamps):
    """Single pass over sorted intervals; no future endpoint enters a prefix."""
    cut = pd.to_datetime(timestamps).astype("int64").to_numpy()
    order = np.argsort(cut, kind="stable")
    result = np.zeros((len(cut), N_BINS))
    accum = np.zeros(N_BINS)
    ends = ledger.end_ns.to_numpy(np.int64)
    bins = ledger.bin.to_numpy(int)
    dn = ledger.dN.to_numpy(float)
    left = 0
    for idx in order:
        right = int(np.searchsorted(ends, cut[idx], side="left"))
        accum += np.bincount(bins[left:right], weights=dn[left:right], minlength=N_BINS)
        result[idx] = accum
        left = right
    return result


def histogram(ledger):
    return np.bincount(ledger.bin.to_numpy(int), weights=ledger.dN.to_numpy(float), minlength=N_BINS)


def rate_weights(parameters, mode, temperature_shift=0.):
    t = GRID_T + float(temperature_shift)
    c = GRID_C.copy()
    if mode == "fixed": c[:] = .5
    elif mode == "sat": c = np.maximum(c, .5)
    elif mode != "extrap": raise ValueError(mode)
    p = parameters
    log_tau = p["lnA"] + p["Ea"]/(8.314*(t+273.15)) + p.get("gamma",0.)*np.log(c)
    return np.exp(-np.clip(log_tau, np.log(20.), np.log(1e6)))
