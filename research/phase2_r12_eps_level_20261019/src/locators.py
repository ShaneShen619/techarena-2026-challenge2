"""Round 12 registered step locators (WP1): charge side CL1-CL5 (anchor CC phase), discharge side DL1-DL5 (CK0
C/20 curve), DL1 on the deep programs, the combination rules, the Q_bot trend, the CK0 split and the WP2 gates.

WP2 and WP3 import this module unchanged; any change is a new registered version (notes/DECISIONS.md)."""
import numpy as np
import ahchain

CELLS = ["cell1_V", "cell2_V", "cell3_V", "cell4_V"]

# ---- registered constants -------------------------------------------------------------------------------
GRID_DX_AH = 0.05
GRID_MARGIN_PTS = 3              # extra grid points beyond window +- smoothing half-width (data must cover them)
CC_I_MIN_A = 20.0                # anchor CC phase: samples with I > 20 A
CL_SMOOTH_AH = {"CL1": 2.0, "CL2": 1.0, "CL3": 3.0}
CL_WINDOW_AH = (50.0, 80.0)      # Ah from the charge start (open interval)
MID_WINDOWS_AH = {"4": (5.0, 15.0), "5": (10.0, 20.0)}   # plateaus [s-b, s-a] and [s+a, s+b]; crossing in [s-a, s+a]
MIN_PLATEAU_SAMPLES = 5
MIN_VARIANTS = 4                 # a cell needs >= 4 finite variants
MIN_CELLS = 3                    # a pack value needs >= 3 finite cells
DL_SMOOTH_AH = {"DL1": 2.0, "DL2": 1.0, "DL3": 3.0}
CK0_Q_AH = 100.41
DL_WINDOW_FROM_END_AH = (50.0, 80.0)   # mirrored window: Ah before the end of the C/20 discharge
PROG_BAND_A = (-12.5, -8.0)      # deep programs (package definition)
PROG_RECHARGE_AH = 2.0
PROG_MIN_DEPTH_AH = 50.0
PROG_MIN_BAND_SAMPLES = 50
PROG_DL1_WINDOW_AH = (22.0, 42.0)  # depth below the CV end (package DVDQ_WINDOW_AH)
RELAXED_ANCHORS = (1, 2, 4, 5, 6, 7)
H_ANCHORS = (1, 2, 4, 5, 6, 7)
MIN_H_ANCHORS = 3
G_SB_SIGMA_MAX_AH = 0.25
G_RESID_FLOOR_AH = 0.15
G_A3_MIN_SAME_SIGN = 4
G_B3_WIDTH_MAX_AH = 0.40
R8_GRID_AH = 0.25
R8_CHECK_TOL_AH = 0.25


# ---- primitives ---------------------------------------------------------------------------------------
def _sorted_unique(q, v):
    q = np.asarray(q, float); v = np.asarray(v, float)
    o = np.argsort(q, kind="stable")
    qs, keep = np.unique(q[o], return_index=True)
    return qs, v[o][keep]


def ma_points(width_ah, dx=GRID_DX_AH):
    """Odd number of grid points of a centred moving average spanning width_ah."""
    return 2 * int(round(width_ah / (2.0 * dx))) + 1


