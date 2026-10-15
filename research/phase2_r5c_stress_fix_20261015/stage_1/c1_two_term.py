"""Stage 1: two-term law refit on the six Challenge 1 cells (protocol.json c1_two_term_refit)."""
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))
from c1_cycles import CELLS, NOM, cycle_summary  # noqa: E402
from smodel import yagci_logA_cal  # noqa: E402

OUT = os.path.join(HERE, "outputs")
R, TREF, N_REF, EA = 8.314462618, 298.15, 6, 37.3e3


def prepare(cell):
    """Same rules as 5A stage_2/fit_prior.prepare."""
    s = cycle_summary(cell).sort_values("cycle_number").reset_index(drop=True)
    q0 = s.loc[s["cycle_number"].between(2, 10), "q_lab"].median()
    s["r"] = s["q_lab"] / q0
    sm = s["r"].rolling(21, center=True, min_periods=3).median()
    below = np.where((s["cycle_number"] >= 2) & (sm < 0.85))[0]
    s = s.iloc[: below[0] if len(below) else len(s)].copy()
    s["cyc_d"] = (s["t1"] - s["t0"]).dt.total_seconds().to_numpy() / 86400
    s["gap_d"] = np.clip(np.r_[(s["t0"].iloc[1:].to_numpy() - s["t1"].iloc[:-1].to_numpy()) / np.timedelta64(1, "s") / 86400, 0.0], 0, None)
    s["Tn"] = float(cell.split("_")[1].replace("degC", ""))
    aT = np.exp(-EA / R * (1 / (s["T"].to_numpy() + 273.15) - 1 / TREF))
    aTn = np.exp(-EA / R * (1 / (s["Tn"].to_numpy() + 273.15) - 1 / TREF))
    s["tau"] = np.cumsum(s["cyc_d"].to_numpy() * aT + s["gap_d"].to_numpy() * aTn) - s["gap_d"].to_numpy() * aTn
    s["ah"] = np.cumsum(s["thr"].to_numpy() * aT)
    s["iref"] = int(np.argmin(np.abs(s["cycle_number"].to_numpy() - N_REF)))
    return s


def model(theta, s):
    lab, ltb, lac, lay = theta
    tau, ah = s["tau"].to_numpy(), s["ah"].to_numpy()
    m = np.exp(lab) * (1 - np.exp(-tau / np.exp(ltb))) + np.exp(lac) * np.sqrt(np.clip(tau, 0, None)) + np.exp(lay) * ah
    return m - m[int(s["iref"].iloc[0])]


def resid(theta, data):
    out = []
    for s in data:
        ok = s["r"].notna().to_numpy() & (s["cycle_number"].to_numpy() >= 2)
        L = NOM * (1 - s["r"].to_numpy())
        out.append((model(theta, s)[ok] - L[ok]) / np.sqrt(max(ok.sum(), 1)))
    return np.concatenate(out)


LB = np.log([1e-3, 0.5, 1e-4, 1e-10])
UB = np.log([50.0, 300.0, 10.0, 1e-2])


def fit(data):
    best = None
    for ab in (1.0, 4.0):
        for tb in (5.0, 30.0):
            for ac in (0.05, 0.3):
                for ay in (1e-6, 3e-5):
                    x0 = np.clip(np.log([ab, tb, ac, ay]), LB + 1e-6, UB - 1e-6)
                    r = least_squares(resid, x0, bounds=(LB, UB), args=(data,))
                    if best is None or r.cost < best.cost:
                        best = r
    return best


if __name__ == "__main__":
    data = [prepare(c) for c in CELLS]
    J = fit(data)
    loco = np.array([fit([d for j, d in enumerate(data) if j != i]).x for i in range(len(data))])
    n = len(data)
    jk = np.sqrt((n - 1) / n * np.sum((loco - loco.mean(0)) ** 2, axis=0))
    names = ["logA_b", "logtau_b", "logA_cal", "logA_cyc"]
    prior = {"c1_joint": dict(zip(names, map(float, J.x))), "c1_jackknife_sd": dict(zip(names, map(float, jk)))}
    for i, nm in enumerate(names):
        at_bound = bool(abs(J.x[i] - LB[i]) < 1e-3 or abs(J.x[i] - UB[i]) < 1e-3)
        unid = bool(jk[i] > np.log(3))
        sd = max(jk[i], 0.5) if nm == "logtau_b" else np.log(3)
        mean, src = float(J.x[i]), "Challenge 1 joint two-term fit"
        if at_bound or unid:
            if nm == "logA_cal":
                mean, src = yagci_logA_cal(0.5, 37.3), "fallback: Yagci-derived at z = 0.5"
            elif nm == "logA_cyc":
                mean, src = -11.754453247878848, "fallback: 5A prior centre"
            else:
                sd, src = max(jk[i], np.log(3)), "fallback: joint value kept, SD max(jk, ln 3)"
        prior[nm] = dict(mean=float(mean), sd=float(sd), source=src, at_bound=at_bound, unidentified=unid)
    rmse = {c: float(np.sqrt(np.mean((resid(J.x, [d]) * np.sqrt(d['r'].notna().sum())) ** 2))) for c, d in zip(CELLS, data)}
    prior["c1_per_cell_rmse_Ah"] = rmse
    json.dump(prior, open(os.path.join(HERE, "prior2.json"), "w"), indent=1)
    pd.DataFrame(loco, columns=names, index=CELLS).to_csv(os.path.join(OUT, "S1_c1_two_term_loco.csv"))
    print(json.dumps(prior, indent=1))
