"""Three-cell age priors for a genuinely nested inner group selection.

For outer i and inner validation j, correction-training k must get its base
prediction from a model excluding i, j and k.  This prevents the inner
validation cell's labels from influencing correction-training residuals.
"""
from __future__ import annotations

import itertools
import json
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
from run_m4_inner_age import metadata  # noqa: E402


def main() -> None:
    panel = pd.read_csv(TASK / "outputs/panel_main.csv", parse_dates=["target_discharge_start"])
    cells = sorted(panel.cell_id.unique())
    run = TASK / "runs/M4_nested_inner_age_v1"
    run.mkdir(parents=True, exist_ok=True)
    visible = {c: visible_age_coordinates(c, panel.loc[panel.cell_id.eq(c)]) for c in cells}
    rows = []
    folds = []
    for omitted in itertools.combinations(cells, 3):
        started = time.monotonic()
        train_ids = [c for c in cells if c not in omitted]
        model = MyModel(lam=1., shape_prior_strength=3., ea_prior_strength=.1,
                        extra_dT_anchors=None)
        training = [make_cell(c) for c in train_ids]
        model.fit(training)
        for correction_training_cell in omitted:
            targets = panel.loc[panel.cell_id.eq(correction_training_cell)].sort_values("target_ordinal")
            temp, rate = metadata(correction_training_cell)
            curve = model.predict_soh(temp, rate)
            anchor_cycle = int(targets.anchor_cycle.iloc[0])
            shift = float(targets.anchor_soh_pp.iloc[0])-float(curve[anchor_cycle-1])
            other_two = [c for c in omitted if c != correction_training_cell]
            for target in targets.itertuples(index=False):
                age, input_end = visible[correction_training_cell][int(target.target_cycle)]
                pred = float(curve[age-1]+shift)
                for outer, inner_validation in itertools.permutations(other_two, 2):
                    rows.append({"outer_held_cell": outer,
                                 "inner_validation_cell": inner_validation,
                                 "correction_training_cell": correction_training_cell,
                                 "target_ordinal": int(target.target_ordinal),
                                 "target_cycle": int(target.target_cycle),
                                 "input_end": input_end.isoformat(),
                                 "nested_inner_age_prediction_pp": pred,
                                 "three_age_training_cells": "|".join(train_ids)})
        folds.append({"omitted_cells": omitted, "training_cells": train_ids,
                      "fit_seconds": time.monotonic()-started})
        pd.DataFrame(rows).to_csv(run / "predictions.partial.csv", index=False)
        (run / "folds.partial.json").write_text(json.dumps(folds, indent=2)+"\n")
        print("omitted", omitted, "fit_seconds", round(time.monotonic()-started, 2), flush=True)
        del model, training
    output = pd.DataFrame(rows)
    if len(output) != 3600:
        raise AssertionError("six outer by five inner by four correction train by 30 targets")
    output.to_csv(run / "predictions.csv", index=False)
    (run / "folds.json").write_text(json.dumps(folds, indent=2)+"\n")


if __name__ == "__main__":
    main()
