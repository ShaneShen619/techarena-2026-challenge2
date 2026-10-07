from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from event_temperature import summarize_temperature  # noqa: E402
from thermal_surface import fit_thermal_surface  # noqa: E402


def test_measured_60_c_is_accepted_and_future_rows_do_not_change_it() -> None:
    stamps = pd.date_range("2021-01-01", periods=5, freq="30s")
    old = summarize_temperature(stamps[:4], [59., 60., 61., 62.],
                                cutoff=stamps[3], nominal_C=45., c_rate=1., fallback=None)
    changed_future = summarize_temperature(stamps, [59., 60., 61., 62., -999.],
                                           cutoff=stamps[3], nominal_C=45., c_rate=1., fallback=None)
    assert old == changed_future
    assert old.source == "measured"
    assert old.used_C > 60.


def test_missing_temperature_uses_training_only_surface_with_source_flag() -> None:
    fit = fit_thermal_surface([
        {"T_nom": 25., "c_rate": .5, "T_eff": 36.},
        {"T_nom": 35., "c_rate": 1., "T_eff": 41.},
        {"T_nom": 45., "c_rate": 1., "T_eff": 50.},
    ])
    stamps = pd.date_range("2021-01-01", periods=3, freq="30s")
    result = summarize_temperature(stamps, [np.nan, np.nan, 52.], cutoff=stamps[-1],
                                   nominal_C=45., c_rate=1., fallback=fit)
    assert result.source == "estimated_training_surface"
    assert result.used_C == fit.predict(45., 1.)
    assert result.measured_median_C == 52.
    assert "low_observed_fraction" in result.flags


def test_temperature_jump_does_not_silently_become_measured_anchor() -> None:
    stamps = pd.date_range("2021-01-01", periods=3, freq="30s")
    result = summarize_temperature(stamps, [40., 60., 41.], cutoff=stamps[-1],
                                   nominal_C=45., c_rate=1., fallback=None)
    assert "temperature_jump" in result.flags
    assert result.source == "nominal_unidentified_fallback"
