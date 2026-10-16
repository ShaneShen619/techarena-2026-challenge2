"""WP0: re-baselining against round 6 and the sqrt-branch inventory (EXECUTION_PROMPT.md, WP0)."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
sys.path.insert(0, os.path.join(STUDY, "sources", "v3"))
from common6 import H  # noqa: E402
from runner5c import COLD, PSEUDO, SCEN, run, scen_mean  # noqa: E402
import grid7 as G  # noqa: E402
import audits6 as A  # noqa: E402

OUT = os.path.join(HERE, "outputs")
R6 = G.R6

if __name__ == "__main__":
    checks = {}
    # 1. SUB on real / pseudo / cold start, all deltas (main step, A4 2 Ah)
    scens = ("real",) + PSEUDO + COLD + ("PC5_all", "PC10_all")
    df = run({"SUB": G.SUB}, scens)
    df.to_csv(os.path.join(OUT, "wp0_sub_predictions.csv"), index=False)
    met = H.metrics(df)
    m = met[(met.scenario == "real") & (met.step == "main")].set_index("delta")
    sub = dict(MAE=[float(m.loc[d, "MAE"]) for d in (0.0, 0.4, 0.8)], MAX=[float(m.loc[d, "MAX"]) for d in (0.0, 0.4, 0.8)],
               pseudo=scen_mean(met, PSEUDO, "SUB"), cold=scen_mean(met, COLD, "SUB"))
    checks["SUB"] = bool(abs(sub["MAE"][1] - 0.123) <= 5e-4 and abs(sub["MAX"][1] - 0.228) <= 5e-4
                         and abs(sub["pseudo"] - 0.148) <= 5e-4 and abs(sub["cold"] - 0.174) <= 5e-4)
    # 2. SUB predictions identical to round 6 WP1 file; round-6 WP1 decision reproduced from its predictions
    p6 = pd.read_csv(os.path.join(R6, "wp1", "outputs", "wp1_predictions.csv"))
    p6r = p6[(p6.scenario == "real") & (p6.step == "main") & (p6.a4s == 2.0)]
    mine = df[(df.scenario == "real") & (df.delta == 0.4)].sort_values("k")["Q"].to_numpy()
    theirs = p6r[p6r.model == "SUB"].sort_values("k")["Q"].to_numpy()
    sub_pred_diff = float(np.max(np.abs(mine - theirs)))
    checks["SUB_equals_round6_predictions"] = bool(sub_pred_diff < 1e-9)
    sc = G.scores(p6r[["scenario", "k", "model", "Q"]], G.targets6())
    cand = [x for x in sc.model.unique() if x != "EX"]
    real = sc.pivot_table(index="h", columns="model", values="s")[cand]
    t, _ = G.decision(real, G.round6_weights(real.index))
    t6 = pd.read_csv(os.path.join(R6, "wp1", "outputs", "wp1_decision_table.csv"), index_col=0)
    grid_diff = float((t["max_regret"] - t6.loc[t.index, "max_regret"]).abs().max())
    checks["round6_grid_reproduced"] = bool(grid_diff < 1e-9 and abs(t.loc["SUB", "max_regret"] - 0.027) < 5e-4)
    # 3. round 6 audits 3a and 3c
    a3 = A.table_3a()
    a3_6 = pd.read_csv(os.path.join(R6, "wp3", "outputs", "wp3a_start_state.csv"))
    checks["3a_reproduced"] = bool(np.allclose(a3["r_upper"].to_numpy(), a3_6["r_upper"].to_numpy(), atol=1e-9))
    c3 = A.table_3c()
    c3_6 = pd.read_csv(os.path.join(R6, "wp3", "outputs", "wp3c_path_offsets.csv"))
    checks["3c_reproduced"] = bool(np.allclose(c3["adj_offset"].to_numpy(), c3_6["adj_offset"].to_numpy(), atol=1e-9))
    a3.to_csv(os.path.join(OUT, "wp0_3a_start_state.csv"), index=False)
    c3.to_csv(os.path.join(OUT, "wp0_3c_path_offsets.csv"), index=False)
    # 4. sqrt-branch inventory (delta 0.4; the branch rule does not depend on delta)
    inv = df[(df.delta == 0.4)][["scenario", "checkup", "k", "branch", "Q", "proxy", "err_pp", "SOH"]]
    inv.to_csv(os.path.join(OUT, "wp0_branch_by_case.csv"), index=False)
    sq = inv[inv.branch == "sqrt_gap"]
    sq.to_csv(os.path.join(OUT, "sqrt_branch_cases.csv"), index=False)
    out = dict(SUB=sub, checks=checks, sub_vs_round6_max_abs_diff_Ah=sub_pred_diff, grid_max_regret_diff=grid_diff,
               SUB_max_regret=float(t.loc["SUB", "max_regret"]),
               sqrt_gap_cases=[f"{r.scenario}:CK{r.k}" for r in sq.itertuples()],
               n_sqrt_gap_nonreal=int((sq.scenario != "real").sum()),
               n_sqrt_gap_nonreal_unique_k=int(sq[sq.scenario != "real"][["scenario", "k"]].drop_duplicates().shape[0]),
               all_checks=bool(all(checks.values())))
    json.dump(out, open(os.path.join(OUT, "reproduce.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))
    if not checks["SUB"]:
        raise SystemExit("SUB reproduction failed")
