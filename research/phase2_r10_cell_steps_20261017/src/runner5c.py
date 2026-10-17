"""Round-5C evaluation runner: the round-3 harness scenarios plus cold-start scenarios CS / CSE.

CS (k = 3..7): the real CK_k cut, with every anchor before anchor k-1 removed from fc and every
program step / A4 row before anchor k-1 removed. The stress history (time, temperature, throughput)
is kept, as at CK1, where the full history is known but no anchor pair exists.
CSE: the same on the PC10 cut (operation data cut 10 days before CK_k).
"""
import numpy as np
import pandas as pd

from common10 import H
from v2 import anchors_by_checkup

CS_K = (3, 4, 5, 6, 7)
SCEN = {"real": [(k, None) for k in range(1, 8)],
        "PG1": [(k, ("gap", 1)) for k in range(4, 8)],
        "PG2": [(k, ("gap", 2)) for k in range(4, 8)],
        "PC5": [(k, ("cut", 5)) for k in range(3, 8)],
        "PC10": [(k, ("cut", 10)) for k in range(3, 8)],
        "PC5_all": [(k, ("cut", 5)) for k in range(2, 8)],
        "PC10_all": [(k, ("cut", 10)) for k in range(2, 8)],
        "CS": [(k, ("cs", None)) for k in CS_K],
        "CSE": [(k, ("cs", 10)) for k in CS_K]}
PSEUDO = ("PG1", "PG2", "PC5", "PC10")
COLD = ("CS", "CSE")


def cold_filter(fc, st, a4, k):
    anc = anchors_by_checkup(fc, H.CK)
    if (k - 1) not in anc:
        return fc, st, a4
    a = anc[k - 1]
    fc2 = fc[fc["t_end"] >= a["t_end"]].reset_index(drop=True)
    st2 = {v: s[s["t_cv_end"] >= a["t_start"]].reset_index(drop=True) for v, s in st.items()}
    a42 = {s: t[t["segment"] >= a["segment"]].reset_index(drop=True) for s, t in a4.items()}
    return fc2, st2, a42


def scenario_tables(k, spec):
    if spec is not None and spec[0] == "cs":
        base = None if spec[1] is None else ("cut", spec[1])
        op, key = H.scenario_op(k, base)
        fc, st, a4 = H.tables(op, key)
        fc, st, a4 = cold_filter(fc, st, a4, k)
        return op, fc, st, a4, ("cs" if spec[1] is None else f"cse{spec[1]}") + f"_ck{k}"
    op, key = H.scenario_op(k, spec)
    if op is None:
        return None
    fc, st, a4 = H.tables(op, key)
    return op, fc, st, a4, key


def run(predictors, scenarios=("real",), variants=("main",), smooths=(2.0,), deltas=H.DELTAS):
    rows = []
    for scen in scenarios:
        for k, spec in SCEN[scen]:
            t = scenario_tables(k, spec)
            if t is None:
                continue
            op, fc, st, a4, key = t
            for d in deltas:
                for v in variants:
                    for s in smooths:
                        ctx = dict(k=k, at_date=H.CK[k], ck=H.CK, op=op, fc=fc, steps=st, step=v, a4=a4,
                                   a4s=s, eps=H.EPS0 + d, eps0=H.EPS0, delta=d, scenario=scen, key=key)
                        for name, f in predictors.items():
                            out = f(ctx)
                            q, info = (out if isinstance(out, tuple) else (out, {}))
                            proxy = H.QFC[k] + H.EPS0 + d
                            rows.append(dict(scenario=scen, checkup=H.CK_NAMES[k], k=k, delta=d, step=v, a4s=s,
                                             model=name, Q=float(q), proxy=float(proxy),
                                             err_pp=(float(q) - proxy) / H.NOM * 100, SOH=float(q) / H.NOM * 100,
                                             **{kk: vv for kk, vv in info.items() if np.isscalar(vv)}))
    return pd.DataFrame(rows)


def scen_mean(met, scens, model, delta=0.4, step="main", a4s=2.0):
    m = met[(met["model"] == model) & (met["delta"] == delta) & (met["step"] == step) & (met["a4s"] == a4s)
            & met["scenario"].isin(scens)]
    return float(m["MAE"].mean()) if len(m) else np.nan
