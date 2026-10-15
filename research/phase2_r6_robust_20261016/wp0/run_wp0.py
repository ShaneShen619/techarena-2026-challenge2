"""WP0: re-baselining. Reproduce V2, SUB (V2+sqrt), 5C R3_TD_w0.75 and R2_B on real/pseudo/CS;
check the archived submitted class against SUB; compute ExampleModel predictions causally."""
import importlib.util
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
from preds5c import ens, s_pred  # noqa: E402
from runner5c import COLD, PSEUDO, run, scen_mean  # noqa: E402
from smodel5c import LawFit  # noqa: E402
from v3 import v3  # noqa: E402
from framework.data import load_dataset  # noqa: E402

OUT = os.path.join(HERE, "outputs")
PKG = os.path.join(STUDY, "cache", "submitted_package", "TechArena_Challenge2_Team_Package")


def sub_pred(ctx):
    q, br, b = v3(ctx["fc"], ctx["steps"][ctx["step"]], ctx["a4"][ctx["a4s"]], ctx["ck"], ctx["k"], ctx["eps"],
                  use_sqrt=True, beta_cap=float("inf"), median=False)
    return q, {"branch": br}


GAP = dict(steps=True, steps_mode="gap_endpoint", beta_mode="one", sigma_s=0.10)
R2_B = s_pred("R2_B", cls=LawFit, cfg=dict(law="two", **GAP), uses_steps=True)
R3_T = s_pred("R3_T", cls=LawFit, cfg=dict(law="two", transient_ref="restart", **GAP), uses_steps=True)
P = {"V2": H.BASELINES["V2"], "M4": H.BASELINES["M4"], "SUB": sub_pred, "R2_B": R2_B,
     "R3_TD_w0.75": ens(R3_T, 0.75)}


def load_class(fname, cls):
    spec = importlib.util.spec_from_file_location(f"pkg_{cls}", os.path.join(PKG, "my_model", fname))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, cls)


def run_class(cls):
    full = load_dataset(H.DATA)
    m = cls()
    m.fit(full)
    return [float(m.estimate_soh(load_dataset(H.DATA, until=d), d)) for d in H.CK]


if __name__ == "__main__":
    df = run(P, ("real",) + PSEUDO + COLD)
    df.to_csv(os.path.join(OUT, "wp0_predictions_long.csv"), index=False)
    met = H.metrics(df)
    met.to_csv(os.path.join(OUT, "wp0_metrics.csv"), index=False)
    m = met[(met["scenario"] == "real") & (met["step"] == "main")].set_index(["model", "delta"])
    rep = {}
    for mod in P:
        rep[mod] = dict(MAE=[float(m.loc[(mod, d), "MAE"]) for d in (0.0, 0.4, 0.8)],
                        MAX=[float(m.loc[(mod, d), "MAX"]) for d in (0.0, 0.4, 0.8)],
                        pseudo=scen_mean(met, PSEUDO, mod), cold=scen_mean(met, COLD, mod))
    expect = {"V2": dict(MAE04=0.215726, tol=5e-7), "SUB": dict(MAE04=0.123, MAX04=0.228, pseudo=0.148, cold=0.174, tol=5e-4),
              "R3_TD_w0.75": dict(MAE04=0.131, pseudo=0.123, cold=0.134, tol=5e-4),
              "R2_B": dict(MAE04=0.258, pseudo=0.119, cold=0.144, tol=5e-4)}
    checks = {}
    for mod, e in expect.items():
        ok = abs(rep[mod]["MAE"][1] - e["MAE04"]) <= e["tol"]
        if "MAX04" in e:
            ok &= abs(rep[mod]["MAX"][1] - e["MAX04"]) <= e["tol"]
        for k in ("pseudo", "cold"):
            if k in e:
                ok &= abs(rep[mod][k] - e[k]) <= e["tol"]
        checks[mod] = bool(ok)
    # archived submitted class vs SUB research (delta 0.4)
    sub_cls = load_class("model_template.py", "MyModel")
    soh_cls = run_class(sub_cls)
    r = df[(df.scenario == "real") & (df.model == "SUB") & (df.delta == 0.4) & (df.step == "main") & (df.a4s == 2.0)].sort_values("k")
    diff = float(np.max(np.abs(np.round(soh_cls[1:], 3) - r["SOH"].to_numpy())))
    checks["submitted_class_vs_SUB"] = bool(diff <= 0.001)
    # official ExampleModel
    ex_cls = load_class("model_example.py", "ExampleModel")
    soh_ex = run_class(ex_cls)
    ex = pd.DataFrame({"checkup": H.CK_NAMES, "date": H.CK.astype(str), "SOH_example": soh_ex,
                       "SOH_submitted_class": soh_cls})
    ex.to_csv(os.path.join(OUT, "wp0_example_and_submitted_class.csv"), index=False)
    out = dict(models=rep, checks=checks, submitted_class_max_diff_pp=diff,
               reproduced=bool(checks["V2"] and checks["SUB"] and checks["submitted_class_vs_SUB"]),
               all_checks=bool(all(checks.values())), example_soh=dict(zip(H.CK_NAMES, soh_ex)))
    json.dump(out, open(os.path.join(OUT, "reproduce.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))
    if not out["reproduced"]:
        raise SystemExit("V2/SUB reproduction failed")
