"""Rebuild protocol v1.5 shallow-only model features and native sequences."""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
OUT = TASK / "runs/M9_D1_v15_inputs_v1"
OUT.mkdir(parents=True, exist_ok=False)
sys.path.insert(0, str(ROOT / "research/phase2_temperature_improvement/src"))
from event_core import extract_charge_events, partial_ah
from route_a_repaired import stable_cc_prefix

draft = pd.read_csv(TASK / "data_manifests/d1_v15_target_visibility_draft.csv")
needed = {budget: {e for field in draft.loc[draft.budget_Ah.eq(budget), "allowed_event_ids_json"]
                   for e in json.loads(field)} for budget in (15, 20, 30)}
wanted = set.union(*needed.values())
windows = [(3.35, 3.39), (3.38, 3.42), (3.41, 3.45), (3.44, 3.48),
           (3.35, 3.42), (3.38, 3.45), (3.41, 3.48), (3.35, 3.45), (3.38, 3.48)]
L = 64
rows, seqs, seq_ids, seq_cells, seq_lengths, sequence_manifest, restricted_audit = [], [], [], [], [], [], []
found = set()
for cell in sorted(draft.cell_id.unique()):
    cell_ids = {e for e in wanted if e.startswith(cell + "|")}
    cycles = {int(e.split("|")[1]) for e in cell_ids}
    pieces = []
    for path in sorted((ROOT / "dataset original" / cell).glob("*.csv")):
        for chunk in pd.read_csv(path, usecols=["absolute_time", "cycle_number", "step_type", "voltage_V",
                                                 "current_A", "temperature_C"], chunksize=100000):
            part = chunk.loc[chunk.cycle_number.isin(cycles) & ~chunk.step_type.eq("cc_discharge")]
            if len(part):
                pieces.append(part.drop(columns="step_type"))
    raw = pd.concat(pieces, ignore_index=True)
    raw["absolute_time"] = pd.to_datetime(raw.absolute_time)
    raw = raw.sort_values("absolute_time", kind="stable").reset_index(drop=True)
    events = extract_charge_events(raw, time_col="absolute_time", voltage_cols=("voltage_V",),
                                   temp_col="temperature_C", segment_col="cycle_number", counter_col=None)
    for event in events:
        v = event.voltages[:, 0]
        crossing = np.flatnonzero((v[:-1] < 3.50) & (v[1:] >= 3.50))
        if not len(crossing):
            continue
        stop = int(crossing[0] + 1)
        shallow_end = pd.Timestamp(int(event.times_s[stop]), unit="s")
        pid = f"{cell}|{event.segment}|{event.start.isoformat()}|{shallow_end.isoformat()}"
        if pid not in cell_ids:
            continue
        found.add(pid)
        truncated = replace(event, end=shallow_end,
                            duration_s=float(event.times_s[stop] - event.times_s[0]),
                            ah=float(event.q_ah[stop]), times_s=event.times_s[:stop+1].copy(),
                            q_ah=event.q_ah[:stop+1].copy(), voltages=event.voltages[:stop+1].copy(),
                            counter_q_ah=None)
        cc, status = stable_cc_prefix(truncated)
        assert status == "pass" and cc is not None and pd.Timestamp(cc.end) >= shallow_end, (pid, status)
        restricted_audit.append({"event_id": pid, "source_completed_event_end_audit_only": event.end,
                                 "shallow_endpoint": shallow_end, "truncated_qualifier": status})
        for budget in (15, 20, 30):
            if pid not in needed[budget]:
                continue
            qstart = float(cc.q_ah[stop] - budget)
            assert qstart >= 0
            mask = (cc.q_ah >= qstart) & (np.arange(len(cc.q_ah)) <= stop)
            times = cc.times_s[mask].copy()
            voltage = cc.voltages[mask].copy()
            q = cc.q_ah[mask].copy()
            q -= q[0]
            span = float(q[-1])
            assert 0 < span <= budget + 1e-8 and len(times) >= 3
            begin = pd.Timestamp(int(times[0]), unit="s")
            end = pd.Timestamp(int(times[-1]), unit="s")
            assert end == shallow_end
            fragment = replace(cc, start=begin, end=end, duration_s=float(times[-1] - times[0]),
                               ah=span, times_s=times, q_ah=q, voltages=voltage, counter_q_ah=None)
            selected = raw.loc[raw.cycle_number.eq(event.segment) &
                               raw.absolute_time.ge(begin) & raw.absolute_time.le(end) & raw.current_A.ge(5)]
            dt = np.diff(times).astype(float)
            assert (dt > 0).all() and dt.max() <= 60
            temperature = float(selected.temperature_C.median()) if selected.temperature_C.notna().any() else np.nan
            current = float(selected.current_A.median()) if len(selected) else np.nan
            rec = {"cell_id": cell, "event_id": pid, "budget_Ah": budget,
                   "crop_position": "first_3p50V_crossing_tail", "fragment_start": begin.isoformat(),
                   "fragment_end": end.isoformat(), "n_samples": len(times), "observed_span_Ah": span,
                   "median_dt_s": float(np.median(dt)), "max_dt_s": float(dt.max()),
                   "temperature_C": temperature, "current_A": current,
                   "v_start_V": float(voltage[0, 0]), "v_end_V": float(voltage[-1, 0])}
            for j, (lo, hi) in enumerate(windows):
                value = partial_ah(fragment, 0, lo, hi)
                rec[f"w{j:02d}_Ah"] = float(value) if value is not None else np.nan
                rec[f"w{j:02d}_visible"] = int(value is not None)
            rows.append(rec)
            if budget == 20:
                assert len(times) <= L
                amps = np.empty(len(times))
                amps[1:] = 3600 * np.diff(q) / np.diff(times)
                amps[0] = amps[1]
                X = np.zeros((L, 5), np.float32)
                offset = L - len(times)
                X[offset:, 0] = (voltage[:, 0] - 3.45) / .1
                X[offset:, 1] = amps / 100
                X[offset:, 2] = temperature / 50 if np.isfinite(temperature) else 0
                X[offset:, 3] = q / 20
                X[offset:, 4] = 1
                seqs.append(X)
                seq_ids.append(pid)
                seq_cells.append(cell)
                seq_lengths.append(len(times))
                sequence_manifest.append({"event_id": pid, "cell_id": cell,
                                          "fragment_start": begin.isoformat(), "fragment_end": end.isoformat(),
                                          "n_native_samples": len(times), "span_Ah": span,
                                          "native_median_dt_s": float(np.median(dt)),
                                          "source_voltage_first_V": float(voltage[0, 0]),
                                          "source_voltage_last_V": float(voltage[-1, 0]),
                                          "source_temperature_C": temperature})
    print(cell, "needed", len(cell_ids), "found", len(found & cell_ids), flush=True)
    del raw, pieces

