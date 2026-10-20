"""Shared evaluation harness for round 3 (EXECUTION_PROMPT.md section 4).

A predictor is a function ``f(ctx) -> Q_hat_Ah`` (or ``(Q_hat, info_dict)``).
``ctx`` holds only data visible at the (pseudo-)cutoff:

    k, at_date, ck (all checkup dates), op (cut operation data), fc (anchors),
    steps[variant], a4[smooth], eps (eps0 + delta), eps0, delta, step, a4s, scenario

Proxies follow V2 exactly: P_k = Q_fc,k(full data) + eps0 + delta.
"""
import os
import pickle
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
RESEARCH = os.path.dirname(STUDY)
ROOT = os.path.abspath(os.path.join(RESEARCH, "..", "TechArena_Challenge2_Team_Package"))
BASE_SRC = os.path.join(RESEARCH, "phase2_anchor_step_20261013", "src")
V2_SRC = os.path.join(RESEARCH, "phase2_v2_phase_matched_20261013", "src")
for p in (HERE, V2_SRC, BASE_SRC, ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from framework.data import Dataset, load_dataset, load_eval_points  # noqa: E402
from events import (STEP_VARIANTS, charge_step_split, full_charges,  # noqa: E402
                    step_programs)

DATA = os.path.join(ROOT, "data")
CACHE = os.path.join(STUDY, "cache")
NOM = 102.0
Q_CK0 = 100.41
DELTAS = (0.0, 0.4, 0.8)
A4_SMOOTH = (1.0, 2.0, 3.0)
VARIANTS = tuple(STEP_VARIANTS)

_EVAL = load_eval_points(DATA)
CK = pd.DatetimeIndex(_EVAL["date"])
CK_NAMES = list(_EVAL["checkup"])


# ----------------------------------------------------------------- data access
def _cache(name, fn):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name + ".pkl")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    obj = fn()
    with open(path, "wb") as f:
        pickle.dump(obj, f)
    return obj


def full_op():
    return _cache("op_full", lambda: load_dataset(DATA).operation)


def cut_op(k):
    """Operation rows exactly as the framework returns them for CK_k."""
    return _cache(f"op_ck{k}", lambda: load_dataset(DATA, until=CK[k]).operation)


def tables(op, key):
    """fc, steps (all variants), a4 (all smoothings) for one cut; cached by key."""
    def build():
        fc = full_charges(op)
        st = {v: step_programs(op, **STEP_VARIANTS[v]) for v in VARIANTS}
        a4 = {s: charge_step_split(op, fc, smooth_Ah=s) for s in A4_SMOOTH} if len(fc) else \
            {s: pd.DataFrame(columns=["segment", "step_to_top_mean"]) for s in A4_SMOOTH}
        return fc, st, a4
    return _cache("tab_" + key, build)


def proxies():
    fc = full_charges(full_op()).sort_values("t_end").reset_index(drop=True)
    q = fc["Q_Ah"].to_numpy()
    return q, Q_CK0 - q[0]


QFC, EPS0 = proxies()


# ------------------------------------------------------------- pseudo scenarios
def month_45_segment(op_full_cut, k_month):
    """Segment number of the 45 C segment of month m (between CK_m and CK_m+1)."""
    seg = op_full_cut.groupby("segment").agg(t0=("timestamp", "min"), sp=("chamber_temperature_C", "first"))
    seg = seg[(seg["t0"] > CK[k_month]) & (seg["t0"] < CK[k_month + 1]) & (seg["sp"] == 45)]
    return int(seg.index[0]) if len(seg) else None


def pseudo_gap(k, keep_steps):
    """PG1/PG2: month k-1 keeps its 25 C segment and its 45 C segment only up to the
    end of the first ``keep_steps`` deep discharges (k = 4..7)."""
    op = cut_op(k)
    s45 = month_45_segment(op, k - 1)
    if s45 is None:
        return None
    g = op[op["segment"] == s45]
    st = step_programs(g)
    st = st.sort_values("t_cv_end")
    if len(st) < keep_steps:
        return None
    t_keep = st["t_measured"].iloc[keep_steps - 1]
    drop = (op["segment"] == s45) & (op["timestamp"] > t_keep)
    return op[~drop].reset_index(drop=True)


