<a id="en"></a>

# Round 3: Alternative Capacity Models — Final Report

> **Language:** English · [中文](#zh)

- **Run:** 2026-10-14, unattended, following [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md).
- **Branch:** `exp/phase2-round3-models-20261014`.
- **Protocols:** every stage froze its protocol (`stage_*/protocol.json` plus SHA256) before its evaluation ran.
- **Exposure:** all results are **exposed-exploratory**. Every CK1–CK7 proxy value had been seen before this round. All errors are proxy errors (post-checkup full charge + ε), not hidden truth.

## Conclusions first

**No alternative model beat V2. V2 stays the leading candidate; the active submission (V1/M4) and `my_model/` were not touched.**

- **B, charge-direction steps: exit.** Only the 8 anchor charges cross the graphite step. The ~5-day CCCV charges start about 21 Ah below full, above the step.
- **D, gap extrapolation: no change.** Every rate-based rule over-corrects the CK2-like pseudo-gaps, so the registered selection kept "no extrapolation". CK2 stays at +0.67 pp.
- **A, full-curve registration β: fails** (MAE 0.242 vs 0.216). The registered bottom section is strongly confounded with each anchor's *start state* (r = −0.975 with start voltage), so it cannot isolate LAM.
- **C, state-space fusion: fails** (MAE 0.355). Its structure lets ε leak into the degradation rates. It does confirm the temperature offset (δ ≈ 0.2 Ah) and the post-checkup transient (≈ +0.6 Ah).
- **E, ε-drift risk: zero, 0.03 or up to 0.5 pp, depending on the checkup protocol.** The large-drift scenario conflicts with the data. A leaderboard-only variant `V2_S1` was produced; it is not recommended.
- **F, ensemble: not applicable.** Only V2 qualified.

## Summary table

Proxy error in pp, main step method, A4 smoothing 2 Ah. MAE is given for δ = ε0 / ε0+0.4 / ε0+0.8; MAX and the CK2–7 MAE are at ε0+0.4.

| Model | Stage | MAE (three δ) | MAX | CK2–7 MAE | PG1 | PG2 | PC5 | PC10 | Gates |
|---|---|---|---|---|---|---|---|---|---|
| M4 (V1, submitted) | base | 0.347 / 0.291 / 0.285 | 0.669 | 0.304 | 0.251 | 0.207 | 0.325 | 0.340 | — |
| **V2** | base | **0.272 / 0.216 / 0.210** | 0.669 | **0.216** | 0.251 | 0.207 | 0.302 | 0.340 | reference |
| V2 + D1 (rate extrapolation) | D | 0.380 / 0.324 / 0.318 | 1.427 | 0.342 | 0.386 | 0.337 | 0.428 | 0.687 | fail |
| V2 + D2 (Arrhenius √t + Ah) | D | 0.370 / 0.270 / 0.244 | 1.049 | 0.279 | 0.412 | 0.350 | 0.365 | 0.473 | fail |
| V2_reg (registration β) | A | 0.298 / 0.242 / 0.236 | 0.669 | 0.246 | 0.251 | 0.207 | 0.312 | 0.340 | fail |
| SS (state space, τ 5 d) | C | 0.479 / 0.355 / 0.242 | 0.696 | 0.334 | 0.136 | 0.225 | 0.336 | 0.353 | fail |

Notes on the table:

- PG1/PG2 truncate month k−1's 45 °C segment after its first / second deep discharge, k = 4..7. PC5/PC10 cut the data 5 / 10 days before the checkup.
- **D3** (anchor √t trend) is undefined for CK2, so its real-data MAE leaves out CK2 and is not comparable. On the pseudo scenarios it did well: PG1 0.205, PG2 0.230, PC5 0.229, PC10 0.176.

Per-checkup errors at ε0+0.4 (pp):

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| M4 | +0.22 | +0.67 | +0.08 | +0.28 | −0.11 | −0.40 | −0.28 |
| V2 | +0.22 | +0.67 | +0.08 | +0.23 | +0.15 | −0.16 | −0.00 |
| V2_reg | +0.22 | +0.67 | +0.08 | +0.35 | +0.22 | −0.10 | +0.05 |
| SS | +0.48 | +0.50 | −0.04 | +0.70 | +0.46 | −0.07 | −0.23 |

## What each stage found

**Stage 0, harness.** It reproduces V2 exactly: 0.216 / 0.669. The pseudo-gap PG1 gives CK4 a fallback error of +0.60 pp, close to CK2's +0.67, so it is a fair stand-in for the CK2 problem.

**B** ([report](stage_B/REPORT.md)). Of the 41 CV-ending charges, all at 20.4 A, only the post-checkup anchors start deep enough (≥ 45 Ah) to cross the step. The registered exit rule applied, so there is no in-month charge-side channel.

**D** ([report](stage_D/REPORT.md)).

- **Results.** D1 and D2 add −0.3 to −0.9 Ah on the pseudo-gaps and flip the errors negative. On CK2 they would give −1.43 and −1.05 pp. The selection, committed before the real-data run, kept D0.
- **Why.** Inside a truncated month, the anchor-to-anchor capacity changes much less than "rate × missing days". Part of the loss is already in the transient captured by the fallback difference, and part is offset by the +0.18 Ah temperature step.
- **Lead.** The anchor-level √t trend (D3) helps pseudo-cutoffs and leave-one-anchor-out cases. It matters for the reduced-data-budget run, but it cannot help CK2, which has only one 25 °C anchor before it.

**A** ([report](stage_A/REPORT.md)).

- **Identifiability.** The registration parameters are mostly identifiable: bottom 60 %, top 85 % of anchor-cells.
- **The start-state problem.** The post-CK3 anchor started from a lower rest voltage (2.907 V/cell), and its registered bottom section came out 0.65 Ah longer. Across anchors, Δbottom follows the start voltage (r = −0.975), so the bottom section does not measure LAM_NE, and β_reg (0.86–1.38) is biased.
- **No linear start-state association was detected for Q_fc** (r = 0.04, 7 anchors). This small diagnostic neither validates Q_fc as the hidden C/20 capacity nor rules out a start-state effect.

**C** ([report](stage_C/REPORT.md)).

- **Fitted structure.** δ is fitted at 0.15–0.22 Ah and the post-checkup transient at +0.5 to +0.8 Ah, which independently confirms the structure V2 was built on.
- **Why it fails.**
  - ε leaks into the rates, because anchor 0 is fixed while the 25 °C anchors move with ε.
  - A single in-month path with an exponential transient fits CK4/CK5 worse than V2's phase-matched difference.
  - Its predicted SD is too small (71 % of errors within 2 SD).
- **Variant seen, not claimable.** τ = 8 days reached MAE 0.243 and CK2 +0.04.

**E** ([report](stage_E/REPORT.md)).

- **S2, a cell-limited checkup charge:** ε drift ≤ 0.03 pp.
- **S1, no start-state cancellation:** drift of 0.26–0.51 pp. With ΔV = 0.05 V it reproduces ε0 (0.285 vs 0.288 Ah) and the 25 °C offset (0.71 vs 0.69 Ah). It sits uneasily with the stage A diagnostic, however: no association between Q_fc and the start state was detected.
- **`V2_S1`.** This leaderboard-only variant differs from V2 by −0.39 to +0.34 pp on CK4–CK7. Do not submit it without information on the checkup protocol.

**F** ([report](stage_F/REPORT.md)). Not applicable; only V2 qualified.

## Recommendation

1. **Keep V2 as the leading candidate.** Whether to wire it into `my_model/` (replacing V1) is still your decision. This round found nothing that changes the comparison: V2 0.216 vs V1 0.291 pp proxy MAE.
2. **Treat CK2 (+0.67 pp) as a floor that the released data cannot fix.** Every extrapolation tested made it worse.
3. **The biggest real-score risk is the checkup protocol (stage E), not the in-month model.** If the organisers can say what happens between the C/20 discharge and the next operating charge, that decides between S0 (no drift) and S1 (up to 0.5 pp).
4. **Leads for a future, pre-registered round** (none can be claimed from this round):
   - the state-space model with anchor 0 given its own offset and τ ≈ 8 d;
   - a start-state-corrected registration β;
   - the anchor √t trend as a fallback for missing recent data (reduced-budget run).

## Deviations from the prompt and independent review

A second session ran an independent review on this branch during the run (`notes/INDEPENDENT_REVIEW.md`, `stage_0/`, `*_independent_*`). Its points, and other deviations, are listed here so that none of them is hidden:

1. **Stage D order.** PC5/PC10 at CK2 contain the same data as the real CK2 cut, so CK2 results of D1/D2 were computed (inside `run_select.py`) before the selection was committed. This breaks the prompt's ordering rule. The selection used PG1 + PG2 only and kept D0.
2. **Stage D, D2 formula.** The prompt asked for β-converted step observations. The registered implementation used M4's β = 1 step changes instead, and estimated the gap throughput from a visible-data rate (the post-gap counter jump is not visible at CK2). D2 was therefore not an exact execution of the prompt's formula. D2 is in any case not selected.
3. **Stage E, model.** The prompt asked for a per-cell CK0-curve mapping. This run implemented mechanism scenarios S0–S2 instead. The independent session registered a supplement for the required per-cell mapping (`stage_E/required_mapping_protocol.json`). Its results are not part of this report.
4. **Wording.** The independent review softened some claims about Q_fc and the start state in the stage A report. This report follows the softer wording.
5. **Candidate checks.** No candidate class was produced in this run, so G-impl was never applied. The review notes that bit-identity checks must compare exact floats, not rounded output.

None of these changes the main result: no alternative passed the gates against V2.

## Risks and limits

- **Exposure.** Every proxy value was known before this round. The pseudo scenarios reuse the same months, so they are not independent tests either.
- **ε and the post-checkup recovery.** As in V1/V2, only the leaderboard can test them.
- **A single pack.**
- **Files not made by this run.** At about 00:21, files appeared that this run did not make: 4 metadata lines in `src/statespace.py` and `stage_C/run_independent_diagnostics.py` with `stage_C/outputs/C_independent_*`. They do not change any predictions. They were left untouched and not committed (`notes/DECISIONS.md`, DX.1).

## Reproduction

```bash
cd research/phase2_round3_models_20261014
python3 stage0_reproduce.py
python3 stage_B/audit_coverage.py
python3 stage_D/run_select.py && python3 stage_D/run_eval.py
python3 stage_A/run_a.py && python3 stage_A/explore_start_state.py
python3 stage_C/run_c.py
python3 stage_E/run_e.py
```

- **Environment:** Python 3.13 (numpy 2.4, pandas 3.0). The full run takes under 2 minutes; extraction is cached in `cache/` (git-ignored).
- **Code reused unchanged:**
  - `research/phase2_anchor_step_20261013/src/events.py`
  - `research/phase2_v2_phase_matched_20261013/src/v2.py`
- **No candidate class** was produced, because no model passed its gates.

---

<a id="zh"></a>

# 第三轮：备选容量模型——最终报告

> **语言：** [English](#en) · 中文

- **运行：** 2026-10-14，无人值守，按 [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md) 执行。
- **分支：** `exp/phase2-round3-models-20261014`。
- **协议：** 每个阶段都在评估运行之前冻结了协议（`stage_*/protocol.json` 及 SHA256）。
- **曝光：** 全部结果都是**已曝光的探索性结果**，CK1–CK7 的每个代理值在本轮之前都已看过。所有误差都是代理误差（检查后完整充电 + ε），不是隐藏真值。

## 结论先读

**没有任何备选模型胜过 V2。V2 仍是领先候选；当前提交（V1/M4）和 `my_model/` 均未改动。**

- **B，充电方向台阶：退出。** 只有 8 次锚点充电越过石墨台阶；约每 5 天一次的 CCCV 充电起点在满充以下约 21 Ah，位于台阶之上。
- **D，缺段外推：无改动。** 所有基于速率的规则在类 CK2 伪缺口上都修正过头，按登记的选择规则保留"不外推"，CK2 仍为 +0.67 pp。
- **A，全曲线配准 β：未通过**（MAE 0.242，V2 为 0.216）。配准得到的底部段与每次锚点充电的*起点状态*高度混淆（与起点电压 r = −0.975），无法单独分离出 LAM。
- **C，状态空间融合：未通过**（MAE 0.355）。其结构会让 ε 泄漏进老化速率。不过它证实了温度偏移（δ ≈ 0.2 Ah）和检查后瞬态（约 +0.6 Ah）。
- **E，ε 漂移风险：视检查协议而定，为 0、0.03 或最多 0.5 pp。** 大漂移情景与数据矛盾。生成了只供排行榜检验的变体 `V2_S1`，不推荐使用。
- **F，集成：不适用。** 只有 V2 符合条件。

## 汇总表

代理误差（pp），主台阶检测方法，A4 平滑 2 Ah。MAE 依次对应 δ = ε0 / ε0+0.4 / ε0+0.8；最大误差和 CK2–7 MAE 取 ε0+0.4。

| 模型 | 阶段 | MAE（三个 δ） | 最大 | CK2–7 MAE | PG1 | PG2 | PC5 | PC10 | 接纳门 |
|---|---|---|---|---|---|---|---|---|---|
| M4（V1，已提交） | 基础 | 0.347 / 0.291 / 0.285 | 0.669 | 0.304 | 0.251 | 0.207 | 0.325 | 0.340 | — |
| **V2** | 基础 | **0.272 / 0.216 / 0.210** | 0.669 | **0.216** | 0.251 | 0.207 | 0.302 | 0.340 | 基准 |
| V2 + D1（速率外推） | D | 0.380 / 0.324 / 0.318 | 1.427 | 0.342 | 0.386 | 0.337 | 0.428 | 0.687 | 不通过 |
| V2 + D2（Arrhenius √t + Ah） | D | 0.370 / 0.270 / 0.244 | 1.049 | 0.279 | 0.412 | 0.350 | 0.365 | 0.473 | 不通过 |
| V2_reg（配准 β） | A | 0.298 / 0.242 / 0.236 | 0.669 | 0.246 | 0.251 | 0.207 | 0.312 | 0.340 | 不通过 |
| SS（状态空间，τ 5 天） | C | 0.479 / 0.355 / 0.242 | 0.696 | 0.334 | 0.136 | 0.225 | 0.336 | 0.353 | 不通过 |

表注：

- PG1/PG2：k = 4..7，把第 k−1 月的 45 °C 段截断到第一次 / 第二次深放电之后。PC5/PC10：在检查日前 5 / 10 天截断数据。
- **D3**（锚点 √t 趋势）在 CK2 处无定义，其真实数据 MAE 不含 CK2，不可比较。它在伪情景上表现不错：PG1 0.205、PG2 0.230、PC5 0.229、PC10 0.176。

ε0+0.4 下的逐检查点误差（pp）：

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| M4 | +0.22 | +0.67 | +0.08 | +0.28 | −0.11 | −0.40 | −0.28 |
| V2 | +0.22 | +0.67 | +0.08 | +0.23 | +0.15 | −0.16 | −0.00 |
| V2_reg | +0.22 | +0.67 | +0.08 | +0.35 | +0.22 | −0.10 | +0.05 |
| SS | +0.48 | +0.50 | −0.04 | +0.70 | +0.46 | −0.07 | −0.23 |

## 各阶段发现

**阶段 0，评估框架。** 精确复现 V2：0.216 / 0.669。伪缺口 PG1 让 CK4 的回退误差达到 +0.60 pp，接近 CK2 的 +0.67，可以作为 CK2 问题的合理替身。

**B**（[报告](stage_B/REPORT.md)）。41 次以 CV 结束的充电都是 20.4 A，其中只有检查后的锚点充电起点足够深（≥ 45 Ah）、能越过台阶。适用登记的退出规则，月内没有充电侧通道。

**D**（[报告](stage_D/REPORT.md)）。

- **结果。** D1、D2 在伪缺口上加入 −0.3 至 −0.9 Ah，把误差翻成负值；用在 CK2 上会得到 −1.43 和 −1.05 pp。选择在真实数据运行之前已经提交，保留 D0。
- **原因。** 在被截断的月份里，锚点间容量的变化远小于"速率 × 缺失天数"：一部分损失已经包含在回退差分所捕捉的瞬态中，另一部分被 +0.18 Ah 的温度平移抵消。
- **线索。** 锚点层面的 √t 趋势（D3）对伪截断和留一锚点的情形有帮助，这与数据削减评估有关；但 CK2 之前只有一个 25 °C 锚点，它帮不上 CK2。

**A**（[报告](stage_A/REPORT.md)）。

- **可辨识性。** 配准参数大多可辨识：底部 60 %、顶部 85 % 的锚点-电芯组合。
- **起点状态问题。** CK3 之后的锚点起点静置电压更低（2.907 V/芯），配准出的底部段长了 0.65 Ah。在各锚点之间，Δ底部跟随起点电压（r = −0.975），所以底部段测的不是 LAM_NE，β_reg（0.86–1.38）因此有偏。
- **未发现 Q_fc 与起点状态的线性关联**（r = 0.04，7 个锚点）。这个小样本诊断既不能证明 Q_fc 等于隐藏 C/20 容量，也不能排除起点状态效应。

**C**（[报告](stage_C/REPORT.md)）。

- **拟合出的结构。** δ 拟合为 0.15–0.22 Ah，检查后瞬态为 +0.5 至 +0.8 Ah，独立证实了 V2 所依据的结构。
- **失败原因。**
  - ε 泄漏进速率：锚点 0 固定，而 25 °C 锚点随 ε 移动。
  - 一条带指数瞬态的月内轨迹，在 CK4/CK5 上不如 V2 的同相位差分。
  - 预测标准差偏小（71 % 的误差落在 2 倍标准差以内）。
- **看到但不能宣称的变体。** τ = 8 天时 MAE 为 0.243，CK2 为 +0.04。

**E**（[报告](stage_E/REPORT.md)）。

- **S2，单芯限顶的检查满充：** ε 漂移 ≤ 0.03 pp。
- **S1，起点状态不抵消：** 漂移 0.26–0.51 pp。取 ΔV = 0.05 V 时它复现了 ε0（0.285 对 0.288 Ah）和 25 °C 偏置（0.71 对 0.69 Ah），但与阶段 A 的诊断不太相符：没有发现 Q_fc 与起点状态的关联。
- **`V2_S1`。** 这个只供排行榜检验的变体，在 CK4–CK7 上与 V2 相差 −0.39 至 +0.34 pp。没有检查协议信息之前，不要提交它。

**F**（[报告](stage_F/REPORT.md)）。不适用，只有 V2 符合条件。

## 建议

1. **继续以 V2 为领先候选。** 是否把它接入 `my_model/`（取代 V1）仍由你决定。本轮没有改变这一对比：代理 MAE 为 V2 0.216，V1 0.291 pp。
2. **把 CK2（+0.67 pp）视为已公开数据修不好的下限。** 测试过的每种外推都让它变得更糟。
3. **真实分数最大的风险是检查协议（阶段 E），不是月内模型。** 如果主办方能说明 C/20 放电与下一次运行充电之间发生了什么，就能在 S0（无漂移）和 S1（最多 0.5 pp）之间作出判断。
4. **留给未来预登记轮次的线索**（本轮都不能宣称为改进）：
   - 给锚点 0 单独偏置、τ ≈ 8 天的状态空间模型；
   - 做起点状态修正的配准 β；
   - 把锚点 √t 趋势作为缺少近期数据时的回退（数据削减评估）。

## 与 prompt 的偏差及独立审查

运行期间，另一个会话在本分支上做了独立审查（`notes/INDEPENDENT_REVIEW.md`、`stage_0/`、`*_independent_*`）。以下列出其指出的问题和其他偏差，一项都不隐瞒：

1. **阶段 D 的顺序。** CK2 处的 PC5/PC10 与真实 CK2 截断数据相同，所以 D1/D2 在 CK2 上的结果在选择提交之前已经算出（在 `run_select.py` 中），违反了 prompt 的顺序规则。选择只用了 PG1 + PG2，并保留了 D0。
2. **阶段 D 的 D2 公式。** prompt 要求台阶观测经 β 换算，登记的实现却用了 M4 的 β = 1 台阶变化；缺段吞吐量用的是可见数据的速率（CK2 时看不到缺段后的计数器跳变）。因此 D2 并非严格按 prompt 的公式执行。D2 本来也没有被选中。
3. **阶段 E 的模型。** prompt 要求用各芯 CK0 曲线做逐芯映射，本次运行实现的是 S0–S2 机理情景。独立会话为所要求的逐芯映射登记了补充协议（`stage_E/required_mapping_protocol.json`），其结果不在本报告之内。
4. **措辞。** 独立审查把阶段 A 报告中关于 Q_fc 与起点状态的部分说法改得更谨慎，本报告采用了更谨慎的措辞。
5. **候选类检查。** 本次运行没有生成候选类，因此从未用到 G-impl。审查指出，逐位一致检查必须比较精确的浮点值，而不是舍入后的输出。

以上各点都不改变主要结论：没有备选方案通过相对 V2 的接纳门。

## 风险与局限

- **曝光。** 每个代理值在本轮之前都已知；伪情景复用了相同的月份，也不是独立检验。
- **ε 和检查后回弹。** 与 V1/V2 相同，只能靠排行榜检验。
- **单一电池组。**
- **非本次运行产生的文件。** 约 00:21 出现了非本次运行产生的文件：`src/statespace.py` 中 4 行元数据，以及 `stage_C/run_independent_diagnostics.py` 和 `stage_C/outputs/C_independent_*`。它们不改变任何预测，本次运行没有改动也没有提交它们（见 `notes/DECISIONS.md` 的 DX.1）。

## 复现

```bash
cd research/phase2_round3_models_20261014
python3 stage0_reproduce.py
python3 stage_B/audit_coverage.py
python3 stage_D/run_select.py && python3 stage_D/run_eval.py
python3 stage_A/run_a.py && python3 stage_A/explore_start_state.py
python3 stage_C/run_c.py
python3 stage_E/run_e.py
```

- **环境：** Python 3.13（numpy 2.4，pandas 3.0）。完整运行不到 2 分钟；提取结果缓存在 `cache/`（git 忽略）。
- **原样复用的代码：**
  - `research/phase2_anchor_step_20261013/src/events.py`
  - `research/phase2_v2_phase_matched_20261013/src/v2.py`
- **没有候选类**：没有模型通过接纳门，因此没有生成。
