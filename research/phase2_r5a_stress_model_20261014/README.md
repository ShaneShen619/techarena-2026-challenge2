<a id="en"></a>

# Round 5A — Self-calibrated stress-history ageing model

> **Language:** English · [中文](#zh)

Branch `exp/phase2-r5a-stress-model-20261014`. A model of a different class from the anchor + graphite-step family: it predicts capacity loss from the stress history alone (time, cell temperature, throughput). It uses a physics prior (Challenge 1 cells, Yagci 2025) and is calibrated on the pack's own post-checkup anchors.

**Result:** no model passed every gate, so V2 stays the leading candidate. S_main is strong from CK3 on (ε-free CK2–7 MAE 0.192 pp vs V2 0.216) but fails at CK1, where only the prior is available (−1.13 pp). The 50/50 ensemble with V2 misses G-proxy only at Δ = 0.8. Read [FINAL_REPORT.md](FINAL_REPORT.md).

## Layout

| Path | Content |
|---|---|
| [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md) | execution brief |
| [FINAL_REPORT.md](FINAL_REPORT.md) | final report |
| [notes/](notes/) | STATUS and DECISIONS |
| [src/stress.py](src/stress.py) | stress-history table (observed, checkup, missing segment, extrapolated) |
| [src/smodel.py](src/smodel.py) | pack model S (numpy/pandas only) |
| [stage0_reproduce.py](stage0_reproduce.py), `stage0/` | V2 / M4 reproduction |
| [stage_1/](stage_1/) | stress extraction audit |
| [stage_2/](stage_2/) | prior protocol, Challenge 1 fits, prior.json |
| [stage_3/](stage_3/) | registered protocol, pseudo and real evaluation, gates |
| [stage_4/](stage_4/) | CK2 decomposition |
| [stage_5/](stage_5/) | ageing-law figure, leaderboard-only table |

Reproduction commands are at the end of the final report. Caches go into git-ignored `cache/` directories.

---

<a id="zh"></a>

# 第五轮 A——基于电池组自身锚点标定的应力历史老化模型

> **语言：** [English](#en) · 中文

分支 `exp/phase2-r5a-stress-model-20261014`。这是与"锚点 + 石墨台阶"系列不同类别的模型：只从应力历史（时间、芯温、吞吐）预测容量损失。它用物理先验（Challenge 1 电芯、Yagci 2025），并以电池组自身的检查后锚点标定。

**结果：** 没有模型通过全部门槛，V2 仍是领先候选。S_main 从 CK3 起表现很好（与 ε 无关的 CK2–7 MAE 0.192 pp，V2 0.216），但在只有先验可用的 CK1 失败（−1.13 pp）。与 V2 的 50/50 集成只在 Δ = 0.8 时未通过 G-proxy。请读 [FINAL_REPORT.md](FINAL_REPORT.md)。

## 目录

| 路径 | 内容 |
|---|---|
| [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md) | 执行任务书 |
| [FINAL_REPORT.md](FINAL_REPORT.md) | 最终报告 |
| [notes/](notes/) | STATUS 与 DECISIONS |
| [src/stress.py](src/stress.py) | 应力历史表（观测、检查、缺失段、外推） |
| [src/smodel.py](src/smodel.py) | 电池组模型 S（只用 numpy/pandas） |
| [stage0_reproduce.py](stage0_reproduce.py)、`stage0/` | 复现 V2 / M4 |
| [stage_1/](stage_1/) | 应力提取审计 |
| [stage_2/](stage_2/) | 先验协议、Challenge 1 拟合、prior.json |
| [stage_3/](stage_3/) | 登记协议、伪场景与真实评估、门槛 |
| [stage_4/](stage_4/) | CK2 分解 |
| [stage_5/](stage_5/) | 老化定律图、排行榜专用表 |

复现命令在最终报告末尾。缓存放在被 git 忽略的 `cache/` 目录中。
