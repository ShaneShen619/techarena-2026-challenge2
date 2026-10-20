"""WP0.1: copy the read-only sources into sources/ with `git show <ref>:<path>` and write sources/SOURCES.md.

Run after `git -C /Users/shane/Desktop/Arena_1013_model fetch origin`:  python3 -B src/wp0_sources.py
"""
import datetime
import hashlib
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ST = os.path.dirname(HERE)
WT = os.path.abspath(os.path.join(ST, "..", ".."))
SRC = os.path.join(ST, "sources")

R6 = ("origin/exp/phase2-r6-robust-20261016", "research/phase2_r6_robust_20261016/")
R11 = ("origin/exp/phase2-r11-eps-transfer-20261018", "research/phase2_r11_eps_transfer_20261018/")
R12 = ("origin/exp/phase2-r12-eps-level-20261019", "research/phase2_r12_eps_level_20261019/")
R13 = ("origin/exp/phase2-r13-top-tail-20261019", "research/phase2_r13_top_tail_20261019/")
R14 = ("origin/exp/phase2-r14-path-drift-20261019", "research/phase2_r14_path_drift_20261019/")

# (copy name under sources/, (ref, prefix), path below the prefix, role, required by the prompt)
SPECS = [
    ("r6/wp1_protocol.json", R6, "wp1/protocol.json", "18-hypothesis grid h = (Delta, f, d), score s", True),
    ("r6/wp1_run_wp1.py", R6, "wp1/run_wp1.py", "T_k(h), s, prior weights", True),
    ("r6/wp6_run_wp6.py", R6, "wp6/run_wp6.py", "probe delta-s machinery", True),
    ("r6/wp6_REPORT.md", R6, "wp6/REPORT.md", "old probe plan", True),
    ("r6/wp6_probe_plan.json", R6, "wp6/outputs/wp6_probe_plan.json", "old probe vectors (older SUB 21a7a55)", True),
    # inputs of round 6's T_k(h) and its reproduction check (needed to build T_k(h) exactly as round 6)
    ("r6/wp1_predictions.csv", R6, "wp1/outputs/wp1_predictions.csv", "proxy column = Q_fc,k + eps0 + Delta (harness)", False),
    ("r6/wp1_scores_long.csv", R6, "wp1/outputs/wp1_scores_long.csv", "reproduction check of s", False),
    ("r6/wp6_delta_s_vs_SUB_by_h.csv", R6, "wp6/outputs/wp6_delta_s_vs_SUB_by_h.csv", "reproduction check of delta-s", False),
    ("r6/wp3_run_wp3.py", R6, "wp3/run_wp3.py", "3b eps-drift transform (P_drift)", False),
    ("r6/wp2_run_wp2.py", R6, "wp2/run_wp2.py", "F1_S_B fusion (P_stress_early rebuild check)", False),
    ("r6/wp2_selection.json", R6, "wp2/outputs/wp2_selection.json", "F1 fusion parameters sigma_SUB, sigma_S0", False),
    ("r6/round3_harness.py", (R6[0], "research/phase2_round3_models_20261014/"), "src/harness.py",
     "QFC, EPS0 definition (round 3 harness, as imported by round 6)", False),
    ("r6/round4_jumps.csv", (R6[0], "research/phase2_round4_signals_20261014/"), "stage_5/outputs/jumps.csv",
     "R_k = recovery_Ah_with_aging", False),
    ("r11/drift.py", R11, "src/drift.py", "round 11 drift model", True),
    ("r11/wp5_decision.json", R11, "wp5/decision.json", "round 11 d interval [-0.036, +0.052]", True),
    ("r12/wp4_budget_decision.json", R12, "wp4/budget_decision.json", "round 12 decision (L1/L2/L3, G_a3)", True),
    ("r12/wp4_SOH_variants.csv", R12, "wp4/SOH_variants.csv", "round 12 SOH variants", True),
    ("r12/wp4_R13_HANDOFF.json", R12, "wp4/R13_HANDOFF.json", "round 12 hand-off", True),
    ("r12/wp4_REPORT.md", R12, "wp4/REPORT.md", "round 12 WP4 report", True),
    ("r12/wp4_run.py", R12, "src/wp4_run.py", "registered SUB_A3fix hook (a3fix_variant)", False),
    ("r13/wp3_R13_RESULT.json", R13, "wp3/R13_RESULT.json", "round 13 outcome", True),
    ("r13/wp3_SOH_variants.csv", R13, "wp3/SOH_variants.csv", "round 13 SOH variants", True),
    ("r14/wp3_R14_RESULT.json", R14, "wp3/R14_RESULT.json", "round 14 outcome", True),
    ("r14/wp3_SOH_variants.csv", R14, "wp3/SOH_variants.csv", "round 14 SOH variants", True),
]
WORKTREE_SPECS = [
    ("base/package_submission.py", "research/phase2_v3_20261015/package_submission.py", "packaging script"),
]


def git(*args):
    return subprocess.run(["git", "-C", WT] + list(args), check=True, capture_output=True).stdout


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    rows, missing = [], []
    tips = {}
    for name, (ref, prefix), path, role, req in SPECS:
        tips.setdefault(ref, git("rev-parse", "--short", ref).decode().strip())
        full = prefix + path
        try:
            b = git("show", f"{ref}:{full}")
        except subprocess.CalledProcessError:
            missing.append((ref, tips[ref], full, role))
            continue
        out = os.path.join(SRC, name)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "wb").write(b)
        rows.append((name, ref, tips[ref], full, role, "yes" if req else "support", sha(b)))
    base = git("rev-parse", "--short", "HEAD").decode().strip()
    for name, path, role in WORKTREE_SPECS:
        b = open(os.path.join(WT, path), "rb").read()
        out = os.path.join(SRC, name)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "wb").write(b)
        rows.append((name, "worktree (base 6525edf)", base, path, role, "yes", sha(b)))
    md = [
        "# Sources",
        "",
        f"Copied {now} by `src/wp0_sources.py` after `git -C /Users/shane/Desktop/Arena_1013_model fetch origin`. "
        "Read-only copies; the originals are not modified. *required* = listed by the prompt; *support* = needed to "
        "build round 6's T_k(h) exactly or to check a rebuild.",
        "",
        "| copy (under `sources/`) | ref | commit | path at ref | role | required | SHA256 |",
        "|---|---|---|---|---|---|---|",
    ]
    md += [f"| `{a}` | `{b}` | `{c}` | `{d}` | {e} | {f} | `{g}` |" for a, b, c, d, e, f, g in rows]
    md += ["", "## Rounds 12–14 presence", "", "| round | ref | commit | status |", "|---|---|---|---|"]
    for r, (ref, _) in (("12", R12), ("13", R13), ("14", R14)):
        req_missing = [m for m in missing if m[0] == ref]
        md.append(f"| {r} | `{ref}` | `{tips[ref]}` | {'present' if not req_missing else 'incomplete'} |")
    if missing:
        md += ["", "## Not available", "", "| ref | commit | path | role |", "|---|---|---|---|"]
        md += [f"| `{a}` | `{b}` | `{c}` | {d} |" for a, b, c, d in missing]
    md += ["", "## User files (listed and hashed only)", "",
           "See `wp0/existing_packages.csv`. Zips are extracted only into the git-ignored `cache/existing/`.", ""]
    open(os.path.join(SRC, "SOURCES.md"), "w").write("\n".join(md))
    print(f"{len(rows)} copied, {len(missing)} missing")
    for m in missing:
        print("missing:", m)


if __name__ == "__main__":
    main()
