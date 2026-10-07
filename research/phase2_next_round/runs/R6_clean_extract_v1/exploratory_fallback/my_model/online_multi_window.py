"""Online feature adapter for the frozen P1-trained multi-window model.

It refuses to extrapolate the supervised ridge map when any required
full-voltage window is absent.  Four-series series-group aggregation remains
an explicit heuristic because no released CK1–CK7 C/20 labels can validate it.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from event_core import extract_charge_events, partial_ah
from multi_window_ridge import RidgeFeatureModel, add_derived_features
from route_a_repaired import stable_cc_prefix


class OnlineMultiWindow:
    def __init__(self, model: RidgeFeatureModel, windows: list[list[float]],
                 q0_Ah: float, anchor_time=None) -> None:
        self.model = model
        self.windows = windows
        self.q0_Ah = float(q0_Ah)
        self.anchor_time = pd.Timestamp(anchor_time) if anchor_time is not None else None
        self.last_diagnostics = {}

    @classmethod
    def from_artifact(cls, model_path: Path, config_path: Path,
                      q0_Ah: float, anchor_time=None) -> "OnlineMultiWindow":
        artifact = json.loads(Path(model_path).read_text())
        windows = json.loads(Path(config_path).read_text())["windows"]
        return cls(RidgeFeatureModel(**artifact["model"]), windows, q0_Ah, anchor_time)

    def estimate(self, operation: pd.DataFrame, at_date) -> float | None:
        cutoff = pd.Timestamp(at_date)
        if self.anchor_time is not None and cutoff <= self.anchor_time:
            self.last_diagnostics = {"mode": "released_CK0_anchor"}
            return float(100.*self.q0_Ah/102.)
        is_p1 = "voltage_V" in operation.columns
        if is_p1:
            args = dict(time_col="absolute_time", voltage_cols=("voltage_V",),
                        temp_col="temperature_C", segment_col="cycle_number", counter_col=None)
        else:
            args = dict(time_col="timestamp", voltage_cols=("cell1_V", "cell2_V", "cell3_V", "cell4_V"),
                        temp_col="temp_mean_C", segment_col="segment", counter_col="charge_Ah_cum")
        events = extract_charge_events(operation, until=cutoff-pd.Timedelta(nanoseconds=1), **args)
        qualified = []
        for ev in events:
            if self.anchor_time is not None and ev.end < self.anchor_time:
                continue
            cc, status = stable_cc_prefix(ev)
            if ev.ah < 15.:
                status = "total_low_Ah"
            if not np.isfinite(ev.median_temp):
                status = "missing_temperature"
            if status != "pass" or cc is None:
                continue
            windows_by_cell = [[partial_ah(cc, ci, lo, hi) for lo, hi in self.windows]
                               for ci in range(ev.voltages.shape[1])]
            qualified.append((ev, cc, windows_by_cell))
        if len(qualified) < 5:
            self.last_diagnostics = {"mode": "insufficient_qualified_events", "n_events": len(qualified)}
            return None
        # Reference and recent event sets match the frozen P1 feature rule.
        initial = qualified[:10]
        recent = qualified[-5:]
        if not is_p1:
            initial_deep = np.mean([ev.ah >= 50. for ev, _, _ in initial])
            recent_deep = np.mean([ev.ah >= 50. for ev, _, _ in recent])
            initial_temp = float(np.median([ev.median_temp for ev, _, _ in initial]))
            recent_temp = float(np.median([ev.median_temp for ev, _, _ in recent]))
            if initial_deep < .8 or recent_deep < .8 or abs(recent_temp-initial_temp) > 5.:
                self.last_diagnostics = {"mode": "charge_depth_or_temperature_domain_shift",
                                         "n_events": len(qualified),
                                         "initial_deep_fraction": float(initial_deep),
                                         "recent_deep_fraction": float(recent_deep),
                                         "early_recent_temp_gap_C": recent_temp-initial_temp}
                return None
        age_efc = sum(ev.ah for ev, _, _ in qualified)/102.
        rows = []
        missing = []
        for ci in range(len(qualified[0][2])):
            row = {"anchor_soh_pp": round(100.*self.q0_Ah/102., 3),
                   "qualified_charge_efc": age_efc,
                   "event_age_days": (cutoff-recent[-1][0].end).total_seconds()/86400,
                   "temp_C": float(np.median([ev.median_temp for ev, _, _ in recent])),
                   "initial_temp_C": float(np.median([ev.median_temp for ev, _, _ in initial])),
                   "current_A": float(np.median([ev.median_current for ev, _, _ in recent])),
                   "delta_current_rel": float(np.median([ev.median_current for ev, _, _ in recent])/
                                              np.median([ev.median_current for ev, _, _ in initial])-1),
                   "recent_cc_Ah": float(np.median([cc.ah for _, cc, _ in recent])),
                   "initial_cc_Ah": float(np.median([cc.ah for _, cc, _ in initial]))}
            row["delta_temp_C"] = row["temp_C"]-row["initial_temp_C"]
            for wi in range(len(self.windows)):
                early = [item[2][ci][wi] for item in initial if item[2][ci][wi] is not None]
                now = [item[2][ci][wi] for item in recent if item[2][ci][wi] is not None]
                if not early or not now:
                    missing.append((ci+1, wi))
                    row[f"w{wi:02d}_logratio"] = np.nan
                else:
                    e = float(np.median(early)); n = float(np.median(now))
                    row[f"w{wi:02d}_logratio"] = float(np.log(n/e)) if e > 0 and n > 0 else np.nan
            rows.append(row)
        if missing:
            self.last_diagnostics = {"mode": "missing_full_voltage_windows", "n_events": len(qualified),
                                     "missing_window_count": len(missing),
                                     "missing_by_cell": {str(ci): sum(x[0] == ci for x in missing)
                                                         for ci in range(1, len(rows)+1)},
                                     "qualified_charge_efc": age_efc,
                                     "latest_event_end": recent[-1][0].end.isoformat()}
            return None
        feature_frame = add_derived_features(pd.DataFrame(rows), age_col="qualified_charge_efc")
        pred = self.model.predict(feature_frame)
        if not np.isfinite(pred).all():
            raise ValueError("nonfinite in-domain ridge prediction")
        estimate = float(np.min(pred)) if len(pred) > 1 else float(pred[0])
        self.last_diagnostics = {"mode": "full_window_ridge",
                                 "n_events": len(qualified), "qualified_charge_efc": age_efc,
                                 "cell_predictions_pp": pred.tolist(),
                                 "pack_rule": "min_cell_prediction_unvalidated_11p2V_cutoff" if len(pred)>1 else "single_cell",
                                 "latest_event_end": recent[-1][0].end.isoformat(),
                                 "estimate_soh_pp": estimate}
        return estimate
