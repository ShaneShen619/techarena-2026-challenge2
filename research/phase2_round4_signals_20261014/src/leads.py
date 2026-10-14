"""Stage 7 leads (stage_7/protocol.json): SS with a free anchor-0 offset; start-corrected registration beta."""
import numpy as np

from common4 import H
import statespace as S
import registration as RG
from events import CELLS
from v2 import anchors_by_checkup, beta_a4, phase_diff, shrink


def ss_fixed(ctx, tau=8.0, beta=None, rw=0.02, sd_o=0.5):
    """Round-3 fit_predict plus one parameter o (level of the whole capacity path)."""
    fc, ck, k, eps = ctx["fc"], ctx["ck"], ctx["k"], ctx["eps"]
    st = ctx["steps"][ctx["step"]].dropna(subset=["step_mean"]).sort_values("t_cv_end")
    anc, mon = S.months(ctx["op"], fc, ck)
    if 0 not in mon:
        return H.Q_CK0, {}
    K = max(mon) + 1
    if beta is None:
        beta = beta_a4(fc, ctx["a4"][2.0], ck, k, 1.0, 1.0)
    i_s0, i_dl = 0, 1
    i25 = {m: 2 + (m - 1) for m in range(1, K)}
    i45 = {m: 2 + (K - 1) + m for m in range(K)}
    iA = {m: 2 + (K - 1) + K + m for m in range(K)}
    i_o = 2 + (K - 1) + 2 * K
    P = i_o + 1
    rows, ys, ws = [], [], []

    def qrow(t):
        d25, d45 = S.regime_days(mon, t)
        r = np.zeros(P)
        for m in range(1, K):
            r[i25[m]] = d25[m]
        for m in range(K):
            r[i45[m]] = d45[m]
        r[i_o] = 1.0
        return r

    for m in range(1, K):
        if m in anc:
            rows.append(qrow(anc[m]["t_end"]))
            ys.append(anc[m]["Q_Ah"] + eps - H.Q_CK0)
            ws.append(1 / S.SD_ANCHOR ** 2)
    for _, s in st.iterrows():
        m = max([mm for mm, (t0, _, t1) in mon.items() if s["t_cv_end"] >= t0 and (t1 is None or s["t_cv_end"] < t1)],
                default=None)
        if m is None:
            continue
        r = qrow(s["t_cv_end"]) / beta
        r[i_s0] = 1.0
        r[i_dl] = 1.0 if s["setpoint_C"] == 45 else 0.0
        r[iA[m]] = np.exp(-S._d(s["t_cv_end"], mon[m][0]) / tau)
        rows.append(r)
        ys.append(s["step_mean"])
        ws.append(1 / S.SD_STEP ** 2)

    def prior(idx, mean, sd, minus=None):
        r = np.zeros(P)
        r[idx] = 1.0
        if minus is not None:
            r[minus] = -1.0
        rows.append(r)
        ys.append(mean)
        ws.append(1 / sd ** 2)

    prior(i_s0, 30.0, 10.0)
    prior(i_dl, 0.18, 0.1)
    for m in range(K):
        prior(iA[m], 0.0, 0.5)
    prior(i45[0], -0.05, 0.1)
    for m in range(1, K):
        prior(i45[m], 0.0, rw, minus=i45[m - 1])
    if K > 1:
        prior(i25[1], -0.05, 0.1)
    for m in range(2, K):
        prior(i25[m], 0.0, rw, minus=i25[m - 1])
    prior(i_o, 0.0, sd_o)
    X, y, w = np.array(rows), np.array(ys), np.array(ws)
    A = X.T @ (X * w[:, None])
    cov = np.linalg.inv(A)
    th = cov @ (X.T @ (w * y))
    c = qrow(ctx["at_date"])
    return H.Q_CK0 + float(c @ th), dict(pred_sd=float(np.sqrt(c @ cov @ c)), o_fit=float(th[i_o]), beta=beta)


def beta_startcorr(ctx, tau=1.0):
    fc, ck, k = ctx["fc"], ctx["ck"], ctx["k"]
    anc, reg = RG.anchor_registrations(ctx["op"], fc, ctx["a4"][2.0], ck, "V", "full")
    js = [j for j in range(2, k) if j in reg]
    if 1 not in anc or len(js) < 3:
        return 1.0, dict(c=np.nan, n=len(js))
    v1 = float(np.mean([anc[1][f"start_{c}"] for c in CELLS]))
    p1 = float(np.mean([c["p1"] for c in reg[js[0]]]))
    dv = np.array([float(np.mean([anc[j][f"start_{c}"] for c in CELLS])) - v1 for j in js])
    db = np.array([float(np.mean([c["bottom"] for c in reg[j]])) - p1 for j in js])
    dq = np.array([anc[j]["Q_Ah"] - anc[1]["Q_Ah"] for j in js])
    cc = float((dv * db).sum() / (dv ** 2).sum()) if (dv ** 2).sum() > 0 else 0.0
    dbc = db - cc * dv
    pairs = list(zip(dq - dbc, dq))
    if tau <= 0:
        x, q = np.array(pairs).T
        return float((x * q).sum() / (x ** 2).sum()), dict(c=cc, n=len(js))
    return shrink(pairs, 1.0, tau), dict(c=cc, n=len(js))


def v2_startcorr(ctx, tau=1.0):
    q, info = H.v2_pred(ctx)
    if info["branch"] != "phase":
        return q, dict(info, beta_sc=np.nan)
    b, inf = beta_startcorr(ctx, tau)
    anc = anchors_by_checkup(ctx["fc"], ctx["ck"])
    x = phase_diff(ctx["steps"][ctx["step"]], anc, ctx["ck"], ctx["k"], 10.0, True)
    return float(anc[ctx["k"] - 1]["Q_Ah"] + ctx["eps"] + b * x), dict(info, beta_sc=b, **inf)
