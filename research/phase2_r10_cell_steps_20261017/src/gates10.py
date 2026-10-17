"""Common gates of round 10 (EXECUTION_PROMPT.md section 4) and the run helpers."""
import os

import numpy as np
import pandas as pd

from common10 import H, STUDY
from runner5c import COLD, PSEUDO, run, scen_mean
import tsqrt as T
from residuals10 import r_anc_b

SCENS = ("real",) + PSEUDO + COLD + ("PC5_all", "PC10_all")
VARIANTS = tuple(H.VARIANTS)
SUB = T.design_pred("T_main")
R8_EVENTS = os.path.join(os.path.dirname(STUDY), "phase2_r8_error_table_20261017", "outputs", "table_events.csv")


def predict(preds, variants=("main",), deltas=H.DELTAS, scens=SCENS):
    return run(preds, scens, variants=variants, deltas=deltas)


def causal(met, model, step="main"):
    p, c = scen_mean(met, PSEUDO, model, step=step), scen_mean(met, COLD, model, step=step)
    return p, c, (p + c) / 2


def real_mae(met, model, step="main", delta=0.4):
    m = met[(met.scenario == "real") & (met.model == model) & (met.step == step) & (met.delta == delta)]
    return float(m["MAE"].iloc[0])


def real_max(met, model, delta, step="main"):
    m = met[(met.scenario == "real") & (met.model == model) & (met.step == step) & (met.delta == delta)]
    return float(m["MAX"].iloc[0])


def changed(df, model, ref="SUB", step="main"):
    d = df[(df.delta == 0.4) & (df.step == step)]
    a = d[d.model == model].set_index(["scenario", "k"])
    b = d[d.model == ref].set_index(["scenario", "k"])
    diff = (a["Q"] - b["Q"]).abs()
    idx = [i for i in diff.index if i[0] != "real" and diff[i] > 1e-9]
    if not idx:
        return dict(n=0, mae_ref=np.nan, mae_cand=np.nan, worst=np.nan, passed=False, cases=[])
    e0, e1 = b.loc[idx, "err_pp"].abs(), a.loc[idx, "err_pp"].abs()
    worst = float((e1 - e0).max())
    return dict(n=len(idx), mae_ref=float(e0.mean()), mae_cand=float(e1.mean()), worst=worst,
                passed=bool(e0.mean() - e1.mean() >= 0.02 and worst <= 0.10),
                cases=[dict(scenario=i[0], k=int(i[1]), err_ref=float(b.loc[i, "err_pp"]), err_cand=float(a.loc[i, "err_pp"]))
                       for i in idx])


def robust_rows(met, pairs):
    """pairs: list of (label, cand_model, cand_step, ref_model, ref_step). Returns rows + verdict pieces."""
    rows = []
    for lab, cm, cs, rm, rs in pairs:
        _, _, cc = causal(met, cm, cs)
        _, _, rc = causal(met, rm, rs)
        rows.append(dict(label=lab, causal_cand=cc, causal_ref=rc, d_causal=cc - rc,
                         real_cand=real_mae(met, cm, cs), real_ref=real_mae(met, rm, rs),
                         d_real=real_mae(met, cm, cs) - real_mae(met, rm, rs)))
    t = pd.DataFrame(rows)
    ok5 = int((t["d_causal"] <= 0.005 + 1e-12).sum())
    passed = bool(ok5 >= 5 and (t["d_causal"] <= 0.03).all() and (t["d_real"] <= 0.05).all())
    return t, dict(n_within_0p005=ok5, max_d_causal=float(t["d_causal"].max()), max_d_real=float(t["d_real"].max()),
                   passed=passed)


# ------------------------------------------------------------------ G_event
def full_events():
    e = pd.read_csv(R8_EVENTS, parse_dates=["t_cv_end"])
    e = e[e.unit == "pack_mean"][["t_cv_end", "segment", "setpoint", "month", "Q_interp_Ah", "t_days"]]
    return e.set_index("t_cv_end")


def event_sd(series):
    """SD of the leave-month-out free-slope residual (R_anc_b) of a pack step series over bracketed events."""
    e = full_events().copy()
    e["depth"] = series.reindex(e.index).to_numpy(float)
    r = r_anc_b(e.reset_index(), "depth")
    return float(np.nanstd(r.to_numpy(float), ddof=1)), int(np.isfinite(r).sum())


def gate_table(name, met, df, robust, ev_sd, ev_sd_ref):
    p, c, cc = causal(met, name)
    ps, cs, ccs = causal(met, "SUB")
    ch = changed(df, name)
    safety = all(real_max(met, name, d) <= real_max(met, "SUB", d) + 0.10 for d in H.DELTAS)
    g = dict(candidate=name, pseudo=p, pseudo_SUB=ps, cold=c, cold_SUB=cs, causal=cc, causal_SUB=ccs,
             G_pseudo=bool(p <= ps + 0.005), G_cold=bool(c <= cs + 0.005),
             changed_n=ch["n"], changed_mae_SUB=ch["mae_ref"], changed_mae=ch["mae_cand"], changed_worst=ch["worst"],
             G_changed=ch["passed"], robust_n_within=robust["n_within_0p005"], robust_max_d_causal=robust["max_d_causal"],
             robust_max_d_real=robust["max_d_real"], G_robust=robust["passed"], event_sd=ev_sd, event_sd_SUB=ev_sd_ref,
             G_event=bool(ev_sd <= 1.02 * ev_sd_ref),
             real_MAE_d0=real_mae(met, name, delta=0.0), real_MAE_d04=real_mae(met, name), real_MAE_d08=real_mae(met, name, delta=0.8),
             real_MAX_d04=real_max(met, name, 0.4), G_real_safety=bool(safety))
    g["passes"] = bool(g["G_pseudo"] and g["G_cold"] and g["G_changed"] and g["G_robust"] and g["G_event"] and g["G_real_safety"])
    return g, ch
