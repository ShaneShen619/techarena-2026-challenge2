<a id="en"></a>

# Sources (round 8)

> **Language:** English · [中文](#zh)

Base: `exp/phase2-r7-lit-checks-20261016` at `c9658adf01454ee0da286b1bec5db24c91f5c88d` (branch tip at creation).

| Copied file (this study) | Source | SHA256 of the source | Change |
|---|---|---|---|
| `EXECUTION_PROMPT.md` | `/Users/shane/Desktop/Arena_1013_model/research/phase2_r8_error_table_20261017/EXECUTION_PROMPT.md` (uncommitted there) | `d4b3f527b0cf01b0660c91f7ff1b23b8d963cb90751e03f66ac2aec2f8982dd9` | none |
| `src/harness.py` | `research/phase2_round3_models_20261014/src/harness.py` | `e401c384…f42` | docstring line only; its location moves `CACHE` to this study's `cache/` (D0.1) |
| `src/common8.py` | `research/phase2_r7_lit_checks_20261016/src/common6.py` | `d6d4a7fe…367` | worktree assertion `Arena_1017_r8_err`; imports the harness copy |
| `src/runner5c.py` | `research/phase2_r7_lit_checks_20261016/src/runner5c.py` | `c16e10d6…26d` | `from common6` → `from common8` |
| `src/audits6.py` | `research/phase2_r7_lit_checks_20261016/src/audits6.py` | `95fa0051…37e` | same import change |
| `src/checks5c.py` | `research/phase2_r7_lit_checks_20261016/src/checks5c.py` | `181819ff…26d` | same import change |
| `src/tsqrt.py` | `research/phase2_r7_lit_checks_20261016/src/tsqrt.py` (T_main design) | `69fc2842…7a3` | none |
| `src/v3.py` | `research/phase2_r7_lit_checks_20261016/sources/v3/v3.py` | `ec2e821c…ead` | none |
| `cache/submitted_package/` (git-ignored) | `git -C /Users/shane/Desktop/Arena_1013_model archive 5cd305c TechArena_Challenge2_Team_Package` | `my_model/model_template.py`: `e3f094e640b291d651f4c022ab4898a966ddbc1f08ab798cc9bf97c9ded90496` | none (read-only) |
| `cache/package_submission_5cd305c.py` (git-ignored) | `git show 5cd305c:research/phase2_v3_20261015/package_submission.py` (source of `EXPECTED_SOH`) | `9ce5a0f27d557cfa3304fbeb19d1097f216f607ca4b56c5933c08326e5bd4d79` | none |

The submitted `model_template.py` differs from the round 7 WP2 candidate class only in its module docstring.

Read in place (not copied), this worktree:
- `research/phase2_anchor_step_20261013/src/events.py`, `research/phase2_v2_phase_matched_20261013/src/v2.py` (imported through the harness);
- `research/phase2_r6_robust_20261016/sources/rebound_diagnosis/outputs/events_merged.csv` (`a9ddd411…4ba`);
- `research/phase2_r7_lit_checks_20261016/wp0/outputs/wp0_3a_start_state.csv` (`442ac1b6…188`), `wp0_3c_path_offsets.csv` (`c53f2186…01d`), `wp0_branch_by_case.csv` (`30f421d8…f34`);
- `research/phase2_r7_lit_checks_20261016/wp1/outputs/anchor_state_table.csv` (`f14ba7f4…bd`).

---

<a id="zh"></a>

# 来源（第 8 轮）

> **语言：** [English](#en) · 中文

基点：`exp/phase2-r7-lit-checks-20261016` 的 `c9658adf01454ee0da286b1bec5db24c91f5c88d`（创建时的分支末端）。

复制文件、来源、SHA256 和改动见英文表格。要点：
- `src/harness.py` 只改了文档字符串；放在本研究目录下后缓存写入本研究的 `cache/`（D0.1）。
- `src/common8.py` 只改了 worktree 断言并导入 harness 副本；`runner5c.py`、`audits6.py`、`checks5c.py` 只改了导入行；`tsqrt.py`、`v3.py` 未改。
- 提交包（`5cd305c`）解压到 `cache/submitted_package/`（git 忽略，只读）；`EXPECTED_SOH` 来自同一提交的 `package_submission.py`。
- 提交的 `model_template.py` 与第 7 轮 WP2 候选类只差模块文档字符串。

就地读取（未复制）的文件见英文列表。
