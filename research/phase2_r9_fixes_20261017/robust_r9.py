"""Post-registration robustness check (added after recalling the V3 result): SUB vs P2a_median on all 6 step
detection variants, real and causal scenarios, delta 0.4."""
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "src"))
from variants import CANDIDATES, H  # noqa: E402
from runner5c import COLD, PSEUDO, run, scen_mean  # noqa: E402

if __name__ == "__main__":
    P = {m: CANDIDATES[m] for m in ("SUB", "P2a_median")}
    df = run(P, ("real",) + PSEUDO + COLD, variants=tuple(H.VARIANTS), deltas=(0.4,))
    met = H.metrics(df)
    rows = []
    for v in H.VARIANTS:
        r = {"variant": v}
        for m in P:
            mm = met[(met.model == m) & (met.step == v)]
            r[f"{m}_real"] = float(mm[mm.scenario == "real"]["MAE"].iloc[0])
            r[f"{m}_pseudo"] = scen_mean(met, PSEUDO, m, step=v)
            r[f"{m}_cold"] = scen_mean(met, COLD, m, step=v)
        rows.append(r)
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(HERE, "outputs", "r9_robust_variants.csv"), index=False)
    pd.set_option("display.width", 250)
    print(t.round(4).to_string())
