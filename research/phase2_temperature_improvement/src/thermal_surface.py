"""Pure thermal surface derived from the first-phase source implementation.

The full-six-cell theta is diagnostic only. Fit a new instance on the other
five physical cells for each held-out evaluation fold.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import least_squares


BOUNDS = ((20.0, 0.0, 0.05), (50.0, 20.0, 6.0))


def effective_temperature(theta, nominal_C, c_rate):
    floor, k_self, smooth = np.asarray(theta, float)
    nominal = np.asarray(nominal_C, float)
    rate = np.asarray(c_rate, float)
    u = nominal + k_self * rate ** 2
    return 0.5 * (u + floor + np.sqrt((u - floor) ** 2 + smooth ** 2))


@dataclass(frozen=True)
class ThermalFit:
    theta: tuple[float, float, float] | None
    n_anchors: int
    n_unique_conditions: int
    train_rmse_C: float | None
    identifiable: bool
    fallback: str

    def predict(self, nominal_C: float, c_rate: float) -> float:
        if self.theta is None:
            return float(nominal_C)
        return float(effective_temperature(self.theta, nominal_C, c_rate))


def fit_thermal_surface(anchors: list[dict]) -> ThermalFit:
    """Replicate `_initial_dT_theta` and `_fit_dT` without importing labels."""
    if not anchors:
        return ThermalFit(None, 0, 0, None, False, "no_anchors_deltaT_zero")
    # One anchor per independent condition. Sibling cells sharpen their
    # coordinate instead of contributing duplicate leverage.
    by_condition: dict[tuple[float, float], list[float]] = {}
    for row in anchors:
        key = (float(row["T_nom"]), float(row["c_rate"]))
        by_condition.setdefault(key, []).append(float(row["T_eff"]))
    conditions = sorted(by_condition)
    P = np.asarray(conditions, float)
    obs = np.asarray([np.median(by_condition[k]) for k in conditions], float)
    if not np.isfinite(P).all() or not np.isfinite(obs).all() or np.any(P[:, 1] <= 0):
        raise ValueError("invalid thermal anchors")
    floor0 = float(np.clip(np.percentile(obs, 25), 20.0, 50.0))
    denom = np.maximum(P[:, 1] ** 2, 1e-6)
    k_candidates = (obs - P[:, 0]) / denom
    k_candidates = k_candidates[np.isfinite(k_candidates)]
    k0 = float(np.clip(np.median(np.maximum(k_candidates, 0.0)), 0.0, 20.0)) if len(k_candidates) else 2.0
    theta0 = np.array([floor0, k0, 2.0], float)
    theta = theta0.copy()
    if len(P) >= 3:
        try:
            result = least_squares(
                lambda x: effective_temperature(x, P[:, 0], P[:, 1]) - obs,
                theta0, bounds=BOUNDS, max_nfev=20_000,
            )
            if np.all(np.isfinite(result.x)):
                theta = result.x
        except Exception:
            pass
    pred = effective_temperature(theta, P[:, 0], P[:, 1])
    rmse = float(np.sqrt(np.mean((pred-obs) ** 2)))
    return ThermalFit(tuple(map(float, theta)), len(anchors), len(P), rmse,
                      len(P) >= 3, "fit" if len(P) >= 3 else "underdetermined_initial_surface")
