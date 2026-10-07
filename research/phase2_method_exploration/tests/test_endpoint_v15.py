"""Audit first-crossing endpoint sensitivities from saved prefix-only artifacts."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

TASK = Path(__file__).resolve().parents[1]

for endpoint, voltage in (("3p45", 3.45), ("3p55", 3.55)):
    folder = TASK / "runs" / f"M9_D1_v15_endpoint_{endpoint}_v1"
    summary = json.loads((folder / "summary.json").read_text())
    views = pd.read_csv(folder / "visibility.csv")
    crop = pd.read_csv(folder / "cropped_events.csv")
    audits = pd.read_csv(folder / "prefix_crossing_audit.csv")

    assert summary["selection_uses_post_endpoint"] is False
    assert summary["endpoint_V"] == voltage
    assert len(views) == 1080 and summary["target_views"] == 1080
    assert views.groupby(["budget_Ah", "history_mode"]).size().eq(180).all()
    assert not views.duplicated(["cell_id", "target_ordinal", "budget_Ah", "history_mode"]).any()
    assert not crop.duplicated(["event_id", "budget_Ah"]).any()
    assert len(crop) == summary["crop_rows"]
    assert len(audits) == summary["first_crossings"]
    assert np.all(crop.v_end_V >= voltage - 1e-10)
    assert np.all(crop.observed_span_Ah <= crop.budget_Ah + 1e-8)
    assert np.all(crop.max_dt_s <= 60)
    assert not {"target_soh_pp", "target_capacity_Ah", "full_cc_Ah", "source_event_end"} & set(crop)
    crop_keys = set(zip(crop.event_id, crop.budget_Ah))
    for row in views.itertuples(index=False):
        ids = json.loads(row.allowed_event_ids_json)
        assert len(ids) == row.allowed_event_count
        assert all((event_id, row.budget_Ah) in crop_keys for event_id in ids)
        assert all(pd.Timestamp(event_id.rsplit("|", 1)[-1]) < pd.Timestamp(row.target_discharge_start)
                   for event_id in ids)
    for budget in (15, 20, 30):
        assert int(audits[f"eligible_{budget}Ah"].sum()) == summary["eligible_by_budget"][str(budget)]
    print(endpoint, "views", len(views), "crops", len(crop), "crossings", len(audits))
