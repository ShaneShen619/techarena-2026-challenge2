"""Registered slice statistics (wp5/protocol.json 'statistics'): effect, block-bootstrap CI, sign share,
within-stratum permutation p, verdict."""
import itertools
import math

import numpy as np
import pandas as pd


def bin_of(x, edges, labels):
    x = np.asarray(x, float)
    idx = np.searchsorted(np.asarray(edges, float), x, side="right")
    return np.where(np.isfinite(x), np.array(labels, dtype=object)[np.minimum(idx, len(labels) - 1)], None)


def effect_fn(hi, lo):
    """mean(y | lab in hi) - mean(y | lab in lo); hi/lo are sets of labels."""
    def f(y, lab):
        a, b = y[np.isin(lab, list(hi))], y[np.isin(lab, list(lo))]
        return float(a.mean() - b.mean()) if len(a) and len(b) else np.nan
    return f


def block_boot(d, stat, block, n_boot, seed):
    blocks = d[block].unique()
    groups = {b: d[d[block] == b] for b in blocks}
    rng = np.random.default_rng(seed)
    out, dropped = [], 0
    for _ in range(n_boot):
        pick = rng.choice(blocks, size=len(blocks), replace=True)
        v = stat(pd.concat([groups[b] for b in pick], ignore_index=True))
        if np.isfinite(v):
            out.append(v)
        else:
            dropped += 1
    if not out:
        return np.nan, np.nan, dropped
    lo, hi = np.percentile(out, [5, 95])
    return float(lo), float(hi), dropped


def perm_p(y, lab, strata, f, n_perm, seed, exact_max):
    y, lab, strata = np.asarray(y, float), np.asarray(lab, dtype=object), np.asarray(strata, dtype=object)
    obs = f(y, lab)
    if not np.isfinite(obs):
        return np.nan, "none"
    groups = [np.where(strata == s)[0] for s in pd.unique(strata)]
    if len(y) <= exact_max:
        perms = [list(itertools.permutations(g)) for g in groups]
        cnt = tot = 0
        for combo in itertools.product(*perms):
            l2 = lab.copy()
            for g, pg in zip(groups, combo):
                l2[g] = lab[list(pg)]
            v = f(y, l2)
            if np.isfinite(v):
                tot += 1
                cnt += abs(v) >= abs(obs) - 1e-12
        return (cnt / tot if tot else np.nan), "exact"
    rng = np.random.default_rng(seed)
    cnt = tot = 0
    for _ in range(n_perm):
        l2 = lab.copy()
        for g in groups:
            l2[g] = lab[rng.permutation(g)]
        v = f(y, l2)
        if np.isfinite(v):
            tot += 1
            cnt += abs(v) >= abs(obs) - 1e-12
    return ((cnt + 1) / (tot + 1) if tot else np.nan), f"mc{n_perm}"


def sign_share(d, ycol, labcol, xcol, block, f, expected, orient):
    """Registered sign share. orient = +1 if the 'hi' group corresponds to larger x, else -1."""
    varies = d.groupby(block)[xcol].nunique().max() > 1
    agree = n = 0
    if varies:
        for _, g in d.groupby(block):
            if g[xcol].nunique() < 2:
                continue
            v = f(g[ycol].to_numpy(float), g[labcol].to_numpy(object))
            if not np.isfinite(v):
                x, y = g[xcol].to_numpy(float), g[ycol].to_numpy(float)
                if np.ptp(x) == 0:
                    continue
                v = orient * np.polyfit(x, y, 1)[0]
            n += 1
            agree += np.sign(v) == expected
        return agree, n, "within_block"
    bm = d.groupby(block).agg(y=(ycol, "mean"), x=(xcol, "mean"))
    mx, my = bm["x"].median(), d[ycol].mean()
    for _, r in bm.iterrows():
        if r["x"] == mx:
            continue
        n += 1
        agree += np.sign(r["y"] - my) == expected * orient * np.sign(r["x"] - mx)
    return agree, n, "block_agreement"


