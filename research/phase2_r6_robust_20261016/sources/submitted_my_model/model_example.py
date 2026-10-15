"""Reference baseline: partial-charge coulomb counting anchored at the beginning-of-life checkup.

Every ~5 days the profile contains a full CCCV charge to 14.0 V. The baseline integrates the charge
throughput from the moment the pack voltage crosses V_LO (13.4 V) until the end of the CV phase,
and takes the ratio to the same quantity measured right after CK0 (segment 1):

    SOH_est(date) = SOH_CK0 * median(Q_partial of the last 3 full charges before date) / Q_partial(BOL)

with SOH_CK0 = 100.41 Ah / 102 Ah = 98.44 % (SOH is defined against the nominal capacity).

It uses nothing but current and pack voltage, and only CK0 as anchor. Its weakness is physics: the
flat LFP voltage plateau makes a voltage threshold an imprecise SOC anchor, so the estimator is
optimistic. A model that reads the cell voltages, temperature and imbalance should beat it clearly.
Score of this model = 1.0."""
import numpy as np
import pandas as pd

V_LO, V_FULL, I_END, MAX_BACK = 13.4, 13.95, 1.5, 6 * 360


def full_charge_events(op: pd.DataFrame) -> pd.DataFrame:
    if op.empty:
        return pd.DataFrame(columns=["t_end", "Q_partial_Ah", "segment"])
    ts = op["timestamp"].values.astype("datetime64[s]").astype("int64")
    I = op["current_A"].to_numpy(float); U = op["pack_voltage_V"].to_numpy(float); seg = op["segment"].to_numpy()
    dt = np.diff(ts, prepend=ts[0]).astype(float); dt[(dt > 600) | (dt < 0)] = 0.0
    ah = I * dt / 3600.0
    hi = U >= V_FULL
    ends = np.where(hi & (I < I_END) & (np.r_[False, (I[:-1] >= 5.0)] | np.r_[False, hi[:-1]]))[0]
    ends = ends[np.r_[True, np.diff(ends) > 60]] if len(ends) else ends
    rows = []
    for e in ends:
        j = e
        while j > 0 and I[j] > -0.5 and U[j] >= V_LO and seg[j] == seg[e] and e - j < MAX_BACK:
            j -= 1
        if e - j < 30 or U[j] > V_LO + 0.05:
            continue
        rows.append((op["timestamp"].iloc[e], float(ah[j:e + 1].clip(min=0).sum()), int(seg[e])))
    return pd.DataFrame(rows, columns=["t_end", "Q_partial_Ah", "segment"])


class ExampleModel:
    def __init__(self):
        self.q_ref = None
        self.soh0 = 100.0

    def fit(self, dataset):
        ck = dataset.checkups_released.sort_values("date")
        self.soh0 = float(ck["SOH_pct"].iloc[0]) if len(ck) else 100.0
        ev = full_charge_events(dataset.operation)
        first = ev[ev["segment"] == ev["segment"].min()] if len(ev) else ev
        self.q_ref = float(first["Q_partial_Ah"].median()) if len(first) else None

    def estimate_soh(self, dataset, at_date) -> float:
        if self.q_ref is None or dataset.operation.empty:
            return self.soh0
        ev = full_charge_events(dataset.operation)
        ev = ev[ev["t_end"] <= pd.Timestamp(at_date)]
        if ev.empty:
            return self.soh0
        q = float(ev.tail(3)["Q_partial_Ah"].median())
        return float(np.clip(self.soh0 * q / self.q_ref, 0.0, 120.0))
