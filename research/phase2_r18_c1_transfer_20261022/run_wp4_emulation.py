"""WP4: run the estimators on the emulated views and apply the registered gates.

Reads cache/views/*.pkl. Writes outputs/wp4_errors.csv, wp4_decisions.json, wp4_tables.md.

    python3 -B run_wp4_emulation.py [--work DIR]
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src import baselines, metrics, model_adapter, store  # noqa: E402
from src.common import PROTOCOL  # noqa: E402

INFO = PROTOCOL["information_structure"]
LEVELS = {"code_as_is": "robust", "method": "robust_interp"}
SINGLES = PROTOCOL["steps"]["keys_single"]
MODEL_EST = {
    "E0_anchor": {"scenario": "no_steps"},
    "E1_fallback": {"phase": False},
    "E2_SUB": {},
    "E2_beta1": {"beta_mode": "one"},
}


def in_scope(vw, k, level):
    lim = INFO["scope_primary_min_rel"] if level == "primary" else INFO["scope_extended_min_rel"]
    return vw.truth[k] >= lim * vw.label0


def row(cell, vw, k, est, key, scenario, pred, trace=None):
    tr = trace or {}
    return {"cell": cell, "k": k, "est": est, "key": key, "scenario": scenario, "pred": pred,
            "truth": vw.truth[k], "err": pred - vw.truth[k], "branch": tr.get("branch"),
            "beta": tr.get("beta"), "beta_v2": tr.get("beta_v2"), "x": tr.get("x"),
            "scope_primary": in_scope(vw, k, "primary"), "scope_extended": in_scope(vw, k, "extended")}


def run_cell(cell, vw):
    rows = []
    ks = sorted(vw.truth)
    for key in LEVELS.values():
        xs = {}
        for k in ks:
            for est, kw in MODEL_EST.items():
                p = model_adapter.predict(vw, k, key=key, **kw)
                rows.append(row(cell, vw, k, est, key, "main", p["q"], p))
                if est == "E2_SUB":
                    xs[k] = p["x"] if p["branch"] == "phase" else None
            for est, kw in (("E2_SUB", {}), ("E1_fallback_no_sqrt", {"phase": False, "gap_rule": False})):
                p = model_adapter.predict(vw, k, key=key, scenario="gap", **kw)
                rows.append(row(cell, vw, k, est, key, "gap", p["q"], p))
        for k in ks:
            if xs.get(k) is None:
                continue
            b = model_adapter.oracle_beta(vw, k, xs)
            if np.isfinite(b):
                p = model_adapter.predict(vw, k, key=key, beta_mode="value", beta_value=b)
                rows.append(row(cell, vw, k, "E2_beta_oracle", key, "main", p["q"], p))
        for single in SINGLES[key]:
            for k in ks:
                p = model_adapter.predict(vw, k, key=single)
                rows.append(row(cell, vw, k, "E2_SUB", single, "main", p["q"], p))
    for k in ks:
        for scen in ("main", "gap"):
            rows.append(row(cell, vw, k, "E4_baseline", "-", scen, baselines.e4_baseline(vw, k)))
            rows.append(row(cell, vw, k, "E5_trend", "-", scen, baselines.e5_trend(vw, k)))
    return rows


def shuffle_mae(cell, vw, key, ks, rng, n_perm):
    """Mean over permutations of E2's MAE when program depths are shuffled across the cell."""
    idx = [n for n, p in enumerate(vw.programs) if p["detected"] and np.isfinite(p[key])]
    vals = np.array([vw.programs[n][key] for n in idx])
    maes = []
    for _ in range(n_perm):
        perm = rng.permutation(vals)
        over = [p[key] for p in vw.programs]
        for n, v in zip(idx, perm):
            over[n] = v
        errs = [model_adapter.predict(vw, k, key=key, depth_override=over)["q"] - vw.truth[k] for k in ks]
        maes.append(float(np.mean(np.abs(errs))))
    return float(np.mean(maes)) if maes else np.nan


