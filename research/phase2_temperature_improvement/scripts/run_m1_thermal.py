"""Measure first-phase thermal anchors and perform condition-held-out tests."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK / "src"))
from thermal_surface import fit_thermal_surface  # noqa: E402


def read_anchor(cell_id: str) -> dict:
    matched = re.fullmatch(r"102Ah_(\d+)degC_(0p5C|1C)_cell\d+", cell_id)
    if not matched:
        raise ValueError(cell_id)
    nominal = float(matched.group(1))
    c_rate = 0.5 if matched.group(2) == "0p5C" else 1.0
    folder = ROOT / "dataset original" / cell_id
    count, present, total = 0, 0, 0.0
    for path in sorted(folder.glob("*.csv")):
        for part in pd.read_csv(path, usecols=["temperature_C"], chunksize=200_000):
            values = pd.to_numeric(part.temperature_C, errors="coerce").to_numpy(float)
            finite = np.isfinite(values)
            count += len(values)
            present += int(finite.sum())
            total += float(values[finite].sum())
    if count == 0:
        raise ValueError("empty raw cell")
    return {"cell_id": cell_id, "T_nom": nominal, "c_rate": c_rate,
            "T_eff": total / present if present else float("nan"),
            "temperature_rows": count, "temperature_observed": present,
            "observed_fraction": present / count, "anchor_usable": present/count >= .2}


def main() -> None:
    panel_manifest = json.loads((TASK / "outputs/panel_manifest.json").read_text())
    cells = sorted(panel_manifest["cells"])
    anchors = [read_anchor(c) for c in cells]
    measured = pd.DataFrame(anchors)
    measured.to_csv(TASK / "outputs/thermal_anchors.csv", index=False)
    fit_rows = [a for a in anchors if a["anchor_usable"]]
    full = fit_thermal_surface(fit_rows)
    print("full_temperature_fit", full, flush=True)
    folds = []
    for held in anchors:
        train = [a for a in fit_rows if a["cell_id"] != held["cell_id"]]
        phys = fit_thermal_surface(train)
        true = float(held["T_eff"])
        nominal = float(held["T_nom"])
        constant_dT = float(np.median([a["T_eff"]-a["T_nom"] for a in train]))
        predictions = {
            "nominal": nominal,
            "constant_dT": nominal+constant_dT,
            "physical": phys.predict(nominal, held["c_rate"]),
        }
        X = np.asarray([[1, a["T_nom"], a["c_rate"]**2] for a in train], float)
        y = np.asarray([a["T_eff"] for a in train], float)
        # Ridge around nominal + constant rise; scale feature columns to avoid
        # a numerical advantage from degrees versus C-rate squared.
        scale = np.maximum(np.std(X[:, 1:], axis=0), 1.0)
        Z = np.column_stack([np.ones(len(X)), X[:, 1:] / scale])
        coef = np.linalg.solve(Z.T@Z + np.diag([0.0, 0.01, 0.01]), Z.T@y)
        predictions["linear"] = float(np.dot([1, nominal/scale[0], held["c_rate"]**2/scale[1]], coef))
        for name, pred in predictions.items():
            folds.append({"heldout_cell": held["cell_id"], "method": name,
                          "training_cells": "|".join(a["cell_id"] for a in train),
                          "n_training_conditions": phys.n_unique_conditions,
                          "heldout_T_nom_C": nominal, "heldout_c_rate": held["c_rate"],
                          "heldout_measured_lifetime_mean_C_diagnostic_only": true,
                          "predicted_T_eff_C": pred, "error_C": pred-true,
                          "thermal_theta_train_only": json.dumps(phys.theta),
                          "train_anchor_rmse_C": phys.train_rmse_C,
                          "heldout_measurement_used_in_fit": False})
        print(held["cell_id"], "physical_prediction", round(predictions["physical"], 3),
              "true_diagnostic", round(true, 3), flush=True)
    cv = pd.DataFrame(folds)
    cv.to_csv(TASK / "outputs/thermal_held_cell.csv", index=False)
    comparison = cv.groupby("method").error_C.agg(
        mae_C=lambda x: np.mean(np.abs(x)), rmse_C=lambda x: np.sqrt(np.mean(x*x)),
    )
    comparison.to_csv(TASK / "outputs/thermal_method_comparison.csv")
    info = {"source_sha256": hashlib.sha256((Path("/Users/shane/Desktop/项目/Current State_Challenge1/my_model/model_template.py")).read_bytes()).hexdigest(),
            "full_six_cell_theta_diagnostic_only": full.theta,
            "full_six_cell_anchor_rmse_C_diagnostic_only": full.train_rmse_C,
            "folds_do_not_use_heldout_temperature_or_labels": True,
            "warning": "Lifetime mean target temperature is diagnostic truth, never an online feature."}
    (TASK / "outputs/thermal_provenance.json").write_text(json.dumps(info, indent=2) + "\n")
    print(comparison.to_string())


if __name__ == "__main__":
    main()
