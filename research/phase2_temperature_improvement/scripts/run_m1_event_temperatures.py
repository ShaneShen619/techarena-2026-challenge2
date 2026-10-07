"""Compare event-wide versus voltage-window temperature on known A failures.

This is a diagnostic on previously seen points. It reads no target capacity
labels and never feeds held-out lifetime mean temperature to the estimator.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
OLD = ROOT / "research/phase2_validation"
sys.path.insert(0, str(TASK / "src"))
sys.path.insert(0, str(OLD / "src"))
from event_core import extract_charge_events  # noqa: E402
from event_temperature import summarize_temperature  # noqa: E402
from thermal_surface import fit_thermal_surface  # noqa: E402


def main() -> None:
    columns = ["cell_id", "stage", "target_cycle", "window", "event_end", "event_cycle",
               "reference_end", "reference_cycle", "event_temp_C", "reference_temp_C", "ratio"]
    old = pd.read_csv(OLD / "outputs/a_failure_review/selected_event_references.csv", usecols=columns)
    anchors = pd.read_csv(TASK / "outputs/thermal_anchors.csv")
    out = []
    for cell_id, group in old.groupby("cell_id", sort=True):
        local_anchor = anchors.loc[anchors.cell_id.eq(cell_id)].iloc[0]
        train = anchors.loc[anchors.cell_id.ne(cell_id) & anchors.anchor_usable]
        fit = fit_thermal_surface(train[["T_nom", "c_rate", "T_eff"]].to_dict("records"))
        cols = ["absolute_time", "cycle_number", "step_type", "voltage_V", "current_A", "temperature_C"]
        source = ROOT / "dataset original" / cell_id
        raw = pd.concat([pd.read_csv(p, usecols=cols, parse_dates=["absolute_time"])
                         for p in sorted(source.glob("*.csv"))], ignore_index=True)
        charging = raw.loc[~raw.step_type.eq("cc_discharge")].copy()
        bound = max(pd.to_datetime(group.event_end).max(), pd.to_datetime(group.reference_end).max())
        events = extract_charge_events(charging, until=bound + pd.Timedelta(seconds=60),
                                       time_col="absolute_time", voltage_cols=("voltage_V",),
                                       temp_col="temperature_C", segment_col="cycle_number", counter_col=None)
        by_id = {(int(ev.segment), pd.Timestamp(ev.end)): ev for ev in events}
        required = (
            set(zip(group.event_cycle.astype(int), pd.to_datetime(group.event_end)))
            | set(zip(group.reference_cycle.astype(int), pd.to_datetime(group.reference_end)))
        )
        absent = required - set(by_id)
        if absent:
            raise AssertionError(f"old selected event not reconstructed: {cell_id}, {list(absent)[:3]}")
        summary_cache = {}
        for row in group.itertuples(index=False):
            lo, hi = map(float, row.window.split("-"))
            pair = []
            for kind, cycle, stamp in (("event", row.event_cycle, row.event_end),
                                       ("reference", row.reference_cycle, row.reference_end)):
                key = (int(cycle), pd.Timestamp(stamp), lo, hi)
                if key not in summary_cache:
                    event = by_id[(key[0], key[1])]
                    block = charging.loc[
                        charging.cycle_number.eq(event.segment)
                        & charging.absolute_time.ge(event.start)
                        & charging.absolute_time.le(event.end)
                        & charging.current_A.ge(5.)
                        & charging.voltage_V.ge(lo)
                        & charging.voltage_V.le(hi),
                        ["absolute_time", "temperature_C"],
                    ]
                    summary_cache[key] = summarize_temperature(
                        block.absolute_time, block.temperature_C,
                        cutoff=event.end, nominal_C=float(local_anchor.T_nom),
                        c_rate=float(local_anchor.c_rate), fallback=fit,
                    )
                pair.append(summary_cache[key])
            ev_temp, ref_temp = pair
            out.append({
                "cell_id": cell_id, "stage": row.stage, "target_cycle": int(row.target_cycle),
                "window": row.window, "event_end": row.event_end, "reference_end": row.reference_end,
                "old_event_median_C": row.event_temp_C, "old_reference_median_C": row.reference_temp_C,
                "old_paired_gap_C": float(row.event_temp_C-row.reference_temp_C),
                "window_event_used_C": ev_temp.used_C, "window_reference_used_C": ref_temp.used_C,
                "window_paired_gap_C": ev_temp.used_C-ref_temp.used_C,
                "event_temperature_source": ev_temp.source, "reference_temperature_source": ref_temp.source,
                "event_valid_fraction": ev_temp.valid_fraction, "reference_valid_fraction": ref_temp.valid_fraction,
                "event_mad_C": ev_temp.mad_C, "reference_mad_C": ref_temp.mad_C,
                "event_slope_C_per_hour": ev_temp.slope_C_per_hour,
                "reference_slope_C_per_hour": ref_temp.slope_C_per_hour,
                "event_flags": "|".join(ev_temp.flags), "reference_flags": "|".join(ref_temp.flags),
                "old_window_ratio": row.ratio,
                "fold_fit_training_cells": "|".join(train.cell_id),
            })
        print(cell_id, "diagnostic_pairs", len(group), "unique_event_window_summaries", len(summary_cache), flush=True)
        del raw, charging
    result = pd.DataFrame(out)
    result.to_csv(TASK / "outputs/event_temperature_diagnostics.csv", index=False)
    print("pairs", len(result), "max_abs_window_gap_C", result.window_paired_gap_C.abs().max(),
          "measured_event_fraction", result.event_temperature_source.eq("measured").mean())


if __name__ == "__main__":
    main()
