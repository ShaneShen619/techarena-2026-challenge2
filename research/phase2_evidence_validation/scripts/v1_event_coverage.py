"""Frozen-rule official event inventory and CK-prefix coverage; no capacity labels."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
OUT = TASK / "runs/V1_event_coverage_20260929_v2"
OUT.mkdir(parents=True, exist_ok=True)
if (OUT / "COMPLETED").exists():
    raise RuntimeError(f"Completed run is immutable: {OUT}")
CONFIG = TASK / "configs/r02.json"
cfg = json.loads(CONFIG.read_text())
lo, hi = cfg["strict_discharge_current_range"]["value"]
min_span = cfg["min_contiguous_span"]["value"]
max_gap = cfg["max_sample_gap"]["value"]
for name in ("protocol.json", "acceptance.json", "r02.json", "r05.json", "frozen_manifest.json"):
    shutil.copy2(TASK / "configs" / name, OUT / name)

cols = ["timestamp", "segment", "chamber_temperature_C", "current_A", "charge_Ah_cum",
        "discharge_Ah_cum", "pack_voltage_V", "temp_mean_C", "temp_min_C", "temp_max_C",
        "cell1_V", "cell2_V", "cell3_V", "cell4_V"]
pieces = [pd.read_csv(p, usecols=cols, parse_dates=["timestamp"])
          for p in sorted((ROOT / "data/operation").glob("segment_*.csv.gz"))]
raw = pd.concat(pieces, ignore_index=True)
raw.sort_values("timestamp", kind="stable", inplace=True)
raw.reset_index(drop=True, inplace=True)
i = raw.current_A.to_numpy(float)
classes = np.full(len(raw), "rest_or_small", dtype=object)
classes[i >= 1.0] = "charge"
classes[(i <= -1.0) & (i > -lo)] = "other_discharge"
classes[(i <= -lo) & (i >= -hi)] = "strict_5p1"
classes[(i < -hi) & (i > -15.0)] = "other_discharge"
classes[(i <= -15.0) & (i >= -25.0)] = "pulse_20A"
classes[i < -25.0] = "other_discharge"
raw["event_class"] = classes
gap = raw.timestamp.diff().dt.total_seconds().fillna(0)
bound = (raw.event_class.ne(raw.event_class.shift()) | raw.segment.ne(raw.segment.shift()) |
         (gap > max_gap) | (gap <= 0))
raw["event_index"] = bound.cumsum().astype(int)
within = raw.event_index.eq(raw.event_index.shift()) & gap.gt(0)
dt_same_event = gap.where(within, 0.0).to_numpy(float)
prev_i = raw.current_A.shift().fillna(0).to_numpy(float)
average_i = 0.5 * (i + prev_i)
raw["integrated_discharge_step_Ah"] = np.maximum(-average_i, 0.0) * dt_same_event / 3600.0
raw["integrated_charge_step_Ah"] = np.maximum(average_i, 0.0) * dt_same_event / 3600.0

valid = raw.event_class.ne("rest_or_small")
grouped = raw.loc[valid].groupby("event_index", sort=True)
event = grouped.agg(
    segment=("segment", "first"), event_class=("event_class", "first"),
    start=("timestamp", "first"), end=("timestamp", "last"), n_samples=("timestamp", "size"),
    current_median_A=("current_A", "median"), current_min_A=("current_A", "min"),
    current_max_A=("current_A", "max"),
    chamber_C=("chamber_temperature_C", "median"),
    temp_mean_C=("temp_mean_C", "median"), temp_min_C=("temp_min_C", "min"),
    temp_max_C=("temp_max_C", "max"),
    pack_start_V=("pack_voltage_V", "first"), pack_end_V=("pack_voltage_V", "last"),
    discharge_start_Ah=("discharge_Ah_cum", "first"),
    discharge_end_Ah=("discharge_Ah_cum", "last"),
    charge_start_Ah=("charge_Ah_cum", "first"), charge_end_Ah=("charge_Ah_cum", "last"),
    integrated_discharge_Ah=("integrated_discharge_step_Ah", "sum"),
    integrated_charge_Ah=("integrated_charge_step_Ah", "sum"),
    c1_valid=("cell1_V", "count"), c2_valid=("cell2_V", "count"),
    c3_valid=("cell3_V", "count"), c4_valid=("cell4_V", "count"),
).reset_index()
event["duration_s"] = (event.end - event.start).dt.total_seconds()
event["discharge_counter_delta_Ah"] = event.discharge_end_Ah - event.discharge_start_Ah
event["charge_counter_delta_Ah"] = event.charge_end_Ah - event.charge_start_Ah
# Current integration is the event-span measure: pulse rows have negative current
# but charge_Ah_cum grows while discharge_Ah_cum stays flat in the source data.
event["discharged_span_Ah"] = event.integrated_discharge_Ah
event["charged_span_Ah"] = event.integrated_charge_Ah
event["event_id"] = event.apply(
    lambda r: f"seg{int(r.segment):02d}|{r.event_class}|{r.start.isoformat()}|{r.end.isoformat()}", axis=1)
event["four_cells_complete"] = event[["c1_valid", "c2_valid", "c3_valid", "c4_valid"]].min(axis=1).eq(event.n_samples)
event["measured_reference_temperature_match"] = "unknown_T_ref"
event["balance_state"] = "unknown_no_field"
event["rest_before_s"] = np.nan

all_group = raw.groupby("event_index", sort=True).agg(
    first=("timestamp", "first"), last=("timestamp", "last"),
    kind=("event_class", "first"), segment=("segment", "first"))
for idx, row in event.iterrows():
    prior = all_group.loc[int(row.event_index) - 1] if int(row.event_index) - 1 in all_group.index else None
    if prior is not None and prior.kind == "rest_or_small" and prior.segment == row.segment:
        event.at[idx, "rest_before_s"] = (prior["last"] - prior["first"]).total_seconds()

event["current_shape_candidate"] = (
    event.event_class.eq("strict_5p1") & (event.n_samples >= 3) &
    event.discharged_span_Ah.ge(min_span) & event.four_cells_complete &
    event.pack_start_V.notna() & event.pack_end_V.notna()
)
event["official_capacity_event_qualified"] = False  # reference T and full-charge state unknown
event["rejection_reason"] = np.select(
    [~event.event_class.eq("strict_5p1"), event.discharged_span_Ah.lt(min_span),
     event.n_samples.lt(3), ~event.four_cells_complete],
    ["current_direction_or_magnitude", "short_Ah_span", "too_few_samples", "cell_voltage_missing"],
    default="reference_T_full_charge_and_path_unknown",
)
event.to_csv(TASK / "outputs/event_eligibility.csv", index=False)

cks = pd.read_csv(ROOT / "data/checkups/evaluation_points.csv", parse_dates=["date"])
rows = []
for ck in cks.itertuples():
    before = event.loc[event.end.le(ck.date)]
    byclass = before.groupby("event_class").size().to_dict()
    candidates = before.loc[before.current_shape_candidate]
    rows.append({
        "checkup": ck.checkup, "cutoff": ck.date.isoformat(),
        "completed_all_events": len(before),
        "completed_strict_5p1_events": int(byclass.get("strict_5p1", 0)),
        "completed_pulse_20A_events": int(byclass.get("pulse_20A", 0)),
        "completed_charge_events": int(byclass.get("charge", 0)),
        "strict_current_shape_candidates_min5Ah": len(candidates),
        "strict_candidate_total_Ah": float(candidates.discharged_span_Ah.sum()),
        "official_capacity_qualified_events": int(before.official_capacity_event_qualified.sum()),
        "reference_temperature_status": "unknown",
        "reference_full_charge_state_status": "unknown",
    })
pd.DataFrame(rows).to_csv(TASK / "outputs/event_coverage_by_ck.csv", index=False)

def first_root_under_shift(shift_V: float) -> float | None:
    ref = pd.read_csv(ROOT / "data/checkups/CK0_reference_discharge.csv.gz",
                      usecols=["voltage_V", "discharged_Ah"])
    v = ref.voltage_V.to_numpy(float) + shift_V
    q = ref.discharged_Ah.to_numpy(float)
    hit = np.flatnonzero(v <= 11.2)
    if not len(hit):
        return None
    j = int(hit[0])
    if j == 0:
        return 0.0
    if v[j - 1] == v[j]:
        return float(q[j])
    return float(q[j - 1] + (11.2 - v[j - 1]) * (q[j] - q[j - 1]) / (v[j] - v[j - 1]))

sensitivity = [{"assumed_pack_shift_mV": m, "first_root_Ah": first_root_under_shift(m / 1000),
                "meaning": "CK0 one-curve assumed voltage-shift sensitivity; not capacity accuracy"}
               for m in [-10, -5, -2, 0, 2, 5, 10]]
pd.DataFrame(sensitivity).to_csv(TASK / "outputs/ck0_pack_root_sensitivity.csv", index=False)

summary = {
    "run_id": OUT.name, "operation_rows": len(raw), "event_rows": len(event),
    "event_counts": event.groupby("event_class").size().to_dict(),
    "current_shape_candidates_all_time": int(event.current_shape_candidate.sum()),
    "strict_shape_candidates_last_ck": int(rows[-1]["strict_current_shape_candidates_min5Ah"]),
    "official_capacity_qualified_events": 0,
    "reason": "CK0 reference temperature and future full-charge preparation state unknown",
    "pulse_counter_audit": {
        "pulse_events": int(event.event_class.eq("pulse_20A").sum()),
        "median_integrated_discharge_Ah": float(event.loc[event.event_class.eq("pulse_20A"), "integrated_discharge_Ah"].median()),
        "median_discharge_counter_delta_Ah": float(event.loc[event.event_class.eq("pulse_20A"), "discharge_counter_delta_Ah"].median()),
        "median_charge_counter_delta_Ah": float(event.loc[event.event_class.eq("pulse_20A"), "charge_counter_delta_Ah"].median()),
        "interpretation": "Negative-current pulse Ah appears in charge counter; use sign-checked current integration for contiguous events and audit counter separately"
    },
    "ck_rows": rows, "voltage_shift_sensitivity": sensitivity,
    "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
}
(OUT / "result.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
(OUT / "COMPLETED").write_text("V1 event inventory complete; inspect result.json and CSVs\n")
print(json.dumps({k: summary[k] for k in ("operation_rows", "event_rows", "event_counts",
                                            "current_shape_candidates_all_time")}, ensure_ascii=False))
