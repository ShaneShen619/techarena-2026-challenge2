"""Replay every frozen P1 target through the packaged online feature adapter."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

TASK = Path(__file__).resolve().parents[1]
RUN = TASK / "runs/M7_online_replay_v1"
sys.path.insert(0, str(TASK / "candidates/multi_temp/my_model"))
sys.path.insert(0, str(TASK / "scripts"))
from online_multi_window import OnlineMultiWindow  # noqa: E402
from multi_window_ridge import RidgeFeatureModel  # noqa: E402
from run_m2_repaired import load_charging  # noqa: E402


def main() -> None:
    RUN.mkdir(parents=True, exist_ok=True)
    panel = pd.read_csv(TASK / "outputs/panel_main.csv")
    frozen = json.loads((TASK / "runs/M4_multi_efc_T_v1/fold_models.json").read_text())
    windows = json.loads((TASK / "runs/M4_feature_audit_v1/config.json").read_text())["windows"]
    expected = pd.read_csv(TASK / "outputs/predictions.csv")
    expected = expected.loc[expected.method.eq("final")]
    rows = []
    for cell in sorted(panel.cell_id.unique()):
        started = time.monotonic()
        operation = load_charging(cell)
        targets = panel.loc[panel.cell_id.eq(cell)].sort_values("target_ordinal")
        model = OnlineMultiWindow(RidgeFeatureModel(**frozen[cell]["model"]), windows,
                                  float(targets.anchor_capacity_Ah.iloc[0]),
                                  targets.anchor_discharge_start.iloc[0])
        for target in targets.itertuples(index=False):
            cutoff = pd.Timestamp(target.target_discharge_start)
            visible = operation.loc[operation.absolute_time.lt(cutoff)]
            pred = model.estimate(visible, cutoff)
            exp = expected.loc[expected.cell_id.eq(cell) &
                               expected.target_ordinal.eq(int(target.target_ordinal))].prediction_soh_pp.iloc[0]
            diff = float(pred-exp) if pred is not None else float("nan")
            rows.append({"cell_id": cell, "target_ordinal": int(target.target_ordinal),
                         "target_cycle": int(target.target_cycle),
                         "online_prediction_soh_pp": pred,
                         "frozen_prediction_soh_pp": float(exp),
                         "difference_pp": diff,
                         "mode": model.last_diagnostics.get("mode")})
        pd.DataFrame(rows).to_csv(RUN / "predictions.partial.csv", index=False)
        print(cell, "seconds", round(time.monotonic()-started, 2),
              "max_abs_diff", float(pd.DataFrame(rows).loc[lambda x:x.cell_id.eq(cell)].difference_pp.abs().max()),
              flush=True)
    result = pd.DataFrame(rows)
    result.to_csv(RUN / "predictions.csv", index=False)
    if len(result) != 180 or not np.isfinite(result.difference_pp).all():
        raise AssertionError("online replay missing/nonfinite target")
    print("online_replay_max_abs_difference_pp", result.difference_pp.abs().max(), flush=True)


if __name__ == "__main__":
    main()
