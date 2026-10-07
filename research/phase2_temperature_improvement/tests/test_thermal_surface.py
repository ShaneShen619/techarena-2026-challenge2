from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from thermal_surface import effective_temperature, fit_thermal_surface  # noqa: E402


def test_surface_is_monotone_for_chamber_temperature_and_c_rate() -> None:
    theta = (35.7, 3.7, 4.5)
    nominal = effective_temperature(theta, np.array([25., 35., 45.]), 1.)
    current = effective_temperature(theta, 35., np.array([.5, 1., 1.5]))
    assert np.all(np.diff(nominal) > 0)
    assert np.all(np.diff(current) > 0)
    assert np.all(nominal >= np.array([25., 35., 45.]))


def test_duplicate_condition_cannot_manufacture_identifiability() -> None:
    single = {"T_nom": 25., "c_rate": 1., "T_eff": 36.}
    fit = fit_thermal_surface([single] * 20)
    assert fit.n_anchors == 20
    assert fit.n_unique_conditions == 1
    assert not fit.identifiable
    assert fit.fallback == "underdetermined_initial_surface"


def test_no_anchor_reports_nominal_fallback() -> None:
    fit = fit_thermal_surface([])
    assert fit.theta is None
    assert fit.predict(25., 1.) == 25.
    assert fit.fallback == "no_anchors_deltaT_zero"
