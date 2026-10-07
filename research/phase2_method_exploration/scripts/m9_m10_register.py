"""Register immutable M9/M10 and strict-v1.5 experiments with hashes."""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

TASK = Path(__file__).resolve().parents[1]
INDEX = TASK / "notes/EXPERIMENT_INDEX.csv"
PANEL = TASK.parents[1] / "research/phase2_temperature_improvement/outputs/panel_main.csv"
VIS = TASK / "data_manifests/d1_v15_target_visibility.csv"
CK0 = TASK.parents[1] / "data/checkups/CK0_reference_discharge.csv.gz"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "not_applicable"


# run, module, code, config, metric, conclusion, status
spec = [
    ("M8_pack_fusion_v2", "M8", "m8_pack_fusion_v2.py", "m8_pack_fusion.json", "summary.json", "weight/calibration/test scenes separated; synthetic oracle quality only", "completed_synthetic"),
    ("M9_shallow_prefix_eligibility_v1", "M9", "m9_shallow_prefix_eligibility_audit.py", "acceptance.json", "summary.json", "D1 v1.4 full-event selection changed all 180 target views", "completed_audit"),
    ("M9_D1_v15_inputs_v1", "M9", "m9_crop_d1_v15.py", "m2_primary_v15.json", "summary.json", "952 selected prefix endpoints; 1080 target views", "completed_development_only"),
    ("M9_D1_v15_target_map_v1", "M9", "m9_d1_v15_target_map.py", "m9_d1_v15_representation.json", "summary.json", "180 label-free target-to-event maps", "completed_development_only"),
    ("M9_D1_v15_M2_15Ah_persistent_v1", "M9", "m2_primary_v15.py", "m2_primary_v15.json", "summary.json", "strict-prefix 15Ah sensitivity", "completed_development_only"),
    ("M9_D1_v15_M2_20Ah_persistent_v1", "M9", "m2_primary_v15.py", "m2_primary_v15.json", "summary.json", "strict-prefix 20Ah primary; best simple method 3.755pp", "completed_development_only"),
    ("M9_D1_v15_M2_30Ah_persistent_v1", "M9", "m2_primary_v15.py", "m2_primary_v15.json", "summary.json", "strict-prefix 30Ah sensitivity", "completed_development_only"),
    ("M9_D1_v15_M2_20Ah_cold_v1", "M9", "m2_primary_v15.py", "m2_primary_v15.json", "summary.json", "strict-prefix cold-start sensitivity", "completed_development_only"),
    ("M9_D1_v15_linear_v1", "M9", "m9_d1_v15_linear.py", "m9_d1_v15_representation.json", "summary.json", "PCA voltage reconstruction does not transfer capacity", "completed_development_only"),
    ("M9_D1_v15_spline_v1", "M9", "m9_d1_v15_spline.py", "m2_spline.json", "summary.json", "temperature-rate spline 4.059pp", "completed_development_only"),
    ("M9_D1_v15_TCN_v1", "M9", "m9_d1_v15_tcn.py", "m9_d1_v15_representation.json", "summary.json", "fine-tune ensemble 2.851pp; absolute and tail thresholds fail", "completed_development_only"),
    ("M9_D1_v15_no_voltage_v1", "M9", "m9_d1_v15_no_voltage.py", "m9_d1_v15_representation.json", "summary.json", "no-voltage ensemble 3.066pp vs scratch 3.073pp", "completed_development_only"),
    ("M9_D1_v15_meta_only_v1", "M9", "m9_d1_v15_meta_only.py", "m9_d1_v15_representation.json", "summary.json", "mask/meta-only ensemble 2.896pp", "completed_development_only"),
    ("M9_D1_v15_scalar_models_v1", "M9", "m9_d1_v15_scalar_models.py", "m9_scalar_models.json", "summary.json", "scalar MLP ensemble 3.216pp", "completed_development_only"),
    ("M9_D1_v15_prefix_temperature_v1", "M9", "m9_d1_v15_prefix_temperature_mlp.py", "m9_scalar_models.json", "summary.json", "allowed fragment temperature MLP ensemble 2.933pp; worst cell 4.966pp", "completed_development_only"),
    ("M9_D1_v15_fusion_v1", "M9", "m9_d1_v15_fusion.py", "m8_fusion.json", "summary.json", "prediction-channel +10pp tests ambiguously named; superseded by v2", "retired_development"),
    ("M9_D1_v15_fusion_v2", "M9", "m9_d1_v15_fusion_v2.py", "m8_fusion.json", "summary.json", "gate 2.855pp, no gain over 2.851pp best single", "completed_development_only"),
    ("M9_prefix_stop_replay_v1", "M9", "m9_prefix_stop_replay.py", "acceptance.json", "prefix_only_crossings.csv", "five too-short crossings inadvertently dropped before rejection recording", "failed_retained"),
    ("M9_prefix_stop_replay_v2", "M9", "m9_prefix_stop_replay_v2.py", "acceptance.json", "summary.json", "prefix-only eligibility sets and 1080 views match v1.5", "completed_audit"),
    ("M9_D1_v15_endpoint_3p45_v1", "M9", "m9_endpoint_sensitivity_v15.py", "m2_primary_v15.json", "summary.json", "3.45V prefix-only endpoint sensitivity; 1080 views", "completed_audit"),
    ("M9_D1_v15_endpoint_3p55_v1", "M9", "m9_endpoint_sensitivity_v15.py", "m2_primary_v15.json", "summary.json", "3.55V prefix-only endpoint sensitivity; 1080 views", "completed_audit"),
    ("M9_D1_v15_M2_3p45_20Ah_persistent_v1", "M9", "m9_d1_v15_endpoint_baselines.py", "m2_primary_v15.json", "summary.json", "3.45V nested-cell baseline sensitivity", "completed_development_only"),
    ("M9_D1_v15_M2_3p55_20Ah_persistent_v1", "M9", "m9_d1_v15_endpoint_baselines.py", "m2_primary_v15.json", "summary.json", "3.55V nested-cell baseline sensitivity", "completed_development_only"),
    ("M9_D1_v15_signal_ablation_3p45_v1", "M9", "m9_d1_v15_endpoint_signal_ablation.py", "m2_primary_v15.json", "summary.json", "3.45V current/voltage/window ablation; interaction conditional", "completed_development_only"),
    ("M9_D1_v15_signal_ablation_3p55_v1", "M9", "m9_d1_v15_endpoint_signal_ablation.py", "m2_primary_v15.json", "summary.json", "3.55V current/voltage/window ablation; interaction conditional", "completed_development_only"),
    ("M9_official_replay_v1", "M9", "m9_official_replay.py", "acceptance.json", "summary.json", "CK1-CK7 strict-prefix predictions only; capacity truth hidden", "completed_unlabeled"),
    ("M5_permutation_recheck_v1", "M10", "m5_permutation_recheck.py", "acceptance.json", "summary.json", "100 independent physical permutations passed", "completed_audit"),
    ("M10_ck0_hold_hard_tests_v2", "M10", "m10_candidate_hard_tests_v2.py", "acceptance.json", "summary.json", "nine hard tests pass at strict numeric tolerance", "completed_correctness"),
    ("M10_exploratory_fallback_hard_tests_v2", "M10", "m10_candidate_hard_tests_v2.py", "acceptance.json", "summary.json", "nine hard tests pass at strict numeric tolerance", "completed_correctness"),
    ("M10_correctness_suite_v1", "M10", "m10_score_acceptance.py", "acceptance.json", "tests.json", "six independent local audit tests rerun", "completed_correctness"),
]
with INDEX.open(newline="") as handle:
    reader = csv.DictReader(handle)
    fields = reader.fieldnames
    rows = list(reader)
