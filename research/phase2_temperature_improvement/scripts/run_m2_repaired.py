"""Evaluate the reference/CC/temperature repair on the frozen P1 targets."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK / "src"))
from route_a_repaired import RouteARepaired  # noqa: E402


VARIANTS = {
    "A_bugfix": {},
    "A_no_true_pair": {"true_pair_temperature": False},
    "A_no_cc_trim": {"cc_only": False},
    "A_no_quality_ref": {"require_quality_for_reference": False},
    "A_no_carry": {"carry_forward": False},
    "A_disagreement_gate": {"disagreement_gate": True},
}


def load_charging(cell_id: str) -> pd.DataFrame:
    folder = ROOT / "dataset original" / cell_id
    cols = ["absolute_time", "cycle_number", "step_type", "voltage_V", "current_A", "temperature_C"]
    pieces = []
    for path in sorted(folder.glob("*.csv")):
        chunk = pd.read_csv(path, usecols=cols, parse_dates=["absolute_time"])
        pieces.append(chunk.loc[~chunk.step_type.eq("cc_discharge")].drop(columns="step_type"))
    frame = pd.concat(pieces, ignore_index=True)
    return frame.sort_values("absolute_time", kind="stable").reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", choices=VARIANTS, default="A_bugfix")
    parser.add_argument("--cell", default="all")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    manifest = json.loads((TASK / "outputs/panel_manifest.json").read_text())
    panel_path = TASK / "outputs/panel_main.csv"
    if hashlib.sha256(panel_path.read_bytes()).hexdigest() != manifest["panel_sha256"]:
        raise RuntimeError("frozen target panel changed")
    panel = pd.read_csv(panel_path, parse_dates=["target_discharge_start", "anchor_discharge_start"])
    cells = sorted(panel.cell_id.unique()) if args.cell == "all" else [args.cell]
    complete = args.cell == "all" and args.limit == 0
    run_id = f"M2_{args.method}_180_v1" if complete else f"M2_smoke_{args.method}"
    run = TASK / "runs" / run_id
    run.mkdir(parents=True, exist_ok=True)
    code_hash = hashlib.sha256((TASK / "src/route_a_repaired.py").read_bytes()).hexdigest()
    (run / "config.json").write_text(json.dumps({
        "run_id": run_id, "method": args.method, "variant": VARIANTS[args.method],
        "panel_sha256": manifest["panel_sha256"], "code_sha256": code_hash,
        "cell": args.cell, "limit": args.limit, "training_cells_used": "none in M2 bug-fix baseline",
    }, indent=2) + "\n")
    results = []
    event_logs = []
    for cell_id in cells:
        started = time.monotonic()
        data = load_charging(cell_id)
        targets = panel.loc[panel.cell_id.eq(cell_id)].sort_values("target_ordinal")
        if args.limit:
            targets = targets.head(args.limit)
        previous = pd.Timestamp(targets.anchor_discharge_start.iloc[0])
        for row in targets.itertuples(index=False):
            cutoff = pd.Timestamp(row.target_discharge_start)
            visible = data.loc[data.absolute_time < cutoff]
            if len(visible) and not visible.absolute_time.max() < cutoff:
                raise AssertionError("model input includes target discharge")
            ds = SimpleNamespace(operation=visible, bol_capacity_Ah=float(row.anchor_capacity_Ah),
                                 anchor_discharge_start=pd.Timestamp(row.anchor_discharge_start))
            model = RouteARepaired(**VARIANTS[args.method])
            model.fit(ds)
            t0 = time.monotonic()
            estimate = model.estimate_soh(ds, cutoff)
            diag = model.last_diagnostics
            if not np.isfinite(estimate):
                raise AssertionError("nonfinite estimate")
            used_ids = set(diag["last_used_event_ids"])
            for event in model.evidence_events:
                end = pd.Timestamp(event["event_end"])
                if previous <= end < cutoff:
                    event_logs.append({"run_id": run_id, "method": args.method,
                                       "cell_id": cell_id, "target_cycle": int(row.target_cycle),
                                       "event_id": cell_id+"|"+event["event_id"],
                                       "event_end": end.isoformat(),
                                       "quality_pass": bool(event["quality_pass"]),
                                       "reference_only": bool(event["reference_only"]),
                                       "used_for_update": bool(event["used_for_update"] and event["event_id"] in used_ids),
                                       "reason": event["reason"],
                                       "matched_windows": int(event["matched_windows"])})
            results.append({
                "run_id": run_id, "method": args.method, "cell_id": cell_id,
                "target_ordinal": int(row.target_ordinal), "target_cycle": int(row.target_cycle),
                "target_discharge_start": cutoff.isoformat(),
                "input_end": visible.absolute_time.max().isoformat() if len(visible) else "",
                "prediction_soh_pp": float(estimate), "prediction_Ah": float(estimate*102/100),
                "fallback": bool(diag["fallback"]), "carried_forward": bool(diag["carried_forward"]),
                "updates_total": int(diag["updates"]), "updates_recent": int(diag["recent_updates"]),
                "reference_count": int(diag["reference_keys"]),
                "rejections_json": json.dumps(diag["rejections"], sort_keys=True),
                "runtime_s": time.monotonic()-t0,
                "evidence": "E3-P1 developmental holdout; target labels stored only in frozen panel",
            })
            previous = cutoff
        pd.DataFrame(results).to_csv(run / "predictions.partial.csv", index=False)
        pd.DataFrame(event_logs).to_csv(run / "evidence_events.partial.csv", index=False)
        print(cell_id, "targets", len(targets), "seconds", round(time.monotonic()-started, 2), flush=True)
        del data
    output = pd.DataFrame(results)
    output.to_csv(run / "predictions.csv", index=False)
    pd.DataFrame(event_logs).to_csv(run / "evidence_events.csv", index=False)
    if complete:
        if len(output) != 180:
            raise AssertionError("expected 180 predictions")
        existing = pd.read_csv(TASK / "outputs/predictions.csv")
        existing = existing.loc[~existing.method.eq(args.method)]
        pd.concat([existing, output], ignore_index=True).to_csv(TASK / "outputs/predictions.csv", index=False)
    joined = output.merge(panel[["cell_id", "target_cycle", "target_soh_pp"]],
                          on=["cell_id", "target_cycle"], validate="one_to_one")
    error = joined.prediction_soh_pp-joined.target_soh_pp
    by = joined.assign(abs_error=error.abs()).groupby("cell_id").abs_error.mean()
    print("macro_mae_pp", by.mean(), "worst_cell_mae_pp", by.max(),
          "fallback_fraction", output.fallback.mean(),
          "carried_forward_fraction", output.carried_forward.mean(), flush=True)


if __name__ == "__main__":
    main()
