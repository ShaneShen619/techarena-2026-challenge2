"""Causal, source-neutral partial-charge event extraction.

Rows are first stable-sorted by timestamp; positive-current runs never bridge a
source segment, nonpositive current, duplicate timestamp or a >60 s gap.
Only finished runs are returned.  Ah is integrated with the current measured at
the right endpoint; counter deltas are diagnostic, never silently substituted.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass
class Event:
    start: pd.Timestamp
    end: pd.Timestamp
    segment: int
    median_current: float
    median_temp: float
    duration_s: float
    ah: float
    times_s: np.ndarray
    q_ah: np.ndarray
    voltages: np.ndarray
    counter_delta_ah: float | None
    cells: tuple[str, ...]
    counter_q_ah: np.ndarray | None = None


def partial_ah(event: Event, cell: int, lo: float, hi: float, use_counter: bool = False) -> float | None:
    """First upward threshold crossings, linearly interpolated in cumulative Ah."""
    if not 0 <= cell < event.voltages.shape[1] or not lo < hi:
        return None
    v = event.voltages[:, cell]
    if not np.all(np.isfinite(v)):
        return None
    # Three-point median removes one-sample voltage spikes without future rows
    # outside this already-completed event.
    v = pd.Series(v).rolling(3, center=True, min_periods=1).median().to_numpy()
    qaxis = event.counter_q_ah if use_counter else event.q_ah
    if qaxis is None or not np.isfinite(qaxis).all() or np.any(np.diff(qaxis)<-0.01):
        return None
    result = []
    prior_index = 0
    for threshold in (lo, hi):
        crossing = np.flatnonzero((v[prior_index:-1] < threshold) & (v[prior_index + 1:] >= threshold))
        if not len(crossing):
            return None
        k = int(crossing[0] + prior_index)
        fraction = (threshold - v[k]) / (v[k + 1] - v[k])
        result.append(float(qaxis[k] + fraction * (qaxis[k + 1] - qaxis[k])))
        prior_index = k + 1
    q = result[1] - result[0]
    return q if np.isfinite(q) and q > 0 else None


def extract_charge_events(
    frame: pd.DataFrame,
    *,
    time_col: str = "timestamp",
    current_col: str = "current_A",
    voltage_cols: tuple[str, ...] = ("cell1_V", "cell2_V", "cell3_V", "cell4_V"),
    temp_col: str = "temp_mean_C",
    segment_col: str = "segment",
    counter_col: str | None = "charge_Ah_cum",
    min_current: float = 5.0,
    min_points: int = 10,
    min_duration_s: float = 60.0,
    max_gap_s: float = 60.0,
    until: pd.Timestamp | None = None,
) -> list[Event]:
    if frame.empty or any(c not in frame for c in (time_col, current_col, *voltage_cols)):
        return []
    if until is not None:
        frame = frame.loc[pd.to_datetime(frame[time_col]) <= pd.Timestamp(until)]
    if frame.empty:
        return []
    frame = frame.sort_values(time_col, kind="stable").reset_index(drop=True)
    ts = pd.to_datetime(frame[time_col]); seconds = ts.to_numpy(dtype="datetime64[s]").astype("int64")
    current = pd.to_numeric(frame[current_col], errors="coerce").to_numpy(float)
    voltage = frame[list(voltage_cols)].to_numpy(float)
    temp = frame[temp_col].to_numpy(float) if temp_col in frame else np.full(len(frame), np.nan)
    segment = frame[segment_col].to_numpy() if segment_col in frame else np.zeros(len(frame), int)
    counter = frame[counter_col].to_numpy(float) if counter_col and counter_col in frame else None
    good = (current >= min_current) & np.isfinite(current) & np.all(np.isfinite(voltage), axis=1)
    dt = np.diff(seconds, prepend=seconds[0])
    boundary = (~good) | (dt <= 0) | (dt > max_gap_s) | (segment != np.roll(segment, 1))
    # A boundary may be caused by a non-positive prior sample, so identify every
    # positive run by a start flag and never integrate across its leading gap.
    starts = np.flatnonzero(good & (boundary | ~np.r_[False, good[:-1]]))
    stop_flags = (~good) | np.r_[boundary[1:], True]
    stops = np.flatnonzero(good & stop_flags)
    if len(starts) != len(stops):
        raise RuntimeError("charge run accounting mismatch")
    events: list[Event] = []
    for a, b in zip(starts, stops):
        if b == len(frame)-1 and good[b]:
            # A prefix ending during charge does not reveal the event endpoint.
            continue
        if b - a + 1 < min_points or seconds[b] - seconds[a] < min_duration_s:
            continue
        d = np.diff(seconds[a:b + 1], prepend=seconds[a]); d[0] = 0
        q = np.cumsum(current[a:b + 1] * d / 3600.0)
        cd = float(counter[b] - counter[a]) if counter is not None and np.isfinite(counter[[a,b]]).all() else None
        counter_axis = (counter[a:b+1]-counter[a]).copy() if cd is not None else None
        events.append(Event(ts.iloc[a], ts.iloc[b], int(segment[a]), float(np.median(current[a:b+1])),
                            float(np.nanmedian(temp[a:b+1])) if np.isfinite(temp[a:b+1]).any() else float("nan"),
                            float(seconds[b] - seconds[a]), float(q[-1]), seconds[a:b+1].copy(), q,
                            voltage[a:b+1].copy(), cd, voltage_cols, counter_axis))
    return events