def pseudo_cut(k, days):
    """PC5/PC10: data cut ``days`` before the CK_k date."""
    op = cut_op(k)
    return op[op["timestamp"] <= CK[k] - pd.Timedelta(days=days)].reset_index(drop=True)


SCENARIOS = {
    "real": [(k, None) for k in range(1, 8)],
    "PG1": [(k, ("gap", 1)) for k in range(4, 8)],
    "PG2": [(k, ("gap", 2)) for k in range(4, 8)],
    "PC5": [(k, ("cut", 5)) for k in range(2, 8)],
    "PC10": [(k, ("cut", 10)) for k in range(2, 8)],
}


def scenario_op(k, spec):
    if spec is None:
        return cut_op(k), f"real_ck{k}"
    kind, n = spec
    if kind == "gap":
        return _cache(f"op_pg{n}_ck{k}", lambda: pseudo_gap(k, n)), f"pg{n}_ck{k}"
    return _cache(f"op_pc{n}_ck{k}", lambda: pseudo_cut(k, n)), f"pc{n}_ck{k}"


# -------------------------------------------------------------------- evaluate
def run(predictors, scenarios=("real",), variants=("main",), smooths=(2.0,), deltas=DELTAS,
        extra_ctx=None):
    """Evaluate ``{name: f(ctx)}``; returns a long DataFrame with errors in pp."""
    rows = []
    for scen in scenarios:
        for k, spec in SCENARIOS[scen]:
            op, key = scenario_op(k, spec)
            if op is None:
                continue
            fc, st, a4 = tables(op, key)
            for d in deltas:
                for v in variants:
                    for s in smooths:
                        ctx = dict(k=k, at_date=CK[k], ck=CK, op=op, fc=fc, steps=st, step=v,
                                   a4=a4, a4s=s, eps=EPS0 + d, eps0=EPS0, delta=d, scenario=scen,
                                   key=key, **(extra_ctx or {}))
                        for name, f in predictors.items():
                            out = f(ctx)
                            q, info = (out if isinstance(out, tuple) else (out, {}))
                            proxy = QFC[k] + EPS0 + d
                            rows.append(dict(scenario=scen, checkup=CK_NAMES[k], k=k, delta=d, step=v,
                                             a4s=s, model=name, Q=float(q), proxy=float(proxy),
                                             err_pp=(float(q) - proxy) / NOM * 100,
                                             SOH=float(q) / NOM * 100, **info))
    return pd.DataFrame(rows)


def metrics(df):
    """MAE / MAX / RMSE and eps-free CK2-7 MAE per (scenario, model, step, a4s, delta)."""
    keys = ["scenario", "model", "step", "a4s", "delta"]
    g = df.groupby(keys)["err_pp"]
    m = g.agg(MAE=lambda e: e.abs().mean(), MAX=lambda e: e.abs().max(),
              RMSE=lambda e: float(np.sqrt((e ** 2).mean())), n="count").reset_index()
    ef = df[df["k"] >= 2].groupby(keys)["err_pp"].apply(lambda e: e.abs().mean()).rename("CK2_7_MAE")
    return m.merge(ef.reset_index(), on=keys, how="left")


def per_ck(df, scenario="real", delta=0.4, step="main", a4s=2.0):
    s = df[(df["scenario"] == scenario) & (df["delta"] == delta) & (df["step"] == step) & (df["a4s"] == a4s)]
    return s.pivot_table(index="checkup", columns="model", values="err_pp")


# ------------------------------------------------------------ baselines (M4, V2)
def m4_pred(ctx):
    from v2 import m4
    return m4(ctx["fc"], ctx["steps"][ctx["step"]], ctx["eps"])


