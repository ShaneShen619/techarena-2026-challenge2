"""Assertion-based scientific checks used by the M6 hard-test runner."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(TASK / "src"))
sys.path.insert(0, str(TASK / "candidates/multi_temp"))
from framework.data import load_dataset  # noqa: E402
from event_core import extract_charge_events, partial_ah  # noqa: E402
from thermal_surface import effective_temperature  # noqa: E402
from my_model import ActiveModel  # noqa: E402


def causality() -> None:
    ck3 = pd.Timestamp("2025-04-14")
    prefix = load_dataset(ROOT / "data", until=ck3)
    full = load_dataset(ROOT / "data")
    model = ActiveModel(); model.fit(full)
    first = model.estimate_soh(prefix, ck3)
    assert model.last_diagnostics["mode"] == "out_of_domain_shallow_charge_ratio"
    assert all(pd.Timestamp(ev["event_end"]) < ck3 for ev in model.last_diagnostics["event_log"])
    again = model.estimate_soh(prefix, ck3)
    assert abs(first-again) < 1e-9
    model.estimate_soh(full, pd.Timestamp("2025-08-28"))
    reordered = model.estimate_soh(prefix, ck3)
    assert abs(first-reordered) < 1e-9
    full_input = model.estimate_soh(full, ck3)
    assert abs(first-full_input) < 1e-9
    mutated = load_dataset(ROOT / "data")
    future = mutated.operation.timestamp.gt(ck3)
    mutated.operation.loc[future, "temp_mean_C"] = 9999.
    mutated.operation.loc[future, "cell1_V"] = -100.
    mutated.operation.loc[future, "current_A"] = 1e6
    changed_future = model.estimate_soh(mutated, ck3)
    assert abs(first-changed_future) < 1e-9
    print("nontrivial CK3 future append/delete/extreme, repetition, order, reference-time checks passed")


def isolation() -> None:
    panel = TASK / "outputs/panel_main.csv"
    manifest = json.loads((TASK / "outputs/panel_manifest.json").read_text())
    assert hashlib.sha256(panel.read_bytes()).hexdigest() == manifest["panel_sha256"]
    frame = pd.read_csv(TASK / "runs/M4_feature_audit_v1/features.csv")
    assert len(frame) == 180 and "target_soh_pp" not in frame and "step_capacity_Ah" not in frame
    assert (pd.to_datetime(frame.input_end) < pd.to_datetime(frame.target_discharge_start)).all()
    fold_models = json.loads((TASK / "runs/M4_multi_efc_T_v1/fold_models.json").read_text())
    for held, entry in fold_models.items():
        train = entry["model"]["training_cells"]
        assert held not in train and len(train) == 5 and len(set(train)) == 5
        assert entry["replay_max_abs_pp"] < 1e-9
    for name, expected_train in (("M4_nested_age_v1", 4), ("M4_nested_inner_age_v1", 3)):
        folds = json.loads((TASK / "runs" / name / "folds.json").read_text())
        for fold in folds:
            assert len(fold["training_cells"]) == expected_train
            assert not set(fold["omitted_cells"]) & set(fold["training_cells"])
    evidence = pd.read_csv(TASK / "outputs/evidence_events.csv")
    assert evidence.event_id.str.contains("102Ah_").all()
    print("panel hash, no target label feature, strict input cutoff, fold/nested exclusion passed")


def math() -> None:
    times = pd.date_range("2025-01-01", periods=12, freq="10s")
    current = np.r_[np.full(11, 36.), 0.]
    q = np.arange(12)*.1
    voltage = 3.1+.4*q
    frame = pd.DataFrame({"absolute_time": times, "current_A": current,
                          "voltage_V": voltage, "temperature_C": 25.,
                          "cycle_number": 1})
    events = extract_charge_events(frame, time_col="absolute_time", voltage_cols=("voltage_V",),
                                   temp_col="temperature_C", segment_col="cycle_number", counter_col=None)
    assert len(events) == 1
    assert abs(events[0].ah-1.) <= 1e-6
    assert abs(partial_ah(events[0], 0, 3.2, 3.4)-.5) <= 1e-6
    first = effective_temperature((35., 4., 2.), 25., 1.)
    second = effective_temperature((35., 4., 2.), 25., 2.)
    assert np.isfinite([first, second]).all() and second > first >= 25.
    print("analytic Ah integration, local Ah voltage crossing, temperature surface units passed")


def official_interface() -> None:
    candidate = TASK / "candidates/multi_temp"
    for rel in ("run_model.py", "validate_submission.py", "framework/data.py",
                "framework/io.py", "framework/persistence.py"):
        assert (candidate / rel).read_bytes() == (ROOT / rel).read_bytes()
    report = (candidate / "validation_report.txt").read_text()
    assert "PASSED" in report
    output = pd.read_csv(TASK / "runs/M5_official_candidate/output.csv")
    assert len(output) == 8 and set(output.checkup) == {f"CK{i}" for i in range(8)}
    assert np.isfinite(output.SOH_est).all() and output.SOH_est.between(50., 110.).all()
    q0 = float(pd.read_csv(ROOT / "data/checkups/checkup_capacities_released.csv").capacity_Ah.iloc[0])
    assert abs(float(output.loc[output.checkup.eq("CK0"), "SOH_est"].iloc[0])-100.*q0/102.) < .00051
    diagnostics = pd.read_csv(TASK / "outputs/official_diagnostics.csv")
    assert len(diagnostics) == 8 and diagnostics.official_accuracy_verified.eq(False).all()
    assert diagnostics.loc[diagnostics.checkup.ne("CK0"), "mode"].eq("out_of_domain_shallow_charge_ratio").all()
    print("official files unchanged, sample validator passed, CK0 anchor and eight unlabeled outputs passed")


def synthetic_truth() -> None:
    config = json.loads((TASK / "configs/synthetic_mechanism.json").read_text())
    results = pd.read_csv(TASK / "runs/M6_mechanism_v1/results.csv")
    assert len(results) == len(config["scenarios"])*config["test_seed_count_per_scenario"]
    assert set(results.scenario) == set(config["scenarios"])
    assert results.groupby("scenario").seed.nunique().eq(config["test_seed_count_per_scenario"]).all()
    assert np.isfinite(results[["baseline_pack_C20_Ah", "target_pack_C20_Ah",
                                "estimate_soh_pp", "error_pp"]].to_numpy(float)).all()
    assert results.coarse_fine_capacity_difference_Ah.max() <= config["step_halving_capacity_difference_max_Ah"]
    assert results.cell_permutation_difference_Ah.max() <= config["cell_permutation_capacity_difference_max_Ah"]
    cases = pd.read_csv(TASK / "runs/M6_mechanism_v1/explicit_4S_truth_cases.csv")
    assert set(cases.case) == {"four_identical", "capacity_mismatch", "soc_mismatch"}
    assert cases.coarse_fine_difference_Ah.max() <= config["step_halving_capacity_difference_max_Ah"]
    assert cases.permutation_difference_Ah.max() <= config["cell_permutation_capacity_difference_max_Ah"]
    assert not np.allclose(cases.C20_group_capacity_Ah, cases.C20_group_capacity_Ah.iloc[0])
    print("140 independent-scenario seeds, three explicit 4S truths, step-halving and permutation passed")


GROUPS = {"causality": causality, "isolation": isolation, "math": math,
          "official_interface": official_interface, "synthetic_truth": synthetic_truth}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("group", choices=GROUPS)
    args = parser.parse_args()
    GROUPS[args.group]()
