"""Independent official CK0--CK7 strict-prefix replay; no hidden labels inferred."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
OUT = TASK / "runs/M9_official_replay_v1"
OUT.mkdir(parents=True, exist_ok=False)
PACKAGE = TASK / "runs/M9_existing_fallback_package_v1"
sys.path.insert(0, str(PACKAGE))
from my_model import ActiveModel
from framework.data import load_dataset, load_eval_points

data = ROOT / "data"
checkups = load_eval_points(str(data))
assert checkups.checkup.tolist() == [f"CK{i}" for i in range(8)]
model = ActiveModel()
model.fit(load_dataset(str(data)))
assert not hasattr(model, "operation")
assert not hasattr(model, "full_dataset")
q0 = float(load_dataset(str(data), until=checkups.date.iloc[0]).bol_capacity_Ah)
baseline = 100 * q0 / 102
scenarios = pd.read_csv(TASK / "runs/M5_official_scenarios_v1/official_assumption_envelopes.csv").set_index("checkup")
rows, diagnostics = [], []
for p in checkups.itertuples(index=False):
    ds = load_dataset(str(data), until=p.date)
    assert ds.operation.empty or (ds.operation.timestamp <= p.date).all()
    assert (ds.checkups_released.date <= p.date).all()
    forecast = float(model.estimate_soh(ds, p.date))
    detail = dict(model.last_diagnostics)
    truth = float(100 * q0 / 102) if p.checkup == "CK0" else np.nan
    for method, pred, mode in (("CK0_hold", baseline, "released_anchor_hold"),
                               ("existing_multi_temp_fallback", forecast, detail.get("mode", "unknown"))):
        rows.append({"checkup": p.checkup, "date": str(p.date.date()), "method": method,
                     "SOH_est_pp": pred, "capacity_est_Ah": pred * 102 / 100,
                     "true_capacity_Ah": q0 if p.checkup == "CK0" else np.nan,
                     "true_SOH_pp": truth, "mode": mode,
                     "n_operation_rows_visible": len(ds.operation), "max_visible_timestamp":
                     str(ds.operation.timestamp.max()) if len(ds.operation) else "",
                     "released_capacity_labels_visible": len(ds.checkups_released),
                     "official_capacity_accuracy_verified": p.checkup == "CK0"})
    scenario = scenarios.loc[p.checkup] if p.checkup in scenarios.index else None
    diagnostics.append({"checkup": p.checkup, "date": str(p.date.date()),
                        "actual_branch": detail.get("mode", "unknown"),
                        "full_detail_json": json.dumps(detail, ensure_ascii=False, default=str),
                        "qualified_events": detail.get("qualified_events", np.nan),
                        "scenario_deep_proxy_Ah": float(scenario.deep_proxy_Ah) if scenario is not None else np.nan,
                        "scenario_q05_Ah": float(scenario.explicit_q05_Ah) if scenario is not None else np.nan,
                        "scenario_q50_Ah": float(scenario.explicit_q50_Ah) if scenario is not None else np.nan,
                        "scenario_q95_Ah": float(scenario.explicit_q95_Ah) if scenario is not None else np.nan,
                        "scenario_interval_calibrated": False,
                        "limitation": "CK1-CK7 hidden; M5 range is an assumption envelope, not empirical confidence"})
pd.DataFrame(rows).to_csv(TASK / "outputs/official_predictions.csv", index=False)
pd.DataFrame(diagnostics).to_csv(TASK / "outputs/official_diagnostics.csv", index=False)
summary = {"checkpoints": 8, "methods": 2, "hidden_truth_count": 7,
           "baseline_CK0_SOH_pp": baseline,
           "candidate_sha256": hashlib.sha256((PACKAGE / "my_model/model.py").read_bytes()).hexdigest(),
           "all_operation_prefixes_causal": True,
           "official_capacity_accuracy_verified": False,
           "claim_limit": "Existing exploratory fallback point estimates are unvalidated; scenario ranges are uncalibrated."}
(OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(pd.DataFrame(rows)[["checkup", "method", "SOH_est_pp", "mode"]].to_string(index=False), flush=True)
