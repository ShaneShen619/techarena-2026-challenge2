"""Anchor + graphite-step SOH estimator (research candidate, not the active model).

Physics: in LFP/graphite, lithium-inventory loss shortens the charge between the
top of charge and the graphite staging step (~33 Ah below full at BOL) one-to-one.

* Anchor: the latest visible charge that starts near empty after a checkup and ends
  in CV at 14.0 V measures nearly the full usable capacity. A constant offset EPS
  maps it to the checkup protocol (0 for the post-CK0 charge, which defines it).
* Update: every ~5 days the profile discharges ~56 Ah from a CV end and crosses the
  step. Its depth (Ah below CV end) is tracked per cell; the change since the
  anchor is added to the anchor capacity (beta = 1).

Only data passed in ``dataset`` (already cut at ``at_date`` by the framework) is used.
"""
import numpy as np
import pandas as pd

NOMINAL_AH = 102.0
CELLS = ["cell1_V", "cell2_V", "cell3_V", "cell4_V"]
EPS_EXTRA_AH = 0.4      # 25 C charge vs checkup offset beyond the CK0-defined value (assumption)
BETA = 1.0              # capacity change per Ah of step-depth change (LLI)
BAND_A = (-12.5, -8.0)  # discharge current band used to locate the step
UPPER_AH, LOWER_AH, SEARCH_FROM_AH = (15.0, 25.0), (42.0, 50.0), 20.0


def _integrated_ah(g):
    t = g["elapsed_s"].to_numpy(float)
    i = g["current_A"].to_numpy(float)
    dt = np.diff(t, prepend=t[0])
    dt[(dt > 600) | (dt <= 0)] = 0.0
    return i, np.cumsum(i * dt / 3600.0)


def _first_full_charge(g):
    i, ah = _integrated_ah(g)
    u = g["pack_voltage_V"].to_numpy(float)
    pos = np.where(i > 0.5)[0]
    if not len(pos):
        return None
    s = pos[0]
    e = s
    while e + 1 < len(i) and i[e + 1] > 0.5:
        e += 1
    q = ah[e] - ah[max(s - 1, 0)]
    if u[s] >= 12.3 or u[s:e + 1].max() < 13.95 or i[e] >= 6.0 or q < 50:
        return None
    return dict(t_end=g["timestamp"].iloc[e], q=q, setpoint=int(g["chamber_temperature_C"].iloc[s]))


def _step_depths(g):
    i, ah = _integrated_ah(g)
    u = g["pack_voltage_V"].to_numpy(float)
    v = g[CELLS].to_numpy(float)
    hi = (u >= 13.95) & (i > 0) & (i < 6.0)
    out = []
    for e in np.where(hi & ~np.r_[hi[1:], False])[0]:
        depth = ah[e] - ah[e:]
        peak = np.maximum.accumulate(depth)
        back = np.where(peak - depth > 2.0)[0]
        d = depth[:back[0]] if len(back) else depth
        if d.max() < 50.0:
            continue
        cur = i[e:e + len(d)]
        band = (cur > BAND_A[0]) & (cur < BAND_A[1])
        if band.sum() < 50:
            continue
        db, vb = d[band], v[e:e + len(d)][band]
        locs = []
        for c in range(4):
            up = (db >= UPPER_AH[0]) & (db <= UPPER_AH[1])
            lo = (db >= LOWER_AH[0]) & (db <= LOWER_AH[1])
            if up.sum() < 5 or lo.sum() < 5:
                locs.append(np.nan)
                continue
            thr = 0.5 * (np.median(vb[up, c]) + np.median(vb[lo, c]))
            idx = np.where((db > SEARCH_FROM_AH) & (vb[:, c] < thr))[0]
            locs.append(float(db[idx[0]]) if len(idx) else np.nan)
        if np.isfinite(locs).any():
            out.append((g["timestamp"].iloc[e], float(np.nanmean(locs))))
    return out


class AnchorStepModel:
    def __init__(self):
        self.q_ck0 = None

    def fit(self, dataset):
        # Only the released CK0 capacity is stored; all other inputs are read causally
        # inside estimate_soh from the cut dataset.
        ck = dataset.checkups_released.sort_values("date")
        self.q_ck0 = float(ck["capacity_Ah"].iloc[0])

    def diagnose(self, dataset):
        op = dataset.operation
        charges, steps = [], []
        if op is not None and not op.empty:
            for _, g in op.groupby("segment", sort=True):
                g = g.reset_index(drop=True)
                fc = _first_full_charge(g)
                if fc:
                    charges.append(fc)
                steps.extend(_step_depths(g))
        return charges, sorted(steps)

    def estimate_capacity_ah(self, dataset):
        charges, steps = self.diagnose(dataset)
        if not charges:
            return self.q_ck0
        eps0 = None
        for c in charges:
            if c["setpoint"] == 45:
                eps0 = self.q_ck0 - c["q"]
                break
        last = max(charges, key=lambda c: c["t_end"])
        if last["setpoint"] == 45 or eps0 is None:
            q_anchor = self.q_ck0 if last["setpoint"] == 45 else last["q"]
        else:
            q_anchor = last["q"] + eps0 + EPS_EXTRA_AH
        after = [s for t, s in steps if t >= last["t_end"]]
        if not after:
            return q_anchor
        return q_anchor + BETA * (after[-1] - after[0])

    def estimate_soh(self, dataset, at_date):
        if self.q_ck0 is None:
            return 100.0
        q = self.estimate_capacity_ah(dataset)
        return float(np.clip(100.0 * q / NOMINAL_AH, 0.0, 120.0))
