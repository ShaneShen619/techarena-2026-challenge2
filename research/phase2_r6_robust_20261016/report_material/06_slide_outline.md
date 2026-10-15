<a id="en"></a>

# Draft — Slide outline (Challenge 2 part, 11 slides)

> **Language:** English · [中文](#zh)

1. **Task and constraint.** 4 × 102 Ah LFP pack, one label (CK0), seven hidden checkups. Why voltage-threshold methods fail on the LFP plateau.
2. **Two signals the pack gives us for free.** The post-checkup full charge (anchor) and the graphite staging step in the 5-day program. Figure: anchor charges and step depths over time.
3. **The submitted model.** Anchor + phase-matched 45 °C step differences × β + √t for the coverage gap. Formula box.
4. **What else moves the step.** Temperature (+0.18 Ah at 45 °C) and the post-anchor path effect (+0.4–0.56 Ah), and how phase matching cancels both.
5. **Validation without labels.** Causality checks, exposed proxies vs causal hold-outs (pseudo-gaps, cold start), pre-registration. Diagram.
6. **Results.** Proxy MAE 0.123 pp, max 0.228; ExampleModel about 4.3 pp. SOH table CK1–CK7.
7. **Robust to what we do not know.** 18 label hypotheses (Δ, unseen recovery f, ε drift): lowest maximum regret. Heat map (WP1).
8. **Interpretability.** Break-in / calendar / cycle decomposition of the stress law (fig_stress_law_decomposition), with the identifiability caveat.
9. **Open data.** Table of the six sources and what each bounded (ε drift, β, priors).
10. **What did not work, and why.** Electrode model (OCP mismatch), cold-start prior, fusion transfer to CK1/CK2.
11. **Limits and next steps.** ε and recovery are leaderboard questions; the probe plan (WP6).

---

<a id="zh"></a>

# 草稿——演示大纲（Challenge 2 部分，11 页）

> **语言：** [English](#en) · 中文

1. **任务与约束。** 4 × 102 Ah LFP 电池组，只有一个标签（CK0），七个隐藏检查点。为什么在 LFP 平台上用电压阈值的方法会失败。
2. **电池组"免费"给我们的两种信号。** 检查后的满充（锚点），以及 5 天程序中的石墨分阶台阶。图：锚点充电量和台阶深度随时间的变化。
3. **提交的模型。** 锚点 + 同相位 45 °C 台阶差 × β + 覆盖缺口用 √t。公式框。
4. **还有什么会让台阶移动。** 温度（45 °C 下 +0.18 Ah）和锚点后的路径效应（+0.4–0.56 Ah），以及同相位比较如何同时抵消两者。
5. **没有标签时怎么验证。** 因果检查、已曝光的代理与因果留出（伪缺口、冷启动）、预登记。示意图。
6. **结果。** 代理 MAE 0.123 pp，最大 0.228；ExampleModel 约 4.3 pp。CK1–CK7 的 SOH 表。
7. **对未知因素的稳健性。** 18 种标签假设（Δ、未被测到的恢复 f、ε 漂移）：最大后悔值最低。热力图（WP1）。
8. **可解释性。** 应力定律的磨合 / 日历 / 循环分解（fig_stress_law_decomposition），附可辨识性的说明。
9. **开放数据。** 六个来源的表，以及各自约束了什么（ε 漂移、β、先验）。
10. **哪些没成功，为什么。** 电极模型（OCP 失配）、冷启动先验、融合迁移不到 CK1/CK2。
11. **局限与下一步。** ε 和恢复问题只能靠排行榜回答；探测计划（WP6）。
