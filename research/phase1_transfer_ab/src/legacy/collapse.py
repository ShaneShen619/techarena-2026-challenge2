# -*- coding: utf-8 -*-
"""Time-scale collapse master curve.

    SOH(n) = s0 - a * pow_term(t) - b * hinge_n(t; w),     t = n / tau

The hinge is NORMALISED so that hinge_n(0, w) == 0, which makes ``s0`` the
model's SOH at cycle 0 instead of an arbitrary offset.  The raw hinge is
negative before the knee (lower bound -w/2), so with the raw form ``s0`` and
the pre-knee bias are entangled.
"""
import numpy as np
from scipy.optimize import least_squares

__all__ = ["hinge_raw", "hinge0", "hinge_n", "pow_term", "master",
           "fit_master", "fit_tau", "cross", "s0_from_early",
           "logdens_weights", "SHAPE_NAMES"]

SHAPE_NAMES = ("s0", "a", "p", "b", "w")


def hinge_raw(t, w):
    """Original C1-smooth hinge; hinge_raw(1, w) == 0 but hinge_raw(0, w) < 0."""
    return 0.5 * ((t - 1.0) + np.sqrt((t - 1.0) ** 2 + w ** 2) - w)


def hinge0(w):
    """Value of the raw hinge at t = 0 (closed form)."""
    return 0.5 * (-1.0 + np.sqrt(1.0 + w ** 2) - w)


def hinge_n(t, w):
    """Normalised hinge: 0 at t=0, still ~0 before the knee, slope->1 after."""
    return hinge_raw(t, w) - hinge0(w)


def pow_term(t, p, eps=0.0):
    """Sub-linear early fade.  eps>0 removes the infinite slope at t=0."""
    tt = np.clip(t, 0.0, None)
    if eps > 0.0:
        return (tt + eps) ** p - eps ** p
    return np.clip(tt, 1e-12, None) ** p


def master(shape, t, normalized=True, eps=0.0):
    """shape = (s0, a, p, b, w)."""
    s0, a, p, b, w = shape
    h = hinge_n(t, w) if normalized else hinge_raw(t, w)
    return s0 - a * pow_term(t, p, eps) - b * h


# --------------------------------------------------------------------------
def s0_from_early(x, y, lo=2, hi=10):
    """Robust initial SOH: median over cycles [lo, hi] (skips cycle 1 and the
    break-in peak).  Falls back to the first few available points."""
    m = (x >= lo) & (x <= hi)
    if m.sum() >= 2:
        return float(np.median(y[m]))
    k = min(5, len(y))
    return float(np.median(y[:k])) if k else np.nan


def logdens_weights(x, tau=None, n_bins=24, lo=-4.0, hi=0.3):
    """Inverse sqrt-density weights in log10 of relative cycle position.

    Raw cycling data is uniform in cycle number, so mid-life is represented by
    an order of magnitude more points than the first 1% of life.  An
    unweighted least-squares fit therefore buys bulk accuracy by sacrificing
    the head of the curve (measured: -0.9 pp bias at t < 0.01).  These weights
    give every decade of lifetime comparable pull.

    The reference scale is max(x), not tau, on purpose: making the weights
    independent of the fitted tau keeps the objective identical across model
    variants, so their RMSEs stay comparable (with a tau-based scale, adding
    a constraint silently changes the objective as well).
    """
    ref = float(tau) if tau is not None else float(np.max(x))
    t = np.log10(np.clip(np.asarray(x, float) / max(ref, 1e-9), 1e-6, None))
    edges = np.linspace(lo, hi, n_bins + 1)
    idx = np.clip(np.digitize(t, edges) - 1, 0, n_bins - 1)
    cnt = np.bincount(idx, minlength=n_bins).astype(float)
    cnt[cnt == 0] = 1.0
    w = 1.0 / np.sqrt(cnt[idx])
    return w / w.mean()


