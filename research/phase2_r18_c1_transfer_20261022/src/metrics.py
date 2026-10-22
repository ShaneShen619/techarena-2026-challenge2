"""Per-cell error summaries and the registered decision rules (protocol.json, "gates").

The physical cell is the unit: targets inside one cell are not independent, so every rule
counts cells and reports leave-one-cell-out values; no p-values.
"""
import math

import numpy as np
import pandas as pd

from .common import PROTOCOL

GATES = PROTOCOL["gates"]
MIN_TARGETS = GATES["min_targets"]


def cell_mae(err, cells=None):
    """MAE per cell of an error frame with columns cell, k, err."""
    out = err.groupby("cell")["err"].apply(lambda e: float(np.mean(np.abs(e))))
    return out if cells is None else out.reindex(cells)


def paired(df, a, b, where=None):
    """Per-cell MAE of estimators a and b on their common targets (rows: cell, k, est, err).

    Returns a frame indexed by cell with mae_a, mae_b, n; only cells with >= MIN_TARGETS.
    """
    d = df if where is None else df[where]
    ea = d[d["est"] == a].set_index(["cell", "k"])["err"]
    eb = d[d["est"] == b].set_index(["cell", "k"])["err"]
    common = ea.dropna().index.intersection(eb.dropna().index)
    rows = []
    for cell in sorted({c for c, _ in common}):
        idx = [i for i in common if i[0] == cell]
        if len(idx) >= MIN_TARGETS:
            rows.append({"cell": cell, "mae_a": float(np.mean(np.abs(ea.loc[idx]))),
                         "mae_b": float(np.mean(np.abs(eb.loc[idx]))), "n": len(idx)})
    return pd.DataFrame(rows, columns=["cell", "mae_a", "mae_b", "n"]).set_index("cell")


def summary(t):
    """Macro values, the cell count where a beats b, and leave-one-cell-out ratios."""
    n = len(t)
    if n == 0:
        return {"n_cells": 0}
    ma, mb = float(t["mae_a"].mean()), float(t["mae_b"].mean())
    loco = [float(t.drop(c)["mae_a"].mean() / t.drop(c)["mae_b"].mean()) for c in t.index] if n > 1 else []
    return {"n_cells": n, "macro_a": ma, "macro_b": mb,
            "macro_ratio": ma / mb if mb > 0 else np.nan, "macro_gain": mb - ma,
            "cells_better": int((t["mae_a"] < t["mae_b"]).sum()),
            "cells_worse": int((t["mae_a"] > t["mae_b"]).sum()),
            "loco_ratio_max": max(loco) if loco else np.nan,
            "per_cell": {c: {"mae_a": float(r.mae_a), "mae_b": float(r.mae_b), "n": int(r.n)}
                         for c, r in t.iterrows()}}


def _need(frac, n):
    return math.ceil(frac * n - 1e-9)


def decide_c1(s, shuffle_cells_ok, delta):
    """C1: the submitted step update against anchor-only (E2_SUB vs E0_anchor)."""
    n = s.get("n_cells", 0)
    if n < 3:
        return "insufficient"
    if (s["macro_ratio"] <= 0.70 and s["cells_better"] >= _need(5 / 6, n)
            and s["loco_ratio_max"] <= 0.80 and shuffle_cells_ok >= _need(5 / 6, n)):
        return "supported"
    if s["macro_ratio"] >= 1.0 or s["cells_better"] <= n // 2:
        return "not_supported"
    return "inconclusive"


def decide_gain(s, delta, worse_rule=False, better_rule_on_fail=True):
    """Shared rule of C1b, C3, C4: gain >= delta on >= 2/3 of cells, else loss / worse rules."""
    n = s.get("n_cells", 0)
    if n < 3:
        return "insufficient"
    if s["macro_gain"] >= delta and s["cells_better"] >= _need(2 / 3, n):
        return "supported"
    if s["macro_gain"] <= -delta:
        return "not_supported"
    if worse_rule and s["cells_worse"] >= _need(2 / 3, n):
        return "not_supported"
    if better_rule_on_fail and s["cells_better"] <= n // 2:
        return "not_supported"
    return "inconclusive"


def decide_c5(robust_macro, single_macros, delta):
    """C5: the variant median against each single detection variant."""
    vals = [v for v in single_macros.values() if np.isfinite(v)]
    if not vals or not np.isfinite(robust_macro):
        return "insufficient"
    med, best = float(np.median(vals)), float(min(vals))
    if robust_macro <= med and robust_macro - best <= delta:
        return "supported"
    if robust_macro > med + delta:
        return "not_supported"
    return "inconclusive"


def decide_c8(ratios):
    """C8: MAE ratio to the ExampleModel analogue per counted cell."""
    r = [v for v in ratios.values() if np.isfinite(v)]
    if len(r) < 3:
        return "insufficient"
    if all(v <= 0.30 for v in r):
        return "supported"
    if any(v >= 1.0 for v in r):
        return "not_supported"
    return "inconclusive"


def delta_from_truth(views):
    """Registered noise threshold from the spread of the labels that make each truth value."""
    n = PROTOCOL["information_structure"]["truth_n"]
    sds = [sd for v in views for sd in v.truth_sd.values() if np.isfinite(sd)]
    floor = float(np.median(sds)) / math.sqrt(n) if sds else 0.0
    return max(PROTOCOL["noise"]["delta_min_ah"], floor)
