"""Causal temperature summary for a completed charging event or voltage window."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from thermal_surface import ThermalFit


@dataclass(frozen=True)
class TemperatureSummary:
    used_C: float
    measured_median_C: float | None
    source: str
    valid_fraction: float
    mad_C: float | None
    p10_p90_C: float | None
    start_end_delta_C: float | None
    slope_C_per_hour: float | None
    flags: tuple[str, ...]
    last_visible_time: pd.Timestamp | None


def summarize_temperature(
    timestamps,
    observed_C,
    *,
    cutoff,
    nominal_C: float,
    c_rate: float,
    fallback: ThermalFit | None,
    min_valid_fraction: float = .6,
    sensor_min_C: float = -20.,
    sensor_max_C: float = 90.,
) -> TemperatureSummary:
    """Use measured temperature when credible; otherwise mark the fallback.

    This function never guesses temperature from a target's future history.
    Constant temperature is reported but not automatically discarded.
    """
    times = pd.to_datetime(pd.Index(timestamps), errors="raise")
    raw = np.asarray(observed_C, float)
    if len(times) != len(raw):
        raise ValueError("time and temperature lengths differ")
    limit = pd.Timestamp(cutoff)
    visible = np.asarray(times <= limit)
    times = times[visible]
    raw = raw[visible]
    valid = np.isfinite(raw) & (raw >= sensor_min_C) & (raw <= sensor_max_C)
    fraction = float(np.mean(valid)) if len(raw) else 0.
    flags: list[str] = []
    if np.isfinite(raw).any() and np.any(np.isfinite(raw) & ~valid):
        flags.append("outside_sensor_range")
    if fraction < min_valid_fraction:
        flags.append("low_observed_fraction")
    last = pd.Timestamp(times.max()) if len(times) else None
    if valid.any():
        sorted_idx = np.argsort(np.asarray(times[valid], dtype="datetime64[ns]"), kind="stable")
        t = times[valid][sorted_idx]
        v = raw[valid][sorted_idx]
        median = float(np.median(v))
        mad = float(np.median(np.abs(v-median)))
        spread = float(np.quantile(v, .9)-np.quantile(v, .1))
        delta = float(v[-1]-v[0]) if len(v) >= 2 else None
        duration_h = (pd.Timestamp(t[-1])-pd.Timestamp(t[0])).total_seconds()/3600 if len(t) >= 2 else 0.
        slope = float(delta/duration_h) if duration_h > 0 else None
        if len(v) >= 3 and float(np.max(v)-np.min(v)) <= .05:
            flags.append("near_constant_sensor")
        if len(v) >= 2:
            dt_s = np.diff(np.asarray(t, dtype="datetime64[s]").astype("int64"))
            dv = np.diff(v)
            if np.any((dt_s > 0) & (np.abs(dv) / np.maximum(dt_s, 1) * 30 > 5.0)):
                flags.append("temperature_jump")
    else:
        median = mad = spread = delta = slope = None
    if fraction >= min_valid_fraction and median is not None and "temperature_jump" not in flags:
        used = median
        source = "measured"
    elif fallback is not None and fallback.theta is not None:
        used = fallback.predict(nominal_C, c_rate)
        source = "estimated_training_surface"
    else:
        used = float(nominal_C)
        source = "nominal_unidentified_fallback"
    return TemperatureSummary(used, median, source, fraction, mad, spread,
                              delta, slope, tuple(flags), last)
