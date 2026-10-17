"""Anchor + phase-matched graphite-step SOH estimator (V2 + temperature-weighted sqrt(t) gap branch, active model).

Round 10 candidate (research copy, NOT wired): the submitted 5cd305c class with one change, the step value of each
deep discharge is the median over the four cells of each cell's median over six detection variants.

Physics
-------
* Anchor. After every checkup the pack is charged from near empty to the end of
  the 14.0 V CV phase; the charged Ah is nearly the usable capacity. ``EPS0``
  (from the released CK0 capacity and the post-CK0 charge) plus ``EPS_EXTRA_AH``
  maps a 25 degC anchor to the checkup protocol.
* In-month update. The ~5-day deep discharge crosses the graphite staging step.
  Its depth below the CV end shifts with chamber temperature and relaxes after
  each checkup, so only 45 degC steps at the end of a month are compared: the end
  of the current month minus the end of the previous month, both brought to their
  checkup dates with the current 45 degC rate. The difference covers exactly one
  checkup cycle, like the step from the previous anchor to the next one.
* Beta. The step reads only the lithium-inventory part of the fade. Beta is the
  capacity change per Ah of step-to-top change in the charge direction, from the
  visible 25 degC anchors, shrunk towards 1.
* Coverage gap. When the last visible deep discharge ends more than
  ``GAP_DAYS`` before the checkup (CK2 here: segment 3 is missing), the steps
  cannot see the uncovered weeks. The loss since the previous anchor is then
  extrapolated with the square root of time since CK0, fitted to the visible
  anchors (the pack fades like calendar ageing, roughly sqrt(t)). Time is
  Arrhenius-weighted (45 degC-equivalent days, Ea ``FADE_EA_J_MOL``), because
  calendar ageing under changing temperature accumulates in "virtual time"
  (Naumann et al., J. Energy Storage 17 (2018) 153). Unobserved time is
  assigned by the public segment schedule: checkup gaps at ``GAP_TEMP_C``, a
  gap longer than ``MISSING_SEGMENT_DAYS`` holds a missing 45 degC segment up
  to the checkup date inside it, and time after the last visible sample is
  45 degC.
* Robust step value. Each cell's step is located with six detection variants
  (midpoint crossing with the main, a narrower current band, shifted plateau
  windows and an IR-corrected voltage, plus the dV/dQ peak). A cell's value is
  the median over the variants and the program's value the median over the four
  cells, so neither a single detection method nor a single cell that drifts away
  from the others moves the pack value much. Which programs are used is decided
  exactly as before (main detection).
* Fallback. When no phase-matched pair is visible (CK1 and CK3 here), the anchor
  plus the step change since the anchor is used (beta 1), as in V1.

Only the data handed in by the framework (cut at the checkup date) is used; the
checkup dates come from ``dataset.eval_points``.
"""
import numpy as np
import pandas as pd

NOMINAL_AH = 102.0
CELLS = ["cell1_V", "cell2_V", "cell3_V", "cell4_V"]

EPS_EXTRA_AH = 0.4          # 25 degC anchor offset beyond EPS0 (assumption)
BETA0 = 1.0                 # prior beta (pure LLI)
BETA_TAU = 1.0              # prior weight (Ah^2 of step-to-top change)
VALID_DAYS = 10.0           # a month-end step must lie this close to the checkup
MIN_45_STEPS = 3            # 45 degC steps needed for a complete segment / a rate
GAP_DAYS = 10.0             # last deep discharge older than this -> sqrt(t) branch
FADE_EXPONENT = 0.5         # calendar-like fade, loss ~ t ** FADE_EXPONENT
FADE_EA_J_MOL = 20600.0     # calendar-ageing activation energy, LFP (Schimpe et al., JES 165 (2018) A181)
GAS_R = 8.314
REF_TEMP_K = 318.15         # effective time in 45 degC-equivalent days
GAP_TEMP_C = 25.0           # assumed temperature during checkup gaps
MISSING_SEGMENT_DAYS = 10.0  # a longer gap between segments holds a missing 45 degC segment
MISSING_SEGMENT_TEMP_C = 45.0
TAIL_TEMP_C = 45.0          # after the last visible sample (alternation schedule)

CHARGE_I_MIN_A = 0.5
START_V_MAX = 12.3
CV_V_MIN = 13.95
END_I_MAX_A = 6.0
ANCHOR_Q_MIN_AH = 50.0
CC_I_MIN_A = 20.0           # CC part of the anchor charge used for the charge-side step
CHARGE_STEP_SMOOTH_AH = 2.0
CHARGE_STEP_WINDOW_AH = (50.0, 80.0)

