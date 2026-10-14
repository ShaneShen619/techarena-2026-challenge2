"""Stage 2: BoL calibration and the CK0 check (protocol.json)."""
import json
import os
import pickle
import sys

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
from common5b import CACHE5, H  # noqa: E402
from edata import anchor_curve, ck0_curve  # noqa: E402
from emodel import OCP, fit_charge, q_c20, valid_range  # noqa: E402
from epack import C_PACK, MAIN_STEP, qfc_sim  # noqa: E402
from emodel import step_depth  # noqa: E402
from events import ck0_reference_step  # noqa: E402
from v2 import anchors_by_checkup  # noqa: E402

OUT = os.path.join(HERE, "outputs")
os.makedirs(OUT, exist_ok=True)
D_END = 100.412
WIN = (5.0, D_END - 15.0)


def fit_ck0(xh, d, v, ocp):
    """Fit eta_dis and the start lithiation theta_n,s for one cell, health fixed."""
    Qn, Qp, QLi = xh[:3]
    w = (d >= WIN[0]) & (d <= WIN[1])
    dd, vv = d[w][::10], v[w][::10]

    def res(p):
        eta, tns = p
        m = ocp.ocv(-dd, (Qn, Qp, QLi, tns)) - eta
        return (m - vv) * 1000.0
    best = None
    for tns in (0.6, 0.75, 0.85, 0.95, 1.0):
        r = least_squares(res, [0.0, tns], bounds=([-0.2, -0.05], [0.2, 1.05]), loss="soft_l1", f_scale=2.0)
        if best is None or r.cost < best.cost:
            best = r
    return best.x, float(np.sqrt(np.mean(res(best.x) ** 2)))


def run(ref_anchor, label):
    ocp = OCP("main")
    op = H.full_op()
    anc = anchors_by_checkup(H.full_charges(op), H.CK)
    q, I, V, vr, qt = anchor_curve(op, anc[ref_anchor])
    cells = []
    for c in range(4):
        x, info = fit_charge(q, I, V[:, c], ocp)
        cells.append(x)
    ref = H.load_dataset(H.DATA).reference_discharge
    d, Vr, c_pack_meas = ck0_curve(ref)
    etas, starts, rms = [], [], []
    for c in range(4):
        p, r = fit_ck0(cells[c], d, Vr[:, c], ocp)
        etas.append(float(p[0])); starts.append(float(p[1])); rms.append(r)
    hps = [(x[0], x[1], x[2], s) for x, s in zip(cells, starts)]
    root, lim = q_c20(hps, etas, ocp, c_pack=C_PACK, q_max=125.0)
    # per-cell residuals over the last 15 Ah (never fitted)
    tail = d > WIN[1]
    tail_rms = [float(np.sqrt(np.mean(((ocp.ocv(-d[tail], hp) - e) - Vr[tail, c]) ** 2)) * 1000)
                for c, (hp, e) in enumerate(zip(hps, etas))]
    # first cell to reach its end of validity / lowest voltage at the root
    meas_step = ck0_reference_step(ref)
    model_step = []
    for c, (hp, e) in enumerate(zip(hps, etas)):
        model_step.append(step_depth(d, ocp.ocv(-d, hp) - e, MAIN_STEP))
    meas = [meas_step[f"mid_cell{c + 1}_V"] for c in range(4)]
    step_diff = [float(a - b) for a, b in zip(model_step, meas)]
    # E3 chain diagnostic: simulated CCCV end of the reference anchor -> C/20
    qfc, ends = qfc_sim(cells, ocp)
    chain_root, chain_lim = q_c20(ends, etas, ocp, c_pack=C_PACK) if ends is not None else (np.nan, None)
    qfc_obs = float(anc[ref_anchor]["Q_Ah"])
    out = dict(reference_anchor=ref_anchor, label=label,
               ref_fit=[list(map(float, x)) for x in cells],
               ck0_fit=dict(eta_dis=etas, theta_n_start=starts, rms_mV_fit_window=rms),
               Q_C20_sim=root, Q_C20_err_vs_10041=(root - 100.41) if np.isfinite(root) else None,
               Q_C20_err_vs_ext_root=(root - 100.416854) if np.isfinite(root) else None,
               limiting_cell_at_root=None if lim is None else lim + 1,
               tail_rms_mV=tail_rms, c_pack_measured=c_pack_meas,
               model_step_Ah=model_step, measured_step_Ah=meas, step_diff_Ah=step_diff,
               credible=bool(np.isfinite(root) and abs(root - 100.41) <= 0.5 and all(abs(x) <= 1.0 for x in step_diff)),
               chain=dict(Q_fc_sim=qfc, Q_fc_obs=qfc_obs, Q_C20_from_anchor=chain_root,
                          eps_sim=(chain_root - qfc_obs) if np.isfinite(chain_root) else None,
                          eps_sim_selfconsistent=(chain_root - qfc) if np.isfinite(chain_root) and np.isfinite(qfc) else None,
                          eps0_observed=100.41 - qfc_obs))
    pickle.dump(dict(cells=cells, etas=etas, starts=starts), open(os.path.join(CACHE5, f"bol_{label}.pkl"), "wb"))
    # curve for the figure
    hp_curve = pd.DataFrame({"d": d[::20], **{f"meas_c{c+1}": Vr[::20, c] for c in range(4)},
                             **{f"model_c{c+1}": ocp.ocv(-d[::20], hps[c]) - etas[c] for c in range(4)}})
    hp_curve.to_csv(os.path.join(OUT, f"S2_ck0_curve_{label}.csv"), index=False)
    return out


if __name__ == "__main__":
    res = {"main_anchor0": run(0, "main_anchor0"), "variant_anchor1": run(1, "variant_anchor1")}
    json.dump(res, open(os.path.join(OUT, "S2_ck0_check.json"), "w"), indent=1, default=float)
    for k, v in res.items():
        print(k, json.dumps({kk: vv for kk, vv in v.items() if kk != "ref_fit"}, indent=1, default=float))
