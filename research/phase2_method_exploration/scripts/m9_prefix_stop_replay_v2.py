"""Counterfactual first-crossing replay without completed-event extraction.

Only a current row and earlier rows in its positive-current run determine a
first-3.50V event. The offline vectorization finds each run start from previous
rows; it never needs a later charge-run boundary to emit the crossing.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
OUT = TASK / "runs/M9_prefix_stop_replay_v2"
OUT.mkdir(parents=True, exist_ok=False)
sys.path.insert(0, str(ROOT / "research/phase2_temperature_improvement/src"))
from event_core import Event
from route_a_repaired import stable_cc_prefix

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
    raw = pd.concat(pieces, ignore_index=True)
    raw["absolute_time"] = pd.to_datetime(raw.absolute_time)
    raw = raw.sort_values("absolute_time", kind="stable").reset_index(drop=True)
    ts = raw.absolute_time
    seconds = ts.to_numpy(dtype="datetime64[s]").astype("int64")
    current = raw.current_A.to_numpy(float)
    voltage = raw.voltage_V.to_numpy(float)
    temp = raw.temperature_C.to_numpy(float)
    segment = raw.cycle_number.to_numpy()
    good = np.isfinite(current) & np.isfinite(voltage) & (current >= 5)
    prev_good = np.r_[False, good[:-1]]
    dt = np.diff(seconds, prepend=seconds[0])
    # A new run is identifiable at the current sample from current and past.
    starts = good & ((~prev_good) | (dt <= 0) | (dt > 60) |
                     (segment != np.roll(segment, 1)))
    run_start = np.maximum.accumulate(np.where(starts, np.arange(len(raw)), -1))
    crossings = np.flatnonzero(good & prev_good & ~starts &
                               np.r_[False, voltage[:-1] < 3.50] & (voltage >= 3.50))
    # Keep the first crossing in each positive-current run. Later crossings
    # cannot modify an event already emitted at the first crossing.
    first = []
    emitted = set()
    for stop in crossings:
        begin = int(run_start[stop])
        if begin < 0 or begin in emitted:
            continue
        emitted.add(begin)
        first.append((begin, int(stop)))
    before = len(records)
    for begin, stop in first:
        times = seconds[begin:stop + 1].copy()
        assert len(times) >= 2 and np.all(np.diff(times) > 0)
        currents = current[begin:stop + 1].copy()
        q = np.cumsum(currents * np.diff(times, prepend=times[0]) / 3600.0)
        start_time, end_time = ts.iloc[begin], ts.iloc[stop]
        event = Event(start=start_time, end=end_time, segment=int(segment[begin]),
                      median_current=float(np.median(currents)),
                      median_temp=float(np.nanmedian(temp[begin:stop + 1])) if np.isfinite(
                          temp[begin:stop + 1]).any() else float("nan"),
                      duration_s=float(times[-1] - times[0]), ah=float(q[-1]),
                      times_s=times, q_ah=q, voltages=voltage[begin:stop + 1, None].copy(),
                      counter_delta_ah=None, cells=("voltage_V",), counter_q_ah=None)
        cc, status = stable_cc_prefix(event)
        endpoint_inside_cc = bool(status == "pass" and cc is not None and
                                  pd.Timestamp(cc.end) >= end_time)
        rec = {"cell_id": cell_dir.name, "event_id":
               f"{cell_dir.name}|{int(segment[begin])}|{start_time.isoformat()}|{end_time.isoformat()}",
               "observed_shallow_end": end_time.isoformat(),
               "truncated_cc_status": status,
               "crossing_still_inside_qualified_CC": endpoint_inside_cc}
        for budget in (15, 20, 30):
            qstart = float(q[-1] - budget)
            rec[f"eligible_{budget}Ah"] = bool(endpoint_inside_cc and qstart >= 0 and
                (q >= qstart).sum() >= 3)
        records.append(rec)
    print(cell_dir.name, "first crossings emitted", len(records) - before, flush=True)
    del raw, pieces

replay = pd.DataFrame(records)
replay.to_csv(OUT / "prefix_only_crossings.csv", index=False)
prior = pd.read_csv(TASK / "runs/M9_shallow_prefix_eligibility_v1/all_crossing_events.csv")
prior["prefix_id"] = ["|".join(source.split("|")[:3]) + "|" + end
                      for source, end in zip(prior.event_id, prior.observed_shallow_end)]
shared = set(prior.prefix_id) & set(replay.event_id)
assert not replay.event_id.duplicated().any()
assert len(shared) == len(prior), (len(shared), len(prior))
for budget in (15, 20, 30):
    old = set(prior.loc[prior[f"eligible_{budget}Ah"], "prefix_id"])
    new = set(replay.loc[replay[f"eligible_{budget}Ah"], "event_id"])
    assert old == new, (budget, len(old - new), len(new - old))
manifest = pd.read_csv(TASK / "data_manifests/d1_v15_target_visibility.csv")
replay["observed_shallow_end"] = pd.to_datetime(replay.observed_shallow_end)
for row in manifest.itertuples(index=False):
    budget = int(row.budget_Ah)
    visible = replay.loc[replay.cell_id.eq(row.cell_id) & replay[f"eligible_{budget}Ah"] &
        (replay.observed_shallow_end < pd.Timestamp(row.target_discharge_start))].sort_values(
        ["observed_shallow_end", "event_id"])
    ids = visible.event_id.astype(str).tolist()
    allowed = [ids[-1]] if row.history_mode == "cold" and ids else (
        sorted(set(ids[:10] + ids[-5:]), key=ids.index) if row.history_mode == "persistent" else [])
    assert len(ids) == row.candidate_event_count
    assert allowed == json.loads(row.allowed_event_ids_json)
summary = {"prefix_first_crossings": len(replay), "old_completed_events_with_crossing": len(prior),
           "shared_event_ids": len(shared),
           "eligible_counts": {str(b): int(replay[f"eligible_{b}Ah"].sum()) for b in (15, 20, 30)},
           "all_1080_target_views_equal": True,
           "candidate_emission_uses_full_run_end": False,
           "note": "Offline vectorized simulation: every start and first-crossing decision uses current or earlier rows; no completed-event extractor is called."}
(OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(summary, ensure_ascii=False), flush=True)