def fit_master(curves, tau0=None, normalized=True, fit_eps=False, s0_init=102.7,
               s0_bounds=(90.0, 110.0), weights=None, reweight=True, fix=None,
               soft_prior=None, prior_strength=0.0):
    """curves: list of (x, y).  Returns (shape5, tau_n, rmse, r2, eps).

    reweight=True runs an unweighted pass first, then refits with
    log-density weights derived from that pass's tau (see logdens_weights).

    fix: dict of shape params to hold constant, e.g. {"a": 16.8, "p": 0.41,
    "w": 0.32} to transfer a frozen shape and re-estimate only s0 / b / tau.
    """
    fix = dict(fix or {})
    soft_prior = dict(soft_prior or {})
    prior_strength = float(prior_strength)

    if prior_strength < 0:
        raise ValueError("prior_strength must be >= 0")
    n = len(curves)
    if tau0 is None:
        tau0 = np.array([x[len(x) // 2] for x, y in curves], float)
    if weights is None and reweight:
        weights = [logdens_weights(x) for x, _ in curves]
    if weights is None:
        weights = [np.ones_like(y) for _, y in curves]
    n_extra = 1 if fit_eps else 0
    free = [k for k in SHAPE_NAMES if k not in fix]
    n_free = len(free)
    prior_keys = [
        k for k in soft_prior
        if k in SHAPE_NAMES and k not in fix
    ]

    n_obs = sum(len(y) for _, y in curves)

    def unpack(th):
        shape = [fix[k] if k in fix else th[free.index(k)] for k in SHAPE_NAMES]
        eps = np.exp(th[n_free]) if fit_eps else 0.0
        tau = np.exp(th[n_free + n_extra:])
        return np.asarray(shape, float), eps, tau
    
    def resid(th):
        shape, eps, tau = unpack(th)

        data_resid = np.concatenate([
            weights[i] * (y - master(shape, x / tau[i], normalized, eps))
            for i, (x, y) in enumerate(curves)
        ])

        # No prior -> exactly the original objective.
        if prior_strength <= 0.0 or not prior_keys:
            return data_resid

        prior_resid = []

        for k in prior_keys:
            mu = float(soft_prior[k])
            value = shape[SHAPE_NAMES.index(k)]

            # Relative deviation makes parameters with different units/scales
            # comparable (e.g. a ~ 14 while p ~ 0.34).
            scale = max(abs(mu), 1e-12)

            prior_resid.append(
                np.sqrt(n_obs * prior_strength)
                * (value - mu)
                / scale
            )

        return np.concatenate([
            data_resid,
            np.asarray(prior_resid, float),
        ])
    
    _init = dict(zip(
        SHAPE_NAMES,
        [s0_init, 8.0, 0.7, 25.0, 0.2]
    ))

    _lo = dict(zip(
        SHAPE_NAMES,
        [s0_bounds[0], 1e-2, 0.1, 0.0, 1e-2]
    ))

    _hi = dict(zip(
        SHAPE_NAMES,
        [s0_bounds[1], 80.0, 2.5, 400.0, 3.0]
    ))

    th0 = [_init[k] for k in free]
    lo = [_lo[k] for k in free]
    hi = [_hi[k] for k in free]

    if fit_eps:
        th0 += [np.log(1e-3)]
        lo += [np.log(1e-8)]
        hi += [np.log(1.0)]

    th0 = np.concatenate([
        th0,
        np.log(tau0),
    ])

    lo = lo + [np.log(20.0)] * n
    hi = hi + [np.log(5e5)] * n

    r = least_squares(
        resid,
        th0,
        bounds=(lo, hi),
        max_nfev=300000,
    )

    shape, eps, tau = unpack(r.x)

    # Report ONLY the real data error, not the prior penalty.
    res = np.concatenate([
        y - master(
            shape,
            x / tau[i],
            normalized,
            eps,
        )
        for i, (x, y) in enumerate(curves)
    ])

    allY = np.concatenate([
        y for _, y in curves
    ])

    rss = float(np.sum(res ** 2))
    rmse = float(np.sqrt(rss / len(res)))

    r2 = 1.0 - rss / float(
        np.sum((allY - allY.mean()) ** 2)
    )

    return np.asarray(shape), tau, rmse, r2, eps


def fit_tau(shape, x, y, normalized=True, eps=0.0, n_starts=12, loss="huber",
            f_scale=0.5, tau_bounds=(20.0, 5e5), weights=None):
    """Shape frozen -> estimate a single tau for one curve.  Multi-start."""
    if len(x) < 4:
        return np.nan
    w = np.ones_like(y) if weights is None else np.asarray(weights, float)

    def resid(lt):
        return w * (y - master(shape, x / np.exp(lt[0]), normalized, eps))

    lo, hi = np.log(tau_bounds[0]), np.log(tau_bounds[1])
    guess = max(float(np.max(x)), 50.0)
    starts = np.log(np.clip(guess * np.logspace(-1.0, 1.0, n_starts),
                            tau_bounds[0], tau_bounds[1]))
    best, best_cost = np.nan, np.inf
    for lt0 in starts:
        try:
            r = least_squares(resid, [float(lt0)], bounds=([lo], [hi]),
                              loss=loss, f_scale=f_scale, max_nfev=20000)
        except Exception:
            continue
        if r.cost < best_cost:
            best_cost, best = float(r.cost), float(np.exp(r.x[0]))
    return best


def cross(x, y, th):
    """First cycle where the curve crosses down through th (interpolated)."""
    i = np.where(y <= th)[0]
    if len(i) == 0 or i[0] == 0:
        return np.nan
    j = i[0]
    return float(np.interp(th, [y[j], y[j - 1]], [x[j], x[j - 1]]))
