"""Round 9: evaluate the registered candidates (protocol.json) against SUB."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "src"))
from variants import CANDIDATES, NON_CAUSAL, H  # noqa: E402
from runner5c import COLD, PSEUDO, run, scen_mean  # noqa: E402
import tsqrt as T  # noqa: E402

OUT = os.path.join(HERE, "outputs")
SCENS = ("real",) + PSEUDO + COLD + ("PC5_all", "PC10_all")

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    df = run({**CANDIDATES, "SUB_ref": T.design_pred("T_main")}, SCENS)
    a = df[df.model == "SUB"].set_index(["scenario", "k", "delta"])["Q"]
    b = df[df.model == "SUB_ref"].set_index(["scenario", "k", "delta"])["Q"]
    assert float((a - b).abs().max()) < 1e-9
    df = df[df.model != "SUB_ref"]
    df.to_csv(os.path.join(OUT, "r9_predictions.csv"), index=False)
    met = H.metrics(df)
    d4 = df[df.delta == 0.4]
    sub = d4[d4.model == "SUB"].set_index(["scenario", "k"])
    rows, changed_rows = [], []
    for m in CANDIDATES:
        c = d4[d4.model == m].set_index(["scenario", "k"])
        diff = (c["Q"] - sub["Q"]).abs()
        nr = [i for i in diff.index if i[0] != "real" and diff[i] > 1e-9]
        if nr:
            e0, e1 = sub.loc[nr, "err_pp"].abs(), c.loc[nr, "err_pp"].abs()
            worst = float((e1 - e0).max())
            g_ch = bool(e0.mean() - e1.mean() >= 0.02 and worst <= 0.10)
            for i in nr:
                changed_rows.append(dict(model=m, scenario=i[0], k=i[1], branch=c.loc[i, "branch"],
                                         err_SUB=sub.loc[i, "err_pp"], err_cand=c.loc[i, "err_pp"]))
        else:
            e0 = e1 = pd.Series(dtype=float)
            worst, g_ch = np.nan, False
        r = met[(met.scenario == "real") & (met.model == m)].set_index("delta")
        rs = met[(met.scenario == "real") & (met.model == "SUB")].set_index("delta")
        rows.append(dict(model=m, causal=m not in NON_CAUSAL,
                         pseudo=scen_mean(met, PSEUDO, m), cold=scen_mean(met, COLD, m),
                         n_changed_nonreal=len(nr), changed_MAE_SUB=float(e0.mean()) if len(e0) else np.nan,
                         changed_MAE_cand=float(e1.mean()) if len(e1) else np.nan, worst_case_increase=worst,
                         real_MAE_d0=r.loc[0.0, "MAE"], real_MAE_d04=r.loc[0.4, "MAE"], real_MAE_d08=r.loc[0.8, "MAE"],
                         real_MAX_d0=r.loc[0.0, "MAX"], real_MAX_d04=r.loc[0.4, "MAX"], real_MAX_d08=r.loc[0.8, "MAX"],
                         G_changed=g_ch,
                         G_real_safety=bool(all(r.loc[d, "MAX"] <= rs.loc[d, "MAX"] + 0.10 for d in H.DELTAS))))
    t = pd.DataFrame(rows).set_index("model")
    t["G_pseudo"] = t["pseudo"] <= t.loc["SUB", "pseudo"] + 0.005
    t["G_cold"] = t["cold"] <= t.loc["SUB", "cold"] + 0.005
    t["passes"] = t[["G_pseudo", "G_cold", "G_changed", "G_real_safety"]].all(axis=1) & t["causal"]
    t.loc["SUB", "passes"] = False
    t.to_csv(os.path.join(OUT, "r9_gates.csv"))
    ch = pd.DataFrame(changed_rows)
    ch.to_csv(os.path.join(OUT, "r9_changed_cases.csv"), index=False)
    per = d4[d4.scenario == "real"].pivot_table(index="model", columns="checkup", values="err_pp")
    per.to_csv(os.path.join(OUT, "r9_real_err_d04.csv"))
    pd.set_option("display.width", 250)
    print(t.round(4).to_string())
    print(per.round(3).to_string())
    print(ch.round(3).to_string())
    json.dump(dict(passing=[m for m in t.index if t.loc[m, "passes"]]), open(os.path.join(OUT, "r9_decision.json"), "w"))
