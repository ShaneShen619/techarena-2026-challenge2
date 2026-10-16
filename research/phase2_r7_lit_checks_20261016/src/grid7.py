"""Round-6 WP1 hypothesis grid, copied from research/phase2_r6_robust_20261016/wp1/run_wp1.py (functions target,
scores, decision, prior_weights, model set P), extended so that extra hypothesis families can be added.

Round 6 grid: T_k(h) = Q_fc,k + eps0 + Delta - f * R_k + d * L_k (18 hypotheses).
Extra families are passed as dicts {name: {k: T_k}} and appended to the grid.
"""
import importlib.util
import itertools
import json
import os

import numpy as np
import pandas as pd

from common6 import H, STUDY, WORKTREE
from framework.data import Dataset, load_dataset
from preds5c import ens, s_pred
from smodel5c import LawFit
from v3 import v3

R6 = os.path.join(WORKTREE, "research", "phase2_r6_robust_20261016")
PROTO6 = json.load(open(os.path.join(R6, "wp1", "protocol.json")))
PKG = os.path.join(STUDY, "cache", "submitted_package", "TechArena_Challenge2_Team_Package")

_FULL = load_dataset(H.DATA)
_spec = importlib.util.spec_from_file_location("pkg_example", os.path.join(PKG, "my_model", "model_example.py"))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
_EX = _mod.ExampleModel()
_EX.fit(_FULL)
_EXMEMO = {}


def ex_pred(ctx):
    if ctx["key"] not in _EXMEMO:
        ds = Dataset(operation=ctx["op"], checkups_released=_FULL.checkups_released, eval_points=_FULL.eval_points,
                     reference_discharge=_FULL.reference_discharge, until=ctx["at_date"])
        _EXMEMO[ctx["key"]] = float(_EX.estimate_soh(ds, ctx["at_date"])) * H.NOM / 100.0
    return _EXMEMO[ctx["key"]]


def v3_pred(**kw):
    def f(ctx):
        q, br, b = v3(ctx["fc"], ctx["steps"][ctx["step"]], ctx["a4"][ctx["a4s"]], ctx["ck"], ctx["k"], ctx["eps"], **kw)
        return q, {"branch": br}
    return f


SUB = v3_pred(use_sqrt=True, beta_cap=float("inf"), median=False)
GAP = dict(steps=True, steps_mode="gap_endpoint", beta_mode="one", sigma_s=0.10)


def round6_models():
    """The round-6 WP1 candidate set (identical definitions)."""
    S5A = s_pred("S_main")
    R2B = s_pred("R2_B", cls=LawFit, cfg=dict(law="two", **GAP), uses_steps=True)
    R3T = s_pred("R3_T", cls=LawFit, cfg=dict(law="two", transient_ref="restart", **GAP), uses_steps=True)
    return {"EX": ex_pred, "M4": H.BASELINES["M4"], "V2": H.BASELINES["V2"], "SUB": SUB,
            "SUB_bcap": v3_pred(use_sqrt=True, beta_cap=1.2, median=False),
            "V3": v3_pred(use_sqrt=True, beta_cap=1.2, median=True),
            "S_main_5A": S5A, "ENS50_5A": ens(S5A, 0.5), "R2_B": R2B, "R2_D_w0.75": ens(R2B, 0.75),
            "R3_T": R3T, "R3_TD_w0.75": ens(R3T, 0.75)}


J = pd.read_csv(os.path.join(WORKTREE, "research", "phase2_round4_signals_20261014", "stage_5", "outputs", "jumps.csv"))
R = dict(zip(J["checkup"], J["recovery_Ah_with_aging"].astype(float)))
HYP6 = [dict(Delta=a, f=b, d=c) for a, b, c in itertools.product(PROTO6["hypotheses"]["Delta"], PROTO6["hypotheses"]["f"],
                                                                  PROTO6["hypotheses"]["d_Ah_per_Ah"])]


def hname(h):
    return f"D{h['Delta']}_f{h['f']}_d{h['d']}"


def target6(k, h):
    p = H.QFC[k] + H.EPS0
    L = max(0.0, 100.41 - p)
    return p + h["Delta"] - h["f"] * R[H.CK_NAMES[k]] + h["d"] * L


def targets6():
    return {hname(h): {k: target6(k, h) for k in range(1, 8)} for h in HYP6}


def prior_weights6(kind):
    if kind == "uniform":
        return np.full(len(HYP6), 1.0 / len(HYP6))
    fw, dw = {0.0: 0.6, 0.5: 0.3, 1.0: 0.1}, {0.0: 0.5, -0.031: 0.5}
    w = np.array([fw[h["f"]] * dw[h["d"]] / 3.0 for h in HYP6])
    return w / w.sum()


def scores(pred, targets):
    """pred: rows (scenario, k, model, Q); targets: {hname: {k: T_k}} (real scenario only in this round)."""
    rows = []
    for (scen, model), g in pred.groupby(["scenario", "model"]):
        g = g.sort_values("k")
        for hn, tk in targets.items():
            e = (g["Q"].to_numpy() - np.array([tk[k] for k in g["k"]])) / H.NOM * 100
            rows.append(dict(scenario=scen, model=model, h=hn, MAE=np.mean(np.abs(e)),
                             RMSE=np.sqrt(np.mean(e ** 2)), MAX=np.max(np.abs(e)), n=len(e)))
    d = pd.DataFrame(rows)
    ex = d[d.model == "EX"].set_index(["scenario", "h"])[["MAE", "RMSE", "MAX"]]
    d = d.join(ex, on=["scenario", "h"], rsuffix="_EX")
    d["s"] = (d["MAE"] / d["MAE_EX"] + d["RMSE"] / d["RMSE_EX"] + d["MAX"] / d["MAX_EX"]) / 3.0
    return d


def decision(sgrid, weights=None):
    """sgrid: index h, columns models (EX excluded). weights: {name: Series over h} of prior expectations."""
    best = sgrid.min(axis=1)
    reg = sgrid.sub(best, axis=0)
    t = pd.DataFrame({"worst_s": sgrid.max(), "max_regret": reg.max()})
    for name, w in (weights or {}).items():
        w = w.reindex(sgrid.index).fillna(0.0)
        t[f"E_{name}"] = sgrid.T.dot(w / w.sum())
    return t, reg


def round6_weights(index):
    hs = [hname(h) for h in HYP6]
    return {"uniform": pd.Series(prior_weights6("uniform"), index=hs).reindex(index),
            "diagnosis": pd.Series(prior_weights6("diagnosis"), index=hs).reindex(index)}