def verdict(eff, lo, hi, share, expected, thr):
    if not np.isfinite(eff):
        return "inconclusive"
    excl = np.isfinite(lo) and (lo > 0 or hi < 0)
    big = abs(eff) >= thr
    ok_share = np.isfinite(share) and share >= 0.70
    if big and excl and ok_share and np.sign(eff) == expected:
        return "systematic"
    if big and excl and np.isfinite(share) and (1 - share) >= 0.70 and np.sign(eff) == -expected:
        return "systematic (opposite sign)"
    if (not big) and not excl:
        return "not systematic"
    return "inconclusive"


def assess(d, ycol, xcol, labcol, hi, lo, block, stratum, expected, thr, P, orient=1, tag=None):
    """One registered effect row plus per-bin rows. d must hold ycol, xcol, labcol, block, stratum."""
    d = d[np.isfinite(d[ycol].astype(float)) & d[labcol].notna()].copy()
    f = effect_fn(hi, lo)
    stat = lambda q: f(q[ycol].to_numpy(float), q[labcol].to_numpy(object))  # noqa: E731
    eff = stat(d)
    lo_ci, hi_ci, dropped = block_boot(d, stat, block, P["n_boot"], P["seed"])
    ag, n, mode = sign_share(d, ycol, labcol, xcol, block, f, expected, orient)
    share = ag / n if n else np.nan
    p, pmode = perm_p(d[ycol], d[labcol], d[stratum], f, P["n_perm"], P["seed"], P["exact_perm_max_n"])
    rows = [dict(**(tag or {}), bin="EFFECT " + "+".join(map(str, sorted(hi))) + " minus " + "+".join(map(str, sorted(lo))),
                 n=len(d), n_months=d[block].nunique(), mean=eff, median=np.nan, ci_lo=lo_ci, ci_hi=hi_ci,
                 boot_dropped=dropped, sign_agree=ag, sign_n=n, sign_mode=mode, perm_p=p, perm_mode=pmode,
                 expected_sign=expected, threshold=thr, verdict=verdict(eff, lo_ci, hi_ci, share, expected, thr))]
    for b, g in d.groupby(labcol, sort=True):
        m = lambda q: float(q[ycol].mean()) if len(q) else np.nan  # noqa: E731
        bl, bh, _ = block_boot(g, m, block, P["n_boot"], P["seed"])
        rows.append(dict(**(tag or {}), bin=str(b), n=len(g), n_months=g[block].nunique(), mean=float(g[ycol].mean()),
                         median=float(g[ycol].median()), ci_lo=bl, ci_hi=bh))
    return rows, dict(effect=eff, ci=(lo_ci, hi_ci), share=share)


def ols_slope_ci(d, ycol, xcol, block, P):
    stat = lambda q: float(np.polyfit(q[xcol].to_numpy(float), q[ycol].to_numpy(float), 1)[0]) \
        if q[xcol].nunique() > 1 else np.nan  # noqa: E731
    lo, hi, _ = block_boot(d, stat, block, P["n_boot"], P["seed"])
    return stat(d), lo, hi


def spearman_exact(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    rx, ry = pd.Series(x).rank().to_numpy(), pd.Series(y).rank().to_numpy()
    rho = float(np.corrcoef(rx, ry)[0, 1])
    vals = [np.corrcoef(rx, ry[list(p)])[0, 1] for p in itertools.permutations(range(len(y)))]
    p = float(np.mean(np.abs(vals) >= abs(rho) - 1e-12))
    return rho, p, math.factorial(len(y))


def theil_sen_slope(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    i, j = np.triu_indices(len(x), 1)
    dx = x[j] - x[i]
    ok = dx != 0
    return float(np.median((y[j] - y[i])[ok] / dx[ok])) if ok.any() else np.nan
