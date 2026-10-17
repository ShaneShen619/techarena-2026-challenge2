"""Instrumented replay of SUB (T_main), V2+sqrt(t) and V2 for the case table (WP1).

``decompose(ctx, model)`` follows the branch logic of v3.v3 / tsqrt.design_pred step by step on the same cut
tables and returns the prediction together with its anchor term, increment and branch internals. The caller
asserts that Q_pred equals the model's own output.
"""
import numpy as np
import pandas as pd

from common8 import H
from events import iter_segments
from v2 import Q_CK0, anchors_by_checkup, beta_a4, end45, month_steps, phase_diff, theil_sen
from v3 import coverage_gap_days, v3
import tsqrt as T

MODELS = ("SUB", "V2_sqrt", "V2")
TMAIN = T.DESIGNS["T_main"]
P_EXP = 0.5
GAP_DAYS = 10.0
VALID_DAYS = 10.0
BETA0, TAU = 1.0, 1.0


def model_q(ctx, model):
    """The models' own outputs (research implementations)."""
    a = (ctx["fc"], ctx["steps"][ctx["step"]], ctx["a4"][ctx["a4s"]], ctx["ck"], ctx["k"], ctx["eps"])
    if model == "SUB":
        return T.design_pred("T_main")(ctx)[0]
    if model == "V2_sqrt":
        return v3(*a, use_sqrt=True, beta_cap=float("inf"), median=False)[0]
    return v3(*a, use_sqrt=False, beta_cap=float("inf"), median=False)[0]


def beta_internals(fc, a4, ck, k):
    """beta_a4 with its pieces: (beta, b_raw, S = sum x^2, shrink weight S/(tau+S), n_pairs)."""
    anc = anchors_by_checkup(fc, ck)
    seg2j = {int(r["segment"]): j for j, r in anc.items()}
    t = {seg2j[int(r["segment"])]: r["step_to_top_mean"] for _, r in a4.iterrows() if int(r["segment"]) in seg2j}
    js = [j for j in range(1, k) if j in anc and j in t and anc[j]["setpoint_C"] == 25]
    beta = beta_a4(fc, a4, ck, k, BETA0, TAU)
    if len(js) < 2:
        return beta, np.nan, 0.0, 0.0, 0
    x = np.array([t[j] - t[js[0]] for j in js[1:]])
    q = np.array([anc[j]["Q_Ah"] - anc[js[0]]["Q_Ah"] for j in js[1:]])
    s = float((x ** 2).sum())
    b = float((x * q).sum() / s) if s > 0 else np.nan
    return beta, b, s, s / (TAU + s), len(js) - 1


def month45(st, anc, m):
    s = month_steps(st, anc, m)
    return s[(s["setpoint_C"] == 45) & s["step_mean"].notna()]


def checkup_index(ck, t):
    return int((ck < t).sum()) - 1


