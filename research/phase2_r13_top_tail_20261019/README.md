<a id="en"></a>

# Round 13 — Top-of-charge CV tail drift bound

> English · [中文](#zh)

**Result: O3 "not identifiable"** (envelope 0.412 Ah > 0.30 Ah). SUB is unchanged. The top-tail ε drift is bounded to [0, +0.41] Ah at CK7; the tail models alone give +0.04…+0.12 Ah, and it is exactly 0 if the checkup stops its CV at 5.1 A. Read [FINAL_REPORT.md](FINAL_REPORT.md) first.

## Layout

| Path | Content |
|---|---|
| [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md) | the prompt this round executed |
| [FINAL_REPORT.md](FINAL_REPORT.md) | conclusions, per-WP findings, the SOH table, hand-off |
| `notes/` | [STATUS.md](notes/STATUS.md) (progress) and [DECISIONS.md](notes/DECISIONS.md) (D1–D15, how open points were resolved) |
| `sources/` | copies of round 5B/8/11 files with SHA256 ([SOURCES.md](sources/SOURCES.md)) |
| `wp0/` | SUB reproduction, the CV catalogue of all 41 full charges, the fact sheet |
| `wp1/` | registered protocol, its hashes, the synthetic test output, the outcome table |
| `wp2/` | fits, tails, top-state tables, figures, measurement report |
| `wp3/` | decision, SOH variants, `R13_RESULT.json` for rounds 14/15 |
| `src/` | `wp0_catalogue.py`; registered `tail.py` and `test_tail.py`; `run_wp2.py`, `wp2_fig.py`, `run_wp3.py` |
| `cache/` | git-ignored: SUB run, CV traces |

## Reproduce

From the worktree root, with Python 3.13, pandas 3.0, numpy 2.4, scipy 1.18 and matplotlib 3.11:

```
S=research/phase2_r13_top_tail_20261019; D=TechArena_Challenge2_Team_Package/data
(cd TechArena_Challenge2_Team_Package && python3 -B run_model.py --model train --input data --output-dir ../$S/cache/sub \
  && python3 -B run_model.py --model test --input data --state-dir ../$S/cache/sub --output-dir ../$S/cache/sub --eval-point all)
python3 -B $S/src/wp0_catalogue.py $S $D
python3 -B $S/src/test_tail.py
python3 -B $S/src/run_wp2.py $S $D && python3 -B $S/src/wp2_fig.py $S
python3 -B $S/src/run_wp3.py $S
```

---

<a id="zh"></a>

# 第 13 轮——充电顶部 CV 尾巴漂移的上界

> [English](#en) · 中文

**结果：O3"无法识别"**（包络 0.412 Ah > 0.30 Ah）。SUB 不变。顶部尾巴引起的 ε 漂移在 CK7 处被限定在 [0, +0.41] Ah；仅尾巴模型给出 +0.04…+0.12 Ah；如果检查在 5.1 A 停止 CV，则恰为 0。请先读 [FINAL_REPORT.md](FINAL_REPORT.md)。

## 目录

| 路径 | 内容 |
|---|---|
| [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md) | 本轮执行的 prompt |
| [FINAL_REPORT.md](FINAL_REPORT.md) | 结论、各工作包的发现、SOH 表、交接 |
| `notes/` | [STATUS.md](notes/STATUS.md)（进度）和 [DECISIONS.md](notes/DECISIONS.md)（D1–D15，未决问题如何处理） |
| `sources/` | 第 5B/8/11 轮文件的副本及其 SHA256（[SOURCES.md](sources/SOURCES.md)） |
| `wp0/` | SUB 复现、全部 41 次满充的 CV 目录、事实清单 |
| `wp1/` | 登记的协议、哈希、合成测试输出、各结果含义表 |
| `wp2/` | 拟合、尾巴、顶部状态表、图、测量报告 |
| `wp3/` | 决策、SOH 变体、供第 14/15 轮使用的 `R13_RESULT.json` |
| `src/` | `wp0_catalogue.py`；登记的 `tail.py` 和 `test_tail.py`；`run_wp2.py`、`wp2_fig.py`、`run_wp3.py` |
| `cache/` | git 忽略：SUB 运行结果、CV 曲线 |

## 复现

在工作树根目录下运行（Python 3.13、pandas 3.0、numpy 2.4、scipy 1.18、matplotlib 3.11），命令见英文部分。
