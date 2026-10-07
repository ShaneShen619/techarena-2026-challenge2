"""Fit the first-phase time-scale law afresh within each held-out-cell fold.

This is the preregistered low-dimensional B_age baseline. Full target-cell
labels and temperatures never enter model.fit; a target's initial released
capacity provides only an additive BOL calibration. The age coordinate is the
largest charge-cycle identifier already visible before that target discharge.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
SOURCE = Path("/Users/shane/Desktop/项目/Current State_Challenge1")
sys.path.insert(0, str(SOURCE))
from framework.data import Cell  # noqa: E402
from my_model.model_template import MyModel  # noqa: E402


def make_cell(cell_id: str) -> Cell:
    match = re.fullmatch(r"102Ah_(\d+)degC_(0p5C|1C)_cell\d+", cell_id)
    if not match:
        raise ValueError(cell_id)
    return Cell(cell_id, str(ROOT / "dataset original" / cell_id),
                int(match.group(1)), .5 if match.group(2) == "0p5C" else 1.)


def visible_age_coordinates(cell_id: str, targets: pd.DataFrame) -> dict[int, tuple[int, pd.Timestamp]]:
    """Compute a prefix maximum from charge rows, never from target labels."""
    chunks = []
    usecols = ["absolute_time", "cycle_number", "step_type", "current_A"]
    for path in sorted((ROOT / "dataset original" / cell_id).glob("*.csv")):
        for chunk in pd.read_csv(path, usecols=usecols, chunksize=200_000):
            charging = chunk.loc[chunk.step_type.ne("cc_discharge") & chunk.current_A.ge(5.),
                                 ["absolute_time", "cycle_number"]]
            chunks.append(charging)
    if not chunks:
        raise ValueError(f"no visible charging rows: {cell_id}")
    frame = pd.concat(chunks, ignore_index=True)
    frame["absolute_time"] = pd.to_datetime(frame.absolute_time, errors="raise")
    frame = frame.sort_values("absolute_time", kind="stable")
    timestamps = frame.absolute_time.to_numpy(dtype="datetime64[ns]")
    age = np.maximum.accumulate(frame.cycle_number.to_numpy(int))
    output = {}
    for row in targets.itertuples(index=False):
        position = int(np.searchsorted(timestamps, np.datetime64(row.target_discharge_start), side="left")-1)
        if position < 0:
            raise AssertionError(f"no charge before target: {cell_id}, {row.target_cycle}")
        output[int(row.target_cycle)] = (int(age[position]), pd.Timestamp(timestamps[position]))
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fold", default="all", help="held-out full cell ID or all")
    args = parser.parse_args()
    panel_path = TASK / "outputs/panel_main.csv"
    manifest = json.loads((TASK / "outputs/panel_manifest.json").read_text())
    if hashlib.sha256(panel_path.read_bytes()).hexdigest() != manifest["panel_sha256"]:
        raise RuntimeError("frozen panel changed")
    panel = pd.read_csv(panel_path, parse_dates=["target_discharge_start", "anchor_discharge_start"])
    all_cells = sorted(panel.cell_id.unique())
    heldouts = all_cells if args.fold == "all" else [args.fold]
    run_id = "M3_B_age_sixfold_v1" if args.fold == "all" else "M3_B_age_fold_smoke"
    run = TASK / "runs" / run_id
    run.mkdir(parents=True, exist_ok=True)
    source_hash = hashlib.sha256((SOURCE / "my_model/model_template.py").read_bytes()).hexdigest()
    pretrain_hash = hashlib.sha256((SOURCE / "my_model/pretrained.json").read_bytes()).hexdigest()
    (run / "config.json").write_text(json.dumps({
        "run_id": run_id, "source_model_sha256": source_hash, "public_pretrained_sha256": pretrain_hash,
        "panel_sha256": manifest["panel_sha256"], "fit_only_five_cells_per_fold": True,
        "hyperparameters": {"lam": 1., "shape_prior_strength": 3., "ea_prior_strength": .1},
        "target_bol_calibration": "add released anchor SOH minus source model SOH at anchor cycle",
        "age_feature": "maximum observed positive-charge cycle number before target discharge",
    }, indent=2) + "\n")
    predictions = []
    folds = []
    for held in heldouts:
        start = time.monotonic()
        train_ids = [x for x in all_cells if x != held]
        training = [make_cell(x) for x in train_ids]
        if any(cell.cell_id == held for cell in training):
            raise AssertionError("held-out cell in training")
        model = MyModel(lam=1., shape_prior_strength=3., ea_prior_strength=.1,
                        extra_dT_anchors=None)
        model.fit(training)
        held_metadata = re.fullmatch(r"102Ah_(\d+)degC_(0p5C|1C)_cell\d+", held)
        if held_metadata is None:
            raise ValueError(held)
        held_nominal = float(held_metadata.group(1))
        held_rate = .5 if held_metadata.group(2) == "0p5C" else 1.
        targets = panel.loc[panel.cell_id.eq(held)].sort_values("target_ordinal")
        visible_cycles = visible_age_coordinates(held, targets)
        curve = model.predict_soh(held_nominal, held_rate)
        anchor_cycle = int(targets.anchor_cycle.iloc[0])
        anchor_soh = float(targets.anchor_soh_pp.iloc[0])
        if not 1 <= anchor_cycle <= len(curve):
            raise ValueError("anchor cycle outside source curve")
        shift = anchor_soh-float(curve[anchor_cycle-1])
        for row in targets.itertuples(index=False):
            observed_cycle, input_end = visible_cycles[int(row.target_cycle)]
            if not 1 <= observed_cycle <= len(curve):
                raise ValueError("visible operation age outside model curve")
            predictions.append({
                "run_id": run_id, "method": "B_age", "cell_id": held,
                "target_ordinal": int(row.target_ordinal), "target_cycle": int(row.target_cycle),
                "target_discharge_start": row.target_discharge_start.isoformat(),
                "input_end": input_end.isoformat(),
                "visible_last_charge_cycle": observed_cycle,
                "prediction_soh_pp": float(curve[observed_cycle-1]+shift),
                "prediction_Ah": float((curve[observed_cycle-1]+shift)*102/100),
                "anchor_shift_pp": shift,
                "training_cells": "|".join(train_ids),
                "evidence": "E3-P1 supervised training only on five other physical cells",
            })
        folds.append({"heldout_cell": held, "training_cells": train_ids,
                      "n_training_cells": model.n_cells_, "temperature_theta_train_only": model.dT_theta_.tolist()
                      if model.dT_theta_ is not None else None,
                      "shape_train_only": model.shape_.tolist(),
                      "anchor_shift_pp": shift,
                      "fit_seconds": time.monotonic()-start})
        pd.DataFrame(predictions).to_csv(run / "predictions.partial.csv", index=False)
        (run / "folds.partial.json").write_text(json.dumps(folds, indent=2) + "\n")
        print(held, "fit_seconds", round(time.monotonic()-start, 2),
              "anchor_shift_pp", round(shift, 3), flush=True)
        del training, model
    output = pd.DataFrame(predictions)
    output.to_csv(run / "predictions.csv", index=False)
    (run / "folds.json").write_text(json.dumps(folds, indent=2) + "\n")
    if args.fold == "all":
        if len(output) != 180:
            raise AssertionError("B_age needs all 180 targets")
        existing = pd.read_csv(TASK / "outputs/predictions.csv")
        existing = existing.loc[~existing.method.eq("B_age")]
        pd.concat([existing, output], ignore_index=True).to_csv(TASK / "outputs/predictions.csv", index=False)
    joined = output.merge(panel[["cell_id", "target_cycle", "target_soh_pp"]],
                          on=["cell_id", "target_cycle"], validate="one_to_one")
    per = joined.assign(ae=(joined.prediction_soh_pp-joined.target_soh_pp).abs()).groupby("cell_id").ae.mean()
    print("B_age_macro_mae_pp", per.mean(), "worst", per.max(), flush=True)


if __name__ == "__main__":
    main()
