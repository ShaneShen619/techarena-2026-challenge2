"""WP1: case table, one row per (scenario, k, delta, model), with the error decomposition (EXECUTION_PROMPT.md, WP1)."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
from common8 import H  # noqa: E402
from runner5c import SCEN, scenario_tables  # noqa: E402
import internals as I  # noqa: E402

OUT = os.path.join(STUDY, "outputs")
SCENS = ("real", "PG1", "PG2", "PC5", "PC10", "CS", "CSE", "PC5_all", "PC10_all")
PP = 100.0 / H.NOM


def build():
    rows = []
    for scen in SCENS:
        for k, spec in SCEN[scen]:
            t = scenario_tables(k, spec)
            if t is None:
                continue
            op, fc, st, a4, key = t
            for d in H.DELTAS:
                ctx = dict(k=k, at_date=H.CK[k], ck=H.CK, op=op, fc=fc, steps=st, step="main", a4=a4, a4s=2.0,
                           eps=H.EPS0 + d, eps0=H.EPS0, delta=d, scenario=scen, key=key)
                for m in I.MODELS:
                    o = I.decompose(ctx, m)
                    q_model = float(I.model_q(ctx, m))
                    assert abs(o["Q_pred"] - q_model) < 1e-9, (scen, k, d, m, o["Q_pred"], q_model)
                    j = o["anchor_j"]
                    assert abs(o["Q_fc_anchor_used"] - H.QFC[j]) < 1e-9, (scen, k, j)
                    proxy = H.QFC[k] + H.EPS0 + d
                    err = o["Q_pred"] - proxy
                    inc_obs = H.QFC[k] - o["Q_fc_anchor_used"]
                    inc_res = o["increment_pred"] - inc_obs
                    r = dict(scenario=scen, k=k, checkup=H.CK_NAMES[k], ck_date=str(H.CK[k].date()), delta=d, model=m,
                             branch=o["branch"], Q_pred=o["Q_pred"], SOH_pred=o["Q_pred"] * PP, proxy=proxy,
                             err_Ah=err, err_pp=err * PP, anchor_used=j, anchor_t_end=str(o["anchor_t_end"]),
                             Q_fc_anchor_used=o["Q_fc_anchor_used"], q_anchor_term=o["q_anchor_term"],
                             increment_pred=o["increment_pred"], Q_fc_k=H.QFC[k], increment_obs=inc_obs,
                             inc_resid_Ah=inc_res, inc_resid_pp=inc_res * PP, offset_part_Ah=err - inc_res,
                             offset_part_pp=(err - inc_res) * PP,
                             uses_first_post_anchor_program=bool(o["branch"] == "fallback" and o["n_after"] >= 2),
                             anchor_setpoint=o["anchor_setpoint"],
                             anchor_is_ck0_45C=bool(j == 0 and o["anchor_setpoint"] == 45))
                    for c in ("beta_used", "beta_a4", "beta_raw", "beta_S", "beta_shrink_w", "beta_n_pairs", "x",
                              "E_cur", "E_prev", "d_cur", "d_prev", "r_cur", "r_used", "n_cur", "n_prev", "gap_days",
                              "sqrt_a", "sqrt_t_km1_days", "sqrt_t_k_days", "sqrt_anchors", "n_after",
                              "ev_E_cur", "ev_E_prev", "ev_rate_fit", "ev_after_first", "ev_after_last"):
                        r[c] = o.get(c, np.nan if not c.startswith(("ev_", "sqrt_anchors")) else "")
                    r.update(I.context(ctx, o))
                    rows.append(r)
    return pd.DataFrame(rows)


def offset_assertion(df):
    """offset_part depends only on (branch family, delta, anchor_is_ck0_45C), to 1e-9 Ah."""
    g = df.groupby(["branch", "delta", "anchor_is_ck0_45C"])["offset_part_Ah"]
    t = g.agg(n="count", value="mean", spread=lambda s: float(s.max() - s.min())).reset_index()
    t["expected"] = np.where(t["anchor_is_ck0_45C"] & (t["branch"] == "fallback"), -t["delta"], 0.0)
    t["passes"] = (t["spread"] <= 1e-9) & ((t["value"] - t["expected"]).abs() <= 1e-9)
    return t


def branch_summary(df):
    d = df[df["delta"] == 0.4]
    out = []
    for (m, b, real), g in d.groupby(["model", "branch", d["scenario"] == "real"]):
        e = g["inc_resid_Ah"]
        out.append(dict(model=m, branch=b, set="real" if real else "causal", n=len(g), mean_Ah=e.mean(),
                        median_Ah=e.median(), MAE_Ah=e.abs().mean(), mean_pp=e.mean() * PP, MAE_pp=e.abs().mean() * PP,
                        err_MAE_pp=g["err_pp"].abs().mean()))
    return pd.DataFrame(out)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.join(HERE, "outputs"), exist_ok=True)
    df = build()
    df.to_csv(os.path.join(OUT, "table_cases.csv"), index=False)
    wide = df[(df.model == "SUB") & (df.delta == 0.4)].reset_index(drop=True)
    wide.to_csv(os.path.join(OUT, "table_cases_wide.csv"), index=False)
    oa = offset_assertion(df)
    oa.to_csv(os.path.join(HERE, "outputs", "wp1_offset_assertion.csv"), index=False)
    bs = branch_summary(df)
    bs.to_csv(os.path.join(HERE, "outputs", "wp1_branch_summary.csv"), index=False)
    # consistency with WP0: SUB err_pp equals the WP0 predictions
    w0 = pd.read_csv(os.path.join(STUDY, "wp0", "outputs", "wp0_sub_predictions.csv"))
    mm = df[df.model == "SUB"].merge(w0, on=["scenario", "k", "delta"], suffixes=("", "_wp0"))
    chk = dict(n_rows=int(len(df)), n_cases_per_delta_model=int(len(wide)),
               offset_assertion_passes=bool(oa["passes"].all()),
               sub_equals_wp0_max_abs_pp=float((mm["err_pp"] - mm["err_pp_wp0"]).abs().max()),
               sub_branch_equals_wp0=bool((mm["branch"] == mm["branch_wp0"]).all()), n_matched=int(len(mm)))
    json.dump(chk, open(os.path.join(HERE, "outputs", "wp1_checks.json"), "w"), indent=1)
    pd.set_option("display.width", 220)
    print(json.dumps(chk, indent=1))
    print(oa.to_string())
    print(bs.round(4).to_string())
    if not chk["offset_assertion_passes"]:
        raise SystemExit("offset assertion failed")
