"""Round-17 evaluation helpers: R3_T / REF predictors, case metrics and paired statistics."""
import numpy as np
import pandas as pd

from common17 import H
from preds5c import ens, s_pred
from runner5c import COLD, PSEUDO, run
from smodel5c import LawFit

GAP = dict(steps=True, steps_mode="gap_endpoint", beta_mode="one")
R3_T_CFG = dict(law="two", sigma_s=0.10, transient_ref="restart", **GAP)
CAUSAL = PSEUDO + COLD
W_REF = 0.75


def stress_pred(name, cfg=None, cls=LawFit):
    return s_pred(name, cls=cls, cfg=dict(R3_T_CFG, **(cfg or {})), uses_steps=True)


def base_predictors():
    r3 = stress_pred("R3_T")
    return {"R3_T": r3, "V2": H.v2_pred, "REF": ens(r3, W_REF)}


def case_metrics(df):
    """MAE per (scenario, model, step, a4s, delta)."""
    keys = ["scenario", "model", "step", "a4s", "delta"]
    return df.groupby(keys)["err_pp"].agg(MAE=lambda e: e.abs().mean(), MAX=lambda e: e.abs().max(),
                                         n="count").reset_index()


def summary(df, delta=0.4, step="main", a4s=2.0):
    """Real MAE, pseudo and cold means (mean over scenario MAEs) per model, as in round 5C."""
    met = case_metrics(df)
    met = met[(met["delta"] == delta) & (met["step"] == step) & (met["a4s"] == a4s)]
    out = {}
    for m, g in met.groupby("model"):
        s = g.set_index("scenario")["MAE"]
        out[m] = dict(real=float(s.get("real", np.nan)),
                      pseudo=float(s.reindex(PSEUDO).mean()),
                      cold=float(s.reindex(COLD).mean()))
    return pd.DataFrame(out).T


def per_ck(df, model, scenario="real", delta=0.4, step="main", a4s=2.0):
    s = df[(df["model"] == model) & (df["scenario"] == scenario) & (df["delta"] == delta)
           & (df["step"] == step) & (df["a4s"] == a4s)]
    return s.set_index("k")["err_pp"].sort_index()


def paired(df, model, base, delta=0.4, step="main", a4s=2.0, scens=CAUSAL):
    """p_i = |err_model| - |err_base| per causal case, with k-block and leave-one-k-out stats."""
    s = df[(df["delta"] == delta) & (df["step"] == step) & (df["a4s"] == a4s) & df["scenario"].isin(scens)]
    a = s[s["model"] == model].set_index(["scenario", "k"])["err_pp"]
    b = s[s["model"] == base].set_index(["scenario", "k"])["err_pp"]
    idx = a.index.intersection(b.index)
    p = (a.loc[idx].abs() - b.loc[idx].abs()).rename("p").reset_index()
    blocks = p.groupby("k")["p"].mean()
    loko = {int(k): float(p[p["k"] != k]["p"].mean()) for k in blocks.index}
    return dict(n=int(len(p)), mean=float(p["p"].mean()), share_neg=float((p["p"] < 0).mean()),
                block_means={int(k): float(v) for k, v in blocks.items()},
                n_pos_blocks=int((blocks > 0).sum()), loko=loko, max_loko=float(max(loko.values())),
                worst=float(p["p"].max()), cases=p)


def pass_rule(st, st_q, st0, st8, delta_thr):
    """WP2 registered pass rule (1-6)."""
    c = {"1_mean_p": st["mean"] <= -delta_thr,
         "2_pos_blocks": st["n_pos_blocks"] <= 1,
         "3_loko": st["max_loko"] <= 0,
         "4_worst": st["worst"] <= 0.30,
         "5_mean_q": st_q["mean"] <= 0,
         "6_delta_0_08": st0["mean"] <= 0 and st8["mean"] <= 0}
    return all(c.values()), c


def noninferior_rule(st, delta_thr):
    c = {"mean_p": st["mean"] <= delta_thr, "worst": st["worst"] <= 0.10}
    return all(c.values()), c


__all__ = ["H", "run", "ens", "stress_pred", "base_predictors", "summary", "per_ck", "paired", "pass_rule",
           "noninferior_rule", "CAUSAL", "PSEUDO", "COLD", "R3_T_CFG", "W_REF", "LawFit"]
