<a id="en"></a>

# Sources (round 7)

> **Language:** English · [中文](#zh)

| Copied file (this study) | Source | SHA256 |
|---|---|---|
| `EXECUTION_PROMPT.md` | `/Users/shane/Desktop/Arena_1013_model/research/phase2_literature_refresh_20261016/R7_EXECUTION_PROMPT.md` (uncommitted there) | `299553523a6dc09414c4a28dba7b7069b2fb54542f161fd6f45126ad4041c9e0` |
| `src/checks5c.py`, `preds5c.py`, `runner5c.py`, `smodel.py`, `smodel5c.py`, `stress.py` | `research/phase2_r6_robust_20261016/src/` at `e144086` (unchanged) | see `shasum -a 256 src/*.py` |
| `src/common6.py` | same; only the worktree assertion changed (`Arena_1016_r6_robust` → `Arena_1016_r7_lit`) | `d6d4a7fe…` |
| `src/grid7.py` | functions `target`, `scores`, `decision`, `prior_weights` and the model set of `research/phase2_r6_robust_20261016/wp1/run_wp1.py` at `e144086`, extended for extra hypothesis families | `a1032e9c…` |
| `src/audits6.py` | functions `rest_voltages`, `audit_3a`, `audit_3c` of `research/phase2_r6_robust_20261016/wp3/audit_wp3.py` at `e144086` (return DataFrames instead of files) | `95fa0051…` |
| `sources/v3/v3.py` | `research/phase2_r6_robust_20261016/sources/v3/v3.py` at `e144086` (itself from submission commit `21a7a55`) | `ec2e821c…` |
| `sources/lit_refresh/03_新文献综述.md` | literature refresh folder (uncommitted) | `e5a9312a…` |
| `sources/lit_refresh/04_全文精读_9篇.md` | same | `9045456e…` |
| `sources/lit_refresh/papers_README.md` | same, `papers/README.md` (PDFs not copied: copyright) | `13e06607…` |
| `sources/lit_refresh/tum_calendar_check/` (`check_tum_calendar.py`, `RESULTS.md`, `outputs/*`) | same | `77b7764a…` (script), `ac8309f7…` (RESULTS) |
| `cache/submitted_package/` (git-ignored) | `git -C /Users/shane/Desktop/Arena_1013_model archive 21a7a55 TechArena_Challenge2_Team_Package` | — |

Read in place (not copied):
- round 6 outputs in this worktree (`research/phase2_r6_robust_20261016/wp1/outputs`, `wp3/outputs`, `wp4/outputs`);
- Yagci raw files in `/Users/shane/Desktop/Arena_1016_r6_robust/research/phase2_r6_robust_20261016/cache/downloads/yagci/`;
- TUM files `/Users/shane/Desktop/kxh42bfgtj-1/*.xlsx`: DischargeCapacity `c684bdb2…`, DifferentialVoltageAnalysis `cc47d2d1…`, R_DC `7a27edb6…`, EIS `c7656fbf…`.

---

<a id="zh"></a>

# 来源（第七轮）

> **语言：** [English](#en) · 中文

上表列出了每个复制进本研究的文件、来源和 SHA256。`common6.py` 只改了 worktree 断言；`grid7.py`、`audits6.py` 是第六轮 WP1/WP3 函数的副本（前者可加入额外假设族，后者返回 DataFrame 而不写文件）。文献 PDF 因版权未复制。原地读取（不复制）的有：本 worktree 中第六轮的输出、第六轮缓存中的 Yagci 原始文件、桌面上的 TUM 数据。
