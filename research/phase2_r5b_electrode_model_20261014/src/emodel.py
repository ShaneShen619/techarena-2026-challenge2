"""Round-5B electrode-level model (EXECUTION_PROMPT.md stage 1b). Model and simulation use numpy only.

Per cell and event, with q the charged Ah from the event start:
    theta_n = theta_n0 + q / Q_n        graphite lithiation
    theta_p = theta_p0 - q / Q_p        LFP lithiation
    Q_Li    = theta_n * Q_n + theta_p * Q_p   (constant within an event)
    V       = U_p(theta_p) - U_n(theta_n) + R * I + h * sign(I)
"""
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OCP_DIR = os.path.join(os.path.dirname(HERE), "ocp")
CELLS = ["cell1_V", "cell2_V", "cell3_V", "cell4_V"]


def _load(name):
    a = np.loadtxt(os.path.join(OCP_DIR, name), delimiter=",", skiprows=1)
    return a[:, 0], a[:, 1]


OCP_SETS = {"main": ("lfp_afshar2017.csv", "graphite_chen2020.csv"),
            "alt_graphite": ("lfp_afshar2017.csv", "graphite_ecker2015.csv")}


class OCP:
    def __init__(self, which="main"):
        p, n = OCP_SETS[which]
        self.xp, self.up = _load(p)
        self.xn, self.un = _load(n)
        self.which = which

    def Up(self, th):
        return np.interp(th, self.xp, self.up)

    def Un(self, th):
        return np.interp(th, self.xn, self.un)

    def ocv(self, q, hp):
        """Full-cell OCV at charged Ah q for health/state hp = (Qn, Qp, QLi, thn0)."""
        Qn, Qp, QLi, thn0 = hp
        thp0 = (QLi - thn0 * Qn) / Qp
        return self.Up(thp0 - q / Qp) - self.Un(thn0 + q / Qn)

    def thetas(self, q, hp):
        Qn, Qp, QLi, thn0 = hp
        thp0 = (QLi - thn0 * Qn) / Qp
        return thn0 + q / Qn, thp0 - q / Qp


# -------------------------------------------------------------------- fitting
def bounds_violation(q, hp, ocp):
    tn, tp = ocp.thetas(np.asarray(q, float), hp)
    return float(np.sum(np.clip(-tn, 0, None) + np.clip(tn - 1, 0, None) +
                        np.clip(-tp, 0, None) + np.clip(tp - 1, 0, None)))


def charge_residual(x, q, I, V, ocp, scale_mV=2.0):
    """x = (Qn, Qp, QLi, thn0, R, h); soft-L1 is applied by the optimiser."""
    Qn, Qp, QLi, thn0, R, h = x
    hp = (Qn, Qp, QLi, thn0)
    model = ocp.ocv(q, hp) + R * I + h
    pen = bounds_violation(q[[0, -1]], hp, ocp)
    return np.r_[(model - V) * 1000.0, 1e3 * pen]


def fit_charge(q, I, V, ocp, x0_list=None, fixed=None):
    """Bounded robust least squares (scipy; research only). fixed: dict index -> value."""
    from scipy.optimize import least_squares
    lb = np.array([60.0, 60.0, 50.0, -0.05, -0.02, -0.2])
    ub = np.array([200.0, 200.0, 250.0, 0.6, 0.02, 0.2])
    if x0_list is None:
        x0_list = []
        for thn0 in (0.01, 0.05, 0.12):
            for qn in (105.0, 120.0):
                for qp in (100.0, 110.0):
                    thp0 = 0.97
                    x0_list.append([qn, qp, thn0 * qn + thp0 * qp, thn0, 0.002, 0.0])
    fixed = fixed or {}
    free = [i for i in range(6) if i not in fixed]

    def full(xf):
        x = np.empty(6)
        x[free] = xf
        for i, v in fixed.items():
            x[i] = v
        return x

    best = None
    for x0 in x0_list:
        x0 = np.clip(np.asarray(x0, float), lb + 1e-9, ub - 1e-9)
        r = least_squares(lambda xf: charge_residual(full(xf), q, I, V, ocp), x0[free],
                          bounds=(lb[free], ub[free]), loss="soft_l1", f_scale=2.0,
                          x_scale=np.array([10, 10, 10, 0.02, 0.001, 0.01])[free], max_nfev=4000)
        if best is None or r.cost < best.cost:
            best = r
    x = full(best.x)
    res = charge_residual(x, q, I, V, ocp)[:-1]
    return x, dict(cost=float(best.cost), rms_mV=float(np.sqrt(np.mean(res ** 2))), resid_mV=res)


