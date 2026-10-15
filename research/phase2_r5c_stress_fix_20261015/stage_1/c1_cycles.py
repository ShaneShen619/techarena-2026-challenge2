"""Per-cycle summaries of the six Challenge 1 cells (read only), cached in the study cache."""
import glob
import os
import pickle
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
CACHE = os.path.join(STUDY, "cache")
C1_DIR = "/Users/shane/Desktop/Arena 阶段 2 官方材料/dataset original"
CELLS = ["102Ah_25degC_0p5C_cell3", "102Ah_25degC_1C_cell3", "102Ah_35degC_1C_cell1",
         "102Ah_45degC_0p5C_cell3", "102Ah_45degC_1C_cell1", "102Ah_55degC_1C_cell3"]
NOM = 102.0
COLS = ["cycle_number", "step_type", "time_in_cycle_s", "temperature_C", "step_capacity_Ah",
        "absolute_time"]


def _labels(qv):
    """Challenge 1 framework label rule (re-implemented; framework/data.py::_derive_soh)."""
    qv = qv.astype(float)
    implaus = (qv > 1.15 * NOM) | (qv < 0)
    med = qv.shift(1).rolling(15, min_periods=3).median().fillna(qv.rolling(9, center=True, min_periods=1).median())
    partial = (qv < 0.6 * med) & ~implaus
    return np.where(~implaus & ~partial, qv, np.nan)


def cycle_summary(cell):
    path = os.path.join(CACHE, f"c1_{cell}.pkl")
    if os.path.exists(path):
        return pickle.load(open(path, "rb"))
    files = sorted(glob.glob(os.path.join(C1_DIR, cell, "*_time_series_part*.csv")))
    parts = []
    for f in files:
        d = pd.read_csv(f, usecols=COLS)
        d["absolute_time"] = pd.to_datetime(d["absolute_time"])
        parts.append(d)
    ts = pd.concat(parts, ignore_index=True)
    ts = ts.sort_values(["absolute_time"], kind="stable").reset_index(drop=True)
    g = ts.groupby("cycle_number", sort=True)
    t0 = g["absolute_time"].min()
    t1 = g["absolute_time"].max()
    # time-weighted temperature: weight rows by the time to the next row within the cycle
    ts["dt"] = ts.groupby("cycle_number")["absolute_time"].diff(-1).dt.total_seconds().abs()
    ts["dt"] = ts["dt"].fillna(0).clip(upper=600)
    ts["Tdt"] = ts["temperature_C"] * ts["dt"]
    tw = g["Tdt"].sum() / g["dt"].sum().replace(0, np.nan)
    tw = tw.fillna(g["temperature_C"].mean())
    chg = ts[ts["step_type"] == "cccv_charge"].groupby("cycle_number")["step_capacity_Ah"].max()
    dis = ts[ts["step_type"] == "cc_discharge"].groupby("cycle_number")["step_capacity_Ah"].max()
    out = pd.DataFrame({"t0": t0, "t1": t1, "T": tw}).join(chg.rename("q_chg")).join(dis.rename("q_dis"))
    out = out.reset_index()
    out["q_lab"] = _labels(out["q_dis"].fillna(-1.0))
    out.loc[out["q_dis"].isna(), "q_lab"] = np.nan
    out["thr"] = out["q_chg"].fillna(0).clip(lower=0, upper=1.15 * NOM) + out["q_dis"].fillna(0).clip(lower=0, upper=1.15 * NOM)
    os.makedirs(CACHE, exist_ok=True)
    pickle.dump(out, open(path, "wb"))
    return out


if __name__ == "__main__":
    for c in CELLS:
        s = cycle_summary(c)
        days = (s["t1"].max() - s["t0"].min()).total_seconds() / 86400
        print(c, len(s), "cycles", round(days, 1), "days", "T", round(s["T"].median(), 1),
              "thr/cyc", round(s["thr"].median(), 1), "labels", int(s["q_lab"].notna().sum()),
              "q2-10", round(s.loc[s.cycle_number.between(2, 10), "q_lab"].median(), 2))
        sys.stdout.flush()
