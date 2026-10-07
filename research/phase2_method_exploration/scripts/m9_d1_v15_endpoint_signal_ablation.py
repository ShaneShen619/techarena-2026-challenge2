"""Nested-cell RBF ablation of early-prefix workpoint and window signals."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

TASK = Path(__file__).resolve().parents[1]
ROOT = TASK.parents[1]
sys.path.insert(0, str(TASK / "src"))
from m2_features import AGE, frame_for_condition

parser = argparse.ArgumentParser()
parser.add_argument("--endpoint", choices=["3p45", "3p55"], required=True)
args = parser.parse_args()
out = TASK / "runs" / f"M9_D1_v15_signal_ablation_{args.endpoint}_v1"
out.mkdir(exist_ok=False)
manifest = TASK / "runs" / f"M9_D1_v15_endpoint_{args.endpoint}_v1"
x = frame_for_condition(20, "persistent", manifest / "visibility.csv", manifest / "cropped_events.csv")
panel = pd.read_csv(ROOT / "research/phase2_temperature_improvement/outputs/panel_main.csv")
keys = pd.MultiIndex.from_frame(x[["cell_id", "target_ordinal"]])
y = panel.set_index(["cell_id", "target_ordinal"]).loc[keys, "target_soh_pp"].to_numpy(float)
anchor = x.anchor_pp.to_numpy(float)
cells = x.cell_id.to_numpy(str)
assert len(x) == len(y) == 180 and len(np.unique(cells)) == 6
window = [f"w{i:02d}_{suffix}" for i in range(9) for suffix in ("Ah", "mask")]
feature_sets = {
    "age_only": AGE,
    "age_plus_current": AGE + ["current_A"],
    "age_plus_voltage": AGE + ["v_start_V", "v_end_V"],
    "age_plus_current_voltage": AGE + ["current_A", "v_start_V", "v_end_V"],
    "age_plus_windows": AGE + window,
    "age_plus_windows_current": AGE + window + ["current_A"],
    "full_window_workpoint": AGE + window + ["v_start_V", "v_end_V", "current_A", "observed_span_Ah"],
}
config = json.loads((TASK / "configs/m2_primary_v15.json").read_text())
grid = [(float(alpha), float(length)) for alpha in config["rbf_alpha_grid"]
        for length in config["rbf_lengthscale_grid"]]


def matrices(train, test, columns):
    a, b = x.iloc[train][columns].to_numpy(float), x.iloc[test][columns].to_numpy(float)
    med = np.array([np.nanmedian(col) if np.isfinite(col).any() else 0. for col in a.T])
    a, b = np.where(np.isfinite(a), a, med), np.where(np.isfinite(b), b, med)
    mean, scale = a.mean(0), a.std(0)
    scale = np.where(scale >= 1e-10, scale, 1.)
    return (a - mean) / scale, (b - mean) / scale


def ridge(a, target, b, alpha=10.):
    aa, bb = np.column_stack([np.ones(len(a)), a]), np.column_stack([np.ones(len(b)), b])
    penalty = np.diag([0.] + [alpha] * a.shape[1])
    return bb @ np.linalg.solve(aa.T @ aa + penalty + np.eye(aa.shape[1])*1e-10, aa.T @ target)


def predict(method, params, train, test):
    age_a, age_b = matrices(train, test, AGE)
    target = y[train] - anchor[train]
    if method == "age_only":
        return anchor[test] + ridge(age_a, target, age_b, 10.)
    a, b = matrices(train, test, feature_sets[method])
    baseline_train, baseline_test = ridge(age_a, target, age_a), ridge(age_a, target, age_b)
    alpha, length = params
    kern = np.exp(-np.mean((a[:, None, :] - a[None, :, :])**2, axis=2)/(2*length**2))
    cross = np.exp(-np.mean((b[:, None, :] - a[None, :, :])**2, axis=2)/(2*length**2))
    delta = cross @ np.linalg.solve(kern + np.eye(len(train))*alpha, target-baseline_train)
    return anchor[test] + baseline_test + delta


rows, choices = [], []
for held in np.unique(cells):
    outer_test = np.flatnonzero(cells == held)
    outer_train = np.flatnonzero(cells != held)
    for method in feature_sets:
        if method == "age_only":
            chosen, inner = None, np.nan
        else:
            scores = []
            for gi, params in enumerate(grid):
                fold_mae = []
                for inner_held in np.unique(cells[outer_train]):
                    val = outer_train[cells[outer_train] == inner_held]
                    fit = outer_train[cells[outer_train] != inner_held]
                    fold_mae.append(float(np.mean(abs(predict(method, params, fit, val)-y[val]))))
                scores.append((float(np.mean(fold_mae)), gi, params))
            inner, _, chosen = min(scores)
        choices.append({"held_cell": held, "method": method, "selected_json": json.dumps(chosen),
                        "inner_macro_mae_pp": inner})
        pred = predict(method, chosen, outer_train, outer_test)
        for index, value in zip(outer_test, pred):
            rows.append({"cell_id": cells[index], "target_ordinal": int(x.target_ordinal.iat[index]),
                         "method": method, "target_soh_pp": float(y[index]),
                         "pred_soh_pp": float(value), "error_pp": float(value-y[index]),
                         "endpoint": args.endpoint, "held_cell": held})
    print("held", held, flush=True)
predictions = pd.DataFrame(rows)
predictions.to_csv(out / "predictions.csv", index=False)
pd.DataFrame(choices).to_csv(out / "inner_selections.csv", index=False)
metrics = []
for method, part in predictions.groupby("method"):
    assert len(part) == 180 and not part.duplicated(["cell_id", "target_ordinal"]).any()
    per = part.error_pp.abs().groupby(part.cell_id).mean()
    metrics.append({"method": method, "macro_mae_pp": float(per.mean()),
                    "worst_cell_mae_pp": float(per.max()),
                    "max_absolute_error_pp": float(part.error_pp.abs().max())})
summary = {"endpoint": args.endpoint, "protocol": "v1.5 prefix-only",
           "n_physical_cells": 6, "n_targets_per_method": 180, "metrics": metrics,
           "interpretation_limit": "P1 six-cell development; workpoint ablation, no official capacity truth."}
(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({m["method"]: m["macro_mae_pp"] for m in metrics}, ensure_ascii=False), flush=True)
