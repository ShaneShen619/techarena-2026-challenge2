<a id="en"></a>

# Sources (round 10)

> **Language:** English · [中文](#zh)

Base: local branch `exp/phase2-r9-fixes-20261017` at `6749c63` (contains rounds 8 and 9).

| Copied file (this study) | Source | SHA256 (source, 12 chars) | Change |
|---|---|---|---|
| `EXECUTION_PROMPT.md` | `/Users/shane/Desktop/Arena_1013_model/research/phase2_r10_cell_steps_20261017/EXECUTION_PROMPT.md` (uncommitted there) | `7b18983ba8b8` | none |
| `src/harness.py` | round 8 `src/harness.py` | `71b4fd9b2791` | none (cache moves to this study by location) |
| `src/common10.py` | round 8 `src/common8.py` | `ad097b05555e` | worktree assertion `Arena_1017_r10_cells`, docstring |
| `src/runner5c.py`, `src/internals.py`, `src/checks5c.py` | round 8 `src/` | `5facb6a5d088`, `d701bf510ebe`, `ca0a3102553d` | `from common8` → `from common10` |
| `src/tsqrt.py`, `src/v3.py`, `src/eventcurves.py`, `src/slicestats.py`, `src/plotstyle.py`, `src/mdtab.py` | round 8 `src/` | `69fc28428281`, `ec2e821c0ef5`, `6b25966b283a`, `1b894e497d7a`, `cb491f98ffb7`, `19da62a71fcd` | none |
| `src/notes10.py` | round 8 `src/notes8.py` | `447c8cfef57a` | renamed |
| `src/residuals10.py` | round 8 `wp2/run_wp2.py::add_residuals` (R_seg rule), `wp5/run_wp5.py::r_anc_b` | — | generalised to any depth column |
| `cache/submitted_package/` (git-ignored) | `git -C /Users/shane/Desktop/Arena_1013_model archive 5cd305c TechArena_Challenge2_Team_Package` | model_template `e3f094e640b2` | none |
| `cache/package_submission_5cd305c.py` (git-ignored) | `git show 5cd305c:research/phase2_v3_20261015/package_submission.py` | `9ce5a0f27d55` | none |

Read in place: round 8 `outputs/table_events.csv`, `outputs/table_anchors.csv`; round 9 `outputs/r9_robust_variants.csv`; events.py and v2.py through the harness.

---

<a id="zh"></a>

# 来源（第 10 轮）

> **语言：** [English](#en) · 中文

基点：本地分支 `exp/phase2-r9-fixes-20261017` 的 `6749c63`（包含第 8、9 轮）。复制的文件、SHA256 与改动见英文表格：harness 原样复制（缓存因此位于本研究）；`common10.py` 只改了 worktree 断言；`runner5c.py`、`internals.py`、`checks5c.py` 只改了导入行；`residuals10.py` 把第 8 轮的 R_seg 和 R_anc_b 规则推广到任意深度列。
