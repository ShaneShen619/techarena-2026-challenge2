"""Explicit out-of-domain 4S fallback for shallow official charge events.

P1 supervised deep-charge regression lacks the windows needed for most
official shallow events.  This conservative same-cell, same-depth, actual
temperature/current ratio is an unlabelled diagnostic fallback, not a
validated C/20 pack-capacity estimator.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from event_core import extract_charge_events, partial_ah
from route_a_repaired import stable_cc_prefix


@dataclass(frozen=True)
class Ref:
    ah: float
    end: pd.Timestamp
    temp_C: float
    current_A: float
    base_ratio: float
    source: str


class OfficialFallback:
    windows = ((3.38, 3.42), (3.41, 3.45))

    def __init__(self, q0_Ah: float = 100.41, anchor_time=None) -> None:
        self.q0_Ah = float(q0_Ah)
        self.anchor_time = pd.Timestamp(anchor_time) if anchor_time is not None else None
        self.last_diagnostics = {}

    @staticmethod
    def _matched(refs: list[Ref], temperature: float, current: float) -> Ref | None:
        candidates = [r for r in refs if abs(temperature-r.temp_C) <= 5. and
                      abs(current-r.current_A) <= .2*max(r.current_A, 1.)]
        return min(candidates, key=lambda r: (abs(temperature-r.temp_C), -r.end.value)) if candidates else None

    def estimate(self, operation: pd.DataFrame, at_date) -> float:
        cutoff = pd.Timestamp(at_date)
        if self.anchor_time is not None and cutoff <= self.anchor_time:
            self.last_diagnostics = {"mode": "released_CK0_anchor", "updates": 0}
            return 100.*self.q0_Ah/102.
        events = extract_charge_events(operation, until=cutoff-pd.Timedelta(nanoseconds=1),
                                       time_col="timestamp", current_col="current_A",
                                       voltage_cols=("cell1_V", "cell2_V", "cell3_V", "cell4_V"),
                                       temp_col="temp_mean_C", segment_col="segment",
                                       counter_col="charge_Ah_cum")
        refs: dict[tuple[int, int, str], list[Ref]] = {}
        update_history: list[list[tuple[pd.Timestamp, float, str]]] = [[] for _ in range(4)]
        logs = []
        for event in events:
            eid = f"{event.segment}|{event.start.isoformat()}|{event.end.isoformat()}"
            cc, status = stable_cc_prefix(event)
            if event.ah < 15.:
                status = "total_low_Ah"
            if not np.isfinite(event.median_temp):
                status = "missing_temperature"
            if status != "pass" or cc is None:
                logs.append({"event_id": eid, "event_end": event.end.isoformat(),
                             "quality": status, "used_cells": [], "reference_cells": []})
                continue
            depth = "deep" if event.ah >= 50. else "shallow"
            used_cells = []
            reference_cells = []
            for ci in range(4):
                estimates = []
                registered = False
                for wi, (lo, hi) in enumerate(self.windows):
                    q = partial_ah(cc, ci, lo, hi)
                    if q is None or q < .5:
                        continue
                    key = (ci, wi, depth)
                    available = refs.setdefault(key, [])
                    ref = self._matched(available, event.median_temp, event.median_current)
                    if ref is None:
                        if self.anchor_time is not None and event.end <= self.anchor_time+pd.Timedelta(days=14):
                            base, source = 1., "near_BOL_anchor"
                        elif update_history[ci]:
                            base, source = float(np.median([x[1] for x in update_history[ci][-5:]])), "propagated_prior_estimate"
                        else:
                            base, source = float("nan"), "uncalibrated_late_stratum"
                        available.append(Ref(float(q), pd.Timestamp(event.end), float(event.median_temp),
                                             float(event.median_current), base, source))
                        registered = True
                        continue
                    if np.isfinite(ref.base_ratio):
                        estimates.append(float(ref.base_ratio*q/ref.ah))
                if estimates:
                    ratio = float(np.median(estimates))
                    update_history[ci].append((event.end, ratio, eid))
                    used_cells.append(ci+1)
                elif registered:
                    reference_cells.append(ci+1)
            logs.append({"event_id": eid, "event_end": event.end.isoformat(),
                         "quality": status, "depth": depth,
                         "temp_C": event.median_temp, "current_A": event.median_current,
                         "used_cells": used_cells, "reference_cells": reference_cells})
        cell_ratios = [float(np.median([x[1] for x in history[-5:]])) if history else 1.
                       for history in update_history]
        # Lowest cell ratio is a conservative series-group heuristic. The
        # official 11.2 V pack cutoff and SOC imbalance can move true C/20
        # capacity away from this proxy; no hidden labels are used to tune it.
        ratio = float(min(cell_ratios))
        estimate = float(100.*self.q0_Ah*ratio/102.)
        self.last_diagnostics = {
            "mode": "out_of_domain_shallow_charge_ratio",
            "qualified_events": sum(log["quality"] == "pass" for log in logs),
            "updates": [len(x) for x in update_history],
            "cell_ratios": cell_ratios,
            "pack_rule": "min_cell_ratio_unvalidated_11p2V_cutoff",
            "used_event_ids": [[x[2] for x in hist[-5:]] for hist in update_history],
            "event_log": logs,
            "q0_Ah": self.q0_Ah, "estimate_soh_pp": estimate,
        }
        return estimate
