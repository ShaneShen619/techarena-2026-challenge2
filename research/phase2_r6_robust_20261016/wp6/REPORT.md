<a id="en"></a>

# WP6 — Synthesis and leaderboard probe plan

> **Language:** English · [中文](#zh)

- **Protocol:** [protocol.json](protocol.json), committed `3c76271` before any WP6 computation. Code: [run_wp6.py](run_wp6.py).
- **Score:** "s" is the WP1 normalised score (ExampleModel = 1), on the real grid, in the submitted configuration. Δs < 0 means the probe beats SUB under that hypothesis.

## Decision table

| Option | Evidence class | Verdict |
|---|---|---|
| **Keep SUB (V2 + √t)** | registered robust choice on the 18-hypothesis grid (WP1: lowest max regret, 0.027); causal checks pass; CK2 √t branch exposed | **keep as the submission** |
| Switch to the WP1 robust choice | WP1's robust choice is SUB itself | — |
| Switch to a WP2 fusion | causal tests better (pseudo 0.119 vs 0.148; cold start 0.141 vs 0.174), but no design passes the gates; CK1/CK2 cannot be validated causally | not supported |
| Switch to a WP4 open-data variant | prior3 = prior2 (Yagci data not obtained); identical to WP2 | not supported |
| Truth-oriented corrections (WP3) | leaderboard-only; ε drift is the best hedge on the grid | **probe, do not adopt blind** |

## Probe plan (at most three submissions; leaderboard evaluated every two weeks)

Expected Δs vs SUB on the WP1 grid ([summary](outputs/wp6_probe_summary.csv), [per hypothesis](outputs/wp6_delta_s_vs_SUB_by_h.csv)):

| Order | Probe | What it discriminates | E[Δs] diagnosis prior | E[Δs] uniform | Hypotheses where it wins | Worst loss | Best gain |
|---|---|---|---|---|---|---|---|
| 1 | **P_drift**: SUB + ε drift (d = −0.031) | is the truth below the anchor-based estimate (ε drift, unseen recovery, small Δ)? | −0.0081 | −0.0163 | 14 / 18 | +0.044 | −0.034 |
| 2 | **P_stress_early**: F1_S_B fusion (exposed-CK1) | early-campaign handling, stress law vs SUB at CK1–CK3 | −0.0035 | −0.0039 | 13 / 18 | +0.013 | −0.013 |
| 3 | **P_start**: SUB + start-state correction (anchor 1 reference) | do anchor start states bias the anchors? | +0.0266 | +0.0270 | 0 / 18 (the grid has no start-state axis) | +0.038 | +0.012 |

Report-only: P_drift_mild (d = −0.020): E[Δs] −0.0062, worst +0.028. P_stress_noexp (F1_S_A): E[Δs] +0.0002, worst +0.038.

**Probe SOH (%)** ([JSON](outputs/wp6_probe_plan.json)):

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| SUB | 95.992 | 94.451 | 93.541 | 92.811 | 92.081 | 91.331 | 90.821 |
| P_drift | 95.916 | 94.327 | 93.389 | 92.637 | 91.884 | 91.111 | 90.585 |
| P_stress_early | 95.928 | 94.350 | 93.395 | 92.728 | 91.980 | 91.302 | 90.917 |
| P_start | 95.992 | 94.451 | 93.541 | 92.179 | 92.301 | 91.865 | 91.159 |

## How to read each probe

The leaderboard returns one normalised score. Compare it with SUB's score on the same board.

1. **P_drift** lowers every checkup by 0.08–0.24 pp, growing with fade.
   - Better than SUB → the hidden C/20 sits below our anchor mapping late in the campaign (ε drift, unseen post-checkup recovery or a smaller Δ). Keep the drift correction.
   - Worse → the truth sits at or above the anchors (larger Δ, no drift). Revert to SUB.
   - This is the most informative single question and the probe with the best expected value.
2. **P_stress_early** changes mainly CK1–CK3 (−0.06 to −0.15 pp) and CK4–CK5 (−0.08 to −0.10 pp), and raises CK7 by 0.10 pp.
   - Better → the stress law's early-campaign view is closer to the truth.
   - Because it overlaps with P_drift in direction, run it after P_drift and compare against the better of the two.
3. **P_start** moves CK4 down by 0.6 pp and CK5–CK7 up by 0.2–0.5 pp.
   - It is the only probe whose signature is not monotone, so it isolates the start-state hypothesis, but it is expected to lose on every grid hypothesis.
   - Use it only if probe slots remain.

**Order and stopping.**

- Submit P_drift first.
- If it wins, try P_stress_early with the drift correction applied on top as the second probe (registered as a follow-up, not computed here); otherwise try P_stress_early alone.
- The last submission before the deadline counts, so always end on the best observed option. SUB is the default.

---

<a id="zh"></a>

# WP6——综合与排行榜探测计划

> **语言：** [English](#en) · 中文

- **协议：** [protocol.json](protocol.json)，在 WP6 的任何计算之前于 `3c76271` 提交。代码：[run_wp6.py](run_wp6.py)。
- **得分：** "s" 是 WP1 的归一化得分（ExampleModel = 1），在真实网格上、按提交配置计算。Δs < 0 表示在该假设下探测候选优于 SUB。

## 决策表

| 选项 | 证据类别 | 结论 |
|---|---|---|
| **保留 SUB（V2 + √t）** | 18 假设网格上登记的稳健选择（WP1：最大后悔值最低，0.027）；因果检查通过；CK2 的 √t 分支已曝光 | **保留作为提交** |
| 换成 WP1 的稳健选择 | WP1 的稳健选择就是 SUB 本身 | — |
| 换成 WP2 的融合 | 因果检验更好（伪场景 0.119 对 0.148；冷启动 0.141 对 0.174），但没有设计通过门槛；CK1/CK2 无法做因果验证 | 不支持 |
| 换成 WP4 的开放数据变体 | prior3 = prior2（没拿到 Yagci 数据）；与 WP2 相同 | 不支持 |
| 真值导向修正（WP3） | 只用于排行榜；ε 漂移是网格上最好的对冲 | **用于探测，不要直接采用** |

## 探测计划（最多三次提交；排行榜每两周评估一次）

在 WP1 网格上相对 SUB 的预期 Δs（[汇总](outputs/wp6_probe_summary.csv)、[逐假设](outputs/wp6_delta_s_vs_SUB_by_h.csv)）：

| 顺序 | 探测 | 区分什么 | E[Δs] 诊断先验 | E[Δs] 均匀 | 胜出的假设数 | 最坏损失 | 最好收益 |
|---|---|---|---|---|---|---|---|
| 1 | **P_drift**：SUB + ε 漂移（d = −0.031） | 真值是否低于基于锚点的估计（ε 漂移、恢复没被测到、Δ 较小）？ | −0.0081 | −0.0163 | 14 / 18 | +0.044 | −0.034 |
| 2 | **P_stress_early**：F1_S_B 融合（已曝光 CK1） | 试验前期的处理方式，CK1–CK3 上应力定律对 SUB | −0.0035 | −0.0039 | 13 / 18 | +0.013 | −0.013 |
| 3 | **P_start**：SUB + 起点修正（以锚点 1 为参照） | 锚点的起点状态是否使锚点有偏？ | +0.0266 | +0.0270 | 0 / 18（网格里没有起点状态这条轴） | +0.038 | +0.012 |

只作报告：P_drift_mild（d = −0.020）：E[Δs] −0.0062，最坏 +0.028。P_stress_noexp（F1_S_A）：E[Δs] +0.0002，最坏 +0.038。

**各探测的 SOH（%）**（[JSON](outputs/wp6_probe_plan.json)）：

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| SUB | 95.992 | 94.451 | 93.541 | 92.811 | 92.081 | 91.331 | 90.821 |
| P_drift | 95.916 | 94.327 | 93.389 | 92.637 | 91.884 | 91.111 | 90.585 |
| P_stress_early | 95.928 | 94.350 | 93.395 | 92.728 | 91.980 | 91.302 | 90.917 |
| P_start | 95.992 | 94.451 | 93.541 | 92.179 | 92.301 | 91.865 | 91.159 |

## 怎么解读每个探测

排行榜只返回一个归一化得分。拿它和同一个榜上 SUB 的得分比较。

1. **P_drift** 把每个检查点都下调 0.08–0.24 pp，越往后（衰减越多）下调越多。
   - 比 SUB 好 → 说明试验后期隐藏的 C/20 低于我们的锚点映射（ε 漂移、检查后恢复没被测到，或 Δ 较小）。保留漂移修正。
   - 比 SUB 差 → 说明真值等于或高于锚点（Δ 较大、没有漂移）。退回 SUB。
   - 这是信息量最大的单个问题，也是预期价值最高的探测。
2. **P_stress_early** 主要改变 CK1–CK3（−0.06 至 −0.15 pp）和 CK4–CK5（−0.08 至 −0.10 pp），并把 CK7 上调 0.10 pp。
   - 比 SUB 好 → 说明应力定律对试验前期的判断更接近真值。
   - 它与 P_drift 的方向有重叠，所以放在 P_drift 之后跑，并与两者中较好的那个比较。
3. **P_start** 把 CK4 下调 0.6 pp，把 CK5–CK7 上调 0.2–0.5 pp。
   - 它是唯一一个改动不单调的探测，所以能单独检验起点状态假设；但预计它在网格的每个假设下都会落败。
   - 只有在还剩探测机会时才用。

**顺序与停止。**

- 先提交 P_drift。
- 如果它胜出，第二个探测就用"在漂移修正之上再叠加 P_stress_early"（作为后续登记，这里没有计算）；否则单独试 P_stress_early。
- 截止前的最后一次提交才算数，所以最后一定要落在观察到的最佳选项上。SUB 是默认选项。