assert fields is not None
seen = {row["run_id"] for row in rows}
for run, module, script, config, metric, conclusion, status in spec:
    if run in seen:
        continue
    artifact = TASK / "runs" / run
    assert artifact.is_dir() and (artifact / metric).is_file(), run
    source = (TASK / "runs" / f"M9_D1_v15_endpoint_{'3p45' if '3p45' in run else '3p55'}_v1/visibility.csv") if "M2_3p" in run or "signal_ablation_3p" in run else (
        VIS if ("D1_v15" in run or "prefix_stop" in run or "shallow_prefix" in run) else (
        CK0 if ("official" in run or run.startswith("M5_") or run.startswith("M8_pack")) else PANEL)
    )
    rows.append(dict(run_id=run, module=module, question=conclusion,
        input_sha256=sha(source),
        code_sha256=sha(TASK / "scripts" / script), config_sha256=sha(TASK / "configs" / config),
        label_protocol="P1 six-cell development proxy" if "D1" in run else
                       "synthetic mechanism" if run.startswith("M8_pack") or run.startswith("M5") else
                       "official hidden capacity" if "official_replay" in run else "audit only",
        split="entire physical cell nested" if "D1" in run else "run-specific; inspect artifact",
        seed="20260928/29/30" if "TCN" in run or "scalar_models" in run else "run-specific",
        status=status, metric_path=f"runs/{run}/{metric}", artifact_path=f"runs/{run}",
        elapsed_s="not_recorded", peak_rss_mb="not_recorded", conclusion=conclusion))
with INDEX.open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
print(f"registered {len(rows)} total experiment rows")
