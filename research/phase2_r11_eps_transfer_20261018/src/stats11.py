"""Registered statistics (wp1/protocol.json): Theil-Sen/OLS slopes, leave-one-out ranges, BIC model comparison, flags."""
import numpy as np
from scipy import stats


def slopes(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    ts = float(stats.theilslopes(y, x)[0]); ols = float(np.polyfit(x, y, 1)[0])
    loo_ts, loo_ols = [], []
    for i in range(len(x)):
        m = np.arange(len(x)) != i
        loo_ts.append(float(stats.theilslopes(y[m], x[m])[0])); loo_ols.append(float(np.polyfit(x[m], y[m], 1)[0]))
    return dict(theil_sen=ts, ols=ols, loo_ts=[min(loo_ts), max(loo_ts)], loo_ols=[min(loo_ols), max(loo_ols)], n=len(x))


def _bic(rss, n, p):
    return float(n * np.log(max(rss, 1e-12) / n) + p * np.log(n))


def bic_models(x, y, step_after=None, steps2=None):
    """(a) linear; (b) constant + step; (c) linear + step; (b2) two steps (sensitivity). step_after: indicator array."""
    x, y = np.asarray(x, float), np.asarray(y, float); n = len(x); out = {}
    A = np.c_[np.ones(n), x]; c, *_ = np.linalg.lstsq(A, y, rcond=None); out["a"] = dict(bic=_bic(((y - A @ c) ** 2).sum(), n, 2), coef=c.tolist())
    if step_after is not None:
        s = np.asarray(step_after, float)
        B = np.c_[np.ones(n), s]; c, *_ = np.linalg.lstsq(B, y, rcond=None); out["b"] = dict(bic=_bic(((y - B @ c) ** 2).sum(), n, 2), coef=c.tolist())
        C = np.c_[np.ones(n), x, s]; c, *_ = np.linalg.lstsq(C, y, rcond=None); out["c"] = dict(bic=_bic(((y - C @ c) ** 2).sum(), n, 3), coef=c.tolist(),
                                                                                              slope=float(c[1]), step=float(c[2]))
    if steps2 is not None:
        D = np.c_[np.ones(n)] if False else np.c_[np.ones(n), np.asarray(steps2, float)]
        c, *_ = np.linalg.lstsq(D, y, rcond=None); out["b2"] = dict(bic=_bic(((y - D @ c) ** 2).sum(), n, D.shape[1]), coef=c.tolist())
    win = "a"
    if "b" in out:
        best = min(("b", "c"), key=lambda m: out[m]["bic"])
        if out[best]["bic"] < out["a"]["bic"] - 2:
            win = best
    out["winner"] = win
    return out


def transfer_slope(x, y, bic):
    w = bic["winner"]
    if w == "a":
        return float(stats.theilslopes(y, x)[0])
    if w == "c":
        return bic["c"]["slope"]
    return 0.0


def mad_flags(v):
    v = np.asarray(v, float); med = np.median(v); mad = np.median(np.abs(v - med))
    if mad == 0:
        return np.abs(v - med) > 0.01 * abs(med)
    return np.abs(v - med) > 3 * mad
