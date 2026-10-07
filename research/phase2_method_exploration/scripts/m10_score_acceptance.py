"""Recompute final acceptance from frozen labels, raw predictions and test receipts."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

TASK = Path(__file__).resolve().parents[1]
ROOT = TASK.parents[1]
OUT = TASK / "outputs"
RUNS = TASK / "runs"
RECEIPT = RUNS / "M10_correctness_suite_v1"
RECEIPT.mkdir(exist_ok=True)

panel_path = ROOT / "research/phase2_temperature_improvement/outputs/panel_main.csv"
panel_sha = hashlib.sha256(panel_path.read_bytes()).hexdigest()
assert panel_sha == "7188b662900f84312292a7062d6023e5eeb4f2e32798b6d61a3547ed40cdc59c"
panel = pd.read_csv(panel_path, usecols=["cell_id", "target_ordinal", "target_soh_pp"])
assert len(panel) == 180 and not panel.duplicated(["cell_id", "target_ordinal"]).any()
keys = ["cell_id", "target_ordinal"]


def score(frame: pd.DataFrame, pred_column: str, embedded_truth: str) -> dict:
    assert len(frame) == 180 and not frame.duplicated(keys).any()
    supplied = frame[keys + [pred_column, embedded_truth]].rename(
        columns={embedded_truth: "embedded_truth"})
    joined = panel.merge(supplied, on=keys,
                         how="left", validate="one_to_one")
    assert len(joined) == 180 and joined[pred_column].notna().all()
    assert np.all(np.isfinite(joined[pred_column].to_numpy(float)))
    assert np.max(abs(joined.target_soh_pp - joined.embedded_truth)) < 1e-4
    error = joined[pred_column] - joined.target_soh_pp
    per = error.abs().groupby(joined.cell_id).mean()
    return {"macro_mae_pp": float(per.mean()), "worst_cell_mae_pp": float(per.max()),
            "max_abs_error_pp": float(error.abs().max()), "p95_abs_error_pp": float(error.abs().quantile(.95)),
            "bias_pp": float(error.mean()), "per_cell_mae_pp": per.to_dict(), "targets": len(joined)}


baseline_run = "M9_D1_v15_M2_20Ah_persistent_v1"
base = pd.read_csv(RUNS / baseline_run / "predictions.csv")
baselines = {}
for method in ("anchor_constant", "age_ridge", "fixed_window_ridge", "mask_ridge",
               "within_cell_ratio_ridge", "rbf_residual"):
    baselines[method] = score(base.loc[base.method.eq(method)], "pred_soh_pp", "target_soh_pp")
best_baseline_name = min(baselines, key=lambda name: baselines[name]["macro_mae_pp"])
best_baseline = baselines[best_baseline_name]

tcn = pd.read_csv(RUNS / "M9_D1_v15_TCN_v1/predictions.csv")
tcn = tcn.loc[tcn.method.eq("TCN_finetune")]
assert set(tcn.seed) == {20260928, 20260929, 20260930}
assert tcn.groupby(keys).size().eq(3).all()
candidate = tcn.groupby(keys, as_index=False).agg(
    pred_soh_pp=("pred_soh_pp", "mean"), target_soh_pp=("target_soh_pp", "first"))
candidate_score = score(candidate, "pred_soh_pp", "target_soh_pp")
relative = 1 - candidate_score["macro_mae_pp"] / best_baseline["macro_mae_pp"]

test_results = []
for name in ("test_visibility_boundary.py", "test_visibility_v15.py", "test_m4_audit.py",
             "test_m5_pack.py", "test_m5_outputs.py", "test_m6_audit.py",
             "test_endpoint_v15.py"):
    result = subprocess.run([sys.executable, str(TASK / "tests" / name)], cwd=ROOT,
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
    test_results.append({"test": name, "exit_code": result.returncode,
                         "stdout": result.stdout.strip()[-1200:], "stderr": result.stderr.strip()[-1200:]})
(RECEIPT / "tests.json").write_text(json.dumps(test_results, ensure_ascii=False, indent=2) + "\n")

hard = {}
for candidate_name in ("ck0_hold", "exploratory_fallback"):
    path = RUNS / f"M10_{candidate_name}_hard_tests_v2/summary.json"
    hard[candidate_name] = json.loads(path.read_text())
    report = (RUNS / "M10_clean_extract_v1" / candidate_name / "validation_report.txt").read_text()
    assert "PASSED" in report
v15 = json.loads((RUNS / "M9_D1_v15_inputs_v1/summary.json").read_text())
prefix_replay = json.loads((RUNS / "M9_prefix_stop_replay_v2/summary.json").read_text())
endpoint = {name: json.loads((RUNS / f"M9_D1_v15_endpoint_{name}_v1/summary.json").read_text())
            for name in ("3p45", "3p55")}
permutation = json.loads((RUNS / "M5_permutation_recheck_v1/summary.json").read_text())
official = json.loads((RUNS / "M9_official_replay_v1/summary.json").read_text())
smoke = json.loads((RUNS / "M0_smoke_v2/smoke.json").read_text())
correctness = bool(all(x["exit_code"] == 0 for x in test_results) and
                   all(x["hard_correctness_pass"] and len(x["tests"]) >= 9 for x in hard.values()) and
                   v15["selected_events"] == 952 and v15["target_views"] == 1080 and
                   v15["model_input_labels_absent"] and v15["forbidden_full_event_end_only_in_restricted_audit"] and
                   prefix_replay["all_1080_target_views_equal"] and
                   prefix_replay["candidate_emission_uses_full_run_end"] is False and
                   prefix_replay["eligible_counts"] == {"15": 18570, "20": 18566, "30": 18558} and
                   all(item["selection_uses_post_endpoint"] is False and
                       item["target_views"] == 1080 and item["zero_event_views"] == 0
                       for item in endpoint.values()) and
                   permutation["passed"] and smoke["serialization_fresh_process_max_diff_pp"] == 0 and
                   official["all_operation_prefixes_causal"])
thresholds = json.loads((TASK / "configs/acceptance.json").read_text())["d1_aspirational_thresholds"]
d1_met = bool(relative >= thresholds["relative_macro_mae_improvement_vs_strongest_eligible_baseline"] and
              candidate_score["macro_mae_pp"] <= thresholds["macro_mae_pp_max"] and
              candidate_score["worst_cell_mae_pp"] <= thresholds["worst_cell_mae_pp_max"] and
              candidate_score["max_abs_error_pp"] <= thresholds["max_absolute_error_pp_max"] and
              candidate_score["worst_cell_mae_pp"] <= best_baseline["worst_cell_mae_pp"])
required_close = ["outputs/LFP_SOH_多路线设计验证与比较报告.md",
                  "outputs/EXECUTIVE_SUMMARY.md", "outputs/MEASUREMENT_PLAN.md",
                  "outputs/event_catalog.csv", "outputs/method_comparison.csv",
                  "outputs/predictions_long.csv", "outputs/official_predictions.csv",
                  "outputs/official_diagnostics.csv", "notes/M9_FINDINGS.md",
                  "notes/FINAL_AUDIT.md", "notes/READER_TEST.md",
                  "notes/STATUS.md", "notes/RESUME.md", "notes/PROTOCOL.md",
                  "notes/READINESS.md", "notes/ASSUMPTIONS.md", "notes/DECISIONS.md",
                  "notes/FAILURES.md", "notes/DATA_GAPS.md",
                  "notes/EXPERIMENT_INDEX.csv", "notes/HYPOTHESIS_BACKLOG.csv",
                  "configs/acceptance.json", "README.md", "REPRODUCE.md"]
required_close += [f"notes/M{n}_FINDINGS.md" for n in range(1, 10)]
closed_files = {path: (TASK / path).exists() for path in required_close}
backlog = pd.read_csv(TASK / "notes/HYPOTHESIS_BACKLOG.csv")
high_required = backlog.loc[backlog.priority.eq("high") & backlog.decision.eq("accepted_required")]
high_closed = bool(high_required.status.str.startswith(("tested", "signal_test_completed")).all())
research_closed = bool(correctness and high_closed and all(closed_files.values()))
result = {"correctness_pass": correctness, "d1_target_met": d1_met,
          "performance_target_met": d1_met,
          "d2_confirmation_status": "not_available",
          "independent_capacity_confirmation": False,
          "official_capacity_accuracy_verified": False,
          "research_closed": research_closed,
          "audit_level": "independent_reviewer" if (TASK / "notes/FINAL_AUDIT.md").exists() else "not_finished",
          "d1_protocol": "v1.5 strict shallow-prefix, P1 six-cell development proxy",
          "strongest_same_input_baseline": {"method": best_baseline_name, **best_baseline},
          "research_candidate": {"method": "TCN_finetune_three_seed_ensemble", **candidate_score},
          "relative_macro_mae_improvement": float(relative),
          "thresholds": thresholds,
          "correctness_evidence": ["runs/M10_correctness_suite_v1/tests.json",
              "runs/M10_ck0_hold_hard_tests_v2/summary.json",
              "runs/M10_exploratory_fallback_hard_tests_v2/summary.json",
              "runs/M5_permutation_recheck_v1/summary.json",
              "runs/M9_D1_v15_inputs_v1/summary.json",
              "runs/M9_prefix_stop_replay_v2/summary.json",
              "runs/M9_D1_v15_endpoint_3p45_v1/summary.json",
              "runs/M9_D1_v15_endpoint_3p55_v1/summary.json",
              "runs/M0_smoke_v2/smoke.json"],
          "required_delivery_files_present": closed_files,
          "high_priority_hypotheses_closed": high_closed,
          "claim_limit": "D1 is reused six-cell P1 high-rate proxy, not independent four-series C/20 confirmation; CK1-CK7 truth hidden."}
(OUT / "acceptance_results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({k: result[k] for k in ("correctness_pass", "d1_target_met", "research_closed",
                                         "relative_macro_mae_improvement", "audit_level")}, ensure_ascii=False))
