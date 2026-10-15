"""Checks of the wired submission model (V2 + sqrt(t) gap branch) against this study.

1. Full-data run through run_model.py equals the research implementation V2+1 (delta 0.4, main step).
2. Causality: noise after every cut leaves each checkup's estimate bit-identical.
3. The fitted object pickles and reloads (done by run_model.py train/test).
"""
import json
import os
import shutil
import subprocess
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.abspath(os.path.join(HERE, "..", "..", "TechArena_Challenge2_Team_Package"))
OUT = os.path.join(HERE, "outputs", "_submission_check")
sys.path[:0] = [HERE, PKG]

from framework.data import load_dataset, load_eval_points  # noqa: E402
from my_model import ActiveModel  # noqa: E402
from stage_v3_eval import noise_copy  # noqa: E402


def run(cmd):
    subprocess.run([sys.executable, "-B", "run_model.py"] + cmd, cwd=PKG, check=True, capture_output=True)


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    run(["--model", "train", "--input", "data", "--output-dir", OUT])
    run(["--model", "test", "--input", "data", "--state-dir", OUT, "--output-dir", OUT, "--eval-point", "all"])
    out = pd.read_csv(next(os.path.join(OUT, f) for f in os.listdir(OUT) if f.endswith(".csv")))

    research = pd.read_csv(os.path.join(HERE, "outputs", "V3_predictions_long.csv"))
    r = research[(research["model"] == "V2+1") & (research["step"] == "main") & (research["a4s"] == 2.0)
                 & (research["eps_offset"] == 0.4)].set_index("checkup")["SOH"]
    m = out.set_index("checkup")["SOH_est"]
    diff = (m.loc[r.index] - r).abs()

    data = os.path.join(PKG, "data")
    model = ActiveModel()
    model.fit(load_dataset(data))
    tmp = os.path.join(OUT, "noise")
    causal = {}
    for p in load_eval_points(data).itertuples():
        noise_copy(data, tmp, p.date)
        a = model.estimate_soh(load_dataset(data, until=p.date), p.date)
        b = model.estimate_soh(load_dataset(tmp, until=p.date), p.date)
        causal[p.checkup] = bool(a == b)
    shutil.rmtree(tmp, ignore_errors=True)

    res = dict(model=ActiveModel.__module__ + "." + ActiveModel.__name__,
               output=out.to_dict("records"),
               max_abs_diff_vs_research_pp=float(diff.max()),
               note="run_model rounds to 3 decimals",
               causality=causal, causality_passed=all(causal.values()))
    with open(os.path.join(HERE, "outputs", "submission_check.json"), "w") as f:
        json.dump(res, f, indent=2, default=str)
    print(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
