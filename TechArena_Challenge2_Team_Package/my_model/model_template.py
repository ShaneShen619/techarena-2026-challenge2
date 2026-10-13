"""Anchor + graphite-step SOH estimator for the 4 x 102 Ah LFP pack.

Physics
-------
* Anchor. After every monthly checkup the pack is charged from near empty to the
  end of the 14.0 V CV phase. The charged Ah of that first full charge is almost
  the usable capacity at that time. A constant offset maps it to the checkup
  protocol: ``EPS0`` is defined by the post-CK0 charge (CK0 capacity minus that
  charge, 45 degC), and ``EPS_EXTRA_AH`` covers the additional offset assumed for
  the 25 degC post-checkup charges.
* In-month update. Roughly every 5 days the fixed profile discharges ~56 Ah from
  a CV end and crosses the graphite staging step (~33 Ah below full at BOL).
  Loss of lithium inventory shortens the distance between the top of charge and
  that step one-to-one, so the change of the step depth since the anchor is
  added to the anchor capacity (``BETA`` = 1).

Only the data handed in by the framework (already cut at the checkup date) is
used. If no anchor is visible the model returns the CK0 capacity.
"""
import numpy as np

NOMINAL_AH = 102.0
CELLS = ["cell1_V", "cell2_V", "cell3_V", "cell4_V"]

# Offset of a 25 degC post-checkup charge vs the checkup protocol, beyond the
# CK0-defined value (assumption: midpoint of the registered range).
EPS_EXTRA_AH = 0.4
# Capacity change per Ah of step-depth change (pure LLI).
BETA = 1.0

# Full-charge anchor detection.
CHARGE_I_MIN_A = 0.5        # current above this counts as charging
START_V_MAX = 12.3          # pack voltage at charge start (near empty)
CV_V_MIN = 13.95            # charge must reach the CV voltage
END_I_MAX_A = 6.0           # charge must end in CV (tapered current)
ANCHOR_Q_MIN_AH = 50.0      # minimum charged Ah for a full charge

# Graphite step detection on the ~5-day deep discharge.
STEP_BAND_A = (-12.5, -8.0)             # discharge current band used to locate the step
STEP_UPPER_AH = (15.0, 25.0)            # depth window of the upper plateau
STEP_LOWER_AH = (42.0, 50.0)            # depth window of the lower plateau
STEP_SEARCH_FROM_AH = 20.0              # start of the threshold-crossing search
STEP_MIN_DEPTH_AH = 50.0                # discharge must reach this depth
STEP_RECHARGE_AH = 2.0                  # recharge that ends a discharge excursion
STEP_MIN_BAND_SAMPLES = 50
STEP_MIN_PLATEAU_SAMPLES = 5

MAX_DT_S = 600              # larger time steps are recording gaps (not integrated)


def _integrated_ah(seg):
    """Current and cumulative charge (Ah) integrated from ``current_A``.

    The Ah counters book the 20 A pulse as charge, so the current is integrated
    directly. Recording gaps longer than ``MAX_DT_S`` contribute nothing.
    """
    t = seg["elapsed_s"].to_numpy(float)
    i = seg["current_A"].to_numpy(float)
    dt = np.diff(t, prepend=t[0])
    dt[(dt > MAX_DT_S) | (dt <= 0)] = 0.0
    return i, np.cumsum(i * dt / 3600.0)


def _first_full_charge(seg):
    """Post-checkup empty-to-full charge at the start of a segment, or None."""
    i, ah = _integrated_ah(seg)
    u = seg["pack_voltage_V"].to_numpy(float)
    pos = np.where(i > CHARGE_I_MIN_A)[0]
    if not len(pos):
        return None
    start = end = pos[0]
    while end + 1 < len(i) and i[end + 1] > CHARGE_I_MIN_A:
        end += 1
    q = ah[end] - ah[max(start - 1, 0)]
    if (u[start] >= START_V_MAX or u[start:end + 1].max() < CV_V_MIN
            or i[end] >= END_I_MAX_A or q < ANCHOR_Q_MIN_AH):
        return None
    return {
        "t_end": seg["timestamp"].iloc[end],
        "q": q,
        "setpoint": int(seg["chamber_temperature_C"].iloc[start]),
    }


