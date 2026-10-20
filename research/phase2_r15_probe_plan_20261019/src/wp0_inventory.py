"""WP0.3-0.4: input templates, leaderboard-log reading and the inventory of the user's existing zips.

The user's zips are read only: hashed, then extracted into the git-ignored cache/existing/<stem>/ to hash their
my_model/model_template.py, match it against the history of exp/phase2-anchor-step-20261013, and run the package
CLI from the extracted copy.  Run:  python3 -B src/wp0_inventory.py
"""
import csv
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ST = os.path.dirname(HERE)
WT = os.path.abspath(os.path.join(ST, "..", ".."))
DATA = os.path.join(WT, "TechArena_Challenge2_Team_Package", "data")
EXIST = os.path.join(ST, "cache", "existing")
INPUTS = os.path.join(ST, "inputs")
OUT = os.path.join(ST, "wp0")
ZIP_GLOBS = ["/Users/shane/Desktop/Arena项目书面文件/提交包/*.zip", "/Users/shane/Desktop/*Challenge2*.zip"]
BRANCH = "exp/phase2-anchor-step-20261013"
TEMPLATE = "TechArena_Challenge2_Team_Package/my_model/model_template.py"
LOG_COLS = ["board_date", "package_file", "package_sha256", "model_commit", "metrics_verbatim", "rank", "notes"]


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def git(*args):
    return subprocess.run(["git", "-C", WT] + list(args), check=True, capture_output=True).stdout


def templates():
    """Create the three input templates if missing; never overwrite a user's file."""
    os.makedirs(INPUTS, exist_ok=True)
    made = []
    p = os.path.join(INPUTS, "leaderboard_log.csv")
    if not os.path.exists(p):
        with open(p, "w", newline="") as f:
            csv.writer(f).writerow(LOG_COLS)
        made.append("leaderboard_log.csv")
    for name, text in (("deadline.txt", "unknown\n"), ("pptx_path.txt", "template\n")):
        q = os.path.join(INPUTS, name)
        if not os.path.exists(q):
            open(q, "w").write(text)
            made.append(name)
    return made


def read_inputs():
    log = pd.read_csv(os.path.join(INPUTS, "leaderboard_log.csv"), dtype=str).fillna("")
    assert list(log.columns) == LOG_COLS, list(log.columns)
    deadline = open(os.path.join(INPUTS, "deadline.txt")).read().strip()
    pptx = open(os.path.join(INPUTS, "pptx_path.txt")).read().strip()
    return log, deadline, pptx


def template_history():
    """{sha256 of model_template.py: [commits on BRANCH that carry exactly this file]}."""
    out = {}
    for c in git("log", "--format=%H", BRANCH, "--", TEMPLATE).decode().split():
        h = hashlib.sha256(git("show", f"{c}:{TEMPLATE}")).hexdigest()
        out.setdefault(h, []).append(c[:7])
    return out


def run_cli(pkg_dir, out_dir):
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    cli = os.path.join(pkg_dir, "run_model.py")
    for args in (["--model", "train", "--input", DATA, "--output-dir", out_dir],
                 ["--model", "test", "--input", DATA, "--state-dir", out_dir, "--output-dir", out_dir,
                  "--eval-point", "all"]):
        subprocess.run([sys.executable, "-B", cli] + args, check=True, capture_output=True, text=True, cwd=pkg_dir)
    return pd.read_csv(os.path.join(out_dir, "output.csv")).set_index("checkup")["SOH_est"]


def main():
    made = templates()
    log, deadline, pptx = read_inputs()
    hist = template_history()
    zips = sorted({z for g in ZIP_GLOBS for z in glob.glob(g)})
    rows = []
    for z in zips:
        stem = os.path.splitext(os.path.basename(z))[0].replace(" ", "_")
        dst = os.path.join(EXIST, stem)
        if os.path.exists(dst):
            shutil.rmtree(dst)
        with zipfile.ZipFile(z) as f:
            f.extractall(dst)
        mt = os.path.join(dst, "my_model", "model_template.py")
        init = open(os.path.join(dst, "my_model", "__init__.py")).read()
        h = sha_file(mt)
        soh = run_cli(dst, os.path.join(ST, "cache", "existing_out", stem))
        zsha = sha_file(z)
        logged = log[(log["package_sha256"].str.lower() == zsha) | (log["package_file"] == os.path.basename(z))]
        rows.append(dict(
            name=os.path.basename(z), path=z, size_bytes=os.path.getsize(z), sha256=zsha,
            model_template_sha256=h, matching_commits=";".join(hist.get(h, [])) or "none",
            active_model_is_mymodel="\nfrom .model_template import MyModel as ActiveModel" in init,
            pptx_in_zip=";".join(n for n in zipfile.ZipFile(z).namelist() if n.lower().endswith(".pptx")),
            **{c: float(soh[c]) for c in soh.index},
            logged_as_submitted=("yes: " + ";".join(logged["board_date"])) if len(logged) else "no (log empty)"
            if log.empty else "no"))
    inv = pd.DataFrame(rows)
    os.makedirs(OUT, exist_ok=True)
    inv.to_csv(os.path.join(OUT, "existing_packages.csv"), index=False)
    # the base SUB through the package CLI (re-verification of EXPECTED_SOH)
    sub = run_cli(os.path.join(WT, "TechArena_Challenge2_Team_Package"), os.path.join(ST, "cache", "out_SUB"))
    sub.to_csv(os.path.join(OUT, "SUB_SOH.csv"))
    json.dump(dict(templates_created=made, log_rows=int(len(log)),
                   observations="no observations" if log.empty else f"{len(log)} rows",
                   deadline=deadline, pptx_path=pptx, n_zips=len(zips),
                   SUB_SOH={c: float(sub[c]) for c in sub.index}),
              open(os.path.join(OUT, "inputs_state.json"), "w"), indent=1, ensure_ascii=False)
    pd.set_option("display.width", 250)
    print(inv.drop(columns=["path"]).to_string())
    print("SUB:", sub.to_dict())
    print("templates created:", made, "| log rows:", len(log), "| deadline:", deadline, "| pptx:", pptx)


if __name__ == "__main__":
    main()
