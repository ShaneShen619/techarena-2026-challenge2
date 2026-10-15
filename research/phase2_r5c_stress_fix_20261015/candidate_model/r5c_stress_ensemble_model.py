"""Round-5C candidate R3_TD_w0.75 (label: exposed-CK1; see FINAL_REPORT.md).

SOH = 100/102 * [0.75 * Q_S + 0.25 * Q_V2], where
* Q_V2 is the V2 anchor + phase-matched graphite-step model (unchanged class);
* Q_S is the round-5C stress model R3_T: two-term law
  L = A_b(1 - exp(-tau/tau_b)) + A_cal tau^0.5 + A_cyc ah (Arrhenius-weighted time and throughput),
  fitted by MAP on consecutive anchor pairs plus one endpoint pair of 45 C program steps for the
  month not yet covered by an anchor (beta = 1, steps within 5 days of the operation restart dropped).
numpy/pandas only; every quantity is computed from the cut dataset passed to estimate_soh.
"""
import os
import sys

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from r5c_anchor_step_v2_model import MyModel as _V2  # noqa: E402
from r5c_events import full_charges, step_programs  # noqa: E402
from r5c_smodel5c import LawFit  # noqa: E402

NOMINAL_AH = 102.0
W_STRESS = 0.75
EPS_EXTRA_AH = 0.4
R3_T = dict(law="two", steps=True, steps_mode="gap_endpoint", beta_mode="one", sigma_s=0.10,
            transient_ref="restart")


class MyModel:
    def __init__(self):
        self.v2 = _V2()
        self.q_ck0 = None

    def fit(self, dataset):
        self.v2.fit(dataset)
        self.q_ck0 = self.v2.q_ck0

    def estimate_capacity_ah(self, dataset, at_date):
        q_v2 = self.v2.estimate_capacity_ah(dataset, at_date)
        op = dataset.operation
        ck = pd.DatetimeIndex(dataset.eval_points.sort_values("date")["date"])
        k = int((ck <= pd.Timestamp(at_date)).sum()) - 1
        if k < 1 or op is None or op.empty:
            return q_v2
        fc = full_charges(op)
        if fc.empty:
            return q_v2
        f45 = fc[fc["setpoint_C"] == 45].sort_values("t_end")
        if f45.empty:
            return q_v2
        eps = self.q_ck0 - float(f45["Q_Ah"].iloc[0]) + EPS_EXTRA_AH
        q_s, _ = LawFit(R3_T).run(op, fc, ck, at_date, eps, steps=step_programs(op))
        return W_STRESS * q_s + (1.0 - W_STRESS) * q_v2

    def estimate_soh(self, dataset, at_date) -> float:
        if self.q_ck0 is None:
            return 100.0
        q = self.estimate_capacity_ah(dataset, at_date)
        return float(np.clip(100.0 * q / NOMINAL_AH, 0.0, 120.0))
