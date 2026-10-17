"""Check the CK2 sqrt(t) gap branch against the TUM Sony LFP calendar-ageing data (Mendeley kxh42bfgtj v1).

Usage: python3 check_tum_calendar.py [DATA_DIR]   (default ~/Desktop/kxh42bfgtj-1)
Writes outputs/ next to this script.

Only DischargeCapacity.xlsx is used (17 static storage conditions, 35 check-ups, 0-21241 h).
The dataset has no charge capacity, so epsilon (charge Ah vs discharge capacity) cannot be tested.
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit, nnls

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")
DATA = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Desktop/kxh42bfgtj-1")

# The submitted CK2 branch: loss at t1 = CK1 - CK0 is extrapolated with t^p to t2 = CK2 - CK0.
T1, T2 = 25.0, 56.0  # days (2025-01-14 -> 02-08 -> 03-11)
OUR_INCREMENT_AH = 1.35  # predicted CK1->CK2 loss increment of the branch at eps0+0.4 (2.719 Ah * (sqrt(56/25)-1))
MIN_LOSS_FRAC = 0.005  # skip conditions that lost < 0.5 % by day 56 (increment too small vs noise)


def load():
    raw = pd.read_excel(os.path.join(DATA, "DischargeCapacity.xlsx"), header=None)
    names = raw.iloc[1, 1:].tolist()
    body = raw.iloc[2:].astype(float)
    t_days = body.iloc[:, 0].to_numpy() / 24.0
    q = body.iloc[:, 1:].to_numpy()
    return t_days, q, names


def loss_at(t, loss, tq):
    """Interpolate loss in log-log space (power-law-consistent) between check-ups."""
    m = (t > 0) & (loss > 0)
    return float(np.exp(np.interp(np.log(tq), np.log(t[m]), np.log(loss[m]))))


def fit_models(t, loss):
    m = t > 0
    tt, ll = t[m], loss[m]
    res = {}
    # free power law L = b t^p
    (b, p), _ = curve_fit(lambda x, b, p: b * x ** p, tt, ll, p0=[ll[-1] / tt[-1] ** 0.5, 0.5], maxfev=20000)
    res["pow"] = {"p": p, "rmse": float(np.sqrt(np.mean((b * tt ** p - ll) ** 2))), "k": 2}
    # sqrt only
    b = float((np.sqrt(tt) * ll).sum() / tt.sum())
    res["sqrt"] = {"rmse": float(np.sqrt(np.mean((b * np.sqrt(tt) - ll) ** 2))), "k": 1}
    # saturating + sqrt / + linear, tau on a grid, non-negative amplitudes
    for name, g in (("sat_sqrt", np.sqrt), ("sat_lin", lambda x: x)):
        best = None
        for tau in np.geomspace(2, 150, 60):
            A = np.column_stack([1 - np.exp(-tt / tau), g(tt)])
            coef, rnorm = nnls(A, ll)
            if best is None or rnorm < best[0]:
                best = (rnorm, tau, coef)
        rnorm, tau, coef = best
        res[name] = {"tau_d": float(tau), "a_sat": float(coef[0]), "b": float(coef[1]),
                     "sat_share_end": float(coef[0] / ll[-1]),
                     "rmse": float(rnorm / np.sqrt(len(ll))), "k": 3}
    n = len(ll)
    for r in res.values():
        r["bic"] = float(n * np.log(r["rmse"] ** 2) + r["k"] * np.log(n))
    # local exponents early vs late
    early, late = tt <= 60, (tt > 60) & (tt <= 400)
    for lab, w in (("p_early_le60d", early), ("p_60_400d", late), ("p_gt400d", tt > 400)):
        if w.sum() >= 3:
            res[lab] = float(np.polyfit(np.log(tt[w]), np.log(ll[w]), 1)[0])
    return res


def main():
    os.makedirs(OUT, exist_ok=True)
    t, q, names = load()
    rows, analog = [], []
    for j, name in enumerate(names):
        loss = q[0, j] - q[:, j]
        l1, l2 = loss_at(t, loss, T1), loss_at(t, loss, T2)
        row = {"condition": name, "Q0_Ah": q[0, j], "loss_end_pct": 100 * loss[-1] / q[0, j],
               "loss_d25_mAh": 1000 * l1, "loss_d56_mAh": 1000 * l2}
        fits = fit_models(t, loss)
        row.update({"p_free": fits["pow"]["p"], "p_early_le60d": fits.get("p_early_le60d"),
                    "p_60_400d": fits.get("p_60_400d"), "p_gt400d": fits.get("p_gt400d"),
                    "rmse_sqrt_mAh": 1000 * fits["sqrt"]["rmse"], "rmse_pow_mAh": 1000 * fits["pow"]["rmse"],
                    "rmse_satsqrt_mAh": 1000 * fits["sat_sqrt"]["rmse"], "tau_satsqrt_d": fits["sat_sqrt"]["tau_d"],
                    "satshare_end": fits["sat_sqrt"]["sat_share_end"],
                    "rmse_satlin_mAh": 1000 * fits["sat_lin"]["rmse"],
                    "best_bic": min(("sqrt", "pow", "sat_sqrt", "sat_lin"), key=lambda k: fits[k]["bic"])})
        rows.append(row)
        if l2 / q[0, j] < MIN_LOSS_FRAC:
            continue
        # analogue of the CK2 branch at the exact days, plus the same ratio at other start times
        for t1 in (T1, 10.0, 17.0, 40.0, 60.0, 100.0):
            t2 = t1 * T2 / T1
            if t2 > t[-1]:
                continue
            a1, a2 = loss_at(t, loss, t1), loss_at(t, loss, t2)
            pred_inc = a1 * ((t2 / t1) ** 0.5 - 1)
            true_inc = a2 - a1
            analog.append({"condition": name, "t1_d": t1, "t2_d": t2, "loss_t1_mAh": 1000 * a1,
                           "true_inc_mAh": 1000 * true_inc, "sqrt_pred_inc_mAh": 1000 * pred_inc,
                           "ratio_true_over_pred": true_inc / pred_inc,
                           "p_eff": float(np.log(a2 / a1) / np.log(t2 / t1))})
    fits = pd.DataFrame(rows)
    an = pd.DataFrame(analog)
    fits.to_csv(os.path.join(OUT, "tum_fits_by_condition.csv"), index=False, float_format="%.4f")
    an.to_csv(os.path.join(OUT, "tum_ck2_analogue.csv"), index=False, float_format="%.4f")

    main_an = an[an.t1_d == T1]
    r = main_an.ratio_true_over_pred.to_numpy()
    # CK2 SOH error implied for our pack if the same ratio applied: (pred - true) increment, in pp of 102 Ah
    implied_pp = (1 - r) * OUR_INCREMENT_AH / 1.02  # >0: branch predicts too much loss -> CK2 SOH too low
    summary = {
        "data_dir": DATA,
        "n_conditions_used": int(len(main_an)),
        "ck2_analogue_t1_t2_days": [T1, T2],
        "ratio_true_over_sqrt_pred": {"median": float(np.median(r)), "min": float(r.min()), "max": float(r.max())},
        "p_eff_d25_to_d56": {"median": float(main_an.p_eff.median()), "min": float(main_an.p_eff.min()),
                             "max": float(main_an.p_eff.max())},
        "implied_CK2_SOH_bias_pp_if_transferred": {"median": float(np.median(implied_pp)),
                                                   "min": float(implied_pp.min()), "max": float(implied_pp.max())},
        "ratio_by_t1_median": an.groupby("t1_d").ratio_true_over_pred.median().round(3).to_dict(),
        "best_bic_counts": fits.best_bic.value_counts().to_dict(),
        "p_free_median_used": float(fits[fits.condition.isin(main_an.condition)].p_free.median()),
    }
    with open(os.path.join(OUT, "tum_summary.json"), "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    pd.set_option("display.width", 250)
    print(fits.round(3).to_string(index=False))
    print(main_an.round(3).to_string(index=False))
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
