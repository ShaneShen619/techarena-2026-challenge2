"""Audit M0 against its actual files and register reproducible runs."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
OLD = ROOT / "research/phase2_validation"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    panel_path = TASK / "outputs/panel_main.csv"
    panel = pd.read_csv(panel_path)
    history = pd.read_csv(TASK / "runs/M0_history_replay_v1/historical_comparison.csv")
    current = pd.read_csv(TASK / "outputs/predictions.csv")
    thermal = pd.read_csv(TASK / "outputs/thermal_held_cell.csv")
    old_details = pd.read_csv(OLD / "outputs/a_failure_review/selected_event_references.csv")
    old_model = OLD / "candidates/route_a/my_model/model_route_a.py"
    render = TASK / "runs/M0_report_render"
    official = pd.read_csv(TASK / "runs/M0_official_smoke/output.csv")
    key_checks = {
        "panel_180_6x30": len(panel) == 180 and panel.groupby("cell_id").size().eq(30).all(),
        "historical_18_exact": len(history) == 18 and history.delta_prediction_pp.abs().max() < 1e-9,
        "old_a_and_b0_180_each": set(current.method) == {"A_old", "B0"} and current.groupby("method").size().eq(180).all(),
        "official_ck3_cross_process": official.checkup.tolist() == ["CK3"] and len(official) == 1,
        "render_9_pages": len(list(render.glob("page-*.png"))) == 9,
        "thermal_sixfold": set(thermal.method) == {"nominal", "constant_dT", "linear", "physical"} and thermal.groupby("method").size().eq(6).all(),
        "known_failures_present": all((old_details.cell_id == cell).any() for cell in (
            "102Ah_25degC_1C_cell3", "102Ah_45degC_1C_cell1", "102Ah_55degC_1C_cell3")),
    }
    key_checks = {name: bool(passed) for name, passed in key_checks.items()}
    if not all(key_checks.values()):
        raise AssertionError(key_checks)
    joined = current.merge(panel[["cell_id", "target_cycle", "target_soh_pp"]], on=["cell_id", "target_cycle"])
    errors = joined.assign(abs_error=(joined.prediction_soh_pp-joined.target_soh_pp).abs())
    method_mae = errors.groupby("method").abs_error.mean().to_dict()
    known = {}
    for cell in ("102Ah_25degC_1C_cell3", "102Ah_45degC_1C_cell1", "102Ah_55degC_1C_cell3"):
        rows = old_details[old_details.cell_id.eq(cell)]
        known[cell] = {"max_paired_temperature_gap_C": float((rows.event_temp_C-rows.reference_temp_C).abs().max()),
                       "window_ratio_min": float(rows.ratio.min()),
                       "window_ratio_max": float(rows.ratio.max())}
    result = {"status": "M0_fact_checks_passed_accuracy_not_yet_met", "checks": key_checks,
              "panel_sha256": sha(panel_path), "old_model_sha256": sha(old_model),
              "historical_A_old_max_prediction_delta_pp": float(history.delta_prediction_pp.abs().max()),
              "main_panel_mae_pp": method_mae,
              "historical_failure_cases": known,
              "official_ck3_prediction_soh_pp_unlabeled": float(official.SOH_est.iloc[0]),
              "render_pages": 9,
              "note": "Rendered prior report is M0 environment smoke; final new Word remains pending."}
    (TASK / "runs/M0_fact_check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    entries = [
        ("M0_history_replay_v1", "M0", "A_old|B0", OLD / "outputs/phase1_crossvalidation_predictions.csv", old_model,
         "bash research/phase2_validation/run_python.sh research/phase2_temperature_improvement/scripts/run_m0_baselines.py --historical",
         TASK / "runs/M0_history_replay_v1/predictions.csv", "18 historical targets; exact comparison"),
        ("M0_A_old_B0_180_v1", "M0", "A_old|B0", panel_path, old_model,
         "bash research/phase2_validation/run_python.sh research/phase2_temperature_improvement/scripts/run_m0_baselines.py",
         TASK / "runs/M0_A_old_B0_180_v1/predictions.csv", "180 frozen P1 proxy targets"),
        ("M1_thermal_sixfold_v1", "M1", "physical|nominal|constant_dT|linear", panel_path,
         TASK / "src/thermal_surface.py",
         "bash research/phase2_validation/run_python.sh research/phase2_temperature_improvement/scripts/run_m1_thermal.py",
         TASK / "outputs/thermal_held_cell.csv", "Heldout measured lifetime mean is diagnostic truth only"),
    ]
    path = TASK / "notes/EXPERIMENT_INDEX.csv"
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["run_id", "module", "method", "config_path", "input_hash", "code_hash", "command", "exit_code", "seconds", "output_path", "notes"])
        writer.writeheader()
        for run_id, module, method, inp, code, command, output, note in entries:
            writer.writerow({"run_id": run_id, "module": module, "method": method,
                             "config_path": "configs/acceptance.json", "input_hash": sha(inp),
                             "code_hash": sha(code), "command": command, "exit_code": 0,
                             "seconds": "", "output_path": str(output.relative_to(ROOT)), "notes": note})
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
