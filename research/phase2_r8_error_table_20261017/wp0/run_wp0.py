"""WP0: re-baseline SUB = T_main (research implementation and submitted class at 5cd305c) and rebuild the branch
inventory for every scenario (EXECUTION_PROMPT.md, WP0)."""
import importlib.util
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "src"))
from common8 import H  # noqa: E402
from runner5c import COLD, PSEUDO, run, scen_mean  # noqa: E402
import tsqrt as T  # noqa: E402

OUT = os.path.join(HERE, "outputs")
PKG = os.path.join(STUDY, "cache", "submitted_package", "TechArena_Challenge2_Team_Package")
SCENS = ("real",) + PSEUDO + COLD + ("PC5_all", "PC10_all")
TARGET = dict(MAE=[0.197, 0.126, 0.146], MAX=[0.609, 0.228, 0.228], pseudo=0.144, cold=0.170, gap_cut=0.105)
TOL = 0.001


def load_expected():
    src = open(os.path.join(STUDY, "cache", "package_submission_5cd305c.py"), encoding="utf-8").read()
    i = src.index("EXPECTED_SOH = {")
    j = src.index("}", i)
    return eval(src[i + len("EXPECTED_SOH = "):j + 1])  # literal dict copied from the submission script


def submitted_class():
    sys.path.insert(0, PKG)
    spec = importlib.util.spec_from_file_location("sub_tmain", os.path.join(PKG, "my_model", "model_template.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.MyModel


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    df = run({"SUB": T.design_pred("T_main")}, SCENS)
    df.to_csv(os.path.join(OUT, "wp0_sub_predictions.csv"), index=False)
    met = H.metrics(df)
    m = met[(met.scenario == "real") & (met.step == "main")].set_index("delta")
    g = df[(df.scenario == "PC10") & (df.delta == 0.4) & (df.branch == "sqrt_gap") & (df.k >= 3)]
    got = dict(MAE=[float(m.loc[d, "MAE"]) for d in H.DELTAS], MAX=[float(m.loc[d, "MAX"]) for d in H.DELTAS],
               pseudo=scen_mean(met, PSEUDO, "SUB"), cold=scen_mean(met, COLD, "SUB"),
               gap_cut=float(g["err_pp"].abs().mean()))
    checks = {}
    for key in ("MAE", "MAX"):
        checks[f"research_{key}"] = bool(all(abs(a - b) <= TOL for a, b in zip(got[key], TARGET[key])))
    for key in ("pseudo", "cold", "gap_cut"):
        checks[f"research_{key}"] = bool(abs(got[key] - TARGET[key]) <= TOL)

    # submitted class on the full data with the framework cut, compared per checkup (delta 0.4 = EPS_EXTRA_AH)
    cls = submitted_class()
    full = H.load_dataset(H.DATA)
    model = cls()
    model.fit(full)
    expected = load_expected()
    res = df[(df.scenario == "real") & (df.delta == 0.4)].set_index("checkup")["SOH"]
    rows = []
    for k, d in enumerate(H.CK):
        s = float(model.estimate_soh(H.load_dataset(H.DATA, until=d), d))
        r = float(res[H.CK_NAMES[k]]) if k >= 1 else np.nan
        rows.append(dict(checkup=H.CK_NAMES[k], k=k, SOH_submitted=s, SOH_research=r, diff_pp=s - r if k else np.nan,
                         SOH_submitted_r3=round(s, 3), EXPECTED_SOH=expected[H.CK_NAMES[k]]))
    sub = pd.DataFrame(rows)
    sub.to_csv(os.path.join(OUT, "wp0_submitted_vs_research.csv"), index=False)
    checks["submitted_vs_research_0p0005"] = bool(sub["diff_pp"].abs().max() <= 0.0005)
    checks["submitted_equals_EXPECTED_SOH"] = bool((sub["SOH_submitted_r3"] == sub["EXPECTED_SOH"]).all())

    inv = df[df.delta == 0.4][["scenario", "checkup", "k", "branch", "Q", "proxy", "err_pp", "SOH"]]
    inv.to_csv(os.path.join(OUT, "wp0_branch_by_case.csv"), index=False)
    counts = inv.groupby(["scenario", "branch"]).size().unstack(fill_value=0)
    counts.to_csv(os.path.join(OUT, "wp0_branch_counts.csv"))
    out = dict(research=got, target=TARGET, tolerance_pp=TOL, checks=checks,
               submitted_max_abs_diff_pp=float(sub["diff_pp"].abs().max()),
               n_cases_delta04=int(len(inv)), branch_counts=counts.to_dict(orient="index"),
               all_checks=bool(all(checks.values())))
    json.dump(out, open(os.path.join(OUT, "reproduce.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))
    print(sub.to_string())
    if not out["all_checks"]:
        raise SystemExit("SUB reproduction failed")