def level_frame(err, key, scenario="main", scope="scope_primary"):
    d = err[((err["key"] == key) | (err["key"] == "-")) & (err["scenario"] == scenario) & err[scope]]
    return d.copy()


def gates(err, views, key, delta, rng):
    d = level_frame(err, key)
    out = {}
    s1 = metrics.summary(metrics.paired(d, "E2_SUB", "E0_anchor"))
    shuf = {}
    for cell in s1.get("per_cell", {}):
        ks = sorted(d[(d["cell"] == cell) & (d["est"] == "E2_SUB")]["k"])
        shuf[cell] = shuffle_mae(cell, views[cell], key, ks, rng, PROTOCOL["controls"]["shuffle_permutations"])
    shuffle_ok = sum(1 for c, v in shuf.items() if v - s1["per_cell"][c]["mae_a"] >= delta)
    out["C1_step_update"] = {**s1, "shuffle_mae": shuf, "shuffle_cells_ok": shuffle_ok,
                             "decision": metrics.decide_c1(s1, shuffle_ok, delta)}
    s = metrics.summary(metrics.paired(d, "E2_SUB", "E5_trend"))
    out["C1b_beyond_trend"] = {**s, "decision": metrics.decide_gain(s, delta)}
    phase_idx = d[(d["est"] == "E2_SUB") & (d["branch"] == "phase")].set_index(["cell", "k"]).index
    on_phase = d.set_index(["cell", "k"]).index.isin(phase_idx)
    s = metrics.summary(metrics.paired(d, "E2_SUB", "E2_beta1", where=on_phase))
    out["C3_beta"] = {**s, "decision": metrics.decide_gain(s, delta, worse_rule=True, better_rule_on_fail=False)}
    so = metrics.summary(metrics.paired(d, "E2_beta_oracle", "E2_SUB", where=on_phase))
    out["C3_beta"]["oracle_vs_SUB"] = so
    s = metrics.summary(metrics.paired(d, "E2_SUB", "E1_fallback", where=on_phase))
    out["C4_phase"] = {**s, "decision": metrics.decide_gain(s, delta, worse_rule=False, better_rule_on_fail=False)}

    sing = err[(err["est"] == "E2_SUB") & (err["scenario"] == "main") & err["scope_primary"]
               & err["key"].isin([key] + SINGLES[key])]
    piv = sing.pivot_table(index=["cell", "k"], columns="key", values="err")
    piv = piv.dropna()
    cell_mae = piv.abs().groupby(level="cell").mean()
    cell_mae = cell_mae[piv.groupby(level="cell").size() >= metrics.MIN_TARGETS]
    macros = cell_mae.mean().to_dict()
    out["C5_robust"] = {"macro_by_key": macros, "n_cells": int(len(cell_mae)),
                        "decision": metrics.decide_c5(macros.get(key, np.nan),
                                                      {k: v for k, v in macros.items() if k != key}, delta)}
    t = metrics.paired(d, "E2_SUB", "E4_baseline")
    ratios = (t["mae_a"] / t["mae_b"]).to_dict()
    out["C8_vs_baseline"] = {"ratio_by_cell": ratios, "decision": metrics.decide_c8(ratios)}

    g = level_frame(err, key, scenario="gap")
    g = g[g["k"] >= 2]
    gap = {}
    for est in ("E2_SUB", "E1_fallback_no_sqrt", "E5_trend"):
        gap[est] = metrics.cell_mae(g[g["est"] == est]).to_dict()
    gap["E0_anchor"] = metrics.cell_mae(d[(d["est"] == "E0_anchor") & (d["k"] >= 2)]).to_dict()
    gap["E2_SUB_branches"] = g[g["est"] == "E2_SUB"]["branch"].value_counts().to_dict()
    out["C9_gap"] = {"cell_mae": gap, "decision": "report_only"}

    first = d[d["k"] == 1]
    out["first_window"] = {est: metrics.cell_mae(first[first["est"] == est]).to_dict()
                           for est in ("E2_SUB", "E0_anchor", "E4_baseline", "E5_trend")}
    ext = level_frame(err, key, scope="scope_extended")
    out["extended_scope"] = {
        "E2_vs_E0": metrics.summary(metrics.paired(ext, "E2_SUB", "E0_anchor")),
        "E2_vs_E5": metrics.summary(metrics.paired(ext, "E2_SUB", "E5_trend"))}
    return out


