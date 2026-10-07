"""Old Route A with exactly one reference-order repair for ablation.

The candidate differs from the copied prior implementation only by checking
the original temperature-bin gate before an event can become a reference.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from .event_core import extract_charge_events, partial_ah


class RouteA:
    windows = ((3.33, 3.40), (3.36, 3.43))

    def __init__(self, single_cell: bool = False, *, use_pack: bool = False,
                 match_conditions: bool = True, use_counter: bool = False,
                 robust: bool = True, split_depth: bool = True,
                 disagreement_gate: bool = False):
        self.q0 = 100.41
        self.nominal = 102.0
        self.single_cell = single_cell
        self.use_pack = use_pack
        self.match_conditions = match_conditions
        self.use_counter = use_counter
        self.robust = robust
        self.split_depth = split_depth
        self.disagreement_gate = disagreement_gate
        self.last_diagnostics = {}

    def fit(self, dataset):
        self.q0 = float(dataset.bol_capacity_Ah)
        # No operation-derived state is stored: fit(full) == fit(prefix).

    def estimate_soh(self, dataset, at_date) -> float:
        cutoff = pd.Timestamp(at_date)
        options = dict(voltage_cols=("voltage_V",), time_col="absolute_time",
                       temp_col="temperature_C", segment_col="cycle_number",
                       counter_col=None) if self.single_cell else (
                       dict(voltage_cols=("pack_voltage_V",)) if self.use_pack else {})
        events = extract_charge_events(dataset.operation, until=cutoff, **options)
        references: dict[tuple[int, int, int, str], tuple[float, pd.Timestamp, float]] = {}
        ratios = []
        recent = []
        for ev in events:
            if not np.isfinite(ev.median_temp) or ev.ah < 15.0:
                continue
            # The first post-CK0 charge replenishes ~100 Ah after a deep
            # discharge, whereas maintenance charges replenish ~21 Ah. Their
            # hysteresis trajectories are not exchangeable even within the
            # same temperature and current stratum.
            depth = ("deep" if ev.ah >= 50.0 else "shallow") if self.split_depth else "any"
            for cell in range(ev.voltages.shape[1]):
                windows = ((13.4,13.95),) if self.use_pack and not self.single_cell else self.windows
                for wi, (lo, hi) in enumerate(windows):
                    q = partial_ah(ev, cell, lo, hi, self.use_counter)
                    if q is None or q < 1.0:
                        continue
                    temp_bin = int(round(ev.median_temp / 20.0)) if self.match_conditions else 0
                    key = (cell, wi, temp_bin, depth)
                    # The prior code installed an out-of-bin event as a
                    # reference and only checked this gate on later events.
                    # Keep every other rule intact to isolate that bug.
                    if self.match_conditions and abs(ev.median_temp - 20.0 * temp_bin) > 7.0:
                        continue
                    ref = references.get(key)
                    if ref is None:
                        references[key] = (q, ev.end, ev.median_current)
                        continue
                    ref_q, ref_date, ref_i = ref
                    if self.match_conditions and abs(ev.median_current - ref_i) > 0.2 * max(ref_i, 1.0):
                        continue
                    if (cutoff - ev.end).total_seconds() > 30 * 86400:
                        continue
                    if (ev.end - ref_date).total_seconds() < 0:
                        continue
                    recent.append((ev.end, cell, wi, q / ref_q))
        if recent:
            # Event is the independent unit; first robustly pool cells/windows
            # within an event, then take the five most recent complete events.
            pooled = {}
            for end, _, _, ratio in recent:
                pooled.setdefault(end, []).append(ratio)
            latest = sorted(pooled)[-5:]
            for t in latest:
                r = pooled[t]
                if self.disagreement_gate and len(r)>1 and max(r)-min(r)>0.15:
                    continue
                ratios.append(float(np.median(r) if self.robust else np.mean(r)))
        ratio = float((np.median if self.robust else np.mean)(ratios)) if ratios else 1.0
        q_raw = self.q0 * ratio
        self.last_diagnostics = {
            "qualified_charge_runs": len(events), "reference_keys": len(references),
            "matched_window_observations": len(recent), "updates": len(ratios),
            "fallback": not bool(ratios), "capacity_Ah_raw": q_raw,
            "last_event": str(max((x[0] for x in recent), default="")),
            "note": "later temperature-stratum references are uncalibrated" if references else "no reference",
        }
        return float(100.0 * q_raw / self.nominal)
