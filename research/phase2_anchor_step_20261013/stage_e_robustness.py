"""Stage B checks and stage E robustness / falsification."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "TechArena_Challenge2_Team_Package"))
sys.path.insert(0, os.path.join(HERE, "src"))
sys.path.insert(0, ROOT)

from framework.data import load_dataset, load_eval_points  # noqa: E402
from events import CELLS, MAIN_STEP, _locate, full_charges, step_programs  # noqa: E402
from predictors import m4  # noqa: E402

OUT = os.path.join(HERE, "outputs")
NOM = 102.0


def leave_one_anchor_out(data, qfc, eps0, de=0.4):
    """Drop the latest visible full charge at each CK and re-run M4 main."""
    rows = []
    pts = load_eval_points(data)
    for k, p in enumerate(pts[pts["checkup"] != "CK0"].itertuples(), start=1):
        if k < 2:
            continue
        ds = load_dataset(data, until=p.date)
        fc = full_charges(ds.operation).sort_values("t_end")
        st = step_programs(ds.operation)
        full = m4(fc, st, p.date, eps0 + de, eps0)
        drop = m4(fc.iloc[:-1], st, p.date, eps0 + de, eps0)
        proxy = qfc[k - 1] + eps0 + de
        rows.append(dict(checkup=p.checkup, M4=full, M4_drop_latest_anchor=drop,
                         err_pp=(full - proxy) / NOM * 100, err_drop_pp=(drop - proxy) / NOM * 100))
    return pd.DataFrame(rows)


def epsilon_drift_checks(fc):
    g = fc[fc["setpoint_C"] == 25].sort_values("t_end").copy()
    t = (g["t_end"] - g["t_end"].iloc[0]).dt.total_seconds().to_numpy() / 86400
    x = np.c_[np.ones(len(t)), np.sqrt(t + 1)]
    coef = np.linalg.lstsq(x, g["Q_Ah"].to_numpy(), rcond=None)[0]
    g["resid_sqrt_fit_Ah"] = g["Q_Ah"].to_numpy() - x @ coef
    g["CV_share"] = 1 - g["Q_CC_Ah"] / g["Q_Ah"]
    r = np.corrcoef(g["resid_sqrt_fit_Ah"], g["pack_start_V"])[0, 1]
    return g[["segment", "t_end", "Q_Ah", "Q_CC_Ah", "CV_share", "I_end_A", "pack_start_V",
              "rest_before_h", "temp_C", "resid_sqrt_fit_Ah"]], float(r)


def per_cell_trends(st):
    st = st.sort_values("t_cv_end")
    t = (st["t_cv_end"] - st["t_cv_end"].iloc[0]).dt.total_seconds().to_numpy() / 86400
    out = {}
    for c in CELLS:
        out[c] = dict(total_change_Ah=float(st[f"step_{c}"].iloc[-1] - st[f"step_{c}"].iloc[0]),
                      slope_Ah_per_100d=float(np.polyfit(t, st[f"step_{c}"], 1)[0] * 100))
    return out


# --- synthetic half-cell mechanism test -------------------------------------------------

def _u_neg(x):
    """Graphite-like OCP (V): two staging steps; values are a coarse, illustrative shape."""
    return (0.085 + 0.035 * (1 - 1 / (1 + np.exp(-(x - X_S) / 0.012)))
            + 0.05 * (1 - 1 / (1 + np.exp(-(x - X_2) / 0.015))) + 0.6 * np.exp(-x / 0.012))


def _u_pos(y):
    """LFP-like OCP (V): flat plateau with steep ends."""
    return 3.42 - 0.6 * np.exp(-(1 - y) / 0.01) + 0.4 * np.exp(-y / 0.008)


C_N0, C_P0, X_TOP0 = 108.0, 104.0, 0.93
X_S = X_TOP0 - 33.0 / C_N0
X_2 = X_TOP0 - 80.0 / C_N0


def _discharge(li, c_n, c_p, v_top=3.5, v_bot=2.8, ir=0.02):
    """Return depth grid (Ah from top) and cell voltage for a full-cell state."""
    # top of charge: find graphite fill where V = v_top (charging), Li conserved
    q = np.arange(-15.0, 130.0, 0.01)
    x0 = li / c_n  # reference: all cyclable Li in graphite
    x = x0 - q / c_n
    y = q / c_p
    ok = (x > 1e-4) & (x < 1) & (y > 1e-4) & (y < 1)
    q, x, y = q[ok], x[ok], y[ok]
    v = _u_pos(y) - _u_neg(x)
    top = q[np.argmax(v <= v_top)]
    vd = v - ir
    after = (q > top) & (vd <= v_bot)
    bot = q[np.argmax(after)] if after.any() else q[-1]
    d = q[(q >= top) & (q <= bot)] - top
    return d, vd[(q >= top) & (q <= bot)], bot - top


def synthetic_test():
    li0 = X_TOP0 * C_N0
    _, _, q0 = _discharge(li0, C_N0, C_P0)
    d0, v0, _ = _discharge(li0, C_N0, C_P0)
    s0 = _locate(d0, v0, MAIN_STEP)
    rows = []
    for mech in ("LLI", "LAM_NE", "LAM_PE", "LLI+LAM_NE_observed_mix"):
        for loss in (1.0, 3.0, 6.0, 9.0):
            li, cn, cp = li0, C_N0, C_P0
            if mech == "LLI":
                li = li0 - loss
            elif mech == "LAM_NE":
                cn = C_N0 - loss / X_S  # shrink bottom->step section by `loss`
            elif mech == "LAM_PE":
                cp = C_P0 - loss
            else:  # bottom section shrinks by 26% of the LLI amount (A4 split)
                li = li0 - loss
                cn = C_N0 - 0.26 * loss / X_S
            d, v, q = _discharge(li, cn, cp)
            s = _locate(d, v, MAIN_STEP)
            pred = q0 + (s - s0)
            rows.append(dict(mechanism=mech, nominal_loss_Ah=loss, Q_true=q, dQ_true=q - q0,
                             step_Ah=s, dstep_Ah=s - s0, M4_pred=pred, M4_err_Ah=pred - q))
    return pd.DataFrame(rows), dict(Q0=q0, step0=s0)


def main():
    data = os.path.join(ROOT, "data")
    full = load_dataset(data)
    fc = full_charges(full.operation).sort_values("t_end").reset_index(drop=True)
    qfc, eps0 = fc.loc[1:, "Q_Ah"].to_numpy(), 100.41 - fc.loc[0, "Q_Ah"]
    st = step_programs(full.operation)

    loo = leave_one_anchor_out(data, qfc, eps0)
    loo.to_csv(os.path.join(OUT, "E3_leave_one_anchor_out.csv"), index=False)
    drift, r = epsilon_drift_checks(fc)
    drift.to_csv(os.path.join(OUT, "B_epsilon_drift_checks.csv"), index=False)
    cells = per_cell_trends(st)
    syn, ref = synthetic_test()
    syn.to_csv(os.path.join(OUT, "E4_synthetic_mechanisms.csv"), index=False)

    summary = dict(leave_one_anchor_out=loo.round(3).to_dict("records"),
                   corr_resid_vs_start_voltage=r, per_cell_step_trends=cells,
                   synthetic_reference=ref, synthetic=syn.round(3).to_dict("records"))
    with open(os.path.join(OUT, "E_summary.json"), "w") as f:
        json.dump(summary, f, indent=2, default=str)
    pd.set_option("display.width", 250)
    print(loo.round(3).to_string(index=False))
    print(drift.round(3).to_string(index=False), "\ncorr(resid, start V) =", round(r, 3))
    print(json.dumps(cells, indent=1))
    print(ref)
    print(syn.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
