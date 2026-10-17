"""WP2: idea B, combine per-cell changes (protocol.json)."""
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
V = list(P["tau_Ah_by_variant"])
TAU = P["tau_Ah_by_variant"]
TAU3 = P["B3_tau_Ah"]

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    log_b2, log_b3 = [], []
    preds = {"SUB": G.SUB,
             "B1": CC.make(CC.provider_variant(), mode="change", combine=CC.combine_median),
             "B2": CC.make(CC.provider_variant(), mode="change", tau_by_variant=TAU, log=log_b2),
             "B3": CC.make(CC.provider_ensemble(V, "median"), mode="change", combine=CC.combine_reject(TAU3, log_b3),
                           selection_step="main")}
    df = G.predict(preds)
    logs = dict(B2=pd.DataFrame(log_b2), B3=pd.DataFrame(log_b3))
    dv = G.predict({k: preds[k] for k in ("SUB", "B1", "B2")}, variants=tuple(v for v in V if v != "main"), deltas=(0.4,))
    lovo = {f"B3_lovo_{j}": CC.make(CC.provider_ensemble([v for v in V if v != j], "median"), mode="change",
                                     combine=CC.combine_reject(TAU3), selection_step="main") for j in V}
    dl = G.predict(lovo, deltas=(0.4,))
    allp = pd.concat([df, dv, dl], ignore_index=True)
    allp.to_csv(os.path.join(OUT, "wp2_predictions.csv"), index=False)
    met = H.metrics(allp)
    st_full = D.full_steps()
    ev = G.full_events()
    ev_sub, _ = G.event_sd(CC.pack_series_position(CC.variant_locs(st_full, "main"), "mean"))
    gates, robust_all, changed_all = [], [], []
    for n in ("B1", "B2", "B3"):
        if n == "B3":
            pairs = [(j, f"B3_lovo_{j}", "main", "SUB", "main") for j in V]
            L, comb = CC.ensemble_locs(st_full, V, "median"), CC.combine_reject(TAU3)
        else:
            pairs = [(v, n, v, "SUB", v) for v in V]
            L = CC.variant_locs(st_full, "main")
            comb = CC.combine_median if n == "B1" else CC.combine_reject(TAU["main"])
        rt, rv = G.robust_rows(met, pairs)
        rt.insert(0, "candidate", n)
        robust_all.append(rt)
        series = CC.pack_series_change(L, ev["segment"].reindex(L.index).to_numpy(), comb)
        ev_c, _ = G.event_sd(series)
        g, ch = G.gate_table(n, met, df, rv, ev_c, ev_sub)
        gates.append(g)
        changed_all += [dict(candidate=n, **x) for x in ch["cases"]]
    gt = pd.DataFrame(gates).set_index("candidate")
    passing = [n for n in P["simplicity_order"] if gt.loc[n, "passes"]]
    adopted = None
    if passing:
        best = min(gt.loc[passing, "causal"])
        adopted = next(n for n in P["simplicity_order"] if n in passing and gt.loc[n, "causal"] <= best + 0.002)
    gt.to_csv(os.path.join(OUT, "wp2_gates.csv"))
    pd.concat(robust_all).to_csv(os.path.join(OUT, "wp2_robust.csv"), index=False)
    pd.DataFrame(changed_all).to_csv(os.path.join(OUT, "wp2_changed_cases.csv"), index=False)
    rej = {}
    for n, lg in logs.items():
        lg = lg[(lg.delta == 0.4) & (lg.step == "main")].drop_duplicates(subset=["scenario", "k"]) if len(lg) else lg
        lg.to_csv(os.path.join(OUT, f"wp2_rejections_{n}.csv"), index=False)
        rej[n] = dict(n_cases=int(len(lg)), n_rejected=int((lg["dropped"] != "").sum()) if len(lg) else 0,
                      by_cell=lg[lg["dropped"] != ""]["dropped"].value_counts().to_dict() if len(lg) else {})
    d4 = df[(df.scenario == "real") & (df.delta == 0.4)]
    d4.pivot_table(index="model", columns="checkup", values="err_pp").to_csv(os.path.join(OUT, "wp2_real_err_d04.csv"))
    d4.pivot_table(index="model", columns="checkup", values="SOH").to_csv(os.path.join(OUT, "wp2_real_SOH_d04.csv"))
    json.dump(dict(passing=passing, adopted=adopted, rejections=rej, event_sd_SUB=ev_sub),
              open(os.path.join(OUT, "wp2_decision.json"), "w"), indent=1, default=float)
    pd.set_option("display.width", 250)
    print(gt.T.round(4).to_string())
    print(pd.concat(robust_all).round(4).to_string())
    print(d4.pivot_table(index="model", columns="checkup", values="err_pp").round(3).to_string())
    print(json.dumps(dict(passing=passing, adopted=adopted, rejections=rej), indent=1, default=float))
