"""Registered statistics (round 14 WP1): Theil-Sen slope against fade, leave-one-anchor-out (LOO) range, slope against
days since CK0, BIC of constant vs linear-in-fade, 3-MAD outlier flags and the registered sensitivities."""
import numpy as np

E_SCALE_AH = 8.2      # E = d * 8.2 Ah, the effect at CK7
MIN_POINTS = 5        # d needs at least 5 points
MIN_POINTS_SENS = 3   # sensitivity fits are reported (with n) from 3 points; they decide nothing
OUTLIER_K = 3.0       # flag |r - median(r)| > 3 * MAD(r) (raw MAD of the Theil-Sen residuals)


def theil_sen(x, y):
    """Median of pairwise slopes, pairs with equal x skipped (as the package's _theil_sen)."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    i, j = np.triu_indices(len(x), 1)
    dx = x[j] - x[i]
    ok = dx != 0
    return float(np.median((y[j] - y[i])[ok] / dx[ok])) if ok.any() else np.nan


def ts_fit(x, y):
    """(slope, intercept = median(y - slope * x))."""
    b = theil_sen(x, y)
    return b, float(np.median(np.asarray(y, float) - b * np.asarray(x, float)))


def loo(x, y, labels):
    """LOO Theil-Sen slopes {label: slope} dropping one point at a time."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    out = {}
    for m, lab in enumerate(labels):
        keep = np.arange(len(x)) != m
        out[lab] = theil_sen(x[keep], y[keep])
    return out


def bic_const_vs_linear(x, y):
    """Gaussian BIC with OLS fits: BIC = n ln(RSS/n) + k ln(n); k = 2 (mean, variance) for (a), 3 for (b).
    Returns (BIC_a, BIC_b, dBIC = BIC_a - BIC_b); dBIC >= 2 means BIC prefers (b) by the registered margin."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    n = len(y)
    rss_a = float(((y - y.mean()) ** 2).sum())
    A = np.c_[np.ones(n), x]
    coef = np.linalg.lstsq(A, y, rcond=None)[0]
    rss_b = float(((y - A @ coef) ** 2).sum())
    tiny = 1e-12  # guards ln(0) for an exact fit
    bic_a = n * np.log(max(rss_a, tiny) / n) + 2 * np.log(n)
    bic_b = n * np.log(max(rss_b, tiny) / n) + 3 * np.log(n)
    return float(bic_a), float(bic_b), float(bic_a - bic_b)


def outlier_flags(x, y):
    """Points whose Theil-Sen residual deviates from the median residual by more than 3 raw MADs (none if MAD = 0)."""
    b, a = ts_fit(x, y)
    r = np.asarray(y, float) - (a + b * np.asarray(x, float))
    dev = np.abs(r - np.median(r))
    m = float(np.median(dev))
    return (dev > OUTLIER_K * m) if m > 0 else np.zeros(len(r), bool), r


def _slope_block(x, y, labels, min_points):
    n = len(y)
    if n < min_points:
        return {"n": n, "estimable": False}
    b, a = ts_fit(x, y)
    lo = loo(x, y, labels)
    vals = np.array(list(lo.values()))
    return {"n": n, "estimable": True, "d": b, "intercept": a, "E": b * E_SCALE_AH,
            "loo": lo, "loo_range_d": [float(vals.min()), float(vals.max())],
            "loo_range_E": [float(vals.min() * E_SCALE_AH), float(vals.max() * E_SCALE_AH)],
            "loo_width_E": float((vals.max() - vals.min()) * E_SCALE_AH)}


def analyze(labels, fade, days, y, drop_for_sensitivity=(3,)):
    """Full registered statistics for one signal. labels: anchor ids k; fade, days, y aligned arrays (finite only)."""
    labels = list(labels); fade = np.asarray(fade, float); days = np.asarray(days, float); y = np.asarray(y, float)
    res = {"labels": labels, "main": _slope_block(fade, y, labels, MIN_POINTS)}
    if not res["main"]["estimable"]:
        return res
    res["days"] = _slope_block(days, y, labels, MIN_POINTS)
    bic_a, bic_b, dbic = bic_const_vs_linear(fade, y)
    res["bic"] = {"bic_const": bic_a, "bic_linear": bic_b, "dBIC_const_minus_linear": dbic}
    flags, resid = outlier_flags(fade, y)
    res["residuals"] = dict(zip(labels, map(float, resid)))
    res["outliers"] = [lab for lab, f in zip(labels, flags) if f]
    sens = {}
    if res["outliers"]:
        keep = ~flags
        sens["without_outliers"] = _slope_block(fade[keep], y[keep], [l for l, k in zip(labels, keep) if k],
                                                MIN_POINTS_SENS)
    for k in drop_for_sensitivity:
        if k in labels:
            keep = np.array([lab != k for lab in labels])
            sens[f"without_anchor_{k}"] = _slope_block(fade[keep], y[keep], [l for l in labels if l != k],
                                                       MIN_POINTS_SENS)
        else:
            sens[f"without_anchor_{k}"] = {"same_as_main": True, "note": f"anchor {k} not in the set"}
    res["sensitivity"] = sens
    return res
