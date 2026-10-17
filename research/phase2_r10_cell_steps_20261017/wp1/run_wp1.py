"""WP1: idea A, variant-ensemble per-cell detection (protocol.json)."""
import hashlib
import json
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
from common10 import H  # noqa: E402
import cellcand as CC  # noqa: E402
import diag10 as D  # noqa: E402
import gates10 as G  # noqa: E402

OUT = os.path.join(HERE, "outputs")
PROTO = os.path.join(HERE, "protocol.json")
assert hashlib.sha256(open(PROTO, "rb").read()).hexdigest() == open(os.path.join(HERE, "protocol.sha256")).read().split()[0]
P = json.load(open(PROTO))
V = P["variants"]
SPEC = {"A1": ("mean", "mean"), "A2": ("mean", "median"), "A3": ("median", "median")}


def cand(variants, how, agg):
    return CC.make(CC.provider_ensemble(variants, how), agg=agg, selection_step="main")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    preds = {"SUB": G.SUB, **{n: cand(V, h, a) for n, (h, a) in SPEC.items()}}
    df = G.predict(preds)
    lovo = {}
    for n, (h, a) in SPEC.items():
        for j in V:
            lovo[f"{n}_lovo_{j}"] = cand([v for v in V if v != j], h, a)
    dl = G.predict(lovo, deltas=(0.4,))
    allp = pd.concat([df, dl], ignore_index=True)
    allp.to_csv(os.path.join(OUT, "wp1_predictions.csv"), index=False)
    met = H.metrics(allp)
    st_full = D.full_steps()
    sub_series = CC.pack_series_position(CC.variant_locs(st_full, "main"), "mean")
    ev_sub, n_ev = G.event_sd(sub_series)
    gates, robust_all, changed_all, diag = [], [], [], {}
    for n, (h, a) in SPEC.items():
        rt, rv = G.robust_rows(met, [(j, f"{n}_lovo_{j}", "main", "SUB", "main") for j in V])
        rt.insert(0, "candidate", n)
        robust_all.append(rt)
        L = CC.ensemble_locs(st_full, V, h)
        ev_c, _ = G.event_sd(CC.pack_series_position(L, a))
        g, ch = G.gate_table(n, met, df, rv, ev_c, ev_sub)
        gates.append(g)
        changed_all += [dict(candidate=n, **x) for x in ch["cases"]]
        diag[n] = dict(sigma=D.sigma_cells(L), cell_picture=D.cell_picture(L))
    diag["single_variants"] = {v: dict(sigma=D.sigma_cells(CC.variant_locs(st_full, v))) for v in V}
    diag["SUB_main_cell_picture"] = D.cell_picture(CC.variant_locs(st_full, "main"))
    diag["event_n"] = n_ev
    gt = pd.DataFrame(gates).set_index("candidate")
    passing = [n for n in P["simplicity_order"] if gt.loc[n, "passes"]]
    adopted = None
    if passing:
        best = min(gt.loc[passing, "causal"])
        adopted = next(n for n in P["simplicity_order"] if n in passing and gt.loc[n, "causal"] <= best + 0.002)
    gt.to_csv(os.path.join(OUT, "wp1_gates.csv"))
    pd.concat(robust_all).to_csv(os.path.join(OUT, "wp1_robust_lovo.csv"), index=False)
    pd.DataFrame(changed_all).to_csv(os.path.join(OUT, "wp1_changed_cases.csv"), index=False)
    d4 = df[(df.scenario == "real") & (df.delta == 0.4)]
    d4.pivot_table(index="model", columns="checkup", values="err_pp").to_csv(os.path.join(OUT, "wp1_real_err_d04.csv"))
    d4.pivot_table(index="model", columns="checkup", values="SOH").to_csv(os.path.join(OUT, "wp1_real_SOH_d04.csv"))
    json.dump(dict(passing=passing, adopted=adopted, diagnostics=diag), open(os.path.join(OUT, "wp1_decision.json"), "w"),
              indent=1, default=float)
    pd.set_option("display.width", 250)
    print(gt.T.round(4).to_string())
    print(pd.concat(robust_all).round(4).to_string())
    print(d4.pivot_table(index="model", columns="checkup", values="err_pp").round(3).to_string())
    print(json.dumps(dict(passing=passing, adopted=adopted, diagnostics=diag), indent=1, default=float))