assert found == wanted, (len(found), len(wanted), list(wanted-found)[:3])
crop = pd.DataFrame(rows)
assert not crop.duplicated(["event_id", "budget_Ah"]).any()
crop.to_csv(TASK / "data_manifests/d1_v15_cropped_events.csv", index=False)
pd.DataFrame(restricted_audit).to_csv(OUT / "source_end_audit_restricted.csv", index=False)
assert len(seq_ids) == len(needed[20]) and len(seq_ids) == len(set(seq_ids))
np.savez_compressed(OUT / "native_sequences.npz", event_ids=np.array(seq_ids), cell_ids=np.array(seq_cells),
                    X=np.stack(seqs), length=np.array(seq_lengths, np.int16))
pd.DataFrame(sequence_manifest).to_csv(OUT / "sequence_manifest.csv", index=False)
index = {(str(r.event_id), int(r.budget_Ah)): r for r in crop.itertuples(index=False)}
final = []
for row in draft.to_dict(orient="records"):
    budget = int(row["budget_Ah"])
    ids = json.loads(row["allowed_event_ids_json"])
    assert all((eid, budget) in index for eid in ids)
    row["allowed_fragment_end_max"] = max((index[(eid, budget)].fragment_end for eid in ids), default="")
    row["metadata_status"] = "native_fragment_verified"
    final.append(row)
view = pd.DataFrame(final)
view.to_csv(TASK / "data_manifests/d1_v15_target_visibility.csv", index=False)
summary = {"selected_events": len(wanted), "20Ah_events": len(seq_ids),
           "crop_rows": len(crop), "target_views": len(view),
           "crop_sha256": hashlib.sha256((TASK / "data_manifests/d1_v15_cropped_events.csv").read_bytes()).hexdigest(),
           "visibility_sha256": hashlib.sha256((TASK / "data_manifests/d1_v15_target_visibility.csv").read_bytes()).hexdigest(),
           "native_sequences_sha256": hashlib.sha256((OUT / "native_sequences.npz").read_bytes()).hexdigest(),
           "forbidden_full_event_end_only_in_restricted_audit": True,
           "model_input_labels_absent": True}
(OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(summary, ensure_ascii=False), flush=True)
