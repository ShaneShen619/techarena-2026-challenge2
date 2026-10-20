"""WP1 checks of the registered machinery (no current-SUB or probe numbers are computed here).

T1  p_k = Q_fc,k + eps0 from round 6's harness output equals an independent recomputation with the base
    events.full_charges (round 3 harness definition: QFC sorted by t_end, EPS0 = 100.41 - QFC[0]).
T2  grid15.raw_metrics / scores reproduce round 6's real-grid MAE, RMSE, MAX and s for all its 12 candidates x 18 h.
T3  grid15.delta_table reproduces round 6's P_drift delta-s vs SUB (wp6) with the 3b transform on round 6's SUB.
T4  readability, T5 reading rules, T6 surviving set: synthetic cases.
Run: python3 -B src/test_wp1.py  (writes wp1/test_wp1.json)
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import grid15 as G  # noqa: E402

ST = G.ST
WT = os.path.abspath(os.path.join(ST, "..", ".."))
R6 = os.path.join(G.SRC, "r6")
res = {}


def check(name, ok, **info):
    res[name] = dict(passed=bool(ok), **info)
    print(("PASS" if ok else "FAIL"), name, info)


# ---- T1 -------------------------------------------------------------------------------------------------
sys.path.insert(0, os.path.join(WT, "research", "phase2_anchor_step_20261013", "src"))
sys.path.insert(0, os.path.join(WT, "TechArena_Challenge2_Team_Package"))
from events import full_charges  # noqa: E402
from framework.data import load_dataset  # noqa: E402

fc = full_charges(load_dataset(os.path.join(WT, "TechArena_Challenge2_Team_Package", "data")).operation)
q = fc.sort_values("t_end")["Q_Ah"].to_numpy()
eps0 = G.Q_CK0 - q[0]
dev = max(abs(q[k] + eps0 - G.P_K[k]) for k in G.KS)
check("T1_pk_independent", len(q) == 8 and dev < 1e-6, n_anchors=int(len(q)), max_abs_dev_Ah=float(dev),
      eps0=float(eps0), p_k={k: round(G.P_K[k], 6) for k in G.KS})

# ---- T2 -------------------------------------------------------------------------------------------------
pr = pd.read_csv(os.path.join(R6, "wp1_predictions.csv"))
pr = pr[(pr.scenario == "real") & (pr.step == "main") & (pr.a4s == 2.0) & (pr.delta == 0.4)]
soh6 = {m: {f"CK{int(k)}": q_ / G.NOM * 100 for k, q_ in zip(g["k"], g["Q"])} for m, g in pr.groupby("model")}
sl = pd.read_csv(os.path.join(R6, "wp1_scores_long.csv"))
sl = sl[sl.scenario == "real"].set_index(["model", "h"])
worst = 0.0
n = 0
for m, soh in soh6.items():
    for h in G.GRIDS["G_main"]:
        r = G.raw_metrics(soh, h)
        s = G.scores(soh, soh6["EX"], h)["s"]
        ref = sl.loc[(m, G.hname(h))]
        worst = max(worst, abs(r["MAE"] - ref["MAE"]), abs(r["RMSE"] - ref["RMSE"]), abs(r["MAX"] - ref["MAX"]),
                    abs(s - ref["s"]))
        n += 1
check("T2_round6_scores", n == 12 * 18 and worst < 1e-9, n_cells=n, max_abs_dev=float(worst))

# ---- T3 -------------------------------------------------------------------------------------------------
sub_q = {f"CK{int(k)}": q_ for k, q_ in zip(pr[pr.model == "SUB"]["k"], pr[pr.model == "SUB"]["Q"])}
pdrift = {c: (v + (-0.031) * max(0.0, G.Q_CK0 - v)) / G.NOM * 100 for c, v in sub_q.items()}
sc = G.score_table({"SUB": soh6["SUB"], "P_drift": pdrift}, soh6["EX"], "G_main")
dt = G.delta_table(sc, "P_drift")
mine = dt[dt.metric == "s"].set_index("h")["delta_s"]
ref6 = pd.read_csv(os.path.join(R6, "wp6_delta_s_vs_SUB_by_h.csv")).set_index("h")["P_drift"]
dev3 = float((mine - ref6.reindex(mine.index)).abs().max())
check("T3_round6_P_drift_delta_s", dev3 < 1e-9, max_abs_dev=dev3, E_uniform=float(mine.mean()),
      round6_E_uniform=-0.0163)

# ---- T4 -------------------------------------------------------------------------------------------------
def synth(values):
    rows = []
    for i, v in enumerate(values):
        for m, x in zip(G.METRICS, v):
            rows.append(dict(probe="X", grid="G", h=f"h{i}", metric=m, delta_s=x))
    return pd.DataFrame(rows)


r_a = G.readability(synth([[-0.01] * 4] * 8 + [[-0.01, -0.01, -0.01, 0.0]] * 2))       # 8/10 agree
r_b = G.readability(synth([[-0.01] * 4] * 7 + [[-0.01, -0.01, -0.01, 0.02]] * 3))      # 7/10 agree
r_c = G.readability(synth([[0.01] * 4] * 10))                                            # all agree, all lose
check("T4_readability", r_a["readable"] and r_a["agree_fraction"] == 0.8 and not r_b["readable"] and r_c["readable"],
      a=r_a, b=r_b, c=r_c)

# ---- T5 -------------------------------------------------------------------------------------------------
cases = [
    (({"score": "0.600"}, {"score": "0.610"}), "probe wins: adopt its scalar"),
    (({"score": "0.612"}, {"score": "0.610"}), "probe loses: revert to SUB, drop the branch"),
    (({"score": "0.611"}, {"score": "0.610"}), "no information: revert to SUB"),
    (({"a": "0.60", "b": "0.75"}, {"a": "0.62", "b": "0.73"}), "probe loses: revert to SUB, drop the branch"),
    (({"a": "0.60", "b": "0.73"}, {"a": "0.62", "b": "0.73"}), "probe wins: adopt its scalar"),
    (({"score": "0.6"}, {"score": "0.6"}), "no information: revert to SUB"),
    (({"rank": "7"}, {}), "no information"),
]
got = [G.reading(a, b)["verdict"] for (a, b), _ in cases]
check("T5_reading_rules", got == [w for _, w in cases], got=got)

# ---- T6 -------------------------------------------------------------------------------------------------
sc6 = G.score_table({"SUB": soh6["SUB"]}, soh6["EX"], "G_main")
h0 = G.hname(G.GRIDS["G_main"][0])
v0 = sc6[(sc6.h == h0) & (sc6.metric == "nMAE")]["value"].iloc[0]
keep, note = G.surviving(sc6, [dict(model="SUB", values={"score": f"{v0:.3f}"})])
none, note2 = G.surviving(sc6, [dict(model="SUB", values={"score": "9.999"})])
full, note3 = G.surviving(sc6, [])
check("T6_surviving_set", h0 in keep and len(keep) < 18 and len(none) == 18 and "inconsistent" in note2
      and len(full) == 18, kept=len(keep), note=note, note_empty=note2, note_none=note3)

# ---- T7 -------------------------------------------------------------------------------------------------
dsyn = synth([[-0.01] * 4, [-0.01, -0.01, -0.01, 0.0], [0.01] * 4])
left = G.drop_branch(dsyn, ["h0", "h1", "h2"])
check("T7_drop_branch", left == ["h1", "h2"], left=left)

res["all_passed"] = all(v["passed"] for v in res.values() if isinstance(v, dict))
os.makedirs(os.path.join(ST, "wp1"), exist_ok=True)
json.dump(res, open(os.path.join(ST, "wp1", "test_wp1.json"), "w"), indent=1, default=float)
print("all passed:", res["all_passed"])
