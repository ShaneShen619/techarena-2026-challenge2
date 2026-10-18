<a id="en"></a>

# WP5 — Transfer, bounds and decision

> English · [中文](#zh)

- **Protocol:** `wp1/protocol.json` (`d183743`) and [protocol.json](protocol.json) (`d1af048`).
- **Script:** `src/wp5_decide.py`.
- **Outputs:** [decision.json](decision.json), [SOH_variants.csv](SOH_variants.csv), [R12_HANDOFF.json](R12_HANDOFF.json).

## Conclusions first

1. **Registered outcome: O3, "inconclusive".** The main interval is **d ∈ [−0.036, +0.052] Ah/Ah**, which is −0.29 to +0.42 pp at CK7 (fade 8.2 Ah).
   - The T_path transfer factor stays in [0, 1], because WP4 met neither factor condition.
   - The interval is the min/max over f ∈ {0, 1} and over the pooling variants: the all-dataset median and the three leave-one-dataset-out medians.
2. **The width comes from Yagci's noise, not from evidence of a large drift.**

| Pool | d_CE | d_path | d (f = 0) | d (f = 1) |
|---|---|---|---|---|
| all three (median) | −0.0008 | −0.0057 | −0.0008 | −0.0065 |
| drop LIC | +0.031 | +0.015 | +0.031 | +0.046 |
| drop Yagci35 | −0.019 | −0.017 | −0.019 | −0.036 |
| drop Yagci50 | +0.049 | +0.003 | +0.049 | +0.052 |

   - The all-median interval alone, [−0.0065, −0.0008], would fall inside O1's ±0.012. The registered rule includes the leave-one-out medians, which are means of two values and swing with Yagci's checkup-0 (formation) points.
   - Every registered sensitivity also gives O3 on the main interval and O1 on the all-median interval:

| Sensitivity | Main interval | All-median interval |
|---|---|---|
| Yagci without checkup 0 | [−0.022, +0.003] | [−0.008, −0.003] |
| LIC without flagged points | [−0.038, +0.051] | [−0.007, −0.001] |
| both | [−0.023, +0.003] | [−0.008, −0.003] |

3. **Dominant term: T_path.** It is 87 % of the pooled slope, and 97 % in LIC, the only dataset that resolves the terms. Without Yagci's checkup 0 the pooled share becomes "mixed". In LIC, the step model does not beat the drift model by the registered margin, so the step-type component is excluded from d. Step sizes from model (c): T_path −0.42 Ah, ε_total −0.25 Ah.
4. **The cleanest single source says something different from the pooled rule.**
   - LIC is a 280 Ah LFP cell with a near-identical CV cutoff and checkups that include a reference charge. Its d = −0.030 comes almost entirely from the top state of the 1C charge.
   - WP4 shows that our anchor's top state does not move: fixed 5.10 A cutoff, flat relaxed voltage.
   - That points to f near 0 and d near d_CE ≈ 0. **This is a reading, not a registered result.** Round 12's top-of-charge model is meant to test it.
5. **Leaderboard probes: no change.** Keep round 7's order: P_stress_early → P_start → P_drift.
6. **SOH variants (leaderboard only, SOH %):**

| Model | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| SUB | 95.984 | 94.507 | 93.600 | 92.821 | 92.015 | 91.426 | 90.765 |
| SUB + drift −0.0363 (d_lo) | 95.895 | 94.364 | 93.424 | 92.617 | 91.782 | 91.171 | 90.486 |
| SUB + drift −0.031 | 95.908 | 94.385 | 93.450 | 92.647 | 91.816 | 91.209 | 90.527 |
| SUB + drift +0.0522 (d_hi) | 96.112 | 94.712 | 93.853 | 93.114 | 92.350 | 91.792 | 91.166 |

7. **Hand-off:** [R12_HANDOFF.json](R12_HANDOFF.json) lists the dominant term, the pack drivers, the proposed top-of-charge model, the unassessed terms, the flagged anchors and the constraints carried over from round 5B.
   - Unassessed terms: cell imbalance under pack-voltage limits, the 25 °C offset Δ, the CE of this pack, the bottom state, and the checkup charge protocol.

---

<a id="zh"></a>

# WP5 — 迁移、区间与决策

> [English](#en) · 中文

## 结论先读

1. **登记结果：O3"无定论"。** 主区间为 **d ∈ [−0.036, +0.052] Ah/Ah**，换算到 CK7（衰减 8.2 Ah）为 −0.29 到 +0.42 pp。WP4 两个系数条件都不满足，所以 T_path 的迁移系数保持在 [0, 1]。区间是在 f ∈ {0, 1} 以及各合并版本（全数据集中位数、三个逐一剔除数据集的中位数）上取最小值和最大值。
2. **区间宽是 Yagci 的噪声造成的，不是有证据表明漂移很大。**
   - 全数据集中位数：d_CE −0.0008，d_path −0.0057，区间 [−0.0065, −0.0008]。单看这个会落在 O1 的 ±0.012 以内。
   - 登记规则还包括逐一剔除数据集的中位数。它们是两个值的平均，会随 Yagci 第 0 次检查（化成测试）的点大幅摆动：剔除 LIC 为 +0.031 到 +0.046，剔除 Yagci35 为 −0.019 到 −0.036，剔除 Yagci50 为 +0.049 到 +0.052。
   - 所有登记的敏感性分析都是主区间 O3、全中位数区间 O1：
     - Yagci 不含第 0 次检查：主区间 [−0.022, +0.003]，全中位数区间 [−0.008, −0.003]；
     - LIC 剔除标记点：[−0.038, +0.051]，[−0.007, −0.001]；
     - 两者都做：[−0.023, +0.003]，[−0.008, −0.003]。
3. **主导项：T_path。** 合并斜率中占 87%；在唯一能干净分项的 LIC 中占 97%。Yagci 不含第 0 次检查时，合并比例变为"混合"。LIC 的台阶模型没有以登记的优势胜过漂移模型，所以台阶成分不计入 d。模型 (c) 的台阶大小：T_path −0.42 Ah，ε_total −0.25 Ah。
4. **最干净的单一来源与合并规则给出的信息不同。**
   - LIC 是 280 Ah LFP 单芯，CV 截止几乎相同，检查中有参考充电。它的 d = −0.030 几乎完全来自 1C 充电的顶部状态。
   - WP4 显示我们锚点充电的顶部状态没有移动：截止电流固定在 5.10 A，弛豫电压平坦。
   - 这指向 f 接近 0、d 接近 d_CE ≈ 0。**这只是解读，不是登记结果**；第 12 轮的顶部模型就是为检验它而设。
5. **排行榜探测：不变。** 保持第 7 轮的顺序：P_stress_early → P_start → P_drift。
6. **SOH 变体（仅供排行榜）：** 见上表。CK7 为 SUB 90.765；d_lo（−0.0363）时 90.486；−0.031 时 90.527；d_hi（+0.0522）时 91.166。
7. **交接：** [R12_HANDOFF.json](R12_HANDOFF.json) 列出了主导项、电池组驱动量、建议的顶部充电模型、未评估项、被标记的锚点，以及从第 5B 轮继承的约束。
   - 未评估项包括：电池组电压限制下的电芯不一致、25 °C 偏移 Δ、本电池组的库伦效率、底部状态、检查的充电协议。