def dvdq_peak(q, v, smooth_ah, window, sign, dx=GRID_DX_AH):
    """Location of the maximum of sign * dV/dQ inside the open window (sub-grid, parabolic interpolation).

    Linear interpolation onto a dx grid, centred moving average of ma_points(smooth_ah) points, central
    differences. NaN if the data do not cover the window plus the smoothing half-width plus the margin, if the
    maximum lies on the first or last window point, or if the three points are not a strict maximum."""
    qs, vs = _sorted_unique(q, v)
    if len(qs) < 3:
        return np.nan
    n = ma_points(smooth_ah, dx)
    pad = (n // 2 + GRID_MARGIN_PTS) * dx
    lo, hi = window
    g0 = np.floor((lo - pad) / dx) * dx
    g1 = np.ceil((hi + pad) / dx) * dx
    if qs[0] > g0 or qs[-1] < g1:
        return np.nan
    grid = np.round(np.arange(g0, g1 + dx / 2, dx), 10)
    vg = np.interp(grid, qs, vs)
    sm = np.convolve(vg, np.ones(n) / n, mode="same")
    y = sign * np.gradient(sm, grid)
    win = np.where((grid > lo) & (grid < hi))[0]
    j = win[int(np.argmax(y[win]))]
    if j == win[0] or j == win[-1]:
        return np.nan
    y0, y1, y2 = y[j - 1], y[j], y[j + 1]
    den = y0 - 2.0 * y1 + y2
    if not den < 0:
        return np.nan
    return float(grid[j] + 0.5 * (y0 - y2) / den * dx)


def midpoint_crossing(q, v, s, a, b, direction):
    """First crossing of the plateau midpoint inside [s-a, s+a], linear interpolation between samples.

    Plateau before the step: [s-b, s-a]; after: [s+a, s+b] (median of the raw samples, >= 5 each).
    direction +1: rising voltage (charge); -1: falling voltage (discharge)."""
    if not np.isfinite(s):
        return np.nan
    qs, vs = _sorted_unique(q, v)
    pre = (qs >= s - b) & (qs <= s - a)
    post = (qs >= s + a) & (qs <= s + b)
    if pre.sum() < MIN_PLATEAU_SAMPLES or post.sum() < MIN_PLATEAU_SAMPLES:
        return np.nan
    thr = 0.5 * (np.median(vs[pre]) + np.median(vs[post]))
    x = direction * (vs - thr)
    for k in np.where((qs >= s - a) & (qs <= s + a))[0]:
        if k >= 1 and x[k - 1] < 0 <= x[k]:
            return float(qs[k - 1] + (thr - vs[k - 1]) * (qs[k] - qs[k - 1]) / (vs[k] - vs[k - 1]))
    return np.nan


# ---- variant families -------------------------------------------------------------------------------------
def charge_variants(q, v):
    """CL1-CL5 for one cell; q = Ah from the charge start of the CC samples (I > 20 A)."""
    out = {k: dvdq_peak(q, v, w, CL_WINDOW_AH, +1) for k, w in CL_SMOOTH_AH.items()}
    for k, (a, b) in MID_WINDOWS_AH.items():
        out["CL" + k] = midpoint_crossing(q, v, out["CL1"], a, b, +1)
    return out


def discharge_variants(q, v, q_end=CK0_Q_AH):
    """DL1-DL5 for one cell; q = Ah from the start of the C/20 discharge (D_top)."""
    window = (q_end - DL_WINDOW_FROM_END_AH[1], q_end - DL_WINDOW_FROM_END_AH[0])
    out = {k: dvdq_peak(q, v, w, window, -1) for k, w in DL_SMOOTH_AH.items()}
    for k, (a, b) in MID_WINDOWS_AH.items():
        out["DL" + k] = midpoint_crossing(q, v, out["DL1"], a, b, -1)
    return out


def cell_value(variants):
    x = np.array([v for v in variants.values() if np.isfinite(v)], float)
    return float(np.median(x)) if len(x) >= MIN_VARIANTS else np.nan


def pack_value(cell_values):
    x = np.array([v for v in cell_values if np.isfinite(v)], float)
    return float(np.median(x)) if len(x) >= MIN_CELLS else np.nan


def combine(per_cell):
    """per_cell: list of 4 variant dicts. Returns (combined pack value, cell values, per-locator pack values)."""
    cells = [cell_value(d) for d in per_cell]
    names = list(per_cell[0].keys())
    per_loc = {n: pack_value([d[n] for d in per_cell]) for n in names}
    return pack_value(cells), cells, per_loc


# ---- data preparation ---------------------------------------------------------------------------------
def anchor_charge(seg, t_charge_start, t_cv_end):
    """(q, V, Q_fc) of an anchor: q = Ah from the charge start (package base ah[start-1]) of the CC samples
    (I > 20 A), V their cell voltages (n x 4), Q_fc the package charge q = ah[end] - ah[start-1]."""
    i, ah = ahchain.integrated_ah(seg)
    ts = seg["timestamp"].to_numpy()
    s = int([x for x in np.where(ts == np.datetime64(t_charge_start))[0] if i[x] > 0.5][0])
    e = int([x for x in np.where(ts == np.datetime64(t_cv_end))[0] if i[x] > 0.5][-1])
    base = ah[max(s - 1, 0)]
    sl = slice(s, e + 1)
    cc = i[sl] > CC_I_MIN_A
    return (ah[sl] - base)[cc], seg[CELLS].to_numpy(float)[sl][cc], float(ah[e] - base)


def program_band(seg, e):
    """Deep program after CV end index e (package definition): (depth below the CV end, cell voltages) of the
    band samples, or None if it is not a deep program."""
    i, ah = ahchain.integrated_ah(seg)
    depth = ah[e] - ah[e:]
    peak = np.maximum.accumulate(depth)
    back = np.where(peak - depth > PROG_RECHARGE_AH)[0]
    d = depth[:back[0]] if len(back) else depth
    if d.max() < PROG_MIN_DEPTH_AH:
        return None
    cur = i[e:e + len(d)]
    band = (cur > PROG_BAND_A[0]) & (cur < PROG_BAND_A[1])
    if band.sum() < PROG_MIN_BAND_SAMPLES:
        return None
    return d[band], seg[CELLS].to_numpy(float)[e:e + len(d)][band]


def program_dl1(seg, e):
    """DL1 (sub-grid -dV/dQ maximum, 2 Ah smoothing) on a deep program: (pack value, cell values)."""
    pb = program_band(seg, e)
    if pb is None:
        return np.nan, [np.nan] * len(CELLS)
    d, V = pb
    cells = [dvdq_peak(d, V[:, c], DL_SMOOTH_AH["DL1"], PROG_DL1_WINDOW_AH, -1) for c in range(len(CELLS))]
    return pack_value(cells), cells


# ---- trend, anomalies and WP2 gates ----------------------------------------------------------------------
def theil_sen(x, y):
    """(slope, intercept): median pairwise slope; intercept = median(y - slope x)."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    i, j = np.triu_indices(len(x), 1)
    dx = x[j] - x[i]
    ok = dx != 0
    b = float(np.median((y[j] - y[i])[ok] / dx[ok]))
    return b, float(np.median(y - b * x))


def loo_residuals(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    r = []
    for k in range(len(x)):
        m = np.arange(len(x)) != k
        b, a = theil_sen(x[m], y[m])
        r.append(float(y[k] - (a + b * x[k])))
    return np.array(r)


def resid_threshold(sigma):
    return max(2.0 * sigma, G_RESID_FLOOR_AH)


def g_sb(x, y, labels):
    """G_SB on the relaxed anchors: sigma_LOO <= 0.25 Ah and no |LOO residual| > max(2 sigma_LOO, 0.15 Ah)."""
    r = loo_residuals(x, y)
    sigma = ahchain.sigma_mad(r)
    thr = resid_threshold(sigma)
    bad = [labels[k] for k in range(len(r)) if abs(r[k]) > thr]
    return dict(sigma_LOO=sigma, threshold=thr, loo_residuals=dict(zip(labels, r.tolist())),
                failed_anchors=bad, passed=bool(sigma <= G_SB_SIGMA_MAX_AH and not bad))


def anomaly(x_rel, y_rel, x0, y0):
    """y0 minus the Theil-Sen trend of the relaxed anchors at x0."""
    b, a = theil_sen(x_rel, y_rel)
    return float(y0 - (a + b * x0))


def g_a3(a3_combined, a3_per_locator, sigma):
    """G_a3: |a3| > max(2 sigma_LOO, 0.15 Ah) on the combined value and the same sign on >= 4 of CL1-CL5."""
    thr = resid_threshold(sigma)
    same = sum(1 for v in a3_per_locator.values() if np.isfinite(v) and np.sign(v) == np.sign(a3_combined))
    big = bool(np.isfinite(a3_combined) and abs(a3_combined) > thr)
    return dict(a3_rel=a3_combined, threshold=thr, same_sign=same, identified=bool(big and same >= G_A3_MIN_SAME_SIGN))


def r8_check(cl1_cells, r8_bottom_to_step):
    """CL1 per cell rounded to the 0.25 Ah grid, mean over cells, vs round 8's bottom_to_step (diagnostic)."""
    x = np.array(cl1_cells, float)
    m = float(np.mean(np.round(x / R8_GRID_AH) * R8_GRID_AH))
    return dict(cl1_rounded_mean=m, r8=r8_bottom_to_step, diff=m - r8_bottom_to_step,
                passed=bool(abs(m - r8_bottom_to_step) <= R8_CHECK_TOL_AH))


# ---- CK0 split (B3) -----------------------------------------------------------------------------------
def h_interval(h_medians):
    """h_medians: {('h1'|'h2', 'A3'|'DL1'): median over k}. Point = median of the finite medians."""
    v = np.array([x for x in h_medians.values() if np.isfinite(x)], float)
    if not len(v):
        return dict(point=np.nan, lo=np.nan, hi=np.nan)
    return dict(point=float(np.median(v)), lo=float(v.min()), hi=float(v.max()))


def median_over_k(values):
    v = np.array([x for x in values if np.isfinite(x)], float)
    return float(np.median(v)) if len(v) >= MIN_H_ANCHORS else np.nan


def ck0_split(d_cells, c_cells, q_fc0, h, q_ck0=CK0_Q_AH):
    """B3. d_cells / c_cells: per-cell variant dicts of DL1-DL5 (D_top) and CL1-CL5 (C_bot, anchor 0).

    D_bot = q_ck0 - D_top, C_top = q_fc0 - C_bot (medians over cells). a_0 = -(D_bot - C_bot) - h; its interval
    combines [h_lo, h_hi] with the min/max of (D_bot - C_bot) over the paired variants i = 1..5 and the combined
    value. Top split F^CK_0 - F^A_0 = (D_top - C_top) - h."""
    d_top, _, d_loc = combine(d_cells)
    c_bot, _, c_loc = combine(c_cells)
    dbcb = (q_ck0 - d_top) - c_bot
    dtct = d_top - (q_fc0 - c_bot)
    pair = {f"{i}": (q_ck0 - d_loc[f"DL{i}"]) - c_loc[f"CL{i}"] for i in range(1, 6)}
    vals = np.array([dbcb] + [v for v in pair.values() if np.isfinite(v)], float)
    out = dict(D_top=d_top, D_bot=q_ck0 - d_top, C_bot=c_bot, C_top=q_fc0 - c_bot, eps0=dtct + dbcb,
               Dbot_minus_Cbot=dbcb, Dtop_minus_Ctop=dtct, Dbot_minus_Cbot_by_variant=pair, h=h)
    if not (np.isfinite(dbcb) and np.isfinite(h["lo"]) and np.isfinite(h["hi"])):
        out.update(a0=np.nan, a0_lo=np.nan, a0_hi=np.nan, top_split=np.nan, top_split_lo=np.nan, top_split_hi=np.nan,
                   G_B3=dict(width=np.nan, status="no finite interval"))
        return out
    a0_lo = -vals.max() - h["hi"]
    a0_hi = -vals.min() - h["lo"]
    dt_vals = np.array([dtct] + [(d_loc[f"DL{i}"] - (q_fc0 - c_loc[f"CL{i}"])) for i in range(1, 6)
                                 if np.isfinite(d_loc[f"DL{i}"]) and np.isfinite(c_loc[f"CL{i}"])], float)
    w = a0_hi - a0_lo
    out.update(a0=-dbcb - h["point"], a0_lo=a0_lo, a0_hi=a0_hi,
               top_split=dtct - h["point"], top_split_lo=dt_vals.min() - h["hi"], top_split_hi=dt_vals.max() - h["lo"],
               G_B3=dict(width=w, status="identified" if w <= G_B3_WIDTH_MAX_AH else "not identified"))
    return out


# ---- E2 step jump ------------------------------------------------------------------------------------------
def step_jump(d25, t25, d45, t45, seg45_days, seg45_depths):
    """J_j = d45 - d25 - r_45 * dt; r_45 = Theil-Sen rate of the 45 degC segment's depths (Ah/day)."""
    x = np.asarray(seg45_days, float); y = np.asarray(seg45_depths, float)
    ok = np.isfinite(y)
    r45 = theil_sen(x[ok], y[ok])[0] if ok.sum() >= 2 else np.nan
    dt = (t45 - t25).total_seconds() / 86400.0
    return dict(raw=float(d45 - d25), r45=r45, dt_days=dt, J=float(d45 - d25 - r45 * dt))
