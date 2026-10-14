"""Stage 2: fit the stress law to the six Challenge 1 cells and build prior.json (protocol.json)."""
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from c1_cycles import CELLS, NOM, cycle_summary  # noqa: E402

OUT = os.path.join(HERE, "outputs")
os.makedirs(OUT, exist_ok=True)
R = 8.314462618
TREF = 298.15
N_REF = 6            # reference cycle (centre of cycles 2..10)


def nominal_T(cell):
    return float(cell.split("_")[1].replace("degC", ""))


def prepare(cell):
    s = cycle_summary(cell).sort_values("cycle_number").reset_index(drop=True)
    q0 = s.loc[s["cycle_number"].between(2, 10), "q_lab"].median()
    s["r"] = s["q_lab"] / q0
    sm = s["r"].rolling(21, center=True, min_periods=3).median()
    s["r_sm"] = sm
    below = np.where((s["cycle_number"] >= 2) & (sm < 0.85))[0]
    end = below[0] if len(below) else len(s)
    s = s.iloc[:end].copy()
    # stress increments per cycle: cycle portion at measured T, idle gap to the next cycle at nominal T
    cyc_d = (s["t1"] - s["t0"]).dt.total_seconds().to_numpy() / 86400
    gap_d = np.clip(np.r_[(s["t0"].iloc[1:].to_numpy() - s["t1"].iloc[:-1].to_numpy()) / np.timedelta64(1, "s") / 86400, 0.0], 0, None)
    s["cyc_d"], s["gap_d"] = cyc_d, gap_d
    s["Tn"] = nominal_T(cell)
    return s


def cum_stress(s, Ea_J):
    aT = np.exp(-Ea_J / R * (1 / (s["T"].to_numpy() + 273.15) - 1 / TREF))
    aTn = np.exp(-Ea_J / R * (1 / (s["Tn"].to_numpy() + 273.15) - 1 / TREF))
    dtau = s["cyc_d"].to_numpy() * aT + s["gap_d"].to_numpy() * aTn
    dah = s["thr"].to_numpy() * aT
    # stress at the end of cycle n's discharge: everything up to and including cycle n's own time
    tau = np.cumsum(dtau) - s["gap_d"].to_numpy() * aTn
    ah = np.cumsum(dah)
    return tau, ah


def model_L(theta, s, fixed=None):
    lac, lay, z, ea = theta
    tau, ah = cum_stress(s, ea * 1e3)
    m = np.exp(lac) * np.power(np.clip(tau, 0, None), z) + np.exp(lay) * ah
    i_ref = int(np.argmin(np.abs(s["cycle_number"].to_numpy() - N_REF)))
    return m - m[i_ref]


def residuals(theta, data, weights):
    out = []
    for s, w in zip(data, weights):
        ok = s["r"].notna().to_numpy() & (s["cycle_number"].to_numpy() >= 2)
        L = NOM * (1 - s["r"].to_numpy())
        out.append(w * (model_L(theta, s)[ok] - L[ok]))
    return np.concatenate(out)


LB = [np.log(1e-6), np.log(1e-9), 0.2, 5.0]
UB = [np.log(1e2), np.log(1e-1), 1.0, 100.0]


def fit_joint(data):
    w = [1 / np.sqrt(max(s["r"].notna().sum(), 1)) for s in data]
    best = None
    for lac0 in (np.log(0.01), np.log(0.3)):
        for lay0 in (np.log(1e-6), np.log(1e-4)):
            for z0 in (0.5, 0.8):
                for ea0 in (30.0, 60.0):
                    r = least_squares(residuals, [lac0, lay0, z0, ea0], bounds=(LB, UB), args=(data, w),
                                      x_scale=[1, 1, 0.1, 10])
                    if best is None or r.cost < best.cost:
                        best = r
    return best


def fit_cell(s):
    """Per-cell fit with temperature absorbed (a_T = 1): theta = (log A_cal, log A_cyc, z)."""
    def res(th):
        return residuals([th[0], th[1], th[2], 0.0], [s.assign(T=25.0, Tn=25.0)], [1.0])
    best = None
    for lac0 in (np.log(0.01), np.log(0.3)):
        for lay0 in (np.log(1e-6), np.log(1e-4)):
            for z0 in (0.5, 0.8):
                r = least_squares(res, [lac0, lay0, z0], bounds=(LB[:3], UB[:3]), x_scale=[1, 1, 0.1])
                if best is None or r.cost < best.cost:
                    best = r
    return best


def yagci_values(z, Ea_kJ):
    """Yagci 2025 derived A_cal (Ah/d^z) and A_cyc (per Ah) on a 102 Ah cell, at T_ref = 25 C."""
    aT = lambda T: np.exp(-Ea_kJ * 1e3 / R * (1 / (T + 273.15) - 1 / TREF))
    cal = {35: (7.5 + 7.8) / 2 / 100, 50: (13.3 + 14.0) / 2 / 100}
    cyc = {35: 11.0 / 100, 50: 22.3 / 100}
    days, thr = 848.0, 1500 * 2 * NOM
    a_cal = [NOM * cal[T] / (aT(T) * days) ** z for T in (35, 50)]
    a_cyc = [NOM * (cyc[T] - cal[T]) / (aT(T) * thr) for T in (35, 50)]
    return float(np.exp(np.mean(np.log(a_cal)))), float(np.exp(np.mean(np.log(a_cyc)))), dict(
        a_cal_35_50=a_cal, a_cyc_35_50=a_cyc)


