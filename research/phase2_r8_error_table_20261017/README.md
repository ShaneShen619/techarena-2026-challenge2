<a id="en"></a>

# Round 8 — error-analysis long tables

> **Language:** English · [中文](#zh)

Builds one consistent set of long tables for the submitted model SUB = T_main (`5cd305c`), with cases, events, anchors and daily cycles, and slices their residuals under a registered protocol. No candidate is built and nothing is wired.

**Results:** [FINAL_REPORT.md](FINAL_REPORT.md).
- The step depth moves 0.745 Ah per Ah of fade, so β = 1 (fallback) and β shrunk to ~1 under-predict the loss. This explains most of CK1, CK3 and CK4.
- Persistent per-cell step offsets with a growing spread explain most of CK6.
- H1, H3, H7, H9 and H10 are null.

| Path | Content |
|---|---|
| [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md) | the execution prompt (English governs) |
| [notes/](notes/) | STATUS, DECISIONS (D0.1–D5.4) |
| [sources/SOURCES.md](sources/SOURCES.md) | copied code with SHA256 |
| [src/](src/) | harness/runner/T_main copies, `internals.py` (instrumented replay), `eventcurves.py`, `slicestats.py`, `plotstyle.py` |
| [outputs/](outputs/) | `table_cases.csv`, `table_cases_wide.csv`, `table_events.csv`, `table_anchors.csv`, `table_cycles.csv` |
| [DATA_DICTIONARY.md](DATA_DICTIONARY.md) | every column of every table |
| [wp0/](wp0/REPORT.md) … [wp5/](wp5/REPORT.md) | script, outputs and report per work package; WP5 also has protocol, figures and dossier |
| [wp6/](wp6/) | error budget and dictionary generator |
| `cache/` | git-ignored: archived submission package, pickled cut data |

## Rebuild (one command per WP, from this directory)

```bash
cd /Users/shane/Desktop/Arena_1017_r8_err/research/phase2_r8_error_table_20261017
mkdir -p cache/submitted_package && git -C /Users/shane/Desktop/Arena_1013_model archive 5cd305c TechArena_Challenge2_Team_Package | tar -x -C cache/submitted_package && git -C /Users/shane/Desktop/Arena_1013_model show 5cd305c:research/phase2_v3_20261015/package_submission.py > cache/package_submission_5cd305c.py
python3 -B wp0/run_wp0.py                                   # WP0: re-baseline, branch inventory
python3 -B wp1/run_wp1.py                                   # WP1: outputs/table_cases*.csv (needs WP0 outputs)
python3 -B wp2/run_wp2.py                                   # WP2: outputs/table_events.csv (needs WP1 for use flags)
python3 -B wp3/run_wp3.py && python3 -B wp3/plot_wp3.py     # WP3: outputs/table_anchors.csv
python3 -B wp4/run_wp4.py                                   # WP4: outputs/table_cycles.csv (needs WP2)
python3 -B wp5/run_wp5.py && python3 -B wp5/plot_wp5.py     # WP5: slices, figures, dossier (protocol already registered; make_protocol.py only re-registers)
python3 -B wp6/run_wp6.py && python3 -B wp6/make_dictionary.py   # WP6: error budget, DATA_DICTIONARY.md
```

Every CSV/JSON output is byte-identical on rerun. Environment: Python 3.13.0, numpy 2.4.2, pandas 3.0.0, scipy 1.18.0, matplotlib 3.11.1.

---

<a id="zh"></a>

# 第 8 轮——误差分析长表

> **语言：** [English](#en) · 中文

为提交模型 SUB = T_main（`5cd305c`）建立一套口径一致的长表（案例、事件、锚点、日循环），并按登记协议切分残差。没有构建候选模型，也没有接入任何改动。

**结果：** 见 [FINAL_REPORT.md](FINAL_REPORT.md)。
- 台阶深度随衰减每 Ah 只移动 0.745 Ah，所以 β = 1（fallback）以及收缩到约 1 的 β 都会低估损失；这解释了 CK1、CK3 和 CK4 的大部分误差。
- 持续存在且离散不断增大的单体台阶偏移解释了 CK6 的大部分误差。
- H1、H3、H7、H9、H10 为零结果。

目录说明见英文表格。重建命令（每个 WP 一条）见英文部分的代码块：依次运行 wp0 → wp6 的脚本。所有 CSV/JSON 输出重跑后逐字节相同。
