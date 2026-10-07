"""Run the untouched prior Route A and CK0 constant on the frozen 180 points."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
OLD = ROOT / "research/phase2_validation/candidates/route_a"
ORDER_ONLY = TASK / "candidates/order_only"


def load_input(cell_id: str) -> pd.DataFrame:
    folder = ROOT / "dataset original" / cell_id
    cols = ["absolute_time", "cycle_number", "step_type", "voltage_V", "current_A", "temperature_C"]
    parts = []
    for path in sorted(folder.glob("*.csv")):
        part = pd.read_csv(path, usecols=cols, parse_dates=["absolute_time"])
        parts.append(part.loc[~part.step_type.eq("cc_discharge")])
    if not parts:
        raise FileNotFoundError(folder)
    data = pd.concat(parts, ignore_index=True)
    data = data.sort_values("absolute_time", kind="stable").reset_index(drop=True)
    # A copy in memory contains no step_capacity_Ah and no target discharges.
    data = data.drop(columns="step_type")
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cell", default="all", help="full cell ID, or all")
    parser.add_argument("--limit", type=int, default=0, help="0 means all 30 targets")
    parser.add_argument("--historical", action="store_true", help="replay prior 18 targets without replacing main panel")
    parser.add_argument("--order-only", action="store_true", help="run old model with only reference check moved before insertion")
    args = parser.parse_args()
    if args.historical and args.order_only:
        parser.error("historical and order-only cannot be combined")
    model_dir = ORDER_ONLY if args.order_only else OLD
    sys.path.insert(0, str(model_dir))
    from my_model.model_route_a import RouteA  # noqa: E402
    if args.historical:
        panel_file = ROOT / "research/phase2_validation/outputs/phase1_crossvalidation_predictions.csv"
        panel = pd.read_csv(panel_file, parse_dates=["target_discharge_start"])
        panel = panel.loc[panel.method.eq("A")].copy()
        panel = panel.sort_values(["cell_id", "target_discharge_start"])
        panel["target_ordinal"] = panel.groupby("cell_id").cumcount() + 1
        panel_hash = hashlib.sha256(panel_file.read_bytes()).hexdigest()
    else:
        panel_file = TASK / "outputs/panel_main.csv"
        panel = pd.read_csv(panel_file, parse_dates=["target_discharge_start"])
        manifest = json.loads((TASK / "outputs/panel_manifest.json").read_text())
        panel_hash = hashlib.sha256(panel_file.read_bytes()).hexdigest()
        if panel_hash != manifest["panel_sha256"]:
            raise RuntimeError("frozen panel changed")
    cells = sorted(panel.cell_id.unique()) if args.cell == "all" else [args.cell]
    if args.cell == "all" and args.limit == 0:
        run_id = "M0_history_replay_v1" if args.historical else ("M2_A_order_only_180_v1" if args.order_only else "M0_A_old_B0_180_v1")
    else:
        run_id = "M2_smoke_order_only" if args.order_only else "M0_smoke"
    run = TASK / "runs" / run_id
    run.mkdir(parents=True, exist_ok=True)
    code_hash = hashlib.sha256((model_dir / "my_model/model_route_a.py").read_bytes()).hexdigest()
    (run / "config.json").write_text(json.dumps({
        "run_id": run_id,
        "panel_sha256": panel_hash,
        "route_a_sha256": code_hash,
        "cell": args.cell,
        "limit": args.limit,
        "model_code_unmodified": True,
    }, indent=2) + "\n")
    all_rows = []
    for cell_id in cells:
        started = time.monotonic()
        targets = panel[panel.cell_id.eq(cell_id)].sort_values("target_ordinal")
        if args.limit:
            targets = targets.head(args.limit)
        input_data = load_input(cell_id)
        for row in targets.itertuples(index=False):
            cutoff = pd.Timestamp(row.target_discharge_start)
            visible = input_data.loc[input_data.absolute_time < cutoff]
            input_end = visible.absolute_time.max() if len(visible) else pd.NaT
            if len(visible) and not input_end < cutoff:
                raise AssertionError("future input")
            dataset = SimpleNamespace(operation=visible, bol_capacity_Ah=float(row.anchor_capacity_Ah))
            for method in (("A_order_only",) if args.order_only else ("B0", "A_old")):
                t0 = time.monotonic()
                if method == "B0":
                    pred = 100 * float(row.anchor_capacity_Ah) / 102.0
                    diagnostics = {"fallback": True, "updates": 0}
                else:
                    model = RouteA(single_cell=True)
                    model.fit(dataset)
                    pred = model.estimate_soh(dataset, cutoff)
                    diagnostics = model.last_diagnostics
                all_rows.append({
                    "run_id": run_id,
                    "method": method,
                    "cell_id": cell_id,
                    "target_ordinal": int(row.target_ordinal),
                    "target_cycle": int(row.target_cycle),
                    "target_discharge_start": cutoff.isoformat(),
                    "input_end": input_end.isoformat() if pd.notna(input_end) else "",
                    "prediction_soh_pp": float(pred),
                    "prediction_Ah": float(pred * 102 / 100),
                    "fallback": bool(diagnostics.get("fallback", False)),
                    "updates": int(diagnostics.get("updates", 0)),
                    "runtime_s": time.monotonic() - t0,
                    "evidence": "E3-P1 developmental holdout; target labels stored only in panel_main.csv",
                })
        pd.DataFrame(all_rows).to_csv(run / "predictions.partial.csv", index=False)
        print(cell_id, "targets", len(targets), "seconds", round(time.monotonic()-started, 2), flush=True)
        del input_data
    predictions = pd.DataFrame(all_rows)
    predictions.to_csv(run / "predictions.csv", index=False)
    if args.cell == "all" and args.limit == 0 and not args.historical:
        if args.order_only:
            if len(predictions) != 180:
                raise AssertionError("expected 180 order-only predictions")
            existing = pd.read_csv(TASK / "outputs/predictions.csv")
            existing = existing.loc[~existing.method.eq("A_order_only")]
            pd.concat([existing, predictions], ignore_index=True).to_csv(TASK / "outputs/predictions.csv", index=False)
        else:
            if len(predictions) != 360:
                raise AssertionError("expected 180 B0 + 180 A_old")
            predictions.to_csv(TASK / "outputs/predictions.csv", index=False)
    joined = predictions.merge(panel[["cell_id", "target_cycle", "target_soh_pp"]],
                               on=["cell_id", "target_cycle"], validate="many_to_one")
    joined["abs_error_pp"] = (joined.prediction_soh_pp - joined.target_soh_pp).abs()
    print(joined.groupby("method").abs_error_pp.mean().to_string(), flush=True)
    if args.historical and args.cell == "all" and args.limit == 0:
        compare = predictions.loc[predictions.method.eq("A_old")].merge(
            panel[["cell_id", "target_cycle", "prediction_soh_pp", "target_soh_pp"]],
            on=["cell_id", "target_cycle"], validate="one_to_one", suffixes=("_replayed", "_recorded"))
        compare["delta_prediction_pp"] = compare.prediction_soh_pp_replayed - compare.prediction_soh_pp_recorded
        compare.to_csv(run / "historical_comparison.csv", index=False)
        maximum = compare.delta_prediction_pp.abs().max()
        print("historical_max_prediction_delta_pp", maximum, flush=True)
        if maximum > 1e-9:
            raise AssertionError("historical old A not exactly reproduced")


if __name__ == "__main__":
    main()
