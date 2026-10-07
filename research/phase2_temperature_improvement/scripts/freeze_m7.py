"""Freeze final candidate/data inputs before independent scoring and reporting."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

TASK = Path(__file__).resolve().parents[1]

FILES = [
    "notes/PROTOCOL.md",
    "configs/acceptance.json",
    "outputs/panel_manifest.json",
    "outputs/panel_main.csv",
    "outputs/predictions.csv",
    "outputs/evidence_events.csv",
    "outputs/temperature_stress.csv",
    "outputs/temperature_stress_evidence.csv",
    "outputs/figures/error_vs_coverage.png",
    "configs/synthetic_mechanism.json",
    "configs/synthetic_curve_variation.json",
    "runs/M6_mechanism_v1/results.csv",
    "runs/M6_curve_variation_v1/results.csv",
    "runs/M4_feature_audit_v1/features.csv",
    "runs/M4_feature_audit_v1/config.json",
    "runs/M4_feature_audit_v1/throughput.csv",
    "runs/M4_feature_audit_v1/events.csv",
    "runs/M4_multi_efc_T_v1/fold_models.json",
    "runs/M4_multi_efc_T_v1/full_six_cell_model.json",
    "runs/M2_A_bugfix_180_v1/evidence_events.csv",
    "runs/M2_A_bugfix_180_v1/config.json",
    "runs/M7_online_replay_v1/predictions.csv",
    "scripts/build_panel.py",
    "scripts/build_m4_features.py",
    "scripts/build_m4_throughput.py",
    "scripts/run_m2_repaired.py",
    "scripts/run_m4_fixed_baseline.py",
    "scripts/run_m4_inner_age.py",
    "scripts/run_m4_inner_inner_age.py",
    "scripts/run_m6_event_stress.py",
    "scripts/run_m6_mechanism.py",
    "scripts/run_m6_curve_variation.py",
    "scripts/build_coverage_plot.py",
    "scripts/replay_online_final.py",
    "scripts/check_acceptance.py",
    "src/event_core.py",
    "src/route_a_repaired.py",
    "src/multi_window_ridge.py",
    "src/thermal_surface.py",
    "candidates/multi_temp/my_model/model.py",
    "candidates/multi_temp/my_model/online_multi_window.py",
    "candidates/multi_temp/my_model/multi_window_ridge.py",
    "candidates/multi_temp/my_model/official_fallback.py",
    "candidates/multi_temp/my_model/route_a_repaired.py",
    "candidates/multi_temp/my_model/event_core.py",
    "candidates/multi_temp/my_model/ridge_p1_pretrained.json",
    "candidates/multi_temp/my_model/windows.json",
]


def main() -> None:
    rows = []
    for rel in FILES:
        file = TASK / rel
        if not file.is_file() or file.stat().st_size == 0:
            raise FileNotFoundError(file)
        rows.append({"path": rel, "sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
                     "size_bytes": file.stat().st_size})
    root = TASK.parents[1]
    raw = root / "dataset original"
    raw_rows = []
    for file in sorted(x for x in raw.rglob("*") if x.is_file()):
        raw_rows.append({"path": str(file.relative_to(root)),
                         "sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
                         "size_bytes": file.stat().st_size})
    if len(raw_rows) != 67:
        raise AssertionError(f"P1 raw inventory changed: {len(raw_rows)} files")
    label_source = Path("/Users/shane/Desktop/项目/Current State_Challenge1/framework/data.py")
    inventory = root / "research/phase2_validation/preflight/downloaded_data/phase1_label_inventory.csv"
    manifest = {"frozen_at_UTC": datetime.now(timezone.utc).isoformat(),
                "protocol": "notes/PROTOCOL.md v1; six-cell developmental grouped validation",
                "files": rows, "raw_p1_files": raw_rows,
                "label_source": {"path": str(label_source),
                                 "sha256": hashlib.sha256(label_source.read_bytes()).hexdigest()},
                "label_inventory": {"path": str(inventory.relative_to(root)),
                                    "sha256": hashlib.sha256(inventory.read_bytes()).hexdigest()},
                "validation_scope": "six-cell P1 proxy; formula reconstruction plus 180-target packaged online replay"}
    (TASK / "runs/M7_frozen_manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    print("frozen", len(rows), "files")


if __name__ == "__main__":
    main()
