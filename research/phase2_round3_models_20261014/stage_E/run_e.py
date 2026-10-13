"""Stage E: four-cell pack-cutoff / eps-drift scenarios (stage_E/protocol.json). Not scored."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))
import harness as H  # noqa: E402
from events import CELLS  # noqa: E402
from framework.data import load_reference_discharge  # noqa: E402
from v2 import anchors_by_checkup, month_steps  # noqa: E402

OUT = os.path.join(HERE, "outputs")
ref = load_reference_discharge(H.DATA)
d = ref["discharged_Ah"].to_numpy(float)
Q0 = d.max()
VC = {c: ref[c].to_numpy(float) for c in CELLS}


def remaining(v0, c):
    """Ah left to the end of the CK0 loaded curve at voltage v0 (first crossing)."""
    below = np.where(VC[c] <= v0)[0]
    return Q0 - d[below[0]] if len(below) else 0.0


def pack_root_extra(r):
    """Smallest x >= 0 with sum_i V_i(Q0 - r_i + x) <= 11.2 (Ah still dischargeable)."""
    xs = np.arange(0.0, 5.0, 0.005)
    tot = sum(np.interp(Q0 - r[i] + xs, d, VC[c], right=VC[c][-1] - 1.0) for i, c in enumerate(CELLS))
    hit = np.where(tot <= 11.2)[0]
    return float(xs[hit[0]]) if len(hit) else np.nan


op = H.cut_op(7)
fc, st, _ = H.tables(op, "real_ck7")
fc = fc.sort_values("t_end").reset_index(drop=True)
anc = anchors_by_checkup(fc, H.CK)
s1 = []
for dv in (0.0, 0.05, 0.10):
    for j, a in sorted(anc.items()):
        r = [remaining(a[f"start_{c}"] - dv, c) for c in CELLS]
        s1.append(dict(dV=dv, anchor=j, setpoint=int(a["setpoint_C"]), r_min=min(r), r_max=max(r),
                       x_star=pack_root_extra(r)))
s1 = pd.DataFrame(s1)
s1["drift_vs_anchor1_pp"] = np.nan
for dv, g in s1.groupby("dV"):
    x1 = g.loc[g.anchor == 1, "x_star"].iloc[0]
    s1.loc[g.index, "drift_vs_anchor1_pp"] = (g["x_star"] - x1) / H.NOM * 100
s1.loc[s1.anchor < 2, "drift_vs_anchor1_pp"] = np.where(s1.loc[s1.anchor < 2, "anchor"] == 1, 0.0, np.nan)

st_main = st["main"].dropna(subset=["step_mean"])
s2 = []
for m in range(0, 7):
    s = month_steps(st_main, anc, m)
    s = s[s["setpoint_C"] == 45]
    if s.empty:
        continue
    rel = np.array([(s[f"step_{c}"] - s["step_mean"]).mean() for c in CELLS])
    s2.append(dict(month=m, checkup_after=m + 1, n45=len(s), **{f"rel_{c}": x for c, x in zip(CELLS, rel)},
                   max_rel=float(rel.max()), range_rel=float(rel.max() - rel.min())))
s2 = pd.DataFrame(s2)
base = s2.loc[s2.month == 1, "max_rel"].iloc[0] if (s2.month == 1).any() else s2["max_rel"].iloc[0]
s2["drift_vs_month1_pp"] = -(s2["max_rel"] - base) / H.NOM * 100

s1.to_csv(os.path.join(OUT, "E_S1_no_cancellation.csv"), index=False)
s2.to_csv(os.path.join(OUT, "E_S2_cell_limited_top.csv"), index=False)
summ = dict(
    S0="drift 0 by construction",
    S1_max_abs_drift_pp={str(dv): float(g.loc[g.anchor >= 2, "drift_vs_anchor1_pp"].abs().max()) for dv, g in s1.groupby("dV")},
    S1_anchor0_x_star_vs_eps0={str(dv): float(g.loc[g.anchor == 0, "x_star"].iloc[0]) for dv, g in s1.groupby("dV")},
    S2_max_abs_drift_pp=float(s2["drift_vs_month1_pp"].abs().max()),
    eps0=float(H.EPS0))
json.dump(summ, open(os.path.join(OUT, "E_summary.json"), "w"), indent=1)
pd.set_option("display.width", 200)
print(s1.round(3).to_string(index=False))
print(s2.round(3).to_string(index=False))
print(json.dumps(summ, indent=1))

# ---- leaderboard-only variant (registered decision rule): V2 with eps_(k-1) = x*_(k-1)(S1, dV 0.05)
xs = s1[s1.dV == 0.05].set_index("anchor")["x_star"]


def v2_s1(ctx):
    q, info = H.v2_pred(ctx)
    a = anchors_by_checkup(ctx["fc"], ctx["ck"])
    j = max(a)
    if j == 0 or j not in xs.index:
        return q, info
    return q - ctx["eps"] + float(xs[j]), dict(info, eps_used=float(xs[j]))


lb = H.run({"V2": H.v2_pred, "V2_S1": v2_s1}, scenarios=("real",), deltas=(0.4,))
tab = lb.pivot_table(index="checkup", columns="model", values="SOH")
tab["diff_pp"] = tab["V2_S1"] - tab["V2"]
tab.to_csv(os.path.join(OUT, "E_leaderboard_only_V2_S1.csv"))
print(tab.round(3))
