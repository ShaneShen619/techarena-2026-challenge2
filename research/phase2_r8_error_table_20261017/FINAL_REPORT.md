<a id="en"></a>

# Round 8: Error-Analysis Long Tables — Final Report

> **Language:** English · [中文](#zh)

- **Run:** 2026-10-17, following [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md), work packages WP0–WP6.
- **Where:** branch `exp/phase2-r8-error-table-20261017`, worktree `/Users/shane/Desktop/Arena_1017_r8_err`, based on round 7's `c9658ad`.
- **Reference model:** SUB = T_main, submission commit `5cd305c`. It was reproduced exactly and equals `EXPECTED_SOH` (WP0).
- **Scope:** no candidate was built, nothing was tuned, and the submission is untouched. All statistics are descriptive. Every real-scenario number is exposed-exploratory.

## Conclusions first

1. **The main systematic error is a scale mismatch.** The graphite-step depth moves only **0.745 Ah per Ah of anchor fade** (90 % CI 0.674–0.765, 40 events, 8 months).
   - The fallback branch uses β = 1, and early phase checkups shrink β towards 1, so they under-predict the loss.
   - The scale mismatch explains +0.86 Ah of CK1's increment residual, +0.32 Ah at CK3 and +0.18 Ah at CK4.
   - The first-program offset, the suspect named in H1, works in the opposite direction. It *hides* part of this error: removing it makes the fallback worse.
2. **Cell heterogeneity is persistent and growing.**
   - Each cell keeps its own step-depth offset in 8 of 8 months: cell 1 −0.36 Ah, cell 3 +0.25 Ah from the cell median.
   - The spread of the four cells grows from 0.56 to 0.72 Ah.
   - With 4-cell means, this moves the phase increment by −0.15 Ah at CK6 (most of CK6's −0.17 Ah), +0.10 at CK5 and −0.09 at CK4.
3. **The case residual falls with fade** by −0.078 Ah/Ah (CI [−0.137, −0.023]).
   - By the registered rule its CI contains the ε-drift value −0.031, so it is labelled "indistinguishable from ε drift, invisible to proxies".
   - **However**, inc_resid is referenced to Q_fc, so this trend *is* visible to the proxies. It overlaps with conclusion 1 (early fallback cases are positive, late ones negative).
4. **Month 0 (the 45 °C campaign-start segment) is an outlier month.**
   - It holds 6 of the 8 worst events by |R_anc| and 4 of 5 by |R_seg|.
   - After the scale and offset terms, CK1 still carries +0.56 Ah that nothing in the tables explains. It cannot be tested causally, because no other checkup starts from a 45 °C anchor.
5. **Null results:**
   - first-program offset as an error source (H1);
   - temperature deviation (H3);
   - resistance mechanism (H7 inconclusive; R is quantised and flat);
   - common CV cut-off and start-state corrections (H9: they do not reduce, or they triple, the month-to-month scatter);
   - step sharpness beyond month 0 (H5 inconclusive);
   - gap-length or horizon effects beyond branch identity (H8);
   - daily cycles (H10: the usage profile is an exact current-controlled replay, so cycle Ah carries no state).

## 1. Failure map (ranked)

| # | Pattern | Where | Size at affected checkups | Evidence | Visible to proxies? |
|---|---|---|---|---|---|
| 1 | Step depth moves 0.745 Ah/Ah; β = 1 (fallback) or β shrunk to ~1 (early phase) under-predicts the loss | fallback (CK1, CK3, cold start CS), phase at CK4 (β 1.06) | contribution +0.86 Ah (CK1), +0.32 (CK3), +0.18 (CK4); ≈ 0.84 / 0.31 / 0.17 pp | b CI [0.674, 0.765]; H1 diagnostic (c) flips the CK1/CK3 sign; strong | yes (inc_resid) |
| 2 | Persistent per-cell step offsets with growing spread; the 4-cell mean picks up the differential drift | phase branch, all event uses | −0.15 Ah at CK6, +0.10 at CK5, −0.09 at CK4 (≈ 0.15 / 0.10 / 0.09 pp) | H6a 8/8 months per cell (seen before registration); H6b +0.16 Ah, CI [0.06, 0.21]; strong | yes |
| 3 | Case residual trends with fade (−0.078 Ah/Ah) | all branches, early positive → late negative | fitted +0.47 Ah at CK1 → −0.12 at CK7 | H4 slope CI [−0.137, −0.023]; ε-drift label by rule; overlaps #1; moderate | yes for inc_resid (label rule notwithstanding) |
| 4 | Month 0 / 45 °C campaign start: step depth and step quality off | CK1 (fallback from anchor 0) | unexplained rest +0.56 Ah (0.55 pp) at CK1 | worst-set enrichment p < 0.001; one month only; weak to moderate | yes (CK1 is the Δ0 MAX, 0.61 pp) |
| 5 | Month 5→6 anchor drop only −0.45 Ah (non-monotone) | CK6 one-month extrapolation (all sqrt pseudo cases, −0.32 Ah) | 0.31 pp at CK6 in 5 scenarios | single month; not explained by cut-off or start state (H9); weak | yes |
| 6 | 45 °C post-switch transient in R_seg | 45 °C segments, first 2 days | +0.023 Ah | CI excludes 0 but below threshold; negligible | — |

## 2. Error budget for SUB at Δ = 0.4 (real scenario)

The table is descriptive. Contributions interact and are not additive ([wp6/outputs/error_budget_real_d04.csv](wp6/outputs/error_budget_real_d04.csv)). err = offset_part + inc_resid. The contribution columns split inc_resid: "β vs scaling" = increment_pred − raw increment/b, "first program" = −(3c offset) for fallback, "cell mean vs median" = increment(means) − increment(medians).

| CK | branch | err Ah (pp) | offset_part | inc_resid | β vs scaling (#1) | first program | cell mean vs median (#2) | rest | H4 fitted (#3) |
|---|---|---|---|---|---|---|---|---|---|
| CK1 | fallback | +0.221 (+0.217) | −0.400 | +0.621 | +0.855 | −0.834 | +0.037 | +0.562 | +0.473 |
| CK2 | sqrt_gap | +0.040 (+0.039) | 0 | +0.040 | — | — | — | +0.040 | +0.228 |
| CK3 | fallback | +0.081 (+0.080) | 0 | +0.081 | +0.324 | −0.549 | −0.053 | +0.359 | +0.123 |
| CK4 | phase | +0.232 (+0.228) | 0 | +0.232 | +0.176 | 0 | −0.089 | +0.145 | +0.043 |
| CK5 | phase | +0.153 (+0.150) | 0 | +0.153 | +0.041 | 0 | +0.097 | +0.015 | −0.027 |
| CK6 | phase | −0.166 (−0.163) | 0 | −0.166 | −0.030 | 0 | −0.148 | +0.013 | −0.080 |
| CK7 | phase | −0.004 (−0.004) | 0 | −0.004 | −0.075 | 0 | +0.047 | +0.024 | −0.115 |

Reading:
- **Phase checkups CK4–CK7.** The two patterns leave rests of only +0.01 to +0.15 Ah. #1 dominates CK4 and #2 dominates CK6.
- **Fallback checkups.** #1 and the first-program offset nearly cancel, and the rest (CK1 +0.56, CK3 +0.36) is the part a 1/b correction alone would overshoot.
- **CK1's offset_part −0.40** is the Δ convention for the 45 °C anchor (fallback uses Q_CK0).

## 3. Next-round feature list

| Pattern | Mechanism | Feature / preprocessing | Columns that hold it | Registered test a candidate must pass |
|---|---|---|---|---|
| #1 | The step reads only part of the capacity fade (b ≈ 0.75, i.e. β ≈ 1.34) | (a) apply the visible-anchor β to the fallback increment; (b) shrink β towards 1/b instead of 1 (prior BETA0 ≈ 1.3) | table_cases: `increment_pred`, `beta_a4`, `beta_raw`, `beta_shrink_w`, `x`; WP2 `b_free_fit` | mean \|inc_resid\| on the causal fallback cases (CS k 3–7, PC5 k 3, PG2 k 7) and the causal phase cases (PC5 k 4–7) must fall, and no CS month may worsen by > 0.10 Ah (the 1/b scaling overshoots CS k 5–7: −0.38/−0.70/−0.62); never decided on CK1/CK3 proxies |
| #2 | Cells drift apart (spread +0.16 Ah over the campaign) and the mean follows the outliers | cell-median steps (V3 change 3, `median_cells`) or per-cell offset removal before averaging | table_events: `depth_main` per cell, `R_cell`, `pack_median_depth` | R_anc_b scatter (pack) must fall with medians; phase inc_resid on PC5 k 4–7 and real must not rise in mean \|·\|; per-cell sign stability re-checked on the post-CK7 events (E39, E40) |
| #3 | Overlaps #1; a residual part may be ε drift | none on the proxies; keep as the risk term (P_drift) | table_cases `cum_fade_at_anchor_Ah`, `inc_resid_Ah` | re-estimate the slope after #1/#2; if it stays inside [−0.137, −0.023], report it as a risk, not a fix |
| #4 | Campaign-start 45 °C segment (first anchor at 45 °C, start-up) | none testable (single month); document as CK1 risk | table_events month 0, table_anchors anchor 0 | — (no causal analogue) |
| #5 | Month 5→6 anchor drop anomalously small | none (no mechanism found) | table_anchors `dQ_fc_next` | — |

Not recommended, because the table evidence speaks against them: the common CV cut-off (zero change at 5.1 A; 6 A cut ratio 0.96), anchor start-state correction (scatter × 3.05), temperature-corrected step depth (H3 null), resistance-linked ε (H7: R flat and quantised), sharpness weights (H5 confounded with month 0), daily-cycle features (WP4: deterministic).

## 4. Null results

- **H1.** The first-program offset does not shift fallback residuals negatively (+0.084 Ah, CI [−0.112, 0.238]).
- **H2.** At 45 °C there is no switch transient ≥ 0.10 Ah (R_anc_b +0.047; R_seg +0.023, real but tiny). The 25 °C "systematic" result is the known first-program offset.
- **H3.** The deviation of measured from set temperature has no effect (R_anc_b +0.016, CI [−0.177, 0.176]).
- **H5.** Step sharpness has no effect outside month 0 (inconclusive).
- **H7.** Pulse resistance has no resolvable trend at the anchors (ρ 0.61, exact p 0.17); CV Ah and the 6 A tail are not linked to it.
- **H8.** |inc_resid| does not grow with the gap or the horizon; the pooled effects are branch identity and CK1.
- **H9.** Neither the 6 A cut-off nor the start-state correction removes month-to-month ΔQ_fc scatter (variance ratio 0.96; r_half 3.05; fitted LOO 1.18).
- **H10.** Daily-cycle Ah residuals are void by construction. H10b: the loaded bottom voltage is +6.5 mV higher in the first block after an anchor, opposite to expectation and irrelevant to SOH.

## Work packages

| WP | Content | Outcome | Report |
|---|---|---|---|
| 0 | setup, re-baselining | SUB = T_main reproduced; submitted class = research = EXPECTED_SOH | [wp0](wp0/REPORT.md) |
| 1 | case table | 423 rows; decomposition assertion passes | [wp1](wp1/REPORT.md) |
| 2 | event table | 205 rows; matches events_merged; b = 0.745 | [wp2](wp2/REPORT.md) |
| 3 | anchor table | 8 rows; common cut-off trivial, 6 A tail 0.10–0.13 Ah | [wp3](wp3/REPORT.md) |
| 4 | cycle table | 430 swings; profile repeats exactly | [wp4](wp4/REPORT.md) |
| 5 | registered slicing, dossier | verdicts H1–H10, worst-20 % dossier | [wp5](wp5/REPORT.md) |
| 6 | synthesis | this report, [README.md](README.md), [DATA_DICTIONARY.md](DATA_DICTIONARY.md) | — |

## Risks and limits

- **Few independent samples:** 7 real cases, 8 anchor months and 41 events. Causal cases are near-duplicates across scenarios.
- **Exposure (D2.2):** the R_anc month trend and the per-cell R_cell signs were seen before registration (H4-event, H6a).
- **The b = 1 residual R_anc** is dominated by the scale mismatch, so event conclusions use the registered secondary R_anc_b.
- **Deviations** are recorded in [notes/DECISIONS.md](notes/DECISIONS.md) (D0.1–D5.4).

---

<a id="zh"></a>

# 第 8 轮：误差分析长表——最终报告

> **语言：** [English](#en) · 中文

- **运行：** 2026-10-17，按 [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md) 执行 WP0–WP6。
- **位置：** 分支 `exp/phase2-r8-error-table-20261017`，worktree `/Users/shane/Desktop/Arena_1017_r8_err`，基于第 7 轮的 `c9658ad`。
- **参照模型：** SUB = T_main，提交 `5cd305c`。已完全复现，且等于 `EXPECTED_SOH`（WP0）。
- **范围：** 没有构建候选模型，没有调参，提交未改动。所有统计都是描述性的；所有真实场景数字都属于已曝光的探索性结果。

## 结论先行

1. **主要的系统性误差是比例不匹配。** 石墨台阶深度随锚点衰减每 Ah 只移动 **0.745 Ah**（90 % CI 0.674–0.765，40 个事件，8 个月）。
   - fallback 分支用 β = 1，早期 phase 检查点又把 β 收缩到接近 1，因此都低估了容量损失。
   - 这一比例不匹配解释了 CK1 增量残差中的 +0.86 Ah、CK3 的 +0.32 Ah 和 CK4 的 +0.18 Ah。
   - H1 中怀疑的首个程序偏移方向相反，反而*掩盖*了部分误差：去掉它会让 fallback 更差。
2. **单体异质性持续存在且在增大。**
   - 每个单体在 8 个月中的 8 个月都保持各自的台阶深度偏移：相对单体中位数，单体 1 为 −0.36 Ah，单体 3 为 +0.25 Ah。
   - 四个单体的离散从 0.56 增至 0.72 Ah。
   - 使用 4 单体均值时，这使 phase 增量在 CK6 偏移 −0.15 Ah（占 CK6 −0.17 Ah 的大部分），CK5 +0.10，CK4 −0.09。
3. **案例残差随衰减下降**，斜率 −0.078 Ah/Ah（CI [−0.137, −0.023]）。
   - 按登记规则，其 CI 包含 ε 漂移值 −0.031，因此标注为"与 ε 漂移不可区分，代理不可见"。
   - **但是**，inc_resid 以 Q_fc 为参照，所以这一趋势*可以*被代理看到。它与结论 1 重叠（早期 fallback 案例为正，后期为负）。
4. **月份 0（45 °C 试验开始段）是离群月。**
   - 按 |R_anc| 最差的 8 个事件中它占 6 个，按 |R_seg| 最差的 5 个中占 4 个。
   - 扣除比例项和偏移项后，CK1 仍有 +0.56 Ah 无法由表中任何量解释。它无法做因果检验，因为没有其他检查点从 45 °C 锚点出发。
5. **零结果：**
   - 首个程序偏移作为误差来源（H1）；
   - 温度偏差（H3）；
   - 内阻机制（H7 不确定；内阻量化且平稳）；
   - 公共 CV 截止和起始状态修正（H9：逐月离散不减小，或增大到 3 倍）；
   - 月份 0 之外的台阶尖锐度（H5 不确定）；
   - 分支身份之外的缺口长度或外推时长效应（H8）；
   - 日循环（H10：工况是电流控制、完全重复的脚本，循环 Ah 不携带状态）。

## 1. 失败图谱（排序）

1. **台阶比例 0.745 与 β 处理不匹配。** fallback（CK1、CK3、冷启动 CS）及 CK4 的 phase（β 1.06）。贡献 +0.86 / +0.32 / +0.18 Ah；证据强；代理可见。
2. **单体偏移持续且离散增大。** phase 分支。CK6 −0.15、CK5 +0.10、CK4 −0.09 Ah；证据强（单体符号部分登记前已见）；代理可见。
3. **案例残差随衰减的趋势。** 斜率 −0.078 Ah/Ah，与 #1 重叠；按规则标注为 ε 漂移不可区分，但对 inc_resid 而言代理可见。
4. **月份 0 / 45 °C 试验开始段。** 只影响 CK1，剩余 +0.56 Ah 未解释；只有一个月，无法因果检验。
5. **第 5→6 月锚点降幅异常小**（−0.45 Ah）。CK6 一个月外推在 5 个场景中都为 −0.32 Ah；未找到机制。
6. **45 °C 切换后的瞬态**（+0.023 Ah）。可忽略。

## 2. SUB 在 Δ = 0.4 下的误差预算

见英文表格（[wp6/outputs/error_budget_real_d04.csv](wp6/outputs/error_budget_real_d04.csv)）。
- **phase 检查点 CK4–CK7：** 两种模式解释后的剩余只有 +0.01 到 +0.15 Ah；#1 主导 CK4，#2 主导 CK6。
- **fallback 检查点：** #1 与首个程序偏移几乎抵消，剩余部分（CK1 +0.56、CK3 +0.36）正是单独做 1/b 修正会过度修正的部分。
- **CK1 的 offset_part −0.40** 是 45 °C 锚点下 Δ 约定的结果（fallback 使用 Q_CK0）。

## 3. 下一轮特征清单

- **#1：** 在 fallback 增量上使用可见锚点 β，或把 β 向 1/b（约 1.3）而不是 1 收缩。检验：因果 fallback 案例（CS k 3–7、PC5 k 3、PG2 k 7）和因果 phase 案例（PC5 k 4–7）的平均 |inc_resid| 必须下降，且任一 CS 月份变差不得超过 0.10 Ah；不得只凭 CK1/CK3 代理决定。
- **#2：** 使用单体中位数台阶（V3 的第 3 项改动 `median_cells`），或平均前先去掉单体偏移。检验：pack 的 R_anc_b 离散下降；PC5 k 4–7 及真实场景 phase 的平均 |inc_resid| 不上升；在 CK7 之后的事件（E39、E40）上复核单体符号稳定性。
- **#3：** 不在代理上处理，保留为风险项（P_drift）。
- **#4、#5：** 无可检验特征，记录为风险。
- **不推荐：** 公共 CV 截止、起始状态修正、温度修正台阶深度、与内阻关联的 ε、尖锐度加权、日循环特征。

## 4. 零结果

H1、H2（45 °C）、H3、H5、H7、H8、H9、H10 的零结果见英文部分。

## 风险与局限

- **独立样本少：** 7 个真实案例、8 个锚点月、41 个事件；因果案例在不同场景间近似重复。
- **曝光（D2.2）：** H4 事件部分和 H6a 的残差在登记前已被看到。
- **事件结论使用 R_anc_b：** b = 1 的 R_anc 被比例不匹配主导，因此事件结论使用登记的次要残差 R_anc_b。
- **偏离记录：** 见 [notes/DECISIONS.md](notes/DECISIONS.md)（D0.1–D5.4）。
