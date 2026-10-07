"""Frozen-weight D1 fusion, ablations, channel shocks, and group-rank intervals."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
OUT = TASK / "runs/M9_D1_v15_fusion_v1"
OUT.mkdir(parents=True, exist_ok=False)
cfg = json.loads((TASK / "configs/m8_fusion.json").read_text())
panel = ROOT / "research/phase2_temperature_improvement/outputs/panel_main.csv"
assert hashlib.sha256(panel.read_bytes()).hexdigest() == "7188b662900f84312292a7062d6023e5eeb4f2e32798b6d61a3547ed40cdc59c"
keys = ["cell_id", "target_ordinal"]


def one(path, method, pred_col, truth_col, name):
    d = pd.read_csv(TASK / path)
    d = d.loc[d.method.eq(method), keys + [pred_col, truth_col]].copy()
    assert len(d) == 180 and not d.duplicated(keys).any(), (name, len(d))
    return d.rename(columns={pred_col: name, truth_col: f"truth_{name}"})


age = one("runs/M9_D1_v15_M2_20Ah_persistent_v1/predictions.csv", "age_ridge", "pred_soh_pp", "target_soh_pp", "age")
temp = one("runs/M9_D1_v15_spline_v1/predictions.csv", "spline_age_temp_rate", "pred_pp", "actual_pp", "temperature")
tcn_raw = pd.read_csv(TASK / "runs/M9_D1_v15_TCN_v1/predictions.csv")
tcn_raw = tcn_raw.loc[tcn_raw.method.eq("TCN_from_scratch")].copy()
assert len(tcn_raw) == 540 and set(tcn_raw.seed) == set(json.loads((TASK / "configs/m9_d1_v15_representation.json").read_text())["seeds"])
tcn = tcn_raw.groupby(keys, as_index=False).agg(tcn=("pred_soh_pp", "mean"), truth_tcn=("target_soh_pp", "first"))
assert tcn_raw.groupby(keys).target_soh_pp.nunique().eq(1).all()
d = age.merge(temp, on=keys, validate="one_to_one").merge(tcn, on=keys, validate="one_to_one")
assert len(d) == 180 and np.max(abs(d.truth_age - d.truth_temperature)) < 1e-7
assert np.max(abs(d.truth_age - d.truth_tcn)) < 1e-4
d = d.rename(columns={"truth_age": "truth_pp"}).drop(columns=["truth_temperature", "truth_tcn"])

d["simple_age_tcn"] = 0.5 * d.age + 0.5 * d.tcn
d["simple_temp_tcn"] = 0.5 * d.temperature + 0.5 * d.tcn
d["disagreement_pp"] = abs(d.temperature - d.tcn)
d["gate_triggered"] = d.disagreement_pp > 5
d["disagreement_gate"] = np.where(d.gate_triggered,
    0.5 * d.age + 0.25 * d.temperature + 0.25 * d.tcn, d.simple_temp_tcn)
d["missing_temperature"] = d.simple_age_tcn
d["missing_waveform"] = 0.5 * d.age + 0.5 * d.temperature
d["temperature_plus10"] = np.where(abs((d.temperature + 10) - d.tcn) > 5,
    0.5 * d.age + 0.25 * (d.temperature + 10) + 0.25 * d.tcn,
    0.5 * (d.temperature + 10) + 0.5 * d.tcn)
d["waveform_plus10"] = np.where(abs(d.temperature - (d.tcn + 10)) > 5,
    0.5 * d.age + 0.25 * d.temperature + 0.25 * (d.tcn + 10),
    0.5 * d.temperature + 0.5 * (d.tcn + 10))

methods = ["age", "temperature", "tcn", "simple_age_tcn", "simple_temp_tcn", "disagreement_gate",
           "missing_temperature", "missing_waveform", "temperature_plus10", "waveform_plus10"]
long = d.melt(id_vars=keys + ["truth_pp", "gate_triggered", "disagreement_pp"], value_vars=methods,
              var_name="method", value_name="prediction_pp")
long["error_pp"] = long.prediction_pp - long.truth_pp
long.to_csv(OUT / "predictions.csv", index=False)
scores = []
for method, part in long.groupby("method"):
    per = part.assign(abs_pp=part.error_pp.abs()).groupby("cell_id").abs_pp.mean()
    scores.append({"method": method, "n_targets": len(part), "macro_MAE_pp": float(per.mean()),
                   "worst_cell_MAE_pp": float(per.max()), "max_abs_error_pp": float(part.error_pp.abs().max()),
                   "P95_abs_error_pp": float(part.error_pp.abs().quantile(.95)),
                   "bias_pp": float(part.error_pp.mean()), "per_cell_mae_pp": json.dumps(per.to_dict())})
pd.DataFrame(scores).to_csv(OUT / "method_scores.csv", index=False)

# This diagnostic is intentionally not called 90% conformal: with five calibration
# entities the 90% rank is six and therefore gives an infinite finite-sample band.
inp = np.load(TASK / "runs/M9_D1_v15_target_map_v1/target_inputs.npz")
meta = inp["metadata"].astype(float)
cell = inp["cell_ids"].astype(str)
ordinals = inp["target_ordinals"].astype(int)
assert np.array_equal(d.sort_values(keys).cell_id.to_numpy(str), cell)
assert np.array_equal(d.sort_values(keys).target_ordinal.to_numpy(int), ordinals)
truth = d.sort_values(keys).truth_pp.to_numpy(float)
anchor = meta[:, 0]
age_feat = meta[:, 1:6]


def fixed_age_ridge(train, test):
    a = age_feat[train]
    b = age_feat[test]
    median = np.array([np.nanmedian(col) if np.isfinite(col).any() else 0.0 for col in a.T])
    a = np.where(np.isfinite(a), a, median)
    b = np.where(np.isfinite(b), b, median)
    mean, std = a.mean(0), a.std(0)
    std[std < 1e-8] = 1
    a = np.c_[np.ones(len(a)), (a - mean) / std]
    b = np.c_[np.ones(len(b)), (b - mean) / std]
    penalty = np.diag([0] + [10.0] * (a.shape[1] - 1))
    beta = np.linalg.solve(a.T @ a + penalty + np.eye(a.shape[1]) * 1e-9,
                           a.T @ (truth[train] - anchor[train]))
    return anchor[test] + b @ beta


band_rows = []
for held in np.unique(cell):
    training = np.flatnonzero(cell != held)
    test = np.flatnonzero(cell == held)
    residual_max = []
    for calibrator in np.unique(cell[training]):
        cal = training[cell[training] == calibrator]
        fit = training[cell[training] != calibrator]
        residual_max.append(float(np.max(abs(fixed_age_ridge(fit, cal) - truth[cal]))))
    width = float(max(residual_max))
    forecast = fixed_age_ridge(training, test)
    for j, i in enumerate(test):
        band_rows.append({"cell_id": cell[i], "target_ordinal": int(ordinals[i]), "truth_pp": truth[i],
                          "prediction_pp": float(forecast[j]), "half_width_pp": width,
                          "covered_80_group_rank": bool(abs(forecast[j] - truth[i]) <= width),
                          "nominal_90_finite_possible": False})
band = pd.DataFrame(band_rows)
band.to_csv(OUT / "age_group_rank_intervals.csv", index=False)
summary = {"n_targets": len(d), "gate_triggered_targets": int(d.gate_triggered.sum()),
           "scores": [{k: v for k, v in item.items() if k != "per_cell_mae_pp"} for item in scores],
           "age_group_rank_80_observed_target_coverage": float(band.covered_80_group_rank.mean()),
           "age_group_rank_80_observed_entire_cell_coverage": float(band.groupby("cell_id").covered_80_group_rank.all().mean()),
           "age_group_rank_median_half_width_pp": float(band.half_width_pp.median()),
           "finite_90_group_band_possible_with_5_calibration_cells": False,
           "claim_limit": "D1 v1.5 six development cells; original fusion weights retained from v1.4 and were chosen after prior M2/M7 development. Intervals are a small-sample rank diagnostic, not a reliable official coverage guarantee."}
(OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"gate_triggered": summary["gate_triggered_targets"],
                  "macro_MAE_pp": {x["method"]: x["macro_MAE_pp"] for x in scores},
                  "interval_80_cell_coverage": summary["age_group_rank_80_observed_entire_cell_coverage"]}, ensure_ascii=False), flush=True)
