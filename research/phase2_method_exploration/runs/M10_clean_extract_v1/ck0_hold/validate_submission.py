#!/usr/bin/env python3
# DO NOT EDIT
"""Local validation: runs your model through the official entry point on sample_data/ and checks
the output schema. Writes validation_report.txt. Run it from a FRESH virtual environment created
from your requirements.txt - that is exactly what the evaluation does."""
import os, subprocess, sys, tempfile, time
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
LOCAL_TRAIN_LIMIT_S, LOCAL_TEST_LIMIT_S = 900, 300     # local sanity limits only, not the competition limits
report = []


def log(msg):
    print(msg); report.append(msg)


def run(args, limit):
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, os.path.join(HERE, "run_model.py")] + args,
                           capture_output=True, text=True, timeout=limit)
    except subprocess.TimeoutExpired:
        fail(f"run_model.py {' '.join(args)} exceeded the local sanity limit of {limit} s")
    if r.returncode != 0:
        log(r.stdout); log(r.stderr); fail(f"run_model.py {' '.join(args)} failed")
    log(f"    ok ({time.time()-t0:.0f} s)")
    return r.stdout


def fail(msg):
    log(f"FAILED: {msg}")
    open(os.path.join(HERE, "validation_report.txt"), "w", encoding="utf-8").write("\n".join(report))
    sys.exit(1)


def main():
    data = os.path.join(HERE, "sample_data"); out = tempfile.mkdtemp(prefix="c2_validate_")
    log("1/4 framework files present ...")
    for name in ("run_model.py", "framework/__init__.py", "framework/data.py", "framework/io.py",
                 "framework/persistence.py", "my_model/__init__.py", "requirements.txt"):
        if not os.path.exists(os.path.join(HERE, name)):
            fail(f"{name} missing - the framework must ship unmodified")
    log("2/4 train on sample_data ...")
    run(["--model", "train", "--input", data, "--output-dir", out], LOCAL_TRAIN_LIMIT_S)
    log("3/4 test on every evaluation point (causal cut) ...")
    run(["--model", "test", "--input", data, "--state-dir", out, "--output-dir", out, "--eval-point", "all"],
        LOCAL_TEST_LIMIT_S)
    log("4/4 checking output schema ...")
    df = pd.read_csv(os.path.join(out, "output.csv"))
    ev = pd.read_csv(os.path.join(data, "checkups", "evaluation_points.csv"))
    if list(df.columns) != ["checkup", "date", "SOH_est"]:
        fail(f"output.csv has columns {list(df.columns)}, expected checkup, date, SOH_est")
    if set(df["checkup"]) != set(ev["checkup"]):
        fail("output must contain one row per evaluation point")
    if df["SOH_est"].isna().any():
        fail(f"{int(df['SOH_est'].isna().sum())} SOH_est values are NaN")
    if not df["SOH_est"].between(50, 110).all():
        fail("SOH_est must be in percent (50..110)")
    init = open(os.path.join(HERE, "my_model", "__init__.py"), encoding="utf-8").read()
    active = [l for l in init.splitlines() if l.strip() and not l.strip().startswith("#")]
    if any("model_example" in l for l in active):
        log("WARNING: ActiveModel still points at the EXAMPLE model - flip the switch in my_model/__init__.py")
    log(f"PASSED - output schema satisfied ({len(df)} evaluation points). Output: {out}/output.csv")
    log("Reminder: package ONE zip named <TeamName>_Challenge2.zip (without data/), test it from a clean")
    log("extraction inside a fresh venv, and keep run_model.py / framework/ / validate_submission.py unmodified.")
    open(os.path.join(HERE, "validation_report.txt"), "w", encoding="utf-8").write("\n".join(report))


if __name__ == "__main__":
    main()
