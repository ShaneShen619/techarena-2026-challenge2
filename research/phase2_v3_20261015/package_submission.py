"""Build <TeamName>_Challenge2.zip exactly as submission_instructions_2026.md prescribes, then
test it from a clean extraction in a fresh Python 3.11 venv.

usage: python3 package_submission.py TEAM_NAME [--members "A, B, C"] [--pptx PATH] [--out DIR]
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.abspath(os.path.join(HERE, "..", "..", "TechArena_Challenge2_Team_Package"))
PY311 = "/opt/homebrew/bin/python3.11"
FILES = ["run_model.py", "validate_submission.py", "requirements.txt", "README.md", "REPORT.md",
         "my_model/__init__.py", "my_model/model_template.py", "my_model/model_example.py"]
DIRS = ["framework", "sample_data"]
EXPECTED_SOH = {"CK0": 98.441, "CK1": 95.992, "CK2": 94.507, "CK3": 93.541,
                "CK4": 92.811, "CK5": 92.081, "CK6": 91.331, "CK7": 90.821}


def stage(team, members, pptx, root):
    for f in FILES:
        os.makedirs(os.path.dirname(os.path.join(root, f)) or root, exist_ok=True)
        shutil.copy2(os.path.join(PKG, f), os.path.join(root, f))
    for d in DIRS:
        shutil.copytree(os.path.join(PKG, d), os.path.join(root, d),
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
    rep = os.path.join(root, "REPORT.md")
    s = open(rep, encoding="utf-8").read().replace("**Team:** <TeamName>", f"**Team:** {team}")
    if members:
        s = s.replace("**Members:** <names>", f"**Members:** {members}")
    open(rep, "w", encoding="utf-8").write(s)
    shutil.copy2(pptx, os.path.join(root, f"{team}_Final_Presentation.pptx"))


def audit(root, team):
    names = sorted(os.path.relpath(os.path.join(d, f), root) for d, _, fs in os.walk(root) for f in fs)
    problems = [n for n in names if n.startswith("data/") or "__pycache__" in n
                or os.path.basename(n).startswith(".")]
    required = FILES + [f"{team}_Final_Presentation.pptx", "framework/data.py", "framework/io.py",
                        "framework/persistence.py", "framework/__init__.py"]
    missing = [r for r in required if r not in names]
    init = open(os.path.join(root, "my_model", "__init__.py")).read()
    switch = "\nfrom .model_template import MyModel as ActiveModel" in init
    return names, problems, missing, switch


def build_zip(root, path):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for d, _, fs in sorted(os.walk(root)):
            for f in sorted(fs):
                full = os.path.join(d, f)
                z.write(full, os.path.relpath(full, root))


def clean_test(zip_path, work):
    ext = os.path.join(work, "extracted")
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(ext)
    venv = os.path.join(work, "venv")
    subprocess.run([PY311, "-m", "venv", venv], check=True)
    py = os.path.join(venv, "bin", "python")
    subprocess.run([py, "-m", "pip", "install", "-q", "-r", "requirements.txt"], cwd=ext, check=True)
    versions = subprocess.run([py, "-c", "import sys,numpy,pandas;print(sys.version.split()[0],numpy.__version__,pandas.__version__)"],
                              capture_output=True, text=True, check=True).stdout.strip()
    val = subprocess.run([py, "validate_submission.py"], cwd=ext, capture_output=True, text=True)
    out = os.path.join(work, "out")
    data = os.path.join(PKG, "data")
    subprocess.run([py, "run_model.py", "--model", "train", "--input", data, "--output-dir", out],
                   cwd=ext, check=True, capture_output=True)
    subprocess.run([py, "run_model.py", "--model", "test", "--input", data, "--state-dir", out,
                    "--output-dir", out, "--eval-point", "all"], cwd=ext, check=True, capture_output=True)
    csv = next(os.path.join(out, f) for f in os.listdir(out) if f.endswith(".csv"))
    rows = [line.split(",") for line in open(csv).read().strip().splitlines()[1:]]
    got = {r[0]: float(r[2]) for r in rows}
    return versions, val, got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("team")
    ap.add_argument("--members", default=None)
    ap.add_argument("--pptx", default=os.path.join(PKG, "TechArena_Final_Presentation_Template.pptx"))
    ap.add_argument("--out", default=os.path.expanduser("~/Desktop"))
    a = ap.parse_args()
    work = tempfile.mkdtemp(prefix="c2_pkg_")
    root = os.path.join(work, "stage")
    stage(a.team, a.members, a.pptx, root)
    names, problems, missing, switch = audit(root, a.team)
    if problems or missing or not switch:
        sys.exit(f"audit failed: problems={problems} missing={missing} switch={switch}")
    zip_path = os.path.join(a.out, f"{a.team}_Challenge2.zip")
    build_zip(root, zip_path)
    versions, val, got = clean_test(zip_path, work)
    ok_val = val.returncode == 0 and "PASSED" in val.stdout
    ok_out = got == EXPECTED_SOH
    print("zip:", zip_path, f"({os.path.getsize(zip_path) / 1e6:.2f} MB, {len(names)} files)")
    print("contents:", *names, sep="\n  ")
    print("fresh venv (python, numpy, pandas):", versions)
    print("validate_submission.py:", "PASSED" if ok_val else "FAILED")
    print(val.stdout.strip()[-600:])
    print("full-data output equals expected:", ok_out, got)
    shutil.rmtree(work, ignore_errors=True)
    if not (ok_val and ok_out):
        sys.exit(1)


if __name__ == "__main__":
    main()
