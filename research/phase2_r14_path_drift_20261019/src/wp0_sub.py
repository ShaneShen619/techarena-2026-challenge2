"""WP0.2: run SUB (my_model/model_template.py at the base commit) with the package CLI; save wp0/SUB_SOH.csv."""
import hashlib, os, shutil, subprocess, sys
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ST = os.path.dirname(HERE)
WT = os.path.abspath(os.path.join(ST, "..", ".."))
PKG = os.path.join(WT, "TechArena_Challenge2_Team_Package")
DATA = os.path.join(PKG, "data")


def run_cli(pkg_dir, out_dir):
    """train + test (all evaluation points, each causal) through the package's own run_model.py."""
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    cli = os.path.join(pkg_dir, "run_model.py")
    for args in (["--model", "train", "--input", DATA, "--output-dir", out_dir],
                 ["--model", "test", "--input", DATA, "--state-dir", out_dir, "--output-dir", out_dir,
                  "--eval-point", "all"]):
        subprocess.run([sys.executable, "-B", cli] + args, check=True, capture_output=True, text=True)
    return pd.read_csv(os.path.join(out_dir, "output.csv"))


def main():
    sub = run_cli(PKG, os.path.join(ST, "cache", "out_SUB"))
    sub["Q_est_Ah"] = (sub["SOH_est"] * 102.0 / 100.0).round(4)
    sub.to_csv(os.path.join(ST, "wp0", "SUB_SOH.csv"), index=False)
    h = hashlib.sha256(open(os.path.join(PKG, "my_model", "model_template.py"), "rb").read()).hexdigest()
    print(sub.to_string(index=False))
    print("model_template.py sha256", h)


if __name__ == "__main__":
    main()
