"""Nested four-cell ageing priors for leakage-free outer-fold residual fitting.

For outer held i, each correction-training cell j gets a B_age prediction from
the model fitted on the four cells excluding both i and j.  Each unordered
pair is fitted once and used for its two complementary validation directions.
"""
from __future__ import annotations

import itertools
import json
import re
import sys
import time
from pathlib import Path

import pandas as pd

TASK = Path(__file__).resolve().parents[1]
SOURCE = Path("/Users/shane/Desktop/项目/Current State_Challenge1")
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(TASK / "scripts"))
from my_model.model_template import MyModel  # noqa: E402
from run_m3_age_prior import make_cell, visible_age_coordinates  # noqa: E402


def metadata(cell_id: str) -> tuple[float, float]:
    match = re.fullmatch(r"102Ah_(\d+)degC_(0p5C|1C)_cell\d+", cell_id)
    if not match:
        raise ValueError(cell_id)
    return float(match.group(1)), .5 if match.group(2) == "0p5C" else 1.


def main() -> None:
    panel = pd.read_csv(TASK / "outputs/panel_main.csv", parse_dates=["target_discharge_start"])
    cells = sorted(panel.cell_id.unique())
    run = TASK / "runs/M4_nested_age_v1"
    run.mkdir(parents=True, exist_ok=True)
    visible = {c: visible_age_coordinates(c, panel.loc[panel.cell_id.eq(c)]) for c in cells}
    rows = []
    folds = []
    for omitted in itertools.combinations(cells, 2):
        started = time.monotonic()
        train_ids = [c for c in cells if c not in omitted]
        training = [make_cell(c) for c in train_ids]
        model = MyModel(lam=1., shape_prior_strength=3., ea_prior_strength=.1,
                        extra_dT_anchors=None)
        model.fit(training)
        for target_cell in omitted:
            outer_cell = omitted[0] if target_cell == omitted[1] else omitted[1]
            targets = panel.loc[panel.cell_id.eq(target_cell)].sort_values("target_ordinal")
            temp, rate = metadata(target_cell)
            curve = model.predict_soh(temp, rate)
            anchor_cycle = int(targets.anchor_cycle.iloc[0])
            shift = float(targets.anchor_soh_pp.iloc[0])-float(curve[anchor_cycle-1])
            for target in targets.itertuples(index=False):
                age, input_end = visible[target_cell][int(target.target_cycle)]
                rows.append({"outer_held_cell": outer_cell,
                             "correction_training_cell": target_cell,
                             "target_ordinal": int(target.target_ordinal),
                             "target_cycle": int(target.target_cycle),
                             "input_end": input_end.isoformat(),
                             "nested_age_prediction_pp": float(curve[age-1]+shift),
                             "four_age_training_cells": "|".join(train_ids)})
        folds.append({"omitted_cells": omitted, "training_cells": train_ids,
                      "fit_seconds": time.monotonic()-started})
        pd.DataFrame(rows).to_csv(run / "predictions.partial.csv", index=False)
        (run / "folds.partial.json").write_text(json.dumps(folds, indent=2)+"\n")
        print("omitted", omitted, "fit_seconds", round(time.monotonic()-started, 2), flush=True)
        del training, model
    output = pd.DataFrame(rows)
    if len(output) != 900:
        raise AssertionError("six outer folds by five correction cells by 30 targets")
    output.to_csv(run / "predictions.csv", index=False)
    (run / "folds.json").write_text(json.dumps(folds, indent=2)+"\n")


if __name__ == "__main__":
    main()
