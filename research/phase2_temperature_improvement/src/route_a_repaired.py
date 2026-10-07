"""M2 reference/temperature repair of the earlier unsupervised Route A.

This is a development candidate, not an official-pack-ready final model.
It never reads a target discharge or future operation rows.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
import pandas as pd

from event_core import Event, extract_charge_events, partial_ah


@dataclass(frozen=True)
class Reference:
    q_window_Ah: float
    end: pd.Timestamp
    temp_C: float
    current_A: float
    base_capacity_ratio: float
    calibration: str
    event_id: str


def stable_cc_prefix(event: Event, minimum_fraction: float = .85) -> tuple[Event | None, str]:
    """Keep the initial constant-current plateau and reject a CV-only span."""
    if len(event.times_s) < 10 or event.duration_s < 60.:
        return None, "too_short"
    dt = np.diff(event.times_s).astype(float)
    dq = np.diff(event.q_ah)
    if len(dt) < 9 or np.any(dt <= 0) or np.any(dq < -1e-7):
        return None, "invalid_integral"
    current = dq * 3600. / dt
    first = current[:min(8, len(current))]
    plateau = float(np.median(first))
    if not np.isfinite(plateau) or plateau < 5.:
        return None, "no_cc_plateau"
    stable = (current >= minimum_fraction * plateau) & (current <= plateau / minimum_fraction)
    if not stable[0]:
        return None, "unstable_cc_start"
    rejected = np.flatnonzero(~stable)
    # current[j] corresponds to the interval ending at point j+1; keep j+1
    # as the final CC point when the following interval starts CV.
    stop = int(rejected[0] + 1) if len(rejected) else len(event.times_s)
    if stop < 10:
        return None, "cc_too_short"
    keep = slice(0, stop)
    cc = replace(event, end=pd.Timestamp(event.start) + pd.Timedelta(seconds=int(event.times_s[stop-1]-event.times_s[0])),
                 duration_s=float(event.times_s[stop-1]-event.times_s[0]),
                 ah=float(event.q_ah[stop-1]-event.q_ah[0]),
                 times_s=event.times_s[keep].copy(),
                 q_ah=(event.q_ah[keep]-event.q_ah[0]).copy(),
                 voltages=event.voltages[keep].copy(),
                 counter_q_ah=None)
    if cc.ah < 15.:
        return None, "cc_low_Ah"
    cv = float(np.std(current[:stop-1]) / max(np.mean(current[:stop-1]), 1e-9))
    if cv > .08:
        return None, "cc_high_variation"
    return cc, "pass"


class RouteARepaired:
    windows = ((3.33, 3.40), (3.36, 3.43))

    def __init__(self, *, max_temp_diff_C: float = 5., max_current_rel: float = .2,
                 cc_only: bool = True, require_quality_for_reference: bool = True,
                 true_pair_temperature: bool = True, carry_forward: bool = True,
                 disagreement_gate: bool = False):
        self.max_temp_diff_C = float(max_temp_diff_C)
        self.max_current_rel = float(max_current_rel)
        self.cc_only = bool(cc_only)
        self.require_quality_for_reference = bool(require_quality_for_reference)
        self.true_pair_temperature = bool(true_pair_temperature)
        self.carry_forward = bool(carry_forward)
        self.disagreement_gate = bool(disagreement_gate)
        self.q0_Ah = 100.41
        self.anchor_time = None
        self.last_diagnostics = {}
        self.evidence_events = []

    def fit(self, dataset) -> None:
        self.q0_Ah = float(dataset.bol_capacity_Ah)
        self.anchor_time = pd.Timestamp(dataset.anchor_discharge_start) if hasattr(dataset, "anchor_discharge_start") else None

    @staticmethod
    def _id(event: Event) -> str:
        return f"{event.segment}|{pd.Timestamp(event.start).isoformat()}|{pd.Timestamp(event.end).isoformat()}"

    def _match(self, refs: list[Reference], temp_C: float, current_A: float) -> Reference | None:
        possible = []
        for ref in refs:
            if self.true_pair_temperature:
                temp_diff = abs(temp_C-ref.temp_C)
                okay_temp = temp_diff <= self.max_temp_diff_C
            else:
                same_bin = int(round(temp_C/20.)) == int(round(ref.temp_C/20.))
                okay_temp = same_bin and abs(temp_C-20.*round(temp_C/20.)) <= 7.
                temp_diff = abs(temp_C-ref.temp_C)
            okay_current = abs(current_A-ref.current_A) <= self.max_current_rel*max(ref.current_A, 1.)
            if okay_temp and okay_current:
                possible.append((temp_diff, -ref.end.value, ref))
        return min(possible, key=lambda item: (item[0], item[1]))[2] if possible else None

    def estimate_soh(self, dataset, at_date) -> float:
        cutoff = pd.Timestamp(at_date)
        operation = dataset.operation
        events = extract_charge_events(operation, until=cutoff,
                                       voltage_cols=("voltage_V",), time_col="absolute_time",
                                       temp_col="temperature_C", segment_col="cycle_number",
                                       counter_col=None)
        refs: dict[tuple[int, str], list[Reference]] = {}
        updates = []
        log = []
        rejection_counts: dict[str, int] = {}
        state_ratio = 1.
        for raw in events:
            event_id = self._id(raw)
            cc, quality = stable_cc_prefix(raw)
            if raw.ah < 15.:
                quality = "total_low_Ah"
            if not np.isfinite(raw.median_temp):
                quality = "missing_temperature"
            if quality != "pass":
                rejection_counts[quality] = rejection_counts.get(quality, 0)+1
            if self.require_quality_for_reference and quality != "pass":
                log.append({"event_id": event_id, "event_end": raw.end, "quality_pass": False,
                            "reference_only": False, "used_for_update": False,
                            "reason": quality, "matched_windows": 0})
                continue
            selected = cc if self.cc_only and cc is not None else raw
            if selected is None:
                continue
            depth = "deep" if raw.ah >= 50. else "shallow"
            matched = []
            registered = 0
            for index, (lo, hi) in enumerate(self.windows):
                q = partial_ah(selected, 0, lo, hi)
                if q is None or q < 1.:
                    continue
                key = (index, depth)
                available = refs.setdefault(key, [])
                ref = self._match(available, raw.median_temp, raw.median_current)
                if ref is None:
                    if not available and self.anchor_time is not None and raw.end <= self.anchor_time + pd.Timedelta(days=14):
                        calibration = "near_BOL_anchor_assumption"
                        base_ratio = 1.
                    elif updates:
                        calibration = "propagated_previous_estimate"
                        base_ratio = state_ratio
                    else:
                        calibration = "uncalibrated_late_reference"
                        base_ratio = float("nan")
                    available.append(Reference(float(q), pd.Timestamp(raw.end), float(raw.median_temp),
                                               float(raw.median_current), base_ratio, calibration, event_id))
                    registered += 1
                    continue
                if not np.isfinite(ref.base_capacity_ratio):
                    continue
                matched.append((index, float(ref.base_capacity_ratio * q/ref.q_window_Ah),
                                float(raw.median_temp-ref.temp_C), ref.event_id))
            if matched:
                ratios = np.asarray([x[1] for x in matched], float)
                if self.disagreement_gate and len(ratios)>1 and np.ptp(ratios)>.15:
                    log.append({"event_id": event_id, "event_end": raw.end, "quality_pass": quality=="pass",
                                "reference_only": False, "used_for_update": False,
                                "reason": "window_disagreement", "matched_windows": len(matched)})
                    continue
                ratio = float(np.median(ratios))
                updates.append({"end": pd.Timestamp(raw.end), "ratio": ratio, "event_id": event_id,
                                "matched": matched})
                state_ratio = float(np.median([u["ratio"] for u in updates[-5:]]))
                log.append({"event_id": event_id, "event_end": raw.end, "quality_pass": quality=="pass",
                            "reference_only": False, "used_for_update": True,
                            "reason": "matched_reference", "matched_windows": len(matched),
                            "ratio": ratio, "state_ratio": state_ratio})
            else:
                log.append({"event_id": event_id, "event_end": raw.end, "quality_pass": quality=="pass",
                            "reference_only": bool(registered), "used_for_update": False,
                            "reason": "registered_reference" if registered else "no_usable_window",
                            "matched_windows": 0})
        # Keep the last scientifically supported state when no recent event
        # exists. The old model silently rebounded to q0 in that situation.
        recent = [u for u in updates if (cutoff-u["end"]).total_seconds() <= 30*86400]
        if not recent and not self.carry_forward:
            state_ratio = 1.
        q_pred = self.q0_Ah*state_ratio
        self.evidence_events = log
        self.last_diagnostics = {"qualified_charge_runs": len(events),
                                 "reference_keys": sum(len(x) for x in refs.values()),
                                 "updates": len(updates),
                                 "recent_updates": len(recent),
                                 "last_used_event_ids": [u["event_id"] for u in updates[-5:]],
                                 "fallback": not bool(updates),
                                 "carried_forward": bool(updates and not recent),
                                 "capacity_Ah_raw": q_pred,
                                 "rejections": rejection_counts,
                                 "event_log": log}
        return float(100.*q_pred/102.)