def v2_pred(ctx, **cfg):
    from v2 import v2
    q, br, b = v2(ctx["fc"], ctx["steps"][ctx["step"]], ctx["a4"][ctx["a4s"]], ctx["ck"], ctx["k"],
                  ctx["eps"], **cfg)
    return q, {"branch": br, "beta": b}


BASELINES = {"M4": m4_pred, "V2": v2_pred}


def gates_vs_v2(met, pck, name, variants_met=None):
    """Common gates against V2 (prompt section 4). ``met`` from metrics() on real data."""
    m = met[met["scenario"] == "real"].set_index(["model", "step", "a4s", "delta"])
    out = {}
    ok = []
    for d in DELTAS:
        a, b = m.loc[(name, "main", 2.0, d)], m.loc[("V2", "main", 2.0, d)]
        ok.append(bool(a["MAE"] < b["MAE"] and a["MAX"] <= b["MAX"] + 0.10))
    out["G-proxy"] = all(ok)
    a, b = m.loc[(name, "main", 2.0, 0.0)], m.loc[("V2", "main", 2.0, 0.0)]
    out["G-epsfree"] = dict(model=float(a["CK2_7_MAE"]), V2=float(b["CK2_7_MAE"]),
                            passed=bool(a["CK2_7_MAE"] <= b["CK2_7_MAE"] - 0.02))
    if variants_met is not None:
        vm = variants_met[variants_met["scenario"] == "real"].set_index(["model", "step", "a4s", "delta"])
        wins = [bool(vm.loc[(name, v, 2.0, 0.4), "MAE"] < vm.loc[("V2", v, 2.0, 0.4), "MAE"]) for v in VARIANTS]
        out["G-robust"] = dict(wins=int(sum(wins)), passed=bool(sum(wins) >= 5))
    inc = float((pck[name].abs() - pck["V2"].abs()).max())
    out["G-regress"] = dict(max_abs_err_increase_pp=inc, passed=bool(inc <= 0.30))
    return out


# --------------------------------------------------------- candidate-class checks
def candidate_checks(model_cls, research_soh, data_dir=DATA):
    """G-causal and G-impl: run like run_model.py, corrupt future rows, compare to research."""
    full = load_dataset(data_dir)
    model = model_cls()
    model.fit(full)
    model = pickle.loads(pickle.dumps(model))
    res, same = [], []
    rng = np.random.default_rng(0)
    for k, d in enumerate(CK):
        ds = load_dataset(data_dir, until=d)
        a = model.estimate_soh(ds, d)
        op = full.operation.copy()
        fut = op["timestamp"] > d
        for c in ["current_A", "pack_voltage_V", "cell1_V", "cell2_V", "cell3_V", "cell4_V",
                  "chamber_temperature_C", "temp_mean_C"]:
            op.loc[fut, c] = rng.normal(size=int(fut.sum()))
        cut = Dataset(operation=op[~fut].reset_index(drop=True),
                      checkups_released=full.checkups_released[full.checkups_released["date"] <= d],
                      eval_points=full.eval_points, reference_discharge=full.reference_discharge, until=d)
        same.append(model.estimate_soh(cut, d) == a)
        res.append(round(float(a), 3))
    m2 = model_cls()
    m2.fit(load_dataset(data_dir, until=CK[1]))
    fit_cut_same = all(round(float(m2.estimate_soh(load_dataset(data_dir, until=d), d)), 3) == r
                       for d, r in zip(CK, res))
    diff = float(np.max(np.abs(np.array(res[1:]) - np.asarray(research_soh))))
    return dict(predictions=res, future_rows_corrupted_identical=bool(all(same)),
                fit_on_cut_data_identical=bool(fit_cut_same), max_abs_diff_vs_research_pp=diff,
                passed=bool(all(same) and fit_cut_same and diff <= 0.001))