def sensitivity(cache):
    """E2 vs E0 on the other window lengths and on dense programs (report only)."""
    res = {}
    for spec in store.VIEW_SPECS:
        if spec == store.PRIMARY:
            continue
        views = store.load_views(cache, spec)
        for key in LEVELS.values():
            rows = []
            for cell, vw in views.items():
                for k in sorted(vw.truth):
                    if not in_scope(vw, k, "primary"):
                        continue
                    for est, kw in (("E2_SUB", {}), ("E0_anchor", {"scenario": "no_steps"})):
                        rows.append({"cell": cell, "k": k, "est": est,
                                     "err": model_adapter.predict(vw, k, key=key, **kw)["q"] - vw.truth[k]})
            if rows:
                res[f"{spec}_{key}"] = metrics.summary(metrics.paired(pd.DataFrame(rows), "E2_SUB", "E0_anchor"))
    return res


def markdown(tab):
    """A frame as a GitHub table (no extra dependency)."""
    cols = [str(c) for c in tab.columns]
    lines = ["| cell | " + " | ".join(cols) + " |", "|---" * (len(cols) + 1) + "|"]
    for idx, r in tab.iterrows():
        lines.append(f"| {idx} | " + " | ".join("" if pd.isna(v) else f"{v:.3f}" for v in r) + " |")
    return "\n".join(lines)


def tables(err, decisions, delta):
    lines = [f"delta = {delta:.3f} Ah", ""]
    for level, key in LEVELS.items():
        d = level_frame(err, key)
        for title, ests, where in (
                ("all targets", ["E0_anchor", "E1_fallback", "E2_SUB", "E2_beta1", "E4_baseline", "E5_trend"], None),
                ("phase targets (k >= 2, phase branch fired)",
                 ["E0_anchor", "E1_fallback", "E2_SUB", "E2_beta1", "E2_beta_oracle", "E5_trend"], "phase")):
            dd = d
            if where == "phase":
                idx = d[(d["est"] == "E2_SUB") & (d["branch"] == "phase")].set_index(["cell", "k"]).index
                dd = d[d.set_index(["cell", "k"]).index.isin(idx)]
            lines += [f"## Level `{level}` (key `{key}`), primary scope, {title}, MAE in Ah", ""]
            tab = pd.DataFrame({e: metrics.cell_mae(dd[dd["est"] == e]) for e in ests})
            tab.loc["macro"] = tab.mean()
            lines += [markdown(tab), ""]
        lines += ["| claim | decision |", "|---|---|"]
        lines += [f"| {c} | {v['decision']} |" for c, v in decisions[level].items() if "decision" in v]
        lines.append("")
    return "\n".join(lines)


def main():
    args = store.parser(__doc__).parse_args()
    cache, out = store.dirs(args.work)
    views = store.load_views(cache)
    if not views:
        sys.exit("no views: run run_wp2_extract.py first")
    err = pd.DataFrame([r for c, vw in views.items() for r in run_cell(c, vw)])
    err.to_csv(out / "wp4_errors.csv", index=False)
    delta = metrics.delta_from_truth(views.values())
    rng = np.random.default_rng(PROTOCOL["controls"]["seed"])
    decisions = {level: gates(err, views, key, delta, rng) for level, key in LEVELS.items()}
    decisions["delta_ah"] = delta
    decisions["sensitivity"] = sensitivity(cache)
    with open(out / "wp4_decisions.json", "w") as f:
        json.dump(decisions, f, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    md = tables(err, decisions, delta)
    (out / "wp4_tables.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