def _locate_step(depth, volts):
    """Depth (Ah) of the first crossing of the mid-plateau voltage, per cell."""
    upper = (depth >= STEP_UPPER_AH[0]) & (depth <= STEP_UPPER_AH[1])
    lower = (depth >= STEP_LOWER_AH[0]) & (depth <= STEP_LOWER_AH[1])
    locs = []
    for c in range(len(CELLS)):
        if (upper.sum() < STEP_MIN_PLATEAU_SAMPLES
                or lower.sum() < STEP_MIN_PLATEAU_SAMPLES):
            locs.append(np.nan)
            continue
        thr = 0.5 * (np.median(volts[upper, c]) + np.median(volts[lower, c]))
        idx = np.where((depth > STEP_SEARCH_FROM_AH) & (volts[:, c] < thr))[0]
        locs.append(float(depth[idx[0]]) if len(idx) else np.nan)
    return locs


def _step_depths(seg):
    """(timestamp of CV end, mean step depth in Ah) for every deep discharge."""
    i, ah = _integrated_ah(seg)
    u = seg["pack_voltage_V"].to_numpy(float)
    v = seg[CELLS].to_numpy(float)
    cv = (u >= CV_V_MIN) & (i > 0) & (i < END_I_MAX_A)
    cv_ends = np.where(cv & ~np.r_[cv[1:], False])[0]
    out = []
    for e in cv_ends:
        depth = ah[e] - ah[e:]
        peak = np.maximum.accumulate(depth)
        back = np.where(peak - depth > STEP_RECHARGE_AH)[0]
        d = depth[:back[0]] if len(back) else depth
        if d.max() < STEP_MIN_DEPTH_AH:
            continue
        cur = i[e:e + len(d)]
        band = (cur > STEP_BAND_A[0]) & (cur < STEP_BAND_A[1])
        if band.sum() < STEP_MIN_BAND_SAMPLES:
            continue
        locs = _locate_step(d[band], v[e:e + len(d)][band])
        if np.isfinite(locs).any():
            out.append((seg["timestamp"].iloc[e], float(np.nanmean(locs))))
    return out


class MyModel:
    """Post-checkup full-charge anchor plus graphite-step displacement."""

    def __init__(self):
        self.q_ck0 = None

    def fit(self, dataset):
        """Store the released CK0 capacity.

        All other inputs are read causally in ``estimate_soh`` from the cut
        dataset, so nothing learned here depends on data after CK0.
        """
        ck = dataset.checkups_released.sort_values("date")
        self.q_ck0 = float(ck["capacity_Ah"].iloc[0])

    def diagnose(self, dataset):
        """Visible anchor charges and step-depth measurements."""
        op = dataset.operation
        charges, steps = [], []
        if op is not None and not op.empty:
            for _, seg in op.groupby("segment", sort=True):
                seg = seg.reset_index(drop=True)
                fc = _first_full_charge(seg)
                if fc:
                    charges.append(fc)
                steps.extend(_step_depths(seg))
        return charges, sorted(steps)

    def estimate_capacity_ah(self, dataset):
        """C/20 capacity estimate (Ah) at the end of the cut dataset."""
        charges, steps = self.diagnose(dataset)
        if not charges:
            return self.q_ck0
        eps0 = next((self.q_ck0 - c["q"] for c in charges
                     if c["setpoint"] == 45), None)
        last = max(charges, key=lambda c: c["t_end"])
        if last["setpoint"] == 45:
            q_anchor = self.q_ck0
        elif eps0 is None:
            q_anchor = last["q"]
        else:
            q_anchor = last["q"] + eps0 + EPS_EXTRA_AH
        after = [s for t, s in steps if t >= last["t_end"]]
        if not after:
            return q_anchor
        return q_anchor + BETA * (after[-1] - after[0])

    def estimate_soh(self, dataset, at_date) -> float:
        """SOH (% of the nominal 102 Ah) at ``at_date`` from the cut dataset."""
        if self.q_ck0 is None:
            return 100.0
        q = self.estimate_capacity_ah(dataset)
        return float(np.clip(100.0 * q / NOMINAL_AH, 0.0, 120.0))
