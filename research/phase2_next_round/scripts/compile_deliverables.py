"""Compile cross-route tables, acceptance fields, and artifact hashes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

TASK = Path(__file__).resolve().parents[1]
ROOT = TASK.parents[1]
OUT = TASK / "outputs"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


# Comparable D1 capacity metrics.
r0 = pd.read_csv(OUT / "r0_baseline_recompute.csv")
r0.insert(0, "route", "R0_recompute")
r0["tier"] = "D1"
r0["selection_role"] = r0.method.map({
    "within_cell_ratio_ridge": "strong_simple_baseline",
    "TCN_finetune": "previous_and_current_average_choice",
    "prefix_temperature_MLP": "previous_tail_reference",
}).fillna("mechanism_reference")
r1 = pd.read_csv(OUT / "r1_condition_comparison.csv").rename(columns={"condition": "method"})
r1.insert(0, "route", "R1_paired_ablation")
r1["tier"] = "D1"
r1["selection_role"] = r1.method.map({
    "full": "average_error_choice",
    "full_tail_weight2": "tail_risk_choice",
}).fillna("paired_mechanism_ablation")
common = ["route", "tier", "method", "selection_role", "macro_MAE_pp",
          "worst_cell_MAE_pp", "max_abs_error_pp", "p95_abs_error_pp",
          "late_macro_MAE_pp", "late_worst_cell_MAE_pp", "targets", "cells"]
comparison = pd.concat([r0[common], r1[common]], ignore_index=True)
comparison["independent_confirmation"] = False
comparison["official_accuracy"] = False
comparison.to_csv(OUT / "method_comparison.csv", index=False)

# Long-form pointwise results for the new experiments.
long_parts = []
for condition in ["full", "no_voltage", "meta_only", "no_temperature", "no_temperature_strict", "full_tail_weight2"]:
    src = TASK / "runs" / f"R1_paired_TCN_{condition}_v1" / "ensemble_predictions.csv"
    d = pd.read_csv(src)
    long_parts.append(pd.DataFrame({
        "run_id": f"R1_paired_TCN_{condition}_v1", "tier": "D1",
        "entity": d.cell_id, "target_id": d.target_ordinal, "method": condition,
        "seed": "three_seed_ensemble", "unit": "SOH_pp",
        "label_protocol": "P1 single-cell high-rate discharge proxy",
        "input_budget": "strict causal D1 v1.5; 20Ah; 3.50V first crossing",
        "truth": d.target_soh_pp, "prediction": d.pred_soh_pp,
        "error": d.error_pp, "true_label_available": True,
    }))
r2 = pd.read_csv(OUT / "r2_counterfactual_predictions.csv")
long_parts.append(pd.DataFrame({
    "run_id": "R2_counterfactual_reanalysis_v1", "tier": "D1_counterfactual",
    "entity": r2.cell_id, "target_id": r2.target_ordinal.astype(str) + "_" + r2.condition.astype(str),
    "method": r2.method, "seed": "frozen", "unit": "SOH_pp",
    "label_protocol": "P1 single-cell high-rate discharge proxy",
    "input_budget": r2.axis.astype(str) + ":" + r2.condition.astype(str),
    "truth": r2.target_soh_pp, "prediction": r2.pred_soh_pp, "error": r2.error_pp,
    "true_label_available": True,
}))
official = pd.read_csv(OUT / "official_prefix_diagnostics.csv")
long_parts.append(pd.DataFrame({
    "run_id": "R6_official_prefix_replay_v1", "tier": "D3",
    "entity": "official_4S_pack", "target_id": official.checkup, "method": official.candidate,
    "seed": "deterministic", "unit": "SOH_pp",
    "label_protocol": "5.1A to 11.2V group cutoff",
    "input_budget": "all operation rows at or before checkpoint",
    "truth": official.true_SOH_pp, "prediction": official.SOH_est_pp,
    "error": official.absolute_error_pp, "true_label_available": official.true_SOH_pp.notna(),
}))
pd.concat(long_parts, ignore_index=True).to_csv(OUT / "predictions_long.csv", index=False)

best = r1.set_index("method").loc["full"]
observed = r1.set_index("method").loc["no_temperature_strict"]
tail = r1.set_index("method").loc["full_tail_weight2"]
simple = r0.set_index("method").loc["within_cell_ratio_ridge"]
previous = r0.set_index("method").loc["TCN_finetune"]
required_files = [OUT / "r1_condition_comparison.csv", OUT / "r2_counterfactual_summary.json",
                  OUT / "r3_pulse_summary.json", OUT / "r4_state_pack_summary.json",
                  OUT / "measurement_plan.md", OUT / "official_prefix_diagnostics.csv",
                  OUT / "candidate_package_manifest.json", TASK / "REPRODUCE.md"]
hard = [json.loads((TASK / "runs" / f"R6_{name}_hard_tests_v1" / "summary.json").read_text())
        for name in ("ck0_hold", "exploratory_fallback")]
validator_paths = [TASK / "candidates" / name / "validation_report.txt"
                   for name in ("ck0_hold", "exploratory_fallback")]
validator_paths += [TASK / "runs/R6_clean_extract_v1" / name / "validation_report.txt"
                    for name in ("ck0_hold", "exploratory_fallback")]
correctness_checks = {
    "required_files_present": all(path.exists() for path in required_files),
    "r1_all_conditions_complete": bool((r1.targets.eq(180) & r1.cells.eq(6)).all()) and "no_temperature_strict" in set(r1.method),
    "candidate_hard_tests_pass": all(item["hard_correctness_pass"] for item in hard),
    "original_and_clean_validator_pass": all(path.exists() and "PASSED - output schema satisfied" in path.read_text() for path in validator_paths),
    "official_hidden_truth_blank": bool(official.loc[official.checkup.ne("CK0"), ["true_SOH_pp", "absolute_error_pp"]].isna().all().all()),
    "root_model_not_silently_switched": "ExampleModel as ActiveModel" in (ROOT / "my_model/__init__.py").read_text(),
}
correctness_pass = all(correctness_checks.values())
audit_ready = (TASK / "notes/INDEPENDENT_AUDIT.md").exists()
reader_ready = (TASK / "notes/READER_TEST.md").exists()
docx_ready = (OUT / "LFP_SOH_下一轮逐路线验证与决策报告.docx").exists()
rendered_pages = sorted((TASK / "rendered_verified").glob("page-*.png")) if (TASK / "rendered_verified").exists() else []
render_ready = bool(rendered_pages) and all(path.stat().st_size > 0 for path in rendered_pages)
research_closed = correctness_pass and audit_ready and reader_ready and docx_ready and render_ready
acceptance = {
    "correctness_pass": correctness_pass,
    "correctness_checks": correctness_checks,
    "d1_target_met": False,
    "d1_thresholds": {"macro_MAE_pp": 1.0, "worst_cell_MAE_pp": 2.0,
                      "max_abs_error_pp": 5.0, "relative_improvement_vs_simple_pct": 20.0},
    "d1_observed": {"macro_MAE_pp": float(best.macro_MAE_pp),
                    "worst_cell_MAE_pp": float(best.worst_cell_MAE_pp),
                    "max_abs_error_pp": float(best.max_abs_error_pp),
                    "relative_improvement_vs_simple_pct": float(100 * (simple.macro_MAE_pp - best.macro_MAE_pp) / simple.macro_MAE_pp)},
    "improvement_vs_previous_best": {
        "overall": False,
        "average_choice_macro_delta_pp": float(best.macro_MAE_pp - previous.macro_MAE_pp),
        "tail_choice_macro_delta_pp": float(tail.macro_MAE_pp - previous.macro_MAE_pp),
        "tail_choice_worst_delta_pp": float(tail.worst_cell_MAE_pp - previous.worst_cell_MAE_pp),
        "tail_choice_max_delta_pp": float(tail.max_abs_error_pp - previous.max_abs_error_pp),
        "tail_choice_late_macro_delta_pp": float(tail.late_macro_MAE_pp - previous.late_macro_MAE_pp),
        "post_audit_strict_no_temperature_macro_delta_pp": float(observed.macro_MAE_pp - previous.macro_MAE_pp),
        "post_audit_strict_no_temperature_worst_delta_pp": float(observed.worst_cell_MAE_pp - previous.worst_cell_MAE_pp),
        "post_audit_strict_no_temperature_max_delta_pp": float(observed.max_abs_error_pp - previous.max_abs_error_pp),
        "tradeoff": "Strict temperature removal is the observed macro leader but worsens worst-cell and maximum error and was not selected by a nested inner-entity rule. Tail weighting slightly improves tail metrics but worsens overall macro MAE."
    },
    "selection_validity": {
        "locked_average_candidate": "full TCN retained from the previous frozen result",
        "strict_no_temperature": "post-audit mechanism repair and outer-panel observation; requires nested or new-entity confirmation before selection",
        "tail_weight2": "predefined experiment but outer-panel exploratory comparison; no valid inner-entity selector was implemented",
    },
    "signal_increment_supported": {
        "temperature_on_D1_proxy": "mixed_tradeoff_not_stable",
        "voltage_waveform_for_capacity_on_D1_proxy": "not_supported_by_paired_ablation",
        "pulse_early1Ah_to_same_pulse_later_voltage": "supported",
        "pulse_waveform_for_capacity": "not_testable_without_capacity_labels",
        "shallow_window_independent_capacity_signal": "not_established_for_current_pipeline",
        "official_per_cell_capacity_state": "not_identifiable_under_current_prefix",
    },
    "external_transfer_confirmation": False,
    "d2_confirmation_status": "no_protocol_compatible_independent_4S_capacity_dataset",
    "independent_capacity_confirmation": False,
    "official_capacity_accuracy_verified": False,
    "research_closed": research_closed,
    "audit_level": "independent_read_only_plus_fresh_reader_plus_rendered_word" if research_closed else "pending_remaining_delivery_checks",
    "root_active_model": "ExampleModel",
    "root_active_model_is_submission_candidate": False,
}
(OUT / "acceptance_results.json").write_text(json.dumps(acceptance, ensure_ascii=False, indent=2) + "\n")

experiments = [
    ("R0_inventory_v1", "R0", "completed", "data_manifests/source_inventory_summary.json"),
    ("R0_smoke_v1", "R0", "completed", "runs/R0_smoke_v1/smoke.json"),
    ("R0_torch_smoke_v1", "R0", "completed", "runs/R0_torch_smoke_v1/summary.json"),
    ("R0_baseline_recompute_v1", "R0", "completed", "outputs/r0_baseline_recompute.json"),
    ("R1_paired_TCN_full_v1", "R1", "completed", "runs/R1_paired_TCN_full_v1/summary.json"),
    ("R1_paired_TCN_no_voltage_v1", "R1", "completed", "runs/R1_paired_TCN_no_voltage_v1/summary.json"),
    ("R1_paired_TCN_meta_only_v1", "R1", "completed", "runs/R1_paired_TCN_meta_only_v1/summary.json"),
    ("R1_paired_TCN_no_temperature_v1", "R1", "completed", "runs/R1_paired_TCN_no_temperature_v1/summary.json"),
    ("R1_paired_TCN_no_temperature_strict_v1", "R1", "completed_correctness_repair", "runs/R1_paired_TCN_no_temperature_strict_v1/summary.json"),
    ("R1_paired_TCN_full_tail_weight2_v1", "R1", "completed", "runs/R1_paired_TCN_full_tail_weight2_v1/summary.json"),
    ("R2_counterfactual_reanalysis_v1", "R2", "completed", "outputs/r2_counterfactual_summary.json"),
    ("R3_pulse_reanalysis_v1", "R3", "completed", "outputs/r3_pulse_summary.json"),
    ("R4_state_pack_decision_v1", "R4", "completed", "outputs/r4_state_pack_summary.json"),
    ("R5_measurement_validator_v1", "R5", "completed", "runs/R5_measurement_validator_v1/summary.json"),
    ("R5_sample_size_sensitivity_v1", "R5", "completed", "outputs/r5_sample_size_sensitivity.json"),
    ("R6_ck0_hold_hard_tests_v1", "R6", "completed", "runs/R6_ck0_hold_hard_tests_v1/summary.json"),
    ("R6_exploratory_fallback_hard_tests_v1", "R6", "completed", "runs/R6_exploratory_fallback_hard_tests_v1/summary.json"),
    ("R6_candidate_packages_v1", "R6", "completed", "outputs/candidate_package_manifest.json"),
]
pd.DataFrame(experiments, columns=["run_id", "route", "status", "primary_artifact"]).to_csv(
    TASK / "notes" / "EXPERIMENT_INDEX.csv", index=False)

hash_targets = [TASK / "START_PROMPT.md", TASK / "configs/acceptance.json",
                TASK / "configs/r1_paired_tcn.json", OUT / "method_comparison.csv",
                OUT / "predictions_long.csv", OUT / "official_prefix_diagnostics.csv",
                OUT / "acceptance_results.json", OUT / "r2_counterfactual_summary.json",
                OUT / "r3_pulse_summary.json", OUT / "r4_state_pack_summary.json",
                OUT / "r4_upstream_sources.csv", OUT / "candidate_package_manifest.json",
                OUT / "ck0_hold_research_candidate.zip", OUT / "exploratory_fallback_research_candidate.zip",
                OUT / "LFP_SOH_下一轮逐路线验证与决策报告.md",
                OUT / "LFP_SOH_下一轮逐路线验证与决策报告.docx",
                TASK / "rendered_verified/LFP_SOH_下一轮逐路线验证与决策报告.pdf",
                TASK / "notes/INDEPENDENT_AUDIT.md"]
if (TASK / "notes/READER_TEST.md").exists():
    hash_targets.append(TASK / "notes/READER_TEST.md")
for run in (TASK / "runs").glob("R1_paired_TCN_*_v1/summary.json"):
    hash_targets.append(run)
pd.DataFrame([{"path": str(path.relative_to(ROOT)), "sha256": sha(path), "bytes": path.stat().st_size}
              for path in sorted(hash_targets)]).to_csv(OUT / "artifact_hashes.csv", index=False)
print(json.dumps(acceptance, ensure_ascii=False, indent=2))
