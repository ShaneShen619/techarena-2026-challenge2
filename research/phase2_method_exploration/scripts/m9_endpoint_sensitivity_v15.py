"""Build causal first-crossing D1 sensitivity views at 3.45 or 3.55 V.

Unlike the retired full-event selector, a candidate is emitted at its first
observed crossing. All qualification and features stop there. This is still a
deep-charge crop proxy, not a real shallow-cycle experiment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research/phase2_temperature_improvement/src"))
from event_core import Event, partial_ah
from route_a_repaired import stable_cc_prefix

parser = argparse.ArgumentParser()
parser.add_argument("--endpoint", choices=["3p45", "3p55"], required=True)
args = parser.parse_args()
threshold = {"3p45": 3.45, "3p55": 3.55}[args.endpoint]
OUT = TASK / "runs" / f"M9_D1_v15_endpoint_{args.endpoint}_v1"
OUT.mkdir(parents=True, exist_ok=False)
template = pd.read_csv(TASK / "data_manifests/d1_v15_target_visibility.csv")
assert len(template) == 1080
windows = [(3.35, 3.39), (3.38, 3.42), (3.41, 3.45), (3.44, 3.48),
           (3.35, 3.42), (3.38, 3.45), (3.41, 3.48), (3.35, 3.45), (3.38, 3.48)]
all_meta, views, crops = [], [], []

for cell_dir in sorted((ROOT / "dataset original").iterdir()):
    if not cell_dir.is_dir() or cell_dir.name not in set(template.cell_id):
        continue
    pieces = []
    for path in sorted(cell_dir.glob("*.csv")):
        for chunk in pd.read_csv(path, usecols=["absolute_time", "cycle_number", "step_type",
                                                 "voltage_V", "current_A", "temperature_C"], chunksize=100000):
            part = chunk.loc[~chunk.step_type.eq("cc_discharge")]
            if len(part):
                pieces.append(part.drop(columns="step_type"))
    raw = pd.concat(pieces, ignore_index=True)
    raw["absolute_time"] = pd.to_datetime(raw.absolute_time)
    raw = raw.sort_values("absolute_time", kind="stable").reset_index(drop=True)
    ts = raw.absolute_time
    seconds = ts.to_numpy(dtype="datetime64[s]").astype("int64")
    current = raw.current_A.to_numpy(float)
    voltage = raw.voltage_V.to_numpy(float)
    temperature = raw.temperature_C.to_numpy(float)
    segment = raw.cycle_number.to_numpy()
    good = np.isfinite(current) & np.isfinite(voltage) & (current >= 5)
    prev_good = np.r_[False, good[:-1]]
    dt = np.diff(seconds, prepend=seconds[0])
    starts = good & ((~prev_good) | (dt <= 0) | (dt > 60) |
                     (segment != np.roll(segment, 1)))
    run_start = np.maximum.accumulate(np.where(starts, np.arange(len(raw)), -1))
    crossings = np.flatnonzero(good & prev_good & ~starts &
        np.r_[False, voltage[:-1] < threshold] & (voltage >= threshold))
    emitted = set()
    cell_events: dict[str, Event] = {}
    cell_meta = []
    for stop in crossings:
        begin = int(run_start[stop])
        if begin < 0 or begin in emitted:
            continue
        emitted.add(begin)
        times = seconds[begin:stop + 1].copy()
        assert len(times) >= 2 and np.all(np.diff(times) > 0)
        amps = current[begin:stop + 1].copy()
        q = np.cumsum(amps * np.diff(times, prepend=times[0]) / 3600.0)
        first_time, end_time = ts.iloc[begin], ts.iloc[stop]
        event = Event(start=first_time, end=end_time, segment=int(segment[begin]),
                      median_current=float(np.median(amps)),
                      median_temp=float(np.nanmedian(temperature[begin:stop + 1])) if np.isfinite(
                          temperature[begin:stop + 1]).any() else float("nan"),
                      duration_s=float(times[-1] - times[0]), ah=float(q[-1]),
                      times_s=times, q_ah=q, voltages=voltage[begin:stop + 1, None].copy(),
                      counter_delta_ah=None, cells=("voltage_V",), counter_q_ah=None)
        cc, status = stable_cc_prefix(event)
        endpoint_in_cc = bool(status == "pass" and cc is not None and pd.Timestamp(cc.end) >= end_time)
        event_id = f"{cell_dir.name}|{int(segment[begin])}|{first_time.isoformat()}|{end_time.isoformat()}"
        item = {"cell_id": cell_dir.name, "event_id": event_id,
                "observed_shallow_end": end_time.isoformat(), "prefix_cc_status": status,
                "endpoint_in_qualified_cc": endpoint_in_cc}
        for budget in (15, 20, 30):
            qstart = float(q[-1] - budget)
            item[f"eligible_{budget}Ah"] = bool(endpoint_in_cc and qstart >= 0 and
                (q >= qstart).sum() >= 3)
        cell_meta.append(item)
        if any(item[f"eligible_{budget}Ah"] for budget in (15, 20, 30)):
            assert cc is not None
            cell_events[event_id] = cc
    all_meta.extend(cell_meta)
    events_df = pd.DataFrame(cell_meta)
    assert not events_df.event_id.duplicated().any()
    events_df["observed_shallow_end"] = pd.to_datetime(events_df.observed_shallow_end)
    selected_by_budget = {15: set(), 20: set(), 30: set()}
    for original in template.loc[template.cell_id.eq(cell_dir.name)].to_dict(orient="records"):
        budget = int(original["budget_Ah"])
        eligible = events_df.loc[events_df[f"eligible_{budget}Ah"] &
            (events_df.observed_shallow_end < pd.Timestamp(original["target_discharge_start"]))].sort_values(
            ["observed_shallow_end", "event_id"])
        ids = eligible.event_id.astype(str).tolist()
        initial, recent = ids[:10], ids[-5:]
        selected = ([ids[-1]] if ids else []) if original["history_mode"] == "cold" else sorted(
            set(initial + recent), key=ids.index)
        selected_by_budget[budget].update(selected)
        original.update({"crop_position": f"first_{args.endpoint}V_crossing_tail",
                         "candidate_event_count": len(ids),
                         "current_event_id": ids[-1] if ids else "",
                         "initial_event_ids_json": json.dumps(initial),
                         "recent_event_ids_json": json.dumps(recent),
                         "allowed_event_ids_json": json.dumps(selected),
                         "allowed_event_count": len(selected),
                         "allowed_event_end_max": eligible.observed_shallow_end.max().isoformat() if len(eligible) else "",
                         "allowed_fragment_end_max": selected[-1].rsplit("|", 1)[-1] if selected else "",
                         "missing_qualified_event_ids_json": "[]",
                         "metadata_status": "native_fragment_verified",
                         "no_event_reason": "" if selected else "no_prefix_qualified_fragment",
                         "forbidden_model_fields": "post_endpoint_rows; full_cc_Ah; target_capacity_Ah; target_soh_pp; future_events",
                         "protocol_version": f"v1.5_{args.endpoint}"})
        views.append(original)
    for budget, event_ids in selected_by_budget.items():
        for event_id in sorted(event_ids):
            cc = cell_events[event_id]
            qstart = float(cc.q_ah[-1] - budget)
            assert qstart >= 0
            mask = cc.q_ah >= qstart
            times = cc.times_s[mask].copy()
            q = cc.q_ah[mask].copy()
            q -= q[0]
            volts = cc.voltages[mask].copy()
            assert len(times) >= 3 and 0 < q[-1] <= budget + 1e-8
            begin, end = pd.Timestamp(int(times[0]), unit="s"), pd.Timestamp(int(times[-1]), unit="s")
            assert end == pd.Timestamp(event_id.rsplit("|", 1)[-1])
            fragment = replace(cc, start=begin, end=end, duration_s=float(times[-1] - times[0]),
                               ah=float(q[-1]), times_s=times, q_ah=q, voltages=volts, counter_q_ah=None)
            segment_id = int(event_id.split("|")[1])
            observed = raw.loc[raw.cycle_number.eq(segment_id) &
                raw.absolute_time.ge(begin) & raw.absolute_time.le(end) & raw.current_A.ge(5)]
            intervals = np.diff(times).astype(float)
            assert (intervals > 0).all() and intervals.max() <= 60
            item = {"cell_id": cell_dir.name, "event_id": event_id, "budget_Ah": budget,
                    "crop_position": f"first_{args.endpoint}V_crossing_tail",
                    "fragment_start": begin.isoformat(), "fragment_end": end.isoformat(),
                    "n_samples": len(times), "observed_span_Ah": float(q[-1]),
                    "median_dt_s": float(np.median(intervals)), "max_dt_s": float(intervals.max()),
                    "temperature_C": float(observed.temperature_C.median()) if observed.temperature_C.notna().any() else np.nan,
                    "current_A": float(observed.current_A.median()) if len(observed) else np.nan,
                    "v_start_V": float(volts[0, 0]), "v_end_V": float(volts[-1, 0])}
            for j, (lo, hi) in enumerate(windows):
                value = partial_ah(fragment, 0, lo, hi)
                item[f"w{j:02d}_Ah"] = float(value) if value is not None else np.nan
                item[f"w{j:02d}_visible"] = int(value is not None)
            crops.append(item)
    print(cell_dir.name, "crossings", len(events_df), "selected", len(set.union(*selected_by_budget.values())), flush=True)
    del raw, pieces, cell_events

metadata = pd.DataFrame(all_meta)
metadata.to_csv(OUT / "prefix_crossing_audit.csv", index=False)
manifest = pd.DataFrame(views).sort_values(["budget_Ah", "cell_id", "target_ordinal", "history_mode"])
crop = pd.DataFrame(crops)
assert len(manifest) == 1080 and not manifest.duplicated(
    ["budget_Ah", "cell_id", "target_ordinal", "history_mode"]).any()
assert not crop.duplicated(["event_id", "budget_Ah"]).any()
assert not {"source_event_end", "full_cc_Ah", "target_soh_pp", "target_capacity_Ah"} & set(crop)
manifest.to_csv(OUT / "visibility.csv", index=False)
crop.to_csv(OUT / "cropped_events.csv", index=False)
summary = {"endpoint_V": threshold, "first_crossings": len(metadata),
           "eligible_by_budget": {str(b): int(metadata[f"eligible_{b}Ah"].sum()) for b in (15, 20, 30)},
           "target_views": len(manifest), "crop_rows": len(crop),
           "zero_event_views": int(manifest.allowed_event_count.eq(0).sum()),
           "selection_uses_post_endpoint": False,
           "visibility_sha256": hashlib.sha256((OUT / "visibility.csv").read_bytes()).hexdigest(),
           "crop_sha256": hashlib.sha256((OUT / "cropped_events.csv").read_bytes()).hexdigest()}
(OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(summary, ensure_ascii=False), flush=True)
