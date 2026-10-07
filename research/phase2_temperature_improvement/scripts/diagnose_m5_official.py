"""Unlabeled CK0–CK7 diagnostics for the exact packaged candidate."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(TASK / "candidates/multi_temp"))
from framework.data import load_dataset  # noqa: E402
from my_model import ActiveModel  # noqa: E402


def main() -> None:
    evals = pd.read_csv(ROOT / "data/checkups/evaluation_points.csv", parse_dates=["date"])
    model = ActiveModel()
    model.fit(load_dataset(ROOT / "data"))
    output = pd.read_csv(TASK / "runs/M5_official_candidate/output.csv")
    rows = []
    events = []
    for ck in evals.itertuples(index=False):
        dataset = load_dataset(ROOT / "data", until=ck.date)
        estimate = float(model.estimate_soh(dataset, ck.date))
        diag = dict(model.last_diagnostics)
        recorded = float(output.loc[output.checkup.eq(ck.checkup), "SOH_est"].iloc[0])
        if abs(estimate-recorded) > .00051:
            raise AssertionError("packaged official output was not reproduced")
        previous = float(output.loc[output.checkup.eq(f"CK{int(ck.checkup[2:])-1}"), "SOH_est"].iloc[0]) if ck.checkup != "CK0" else estimate
        for ev in diag.get("event_log", []):
            events.append({"checkup": ck.checkup, **ev})
        rows.append({"checkup": ck.checkup, "date": ck.date.isoformat(), "SOH_est_pp": estimate,
                     "delta_from_previous_ck_pp": estimate-previous,
                     "mode": diag.get("mode"),
                     "primary_rejection": json.dumps(diag.get("primary_rejection", {}), sort_keys=True),
                     "qualified_events": diag.get("qualified_events"),
                     "updates_by_cell": json.dumps(diag.get("updates", [])),
                     "cell_ratios": json.dumps(diag.get("cell_ratios", [])),
                     "pack_rule": diag.get("pack_rule"),
                     "official_accuracy_verified": False,
                     "warning": "large_unvalidated_step" if abs(estimate-previous)>5 else
                                "nonmonotonic_unvalidated" if estimate>previous+2 else ""})
        print(ck.checkup, round(estimate, 3), diag.get("mode"), diag.get("updates"), flush=True)
    pd.DataFrame(rows).to_csv(TASK / "outputs/official_diagnostics.csv", index=False)
    pd.DataFrame(events).to_csv(TASK / "runs/M5_official_candidate/event_diagnostics.csv", index=False)


if __name__ == "__main__":
    main()
