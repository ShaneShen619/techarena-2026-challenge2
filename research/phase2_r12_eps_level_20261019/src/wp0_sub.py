"""WP0.3: run SUB with the package CLI and research copies that change only EPS_EXTRA_AH."""
import difflib, json, os, re, shutil, subprocess, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ST = os.path.dirname(HERE)
WT = os.path.abspath(os.path.join(ST, "..", ".."))
PKG = os.path.join(WT, "TechArena_Challenge2_Team_Package")
DATA = os.path.join(PKG, "data")
VAR = os.path.join(ST, "cache", "variants")
EPS = (0.0, 0.2, 0.4, 0.6, 0.8)
CODE = ("run_model.py", "framework", "my_model")


def run_cli(pkg_dir, out_dir):
    """train + test (all evaluation points) through the package's own run_model.py."""
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    cli = os.path.join(pkg_dir, "run_model.py")
    for args in (["--model", "train", "--input", DATA, "--output-dir", out_dir],
                 ["--model", "test", "--input", DATA, "--state-dir", out_dir, "--output-dir", out_dir,
                  "--eval-point", "all"]):
        subprocess.run([sys.executable, "-B", cli] + args, check=True, capture_output=True, text=True)
    return pd.read_csv(os.path.join(out_dir, "output.csv"))


def build_variant(eps):
    """Copy of the package code with EPS_EXTRA_AH = eps; returns (dir, unified diff of model_template.py)."""
    d = os.path.join(VAR, f"eps_{eps:.1f}")
    if os.path.exists(d):
        shutil.rmtree(d)
    os.makedirs(d)
    for c in CODE:
        src = os.path.join(PKG, c)
        (shutil.copytree(src, os.path.join(d, c), ignore=shutil.ignore_patterns("__pycache__"))
         if os.path.isdir(src) else shutil.copy2(src, os.path.join(d, c)))
    path = os.path.join(d, "my_model", "model_template.py")
    old = open(path).read()
    new, n = re.subn(r"^EPS_EXTRA_AH = 0\.4 ", f"EPS_EXTRA_AH = {eps:.1f} ", old, flags=re.M)
    assert n == 1
    open(path, "w").write(new)
    diff = [l for l in difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm="", n=0)
            if l[:1] in "+-" and not l.startswith(("+++", "---"))]
    return d, diff


def main():
    sub = run_cli(PKG, os.path.join(ST, "cache", "out_SUB"))
    sub.to_csv(os.path.join(ST, "wp0", "SUB_SOH.csv"), index=False)
    wide = sub[["checkup", "date"]].copy()
    diffs = {}
    for eps in EPS:
        d, diff = build_variant(eps)
        diffs[f"{eps:.1f}"] = diff
        out = run_cli(d, os.path.join(ST, "cache", f"out_eps_{eps:.1f}"))
        wide[f"SOH_eps{eps:.1f}"] = out.set_index("checkup").loc[wide["checkup"], "SOH_est"].to_numpy()
    cols = [f"SOH_eps{e:.1f}" for e in EPS]
    y = wide[cols].to_numpy(float)
    wide["slope_pp_per_Ah"] = np.round(np.polyfit(np.array(EPS), y.T, 1)[0], 4)
    wide["range_pp"] = np.round(y.max(1) - y.min(1), 3)
    wide["eps0.4_minus_SUB_pp"] = np.round(wide["SOH_eps0.4"] - sub["SOH_est"].to_numpy(), 3)
    wide.to_csv(os.path.join(ST, "wp0", "eps_extra_sensitivity.csv"), index=False)
    nominal = 100.0 / 102.0
    # the model's only other use of EPS_EXTRA is the sqrt(t) gap branch (CK2): loss_j depends on eps, so
    # dQ/deps = sqrt(te_k)/sqrt(te_1) there. Reproduce that factor from the package's own helper.
    sys.path.insert(0, PKG)
    from framework.data import load_dataset
    from my_model import model_template as mt
    ck = pd.DatetimeIndex(pd.to_datetime(sub["date"]))
    ds = load_dataset(DATA, until=ck[2])
    te = mt._effective_days(ds.operation, ck, [ck[1], ck[1], ck[2]])
    ck2_factor = float(np.sqrt(te[2]) / np.sqrt(te[0]))
    sl = wide.set_index("checkup")["slope_pp_per_Ah"]
    # unrounded in-process slopes (diagnostic for the 0.001 pp output rounding), same model code
    model = mt.MyModel(); model.fit(load_dataset(DATA))
    unrounded = {}
    for k in range(1, 8):
        dk = load_dataset(DATA, until=ck[k]); q = []
        for eps in EPS:
            mt.EPS_EXTRA_AH = eps
            q.append(100.0 * model.estimate_capacity_ah(dk, ck[k]) / 102.0)
        mt.EPS_EXTRA_AH = 0.4
        unrounded[f"CK{k}"] = round(float(np.polyfit(np.array(EPS), np.array(q), 1)[0]), 6)
    checks = {
        "eps0.4_reproduces_SUB": bool((wide["eps0.4_minus_SUB_pp"].abs() == 0).all()),
        "CK1_unchanged": bool(wide.set_index("checkup").loc["CK1", "range_pp"] == 0),
        "nominal_pp_per_Ah": round(nominal, 4),
        "CK3_CK7_slopes": {k: float(sl[k]) for k in ["CK3", "CK4", "CK5", "CK6", "CK7"]},
        "CK3_CK7_at_nominal_within_rounding": bool(all(abs(sl[k] - nominal) <= 0.0026
                                                       for k in ["CK3", "CK4", "CK5", "CK6", "CK7"])),
        "CK2_slope": float(sl["CK2"]),
        "CK2_expected_sqrt_branch": round(nominal * ck2_factor, 4),
        "CK2_te_days_45eq": {"CK1": round(te[0], 3), "CK2": round(te[2], 3)},
        "unrounded_slopes_pp_per_Ah": unrounded,
        "variant_diffs": diffs,
        "note": "outputs are rounded to 0.001 pp by run_model.py; slope = OLS over the five EPS_EXTRA values",
    }
    json.dump(checks, open(os.path.join(ST, "wp0", "eps_extra_checks.json"), "w"), indent=1)
    print(wide.to_string()); print(json.dumps(checks, indent=1))


if __name__ == "__main__":
    main()
