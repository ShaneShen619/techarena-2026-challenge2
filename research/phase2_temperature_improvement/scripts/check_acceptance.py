"""Independent acceptance computation from frozen targets and raw predictions.

Candidates must not write their own success flag. Missing data never passes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


TASK = Path(__file__).resolve().parents[1]


def load_csv(path: Path) -> pd.DataFrame | None:
    if not path.is_file() or path.stat().st_size == 0:
        return None
    try:
        return pd.read_csv(path)
    except (pd.errors.EmptyDataError, OSError, ValueError):
        return None


def check_panel(panel: pd.DataFrame | None, config: dict, reasons: list[str]) -> pd.DataFrame | None:
    if panel is None:
        reasons.append("missing_or_unreadable_frozen_panel")
        return None
    needed = {"cell_id", "target_cycle", "target_ordinal", "target_soh_pp", "target_discharge_start", "anchor_discharge_start"}
    if not needed.issubset(panel.columns):
        reasons.append("panel_missing_columns:" + ",".join(sorted(needed - set(panel.columns))))
        return None
    if len(panel) != config["expected_targets"] or panel.cell_id.nunique() != config["expected_cells"]:
        reasons.append("panel_incomplete")
    if panel.duplicated(["cell_id", "target_cycle"]).any():
        reasons.append("panel_duplicate_targets")
    counts = panel.groupby("cell_id").size()
    if not (counts == config["targets_per_cell"]).all():
        reasons.append("panel_unequal_targets")
    if not np.isfinite(pd.to_numeric(panel.target_soh_pp, errors="coerce")).all():
        reasons.append("panel_nonfinite_labels")
    manifest_path = TASK / "outputs/panel_manifest.json"
    if not manifest_path.is_file():
        reasons.append("missing_panel_manifest")
    else:
        manifest = json.loads(manifest_path.read_text())
        actual = hashlib.sha256((TASK / "outputs/panel_main.csv").read_bytes()).hexdigest()
        if manifest.get("panel_sha256") != actual:
            reasons.append("panel_hash_mismatch")
    return panel


def scored_predictions(panel: pd.DataFrame, predictions: pd.DataFrame | None,
                       reasons: list[str]) -> tuple[pd.DataFrame | None, dict]:
    if predictions is None:
        reasons.append("missing_or_unreadable_predictions")
        return None, {}
    needed = {"method", "cell_id", "target_cycle", "prediction_soh_pp", "input_end"}
    if not needed.issubset(predictions.columns):
        reasons.append("predictions_missing_columns:" + ",".join(sorted(needed - set(predictions.columns))))
        return None, {}
    if any(x in predictions.columns for x in ("target_soh_pp", "target_capacity_Ah")):
        reasons.append("prediction_file_contains_target_labels")
    keys = ["cell_id", "target_cycle"]
    if predictions.duplicated(["method", *keys]).any():
        reasons.append("duplicate_predictions")
    predictions = predictions.copy()
    predictions["prediction_soh_pp"] = pd.to_numeric(predictions.prediction_soh_pp, errors="coerce")
    if not np.isfinite(predictions.prediction_soh_pp).all():
        reasons.append("nonfinite_predictions")
        return None, {}
    if "target_discharge_start" in predictions:
        predictions = predictions.rename(columns={"target_discharge_start": "claimed_target_discharge_start"})
    score = predictions.merge(
        panel[[*keys, "target_soh_pp", "target_discharge_start"]],
        on=keys, how="left", validate="many_to_one", indicator=True,
    )
    if (score._merge != "both").any():
        reasons.append("prediction_target_not_in_panel")
    if "claimed_target_discharge_start" in score:
        claimed = pd.to_datetime(score.claimed_target_discharge_start, errors="coerce")
        canonical = pd.to_datetime(score.target_discharge_start, errors="coerce")
        if not (claimed == canonical).all():
            reasons.append("prediction_target_date_disagrees_with_panel")
    end = pd.to_datetime(score.input_end, errors="coerce")
    cutoff = pd.to_datetime(score.target_discharge_start, errors="coerce")
    if ((end >= cutoff) & end.notna()).any():
        reasons.append("input_not_before_target_discharge")
    score["error_pp"] = score.prediction_soh_pp - score.target_soh_pp
    score["abs_error_pp"] = score.error_pp.abs()
    metrics = {}
    for method, group in score.groupby("method", sort=True):
        if len(group) != len(panel) or set(map(tuple, group[keys].to_numpy())) != set(map(tuple, panel[keys].to_numpy())):
            reasons.append(f"incomplete_or_extra_method:{method}")
            continue
        per = group.groupby("cell_id").agg(
            mae_pp=("abs_error_pp", "mean"),
            rmse_pp=("error_pp", lambda x: float(np.sqrt(np.mean(np.square(x))))),
        )
        metrics[method] = {
            "n": len(group),
            "macro_mae_pp": float(per.mae_pp.mean()),
            "macro_rmse_pp": float(per.rmse_pp.mean()),
            "pooled_rmse_pp": float(np.sqrt(np.mean(np.square(group.error_pp)))),
            "p95_abs_error_pp": float(np.quantile(group.abs_error_pp, .95)),
            "max_abs_error_pp": float(group.abs_error_pp.max()),
            "per_cell_mae_pp": {str(k): float(v) for k, v in per.mae_pp.items()},
            "per_cell_rmse_pp": {str(k): float(v) for k, v in per.rmse_pp.items()},
        }
    if metrics:
        rows = []
        for method, value in metrics.items():
            for cell_id in value["per_cell_mae_pp"]:
                rows.append({"method": method, "cell_id": cell_id,
                             "mae_pp": value["per_cell_mae_pp"][cell_id],
                             "rmse_pp": value["per_cell_rmse_pp"][cell_id]})
        pd.DataFrame(rows).to_csv(TASK / "outputs/per_cell_metrics.csv", index=False)
    return score, metrics


def evidence_coverage(panel: pd.DataFrame, method: str, evidence_path: Path,
                      reasons: list[str], scenario: str | None = None) -> dict | None:
    evidence = load_csv(evidence_path)
    if evidence is None:
        reasons.append(f"missing_evidence:{evidence_path.name}")
        return None
    needed = {"method", "cell_id", "target_cycle", "event_id", "event_end", "quality_pass", "used_for_update", "reference_only"}
    if scenario is not None:
        needed.add("scenario")
    if not needed.issubset(evidence.columns):
        reasons.append(f"evidence_missing_columns:{evidence_path.name}")
        return None
    evidence = evidence.loc[evidence.method.eq(method)].copy()
    if scenario is not None:
        evidence = evidence.loc[evidence.scenario.eq(scenario)].copy()
    for key in ("quality_pass", "used_for_update", "reference_only"):
        evidence[key] = evidence[key].astype(str).str.lower().eq("true")
    evidence["parsed_event_end"] = pd.to_datetime(evidence.event_end, errors="coerce")
    by_target = {key: frame for key, frame in evidence.groupby(["cell_id", "target_cycle"], sort=False)}
    panel = panel.sort_values(["cell_id", "target_discharge_start"]).copy()
    panel["previous_cutoff"] = panel.groupby("cell_id").target_discharge_start.shift(1).fillna(panel.anchor_discharge_start)
    seen = set()
    cell_counts = {}
    for row in panel.itertuples(index=False):
        sel = by_target.get((row.cell_id, row.target_cycle))
        left = pd.Timestamp(row.previous_cutoff)
        right = pd.Timestamp(row.target_discharge_start)
        valid = False
        for event in sel.itertuples(index=False) if sel is not None else ():
            event_end = event.parsed_event_end
            identifier = str(event.event_id)
            if pd.isna(event_end) or not identifier:
                continue
            if not (left <= event_end < right):
                continue
            if not event.quality_pass or not event.used_for_update or event.reference_only:
                continue
            key = (row.cell_id, identifier)
            if key in seen:
                continue
            seen.add(key)
            valid = True
        n, good = cell_counts.get(row.cell_id, (0, 0))
        cell_counts[row.cell_id] = (n + 1, good + int(valid))
    per_cell = {cell: good / n for cell, (n, good) in cell_counts.items()}
    return {
        "fraction": sum(good for n, good in cell_counts.values()) / len(panel),
        "per_cell_fraction": per_cell,
        "qualified_distinct_event_ids": len(seen),
    }


def test_receipts(config: dict, reasons: list[str]) -> bool:
    path = TASK / "outputs/hard_tests.json"
    if not path.is_file():
        reasons.append("missing_hard_tests_receipts")
        return False
    obj = json.loads(path.read_text())
    groups = obj.get("groups", {})
    ok = True
    for name in config["required_hard_test_groups"]:
        receipt = groups.get(name, {})
        log = TASK / receipt.get("log", "") if receipt.get("log") else None
        if receipt.get("exit_code") != 0 or not log or not log.is_file() or log.stat().st_size == 0:
            reasons.append(f"hard_test_unverified:{name}")
            ok = False
    return ok


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()
    config = json.loads((TASK / "configs/acceptance.json").read_text())
    reasons: list[str] = []
    gates: dict[str, dict] = {}
    panel = check_panel(load_csv(TASK / "outputs/panel_main.csv"), config, reasons)
    if panel is None:
        return write_result(config, {}, {}, reasons, args.require_pass)
    _, metrics = scored_predictions(panel, load_csv(TASK / "outputs/predictions.csv"), reasons)
    final = metrics.get("final")
    old = metrics.get("A_old")
    baselines = config["fixed_baseline_methods"]
    if not all(x in metrics for x in baselines):
        reasons.append("fixed_baselines_incomplete")
    if final is None:
        reasons.append("final_candidate_missing")
    if old is None:
        reasons.append("old_a_same_panel_missing")
    coverage = evidence_coverage(panel, "final", TASK / "outputs/evidence_events.csv", reasons)
    def gate(name: str, actual, comparator: str, threshold, passed: bool, evidence: str):
        gates[name] = {"actual": actual, "operator": comparator, "threshold": threshold,
                       "passed": bool(passed), "evidence": evidence}
    if final:
        p = "outputs/predictions.csv; outputs/panel_main.csv"
        for key, field, threshold in [
            ("macro_mae", "macro_mae_pp", config["macro_mae_max"]),
            ("macro_rmse", "macro_rmse_pp", config["macro_rmse_max"]),
            ("per_cell_mae", None, config["per_cell_mae_max"]),
            ("p95_abs_error", "p95_abs_error_pp", config["p95_abs_error_max"]),
            ("max_abs_error", "max_abs_error_pp", config["max_abs_error_max"]),
        ]:
            actual = max(final["per_cell_mae_pp"].values()) if field is None else final[field]
            gate(key, actual, "<=", threshold, actual <= threshold, p)
        if old:
            decline = (old["macro_mae_pp"]-final["macro_mae_pp"])/old["macro_mae_pp"]
            gate("old_a_mae_reduction", decline, ">=", config["old_a_reduction_min_fraction"],
                 decline >= config["old_a_reduction_min_fraction"], p)
            count = sum(final["per_cell_mae_pp"][k] <= old["per_cell_mae_pp"][k]
                        for k in final["per_cell_mae_pp"])
            gate("old_a_per_cell_noninferiority", count, ">=", config["old_a_noninferior_cells_min"],
                 count >= config["old_a_noninferior_cells_min"], p)
        if all(x in metrics for x in baselines):
            best = min(metrics[x]["macro_mae_pp"] for x in baselines)
            gate("strongest_fixed_baseline", final["macro_mae_pp"], "<=", best,
                 final["macro_mae_pp"] <= best, p)
    if coverage:
        gate("coverage", coverage["fraction"], ">=", config["coverage_min_fraction"],
             coverage["fraction"] >= config["coverage_min_fraction"], "outputs/evidence_events.csv")
        worst = min(coverage["per_cell_fraction"].values())
        gate("per_cell_coverage", worst, ">=", config["per_cell_coverage_min_fraction"],
             worst >= config["per_cell_coverage_min_fraction"], "outputs/evidence_events.csv")
    stress = load_csv(TASK / "outputs/temperature_stress.csv")
    if stress is None or not {"scenario", "cell_id", "target_cycle", "prediction_soh_pp"}.issubset(stress.columns):
        reasons.append("temperature_stress_incomplete")
    elif final:
        for offset in config["temp_bias_offsets_C"]:
            scenario = f"bias_{offset:+g}C"
            rows = stress.loc[stress.scenario.eq(scenario)]
            if len(rows) != len(panel) or rows.duplicated(["cell_id", "target_cycle"]).any():
                reasons.append(f"temperature_stress_incomplete:{scenario}")
                continue
            joined = rows.merge(panel[["cell_id", "target_cycle", "target_soh_pp"]],
                                on=["cell_id", "target_cycle"], validate="one_to_one")
            if len(joined) != len(panel) or not np.isfinite(joined.prediction_soh_pp).all():
                reasons.append(f"temperature_stress_nonfinite_or_wrong_panel:{scenario}")
                continue
            temp_mae = joined.assign(err=(joined.prediction_soh_pp-joined.target_soh_pp).abs()).groupby("cell_id").err.mean().mean()
            delta = float(temp_mae-final["macro_mae_pp"])
            gate(f"temperature_mae_{scenario}", delta, "<=", config["temp_bias_mae_increase_max_pp"],
                 delta <= config["temp_bias_mae_increase_max_pp"], "outputs/temperature_stress.csv")
            sub_coverage = evidence_coverage(panel, "final", TASK / "outputs/temperature_stress_evidence.csv", reasons, scenario)
            if sub_coverage and coverage:
                drop = coverage["fraction"]-sub_coverage["fraction"]
                gate(f"temperature_coverage_{scenario}", drop, "<=", config["temp_bias_coverage_drop_max_fraction"],
                     drop <= config["temp_bias_coverage_drop_max_fraction"], "outputs/temperature_stress_evidence.csv")
    tests_ok = test_receipts(config, reasons)
    gate("hard_tests", tests_ok, "==", True, tests_ok, "outputs/hard_tests.json")
    missing_artifacts = [p for p in config["required_artifacts"]
                         if not (TASK / p).is_file() or (TASK / p).stat().st_size == 0]
    if missing_artifacts:
        reasons.append("required_artifacts_missing:" + ",".join(missing_artifacts))
    qa = TASK / "outputs/report_render/qa.json"
    if not qa.is_file() or not json.loads(qa.read_text()).get("passed", False):
        reasons.append("word_visual_qa_missing_or_failed")
    review = TASK / "outputs/independent_review.json"
    if not review.is_file() or json.loads(review.read_text()).get("severe_unresolved") != 0:
        reasons.append("independent_review_missing_or_severe")
    if not all(name in gates and gate["passed"] for name, gate in gates.items()):
        reasons.append("one_or_more_present_gates_failed")
    expected_gates = {"macro_mae", "macro_rmse", "per_cell_mae", "p95_abs_error", "max_abs_error",
                      "old_a_mae_reduction", "old_a_per_cell_noninferiority", "strongest_fixed_baseline",
                      "coverage", "per_cell_coverage", "hard_tests"}
    for offset in config["temp_bias_offsets_C"]:
        expected_gates |= {f"temperature_mae_bias_{offset:+g}C", f"temperature_coverage_bias_{offset:+g}C"}
    if not expected_gates.issubset(gates):
        reasons.append("gates_not_yet_evaluable:" + ",".join(sorted(expected_gates - set(gates))))
    return write_result(config, metrics, gates, reasons, args.require_pass)


def write_result(config: dict, metrics: dict, gates: dict, reasons: list[str], require_pass: bool) -> int:
    result = {"protocol_version": config["version"], "goal_achieved": not reasons and all(v["passed"] for v in gates.values()),
              "metrics": metrics, "gates": gates, "unmet_or_unverified": list(dict.fromkeys(reasons))}
    out = TASK / "outputs/acceptance.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"goal_achieved": result["goal_achieved"], "metrics": metrics,
                      "unmet_or_unverified": result["unmet_or_unverified"]}, ensure_ascii=False))
    return 0 if result["goal_achieved"] or not require_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
