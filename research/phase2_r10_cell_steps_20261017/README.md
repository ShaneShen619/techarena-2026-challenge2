<a id="en"></a>

# Round 10 — robust per-cell step aggregation

> **Language:** English · [中文](#zh)

Tests three ideas for combining the four cells' graphite-step locations in SUB = T_main (`5cd305c`), one at a time, each registered before evaluation. **Result** ([FINAL_REPORT.md](FINAL_REPORT.md)):
- **A3** passes every gate (causal 0.157 → 0.147 pp, robust on 6/6 leave-one-variant-out rebuilds). A3 = median over 6 detection variants per cell, then median over the 4 cells.
- Idea B adds nothing, and idea C's mechanism is not supported.
- The candidate class passes all checks and is **not wired**.

| Path | Content |
|---|---|
| [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md) | the execution prompt (English governs) |
| [notes/](notes/) | STATUS, DECISIONS |
| [sources/SOURCES.md](sources/SOURCES.md) | copied code with SHA256 |
| [src/](src/) | round 8 copies, `cellcand.py` (branch-freeze candidate framework), `gates10.py`, `diag10.py`, `residuals10.py` |
| [wp0/](wp0/REPORT.md) … [wp4/](wp4/REPORT.md) | protocol, script, outputs, report per WP; `wp4/candidate_model/` holds the A3 class |
| `cache/` | git-ignored: archived package, pickled cuts, Python 3.11 venv, package copy |

## Rebuild (one command per WP, from this directory)

```bash
cd /Users/shane/Desktop/Arena_1017_r10_cells/research/phase2_r10_cell_steps_20261017
mkdir -p cache/submitted_package && git -C /Users/shane/Desktop/Arena_1013_model archive 5cd305c TechArena_Challenge2_Team_Package | tar -x -C cache/submitted_package && git -C /Users/shane/Desktop/Arena_1013_model show 5cd305c:research/phase2_v3_20261015/package_submission.py > cache/package_submission_5cd305c.py
python3 -B wp0/run_wp0.py                                   # WP0: re-baseline, caches, noise scale
python3 -B wp1/run_wp1.py                                   # WP1: idea A
python3 -B wp2/run_wp2.py                                   # WP2: idea B
python3 -B wp3/run_wp3a.py                                  # WP3: mechanism check (exits)
python3 -B wp4/run_wp4.py && python3 -B wp4/check_candidate.py && sh wp4/check_package.sh   # WP4
```

WP5 is the writing of FINAL_REPORT.md and this README. CSV/JSON outputs are byte-identical on rerun.

---

<a id="zh"></a>

# 第 10 轮——稳健的单体台阶合并

> **语言：** [English](#en) · 中文

逐个检验三种合并四个单体石墨台阶位置的想法，每个都先登记后评估。**结果**（见 [FINAL_REPORT.md](FINAL_REPORT.md)）：
- **A3**（每个电芯在 6 种检测变体上取中位数，再对 4 个电芯取中位数）通过全部检验：因果 0.157 → 0.147 pp，6 个留一变体重建全部稳健。
- 想法 B 没有增加任何东西，想法 C 的机制不成立。
- 候选模型类通过全部检查，**未接入**。

重建命令见英文部分（每个 WP 一条命令）。
