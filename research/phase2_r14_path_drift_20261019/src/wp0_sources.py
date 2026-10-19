"""WP0.1: copy read-only sources from earlier rounds (git show) and write sources/SOURCES.md with ref, path, SHA256."""
import datetime, hashlib, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ST = os.path.dirname(HERE)
WT = os.path.abspath(os.path.join(ST, "..", ".."))
MAIN = "/Users/shane/Desktop/Arena_1013_model"
SRC = os.path.join(ST, "sources")

R11 = ("origin/exp/phase2-r11-eps-transfer-20261018", "research/phase2_r11_eps_transfer_20261018")
R8 = ("origin/exp/phase2-r8-error-table-20261017", "research/phase2_r8_error_table_20261017")
R12 = ("origin/exp/phase2-r12-eps-level-20261019", "research/phase2_r12_eps_level_20261019")
R13 = ("origin/exp/phase2-r13-top-tail-20261019", "research/phase2_r13_top_tail_20261019")

REQUIRED = [
    (R11, "FINAL_REPORT.md", "r11/FINAL_REPORT.md"),
    (R11, "wp2/REPORT.md", "r11/wp2_REPORT.md"),
    (R11, "wp4/pack_drivers.csv", "r11/wp4_pack_drivers.csv"),
    (R11, "src/drift.py", "r11/drift.py"),
    (R8, "DATA_DICTIONARY.md", "r8/DATA_DICTIONARY.md"),
    (R8, "outputs/table_events.csv", "r8/table_events.csv"),
    (R8, "outputs/table_anchors.csv", "r8/table_anchors.csv"),
    (R8, "outputs/table_cycles.csv", "r8/table_cycles.csv"),
]
OPTIONAL = [
    (R12, "src/ahchain.py", "r12/ahchain.py"),
    (R12, "wp3/pairs.csv", "r12/wp3_pairs.csv"),
    (R13, "wp3/R13_RESULT.json", "r13/R13_RESULT.json"),
]
BASE_DIR = "research/phase2_rebound_diagnosis_20261015"


def git(*args):
    return subprocess.run(["git", "-C", MAIN] + list(args), capture_output=True, check=False)


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def main():
    git("fetch", "origin")
    rows, missing = [], []
    for (ref, root), rel, dst in REQUIRED + OPTIONAL:
        commit = git("rev-parse", "--verify", "-q", ref).stdout.decode().strip()
        r = git("show", f"{ref}:{root}/{rel}")
        if r.returncode != 0:
            if ((ref, root), rel, dst) in REQUIRED:
                sys.exit(f"required source missing: {ref}:{root}/{rel}")
            missing.append((ref, commit, f"{root}/{rel}"))
            continue
        out = os.path.join(SRC, dst)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "wb").write(r.stdout)
        rows.append((dst, ref, commit[:7], f"{root}/{rel}", sha(out)))
    base_commit = subprocess.run(["git", "-C", WT, "rev-parse", "--short", "6525edf"],
                                 capture_output=True, text=True).stdout.strip()
    for dirpath, _, files in os.walk(os.path.join(WT, BASE_DIR)):
        for f in sorted(files):
            p = os.path.join(dirpath, f)
            rel = os.path.relpath(p, WT)
            dst = os.path.join("base/rebound_diagnosis", os.path.relpath(p, os.path.join(WT, BASE_DIR)))
            out = os.path.join(SRC, dst)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            shutil.copy2(p, out)
            rows.append((dst, "base (worktree)", base_commit, rel, sha(out)))
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = ["# Sources", "",
             f"Copied {stamp} by `src/wp0_sources.py` after `git -C {MAIN} fetch origin`. "
             "Read-only copies; the originals are not modified.", "",
             "| copy (under `sources/`) | ref | commit | path at ref | SHA256 |", "|---|---|---|---|---|"]
    lines += [f"| `{d}` | `{r}` | `{c}` | `{p}` | `{h}` |" for d, r, c, p, h in rows]
    lines += ["", "## Optional sources not available", "",
              "| ref | commit at check | path | status |", "|---|---|---|---|"]
    lines += [f"| `{r}` | `{c[:7]}` | `{p}` | not available ({stamp}) |" for r, c, p in missing]
    lines += ["", "Optional sources are re-checked at the step that would use them (see `notes/DECISIONS.md`).", ""]
    open(os.path.join(SRC, "SOURCES.md"), "w").write("\n".join(lines))
    print(f"{len(rows)} copied, {len(missing)} optional missing")


if __name__ == "__main__":
    main()
