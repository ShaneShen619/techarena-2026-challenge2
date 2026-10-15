<a id="en"></a>

# Round 2 diagnosis (from pseudo / cold-start results and physics only)

> **Language:** English · [中文](#zh)

Source: [../stage_1/outputs/S1_pseudo_cold_predictions.csv](../stage_1/outputs/S1_pseudo_cold_predictions.csv) (PG1, PG2, PC5, PC10, CS, CSE; Δ = 0.4, main step). No real-scenario number is used here.

1. **With anchors available (pseudo scenarios), the step terms over-predict the month's loss.**
   - D1/D3 errors are negative in every pseudo case (−0.02 to −0.66 pp). Their predicted month loss is 1.0–1.16 Ah, against 0.67–0.78 Ah for D2 without steps.
   - Two causes. First, about 10 step pairs per cutoff at σ_s = 0.05 Ah outweigh the anchor pairs (σ = 0.20 Ah) by roughly 16 : 1 per term. Second, the fixed β ≈ 1.30 (V2's A4 ratio, a 25 °C anchor-to-anchor charge-side quantity) is applied to 45 °C in-segment step declines.
   - Doubling σ_s reduces the bias (D1 pseudo MAE 0.290 → 0.169), which confirms that weighting is part of the problem.
2. **In cold-start scenarios the step terms help.**
   - There, β falls back to 1 (no A4 anchors after the filter) and only about three step pairs exist.
   - D1/D3 cold-start MAE is 0.150–0.187, against 0.350 for D2 and 0.287 for 5A's S_main, both of which depend on the prior alone.
3. **D2 (two-term law) without steps is the best on pseudo scenarios (0.118) and the worst on cold start (0.350).** Its prior over-predicts loss when no in-month information is used (CS errors −0.22 to −0.78 pp).

**Conclusion for round 2.** Use step information only where anchors give none: the latest, not-yet-anchored month (at CK1 this is month 0). Use one endpoint pair per such month, with σ_month = 0.10 Ah and β = 1. Leave months covered by anchor pairs to the anchors.

---

<a id="zh"></a>

# 第二轮诊断（仅依据伪场景 / 冷启动结果和物理）

> **语言：** [English](#en) · 中文

来源：[../stage_1/outputs/S1_pseudo_cold_predictions.csv](../stage_1/outputs/S1_pseudo_cold_predictions.csv)（PG1、PG2、PC5、PC10、CS、CSE；Δ = 0.4，主台阶方法）。这里没有使用任何真实场景的数字。

1. **有锚点可用时（伪场景），台阶项会把当月损失算多。**
   - D1/D3 在每个伪场景情形中误差都为负（−0.02 至 −0.66 pp）。它们预测的月损失为 1.0–1.16 Ah，而不带台阶的 D2 为 0.67–0.78 Ah。
   - 原因有两个。其一，每个截断约有 10 对台阶，σ_s = 0.05 Ah，单项权重约为锚点对（σ = 0.20 Ah）的 16 倍。其二，把固定的 β ≈ 1.30（V2 的 A4 比值，是 25 °C 锚点之间的充电侧量）用在了 45 °C 段内的台阶下降上。
   - 把 σ_s 加倍就能减小偏差（D1 伪场景 MAE 0.290 → 0.169），说明权重是问题的一部分。
2. **在冷启动场景中，台阶项有帮助。**
   - 这时 β 回退为 1（过滤后没有 A4 锚点），台阶对也只有约三对。
   - D1/D3 的冷启动 MAE 为 0.150–0.187；只靠先验的 D2 为 0.350，5A 的 S_main 为 0.287。
3. **不带台阶的 D2（两项定律）在伪场景上最好（0.118），在冷启动上最差（0.350）。** 不用月内信息时，它的先验会多算损失（CS 误差 −0.22 至 −0.78 pp）。

**第二轮的结论。** 台阶信息只用在锚点覆盖不到的地方：最新的、还没有锚点的那个月（CK1 时就是第 0 月）。每个这样的月只用首尾一对台阶，σ_month = 0.10 Ah，β = 1。已被锚点对覆盖的月份交给锚点。
