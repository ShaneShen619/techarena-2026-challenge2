"""Publish the audited official diagnostic-pulse event catalog."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

TASK = Path(__file__).resolve().parents[1]
source = TASK / "runs/M1_certification_v2/event_certification.csv"
events = pd.read_csv(source)
assert len(events) == 41 and events.accepted.all()

catalog = pd.DataFrame({
    "event_type": "official_standard_discharge_pulse",
    "source_file": events.file,
    "event_start": events.start,
    "event_end": events.end,
    "quality_status": events.accepted.map({True: "certified", False: "rejected"}),
    "reject_reason": events.reject_reasons.fillna(""),
    "temperature_C": events.chamber_C,
    "temperature_span_C": events.temp_span_C,
    "duration_s": events.duration_s,
    "discharged_Ah": events.q_integral_Ah,
    "prior_charge_s": events.prior_charge_s,
    "prior_charge_max_pack_V": events.prior_charge_max_pack_V,
    "pre_rest_s": events.pre_rest_s,
    "post_rest_s": events.post_rest_s,
    "before_CK7": events.before_CK7,
    "effective_modalities": "pack_voltage; four_cell_voltages; current; chamber_temperature; integrated_Ah; pre_post_rest",
    "capacity_label_available": False,
    "source_audit": "runs/M1_certification_v2/event_certification.csv",
})
catalog.to_csv(TASK / "outputs/event_catalog.csv", index=False)
print(json.dumps({"catalog_events": len(catalog), "certified": int(catalog.quality_status.eq("certified").sum()),
                  "before_CK7": int(catalog.before_CK7.sum()), "source": str(source.relative_to(TASK))}))
