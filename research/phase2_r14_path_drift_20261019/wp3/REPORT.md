<a id="en"></a>

# Round 14 WP3 — Decision and hand-off: report

> **Language:** English · [中文](#zh)

Rules from `wp1/protocol.json` (commit `46f3c26`), applied by `src/decide.py` through the driver `src/wp3_decide.py`. No rule or output used P_k or any proxy error.

## Conclusions

- **Registered outcome: O3 "not identifiable".** The noise gate passes. The LOO range of E is 0.59 Ah wide, above the 0.30 Ah limit. O1 and O2 were unreachable in any case, because P1b is not estimable.
- **SUB is unchanged, and there is no candidate.** This round does not change the submission.
- **d_path = −0.118 Ah/Ah (LOO −0.167 … −0.095), i.e. E = −0.97 Ah at CK7 (LOO −1.37 … −0.78).**
  - ΔBIC = +7.2 favours the linear model.
  - **This number should not be used.** The exploratory analysis in WP2 shows that it comes from the Ah chain's month-specific loss rate λ, not from the pack's tops. With a same-cycle λ, Term3 shows no trend (E ≈ −0.11 … +0.04 Ah).
- **Agreement.**
  - P1b: not estimable (2 points; where it exists, Term3' = Term3 exactly).
  - P2 (voltage, λ-free): the same sign but much smaller, E = −0.28 Ah (LOO −0.31 … −0.14). The LOO ranges do not overlap, and the P2 trend comes from cell 3 alone.
- **Combination with round 13 (reported only):**
  - d_tail = 0.0131 Ah/Ah (range 0 … 0.0502), from round 13's own O3 "not identifiable" result.
  - **d_top = −0.105 Ah/Ah (range −0.167 … −0.045); E_top = −0.86 Ah (range −1.37 … −0.37).**
  - Because it inherits the d_path artefact, it is passed to round 15 as a number with that caveat, not as an estimate.

## Rule by rule

| Rule (registered) | Value | Result |
|---|---|---|
| Noise gate: σ_TT,25 ≤ 0.30 Ah | 0.125 Ah (max of the reduced reading, 0.062, and the full reading, 0.125) | **pass** |
| P1 estimable (≥ 5 points) | 5 (anchors 1, 2, 4, 5, 6) | pass |
| Identifiability: LOO range of E ≤ 0.30 Ah wide | −1.37 … −0.78 Ah, width **0.59 Ah** | **fail → O3 "not identifiable"** |
| O1: LOO E ⊂ [−0.10, +0.10] Ah and \|P1b E\| ≤ 0.15 Ah | LOO E entirely below −0.78; P1b not estimable | not met (not evaluated after the identifiability exit) |
| O2: LOO E excludes 0, \|E\| > 0.10, ΔBIC ≥ 2, P1b same sign | the first three hold (excludes 0; 0.97; +7.2); P1b not estimable | not met |

## SOH per checkup (%) — leaderboard-only, never scored against proxies

Built with the copied round 11 `drift.py`: Q' = Q + d · max(0, 100.41 − Q).

| Variant | d (Ah/Ah) | CK0 | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 | CK7 − SUB (pp) |
|---|---|---|---|---|---|---|---|---|---|---|
| **SUB** | 0 | 98.441 | 95.984 | 94.507 | 93.600 | 92.821 | 92.015 | 91.426 | **90.765** | 0 |
| SUB + d_path (median) | −0.1179 | 98.441 | 95.694 | 94.043 | 93.029 | 92.158 | 91.257 | 90.599 | 89.860 | −0.905 |
| SUB + d_path (LOO low) | −0.1670 | 98.441 | 95.574 | 93.850 | 92.792 | 91.883 | 90.942 | 90.255 | 89.483 | −1.282 |
| SUB + d_path (LOO high) | −0.0953 | 98.441 | 95.750 | 94.132 | 93.139 | 92.286 | 91.403 | 90.758 | 90.034 | −0.731 |
| SUB + d_top (median) | −0.1048 | 98.441 | 95.727 | 94.095 | 93.093 | 92.232 | 91.342 | 90.691 | 89.961 | −0.804 |
| SUB + d_top (low) | −0.1670 | 98.441 | 95.574 | 93.850 | 92.792 | 91.883 | 90.942 | 90.255 | 89.483 | −1.282 |
| SUB + d_top (high) | −0.0451 | 98.441 | 95.873 | 94.330 | 93.382 | 92.568 | 91.725 | 91.110 | 90.419 | −0.346 |

**None of these variants is recommended.** The outcome is O3, and the d behind them is the λ artefact.

## Recommendation and hand-off to round 15

1. **Keep SUB.** Do not submit SUB + d_path or SUB + d_top.
2. **The Ah chain needs a same-cycle loss rate.**
   - λ is stable within a segment but steps by up to 0.8·10⁻³ (≈ 0.3 Ah per 5-day block) between checkup cycles.
   - Any Ah-chain term that borrows λ from another month carries that error.
   - **Round 12's Term3 uses the same pooled 25 °C λ for anchors 1–4 and 7, so it has the same exposure.**
3. **Before re-estimating d_path,** register a rule that takes λ from the 45 °C segment of the same cycle.
   - The 25 vs 45 °C transfer error measured where both exist is −0.03 and +0.18 Ah per block.
   - Anchors 1 and 7 have no same-cycle 45 °C segment.
4. **What the pack-native evidence supports (not registered):**
   - the path part of the ε drift is at most a few tenths of an Ah at CK7: same-cycle Term3 −0.11 … +0.04 Ah; P2 −0.28 Ah from one cell; P2 cell mean −0.11 Ah;
   - with round 13's tail bound [0, +0.41] Ah, the open variable remains the checkup's CV termination and charge rate.

## Files

| File | Content |
|---|---|
| `decision.json` | the full output of `decide()`, every check |
| `R14_RESULT.json` | hand-off for round 15: outcome, d_path, BIC, P1b/P2 agreement, d_top, per-anchor table, exploratory λ finding (labelled), recommendation |
| `SOH_variants.csv` | the SOH table above |
| `per_anchor.csv` | per anchor: Q_fc, fade, λ, Term3, Term3', S_gap, P2, P3, exploratory same-cycle Term3 |

---

<a id="zh"></a>

# 第 14 轮 WP3 — 决策与交接：报告

> [English](#en) · 中文

规则来自 `wp1/protocol.json`（提交 `46f3c26`），由 `src/decide.py` 通过驱动脚本 `src/wp3_decide.py` 执行。没有任何规则或输出使用 P_k 或代理误差。

## 结论

- **登记结果：O3"无法识别"。** 噪声门通过。E 的 LOO 范围宽 0.59 Ah，超过 0.30 Ah 的上限。无论如何 O1 和 O2 都不可达，因为 P1b 无法估计。
- **SUB 不变，没有候选。** 本轮不改动提交。
- **d_path = −0.118 Ah/Ah（LOO −0.167 … −0.095），即 CK7 处 E = −0.97 Ah（LOO −1.37 … −0.78）。**
  - ΔBIC = +7.2，偏好线性模型。
  - **这个数字不应使用。** WP2 的探索性分析表明，它来自电量链中按月变化的损耗率 λ，而不是电池组的顶部。改用同周期 λ 后，Term3 没有趋势（E ≈ −0.11 … +0.04 Ah）。
- **一致性。**
  - P1b：无法估计（2 个点；在存在的地方 Term3' 与 Term3 完全相等）。
  - P2（电压信号，不依赖 λ）：符号相同但小得多，E = −0.28 Ah（LOO −0.31 … −0.14）。两者的 LOO 范围不重叠，且 P2 的趋势只来自电芯 3。
- **与第 13 轮合并（只报告）：**
  - d_tail = 0.0131 Ah/Ah（范围 0 … 0.0502），来自第 13 轮自己的 O3"无法识别"结果。
  - **d_top = −0.105 Ah/Ah（范围 −0.167 … −0.045）；E_top = −0.86 Ah（范围 −1.37 … −0.37）。**
  - 由于它继承了 d_path 的假象，交给第 15 轮时附带这一说明，作为一个数字而不是一个估计。

## 逐条规则

| 规则（已登记） | 数值 | 结果 |
|---|---|---|
| 噪声门：σ_TT,25 ≤ 0.30 Ah | 0.125 Ah（缩减读法 0.062 与全集读法 0.125 中的较大者） | **通过** |
| P1 可估计（≥ 5 个点） | 5（锚点 1、2、4、5、6） | 通过 |
| 可识别性：E 的 LOO 范围宽度 ≤ 0.30 Ah | −1.37 … −0.78 Ah，宽 **0.59 Ah** | **不通过 → O3"无法识别"** |
| O1：LOO E ⊂ [−0.10, +0.10] Ah 且 \|P1b E\| ≤ 0.15 Ah | LOO E 全部低于 −0.78；P1b 无法估计 | 不满足（可识别性退出后未再评估） |
| O2：LOO E 不含 0、\|E\| > 0.10、ΔBIC ≥ 2、P1b 同号 | 前三条成立（不含 0；0.97；+7.2）；P1b 无法估计 | 不满足 |

## 各检查点 SOH（%）— 只用于排行榜，绝不与代理对比打分

用复制来的第 11 轮 `drift.py` 构造：Q' = Q + d · max(0, 100.41 − Q)。

| 变体 | d（Ah/Ah） | CK0 | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 | CK7 − SUB（pp） |
|---|---|---|---|---|---|---|---|---|---|---|
| **SUB** | 0 | 98.441 | 95.984 | 94.507 | 93.600 | 92.821 | 92.015 | 91.426 | **90.765** | 0 |
| SUB + d_path（中位数） | −0.1179 | 98.441 | 95.694 | 94.043 | 93.029 | 92.158 | 91.257 | 90.599 | 89.860 | −0.905 |
| SUB + d_path（LOO 下端） | −0.1670 | 98.441 | 95.574 | 93.850 | 92.792 | 91.883 | 90.942 | 90.255 | 89.483 | −1.282 |
| SUB + d_path（LOO 上端） | −0.0953 | 98.441 | 95.750 | 94.132 | 93.139 | 92.286 | 91.403 | 90.758 | 90.034 | −0.731 |
| SUB + d_top（中位数） | −0.1048 | 98.441 | 95.727 | 94.095 | 93.093 | 92.232 | 91.342 | 90.691 | 89.961 | −0.804 |
| SUB + d_top（下端） | −0.1670 | 98.441 | 95.574 | 93.850 | 92.792 | 91.883 | 90.942 | 90.255 | 89.483 | −1.282 |
| SUB + d_top（上端） | −0.0451 | 98.441 | 95.873 | 94.330 | 93.382 | 92.568 | 91.725 | 91.110 | 90.419 | −0.346 |

**这些变体都不推荐。** 结果是 O3，而它们背后的 d 就是 λ 假象。

## 建议与交给第 15 轮的内容

1. **保留 SUB。** 不要提交 SUB + d_path 或 SUB + d_top。
2. **电量链需要同周期的损耗率。**
   - λ 在段内稳定，但在检查周期之间最多跳变 0.8·10⁻³（每个 5 天块约 0.3 Ah）。
   - 任何从别的月份借用 λ 的电量链项都带有这个误差。
   - **第 12 轮的 Term3 对锚点 1–4 和 7 使用同一个 25 °C 合并 λ，所以有同样的风险。**
3. **在重新估计 d_path 之前，** 先登记一条规则：λ 取同一周期的 45 °C 段。
   - 在两者都存在的地方测得的 25 °C 与 45 °C 迁移误差为每块 −0.03 和 +0.18 Ah。
   - 锚点 1 和 7 没有同周期的 45 °C 段。
4. **本电池组上的证据支持什么（未登记）：**
   - ε 漂移的路径部分在 CK7 处至多零点几 Ah：同周期 Term3 −0.11 … +0.04 Ah；P2 −0.28 Ah，只来自一个电芯；P2 电芯平均 −0.11 Ah；
   - 结合第 13 轮的尾巴界限 [0, +0.41] Ah，未决变量仍然是检查的 CV 终止条件和充电倍率。

## 文件

| 文件 | 内容 |
|---|---|
| `decision.json` | `decide()` 的完整输出及每一项检查 |
| `R14_RESULT.json` | 交给第 15 轮：结果、d_path、BIC、P1b/P2 一致性、d_top、逐锚点表、探索性 λ 发现（已标注）、建议 |
| `SOH_variants.csv` | 上面的 SOH 表 |
| `per_anchor.csv` | 每个锚点：Q_fc、衰减、λ、Term3、Term3'、S_gap、P2、P3、探索性同周期 Term3 |
