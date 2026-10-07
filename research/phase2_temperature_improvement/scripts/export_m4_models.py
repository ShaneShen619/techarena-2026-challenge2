"""Freeze exact fold models and a six-cell model for unlabeled deployment."""
from __future__ import annotations

import itertools
import json
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

TASK = Path(__file__).resolve().parents[1]
RUN = TASK / "runs/M4_multi_efc_T_v1"
sys.path.insert(0, str(TASK / "src"))
from multi_window_ridge import WIDTHS, RidgeFeatureModel, add_derived_features  # noqa: E402


def load_training_frame() -> pd.DataFrame:
    f = pd.read_csv(TASK / "runs/M4_feature_audit_v1/features.csv")
    throughput = pd.read_csv(TASK / "runs/M4_feature_audit_v1/throughput.csv")
    panel = pd.read_csv(TASK / "outputs/panel_main.csv")
    key = ["cell_id", "target_ordinal"]
    data = f.merge(throughput[key+["qualified_charge_efc"]], on=key, validate="one_to_one")
    data = data.merge(panel[key+["anchor_soh_pp", "target_soh_pp"]], on=key, validate="one_to_one")
    return add_derived_features(data, age_col="qualified_charge_efc")


def main() -> None:
    data = load_training_frame()
    selections = json.loads((RUN / "selections.json").read_text())
    recorded = pd.read_csv(RUN / "predictions.csv")
    folds = {}
    for choice in selections:
        held = choice["heldout_cell"]
        best = choice["selected"]
        train = data.loc[data.cell_id.ne(held)]
        test = data.loc[data.cell_id.eq(held)].sort_values("target_ordinal")
        model = RidgeFeatureModel.fit(train, best["width"], best["lambda"], with_temperature=True)
        expected = recorded.loc[recorded.cell_id.eq(held)].sort_values("target_ordinal").prediction_soh_pp.to_numpy(float)
        diff = float(np.max(np.abs(model.predict(test)-expected)))
        if diff > 1e-9:
            raise AssertionError(f"fold model not exact replay: {held}: {diff}")
        folds[held] = {"selected_inner": best, "model": asdict(model), "replay_max_abs_pp": diff}
    (RUN / "fold_models.json").write_text(json.dumps(folds, indent=2)+"\n")
    cells = sorted(data.cell_id.unique())
    options = []
    for width, lam in itertools.product(WIDTHS, (.1, 1., 10., 100.)):
        per = []
        for held in cells:
            train = data.loc[data.cell_id.ne(held)]
            test = data.loc[data.cell_id.eq(held)]
            model = RidgeFeatureModel.fit(train, width, lam, with_temperature=True)
            per.append(float(np.mean(np.abs(model.predict(test)-test.target_soh_pp.to_numpy(float)))))
        options.append({"width": width, "lambda": lam, "macro_mae_pp": float(np.mean(per)),
                        "per_cell_mae_pp": per})
    best = min(options, key=lambda item: (item["macro_mae_pp"], item["lambda"]))
    full = RidgeFeatureModel.fit(data, best["width"], best["lambda"], with_temperature=True)
    (RUN / "full_six_cell_model.json").write_text(json.dumps({
        "selection": best, "all_group_choices": options, "model": asdict(full),
        "scope": "P1 proxy training; official four-series pack precision not validated",
    }, indent=2)+"\n")
    print("fold_replay_max_abs_pp", max(x["replay_max_abs_pp"] for x in folds.values()),
          "full_six_cell_selection", best, flush=True)


if __name__ == "__main__":
    main()
