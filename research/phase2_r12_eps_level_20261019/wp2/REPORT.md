<a id="en"></a>

# WP2 — Bottom: shared-bottom test and start anomalies: report

> **Language:** English · [中文](#zh)

Protocol v1 (`wp1/protocol.json`, registered in `b3f3e7a`). `src/locators.py` and `src/ahchain.py` are imported unchanged (`shasum -c wp1/protocol.sha256`: OK). Figure: `wp2/wp2_bottom.png`.

## Conclusions

1. **H_SB's necessary condition fails for anchors 5 and 7 (G_SB).**
   - σ_LOO = 0.132 Ah, which is below the 0.25 Ah limit.
   - The leave-one-out residuals of anchor 5 (−0.520 Ah) and anchor 7 (+0.400 Ah) exceed max(2·σ_LOO, 0.15) = 0.264 Ah.
   - By the registered rule, H_SB is "rejected for anchors 5, 7", and both join the anomaly list.
   - Caveat: the dV/dQ locators scatter by up to ~3 Ah within a cell (1 mV quantisation, see point 7). These residuals may reflect locator noise as much as real bottom shifts. The rule is applied as registered.
2. **Anchor 3's bottom anomaly is identified (G_a3).**
   - a_3^rel = **+0.305 Ah** on the combined value, against a threshold of 0.264 Ah.
   - Four of the five locators share its sign (CL2 +0.68, CL3 +0.80, CL4 +0.28, CL5 +0.22; CL1 −0.09).
   - Anchor 3 started about 0.3 Ah deeper than the relaxed trend. This fits its unrelaxed, low start (11.624 V, +53 mV/h) and the exposed exploratory value of 0.3–0.4 Ah.
   - The anchor-3 rule's condition therefore holds, and SUB_A3fix becomes a WP4 candidate (leaderboard-only).
   - Caveat: the anomaly is only just above the threshold, and it has the same size as the failing residuals of the relaxed anchors 5 and 7.
3. **a_0 is not identified (G_B3).**
   - D_bot − C_bot = +2.09 Ah.
   - h, from the 25 °C anchors, is −5.46 Ah [−6.17, −4.74].
   - a_0 = −(D_bot − C_bot) − h = **+3.37 Ah [1.74, 4.72]**. The width is 2.98 Ah, above the 0.40 Ah limit.
   - a_0 enters the budget with its full interval. Interval endpoints add, so the width of EPS_EXTRA_hat is at least 2.98 Ah, beyond the 0.50 Ah limit of L1 and L2. WP4 records the decision formally.
   - The top split is F^CK_0 − F^A_0 = +3.66 Ah [2.03, 5.01].
4. **Why: h does not transfer from 25 °C to the 45 °C anchor 0.**
   - An exploratory, non-registered h1 from anchor 0's own first program (45 °C) is −1.58 Ah (A3) or −1.78 Ah (DL1). That is 3.7–3.9 Ah away from the 25 °C h.
   - With it, a_0 ≈ −0.31 … −0.51 Ah, still carrying the first-program offset that h1 includes.
   - The registered a_0 of +3.4 Ah is therefore dominated by the temperature dependence of h (the charge-side step position against the discharge-side one), not by a deep anchor-0 start.
   - The registered design has no 45 °C h, so a_0 stays unidentified. A 45 °C h with an explicit first-program correction is a round-13 item.
   - The second caveat, CK0's 5.1 A against the programs' ≈ 10 A, is not resolved either.
5. **Start audit (B1).**
   - Anchors 1, 2 and 4–7 are relaxed (last-30-min slope −0.2 … +5.5 mV/h), consistent with "C/20 end state plus rest only".
   - **Anchor 0** is unrelaxed (+84.5 mV/h) 3.41 d after its C/20 ended.
     - The 25 °C anchors relax within ≤ 5.5 mV/h after checkup windows of 3.2–6.0 d (anchor 2: unknown).
     - The pack starts at 47.0 °C, 2 K above the set point, and cools at −0.89 K/h. This excludes a warming transient.
     - Through dU/dT, the temperature drift moves the voltage by only ≈ ±1 mV/h (4 × 0.3 mV/K × 0.89 K/h).
     - The four cells sit within 5–7 mV of each other, as they do at a C/20 cutoff. The relaxed 25 °C anchors sit 22–35 mV apart.
     - Together this points to an unrecorded current event (a discharge towards the cutoff, with self-heating) shortly before the recording started, not to a thermal transient.
   - **Anchor 3** is unrelaxed (+53.2 mV/h, +74.1 mV/h over the whole 2 h rest).
     - Its window of 3.11 d is only 0.12 d shorter than anchor 1's, and anchor 1 is relaxed (+3.2 mV/h).
     - The temperature is flat (−0.10 K/h), and the start voltage is 0.18–0.33 V below the other 25 °C anchors.
     - A short window does not explain this. It is "something else": an unrecorded event before segment 6. Segment 6 is also the segment whose profile paused twice (WP0).
6. **Descriptive: no relation.** Among the relaxed anchors, the Q_bot residuals do not relate to the start voltage (Spearman ρ = −0.32, p = 0.54) or to the bottom spread (ρ = 0.03, p = 0.96), with n = 6. Under H_SB the rising start voltage has no ε effect anyway.
7. **Round-8 check (diagnostic, not a gate).**
   - Rounding CL1 to 0.25 Ah reproduces round 8's `bottom_to_step` within 0.25 Ah for anchors 0, 2, 4 and 6 only. Anchors 1, 3, 5 and 7 are off by −0.69, −1.13, −0.31 and −0.63 Ah.
   - Per cell, CL1 − R8 lies in −1.80 … +1.17 Ah (median −0.37).
   - Cause: the charge-side dV/dQ is a broad plateau (2.4–3.0 mV/Ah over ≈ 6 Ah) quantised in steps of 0.49 mV/Ah, so an argmax on either grid lands on one of several near-equal maxima. The package's even-window convolution adds a +0.125 Ah shift (DECISIONS D30).
   - This matches the WP1 synthetic resolution. It also means round 8's per-cell charge-side values are uncertain at the ±1 Ah level.

## B1 — start audit (`start_audit.csv`)

| k | Seg | Set °C | Window d | Rest h | Start pack V | Slope last 30 min mV/h | Temp start °C | Temp trend K/h | Spread start mV | Relaxed |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1 | 45 | 3.39 (C/20 end) | 0.50 | 11.570 | +84.5 | 46.55 | −0.885 | 7 | **no** |
| 1 | 2 | 25 | 3.23 | 2.00 | 11.805 | +3.2 | 25.58 | +0.047 | 22 | yes |
| 2 | 4 | 25 | unknown (≤ 3.68) | 2.00 | 11.808 | +5.5 | 25.38 | +0.009 | 23 | yes |
| 3 | 6 | 25 | 3.11 | 2.00 | 11.624 | +53.2 | 25.42 | −0.096 | 26 | **no** |
| 4 | 8 | 25 | 3.71 | 2.00 | 11.879 | +4.0 | 25.34 | −0.022 | 24 | yes |
| 5 | 10 | 25 | 5.35 | 2.00 | 11.953 | −0.2 | 25.39 | −0.124 | 29 | yes |
| 6 | 12 | 25 | 5.98 | 2.00 | 11.891 | +1.5 | 25.31 | +0.004 | 32 | yes |
| 7 | 14 | 25 | 4.28 | 2.00 | 11.921 | +2.5 | 25.40 | +0.005 | 35 | yes |

Cell 1 is the lowest cell at every start.

## B2 — bottom section (`bottom_locators.csv`, `b2_results.json`)

| k | t d | Q_fc Ah | Q_bot Ah | Q_top Ah | CL1 | CL2 | CL3 | CL4 | CL5 | in-sample resid. | LOO resid. |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 5.8 | 100.122 | 65.744 | 34.379 | 66.00 | 65.92 | 66.05 | 65.17 | 64.84 | +3.211 (a_0^rel, diagnostic) | — |
| 1 | 29.0 | 97.003 | 62.325 | 34.678 | 62.77 | 62.87 | 62.94 | 62.08 | 62.08 | +0.002 | +0.085 |
| 2 | 59.8 | 95.670 | 62.043 | 33.627 | 62.27 | 62.04 | 62.68 | 61.79 | 61.79 | −0.002 | +0.043 |
| 3 | 92.8 | 94.642 | 62.051 | 32.591 | 62.08 | 62.66 | 62.88 | 61.79 | 61.79 | +0.305 (a_3^rel) | — |
| 4 | 125.7 | 93.747 | 61.452 | 32.295 | 62.06 | 61.94 | 61.45 | 61.19 | 61.37 | +0.002 | −0.039 |
| 5 | 159.0 | 93.082 | 60.633 | 32.449 | 61.22 | 60.21 | 60.72 | 60.63 | 60.63 | −0.517 | **−0.520** |
| 6 | 195.8 | 92.636 | 60.729 | 31.907 | 61.27 | 60.71 | 60.76 | 60.66 | 60.72 | −0.089 | −0.093 |
| 7 | 230.9 | 91.954 | 60.790 | 31.163 | 61.30 | 61.12 | 60.69 | 60.72 | 60.80 | +0.290 | **+0.400** |

- **Trend.** Q_bot = 62.585 − 0.00903·t Ah (Theil–Sen over anchors 1, 2, 4–7; −0.27 Ah/month).
- **Locator columns.** CL1–CL5 are per-locator pack values (median over the cells). The per-cell values are in `bottom_locators.csv`.

## B3 — CK0 split (`ck0_split.json`, `h_table.csv`)

| Quantity | Value (Ah) |
|---|---|
| D_top (CK0, C/20 start → step), cells 32.46 / 32.69 / 32.86 / 32.31 | 32.578 |
| D_bot = 100.41 − D_top | 67.832 |
| C_bot (anchor 0, charge start → step), cells 65.78 / 65.38 / 65.71 / 66.04 | 65.744 |
| C_top = Q_fc,0 − C_bot | 34.379 |
| D_bot − C_bot (combined; paired variants i = 1..5: 1.84, 2.11, 1.44, 2.67, 2.99; 5 × 5 cross range 1.44–3.19) | +2.088 |
| D_top − C_top | −1.801 |
| ε0 check (= 100.41 − Q_fc,0) | 0.2876 (exact) |
| h medians: h1 A3 / h1 DL1 / h2 A3 / h2 DL1 | −4.736 / −5.230 / −5.696 / −6.166 |
| h point [lo, hi] | −5.463 [−6.166, −4.736] |
| **a_0 [interval]** | **+3.374 [1.745, 4.722]**, width 2.977 → G_B3 not identified |
| F^CK_0 − F^A_0 [interval] | +3.662 [2.033, 5.010] |
| exploratory (not registered): h1_0 A3 / DL1 → a_0 | −1.580 / −1.781 → −0.509 / −0.307 |

| k | C_top | D1 A3 | D1 DL1 | D2 A3 | D2 DL1 | Term3 (F^T2 − F^A) | h1 A3 | h1 DL1 | h2 A3 | h2 DL1 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 34.678 | 29.970 | 29.732 | 29.271 | 28.820 | 0.600 | −4.708 | −4.946 | −6.007 | −6.458 |
| 2 | 33.627 | 28.868 | 28.113 | 28.312 | 27.602 | 0.579 | −4.759 | −5.514 | −5.893 | −6.604 |
| 4 | 32.295 | 27.608 | 27.163 | 27.061 | 26.565 | 0.418 | −4.687 | −5.132 | −5.652 | −6.148 |
| 5 | 32.449 | 27.244 | 27.167 | 26.846 | 26.376 | 0.093 | −5.204 | −5.282 | −5.696 | −6.166 |
| 6 | 31.907 | 26.864 | 26.362 | 26.346 | 25.909 | 0.135 | −5.043 | −5.545 | −5.696 | −6.134 |
| 7 | 31.163 | 26.449 | 25.985 | 25.970 | 25.257 | — (AT pair not admissible) | −4.714 | −5.179 | — | — |

- **Term3.** Term3_k = N − λ_s·thr of the AT pair, from `ahchain.terms` with the main λ. It is needed for h2 and is reported again in WP3.
- **h1 vs h2.** h1 − h2 = 0.5–1.5 Ah per anchor. That is the first-program offset plus 5 days of in-segment step decline, corrected for Term3.

**Caveats.**
- CK0 discharges at 5.1 A, while the programs' step band is ≈ 10 A.
- The checkup temperature is unknown.
- Anchor 0 charged at 45 °C. This caveat dominates (point 4).
- The dV/dQ variants are quantisation-limited (`wp1/synthetic_resolution.json`).

## Gates (`gates.json`)

| Gate | Result |
|---|---|
| G_SB | **failed**: σ_LOO 0.132 ≤ 0.25, but anchors 5 (−0.520) and 7 (+0.400) exceed 0.264 → H_SB rejected for anchors 5, 7 |
| G_a3 | **identified**: a_3^rel +0.305 > 0.264, same sign on 4/5 locators |
| G_B3 | **not identified**: a_0 width 2.977 > 0.40 → enters the budget with [1.745, 4.722] |
| Anomaly list | anchors 3 (G_a3), 5 and 7 (G_SB); unrelaxed starts: 0, 3 |

---

<a id="zh"></a>

# WP2 — 底部："共用底部"检验与起点异常：报告

> [English](#en) · 中文

使用协议第 1 版（`wp1/protocol.json`，在 `b3f3e7a` 中登记），原样导入 `src/locators.py` 和 `src/ahchain.py`（`shasum -c wp1/protocol.sha256` 通过）。图：`wp2/wp2_bottom.png`。

## 结论

1. **H_SB 的必要条件对锚点 5 和 7 不成立（G_SB）。**
   - σ_LOO = 0.132 Ah，低于 0.25 Ah 的上限。
   - 锚点 5（−0.520 Ah）和锚点 7（+0.400 Ah）的留一残差超过 max(2·σ_LOO, 0.15) = 0.264 Ah。
   - 按登记规则，H_SB 记为"对锚点 5、7 不成立"，两者加入异常列表。
   - 局限：dV/dQ 定位器在同一电芯内的离散最大可达约 3 Ah（1 mV 量化，见第 7 点）。这些残差反映的可能主要是定位噪声，而不是真实的底部偏移。规则仍按登记执行。
2. **锚点 3 的底部异常已识别（G_a3）。**
   - 合并值 a_3^rel = **+0.305 Ah**，阈值为 0.264 Ah。
   - 5 个定位器中有 4 个与它同号（CL2 +0.68、CL3 +0.80、CL4 +0.28、CL5 +0.22；CL1 −0.09）。
   - 锚点 3 比已静置锚点的趋势深约 0.3 Ah 开始充电。这与它未静置好的低起点（11.624 V，+53 mV/h）以及已曝光的探索值 0.3–0.4 Ah 一致。
   - 因此锚点 3 规则的条件成立，SUB_A3fix 成为 WP4 的候选（只用于排行榜）。
   - 局限：异常只略高于阈值，与已静置锚点 5、7 未通过的残差大小相当。
3. **a_0 未识别（G_B3）。**
   - D_bot − C_bot = +2.09 Ah。
   - h 来自 25 °C 锚点，为 −5.46 Ah [−6.17, −4.74]。
   - a_0 = −(D_bot − C_bot) − h = **+3.37 Ah [1.74, 4.72]**，宽度 2.98 Ah，超过 0.40 Ah 的上限。
   - a_0 以完整区间进入预算。区间端点相加，所以 EPS_EXTRA_hat 的宽度至少为 2.98 Ah，超过 L1 和 L2 的 0.50 Ah 上限。决策由 WP4 正式记录。
   - 顶部拆分 F^CK_0 − F^A_0 = +3.66 Ah [2.03, 5.01]。
4. **原因：h 不能从 25 °C 迁移到 45 °C 的锚点 0。**
   - 用锚点 0 自己在 45 °C 下的第一个程序算出的探索性 h1（未登记）为 −1.58 Ah（A3）或 −1.78 Ah（DL1），与 25 °C 的 h 相差 3.7–3.9 Ah。
   - 用它算出 a_0 ≈ −0.31 … −0.51 Ah，其中仍含有 h1 带入的首个程序偏移。
   - 所以登记得到的 a_0 = +3.4 Ah 主要来自 h（充电侧台阶相对放电侧台阶的位置）随温度的变化，而不是锚点 0 起点更深。
   - 登记的设计里没有 45 °C 的 h，因此 a_0 仍为未识别。带明确首个程序修正的 45 °C h 留给第 13 轮。
   - 另一项局限——CK0 用 5.1 A、程序约用 10 A——同样没有解决。
5. **起点审查（B1）。**
   - 锚点 1、2、4–7 已静置好（最后 30 min 斜率 −0.2 … +5.5 mV/h），与"C/20 结束状态加单纯静置"一致。
   - **锚点 0** 在其 C/20 结束 3.41 天后仍未静置好（+84.5 mV/h）。
     - 25 °C 锚点在 3.2–6.0 天的检查窗口后斜率都 ≤ 5.5 mV/h（锚点 2 未知）。
     - 电池组起始温度 47.0 °C，比设定温度高 2 K，并以 −0.89 K/h 降温，排除了升温过程。
     - 温度漂移经 dU/dT 只带来约 ±1 mV/h（4 × 0.3 mV/K × 0.89 K/h）。
     - 四个电芯彼此相差仅 5–7 mV，就像在 C/20 截止时那样；而已静置的 25 °C 锚点相差 22–35 mV。
     - 综合起来，这指向记录开始前不久有一次未记录的电流事件（向截止电压的放电，伴随自发热），而不是单纯的温度瞬变。
   - **锚点 3** 未静置好（+53.2 mV/h，整个 2 h 静置为 +74.1 mV/h）。
     - 它的窗口 3.11 天，只比已静置好的锚点 1（+3.2 mV/h）短 0.12 天。
     - 温度平稳（−0.10 K/h），起始电压比其他 25 °C 锚点低 0.18–0.33 V。
     - 窗口短解释不了，是"别的原因"：第 6 段之前有一次未记录的事件。第 6 段也正是工况程序暂停过两次的那一段（WP0）。
6. **描述性：没有关系。** 在已静置锚点中，Q_bot 残差与起始电压（Spearman ρ = −0.32，p = 0.54）和底部压差（ρ = 0.03，p = 0.96）都没有关系，n = 6。在 H_SB 下，起始电压上升本来就不影响 ε。
7. **与第 8 轮的核对（诊断，不是门槛）。**
   - 把 CL1 取整到 0.25 Ah 后，只有锚点 0、2、4、6 在 0.25 Ah 以内重现了第 8 轮的 `bottom_to_step`；锚点 1、3、5、7 相差 −0.69、−1.13、−0.31、−0.63 Ah。
   - 逐电芯 CL1 − R8 在 −1.80 … +1.17 Ah 之间（中位数 −0.37）。
   - 原因：充电侧 dV/dQ 是一个宽平台（约 6 Ah 范围内为 2.4–3.0 mV/Ah），并以 0.49 mV/Ah 的台阶量化，所以两种网格上的 argmax 都会落在几个几乎相等的极大值之一。包内偶数窗口卷积还带来 +0.125 Ah 的平移（DECISIONS D30）。
   - 这与 WP1 合成实验得到的分辨率一致，也说明第 8 轮逐电芯的充电侧数值有 ±1 Ah 量级的不确定性。

## B1、B2、B3 与门槛表格

各表与英文部分相同（`start_audit.csv`、`bottom_locators.csv`、`b2_results.json`、`ck0_split.json`、`h_table.csv`、`gates.json`）。

| 门槛 | 结果 |
|---|---|
| G_SB | **失败**：σ_LOO 0.132 ≤ 0.25，但锚点 5（−0.520）和 7（+0.400）超过 0.264 → H_SB 对锚点 5、7 不成立 |
| G_a3 | **已识别**：a_3^rel +0.305 > 0.264，5 个定位器中 4 个同号 |
| G_B3 | **未识别**：a_0 宽度 2.977 > 0.40 → 以 [1.745, 4.722] 进入预算 |
| 异常列表 | 锚点 3（G_a3）、5 和 7（G_SB）；未静置好的起点：0、3 |

**局限。**
- CK0 以 5.1 A 放电，而程序的台阶电流带约为 10 A。
- 检查温度未知。
- 锚点 0 在 45 °C 下充电，这是主要局限（第 4 点）。
- dV/dQ 变体受量化限制（`wp1/synthetic_resolution.json`）。
