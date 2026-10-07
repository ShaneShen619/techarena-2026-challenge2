"""Causal partial-charge feature audit on the frozen P1 panel.

The complete raw file is parsed once per physical cell.  An event is usable
for a target only when the separate M2 prefix replay logged that exact event
before that target; this prevents an event completed by later rows being used.
No discharge capacity or target label is read in this script.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

TASK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK / "src"))
sys.path.insert(0, str(TASK / "scripts"))
from event_core import extract_charge_events, partial_ah  # noqa: E402
from route_a_repaired import stable_cc_prefix  # noqa: E402
from run_m2_repaired import load_charging  # noqa: E402

WIDTHS = (.04, .07, .10)
LOWS = np.round(np.arange(3.20, 3.501, .03), 3)
WINDOWS = [(float(lo), float(lo + width)) for width in WIDTHS for lo in LOWS
           if lo + width <= 3.500001]


def event_id(cell: str, ev) -> str:
    return f"{cell}|{ev.segment}|{pd.Timestamp(ev.start).isoformat()}|{pd.Timestamp(ev.end).isoformat()}"


def main() -> None:
    panel_path = TASK / "outputs/panel_main.csv"
    manifest = json.loads((TASK / "outputs/panel_manifest.json").read_text())
    if hashlib.sha256(panel_path.read_bytes()).hexdigest() != manifest["panel_sha256"]:
        raise RuntimeError("frozen panel changed")
    panel = pd.read_csv(panel_path, parse_dates=["target_discharge_start", "anchor_discharge_start"])
    logs = pd.read_csv(TASK / "runs/M2_A_bugfix_180_v1/evidence_events.csv",
                       parse_dates=["event_end"])
    out_dir = TASK / "runs/M4_feature_audit_v1"
    out_dir.mkdir(parents=True, exist_ok=True)
    event_rows = []
    feature_rows = []
    for cell in sorted(panel.cell_id.unique()):
        raw = load_charging(cell)
        events = extract_charge_events(raw, time_col="absolute_time", voltage_cols=("voltage_V",),
                                       temp_col="temperature_C", segment_col="cycle_number", counter_col=None)
        # A whitelist of events explicitly seen by the earlier independent prefix replay.
        cell_logs = logs.loc[logs.cell_id.eq(cell)]
        visible_by_target = {}
        seen_ids: set[str] = set()
        ordered_targets = panel.loc[panel.cell_id.eq(cell)].sort_values("target_ordinal")
        for target in ordered_targets.itertuples(index=False):
            current = cell_logs.loc[cell_logs.target_cycle.eq(int(target.target_cycle))]
            seen_ids.update(str(eid) for eid in current.event_id)
            visible_by_target[int(target.target_cycle)] = seen_ids.copy()
        visible_any = set(cell_logs.event_id)
        for ev in events:
            eid = event_id(cell, ev)
            if eid not in visible_any:
                continue
            cc, status = stable_cc_prefix(ev)
            if status != "pass" or cc is None or not np.isfinite(ev.median_temp):
                continue
            row = {"cell_id": cell, "event_id": eid, "event_end": pd.Timestamp(ev.end),
                   "cycle": ev.segment, "temp_C": ev.median_temp, "current_A": ev.median_current,
                   "total_Ah": ev.ah, "cc_Ah": cc.ah}
            for i, (lo, hi) in enumerate(WINDOWS):
                val = partial_ah(cc, 0, lo, hi)
                row[f"w{i:02d}"] = float(val) if val is not None else np.nan
            event_rows.append(row)
        cell_ev = pd.DataFrame([x for x in event_rows if x["cell_id"] == cell]).sort_values("event_end")
        cell_ev.to_csv(out_dir / f"events_{cell}.csv", index=False)
        targets = panel.loc[panel.cell_id.eq(cell)].sort_values("target_ordinal")
        for target in targets.itertuples(index=False):
            cutoff = pd.Timestamp(target.target_discharge_start)
            allowed = visible_by_target.get(int(target.target_cycle), set())
            ev = cell_ev.loc[cell_ev.event_id.isin(allowed) & cell_ev.event_end.lt(cutoff)].copy()
            ev = ev.sort_values("event_end")
            if len(ev) == 0:
                raise AssertionError(f"no strictly visible quality event: {cell} {target.target_cycle}")
            # Early reference is fixed once from the first ten qualified events.
            # It is used only when those events had already completed before target.
            initial = ev.head(min(10, len(ev)))
            recent = ev.tail(min(5, len(ev)))
            rec = {"cell_id": cell, "target_ordinal": int(target.target_ordinal),
                   "target_cycle": int(target.target_cycle), "target_discharge_start": cutoff.isoformat(),
                   "latest_event_id": str(recent.event_id.iloc[-1]),
                   "recent_event_ids": "|#|".join(recent.event_id.astype(str)),
                   "input_end": pd.Timestamp(recent.event_end.iloc[-1]).isoformat(),
                   "n_quality_events": len(ev), "n_recent_events": len(recent),
                   "event_age_days": (cutoff-recent.event_end.iloc[-1]).total_seconds()/86400,
                   "temp_C": float(recent.temp_C.median()),
                   "initial_temp_C": float(initial.temp_C.median()),
                   "delta_temp_C": float(recent.temp_C.median()-initial.temp_C.median()),
                   "current_A": float(recent.current_A.median()),
                   "delta_current_rel": float(recent.current_A.median()/initial.current_A.median()-1),
                   "recent_cc_Ah": float(recent.cc_Ah.median()),
                   "initial_cc_Ah": float(initial.cc_Ah.median())}
            for i in range(len(WINDOWS)):
                name = f"w{i:02d}"
                early_values = initial[name].dropna()
                now_values = recent[name].dropna()
                early = float(early_values.median()) if len(early_values) else np.nan
                now = float(now_values.median()) if len(now_values) else np.nan
                rec[f"{name}_logratio"] = float(np.log(now/early)) if np.isfinite(now) and np.isfinite(early) and now > 0 and early > 0 else np.nan
                rec[f"{name}_now"] = now
                rec[f"{name}_initial"] = early
            feature_rows.append(rec)
        print(cell, "qualified_events", len(cell_ev), "targets", len(targets), flush=True)
        pd.DataFrame(feature_rows).to_csv(out_dir / "features.partial.csv", index=False)
        del raw, events
    pd.DataFrame(feature_rows).to_csv(out_dir / "features.csv", index=False)
    pd.DataFrame(event_rows).to_csv(out_dir / "events.csv", index=False)
    (out_dir / "config.json").write_text(json.dumps({
        "panel_sha256": manifest["panel_sha256"], "event_source": "M2 strict prefix replay",
        "windows": WINDOWS, "reference_events": "first up to ten strictly visible quality events",
        "recent_events": "last up to five strictly visible quality events",
        "target_labels_read": False,
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
