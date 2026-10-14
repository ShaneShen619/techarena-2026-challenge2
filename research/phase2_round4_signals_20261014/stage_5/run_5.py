"""Stage 5 (descriptive, nothing tuned): post-checkup recovery size and time constant, and the
sensitivity of the M4/V2 ranking to whether the hidden C/20 reflects the pre- or post-recovery state."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))
from common4 import H  # noqa: E402
from v2 import anchors_by_checkup, month_steps  # noqa: E402

OUT = os.path.join(HERE, "outputs")
op = H.full_op()
fc, st, _ = H.tables(op, "real_full")
st = st["main"].dropna(subset=["step_mean"]).sort_values("t_cv_end")
anc = anchors_by_checkup(fc, H.CK)

# --- 1. jumps across checkups and bridges within months
rows = []
for m in range(1, 8):
    pre = st[st["t_cv_end"] < H.CK[m]]
    post = month_steps(st, anc, m)
    if pre.empty or post.empty:
        continue
    a, b = pre.iloc[-1], post.iloc[0]
    mon = month_steps(st, anc, m)
    s25, s45 = mon[mon.setpoint_C == 25], mon[mon.setpoint_C == 45]
    bridge = float(s45.step_mean.iloc[0] - s25.step_mean.iloc[-1]) if len(s25) and len(s45) else np.nan
    rows.append(dict(checkup=f"CK{m}", last_pre=a.t_cv_end, pre_sp=int(a.setpoint_C), first_post=b.t_cv_end,
                     post_sp=int(b.setpoint_C), gap_days=(b.t_cv_end - a.t_cv_end).total_seconds() / 86400,
                     jump_Ah=float(b.step_mean - a.step_mean), bridge_next_Ah=bridge))
J = pd.DataFrame(rows)
delta = float(J["bridge_next_Ah"].iloc[2:].median())          # months 3.. (month 1 bridge spans the missing segment)
r45 = -0.025                                                    # typical 45 C step rate (Ah/day), descriptive
J["recovery_Ah"] = J["jump_Ah"] + np.where(J.pre_sp == 45, delta, 0.0) - r45 * J["gap_days"] * 0.0
J["recovery_Ah_with_aging"] = J["jump_Ah"] + np.where(J.pre_sp == 45, delta, 0.0) - r45 * J["gap_days"]

# --- 2. transient time constant: pooled fit over months 2..6 (25 C then 45 C segment)
pts = []
for m in range(2, 7):
    mon = month_steps(st, anc, m)
    if len(mon) < 4:
        continue
    t0 = anc[m]["t_end"]
    s0 = mon.step_mean.iloc[0]
    for _, r in mon.iterrows():
        pts.append(dict(month=m, t=(r.t_cv_end - t0).total_seconds() / 86400, ds=r.step_mean - s0,
                        hot=float(r.setpoint_C == 45)))
P = pd.DataFrame(pts)
t1 = P.groupby("month")["t"].transform("min")
prof = []
for tau in np.r_[np.arange(0.5, 10, 0.25), np.arange(10, 61, 1.0)]:
    # ds = A*(exp(-(t - t1)/tau) - 1) + r*(t - t1) + delta_fit*hot   (relative to the first step of the month)
    tt = P.t - t1
    X = np.c_[np.exp(-tt / tau) - 1, tt, P.hot]
    coef, *_ = np.linalg.lstsq(X, P.ds, rcond=None)
    prof.append(dict(tau=tau, sse=float(((X @ coef - P.ds) ** 2).sum()), A=coef[0], r=coef[1], delta=coef[2]))
prof = pd.DataFrame(prof)
best = prof.loc[prof.sse.idxmin()]
n = len(P)
ok = prof[n * np.log(prof.sse / best.sse) <= 3.84]

# --- 3. ranking sensitivity: proxies shifted to a pre-recovery state (descriptive)
pred = H.run(H.BASELINES, scenarios=("real",), deltas=(0.4,))
rec = J.set_index("checkup")["recovery_Ah_with_aging"]
sens = []
for frac in (0.0, 0.5, 1.0):
    for mod in ("M4", "V2"):
        g = pred[pred.model == mod].copy()
        shift = g["checkup"].map(rec).fillna(0.0).clip(lower=0.0) * frac
        e = (g["Q"] - (g["proxy"] - shift)) / H.NOM * 100
        sens.append(dict(fraction_pre=frac, model=mod, MAE=float(e.abs().mean()), MAX=float(e.abs().max()),
                         **{c: round(float(x), 3) for c, x in zip(g["checkup"], e)}))
S = pd.DataFrame(sens)
J.to_csv(os.path.join(OUT, "jumps.csv"), index=False)
prof.to_csv(os.path.join(OUT, "tau_profile.csv"), index=False)
S.to_csv(os.path.join(OUT, "ranking_sensitivity.csv"), index=False)
summ = dict(delta_bridge_median=delta, tau_best_days=float(best.tau), tau_95=[float(ok.tau.min()), float(ok.tau.max())],
            A_best=float(best.A), r_best=float(best.r), delta_fit=float(best.delta), n_points=n)
json.dump(summ, open(os.path.join(OUT, "summary.json"), "w"), indent=1)
pd.set_option("display.width", 220)
print(J.round(3).to_string(index=False))
print(json.dumps(summ, indent=1))
print(S.to_string(index=False))
