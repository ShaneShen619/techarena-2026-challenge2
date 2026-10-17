"""Residual rules copied from round 8 (wp2/run_wp2.py::add_residuals R_seg rule, wp5/run_wp5.py::r_anc_b), generalised to
any depth column. Diagnostic (full data)."""
import numpy as np
import pandas as pd

from v2 import theil_sen


def r_seg(df, col, group=("segment", "unit")):
    """col minus a leave-one-out Theil-Sen line in time (t_days) over the other rows of the same group; NaN if < 3 others."""
    out = pd.Series(np.nan, index=df.index)
    for _, g in df.groupby(list(group)):
        for i in g.index:
            o = g.drop(index=i)
            o = o[np.isfinite(o[col])]
            if len(o) < 3 or not np.isfinite(g.loc[i, col]):
                continue
            b = theil_sen(o["t_days"], o[col])
            a = float(np.median(o[col] - b * o["t_days"]))
            out[i] = g.loc[i, col] - (a + b * g.loc[i, "t_days"])
    return out


def r_anc_b(df, col):
    """Leave-month-out OLS col = a_25*I25 + a_45*I45 + b*Q_interp (rows with Q_interp only)."""
    out = pd.Series(np.nan, index=df.index)
    g = df[df["Q_interp_Ah"].notna() & np.isfinite(df[col])]
    for i in g.index:
        o = g[g["month"] != g.loc[i, "month"]]
        X = np.column_stack([(o.setpoint == 25).astype(float), (o.setpoint == 45).astype(float), o["Q_interp_Ah"]])
        coef = np.linalg.lstsq(X, o[col].to_numpy(float), rcond=None)[0]
        x = np.array([g.loc[i, "setpoint"] == 25, g.loc[i, "setpoint"] == 45, g.loc[i, "Q_interp_Ah"]], float)
        out[i] = g.loc[i, col] - x @ coef
    return out


def robust_sd(x):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return float(1.4826 * np.median(np.abs(x - np.median(x))))
