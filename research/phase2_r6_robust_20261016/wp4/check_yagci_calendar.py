"""WP4 diagnostic: prior2 vs prior3 calendar+break-in prediction on the Yagci storage cells (A_cyc = 0).
Usage: python3 -I check_yagci_calendar.py <study_dir>"""
import json
import os
import sys

import numpy as np
import pandas as pd

STUDY = sys.argv[1]
R, TREF, EA = 8.314462618, 298.15, 37.3e3
y = pd.read_csv(os.path.join(STUDY, "wp4", "outputs", "wp4_yagci_table.csv"))
y = y[y["kind"] == "calendar"].copy()
y["tau"] = y["day"] * np.exp(-EA / R * (1.0 / (y["T_C"] + 273.15) - 1.0 / TREF))
y["loss"] = y.groupby("cell")["capacity_Ah"].transform(lambda c: 102.0 * (1 - c / c.iloc[0]))


def pred(p, tau):
    return np.exp(p["logA_b"]["mean"]) * (1 - np.exp(-tau / np.exp(p["logtau_b"]["mean"]))) + np.exp(p["logA_cal"]["mean"]) * np.sqrt(tau)


P2 = json.load(open(os.path.join(STUDY, "sources", "prior2_5c.json")))
P3 = json.load(open(os.path.join(STUDY, "wp4", "prior3.json")))
y["pred_prior2"] = pred(P2, y["tau"])
y["pred_prior3"] = pred(P3, y["tau"])
y.to_csv(os.path.join(STUDY, "wp4", "outputs", "wp4_yagci_calendar_check.csv"), index=False)
z = y[y["checkup"] > 0]
g = z.groupby(["T_C", "checkup"])[["day", "tau", "loss", "pred_prior2", "pred_prior3"]].mean()
print(g.round(2).to_string())
for c in ("pred_prior2", "pred_prior3"):
    print(c, "MAE Ah", round(float((z[c] - z["loss"]).abs().mean()), 3), "bias Ah", round(float((z[c] - z["loss"]).mean()), 3))
