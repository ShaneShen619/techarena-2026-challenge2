"""WP3 evaluation (protocol.json incl. amendment_1): leaderboard-only SOH tables and WP1-grid scores."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
sys.path.insert(0, os.path.join(STUDY, "sources", "v3"))
sys.path.insert(0, os.path.join(STUDY, "wp2"))
sys.path.insert(0, os.path.join(STUDY, "wp1"))
from common6 import H  # noqa: E402
from runner5c import run  # noqa: E402
from v2 import theil_sen  # noqa: E402
from v3 import v3  # noqa: E402
import run_wp2 as W2  # noqa: E402

OUT = os.path.join(HERE, "outputs")
AUD = pd.read_csv(os.path.join(OUT, "wp3a_start_state.csv"), parse_dates=["t_end"])
PRM = json.load(open(os.path.join(STUDY, "wp2", "outputs", "wp2_selection.json")))["params"]


# ---------------------------------------------------------------- 3a: anchor correction
def dr_map(ref_anchor, half):
    r = AUD.set_index("anchor")["r_upper"] * (0.5 if half else 1.0)
    ref = r.loc[ref_anchor]
    m = {}
    for _, row in AUD.iterrows():
        a = int(row["anchor"])
        if ref_anchor == 1 and a == 0:
            m[row["t_end"]] = 0.0
        else:
            m[row["t_end"]] = float(r.loc[a] - ref)
    return m


def with_3a(f, ref_anchor, half, tag):
    dm = dr_map(ref_anchor, half)

    def g(ctx):
        c = dict(ctx)
        fc = ctx["fc"].copy()
        if len(fc):
            fc["Q_Ah"] = fc["Q_Ah"] + fc["t_end"].map(lambda t: dm.get(pd.Timestamp(t), 0.0))
        c["fc"] = fc
        c["key"] = ctx["key"] + "|" + tag
        return f(c)
    return g


# ---------------------------------------------------------------- 3b: eps drift
def with_3b(f, d):
    def g(ctx):
        out = f(ctx)
        q, info = out if isinstance(out, tuple) else (out, {})
        return q + d * max(0.0, 100.41 - q), info
    return g


# ---------------------------------------------------------------- 3c: path effect
def sub_3c(ctx):
    q0, br, b = v3(ctx["fc"], ctx["steps"][ctx["step"]], ctx["a4"][ctx["a4s"]], ctx["ck"], ctx["k"], ctx["eps"],
                   use_sqrt=True, beta_cap=float("inf"), median=False)
    if br != "fallback" or ctx["fc"].empty:
        return q0, {"branch": br, "path_changed": False}
    fc = ctx["fc"].sort_values("t_end")
    last = fc.iloc[-1]
    base = 100.41 if last["setpoint_C"] == 45 else float(last["Q_Ah"]) + ctx["eps"]
    st = ctx["steps"][ctx["step"]].dropna(subset=["step_mean"]).sort_values("t_cv_end")
    s = st[st["t_cv_end"] >= last["t_end"] - pd.Timedelta(minutes=10)]
    if len(s) < 3:
        return q0, {"branch": br, "path_changed": False}
    p1, rest = s.iloc[0], s.iloc[1:]
    days = (rest["t_cv_end"] - p1["t_cv_end"]).dt.total_seconds().to_numpy() / 86400
    y = rest["step_mean"].to_numpy()
    rate = theil_sen(days, y) if len(rest) >= 3 else (y[-1] - y[0]) / max(days[-1] - days[0], 1e-9)
    q = base + (y[-1] - y[0]) + rate * (days[0] - 0.0)
    return float(q), {"branch": br, "path_changed": True}


# ---------------------------------------------------------------- model set
def build():
    SUB = W2.sub_pred
    F2A, F1A = W2.fused("S_A", "F2", PRM), W2.fused("S_A", "F1", PRM)

    def fused_3c(mode):
        S = W2.SVAR["S_C"]

        def f(ctx):
            qs, i_s = S(ctx)
            qu, i_u = sub_3c(ctx)
            c = W2.cls_of(i_s, i_u)
            if mode == "F1":
                s2s = i_s["q_sd"] ** 2 + PRM["sigma_S0"]["S_C"] ** 2
                su = PRM["sigma_SUB"].get(i_u["branch"], PRM["sigma_SUB"]["pooled"])
                w = su ** 2 / (s2s + su ** 2)
            else:
                w = PRM["F2_w"]["S_C"].get(c, 0.5)
            return w * qs + (1 - w) * qu, {"w": w}
        return f
    bases = {"SUB": (SUB, sub_3c), "F2_S_A": (F2A, fused_3c("F2")), "F1_S_A": (F1A, fused_3c("F1"))}
    P = {}
    for b, (f, f3c) in bases.items():
        P[f"{b}|base"] = f
        P[f"{b}|3a"] = with_3a(f, 0, False, "3a")
        P[f"{b}|3a_half"] = with_3a(f, 0, True, "3a_half")
        P[f"{b}|3a_ref1"] = with_3a(f, 1, False, "3a_ref1")
        P[f"{b}|3a_ref1_half"] = with_3a(f, 1, True, "3a_ref1_half")
        for d in (-0.031, -0.020, -0.035):
            P[f"{b}|3b{d}"] = with_3b(f, d)
        P[f"{b}|3c"] = f3c
        P[f"{b}|combined"] = with_3b(with_3a(f3c, 0, False, "3a_c"), -0.031)
        P[f"{b}|combined_ref1"] = with_3b(with_3a(f3c, 1, False, "3a_ref1_c"), -0.031)
    return P


if __name__ == "__main__":
    import run_wp1 as W1
    P = build()
    df = run(P, ("real",), deltas=(0.4,))
    df.to_csv(os.path.join(OUT, "wp3_real_predictions_d04.csv"), index=False)
    soh = df.pivot_table(index="model", columns="checkup", values="SOH")
    soh.round(3).to_csv(os.path.join(OUT, "wp3_leaderboard_only_SOH.csv"))
    base = pd.read_csv(os.path.join(STUDY, "wp1", "outputs", "wp1_predictions.csv"))
    base = base[(base.scenario == "real") & (base.step == "main") & (base.a4s == 2.0)][["scenario", "k", "model", "Q"]]
    add = df[["scenario", "k", "model", "Q"]]
    sc = W1.scores(pd.concat([base, add], ignore_index=True))
    cand = [m for m in sc.model.unique() if m != "EX"]
    real = sc[sc.scenario == "real"].pivot_table(index="h", columns="model", values="s")[cand]
    t, reg = W1.decision(real)
    t.to_csv(os.path.join(OUT, "wp3_hypothesis_decision_table.csv"))
    reg.to_csv(os.path.join(OUT, "wp3_regret_by_h.csv"))
    real.to_csv(os.path.join(OUT, "wp3_s_by_h.csv"))
    pd.set_option("display.width", 240)
    print(soh.round(3).to_string())
    keep = [m for m in t.index if "|" in m] + ["SUB", "R3_TD_w0.75", "V3"]
    print(t.loc[[m for m in keep if m in t.index]].round(4).sort_values("max_regret").to_string())
