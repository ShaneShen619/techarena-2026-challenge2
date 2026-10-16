"""WP4: fit the two-term law on open data and write prior3.json (protocol.json).
Usage: python3 -I fit_prior3.py <study_dir> [<yagci_table_csv>]
The Yagci table (if given) has columns: cell, kind (calendar|cyclic), T_C, soc, day, capacity_Ah, cycles."""
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

STUDY = sys.argv[1]
YT = sys.argv[2] if len(sys.argv) > 2 and os.path.exists(sys.argv[2]) else None
OUT = os.path.join(STUDY, "wp4", "outputs")
R, TREF, EA = 8.314462618, 298.15, 37.3e3
P2 = json.load(open(os.path.join(STUDY, "sources", "prior2_5c.json")))
LN3 = float(np.log(3.0))


def aT(T):
    return np.exp(-EA / R * (1.0 / (np.asarray(T, float) + 273.15) - 1.0 / TREF))


def cal_model(theta, tau):
    lab, ltb, lac = theta
    return np.exp(lab) * (1 - np.exp(-tau / np.exp(ltb))) + np.exp(lac) * np.sqrt(np.clip(tau, 0, None))


LB = np.log([1e-3, 0.5, 1e-4])
UB = np.log([50.0, 3000.0, 10.0])


def fit_cal(df):
    def res(th):
        return np.concatenate([(cal_model(th, g["tau"].to_numpy()) - g["loss"].to_numpy()) / np.sqrt(len(g))
                               for _, g in df.groupby("cell")])
    best = None
    for ab in (0.5, 3.0):
        for tb in (10.0, 100.0, 1000.0):
            for ac in (0.05, 0.3):
                x0 = np.clip(np.log([ab, tb, ac]), LB + 1e-6, UB - 1e-6)
                r = least_squares(res, x0, bounds=(LB, UB))
                if best is None or r.cost < best.cost:
                    best = r
    return best.x


out = {"sources": {}, "notes": []}
names = ["logA_b", "logtau_b", "logA_cal"]
if YT:
    y = pd.read_csv(YT)
    y["tau"] = y["day"] * aT(y["T_C"])
    y["loss"] = y.groupby("cell")["capacity_Ah"].transform(lambda c: 102.0 * (1 - c / c.iloc[0]))
    cal = y[y["kind"] == "calendar"].copy()
    th = fit_cal(cal)
    cells = sorted(cal["cell"].unique())
    jk = np.array([fit_cal(cal[cal["cell"] != c]) for c in cells])
    n = len(cells)
    jsd = np.sqrt((n - 1) / n * np.sum((jk - jk.mean(0)) ** 2, axis=0))
    out["calendar_fit"] = dict(zip(names, map(float, th)))
    out["calendar_jackknife_sd"] = dict(zip(names, map(float, jsd)))
    out["sources"]["calendar"] = f"Yagci 2025 storage cells (n = {n})"
    pd.DataFrame(jk, columns=names, index=cells).to_csv(os.path.join(OUT, "wp4_calendar_jackknife.csv"))
    for i, nm in enumerate(names):
        at_bound = bool(abs(th[i] - LB[i]) < 1e-3 or abs(th[i] - UB[i]) < 1e-3)
        unid = bool(jsd[i] > LN3)
        if at_bound or unid:
            out[nm] = dict(mean=P2[nm]["mean"], sd=P2[nm]["sd"], source="fallback: 5C prior2", at_bound=at_bound,
                           unidentified=unid)
        else:
            sd = max(jsd[i], 0.5) if nm == "logtau_b" else max(jsd[i], LN3)
            out[nm] = dict(mean=float(th[i]), sd=float(sd), source="Yagci 2025 storage cells")
else:
    out["notes"].append("Yagci unavailable: A_b, tau_b, A_cal from 5C prior2")
    for nm in names:
        out[nm] = dict(mean=P2[nm]["mean"], sd=P2[nm]["sd"], source="5C prior2 (Yagci unavailable)")

# ---------------------------------------------------------------- cycle term
thc = [out[nm]["mean"] for nm in names]
cyc = pd.read_csv(os.path.join(OUT, "wp4_cycling_axes.csv")).dropna(subset=["capacity_Ah"])
cyc["tau"] = cyc["days"] * aT(cyc["T_mean_C"])
cyc["ah"] = cyc["thr_Ah_102"] * aT(cyc["T_mean_C"])
cyc["loss"] = cyc["loss_Ah_102"]
sets = {d: g for d, g in cyc.groupby("dataset")}
if YT:
    yc = y[y["kind"] == "cyclic"].copy()
    yc["ah"] = yc["cycles"] * 2 * 180.0 * 102.0 / 180.0 * aT(yc["T_C"])
    for c, g in yc.groupby("cell"):
        sets[f"Yagci_cyc_{c}"] = g
acyc = {}
for d, g in sets.items():
    resid = g["loss"].to_numpy() - cal_model(thc, g["tau"].to_numpy())
    a = g["ah"].to_numpy()
    acyc[d] = float(max(np.sum(a * resid) / max(np.sum(a * a), 1e-12), 1e-12))
la = np.log(np.array(list(acyc.values())))
lodo = [np.median(np.delete(la, i)) for i in range(len(la))] if len(la) > 1 else [la[0]]
spread = float(np.max(np.abs(np.array(lodo) - np.median(la)))) if len(la) > 1 else LN3
out["A_cyc_by_dataset"] = acyc
out["logA_cyc"] = dict(mean=float(np.median(la)), sd=float(max(spread, LN3)), source="median over cycling datasets after subtracting the calendar prediction")
# registered fallback (fits.fallback, D4.3): a term that hits a bound (here the 1e-12 floor) or has spread > ln 3 -> prior2
cyc_bound = bool(np.median(la) <= np.log(1e-12) + 1e-3)
if cyc_bound or spread > LN3:
    out["logA_cyc_fit"] = out["logA_cyc"]
    out["logA_cyc"] = dict(mean=P2["logA_cyc"]["mean"], sd=P2["logA_cyc"]["sd"], source="fallback: 5C prior2",
                           at_bound=cyc_bound, unidentified=bool(spread > LN3))
out["Ea_kJ"] = 37.3
out["units"] = "loss in Ah on a 102 Ah cell; tau Arrhenius-weighted days; ah Arrhenius-weighted Ah scaled to 102 Ah"
out["deviation"] = "cycling datasets use the cumulative mean cell temperature up to each capacity point for the Arrhenius weighting (approximation)"
json.dump(out, open(os.path.join(STUDY, "wp4", "prior3.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