def predict_yagci(A_cal, A_cyc, z, Ea_kJ):
    aT = lambda T: np.exp(-Ea_kJ * 1e3 / R * (1 / (T + 273.15) - 1 / TREF))
    out = {}
    for T, cal_obs, cyc_obs in ((35, 7.65, 11.0), (50, 13.65, 22.3)):
        cal = A_cal * (aT(T) * 848) ** z / NOM * 100
        cyc = cal + A_cyc * aT(T) * 1500 * 2 * NOM / NOM * 100
        out[f"{T}C"] = dict(calendar_pred_pct=cal, calendar_obs_pct=cal_obs, factor_cal=cal / cal_obs,
                            cyclic_pred_pct=cyc, cyclic_obs_pct=cyc_obs, factor_cyc=cyc / cyc_obs)
    return out


if __name__ == "__main__":
    data = [prepare(c) for c in CELLS]
    info = []
    for c, s in zip(CELLS, data):
        info.append(dict(cell=c, n_used=int(s["r"].notna().sum()), last_cycle=int(s["cycle_number"].max()),
                         days=float((s["t1"].max() - s["t0"].min()).total_seconds() / 86400),
                         T_median=float(s["T"].median()), r_end=float(s["r_sm"].iloc[-1]),
                         thr_kAh=float(s["thr"].sum() / 1e3)))
    pd.DataFrame(info).to_csv(os.path.join(OUT, "S2_cells_used.csv"), index=False)
    print(pd.DataFrame(info).round(3).to_string())

    # per-cell fits
    pc = []
    for c, s in zip(CELLS, data):
        r = fit_cell(s)
        pc.append(dict(cell=c, A_cal=float(np.exp(r.x[0])), A_cyc=float(np.exp(r.x[1])), z=float(r.x[2]),
                       rmse_Ah=float(np.sqrt(np.mean(r.fun ** 2)))))
    pc = pd.DataFrame(pc)
    pc.to_csv(os.path.join(OUT, "S2_per_cell_fits.csv"), index=False)
    print(pc.to_string())

    # joint fit + LOCO jackknife
    J = fit_joint(data)
    th = J.x
    loco = []
    for i in range(len(data)):
        r = fit_joint([d for j, d in enumerate(data) if j != i])
        loco.append(r.x)
    loco = np.array(loco)
    n = len(data)
    jk_sd = np.sqrt((n - 1) / n * np.sum((loco - loco.mean(0)) ** 2, axis=0))
    names = ["logA_cal", "logA_cyc", "z", "Ea_kJ"]
    joint = {k: float(v) for k, v in zip(names, th)}
    sd = {k: float(v) for k, v in zip(names, jk_sd)}
    pd.DataFrame(loco, columns=names, index=CELLS).to_csv(os.path.join(OUT, "S2_loco_fits.csv"))
    # per-cell RMSE of the joint fit
    jr = []
    for c, s in zip(CELLS, data):
        res = residuals(th, [s], [1.0])
        jr.append(dict(cell=c, rmse_Ah=float(np.sqrt(np.mean(res ** 2))), bias_Ah=float(np.mean(res))))
    pd.DataFrame(jr).to_csv(os.path.join(OUT, "S2_joint_residuals.csv"), index=False)

    # prior rules (protocol.json)
    z_mu, z_sd = joint["z"], max(sd["z"], 0.1)
    ea_width = 2 * 1.96 * sd["Ea_kJ"]
    if ea_width < 25.6:
        ea_mu, ea_sd, ea_src = joint["Ea_kJ"], sd["Ea_kJ"], "Challenge 1 joint fit"
    else:
        ea_mu, ea_sd, ea_src = 37.3, 12.8 / 1.96, "Yagci 2025"
    ya_cal, ya_cyc, ya_detail = yagci_values(z_mu, ea_mu)
    prior = {"z": dict(mean=z_mu, sd=z_sd, source="Challenge 1 joint fit; sd = max(jackknife, 0.1)"),
             "Ea_kJ": dict(mean=ea_mu, sd=ea_sd, source=ea_src, c1_joint=joint["Ea_kJ"], c1_sd=sd["Ea_kJ"],
                           c1_95width=ea_width)}
    for key, ya in (("logA_cal", ya_cal), ("logA_cyc", ya_cyc)):
        at_bound = (abs(th[names.index(key)] - LB[names.index(key)]) < 1e-3 or
                    abs(th[names.index(key)] - UB[names.index(key)]) < 1e-3)
        unident = sd[key] > np.log(3)
        if at_bound or unident:
            prior[key] = dict(mean=float(np.log(ya)), sd=float(np.log(3)),
                              source="Yagci 2025 derived (identifiability fallback)",
                              c1_joint=joint[key], c1_jackknife_sd=sd[key], c1_at_bound=bool(at_bound))
        else:
            prior[key] = dict(mean=joint[key], sd=float(np.log(3)), source="Challenge 1 joint fit",
                              c1_jackknife_sd=sd[key], yagci_value=float(np.log(ya)))
    prior["T_ref_K"] = TREF
    prior["units"] = "L in Ah on a 102 Ah cell; tau_eff in Arrhenius-weighted days; ah_eff in Arrhenius-weighted Ah of total throughput"
    prior["sanity_vs_yagci"] = predict_yagci(np.exp(prior["logA_cal"]["mean"]), np.exp(prior["logA_cyc"]["mean"]),
                                             z_mu, ea_mu)
    prior["yagci_detail"] = ya_detail
    prior["c1_joint"] = joint
    prior["c1_jackknife_sd"] = sd
    json.dump(prior, open(os.path.join(HERE, "prior.json"), "w"), indent=1)
    print(json.dumps(prior, indent=1))
