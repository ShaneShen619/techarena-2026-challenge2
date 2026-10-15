"""WP1: hypothesis-robust selection among existing models (protocol.json)."""
import importlib.util
import itertools
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
WT = os.path.dirname(os.path.dirname(STUDY))
sys.path.insert(0, os.path.join(STUDY, "src"))
sys.path.insert(0, os.path.join(STUDY, "sources", "v3"))
from common6 import H  # noqa: E402
from framework.data import Dataset, load_dataset  # noqa: E402
from preds5c import ens, s_pred  # noqa: E402
from runner5c import COLD, PSEUDO, run  # noqa: E402
from smodel5c import LawFit  # noqa: E402
from v3 import v3  # noqa: E402

OUT = os.path.join(HERE, "outputs")
PROTO = json.load(open(os.path.join(HERE, "protocol.json")))
PKG = os.path.join(STUDY, "cache", "submitted_package", "TechArena_Challenge2_Team_Package")
SCENS = ("real",) + PSEUDO + COLD

# ------------------------------------------------------------------ candidates
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


GAP = dict(steps=True, steps_mode="gap_endpoint", beta_mode="one", sigma_s=0.10)
S5A = s_pred("S_main")
R2B = s_pred("R2_B", cls=LawFit, cfg=dict(law="two", **GAP), uses_steps=True)
R3T = s_pred("R3_T", cls=LawFit, cfg=dict(law="two", transient_ref="restart", **GAP), uses_steps=True)
P = {"EX": ex_pred, "M4": H.BASELINES["M4"], "V2": H.BASELINES["V2"],
     "SUB": v3_pred(use_sqrt=True, beta_cap=float("inf"), median=False),
     "SUB_bcap": v3_pred(use_sqrt=True, beta_cap=1.2, median=False),
     "V3": v3_pred(use_sqrt=True, beta_cap=1.2, median=True),
     "S_main_5A": S5A, "ENS50_5A": ens(S5A, 0.5), "R2_B": R2B, "R2_D_w0.75": ens(R2B, 0.75),
     "R3_T": R3T, "R3_TD_w0.75": ens(R3T, 0.75)}
EXPOSED = {"SUB": "CK2", "SUB_bcap": "CK2", "V3": "CK2", "R3_T": "CK1", "R3_TD_w0.75": "CK1"}

# ------------------------------------------------------------------ hypotheses
J = pd.read_csv(os.path.join(WT, "research", "phase2_round4_signals_20261014", "stage_5", "outputs", "jumps.csv"))
R = dict(zip(J["checkup"], J["recovery_Ah_with_aging"].astype(float)))
HYP = [dict(Delta=a, f=b, d=c) for a, b, c in itertools.product(PROTO["hypotheses"]["Delta"], PROTO["hypotheses"]["f"],
                                                                 PROTO["hypotheses"]["d_Ah_per_Ah"])]


def target(k, h):
    p = H.QFC[k] + H.EPS0
    L = max(0.0, 100.41 - p)
    return p + h["Delta"] - h["f"] * R[H.CK_NAMES[k]] + h["d"] * L


def hname(h):
    return f"D{h['Delta']}_f{h['f']}_d{h['d']}"


def prior_weights(kind):
    if kind == "uniform":
        return np.full(len(HYP), 1.0 / len(HYP))
    fw, dw = {0.0: 0.6, 0.5: 0.3, 1.0: 0.1}, {0.0: 0.5, -0.031: 0.5}
    w = np.array([fw[h["f"]] * dw[h["d"]] / 3.0 for h in HYP])
    return w / w.sum()


def scores(pred):
    """pred: rows (scenario, k, model, Q). Returns DataFrame s[scenario, h, model] plus raw MAE/MAX."""
    rows = []
    for (scen, model), g in pred.groupby(["scenario", "model"]):
        g = g.sort_values("k")
        for h in HYP:
            e = (g["Q"].to_numpy() - np.array([target(k, h) for k in g["k"]])) / H.NOM * 100
            rows.append(dict(scenario=scen, model=model, h=hname(h), MAE=np.mean(np.abs(e)),
                             RMSE=np.sqrt(np.mean(e ** 2)), MAX=np.max(np.abs(e)), n=len(e)))
    d = pd.DataFrame(rows)
    ex = d[d.model == "EX"].set_index(["scenario", "h"])[["MAE", "RMSE", "MAX"]]
    d = d.join(ex, on=["scenario", "h"], rsuffix="_EX")
    d["s"] = (d["MAE"] / d["MAE_EX"] + d["RMSE"] / d["RMSE_EX"] + d["MAX"] / d["MAX_EX"]) / 3.0
    return d


