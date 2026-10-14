"""Stage 6 (leaderboard-only): V2 with a temperature-based anchor offset eps0 + delta_k."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))
from common4 import H  # noqa: E402
from v2 import anchors_by_checkup, month_steps  # noqa: E402


def delta_k(ctx):
    st = ctx["steps"]["main"].dropna(subset=["step_mean"])
    anc = anchors_by_checkup(ctx["fc"], ctx["ck"])
    br = []
    for m in sorted(anc):
        mon = month_steps(st, anc, m)
        s25, s45 = mon[mon.setpoint_C == 25], mon[mon.setpoint_C == 45]
        if len(s25) and len(s45):
            br.append(float(s45.step_mean.iloc[0] - s25.step_mean.iloc[-1]))
    return (float(np.mean(br)) if br else 0.4), len(br)


def v2_epsT(ctx):
    q, info = H.v2_pred(ctx)
    anc = anchors_by_checkup(ctx["fc"], ctx["ck"])
    j = max(anc)
    d, n = delta_k(ctx)
    if j == 0 or anc[j]["setpoint_C"] != 25:
        return q, dict(info, delta_k=d, n_bridges=n)
    return q - ctx["eps"] + (ctx["eps0"] + d), dict(info, delta_k=d, n_bridges=n)


df = H.run({"V2": H.v2_pred, "V2_epsT": v2_epsT}, scenarios=("real",), deltas=(0.4,))
t = df.pivot_table(index="checkup", columns="model", values="SOH")
t["diff_pp"] = t["V2_epsT"] - t["V2"]
dk = df[df.model == "V2_epsT"].set_index("checkup")[["delta_k", "n_bridges"]]
t = t.join(dk)
t.to_csv(os.path.join(HERE, "outputs", "V2_epsT_table.csv"))
print(t.round(3))
