"""Read one Challenge 1 cell (read only) and summarise it per cycle.

Only structure (step types, times, currents, voltages) selects input cycles. The discharge
capacity label is computed here as well, but it is used only for label0 and for scoring.
"""
import glob
import os

import numpy as np
import pandas as pd

from .common import PROTOCOL

DATA = PROTOCOL["data"]
STEP = DATA["step_types"]
STRUCT = PROTOCOL["structure"]
NOMINAL_AH = DATA["nominal_ah"]


def cell_files(c1_dir, cell_id):
    """Time-series files of one cell, in part order (single file or *_partNN)."""
    folder = os.path.join(c1_dir, cell_id)
    for pattern in (f"{cell_id}_time_series.csv*", f"{cell_id}_time_series_part*.csv*",
                    "*_time_series*.csv*"):
        files = sorted(glob.glob(os.path.join(folder, pattern)))
        if files:
            return files
    raise FileNotFoundError(f"no time series for {cell_id} under {folder}")


def read_cell(c1_dir, cell_id):
    """All rows of one cell, sorted by time, duplicate step-transition rows removed."""
    parts = [pd.read_csv(f, usecols=DATA["columns"]) for f in cell_files(c1_dir, cell_id)]
    raw = pd.concat(parts, ignore_index=True)
    raw["absolute_time"] = pd.to_datetime(raw["absolute_time"])
    raw = raw.sort_values("absolute_time", kind="stable")
    raw = raw.drop_duplicates(DATA["dedup_keys"], keep="last").reset_index(drop=True)
    return raw


def framework_labels(q_dis):
    """Challenge 1 label rule (framework/data.py::_derive_soh), in Ah; NaN where no label."""
    qv = pd.Series(q_dis, dtype=float).reset_index(drop=True)
    implaus = (qv > 1.15 * NOMINAL_AH) | (qv < 0) | qv.isna()
    med = qv.shift(1).rolling(15, min_periods=3).median().fillna(
        qv.rolling(9, center=True, min_periods=1).median())
    partial = (qv < 0.6 * med) & ~implaus
    return np.where(~implaus & ~partial, qv, np.nan)


def cycle_summary(raw):
    """One row per cycle: charge and discharge step summaries, structural flags, label."""
    d = raw.assign(abs_i=raw["current_A"].abs())
    out = {}
    for name, kind in (("chg", STEP["charge"]), ("dis", STEP["discharge"])):
        s = d[d["step_type"] == kind]
        g = s.groupby("cycle_number", sort=True)
        cc = s[s["abs_i"] >= 0.9 * g["abs_i"].transform("max")].groupby("cycle_number")["abs_i"]
        out[name] = pd.DataFrame({
            f"{name}_t0": g["absolute_time"].min(),
            f"{name}_t1": g["absolute_time"].max(),
            f"{name}_q": g["step_capacity_Ah"].max(),
            f"{name}_vmax": g["voltage_V"].max(),
            f"{name}_vmin": g["voltage_V"].min(),
            f"{name}_v0": g["voltage_V"].first(),
            f"{name}_icc": cc.median(),
            f"{name}_iend": g["abs_i"].last(),
            f"{name}_n": g.size(),
        })
    temp = d.groupby("cycle_number", sort=True)["temperature_C"].mean().rename("T_mean")
    cyc = out["chg"].join(out["dis"], how="outer").join(temp, how="left").sort_index()
    cyc["label"] = framework_labels(cyc["dis_q"].to_numpy())
    return cyc


def structural_flags(cyc):
    """Input-side eligibility from structure only; thresholds from the reference period."""
    t_first = cyc["chg_t0"].min()
    ref = cyc[cyc["chg_t0"] < t_first + pd.Timedelta(days=STRUCT["reference_days"])]
    v_top = float(ref["chg_vmax"].median())
    v_empty = float(ref["chg_v0"].median())
    ordered = cyc["chg_t1"] < cyc["dis_t0"]
    cv_ok = ((cyc["chg_vmax"] >= v_top - STRUCT["cv_reached_margin_v"])
             & (cyc["chg_iend"] <= STRUCT["cv_end_current_frac_max"] * cyc["chg_icc"]))
    empty_ok = cyc["chg_v0"] <= v_empty + STRUCT["empty_start_margin_v"]
    deep = cyc["dis_q"] >= PROTOCOL["information_structure"]["visible_depth_ah"]
    first = cyc.index >= STRUCT["first_cycle_number"]
    flags = pd.DataFrame({
        "anchor_ok": cv_ok & empty_ok & first,
        "program_ok": cv_ok & ordered & deep & first,
    }, index=cyc.index).fillna(False)
    return flags, {"v_top_ref": v_top, "v_empty_ref": v_empty}


class CellRows:
    """Fast access to the rows of one cycle step."""

    def __init__(self, raw):
        self.raw = raw
        self.idx = raw.groupby(["cycle_number", "step_type"], sort=False).indices
        self.t = raw["absolute_time"].to_numpy()
        self.v = raw["voltage_V"].to_numpy(float)
        self.i = raw["current_A"].to_numpy(float)
        self.q = raw["step_capacity_Ah"].to_numpy(float)

    def step(self, cycle, kind):
        """(times, |current|, voltage, step capacity) of one step, in time order."""
        pos = np.sort(self.idx.get((cycle, kind), np.array([], int)))
        return self.t[pos], np.abs(self.i[pos]), self.v[pos], self.q[pos]

    def rest_voltage_before(self, cycle, t_start):
        """Last rest voltage of the cycle before t_start (NaN if none)."""
        pos = np.sort(self.idx.get((cycle, STEP["rest"]), np.array([], int)))
        pos = pos[self.t[pos] < t_start]
        return float(self.v[pos[-1]]) if len(pos) else np.nan