STEP_BAND_A = (-12.5, -8.0)
STEP_UPPER_AH = (15.0, 25.0)
STEP_LOWER_AH = (42.0, 50.0)
STEP_SEARCH_FROM_AH = 20.0
STEP_MIN_DEPTH_AH = 50.0
STEP_RECHARGE_AH = 2.0
STEP_MIN_BAND_SAMPLES = 50
STEP_MIN_PLATEAU_SAMPLES = 5
# detection variants for the robust step value: (current band, upper window, lower window, method, IR correction)
STEP_VARIANTS = (
    ((-12.5, -8.0), (15.0, 25.0), (42.0, 50.0), "midpoint", False),
    ((-11.5, -9.0), (15.0, 25.0), (42.0, 50.0), "midpoint", False),
    ((-12.5, -8.0), (12.0, 22.0), (39.0, 47.0), "midpoint", False),
    ((-12.5, -8.0), (18.0, 28.0), (45.0, 53.0), "midpoint", False),
    ((-12.5, -8.0), (15.0, 25.0), (42.0, 50.0), "dvdq", False),
    ((-12.5, -8.0), (15.0, 25.0), (42.0, 50.0), "midpoint", True),
)
STEP_MIN_VARIANTS = 4       # a cell needs this many finite variants
DVDQ_GRID_AH = (18.0, 46.0, 0.25)
DVDQ_SMOOTH_POINTS = 8
DVDQ_WINDOW_AH = (22.0, 42.0)
PULSE_I_A = -15.0           # the 20 A pulse that follows each CV end (apparent resistance for the IR variant)

MAX_DT_S = 600


def _integrated_ah(seg):
    t = seg["elapsed_s"].to_numpy(float)
    i = seg["current_A"].to_numpy(float)
    dt = np.diff(t, prepend=t[0])
    dt[(dt > MAX_DT_S) | (dt <= 0)] = 0.0
    return i, np.cumsum(i * dt / 3600.0)


def _charge_step_to_top(seg, i, ah, start, end, q):
    """Ah from the charge-direction graphite step to the top of the anchor charge."""
    base = ah[max(start - 1, 0)]
    qs = ah[start:end + 1] - base
    cc = i[start:end + 1] > CC_I_MIN_A
    qq, keep = np.unique(qs[cc], return_index=True)
    grid = np.arange(0.0, qq.max(), 0.25)
    k = max(1, int(round(CHARGE_STEP_SMOOTH_AH / 0.25)))
    win = (grid > CHARGE_STEP_WINDOW_AH[0]) & (grid < CHARGE_STEP_WINDOW_AH[1])
    tops = []
    for c in CELLS:
        v = seg[c].to_numpy(float)[start:end + 1][cc][keep]
        vs = np.convolve(np.interp(grid, qq, v), np.ones(k) / k, mode="same")
        slope = np.gradient(vs, grid)
        tops.append(q - float(grid[win][np.argmax(slope[win])]))
    return float(np.mean(tops))


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
        "t_start": seg["timestamp"].iloc[start],
        "t_end": seg["timestamp"].iloc[end],
        "q": q,
        "setpoint": int(seg["chamber_temperature_C"].iloc[start]),
        "top": _charge_step_to_top(seg, i, ah, start, end, q),
    }


def _locate_step(depth, volts, upper_ah=STEP_UPPER_AH, lower_ah=STEP_LOWER_AH):
    upper = (depth >= upper_ah[0]) & (depth <= upper_ah[1])
    lower = (depth >= lower_ah[0]) & (depth <= lower_ah[1])
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


def _locate_dvdq(depth, volts):
    """Depth of the steepest voltage drop (dV/dQ peak) per cell, or NaN."""
    order = np.argsort(depth, kind="stable")
    dd, keep = np.unique(depth[order], return_index=True)
    grid = np.arange(*DVDQ_GRID_AH)
    if dd.min() > grid[0] or dd.max() < grid[-1]:
        return [np.nan] * len(CELLS)
    win = (grid >= DVDQ_WINDOW_AH[0]) & (grid <= DVDQ_WINDOW_AH[1])
    locs = []
    for c in range(len(CELLS)):
        vg = np.interp(grid, dd, volts[order, c][keep])
        vs = np.convolve(vg, np.ones(DVDQ_SMOOTH_POINTS) / DVDQ_SMOOTH_POINTS, mode="same")
        locs.append(float(grid[win][np.argmax(-np.gradient(vs, grid)[win])]))
    return locs


def _pulse_resistance(seg, i, e):
    """Per-cell apparent resistance at the start of the pulse after CV end e (NaN if not visible)."""
    idx = np.where(i[e + 1:] < PULSE_I_A)[0]
    if not len(idx):
        return np.full(len(CELLS), np.nan)
    p = e + 1 + idx[0]
    if p - 1 <= e or p + 2 >= len(i):
        return np.full(len(CELLS), np.nan)
    v = seg[CELLS].to_numpy(float)
    return (v[p - 1] - v[p + 2]) / abs(i[p + 2])


