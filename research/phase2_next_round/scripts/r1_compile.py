"""Compile paired R1 ablations and target-level counterfactual deltas."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

TASK = Path(__file__).resolve().parents[1]
OUT = TASK / "outputs"
conditions = ["full", "no_voltage", "meta_only", "no_temperature", "no_temperature_strict", "full_tail_weight2"]
summaries = []
predictions = {}
for condition in conditions:
    run = TASK / "runs" / f"R1_paired_TCN_{condition}_v1"
    summary = json.loads((run / "summary.json").read_text())
    summaries.append(summary)
    frame = pd.read_csv(run / "ensemble_predictions.csv")
    assert len(frame) == 180 and frame.cell_id.nunique() == 6
    predictions[condition] = frame

base = predictions["full"]
rows = []
for condition, frame in predictions.items():
    merged = base.merge(frame, on=["cell_id", "target_ordinal", "target_soh_pp", "late"],
                        suffixes=("_full", "_condition"), validate="one_to_one")
    delta = merged.error_pp_condition.abs() - merged.error_pp_full.abs()
    rows.append({
        "condition": condition,
        "mean_abs_error_delta_vs_full_pp": float(delta.mean()),
        "median_abs_error_delta_vs_full_pp": float(delta.median()),
        "fraction_targets_better_than_full": float((delta < 0).mean()),
        "late_mean_abs_error_delta_vs_full_pp": float(delta[merged.late].mean()),
        "cells_with_lower_MAE_than_full": int(sum(
            frame.loc[frame.cell_id == cell, "error_pp"].abs().mean()
            < base.loc[base.cell_id == cell, "error_pp"].abs().mean()
            for cell in base.cell_id.unique()
        )),
    })

summary_df = pd.DataFrame(summaries)
summary_df = summary_df[["condition", "macro_MAE_pp", "worst_cell_MAE_pp",
                         "max_abs_error_pp", "p95_abs_error_pp", "late_macro_MAE_pp",
                         "late_worst_cell_MAE_pp", "targets", "cells"]]
summary_df.merge(pd.DataFrame(rows), on="condition", validate="one_to_one").to_csv(
    OUT / "r1_condition_comparison.csv", index=False)

strict = summary_df.set_index("condition").loc["no_temperature_strict"]
full = summary_df.set_index("condition").loc["full"]
result = {
    "average_error_choice": "full",
    "average_error_observed_leader_post_audit": "no_temperature_strict",
    "average_error_observed_leader_selection_valid": False,
    "tail_risk_choice": "not_locked; full_tail_weight2 is an outer-panel exploratory comparator",
    "tail_tradeoff_vs_full_pp": {
        key: float(summary_df.set_index("condition").loc["full_tail_weight2", key]
                   - summary_df.set_index("condition").loc["full", key])
        for key in ["macro_MAE_pp", "worst_cell_MAE_pp", "max_abs_error_pp",
                    "p95_abs_error_pp", "late_macro_MAE_pp", "late_worst_cell_MAE_pp"]
    },
    "strict_temperature_ablation_vs_full_pp": {
        key: float(strict[key] - full[key])
        for key in ["macro_MAE_pp", "worst_cell_MAE_pp", "max_abs_error_pp",
                    "p95_abs_error_pp", "late_macro_MAE_pp", "late_worst_cell_MAE_pp"]
    },
    "temperature_increment_supported_on_D1": "mixed_not_stable",
    "voltage_increment_supported_on_D1": False,
    "reason": "The original no_temperature condition retained current_temp_C metadata. The repaired strict ablation improves macro MAE but worsens worst-cell and maximum error, so temperature has a tail-risk tradeoff rather than a stable average benefit. Voltage removal changes macro MAE by only about 0.03 pp.",
    "claim_limit": "Six-cell D1 proxy, repeatedly used for development; no independent capacity confirmation."
}
(OUT / "r1_summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(summary_df.to_string(index=False))