# ----------------------------------------------------------------- simulation
def start_state(hp_ref, ocp, v_ocv_start, Qn, Qp, QLi):
    """theta_n0 for a new health (Qn, Qp, QLi) such that the full-cell OCV at q=0 equals v_ocv_start."""
    lo, hi = -0.05, 0.6
    def f(t):
        return ocp.ocv(0.0, (Qn, Qp, QLi, t)) - v_ocv_start
    flo, fhi = f(lo), f(hi)
    if flo * fhi > 0:
        return np.nan
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if flo * fm <= 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
    return 0.5 * (lo + hi)


def sim_cccv(hps, Rs, hs, I_cc=20.4, V_pack=14.0, I_end=5.1, dq=0.02, q_max=130.0, ocp=None):
    """Series pack CCCV from the given start states. Returns charged Ah and end q per cell (same q)."""
    q = 0.0
    while q < q_max:
        U = sum(ocp.ocv(q, hp) for hp in hps)
        if U + I_cc * sum(Rs) + sum(hs) >= V_pack:
            break
        q += dq
    else:
        return np.nan
    # CV: I = (V_pack - sum U - sum h) / sum R, integrate until I <= I_end
    for _ in range(200000):
        U = sum(ocp.ocv(q, hp) for hp in hps)
        I = (V_pack - U - sum(hs)) / max(sum(Rs), 1e-6)
        if I <= I_end:
            break
        q += min(dq, I * 10 / 3600.0)
    return q


def sim_discharge_curve(hps_end, etas, I_dis, q_max, dq=0.05, ocp=None):
    """Discharge from end states (q measured as discharged Ah). etas: per-cell voltage drop (V)."""
    d = np.arange(0.0, q_max + dq, dq)
    V = np.stack([ocp.ocv(-d, hp) - eta for hp, eta in zip(hps_end, etas)], axis=1)
    return d, V


def end_state(hp, q_end):
    """Health/state tuple re-based at charged Ah q_end (theta_n0 moved to the end point)."""
    Qn, Qp, QLi, thn0 = hp
    return (Qn, Qp, QLi, thn0 + q_end / Qn)


def valid_range(hp, d, ocp):
    tn, tp = ocp.thetas(-d, hp)
    return (tn >= 0) & (tn <= 1) & (tp >= 0) & (tp <= 1)


def q_c20(hps_end, etas, ocp, c_pack=-0.003, I=5.1, v_cut=11.2, q_max=125.0):
    """First pack 11.2 V root of the 5.1 A discharge; nan if outside the valid theta range."""
    d, V = sim_discharge_curve(hps_end, etas, I, q_max, dq=0.01, ocp=ocp)
    ok = np.all(np.stack([valid_range(hp, d, ocp) for hp in hps_end], axis=1), axis=1)
    pack = V.sum(axis=1) + c_pack
    idx = np.where(pack <= v_cut)[0]
    if not len(idx):
        return np.nan, None
    i = idx[0]
    if not ok[: i + 1].all():
        return np.nan, None
    if i == 0:
        return 0.0, None
    f = (pack[i - 1] - v_cut) / (pack[i - 1] - pack[i])
    root = d[i - 1] + f * (d[i] - d[i - 1])
    limiting = int(np.argmin(V[i]))
    return float(root), limiting


def step_depth(d, v, cfg):
    """Same rule as events._locate (midpoint crossing) applied to a simulated curve."""
    up = (d >= cfg["upper_window_Ah"][0]) & (d <= cfg["upper_window_Ah"][1])
    low = (d >= cfg["lower_window_Ah"][0]) & (d <= cfg["lower_window_Ah"][1])
    if up.sum() < 5 or low.sum() < 5:
        return np.nan
    thr = 0.5 * (np.median(v[up]) + np.median(v[low]))
    idx = np.where((d > cfg["search_from_Ah"]) & (v < thr))[0]
    return float(d[idx[0]]) if len(idx) else np.nan