def _robust_step(seg, i, v, e, d):
    """Median over cells of each cell's median over the detection variants (NaN if no cell has enough variants)."""
    cur = i[e:e + len(d)]
    vv = v[e:e + len(d)]
    per_variant = []
    for band_a, upper, lower, method, ir in STEP_VARIANTS:
        band = (cur > band_a[0]) & (cur < band_a[1])
        if band.sum() < STEP_MIN_BAND_SAMPLES:
            per_variant.append([np.nan] * len(CELLS))
            continue
        volts = vv + np.abs(cur)[:, None] * _pulse_resistance(seg, i, e)[None, :] if ir else vv
        if method == "dvdq":
            per_variant.append(_locate_dvdq(d[band], volts[band]))
        else:
            per_variant.append(_locate_step(d[band], volts[band], upper, lower))
    arr = np.array(per_variant, float)
    cells = []
    for c in range(len(CELLS)):
        x = arr[:, c][np.isfinite(arr[:, c])]
        cells.append(float(np.median(x)) if len(x) >= STEP_MIN_VARIANTS else np.nan)
    cells = np.array(cells)
    return float(np.median(cells[np.isfinite(cells)])) if np.isfinite(cells).any() else np.nan


def _step_depths(seg):
    """(CV-end time, chamber set point, robust step depth, end time) for every deep discharge; which discharges are
    kept is decided by the main detection, as in the submitted model."""
    i, ah = _integrated_ah(seg)
    u = seg["pack_voltage_V"].to_numpy(float)
    v = seg[CELLS].to_numpy(float)
    cv = (u >= CV_V_MIN) & (i > 0) & (i < END_I_MAX_A)
    out = []
    for e in np.where(cv & ~np.r_[cv[1:], False])[0]:
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
            out.append((seg["timestamp"].iloc[e],
                        int(seg["chamber_temperature_C"].iloc[e]),
                        _robust_step(seg, i, v, e, d),
                        seg["timestamp"].iloc[e + len(d) - 1]))
    return out


def _theil_sen(x, y):
    i, j = np.triu_indices(len(x), 1)
    dx = x[j] - x[i]
    ok = dx != 0
    return float(np.median((y[j] - y[i])[ok] / dx[ok])) if ok.any() else 0.0


def _effective_days(op, ck, dates):
    """45 degC-equivalent days from ck[0] to each date (hourly grid, Arrhenius weights)."""
    end = max(dates)
    grid = pd.date_range(ck[0], end, freq="h", inclusive="left")
    temp = np.full(len(grid), GAP_TEMP_C)
    if op is not None and not op.empty:
        seg = op.groupby("segment").agg(t0=("timestamp", "min"), t1=("timestamp", "max"),
                                        sp=("chamber_temperature_C", "first")).sort_values("t0")
        temp[grid > seg["t1"].max()] = TAIL_TEMP_C
        ends, starts = seg["t1"].to_numpy()[:-1], seg["t0"].to_numpy()[1:]
        for a, b in zip(ends, starts):
            if (b - a) / np.timedelta64(1, "D") > MISSING_SEGMENT_DAYS:
                inside = ck[(ck > a) & (ck <= b)]
                stop = inside[0] if len(inside) else b
                temp[(grid >= a) & (grid < stop)] = MISSING_SEGMENT_TEMP_C
        for _, r in seg.iterrows():
            temp[(grid >= r["t0"]) & (grid <= r["t1"])] = float(r["sp"])
    else:
        temp[:] = TAIL_TEMP_C
    w = np.exp(FADE_EA_J_MOL / GAS_R * (1.0 / REF_TEMP_K - 1.0 / (temp + 273.15)))
    cum = np.concatenate([[0.0], np.cumsum(w / 24.0)])
    return [float(cum[len(pd.date_range(ck[0], d, freq="h", inclusive="left"))]) for d in dates]


