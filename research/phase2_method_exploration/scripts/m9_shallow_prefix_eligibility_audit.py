"""Requalify every P1 charge using data available only through first 3.50V crossing."""
from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
OUT = TASK / "runs/M9_shallow_prefix_eligibility_v1"
OUT.mkdir(parents=True, exist_ok=False)
sys.path.insert(0, str(ROOT / "research/phase2_temperature_improvement/src"))
from event_core import extract_charge_events
from route_a_repaired import stable_cc_prefix

old_events = pd.read_csv(ROOT / "research/phase2_temperature_improvement/runs/M4_feature_audit_v1/events.csv",
                         usecols=["cell_id", "event_id", "event_end", "cc_Ah"])
old_ids = set(old_events.event_id.astype(str))
panel = pd.read_csv(ROOT / "research/phase2_temperature_improvement/outputs/panel_main.csv",
                    usecols=["cell_id", "target_ordinal", "target_discharge_start"])
old_view = pd.read_csv(TASK / "data_manifests/d1_target_visibility.csv")
records = []
for cell_dir in sorted((ROOT / "dataset original").iterdir()):
    if not cell_dir.is_dir():
        continue
    pieces = []
    for path in sorted(cell_dir.glob("*.csv")):
        for chunk in pd.read_csv(path, usecols=["absolute_time", "cycle_number", "step_type",
                                                 "voltage_V", "current_A", "temperature_C"], chunksize=100000):
            part = chunk.loc[~chunk.step_type.eq("cc_discharge")]
            if len(part):
                pieces.append(part.drop(columns="step_type"))
    if not pieces:
        continue
    raw = pd.concat(pieces, ignore_index=True)
    raw["absolute_time"] = pd.to_datetime(raw.absolute_time)
    raw = raw.sort_values("absolute_time", kind="stable").reset_index(drop=True)
    events = extract_charge_events(raw, time_col="absolute_time", voltage_cols=("voltage_V",),
                                   temp_col="temperature_C", segment_col="cycle_number", counter_col=None)
    before = len(records)
    for event in events:
        eid = f"{cell_dir.name}|{event.segment}|{event.start.isoformat()}|{event.end.isoformat()}"
        measured = event.voltages[:, 0]
        crossing = np.flatnonzero((measured[:-1] < 3.50) & (measured[1:] >= 3.50))
        if not len(crossing):
            continue
        stop = int(crossing[0] + 1)
        t = pd.Timestamp(int(event.times_s[stop]), unit="s")
        truncated = replace(event, end=t, duration_s=float(event.times_s[stop] - event.times_s[0]),
                            ah=float(event.q_ah[stop]), times_s=event.times_s[:stop+1].copy(),
                            q_ah=event.q_ah[:stop+1].copy(), voltages=event.voltages[:stop+1].copy(),
                            counter_q_ah=None)
        cc, status = stable_cc_prefix(truncated)
        has_endpoint = bool(status == "pass" and cc is not None and pd.Timestamp(cc.end) >= t)
        rec = {"cell_id": cell_dir.name, "event_id": eid, "source_event_end": event.end.isoformat(),
               "observed_shallow_end": t.isoformat(), "q_at_crossing_Ah": float(event.q_ah[stop]),
               "full_event_old_eligible": eid in old_ids,
               "truncated_cc_status": status,
               "crossing_still_inside_qualified_CC": has_endpoint,
               "median_prefix_temperature_C": float(np.nanmedian(raw.loc[(raw.cycle_number == event.segment) &
                     (raw.absolute_time >= event.start) & (raw.absolute_time <= t), "temperature_C"]))}
        for budget in (15, 20, 30):
            qstart = float(event.q_ah[stop] - budget)
            mask = (event.q_ah[:stop+1] >= qstart)
            rec[f"eligible_{budget}Ah"] = bool(has_endpoint and qstart >= 0 and mask.sum() >= 3)
        records.append(rec)
    print(cell_dir.name, "all events", len(events), "crossings", len(records)-before, flush=True)
    del raw, pieces

events = pd.DataFrame(records)
events.to_csv(OUT / "all_crossing_events.csv", index=False)
target_rows = []
for budget in (15, 20, 30):
    eligible = events.loc[events[f"eligible_{budget}Ah"]].copy()
    eligible["observed_shallow_end"] = pd.to_datetime(eligible.observed_shallow_end)
    for p in panel.itertuples(index=False):
        visible = eligible.loc[eligible.cell_id.eq(p.cell_id) &
            (eligible.observed_shallow_end < pd.Timestamp(p.target_discharge_start))].sort_values(
            ["observed_shallow_end", "event_id"])
        ids = visible.event_id.astype(str).tolist()
        new = set(ids[:10] + ids[-5:])
        match = old_view.loc[old_view.cell_id.eq(p.cell_id) & old_view.target_ordinal.eq(p.target_ordinal) &
                             old_view.budget_Ah.eq(budget) & old_view.history_mode.eq("persistent")].iloc[0]
        old = set(json.loads(match.allowed_event_ids_json))
        target_rows.append({"cell_id": p.cell_id, "target_ordinal": int(p.target_ordinal),
                            "budget_Ah": budget, "old_allowed_count": len(old), "new_allowed_count": len(new),
                            "old_current_event_id": str(match.current_event_id),
                            "new_current_event_id": ids[-1] if ids else "",
                            "added_count": len(new-old), "removed_count": len(old-new),
                            "added_json": json.dumps(sorted(new-old)), "removed_json": json.dumps(sorted(old-new))})
targets = pd.DataFrame(target_rows)
targets.to_csv(OUT / "target_visibility_delta.csv", index=False)
summary = {"crossing_events": len(events),
           "old_whitelisted_crossing_events": int(events.full_event_old_eligible.sum()),
           "eligible_by_budget": {str(b): int(events[f"eligible_{b}Ah"].sum()) for b in (15, 20, 30)},
           "new_eligible_but_old_full_event_rejected_by_budget": {str(b): int((events[f"eligible_{b}Ah"] & ~events.full_event_old_eligible).sum()) for b in (15,20,30)},
           "targets_with_changed_allowed_by_budget": {str(b): int(((targets.budget_Ah.eq(b)) &
               (targets.added_count.add(targets.removed_count).gt(0))).sum()) for b in (15,20,30)},
           "targets_with_changed_current_by_budget": {str(b): int((targets.loc[targets.budget_Ah.eq(b),
               "old_current_event_id"].fillna("").to_numpy(str) != targets.loc[targets.budget_Ah.eq(b),
               "new_current_event_id"].fillna("").to_numpy(str)).sum()) for b in (15,20,30)},
           "status": "audit only; old frozen D1 manifests and scores are not overwritten"}
(OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(summary, ensure_ascii=False), flush=True)
