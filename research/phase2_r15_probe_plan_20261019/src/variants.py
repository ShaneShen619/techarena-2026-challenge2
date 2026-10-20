"""Registered round-15 variant builder (WP1): research copies of the base package under cache/variants/ and SOH
vectors through the package CLI.  The base package is never modified.

- EX: the base package with the my_model/__init__.py switch pointed at ExampleModel (the reference baseline).
- P_A3fix: round 12's registered hook `a3fix_variant(a3_rel, segment=6)` (sources/r12/wp4_run.py), applied as an exact
  text replacement to the base model_template.py with a3_rel from sources/r12/wp4_budget_decision.json.
"""
import difflib
import importlib.util
import json
import os
import shutil
import subprocess
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ST = os.path.dirname(HERE)
WT = os.path.abspath(os.path.join(ST, "..", ".."))
PKG = os.path.join(WT, "TechArena_Challenge2_Team_Package")
DATA = os.path.join(PKG, "data")
VAR = os.path.join(ST, "cache", "variants")
CODE = ("run_model.py", "framework", "my_model")
SWITCH_EX = ("# from .model_example import ExampleModel as ActiveModel   # <-- the reference baseline (score = 1.0)\n"
             "from .model_template import MyModel as ActiveModel         # <-- your model",
             "from .model_example import ExampleModel as ActiveModel   # <-- the reference baseline (score = 1.0)\n"
             "# from .model_template import MyModel as ActiveModel         # <-- your model")


def _r12():
    spec = importlib.util.spec_from_file_location("r12_wp4_run", os.path.join(ST, "sources", "r12", "wp4_run.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def a3_rel():
    d = json.load(open(os.path.join(ST, "sources", "r12", "wp4_budget_decision.json")))
    assert d["anchor3_rule"]["G_a3_identified"] is True
    return float(d["anchor3_rule"]["a3_rel"])


def replacements(name):
    if name == "SUB":
        return [], []
    if name == "EX":
        return [], [SWITCH_EX]
    if name == "P_A3fix":
        return _r12().a3fix_variant(a3_rel()), []
    raise KeyError(name)


def build(name, root=VAR):
    """Copy run_model.py, framework/ and my_model/ of the base package and apply the registered replacements.
    Returns (directory, diff lines of model_template.py, diff lines of __init__.py)."""
    d = os.path.join(root, name)
    if os.path.exists(d):
        shutil.rmtree(d)
    os.makedirs(d)
    for c in CODE:
        src = os.path.join(PKG, c)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(d, c), ignore=shutil.ignore_patterns("__pycache__"))
        else:
            shutil.copy2(src, os.path.join(d, c))
    rep_t, rep_i = replacements(name)
    diffs = []
    for fname, reps in (("model_template.py", rep_t), ("__init__.py", rep_i)):
        path = os.path.join(d, "my_model", fname)
        old = open(path).read()
        new = old
        for a, b in reps:
            assert new.count(a) == 1, (name, fname)
            new = new.replace(a, b)
        open(path, "w").write(new)
        diffs.append([ln for ln in difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm="", n=0)
                      if ln[:1] in "+-" and not ln.startswith(("+++", "---"))])
    return d, diffs[0], diffs[1]


def run_cli(pkg_dir, out_dir):
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    cli = os.path.join(pkg_dir, "run_model.py")
    for args in (["--model", "train", "--input", DATA, "--output-dir", out_dir],
                 ["--model", "test", "--input", DATA, "--state-dir", out_dir, "--output-dir", out_dir,
                  "--eval-point", "all"]):
        subprocess.run([sys.executable, "-B", cli] + args, check=True, capture_output=True, text=True, cwd=pkg_dir)
    return pd.read_csv(os.path.join(out_dir, "output.csv")).set_index("checkup")["SOH_est"]


def soh(name):
    d, dt, di = build(name)
    s = run_cli(d, os.path.join(ST, "cache", "out", name))
    return {c: float(s[c]) for c in s.index}, dt, di