class MyModel:
    """Post-checkup full-charge anchor plus phase-matched graphite-step update."""

    def __init__(self):
        self.q_ck0 = None

    def fit(self, dataset):
        """Store the released CK0 capacity; everything else is read causally."""
        ck = dataset.checkups_released.sort_values("date")
        self.q_ck0 = float(ck["capacity_Ah"].iloc[0])

    # ----- event extraction -------------------------------------------------
    @staticmethod
    def diagnose(dataset):
        op = dataset.operation
        charges, steps = [], []
        if op is not None and not op.empty:
            for _, seg in op.groupby("segment", sort=True):
                seg = seg.reset_index(drop=True)
                fc = _first_full_charge(seg)
                if fc:
                    charges.append(fc)
                steps.extend(_step_depths(seg))
        return sorted(charges, key=lambda c: c["t_end"]), sorted(steps)

    # ----- helpers ----------------------------------------------------------
    @staticmethod
    def _anchors(charges, ck):
        anc = {}
        for c in charges:
            j = int((ck < c["t_end"]).sum()) - 1
            if j >= 0 and j not in anc:
                anc[j] = c
        return anc

    @staticmethod
    def _end45(steps, anc, ck, m):
        if m not in anc:
            return None
        t0 = anc[m]["t_end"]
        t1 = anc[m + 1]["t_start"] if m + 1 in anc else None
        s = [(t, d) for t, sp, d, _ in steps
             if sp == 45 and t >= t0 and (t1 is None or t < t1)]
        if not s:
            return None
        t_last, e = s[-1]
        days = np.array([(t - s[0][0]).total_seconds() / 86400.0 for t, _ in s])
        rate = _theil_sen(days, np.array([d for _, d in s])) if len(s) >= MIN_45_STEPS else 0.0
        return {"E": e, "d": (ck[m + 1] - t_last).total_seconds() / 86400.0,
                "n": len(s), "r": rate}

    def _phase_diff(self, steps, anc, ck, k):
        if k < 2:
            return None
        cur, prev = self._end45(steps, anc, ck, k - 1), self._end45(steps, anc, ck, k - 2)
        if cur is None or prev is None or prev["n"] < MIN_45_STEPS or prev["d"] > VALID_DAYS:
            return None
        if not (cur["d"] <= VALID_DAYS or cur["n"] >= MIN_45_STEPS):
            return None
        r = cur["r"] if cur["n"] >= MIN_45_STEPS else 0.0
        return cur["E"] - prev["E"] + r * (cur["d"] - prev["d"])

    @staticmethod
    def _beta(anc, k):
        js = [j for j in range(1, k) if j in anc and anc[j]["setpoint"] == 25]
        if len(js) < 2:
            return BETA0
        j1 = js[0]
        x = np.array([anc[j]["top"] - anc[j1]["top"] for j in js[1:]])
        q = np.array([anc[j]["q"] - anc[j1]["q"] for j in js[1:]])
        s = float((x ** 2).sum())
        b = float((x * q).sum() / s) if s > 0 else BETA0
        return (BETA_TAU * BETA0 + s * b) / (BETA_TAU + s)

    def _sqrt_extrapolation(self, anc, ck, k, eps, op):
        """Anchor k-1 plus the sqrt(t_eff) loss to CK_k, fitted to visible anchors 1..k-1."""
        js = [j for j in range(1, k) if j in anc]
        te = _effective_days(op, ck, [ck[j] for j in js] + [ck[k - 1], ck[k]])
        x = np.array(te[:len(js)]) ** FADE_EXPONENT
        loss = np.array([self.q_ck0 - (anc[j]["q"] + eps) for j in js])
        a = float((x * loss).sum() / (x ** 2).sum())
        return (anc[k - 1]["q"] + eps
                - a * (te[-1] ** FADE_EXPONENT - te[-2] ** FADE_EXPONENT))

    # ----- estimate ---------------------------------------------------------
    def estimate_capacity_ah(self, dataset, at_date):
        charges, steps = self.diagnose(dataset)
        if not charges:
            return self.q_ck0
        eps0 = next((self.q_ck0 - c["q"] for c in charges if c["setpoint"] == 45), None)
        ck = pd.DatetimeIndex(dataset.eval_points.sort_values("date")["date"])
        k = int((ck < pd.Timestamp(at_date)).sum())
        anc = self._anchors(charges, ck)

        if eps0 is not None and k >= 2 and (k - 1) in anc and steps:
            gap = (ck[k] - max(s[3] for s in steps)).total_seconds() / 86400.0
            if gap > GAP_DAYS:
                return self._sqrt_extrapolation(anc, ck, k, eps0 + EPS_EXTRA_AH, dataset.operation)

        last = charges[-1]
        if last["setpoint"] == 45:
            q_anchor = self.q_ck0
        elif eps0 is None:
            q_anchor = last["q"]
        else:
            q_anchor = last["q"] + eps0 + EPS_EXTRA_AH

        if (eps0 is not None and (k - 1) in anc and anc[k - 1] is last
                and last["setpoint"] == 25):
            x = self._phase_diff(steps, anc, ck, k)
            if x is not None:
                return q_anchor + self._beta(anc, k) * x

        after = [d for t, _, d, _ in steps if t >= last["t_end"]]
        if not after:
            return q_anchor
        return q_anchor + (after[-1] - after[0])

    def estimate_soh(self, dataset, at_date) -> float:
        """SOH (% of the nominal 102 Ah) at ``at_date`` from the cut dataset."""
        if self.q_ck0 is None:
            return 100.0
        q = self.estimate_capacity_ah(dataset, at_date)
        return float(np.clip(100.0 * q / NOMINAL_AH, 0.0, 120.0))