def decision(sgrid):
    """sgrid: index h, columns models (EX excluded). Returns decision table."""
    best = sgrid.min(axis=1)
    reg = sgrid.sub(best, axis=0)
    hs = [hname(h) for h in HYP]
    t = pd.DataFrame({"worst_s": sgrid.max(), "max_regret": reg.max(),
                      "E_uniform": sgrid.loc[hs].T.dot(prior_weights("uniform")),
                      "E_diagnosis": sgrid.loc[hs].T.dot(prior_weights("diagnosis")),
                      "s_at_D0.4_f0_d0": sgrid.loc["D0.4_f0.0_d0.0"]})
    return t, reg


def choose(t):
    m = t["max_regret"].min()
    tied = t[t["max_regret"] <= m + 0.01]
    return str(tied["E_diagnosis"].idxmin()), list(tied.index)


if __name__ == "__main__":
    df = run(P, SCENS, deltas=(0.4,))
    df.to_csv(os.path.join(OUT, "wp1_predictions.csv"), index=False)
    sc = scores(df[["scenario", "k", "model", "Q"]])
    sc.to_csv(os.path.join(OUT, "wp1_scores_long.csv"), index=False)
    cand = [m for m in P if m != "EX"]
    real = sc[sc.scenario == "real"].pivot_table(index="h", columns="model", values="s")[cand]
    causal = sc[sc.scenario != "real"].groupby(["h", "model"])["s"].mean().unstack()[cand]
    t_real, reg_real = decision(real)
    t_caus, reg_caus = decision(causal)
    pick_real, tied_real = choose(t_real)
    pick_caus, tied_caus = choose(t_caus)
    rank = {f"real_{c}": t_real[c].rank().astype(int).to_dict() for c in ("max_regret", "E_uniform", "E_diagnosis", "worst_s")}
    rank.update({f"causal_{c}": t_caus[c].rank().astype(int).to_dict() for c in ("max_regret", "E_uniform", "E_diagnosis", "worst_s")})
    raw = sc[(sc.scenario == "real")].pivot_table(index="h", columns="model", values="MAE")[cand]
    rawmax = sc[(sc.scenario == "real")].pivot_table(index="h", columns="model", values="MAX")[cand]
    t_real.join(t_caus, rsuffix="_causal").to_csv(os.path.join(OUT, "wp1_decision_table.csv"))
    real.to_csv(os.path.join(OUT, "wp1_s_real_by_h.csv"))
    causal.to_csv(os.path.join(OUT, "wp1_s_causal_by_h.csv"))
    reg_real.to_csv(os.path.join(OUT, "wp1_regret_real_by_h.csv"))
    raw.to_csv(os.path.join(OUT, "wp1_rawMAE_real_by_h.csv"))
    rawmax.to_csv(os.path.join(OUT, "wp1_rawMAX_real_by_h.csv"))
    best_by_h = real.idxmin(axis=1).to_dict()
    out = dict(robust_choice_real=pick_real, tied_real=tied_real, robust_choice_causal=pick_caus, tied_causal=tied_caus,
               agree=bool(pick_real == pick_caus), best_model_per_h_real=best_by_h, ranks=rank,
               exposed=EXPOSED, R_k=R)
    json.dump(out, open(os.path.join(OUT, "wp1_choice.json"), "w"), indent=1)
    # heat map
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(15, 7), sharey=True)
    for a, g, ttl in ((ax[0], real, "real grid (exposed proxies)"), (ax[1], causal, "causal grid (pseudo + cold start)")):
        im = a.imshow(g.values, aspect="auto", cmap="viridis_r")
        a.set_xticks(range(len(g.columns)))
        a.set_xticklabels(g.columns, rotation=60, ha="right", fontsize=8)
        a.set_yticks(range(len(g.index)))
        a.set_yticklabels(g.index, fontsize=7)
        a.set_title(ttl, fontsize=10)
        for i in range(g.shape[0]):
            for j in range(g.shape[1]):
                a.text(j, i, f"{g.values[i, j]:.3f}", ha="center", va="center", fontsize=5,
                       color="w" if g.values[i, j] > np.nanmedian(g.values) else "k")
        fig.colorbar(im, ax=a, fraction=0.03)
    fig.suptitle("Normalised score s_h(m) (ExampleModel = 1; lower is better)", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "wp1_heatmap.png"), dpi=130)
    pd.set_option("display.width", 220)
    print(t_real.join(t_caus, rsuffix="_c").round(4).sort_values("max_regret").to_string())
    print(json.dumps({k: v for k, v in out.items() if k not in ("ranks", "best_model_per_h_real")}, indent=1))
    print(pd.Series(best_by_h).value_counts().to_string())
