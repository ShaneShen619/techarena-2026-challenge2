"""Conservative no-update reference; no claim of accurate aging prediction."""
from __future__ import annotations


class ActiveModel:
    def __init__(self):
        self.q0_Ah = None
        self.last_diagnostics = {}

    def fit(self, dataset):
        self.q0_Ah = float(dataset.bol_capacity_Ah)
        self.last_diagnostics = {"mode": "CK0_hold", "q0_Ah": self.q0_Ah}

    def estimate_soh(self, dataset, at_date):
        if self.q0_Ah is None:
            raise RuntimeError("fit required")
        self.last_diagnostics = {"mode": "CK0_hold", "q0_Ah": self.q0_Ah,
                                 "capacity_accuracy_verified": False}
        return 100.0 * self.q0_Ah / 102.0
