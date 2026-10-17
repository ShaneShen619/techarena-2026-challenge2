"""Per-cell step candidates on top of SUB with the branch freeze (EXECUTION_PROMPT.md section 3 rule 2).

SUB's own selection is replayed with internals.decompose (branch, E_cur/E_prev, rate-fit set, after[0]/after[-1], n, d,
beta, anchor term). A candidate only supplies per-cell step locations (a 'provider') and how they are combined:
  mode 'position': per-program pack value = agg over cells, then SUB's formulas on that series;
  mode 'change'  : per-cell change x_c (per-cell Theil-Sen rate), then combine over cells.
With provider = main-variant cells and agg = mean this reproduces SUB exactly."""
import numpy as np
import pandas as pd

from common10 import H
from v2 import theil_sen
import internals as I

CELLS = ["cell1_V", "cell2_V", "cell3_V", "cell4_V"]
COLS = [f"step_{c}" for c in CELLS]
NAN_LOG = []   # (scenario, k, delta, step, role) whenever a selected program has a NaN cell value


def variant_locs(steps, variant):
    st = steps[variant]
    return st.set_index("t_cv_end")[COLS].astype(float)


def ensemble_locs(steps, variants, how="mean", min_finite=4):
    tabs = [variant_locs(steps, v) for v in variants]
    idx = tabs[0].index
    for t in tabs[1:]:
        idx = idx.union(t.index)
    arr = np.stack([t.reindex(idx).to_numpy(float) for t in tabs])          # (n_variants, n_programs, 4)
    n = np.isfinite(arr).sum(axis=0)
    with np.errstate(all="ignore"):
        val = np.nanmean(arr, axis=0) if how == "mean" else np.nanmedian(arr, axis=0)
    val[n < min_finite] = np.nan
    return pd.DataFrame(val, index=idx, columns=COLS)


def provider_variant(variant=None):
    """Per-cell locations of one detection variant (None = the ctx's own step variant)."""
    return lambda ctx: variant_locs(ctx["steps"], variant or ctx["step"])


def provider_ensemble(variants, how="mean"):
    return lambda ctx: ensemble_locs(ctx["steps"], variants, how)


def agg_cells(v, agg):
    v = np.asarray(v, float)
    if not np.isfinite(v).any():
        return np.nan
    return float(np.nanmean(v) if agg == "mean" else np.nanmedian(v))


def combine_median(xc, meta=None):
    xc = np.asarray(xc, float)
    xc = xc[np.isfinite(xc)]
    return float(np.median(xc)) if len(xc) else np.nan


def combine_reject(tau, log=None):
    """B2: drop the one cell whose change deviates from the median of the other three by more than tau."""
    def f(xc, meta=None):
        xc = np.asarray(xc, float)
        ok = np.isfinite(xc)
        if ok.sum() < 4:
            return float(np.nanmean(xc)) if ok.any() else np.nan
        dev = np.array([xc[c] - np.median(np.delete(xc, c)) for c in range(4)])
        c = int(np.argmax(np.abs(dev)))
        if abs(dev[c]) > tau:
            if log is not None:
                log.append(dict(**(meta or {}), dropped=CELLS[c][:-2], dev=float(dev[c])))
            return float(np.mean(np.delete(xc, c)))
        if log is not None:
            log.append(dict(**(meta or {}), dropped="", dev=float(dev[c])))
        return float(np.mean(xc))
    return f


def _rows(L, ts, ctx, role):
    out = []
    for t in ts:
        t = pd.Timestamp(t)
        v = L.loc[t].to_numpy(float) if t in L.index else np.full(4, np.nan)
        if not np.isfinite(v).all():
            NAN_LOG.append((ctx["scenario"], ctx["k"], ctx["delta"], ctx["step"], role, str(t)))
        out.append(v)
    return np.array(out)


def make(provider, mode="position", agg="mean", combine=None, selection_step=None, tau_by_variant=None, log=None):
    """selection_step: detection variant whose SUB selection is replayed (default: the ctx's own step)."""
    def f(ctx):
        sctx = ctx if selection_step is None else dict(ctx, step=selection_step)
        o = I.decompose(sctx, "SUB")
        info = {"branch": o["branch"]}
        if o["branch"] == "sqrt_gap":
            return o["Q_pred"], info
        L = provider(ctx)
        comb = combine
        if tau_by_variant is not None:
            comb = combine_reject(tau_by_variant[ctx["step"]], log=log)
        meta = dict(scenario=ctx["scenario"], k=ctx["k"], delta=ctx["delta"], step=ctx["step"], branch=o["branch"])
        if o["branch"] == "phase":
            ts = [o["ev_E_cur"], o["ev_E_prev"]]
            rate = [t for t in str(o.get("ev_rate_fit") or "").split("|") if t]
            M = _rows(L, ts, ctx, "E")
            R = _rows(L, rate, ctx, "rate") if rate else None
            days = (np.array([(pd.Timestamp(t) - pd.Timestamp(rate[0])).total_seconds() for t in rate]) / 86400.0
                    if rate else None)
            dd = o["d_cur"] - o["d_prev"]
            if mode == "position":
                p = [agg_cells(r, agg) for r in M]
                r_p = theil_sen(days, np.array([agg_cells(r, agg) for r in R])) if rate else 0.0
                x = p[0] - p[1] + r_p * dd
            else:
                xc = []
                for c in range(4):
                    r_c = theil_sen(days[np.isfinite(R[:, c])], R[np.isfinite(R[:, c]), c]) if rate else 0.0
                    xc.append(M[0, c] - M[1, c] + r_c * dd)
                x = comb(xc, meta)
            return float(o["q_anchor_term"] + o["beta_used"] * x), info
        first, last = o.get("ev_after_first"), o.get("ev_after_last")
        if not (isinstance(first, str) and first):
            return o["Q_pred"], info
        M = _rows(L, [last, first], ctx, "after")
        if mode == "position":
            inc = agg_cells(M[0], agg) - agg_cells(M[1], agg)
        else:
            xc = M[0] - M[1]
            inc = comb(xc, meta)
        return float(o["q_anchor_term"] + inc), info
    return f


# ---------------------------------------------------------------- G_event helpers (full data, diagnostic)
def pack_series_position(L, agg):
    return pd.Series([agg_cells(r, agg) for r in L.to_numpy(float)], index=L.index)


def pack_series_change(L, segments, combine):
    """Chained series for change-based candidates (D2.x): within each segment start at the 4-cell mean of the first
    program, then add the combined per-cell change between consecutive programs."""
    s = pd.Series(np.nan, index=L.index)
    seg = pd.Series(segments, index=L.index)
    for _, idx in seg.groupby(seg).groups.items():
        idx = sorted(idx)
        prev = None
        for t in idx:
            v = L.loc[t].to_numpy(float)
            if prev is None:
                s[t] = np.nanmean(v)
            else:
                s[t] = s[prev] + combine(v - L.loc[prev].to_numpy(float))
            prev = t
    return s
