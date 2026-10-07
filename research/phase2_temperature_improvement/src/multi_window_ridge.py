"""Portable low-dimensional charge-window SOH-delta regression.

The model maps a target's causally visible completed-charge features to its
SOH change from the released first capacity.  Training labels and scalers
come only from the stated training physical cells.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


WIDTHS = {"0.04V": list(range(0, 9)), "0.07V": list(range(9, 17)), "0.10V": list(range(17, 24))}


def feature_columns(width: str, with_temperature: bool) -> list[str]:
    if width not in WIDTHS:
        raise ValueError(width)
    columns = ["age_fraction", "age_fraction_sq", "event_age_days", "cc_ratio",
               "delta_current_rel", f"{width}_mean", f"{width}_std", f"{width}_slope"]
    columns += [f"w{i:02d}_logratio" for i in WIDTHS[width]]
    if with_temperature:
        columns += ["temp_C", "initial_temp_C", "delta_temp_C", "temp_interaction"]
    return columns


def add_derived_features(frame: pd.DataFrame, *, age_col: str) -> pd.DataFrame:
    out = frame.copy()
    out["age_fraction"] = out[age_col].to_numpy(float)/5500.
    out["age_fraction_sq"] = out.age_fraction**2
    out["cc_ratio"] = np.log(out.recent_cc_Ah/out.initial_cc_Ah)
    all_windows = out[[f"w{i:02d}_logratio" for i in range(24)]].to_numpy(float)
    out["temp_interaction"] = out.delta_temp_C*all_windows.mean(axis=1)
    for width, idx in WIDTHS.items():
        values = all_windows[:, idx]
        out[f"{width}_mean"] = values.mean(axis=1)
        out[f"{width}_std"] = values.std(axis=1)
        out[f"{width}_slope"] = values[:, -1]-values[:, 0]
    return out


@dataclass
class RidgeFeatureModel:
    columns: list[str]
    lam: float
    feature_mean: list[float]
    feature_scale: list[float]
    response_mean: float
    coefficients: list[float]
    training_cells: list[str]

    @classmethod
    def fit(cls, train: pd.DataFrame, width: str, lam: float,
            *, with_temperature: bool) -> "RidgeFeatureModel":
        columns = feature_columns(width, with_temperature)
        x = train[columns].to_numpy(float)
        y = (train.target_soh_pp-train.anchor_soh_pp).to_numpy(float)
        if not (np.isfinite(x).all() and np.isfinite(y).all()):
            raise ValueError("nonfinite training features/labels")
        mean = x.mean(axis=0)
        scale = np.where(x.std(axis=0) < 1e-7, 1., x.std(axis=0))
        xs = np.clip((x-mean)/scale, -6., 6.)
        ym = float(y.mean())
        coefs = np.linalg.solve(xs.T@xs+lam*np.eye(len(columns)), xs.T@(y-ym))
        return cls(columns, float(lam), mean.tolist(), scale.tolist(), ym,
                   coefs.tolist(), sorted(train.cell_id.unique().tolist()))

    def predict(self, test: pd.DataFrame) -> np.ndarray:
        x = test[self.columns].to_numpy(float)
        if not np.isfinite(x).all():
            raise ValueError("nonfinite prediction features")
        xs = np.clip((x-np.asarray(self.feature_mean))/np.asarray(self.feature_scale), -6., 6.)
        delta = self.response_mean+xs@np.asarray(self.coefficients)
        return test.anchor_soh_pp.to_numpy(float)+delta
