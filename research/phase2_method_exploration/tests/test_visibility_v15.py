"""Independently check the corrected D1 shallow-prefix input boundary."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pandas as pd

TASK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK / "src"))
from visibility import D1Visibility, FEATURE_COLUMNS


def main() -> None:
    manifest_path = TASK / "data_manifests/d1_v15_target_visibility.csv"
    crop_path = TASK / "data_manifests/d1_v15_cropped_events.csv"
    manifest = pd.read_csv(manifest_path)
    crops = pd.read_csv(crop_path)
    audit = pd.read_csv(TASK / "runs/M9_shallow_prefix_eligibility_v1/all_crossing_events.csv",
                        parse_dates=["observed_shallow_end"])
    assert len(manifest) == 1080 and not manifest.duplicated(
        ["cell_id", "target_ordinal", "budget_Ah", "history_mode"]).any()
    assert not crops.duplicated(["event_id", "budget_Ah"]).any()
    assert manifest.protocol_version.eq("v1.5").all()
    assert not {"source_event_end", "full_cc_Ah", "target_soh_pp", "target_capacity_Ah"} & set(crops)
    boundary = D1Visibility(manifest_path, crop_path)
    for row in manifest.itertuples(index=False):
        budget = int(row.budget_Ah)
        candidate = audit.loc[audit.cell_id.eq(row.cell_id) & audit[f"eligible_{budget}Ah"] &
            (audit.observed_shallow_end < pd.Timestamp(row.target_discharge_start))].sort_values(
            ["observed_shallow_end", "event_id"])
        assert len(candidate) == row.candidate_event_count
        ids = ["|".join(source.split("|")[:3]) + "|" + end.isoformat()
               for source, end in zip(candidate.event_id, candidate.observed_shallow_end)]
        expected = ([ids[-1]] if ids else []) if row.history_mode == "cold" else sorted(
            set(ids[:10] + ids[-5:]), key=ids.index)
        assert json.loads(row.allowed_event_ids_json) == expected
        view = boundary.get(row.cell_id, int(row.target_ordinal), budget, row.history_mode)
        assert list(view["fragments"].columns) == FEATURE_COLUMNS
        assert len(view["fragments"]) == len(expected)
        assert view["prefix_prequalified_charge_count"] == len(candidate)
        assert view["fragments"].observed_span_Ah.le(budget + 1e-8).all()
        assert pd.to_datetime(view["fragments"].fragment_end).lt(
            pd.Timestamp(row.target_discharge_start)).all()
        assert view["fragments"].max_dt_s.le(60).all()
        for event_id in expected:
            crop = crops.loc[crops.event_id.eq(event_id) & crops.budget_Ah.eq(budget)].iloc[0]
            assert pd.Timestamp(crop.fragment_end) == pd.Timestamp(event_id.rsplit("|", 1)[-1])
    # Poison the model-facing crop with a future capacity label; fail closed.
    with tempfile.TemporaryDirectory() as temp:
        poisoned_path = Path(temp) / "crop.csv"
        crops.assign(target_soh_pp=99.0).to_csv(poisoned_path, index=False)
        try:
            D1Visibility(manifest_path, poisoned_path)
        except AssertionError:
            pass
        else:
            raise AssertionError("v1.5 boundary accepted a target label")
    print(json.dumps({"views_checked": len(manifest), "crop_rows": len(crops),
                      "independent_prefix_count_and_event_list_match": True,
                      "model_facing_label_injection_rejected": True}))


if __name__ == "__main__":
    main()