def decompose(ctx, model):
    fc, st, a4, op, ck, k, eps = (ctx["fc"], ctx["steps"][ctx["step"]], ctx["a4"][ctx["a4s"]], ctx["op"],
                                  ctx["ck"], ctx["k"], ctx["eps"])
    anc = anchors_by_checkup(fc, ck)
    gap = coverage_gap_days(st, ck, k)
    o = dict(gap_days=float(gap))
    beta, b_raw, s_sum, w, n_pairs = beta_internals(fc, a4, ck, k)
    o.update(beta_a4=beta, beta_raw=b_raw, beta_S=s_sum, beta_shrink_w=w, beta_n_pairs=n_pairs)
    if model in ("SUB", "V2_sqrt") and k >= 2 and (k - 1) in anc and gap > GAP_DAYS:
        j = k - 1
        js = [i for i in range(1, k) if i in anc]
        if model == "SUB":
            te = T.t_eff_days(op, ck[0], [ck[i] for i in js] + [ck[k - 1], ck[k]], TMAIN["Ea"], TMAIN["T_gap"],
                              TMAIN["T_seg3"])
        else:
            te = [(d - ck[0]).total_seconds() / 86400.0 for d in [ck[i] for i in js] + [ck[k - 1], ck[k]]]
        x = np.array(te[:len(js)]) ** P_EXP
        loss = np.array([Q_CK0 - (anc[i]["Q_Ah"] + eps) for i in js])
        a = float((x * loss).sum() / (x ** 2).sum())
        inc = -a * (te[-1] ** P_EXP - te[-2] ** P_EXP)
        o.update(branch="sqrt_gap", anchor_j=j, q_anchor_term=float(anc[j]["Q_Ah"] + eps), increment_pred=float(inc),
                 sqrt_a=a, sqrt_t_km1_days=float(te[-2]), sqrt_t_k_days=float(te[-1]),
                 sqrt_anchors="|".join(map(str, js)), beta_used=np.nan, n_after=np.nan)
        a_row = anc[j]
    else:
        x = phase_diff(st, anc, ck, k, VALID_DAYS, True) if (k - 1) in anc else None
        cur = end45(st, anc, ck, k - 1) if (k - 1) in anc else None
        prev = end45(st, anc, ck, k - 2) if (k >= 2 and (k - 2) in anc) else None
        for nm, e in (("cur", cur), ("prev", prev)):
            for f in ("E", "d", "n", "r"):
                o[f"{f}_{nm}"] = float(e[f]) if e is not None else np.nan
        if x is not None and anc[k - 1]["setpoint_C"] == 25:
            j = k - 1
            mc, mp = month45(st, anc, k - 1), month45(st, anc, k - 2)
            use_r = cur["n"] >= 3
            o.update(branch="phase", anchor_j=j, q_anchor_term=float(anc[j]["Q_Ah"] + eps),
                     increment_pred=float(beta * x), x=float(x), beta_used=float(beta), n_after=np.nan,
                     r_used=float(cur["r"]) if use_r else 0.0,
                     ev_E_cur=str(mc["t_cv_end"].iloc[-1]), ev_E_prev=str(mp["t_cv_end"].iloc[-1]),
                     ev_rate_fit="|".join(str(t) for t in mc["t_cv_end"]) if use_r else "")
            a_row = anc[j]
        else:
            last = fc.sort_values("t_end").iloc[-1]
            j = checkup_index(ck, last["t_end"])
            q = Q_CK0 if last["setpoint_C"] == 45 else last["Q_Ah"] + eps
            s = st.dropna(subset=["step_mean"])
            s = s[s["t_cv_end"] >= last["t_end"]].sort_values("t_cv_end")
            inc = float(s["step_mean"].iloc[-1] - s["step_mean"].iloc[0]) if len(s) else 0.0
            o.update(branch="fallback", anchor_j=j, q_anchor_term=float(q), increment_pred=inc, beta_used=1.0,
                     n_after=int(len(s)),
                     ev_after_first=str(s["t_cv_end"].iloc[0]) if len(s) else "",
                     ev_after_last=str(s["t_cv_end"].iloc[-1]) if len(s) else "")
            a_row = last
    o["anchor_t_end"] = a_row["t_end"]
    o["Q_fc_anchor_used"] = float(a_row["Q_Ah"])
    o["anchor_setpoint"] = int(a_row["setpoint_C"])
    o["Q_pred"] = float(o["q_anchor_term"] + o["increment_pred"])
    return o


# ------------------------------------------------------------------ context fields (cut data only)
_DIS = {}


def discharge_since(op, key, t0):
    """Integrated discharge Ah (|current_A| of negative samples) after t0 in the cut data."""
    if key not in _DIS:
        parts = []
        for _, g in iter_segments(op):
            t = g["elapsed_s"].to_numpy(float)
            i = g["current_A"].to_numpy(float)
            dt = np.diff(t, prepend=t[0])
            dt[(dt > 600) | (dt <= 0)] = 0.0
            parts.append(pd.DataFrame({"ts": g["timestamp"].to_numpy(), "dis": np.where(i < 0, -i, 0.0) * dt / 3600.0,
                                       "sp": g["chamber_temperature_C"].to_numpy(), "dt": dt}))
        _DIS[key] = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=["ts", "dis", "sp", "dt"])
    d = _DIS[key]
    sel = d["ts"] > t0
    return float(d.loc[sel, "dis"].sum()), float(d.loc[sel & (d["sp"] == 45), "dt"].sum() / 3600.0)


def context(ctx, o):
    op, ck, k = ctx["op"], ctx["ck"], ctx["k"]
    t0 = o["anchor_t_end"]
    days = (ck[k] - t0).total_seconds() / 86400.0
    te = T.t_eff_days(op, ck[0], [t0, ck[k]], TMAIN["Ea"], TMAIN["T_gap"], TMAIN["T_seg3"])
    grid, temp = T.hourly_temperature(op, t0.floor("h"), ck[k], TMAIN["T_gap"], TMAIN["T_seg3"])
    dis, h45 = discharge_since(op, ctx["key"], t0)
    return dict(days_anchor_to_ck=days, eff45_days_anchor_to_ck=te[1] - te[0],
                cum_fade_at_anchor_Ah=Q_CK0 - o["Q_fc_anchor_used"] - H.EPS0,
                throughput_dis_Ah_since_anchor=dis,
                share_45C_assigned=float((temp == 45.0).mean()) if len(temp) else np.nan,
                share_45C_visible=h45 / (days * 24.0) if days > 0 else np.nan)
