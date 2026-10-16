<a id="en"></a>

# WP0 — Setup and re-baselining

> **Language:** English · [中文](#zh)

**Result: everything reproduces.** Script [run_wp0.py](run_wp0.py); outputs [outputs/reproduce.json](outputs/reproduce.json).

| Check | Value | Target | Pass |
|---|---|---|---|
| SUB MAE Δ0 / 0.4 / 0.8 | 0.2065 / 0.1227 / 0.1395 | 0.207 / 0.123 / 0.140 | yes |
| SUB MAX Δ0.4 | 0.2277 | 0.228 | yes |
| SUB pseudo / cold start | 0.1476 / 0.1743 | 0.148 / 0.174 | yes |
| SUB predictions vs round 6 WP1 file | max diff 1.4e-14 Ah | identical | yes |
| Round 6 WP1 grid from its predictions | max-regret diff 1.5e-15; SUB 0.0271 | 0.027 | yes |
| 3a start-state table, 3c path offsets | identical to round 6 | identical | yes |

**sqrt_gap inventory** ([sqrt_branch_cases.csv](outputs/sqrt_branch_cases.csv)): the branch fires at real CK2 and in 24 non-real cases: PG1 k 4–7, PG2 k 4–6, PC10 k 3–7, CSE k 3–7, PC5_all/PC10_all CK2 and PC10_all k 3–7. Because the branch uses only anchors and dates, the cut-family cases at the same k are identical (decision D0.1). The causal test therefore rests on **5 distinct one-month extrapolations (k = 3..7)**, plus their near-duplicates under CSE. That is ≥ 4, so WP2's exit rule does not fire.

---

<a id="zh"></a>

# WP0 — 准备与重新确定基线

> **语言：** [English](#en) · 中文

**结果：全部复现。** SUB 的代理 MAE、MAX、伪场景、冷启动与第六轮一致；SUB 的预测与第六轮 WP1 文件逐位一致（差 1.4e-14 Ah）；用第六轮的预测重算网格，SUB 最大后悔值 0.0271；3a、3c 表与第六轮相同。

**sqrt_gap 清点：** 除真实 CK2 外，该分支在 24 个非真实案例上触发。由于分支只用锚点和日期，同一 k 的截断族案例完全相同（决策 D0.1），因此因果检验实际是 **k = 3..7 共 5 个不同的一个月外推**，外加 CSE 下近乎重复的一组。数量 ≥ 4，WP2 的退出规则不触发。
