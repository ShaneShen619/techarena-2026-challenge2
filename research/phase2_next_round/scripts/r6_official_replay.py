"""Replay one candidate on CK0--CK7 using only each legal prefix."""
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
parser = argparse.ArgumentParser()
parser.add_argument("--candidate", choices=["ck0_hold", "exploratory_fallback"], required=True)
args = parser.parse_args()
package = TASK / "candidates" / args.candidate
sys.path.insert(0, str(package))
from framework.data import load_dataset, load_eval_points
from my_model import ActiveModel

points = load_eval_points(str(ROOT / "data"))
assert points.checkup.tolist() == [f"CK{i}" for i in range(8)]
model = ActiveModel()
model.fit(load_dataset(str(ROOT / "data")))
rows = []
for point in points.itertuples(index=False):
    dataset = load_dataset(str(ROOT / "data"), until=point.date)
    assert dataset.operation.empty or bool((dataset.operation.timestamp <= point.date).all())
    assert bool((dataset.checkups_released.date <= point.date).all())
    estimate = float(model.estimate_soh(dataset, point.date))
    detail = getattr(model, "last_diagnostics", {}) or {}
    rows.append({
        "candidate": args.candidate,
        "checkup": point.checkup,
        "date": str(pd.Timestamp(point.date).date()),
        "SOH_est_pp": estimate,
        "capacity_est_Ah": estimate * 102 / 100,
        "branch": detail.get("mode", "released_anchor_hold" if args.candidate == "ck0_hold" else "unknown"),
        "qualified_events": detail.get("qualified_events", np.nan),
        "visible_operation_rows": len(dataset.operation),
        "max_visible_timestamp": str(dataset.operation.timestamp.max()) if len(dataset.operation) else "",
        "visible_capacity_labels": len(dataset.checkups_released),
        "true_SOH_pp": estimate if point.checkup == "CK0" else np.nan,
        "absolute_error_pp": 0.0 if point.checkup == "CK0" else np.nan,
        "official_capacity_accuracy_verified": point.checkup == "CK0",
    })
frame = pd.DataFrame(rows)
path = TASK / "outputs" / f"r6_{args.candidate}_official_prefix.csv"
frame.to_csv(path, index=False)
summary = {
    "candidate": args.candidate,
    "checkpoints": len(frame),
    "strict_prefix_pass": True,
    "hidden_truth_count": 7,
    "official_capacity_accuracy_verified": False,
    "model_sha256": hashlib.sha256((package / "my_model/model.py").read_bytes()).hexdigest(),
}
(TASK / "runs" / f"R6_{args.candidate}_official_replay_v1").mkdir(parents=True, exist_ok=False)
(TASK / "runs" / f"R6_{args.candidate}_official_replay_v1" / "summary.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(frame[["checkup", "SOH_est_pp", "branch"]].to_string(index=False))
