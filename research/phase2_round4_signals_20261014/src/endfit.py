"""Stage 1: month-end value from a robust line over the month's 45 C steps (stage_1/protocol.json)."""
import numpy as np

from common4 import H
from v2 import anchors_by_checkup, beta_a4, end45, month_steps, theil_sen


def _days(a, b):
    return (a - b).total_seconds() / 86400.0


def month_line(st, anc, ck, m, method="ts", last3=False):
    s = month_steps(st, anc, m)
    s = s[(s["setpoint_C"] == 45) & s["step_mean"].notna()].sort_values("t_cv_end")
    if len(s) < 3:
        return None
    if last3:
        s = s.iloc[-3:]
    t0 = s["t_cv_end"].iloc[0]
    t = np.array([_days(x, t0) for x in s["t_cv_end"]])
    y = s["step_mean"].to_numpy(float)
    if method == "ols":
        slope, b = np.polyfit(t, y, 1)
    else:
        slope = theil_sen(t, y)
        b = float(np.median(y - slope * t))
    res = y - (b + slope * t)
    return dict(L_ck=float(b + slope * _days(ck[m + 1], t0)), L_last=float(b + slope * t[-1]),
                slope=float(slope), resid_sd=float(np.std(res, ddof=1)) if len(y) > 2 else np.nan, n=len(y))


def pred(ctx, method="ts", last3=False, at_last_plus_rate=False, beta_one=False):
    q, info = H.v2_pred(ctx)
    if info["branch"] != "phase":
        return q, dict(info, s1_branch="fallback")
    fc, ck, k = ctx["fc"], ctx["ck"], ctx["k"]
    st = ctx["steps"][ctx["step"]].dropna(subset=["step_mean"])
    anc = anchors_by_checkup(fc, ck)
    prev = month_line(st, anc, ck, k - 2, method, last3)
    cur = month_line(st, anc, ck, k - 1, method, last3)
    e_cur, e_prev = end45(st, anc, ck, k - 1), end45(st, anc, ck, k - 2)
    beta = 1.0 if beta_one else beta_a4(fc, ctx["a4"][ctx["a4s"]], ck, k, 1.0, 1.0)
    if at_last_plus_rate:
        r = e_cur["r"] if e_cur["n"] >= 3 else 0.0
        c = cur["L_last"] if cur else e_cur["E"]
        x = c - prev["L_last"] + r * (e_cur["d"] - e_prev["d"])
    else:
        c = cur["L_ck"] if cur else e_cur["E"]
        x = c - prev["L_ck"]
    q1 = anc[k - 1]["Q_Ah"] + ctx["eps"] + beta * x
    return float(q1), dict(info, s1_branch="phase", s1_beta=beta,
                           slope_cur=cur["slope"] if cur else np.nan, slope_prev=prev["slope"],
                           sd_cur=cur["resid_sd"] if cur else np.nan, sd_prev=prev["resid_sd"],
                           n_cur=cur["n"] if cur else e_cur["n"])
