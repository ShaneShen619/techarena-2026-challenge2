<a id="en"></a>

# Round 10: Robust Per-Cell Step Aggregation — Final Report

> **Language:** English · [中文](#zh)

- **Run:** 2026-10-17, following [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md), WP0–WP5.
- **Where:** branch `exp/phase2-r10-cell-steps-20261017`, worktree `/Users/shane/Desktop/Arena_1017_r10_cells`, based on round 9's `6749c63`.
- **Reference:** SUB = T_main (submission `5cd305c`), reproduced exactly.
- **Rules:** every WP was registered before evaluation. Real-proxy numbers are exposed; selection used the causal scenarios. Nothing was wired.

## Conclusions first

1. **Idea A (stabilise detection) works, in one form only.** A3 takes each cell's step location as the **median over the 6 detection variants**, then the **median over the 4 cells**, and it passes every gate.
   - **Causal:** the causal mean falls from 0.1571 to 0.1470 pp (pseudo 0.1439 → 0.1342, cold start 0.1703 → 0.1599), and the 16 changed causal cases improve from 0.217 to 0.190 pp.
   - **Robust:** all 6 leave-one-variant-out rebuilds beat SUB. This is exactly where round 9's plain median failed.
   - **Real proxies (exposed):** MAE 0.126 → 0.120.
   - **Why the mean versions fail:** they let the noisy dvdq_peak variant (σ 0.37 Ah, against about 0.09 for the others) into the cell value, and they fail on cold start.
2. **Idea B (combine per-cell changes) adds nothing.**
   - The median of per-cell changes is not robust (4/6 variants).
   - The one-cell rejection rule almost never fires. On the main variant 1 of 22 cases exceeds τ = 0.38 Ah; on the A3 locations none exceeds 0.29 Ah.
   - B3 passes only because, without rejections, it reduces to A3's locations with a mean of changes, and it is weaker than A3 (causal 0.1515).
   - **There is no "one cell jumps in a month" event to reject.**
3. **Idea C (remove top-state drift) is not supported.** Neither the cell voltage at the CV end (within-cell R² 0.00002) nor the anchor's per-cell step→top distance (R² 0.065) explains the per-cell drift. WP3 exited by rule.
4. **The cell divergence is real ageing of one cell.**
   - Cell 1 is the weakest cell at maximum depth. Its relative step depth falls steadily from −0.18 to −0.51 Ah over 8 months, while cells 2–4 keep fixed offsets.
   - The pattern survives variant-ensemble detection unchanged, so it is not detection noise.
   - It does not follow the top-state imbalance, which converges over the same period (cell 3's CV-end lead falls 133 → 18 mV).
5. **Recommendation: A3 is a small, low-risk robustness upgrade.** Wiring it is optional and is your decision.
   - It changes the SOH by −0.07 to +0.10 pp per checkup (CK3 +0.060, CK5 −0.066, CK6 +0.095, CK7 −0.056).
   - Its candidate class matches the research version to 1.4e-14 pp, passes the causality checks, and validates as a package under Python 3.11 (full run 12 s).

## 1. Verdict per idea (Δ 0.4; gates as in the prompt, section 4)

| Candidate | pseudo | cold | changed cases (SUB 0.217) / worst | G_robust | G_event SD (SUB 0.2625) | real MAE (SUB 0.126) | real MAX (SUB 0.228) | Verdict |
|---|---|---|---|---|---|---|---|---|
| A1 variant mean, cell mean | 0.1348 | 0.1829 ✗ | 0.203 / +0.094 ✗ | 5/6 ✓ | 0.2589 | 0.165 | 0.378 ✗ | fail |
| A2 variant mean, cell median | 0.1394 | 0.1776 ✗ | 0.211 / +0.112 ✗ | 5/6, max +0.050 ✗ | 0.2646 | 0.165 | 0.362 ✗ | fail |
| **A3 variant median, cell median** | **0.1342** | **0.1599** | **0.190 / +0.060** | **6/6** | **0.2621** | **0.120** | **0.237** | **pass → final** |
| B1 median of per-cell changes | 0.1402 | 0.1696 | 0.208 / +0.029 ✗ | 4/6 ✗ | 0.2631 | 0.128 | 0.241 | fail |
| B2 one-cell rejection (τ 0.38) | 0.1439 | 0.1786 ✗ | 1 case, +0.083 ✗ | 5/6 | 0.2625 | 0.126 | 0.227 | fail |
| B3 rejection on A3 locations | 0.1331 | 0.1698 | 0.192 / +0.029 | 6/6 | 0.2527 | 0.135 | 0.231 | pass, but weaker than A3 |
| C (top-state) | — | — | — | — | — | — | — | not built: WP3a mechanism fails (u: R² 0.00002; w: R² 0.065) |
| Combination A → B (= B3) | as B3 | | | | | | | pass; causal 0.1515 > A3 0.1470 |

Reports: [wp1](wp1/REPORT.md), [wp2](wp2/REPORT.md), [wp3](wp3/REPORT.md), [wp4](wp4/REPORT.md).

## 2. What changes and where (real scenario, Δ 0.4; differences < 0.25 pp are unresolvable)

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| branch | fallback | sqrt_gap | fallback | phase | phase | phase | phase |
| SUB err (pp) | +0.217 | +0.039 | +0.080 | +0.228 | +0.150 | −0.163 | −0.004 |
| A3 err (pp) | +0.210 | +0.039 | +0.140 | +0.237 | +0.084 | −0.068 | −0.060 |
| SUB SOH | 95.992 | 94.507 | 93.541 | 92.811 | 92.081 | 91.331 | 90.821 |
| A3 SOH | 95.984 | 94.507 | 93.600 | 92.821 | 92.015 | 91.426 | 90.765 |

CK2 (sqrt_gap) cannot change. The largest move is CK6 (+0.095 pp), the checkup where round 8 attributed most of the error to the cell mean.

## 3. The cell picture after this round

- **The offsets survive ensemble detection unchanged:** cell1 −0.37, cell2 +0.12, cell3 +0.23, cell4 −0.12 Ah, each in 8/8 months. **This is not detection noise.**
- **The divergence is one cell.** Cell 1's relative depth goes −0.18, −0.28, −0.25, −0.38, −0.34, −0.48, −0.43, −0.51 Ah over months 0–7, while cells 2–4 are flat.
- **It is not top-state drift.** The top imbalance converges, and neither top-state covariate explains the drift.
- **It is slow.** In any one month the deviation of a cell's change (≤ 0.30 Ah) is within the detection noise, so rejection never acts.
- **Open question: which cell does the pack capacity follow?** In a series pack the weakest cell limits the capacity, but the weakest-cell value (round 9) fails every gate. A3's median of cells is the robust middle ground. A per-cell capacity model would need per-cell capacity references, which the data do not provide.

## 4. Recommendation

- **Wire A3: optional, low risk.** It improves every causal metric by about 0.01 pp, is the only candidate in two rounds that is robust across detection methods, and moves no checkup by more than 0.1 pp.
- **The change.** Replace `TechArena_Challenge2_Team_Package/my_model/model_template.py` with [wp4/candidate_model/model_template.py](wp4/candidate_model/model_template.py), set `EXPECTED_SOH` in the packaging script to CK0..CK7 = 98.441, 95.984, 94.507, 93.600, 92.821, 92.015, 91.426, 90.765, then rerun the packaging check.
- **Not recommended:** any B or C variant, or the plain cell median or minimum.

## 5. Risks and limits

- **Small, overlapping samples.** The causal evidence rests on 16 changed cases, of which 5 are duplicates (PC5 = PC5_all). The gains are about 0.01 pp in mean causal MAE.
- **A full-data constant.** σ_det (B's τ) comes from full-data residuals seen in round 8; it affects only B, which was not adopted.
- **Three A candidates were compared.** Selection among them was by the registered rule, so a little selection optimism is possible. The leave-one-variant-out robustness and the event gate limit it.
- **A prompt flaw.** C1/C2 as written would have been identical to SUB under the cell mean (D3.1). This did not matter because WP3 exited at the mechanism check.
- **Exposure.** Real-proxy numbers and the round 8 cell offsets were known before this round.

## Reproduction

See [README.md](README.md). Environment: Python 3.13.0, numpy 2.4.2, pandas 3.0.0, scipy 1.18.0; package check Python 3.11.14, numpy 2.4.6, pandas 3.0.6.

---

<a id="zh"></a>

# 第 10 轮：稳健的单体台阶合并——最终报告

> **语言：** [English](#en) · 中文

- **运行：** 2026-10-17，按 [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md) 执行 WP0–WP5。
- **位置：** 分支 `exp/phase2-r10-cell-steps-20261017`，worktree `/Users/shane/Desktop/Arena_1017_r10_cells`，基于第 9 轮的 `6749c63`。
- **参照：** SUB = T_main（提交 `5cd305c`），已完全复现。
- **规则：** 每个 WP 都先登记后评估。真实代理数字已曝光，选择依据是因果场景。没有接入任何改动。

## 结论先行

1. **想法 A（先把检测做稳）有效，但只有一种形式。** A3 的做法是：每个电芯的台阶位置**先在 6 种检测变体上取中位数**，**再对 4 个电芯取中位数**，它通过了全部检验。
   - **因果指标：** 因果平均从 0.1571 降到 0.1470 pp（伪场景 0.1439 → 0.1342，冷启动 0.1703 → 0.1599），变化的 16 个因果案例平均误差从 0.217 降到 0.190 pp。
   - **稳健性：** 6 个留一变体的重建全部优于 SUB，这正是第 9 轮普通中位数失败的地方。
   - **真实代理（已曝光）：** MAE 0.126 → 0.120。
   - **均值版本失败的原因：** 它们把噪声很大的 dvdq_peak 变体（σ 0.37 Ah，其他约 0.09）带进了单体值，并且在冷启动上不通过。
2. **想法 B（合并单体变化量）没有增加任何东西。**
   - 单体变化量取中位数不稳健（6 个变体中只有 4 个达标）。
   - 剔除规则几乎从不触发：主变体上 22 个案例只有 1 个超过 τ = 0.38 Ah；在 A3 位置上没有任何案例超过 0.29 Ah。
   - B3 之所以通过，是因为在没有剔除时它就等于"A3 的位置 + 变化量取平均"，而且比 A3 弱（因果 0.1515）。
   - **根本不存在"某个电芯在某个月突然跳变"可供剔除。**
3. **想法 C（消除顶部状态漂移）不成立。** CV 结束时的单体电压（单体内 R² 0.00002）和锚点处单体台阶到顶部的距离（R² 0.065）都解释不了单体漂移，WP3 按规则退出。
4. **单体拉开是某一个电芯的真实老化。**
   - 单体 1 是最大深度处最弱的电芯，它的相对台阶深度在 8 个月里从 −0.18 稳步降到 −0.51 Ah，而单体 2–4 保持固定偏移。
   - 这一模式在多变体集成检测下依然不变，所以不是检测噪声。
   - 它也不跟随顶部不平衡；同一时期顶部不平衡在收敛（单体 3 的 CV 结束电压领先从 133 mV 降到 18 mV）。
5. **建议：A3 是一个小而低风险的稳健性升级。** 是否接入可选，由你决定。
   - 各检查点 SOH 变化在 −0.07 到 +0.10 pp 之间（CK3 +0.060、CK5 −0.066、CK6 +0.095、CK7 −0.056）。
   - 它的候选模型类与研究实现相差 1.4e-14 pp，通过因果性检查，并在 Python 3.11 下通过提交包验证（完整运行 12 s）。

## 1. 各想法结论

见英文表格。A1、A2、B1、B2 未通过；A3 通过并成为最终候选；B3 通过但弱于 A3；C 未构建（机制不成立）；组合等于 B3。

## 2. 改了什么、改在哪里

见英文表格。CK2（sqrt_gap 分支）不可能变化。最大的变化在 CK6（+0.095 pp），第 8 轮正是把这个检查点的大部分误差归因于单体均值。

## 3. 本轮之后的单体图景

- **偏移在集成检测后依然不变**：cell1 −0.37、cell2 +0.12、cell3 +0.23、cell4 −0.12 Ah，每个单体 8 个月中 8 个月同号。**这不是检测噪声。**
- **拉开来自一个电芯。** 单体 1 的相对深度在第 0–7 月依次为 −0.18、−0.28、−0.25、−0.38、−0.34、−0.48、−0.43、−0.51 Ah，单体 2–4 基本平稳。
- **这不是顶部状态漂移。** 顶部不平衡在收敛，两个顶部状态协变量都解释不了漂移。
- **它变化缓慢。** 单个月内一个电芯变化量的偏离（≤ 0.30 Ah）落在检测噪声之内，所以剔除规则从不起作用。
- **待解问题：电池组容量跟随哪个电芯？** 串联电池组的容量受最弱电芯限制，但取最弱电芯（第 9 轮）所有检验都没通过。A3 的单体中位数是稳健的折中。要建立按单体的容量模型，需要单体容量参考值，而数据中没有。

## 4. 建议

- **接入 A3：可选，风险低。** 它让每项因果指标改善约 0.01 pp，是两轮中唯一在各种检测方法上都稳健的候选，且没有任何检查点变化超过 0.1 pp。
- **具体改动：** 用 [wp4/candidate_model/model_template.py](wp4/candidate_model/model_template.py) 替换 `TechArena_Challenge2_Team_Package/my_model/model_template.py`，把打包脚本中的 `EXPECTED_SOH` 设为 CK0..CK7 = 98.441、95.984、94.507、93.600、92.821、92.015、91.426、90.765，然后重新运行打包检查。
- **不推荐：** 任何 B 或 C 变体，以及普通的单体中位数或最小值。

## 5. 风险与局限

- **样本少且重叠：** 因果证据来自 16 个变化的案例，其中 5 个是重复（PC5 = PC5_all），提升约 0.01 pp。
- **全量数据常数：** σ_det（B 的 τ）来自第 8 轮已看过的全量数据残差，只影响未被采用的 B。
- **比较了三个 A 候选：** 按登记规则在其中选择，可能有少许选择乐观偏差；留一变体稳健性和事件检验对此有所约束。
- **prompt 缺陷：** 按原文，C1/C2 在单体均值下会与 SUB 完全相同（D3.1）。由于 WP3 在机制检查处就已退出，这一点没有造成影响。
- **曝光：** 真实代理数字和第 8 轮的单体偏移在本轮之前就已知道。
