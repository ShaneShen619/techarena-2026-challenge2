<a id="en"></a>

# Round 14 — Path drift on our own pack

> English · [中文](#zh)

**Outcome: O3 "not identifiable"; SUB unchanged.** The registered path drift is E = −0.97 Ah at CK7, with a LOO range 0.59 Ah wide (limit 0.30 Ah). It is explained by a month-specific Ah-chain loss rate λ, not by the pack's tops. With a same-cycle λ (exploratory), there is no trend. Read [`FINAL_REPORT.md`](FINAL_REPORT.md) first; the hand-off for round 15 is [`wp3/R14_RESULT.json`](wp3/R14_RESULT.json).

## Layout

| Path | Content |
|---|---|
| `EXECUTION_PROMPT.md` | the prompt this round executed (copy of the original) |
| `notes/STATUS.md`, `notes/DECISIONS.md` | progress and every open decision (D1–D22) |
| `sources/` | read-only copies from rounds 8, 11, 12, 13 and the base branch, with SHA256 (`SOURCES.md`) |
| `src/` | registered code (`data14.py`, `ahchain.py`, `signals.py`, `stats14.py`, `decide.py`, `test_synthetic.py`) and drivers (`wp0_*`, `wp1_register.py`, `wp2_*`, `wp3_decide.py`) |
| `wp0/` | SUB per checkup, anchor blocks, fact sheet |
| `wp1/` | `protocol.json` + `protocol.sha256`, synthetic test, outcome table |
| `wp2/` | pairs, λ, Term3, P2, P3, statistics, figures, exploratory λ analysis |
| `wp3/` | decision, SOH variants (leaderboard-only), `R14_RESULT.json`, per-anchor table |
| `cache/` | git-ignored: segment pickle, CLI outputs |

## Reproduce

Run from `src/` with Python 3 (numpy, pandas, matplotlib). Each step reads the outputs of the one before. `wp0_sources.py` re-fetches origin and rewrites `sources/SOURCES.md` from scratch, so it is left out here (the committed copies are used). Do not re-run `wp1_register.py`: it rewrites the registration.

```
python3 -B wp0_sub.py && python3 -B wp0_blocks.py && python3 -B wp0_facts.py
python3 -B test_synthetic.py                                   # 19/19
(cd ../wp1 && shasum -a 256 -c protocol.sha256)                # protocol.json: OK
python3 -B wp2_sources.py && python3 -B wp2_measure.py && python3 -B wp2_explore.py && python3 -B wp2_figures.py
python3 -B wp3_decide.py
```

---

<a id="zh"></a>

# 第 14 轮 — 本电池组上的路径漂移

> [English](#en) · 中文

**结果：O3"无法识别"；SUB 不变。** 登记的路径漂移为 CK7 处 E = −0.97 Ah，LOO 范围宽 0.59 Ah（上限 0.30 Ah）。它可以用电量链中按月变化的损耗率 λ 解释，而不是电池组顶部的变化。改用同周期 λ（探索性）后没有趋势。请先读 [`FINAL_REPORT.md`](FINAL_REPORT.md)；交给第 15 轮的是 [`wp3/R14_RESULT.json`](wp3/R14_RESULT.json)。

## 目录结构

| 路径 | 内容 |
|---|---|
| `EXECUTION_PROMPT.md` | 本轮执行的 prompt（原文副本） |
| `notes/STATUS.md`、`notes/DECISIONS.md` | 进度以及每一个未决问题的决定（D1–D22） |
| `sources/` | 第 8、11、12、13 轮及基点分支的只读副本，附 SHA256（`SOURCES.md`） |
| `src/` | 登记的代码（`data14.py`、`ahchain.py`、`signals.py`、`stats14.py`、`decide.py`、`test_synthetic.py`）和驱动脚本（`wp0_*`、`wp1_register.py`、`wp2_*`、`wp3_decide.py`） |
| `wp0/` | 各检查点 SUB、锚点块、事实清单 |
| `wp1/` | `protocol.json` + `protocol.sha256`、合成测试、结果含义表 |
| `wp2/` | 配对、λ、Term3、P2、P3、统计、图、探索性 λ 分析 |
| `wp3/` | 决策、SOH 变体（只用于排行榜）、`R14_RESULT.json`、逐锚点表 |
| `cache/` | git 忽略：分段数据缓存、CLI 输出 |

## 复现

在 `src/` 下用 Python 3（numpy、pandas、matplotlib）运行。每一步读取上一步的输出。`wp0_sources.py` 会重新从 origin 获取并从头改写 `sources/SOURCES.md`，所以这里不运行它（使用已提交的副本）。不要重新运行 `wp1_register.py`：它会改写登记。

```
python3 -B wp0_sub.py && python3 -B wp0_blocks.py && python3 -B wp0_facts.py
python3 -B test_synthetic.py                                   # 19/19
(cd ../wp1 && shasum -a 256 -c protocol.sha256)                # protocol.json: OK
python3 -B wp2_sources.py && python3 -B wp2_measure.py && python3 -B wp2_explore.py && python3 -B wp2_figures.py
python3 -B wp3_decide.py
```
