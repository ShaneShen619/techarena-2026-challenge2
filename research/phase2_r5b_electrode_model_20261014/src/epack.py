"""Pack-level simulations on fitted electrode states (stage_1/protocol.json, simulation_conventions)."""
import numpy as np

from emodel import end_state, q_c20, sim_cccv, start_state, step_depth

MAIN_STEP = {"method": "midpoint_crossing", "current_band_A": (-12.5, -8.0),
             "upper_window_Ah": (15.0, 25.0), "lower_window_Ah": (42.0, 50.0),
             "search_from_Ah": 20.0, "ir_correction": False}
I_PROG = 10.782
C_PACK = -0.003


def hp_of(x):
    return (x[0], x[1], x[2], x[3])


def restart(x, v_start, ocp):
    """Same health as x, start state re-solved so that OCV(q=0) = v_start."""
    t = start_state(None, ocp, v_start, x[0], x[1], x[2])
    y = np.array(x, float).copy()
    y[3] = t
    return y


def start_ocv(x, ocp):
    return float(ocp.ocv(0.0, hp_of(x)))


def qfc_sim(cells, ocp):
    """cells: list of 4 parameter vectors (Qn, Qp, QLi, thn0, R, h). Returns (Q_fc, end states)."""
    hps = [hp_of(x) for x in cells]
    q = sim_cccv(hps, [x[4] for x in cells], [x[5] for x in cells], ocp=ocp)
    if not np.isfinite(q):
        return np.nan, None
    return float(q), [end_state(hp, q) for hp in hps]


def dprog_sim(cells, ends, ocp, cfg=MAIN_STEP):
    d = np.arange(0.0, 56.0, 0.05)
    locs = []
    for x, hp in zip(cells, ends):
        v = ocp.ocv(-d, hp) - x[4] * I_PROG - x[5]
        locs.append(step_depth(d, v, cfg))
    return float(np.nanmean(locs)) if np.isfinite(locs).any() else np.nan


def qc20_sim(ends, etas, ocp):
    return q_c20(ends, etas, ocp, c_pack=C_PACK)


def pack_quantities(cells, ocp, etas=None):
    q, ends = qfc_sim(cells, ocp)
    if ends is None:
        return dict(Q_fc=np.nan, D_prog=np.nan, Q_C20=np.nan, limiting=None)
    out = dict(Q_fc=q, D_prog=dprog_sim(cells, ends, ocp))
    if etas is not None:
        r, lim = qc20_sim(ends, etas, ocp)
        out.update(Q_C20=r, limiting=lim)
    return out


def beta_E(cells_ref, cells_deg, v_starts, ocp):
    """Pack beta along ref -> deg, both started at the reference start OCVs (start defined by voltage)."""
    a = [restart(x, v, ocp) for x, v in zip(cells_ref, v_starts)]
    b = [restart(x, v, ocp) for x, v in zip(cells_deg, v_starts)]
    if any(not np.isfinite(y[3]) for y in a + b):
        return np.nan, {}
    pa, pb = pack_quantities(a, ocp), pack_quantities(b, ocp)
    dd = pb["D_prog"] - pa["D_prog"]
    dq = pb["Q_fc"] - pa["Q_fc"]
    return (float(dq / dd) if np.isfinite(dd) and abs(dd) > 1e-9 else np.nan), dict(dQ_fc=dq, dD_prog=dd)
