<a id="en"></a>

# WP1 — Is the post-anchor offset an overhang state effect?

> **Language:** English · [中文](#zh)

- **Protocol:** [protocol.json](protocol.json), SHA256 `3089ba08…`, committed in `0a51969` before any WP1 number was computed. It includes amendment 1 (see below).
- **Script:** [run_wp1.py](run_wp1.py). **Outputs:** [anchor_state_table.csv](outputs/anchor_state_table.csv), [wp1_predictions_P.json](outputs/wp1_predictions_P.json), [grid tables](outputs/), [figure](outputs/wp1_offset_vs_state.png), and a [descriptive sensitivity](outputs/wp1_sensitivity_descriptive.json) computed after the registered result.
- **Sample:** 7 anchors. Every statistic is descriptive.

## Conclusions first

1. **Registered classification: not supported.** None of the three registered predictions holds, and all three point the wrong way:

| Prediction (anchors 1–7) | Registered threshold | Spearman ρ | exact p (two-sided) | Holds |
|---|---|---|---|---|
| P1: offset vs residual start charge r_j | ρ ≥ +0.5 | −0.29 | 0.54 | no |
| P2: offset vs dwell before the anchor | ρ ≥ +0.5 | −0.18 | 0.71 | no |
| P3: offset vs anchor bottom→step section | ρ ≤ −0.5 | +0.61 | 0.16 | no (opposite sign) |
| P4: second program offset ≤ 0.15 Ah | ≥ 5 anchors | — | — | not evaluable (only 2 anchors have ≥ 3 programs in the segment) |

   The six step variants agree in sign on every prediction (P1 −0.02 to −0.70; P2 −0.07 to −0.46; P3 +0.41 to +0.85).

2. **What the data show instead.**
   - The offset is fairly constant (0.20–0.65 Ah) and does not follow the anchor state.
   - The positive P3 correlation is mostly a shared time trend: the bottom section shrinks with anchor index (ρ = −0.83), and the offset tends to shrink too (ρ = −0.43). After removing linear time trends, ρ(P1) = +0.39 (now in the predicted direction, but weak) and ρ(P3) = +0.39 (still opposite). This was computed after the registered result and is descriptive only.
   - The dwell column (P2) is distorted at anchor 2, whose gap includes the missing segment 3 (560 h). Without anchor 2, ρ = −0.49, still opposite in sign.

3. **The checkup order points to "no effect on the hidden C/20".** In 7 of 7 checkups the operation ends at a pack voltage of 13.10–13.31 V, i.e. charged, not near empty. So the C/20 checkup most likely follows a full charge without a near-empty dwell before it. By the registered rule **H_ov_before is the main reading**. In that reading even a real overhang release would not change the hidden capacity relative to Q_fc, because Q_fc is unaffected by it (amendment 1).

4. **Grid implications are small.**
   - On the round-6 grid plus the 6 H_ov_after hypotheses (b_0 = median), **SUB keeps the lowest max regret** (0.034 among the round-6 models plus SUB + drift).
   - On the H_ov_after hypotheses alone, SUB + drift (d = −0.020) is marginally lower (0.033 vs 0.034).
   - With the registered prior update for "not supported" (f weights 0.5 / 0.3 / 0.2), the lowest expected score is SUB + drift (d = −0.031): 0.091 vs SUB 0.103. That is the same ordering as round 6's diagnosis prior.

5. **Interpretation for the report.**
   - The overhang mechanism remains possible physics, but this pack's data do not support it: the offset does not grow with the dwell or with the start state.
   - With the memory effect excluded (literature) and homogenisation disfavoured (no step sharpening), the offset is best described as a **reproducible measurement/charge-path effect of the first deep discharge after a from-empty charge**, of unknown mechanism. That is how round 6 described it.
   - It does not affect SUB, which uses phase-matched month-end steps.

## Amendment 1 (registered before computing)

- **Column (f) cannot be measured.** The CCCV charge that opens each deep program covers only about 21 Ah from 13.4 V and does not cross the graphite step. The recharges after a deep program are dynamic (2–12 A with interleaved discharges).
- **Li accounting changes the predicted signs.** With the discharge end set by the anode, Li released from the overhang during a near-empty dwell raises the anode's starting lithiation:
  - the anchor's bottom→step section gets shorter;
  - the pre-charge rest voltage (and so r_j) rises;
  - the step after the anchor sits deeper below the top;
  - **Q_fc itself is unchanged**, because all cathode Li is still moved.
- P1 and P3, the classification and the H_ov target were re-registered on this basis. P1's inputs were visible in round 6 outputs before registration; the statistic was not (decision D1.1).

## Physical discussion

- **Temperature.** With Ea = 64.5 kJ/mol (Lewerenz 2018) the overhang exchange is 5.1× faster at 45 °C than at 25 °C.
  - Month 0 (anchor at 45 °C, 140 h dwell) has the largest offset: 0.71 Ah median (0.83 Ah in round 6's main variant). This is qualitatively consistent with faster exchange, but also with break-in and the unknown delivery state, so it cannot separate the hypotheses.
- **Size.** 0.2–0.65 Ah is 0.2–0.65 % of capacity. That is well within what a 5.7–9 % overhang could exchange, so size alone does not argue against overhang. The missing state dependence does.

## Anchor table (excerpt)

| Anchor | Dwell h | End pack V | Rest V | r_j upper Ah | Offset median Ah | Bottom→step Ah | Step→top Ah |
|---|---|---|---|---|---|---|---|
| 0 (45 °C) | 140 | — | 11.57 | 0.77 | 0.71 | 66.38 | 33.75 |
| 1 | 95 | 13.29 | 11.81 | 1.53 | 0.65 | 63.25 | 33.75 |
| 2 | 560* | 13.30 | 11.81 | 1.53 | 0.53 | 62.69 | 32.98 |
| 3 | 77 | 13.22 | 11.63 | 1.00 | 0.42 | 63.25 | 31.39 |
| 4 | 91 | 13.20 | 11.88 | 1.78 | 0.49 | 62.13 | 31.62 |
| 5 | 143 | 13.31 | 11.95 | 2.06 | 0.36 | 61.44 | 31.64 |
| 6 | 146 | 13.27 | 11.89 | 1.85 | 0.20 | 61.38 | 31.26 |
| 7 | 119 | 13.10 | 11.92 | 1.99 | 0.54 | 61.94 | 30.02 |

\* The gap includes the missing segment 3.

---

<a id="zh"></a>

# WP1 — 锚点后偏移是不是 overhang 状态效应？

> **语言：** [English](#en) · 中文

- **协议：** [protocol.json](protocol.json)（SHA256 `3089ba08…`），在计算任何 WP1 数字之前于 `0a51969` 提交，含修订 1。
- **脚本：** [run_wp1.py](run_wp1.py)。**输出：** 逐锚点表、预测结果、网格表、图，以及在登记结果之后补算的描述性敏感性分析。
- **样本：** 7 个锚点。所有统计量都是描述性的。

## 结论先读

1. **登记的分类：不支持。** 三条登记预测没有一条成立，而且方向都相反：P1（偏移与起点剩余电量 r_j）ρ = −0.29；P2（偏移与锚点前停放时长）ρ = −0.18；P3（偏移与锚点底段长度）ρ = +0.61，与预测符号相反；P4 无法评估（同一运行段内有 ≥ 3 次程序的锚点只有 2 个）。6 种台阶方法的符号全部一致。
2. **数据显示的情况。**
   - 偏移相当稳定（0.20–0.65 Ah），不随锚点状态变化。
   - P3 的正相关主要来自共同的时间趋势：底段随锚点序号缩短（ρ = −0.83），偏移也有缩小趋势（ρ = −0.43）。去掉线性时间趋势后，ρ(P1) = +0.39（方向转为与预测一致，但很弱），ρ(P3) = +0.39（仍相反）。这些是登记结果之后补算的描述性数字。
   - 锚点 2 的停放时长（560 h）包含了缺失的段 3，P2 在这一点上失真；去掉锚点 2 后 ρ = −0.49，仍与预测相反。
3. **检查顺序表明隐藏 C/20 不受影响。** 7 次检查前的运行都结束在 13.10–13.31 V（已充电，而不是近空），所以 C/20 检查很可能在满充之后进行，之前没有近空停放。按登记规则，**H_ov_before 是主解读**。在这种解读下，即使真的存在 overhang 释放，也不会改变隐藏容量相对于 Q_fc 的关系，因为 Q_fc 本身不受它影响（修订 1）。
4. **对网格的影响很小。**
   - 在第六轮网格加上 6 个 H_ov_after 假设（b_0 取中位数）后，**SUB 仍然是最大后悔值最低的**（0.034）。
   - 只看 H_ov_after 假设时，SUB + 漂移（d = −0.020）略低（0.033 对 0.034）。
   - 按“不支持”登记的先验更新（f 权重 0.5 / 0.3 / 0.2），期望得分最低的是 SUB + 漂移（d = −0.031）：0.091，SUB 为 0.103。排序与第六轮的诊断先验相同。
5. **报告中的解读。**
   - overhang 机理在物理上仍然可能，但本电池组的数据不支持它：偏移不随停放时长或起点状态增大。
   - 记忆效应已被文献排除，均匀化也不利（台阶没有变尖），所以这个偏移最好描述为**从空态满充之后第一次深放电的可重复测量/充电路径效应，机理未明**，与第六轮的表述相同。
   - 它不影响 SUB，因为 SUB 用的是同相位的月末台阶。

## 修订 1（计算前登记）

- **列 (f) 无法测量。** 每个深放电程序开头的 CCCV 充电只有约 21 Ah、从 13.4 V 开始，不越过石墨台阶；深放电之后的回充是动态的（2–12 A，中间夹着放电）。
- **锂库存推导改变了预测的符号。** 放电末端由负极决定时，近空停放期间从 overhang 释放的锂会提高负极的起始嵌锂量：
  - 锚点的底段（底 → 台阶）变短；
  - 充电前的静置电压（因此 r_j）升高；
  - 锚点之后的台阶在满充端以下更深；
  - **Q_fc 本身不变**，因为正极的锂仍然全部转移。
- P1、P3、分类和 H_ov 目标据此重新登记。P1 的输入在登记前已在第六轮输出中可见，但统计量没有（决策 D1.1）。

## 物理讨论

- **温度。** 取 Ea = 64.5 kJ/mol（Lewerenz 2018），overhang 交换在 45 °C 下比 25 °C 快 5.1 倍。
  - 第 0 个月（锚点在 45 °C，停放 140 h）偏移最大：中位 0.71 Ah（第六轮主方法为 0.83 Ah）。这在定性上与交换更快一致，但也与磨合和未知的出厂状态一致，无法区分各假设。
- **量级。** 0.2–0.65 Ah 即容量的 0.2–0.65 %，完全在 5.7–9 % 的 overhang 能交换的范围内，所以量级本身不构成反对理由；反对理由是偏移缺乏状态依赖。
