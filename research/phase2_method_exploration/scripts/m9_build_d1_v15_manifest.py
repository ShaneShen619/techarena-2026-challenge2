"""Protocol v1.5 D1 views selected only by shallow-prefix eligibility/end time."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

TASK = Path(__file__).resolve().parents[1]
OUT = TASK / "data_manifests"
audit = pd.read_csv(TASK / "runs/M9_shallow_prefix_eligibility_v1/all_crossing_events.csv",
                    parse_dates=["observed_shallow_end"])
old = pd.read_csv(OUT / "d1_target_visibility.csv")
assert len(old) == 1080 and not audit.event_id.duplicated().any()
views = []
for budget in (15, 20, 30):
    eligible = audit.loc[audit[f"eligible_{budget}Ah"]].copy()
    # Event identifiers themselves may be inspected by a model adapter. Use
    # only the simulated end time; never encode the later full-charge end.
    eligible["event_id"] = ["|".join(eid.split("|")[:3]) + "|" + end.isoformat()
                            for eid, end in zip(eligible.event_id, eligible.observed_shallow_end)]
    for row in old.loc[old.budget_Ah.eq(budget)].to_dict(orient="records"):
        visible = eligible.loc[eligible.cell_id.eq(row["cell_id"]) &
            (eligible.observed_shallow_end < pd.Timestamp(row["target_discharge_start"]))].sort_values(
            ["observed_shallow_end", "event_id"])
        ids = visible.event_id.astype(str).tolist()
        initial = ids[:10]
        recent = ids[-5:]
        current = ids[-1] if ids else None
        selected = [current] if row["history_mode"] == "cold" and current else (
            sorted(set(initial + recent), key=ids.index) if row["history_mode"] == "persistent" else [])
        row["candidate_event_count"] = len(ids)
        row["current_event_id"] = current if current else ""
        row["initial_event_ids_json"] = json.dumps(initial)
        row["recent_event_ids_json"] = json.dumps(recent)
        row["allowed_event_ids_json"] = json.dumps(selected)
        row["allowed_event_count"] = len(selected)
        row["allowed_event_end_max"] = visible.observed_shallow_end.max().isoformat() if len(visible) else ""
        row["allowed_fragment_end_max"] = ""
        row["missing_qualified_event_ids_json"] = "[]"
        row["metadata_status"] = "shallow_prefix_prequalified_raw_crop_pending"
        row["no_event_reason"] = "" if selected else "no_prefix_qualified_fragment"
        row["forbidden_model_fields"] = "post_3p50V_rows; full_cc_Ah; target_capacity_Ah; target_soh_pp; future_events"
        row["allowed_model_fields"] = "cropped_I_V_T_time; cropped_window_Ah; window_mask; anchor_capacity_Ah; count_of_prior_prefix_qualified_charge_events"
        row["protocol_version"] = "v1.5"
        views.append(row)
frame = pd.DataFrame(views).sort_values(["budget_Ah", "cell_id", "target_ordinal", "history_mode"])
assert len(frame) == 1080 and not frame.duplicated(["budget_Ah", "cell_id", "target_ordinal", "history_mode"]).any()
for row in frame.itertuples(index=False):
    if row.allowed_event_end_max:
        assert pd.Timestamp(row.allowed_event_end_max) < pd.Timestamp(row.target_discharge_start)
frame.to_csv(OUT / "d1_v15_target_visibility_draft.csv", index=False)
wanted = {eid for field in frame.allowed_event_ids_json for eid in json.loads(field)}
summary = {"target_views": len(frame), "selected_event_ids_any_budget": len(wanted),
           "selected_event_ids_20Ah": len({eid for field in frame.loc[frame.budget_Ah.eq(20),
                         "allowed_event_ids_json"] for eid in json.loads(field)}),
           "count_is_prefix_endpoint_qualified": True,
           "selection_reads_post_endpoint": False,
           "source": "M9_shallow_prefix_eligibility_v1/all_crossing_events.csv"}
(OUT / "d1_v15_manifest_draft_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(summary, ensure_ascii=False), flush=True)
