"""Official Challenge 2 interface with explicit P1-to-4S domain gate.

Full-depth, full-voltage events use the externally trained P1 ridge map.
Most official shallow events are outside that map's support; they use the
same-cell matched-temperature diagnostic fallback.  CK1–CK7 are unlabeled.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

MODULE_DIR = Path(__file__).resolve().parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from official_fallback import OfficialFallback  # noqa: E402
from online_multi_window import OnlineMultiWindow  # noqa: E402


class ActiveModel:
    def __init__(self) -> None:
        self.q0_Ah = 100.41
        self.anchor_time = None
        self.primary: OnlineMultiWindow | None = None
        self.fallback: OfficialFallback | None = None
        self.last_diagnostics = {}

    def fit(self, dataset) -> None:
        self.q0_Ah = float(dataset.bol_capacity_Ah)
        released = dataset.checkups_released.sort_values("date")
        self.anchor_time = pd.Timestamp(released.date.iloc[0])
        self.primary = OnlineMultiWindow.from_artifact(
            MODULE_DIR / "ridge_p1_pretrained.json", MODULE_DIR / "windows.json",
            self.q0_Ah, self.anchor_time)
        self.fallback = OfficialFallback(self.q0_Ah, self.anchor_time)
        # `fit` stores neither full operation nor unreleased checkup data.

    def estimate_soh(self, dataset, at_date) -> float:
        if self.primary is None or self.fallback is None:
            raise RuntimeError("fit must precede estimate_soh")
        cutoff = pd.Timestamp(at_date)
        if self.anchor_time is not None and cutoff <= self.anchor_time:
            self.last_diagnostics = {"mode": "released_CK0_anchor", "q0_Ah": self.q0_Ah}
            return float(100.*self.q0_Ah/102.)
        estimate = self.primary.estimate(dataset.operation, cutoff)
        if estimate is not None:
            self.last_diagnostics = self.primary.last_diagnostics
            return float(estimate)
        primary_diagnostic = dict(self.primary.last_diagnostics)
        if "voltage_V" in dataset.operation:
            # A single-cell P1 input with insufficient windows has no
            # validated alternative for the proxy target; carry the anchor.
            self.last_diagnostics = {"mode": "single_cell_anchor_fallback",
                                     "primary_rejection": primary_diagnostic}
            return float(100.*self.q0_Ah/102.)
        estimate = self.fallback.estimate(dataset.operation, cutoff)
        self.last_diagnostics = {**self.fallback.last_diagnostics,
                                 "primary_rejection": primary_diagnostic,
                                 "official_accuracy_verified": False}
        return float(estimate)
