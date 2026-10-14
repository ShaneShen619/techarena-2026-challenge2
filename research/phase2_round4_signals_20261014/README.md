<a id="en"></a>

# phase2_round4_signals_20261014

> **Language:** English · [中文](#zh)

Round 4 tested whether more or cleaner graphite-step signals can improve V2 (directions 1–7). Conclusions are in [FINAL_REPORT.md](FINAL_REPORT.md), and the brief is [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md). Progress and decisions are in `notes/STATUS.md` and `notes/DECISIONS.md`.

| Path | Contents |
|---|---|
| `src/common4.py` | path setup; imports round 3's harness, `events.py` and `v2.py` from this worktree |
| `src/endfit.py` | stage 1 month-end regression |
| `src/dyncross.py` | stage 2 dynamic step crossings and coulomb closure |
| `src/leads.py` | stage 7 SS_fixed and start-corrected registration β |
| `stage0_reproduce.py`, `stage0/` | exact V2/M4 reproduction |
| `stage_N/` | per stage: protocol + SHA256, run or audit script, `outputs/`, bilingual `REPORT.md` |
| `cache/` | git-ignored |

**Environment.** Python 3.13 (numpy, pandas). Run scripts with `python3 -B` from this directory; the commands are in the final report.

---

<a id="zh"></a>

# phase2_round4_signals_20261014

> **语言：** [English](#en) · 中文

第四轮检验更多、更干净的石墨台阶信号能否改进 V2（方向 1–7）。结论见 [FINAL_REPORT.md](FINAL_REPORT.md)，任务书见 [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md)，进度与决策记录在 `notes/STATUS.md` 和 `notes/DECISIONS.md`。

| 路径 | 内容 |
|---|---|
| `src/common4.py` | 路径设置；从本 worktree 导入第三轮的评估框架、`events.py` 和 `v2.py` |
| `src/endfit.py` | 阶段 1：月末回归 |
| `src/dyncross.py` | 阶段 2：动态台阶穿越与库仑闭合 |
| `src/leads.py` | 阶段 7：SS_fixed 与起点修正的配准 β |
| `stage0_reproduce.py`、`stage0/` | 精确复现 V2/M4 |
| `stage_N/` | 每个阶段：协议 + SHA256、运行或审计脚本、`outputs/`、中英双语 `REPORT.md` |
| `cache/` | git 忽略 |

**环境。** Python 3.13（numpy、pandas）。在本目录用 `python3 -B` 运行脚本，命令见最终报告。
