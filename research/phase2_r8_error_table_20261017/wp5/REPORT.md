<a id="en"></a>

# WP5 — Registered slicing and worst-20 % dossier

> **Language:** English · [中文](#zh)

**Registration.** [protocol.json](protocol.json) (SHA256 in [protocol.sha256](protocol.sha256)) was committed in `16168a1`, before any residual was grouped by a slice. The exposure before registration is recorded in D2.2: the pack-level R_anc/R_seg per event, the per-unit summary of R_cell, and WP1's per-branch summary. Scripts: [run_wp5.py](run_wp5.py) (statistics) and [plot_wp5.py](plot_wp5.py) (figures, dossier). Outputs: [outputs/slice_summary.csv](outputs/slice_summary.csv), [outputs/wp5_extra.json](outputs/wp5_extra.json), [outputs/h1_counterfactuals_diagnostic_only.csv](outputs/h1_counterfactuals_diagnostic_only.csv), [figures/](figures/), [dossier/](dossier/). A rerun gives byte-identical CSV/JSON.

## Conclusions first

1. **The largest and most robust pattern is a step-depth scaling the model handles only in the phase branch.**
   - The graphite-step depth moves **0.745 Ah per Ah of anchor fade** (WP2 free-slope fit, 90 % CI 0.674–0.765).
   - The phase branch corrects for this with β (1.06–1.51). The fallback uses β = 1, so it under-predicts the loss whenever the increment is large.
   - This, and **not** the first-program offset, explains the fallback errors. H1 is not systematic, and dividing the fallback increment by b moves real CK1 from +0.62 to −0.23 Ah and CK3 from +0.08 to −0.24 Ah (diagnostic only).
   - The b = 1 residual R_anc is dominated by this artifact, so all event conclusions use the registered secondary R_anc_b.
2. **Cell heterogeneity is systematic (H6), but the per-cell sign part was seen before registration.**
   - Cell 1 sits 0.36 Ah shallower than the cell median, cell 3 0.25 Ah deeper, cell 2 0.13 Ah deeper and cell 4 0.13 Ah shallower, in 8 of 8 months.
   - The spread of the four cell depths grows from 0.56 to 0.72 Ah (m0–2 → m6–7, +0.16 Ah, CI [0.06, 0.21]).
   - The weakest cell at maximum depth stays cell 1.
3. **The case residual trends with fade (H4).**
   - inc_resid falls by 0.078 Ah per Ah of fade (CI [−0.137, −0.023]; −0.067 [−0.163, −0.004] without CK1). The CI contains −0.031, so the registered label applies: **"indistinguishable from ε drift, invisible to proxies"**.
   - Caveat: inc_resid is measured against Q_fc, so this trend *is* seen by the Q_fc-based proxies. The label only says that its size equals the plausible ε drift.
   - The binned effect (−0.71 Ah, "systematic") rests on a single case in the 0–3 % bin (real CK1).
4. **No support for** a temperature-deviation effect (H3), a resistance mechanism (H7), anchor start-state or CV cut-off corrections (H9), or step-quality effects beyond month 0 (H5 inconclusive). **H10 is void by construction** (WP4).
5. **The worst-20 % sets are concentrated in two places.**
   - Worst events: month 0 (the 45 °C campaign-start segment) holds 6 of 8 by |R_anc| (Fisher p = 0.008) and 4 of 5 by |R_seg|.
   - Worst cases: fallback CK1, the cold-start fallbacks CS CK6/CK7, PC5 CK4, and the CK6 one-month extrapolation (−0.32 Ah, the same in 5 scenarios). No case category is enriched (all Fisher p ≥ 0.17).

## Verdict per hypothesis

Threshold 0.10 Ah (H10b: 5 mV). "Sign" = within-block or block-agreement share. CI = 90 % block bootstrap (months or checkups as blocks). p = permutation within strata, reported but not used in the verdict.

| H | Residual / subset | Effect (Ah) | 90 % CI | Sign | p | Verdict | Reading |
|---|---|---|---|---|---|---|---|
| H1 | inc_resid, all 47 cases: first-program cases − others | +0.084 | [−0.112, 0.238] | 3/5 | 1.00* | not systematic | expected −0.4…−0.8; observed sign opposite and small |
| H2 | R_seg, 45 °C direct-switch, 0–2 d − >5 d | +0.023 | [0.019, 0.027] | 3/5 | 0.50 | inconclusive | a real but tiny transient (< 0.10 Ah) |
| H2 | R_anc_b, same | +0.047 | [−0.084, 0.160] | 5/5 | 0.56 | not systematic | |
| H2 | R_anc_b, 25 °C (all 0–2 d events are first programs) | +0.471 | [0.401, 0.560] | 6/6 | 0.001 | systematic | the known first-program offset, re-detected; not new |
| H3 | R_anc_b, high − low dT tercile | +0.016 | [−0.177, 0.176] | 5/7 | 0.88 | not systematic | (R_anc: −1.24, inconclusive; confounded by month trend × b) |
| H4 | inc_resid, >6 % − 0–3 % fade | −0.714 | [−0.924, −0.587] | 5/6 | 0.0002 | systematic | 0–3 % bin = real CK1 only; slope −0.078 Ah/Ah → ε-drift label |
| H4 | R_anc_b events, >6 % − 0–3 % | −0.205 | [−0.253, −0.129] | 6/7 | 0.13 | systematic | 0–3 % bin = month 0 only; slope −0.026 [−0.058, 0.084] → ε-drift label |
| H4 | R_anc (b = 1) events | +1.800 | [1.658, 1.928] | 2/7 | 0.0002 | systematic (opposite sign) | slope +0.305 = 1 − b artifact (seen) |
| H5 | \|R_seg\| low − mid+high sharpness, pack (cells) | +0.196 (+0.171) | [−0.020, 0.327] ([−0.065, 0.304]) | 4/6 | 0.004 (0.0002) | inconclusive | low tercile sits mostly in month 0; Fisher enrichment p = 0.023 (pack), 1.8e-6 (cells, pseudo-replicated) |
| H6a | R_cell per cell (seen) | c1 −0.356, c2 +0.131, c3 +0.246, c4 −0.128 | all exclude 0 | 8/8 each | 0.008 | systematic | persistent per-cell offsets |
| H6b | spread of cell depths, m6–7 − m0–2 | +0.162 | [0.062, 0.206] | 6/8 | 0.0002 | systematic | spread grows 0.56 → 0.72 Ah |
| H6c | weakest cell at max depth | — | — | — | — | does not change | cell 1 is modal in m0–2 and m6–7 |
| H7 | Spearman(R, anchor 1..7); (CV Ah, R); (−dQ_cut6A, R) | ρ 0.61; 0.61; 0.50 | — | — | 0.17; 0.17; 0.27 (exact) | inconclusive | R quantised (0.049 mΩ); 25 °C events +0.0003 mΩ/day, 45 °C −0.0009 mΩ/day |
| H8 | \|inc_resid\| by gap days, >10 − 0–5 | −0.113 | [−0.224, −0.044] | 1/5 | 0.59 | systematic (opposite sign) | the >10 d bin is entirely sqrt_gap: a branch comparison |
| H8 | \|inc_resid\| by days anchor→CK, >30 − 0–25 | −0.452 | [−0.538, −0.318] | 3/6 | 0.08 | inconclusive | the 0–25 d bin is real CK1 only |
| H9 | variance ratio of month-to-month ΔQ_fc scatter | 6 A cut 0.96; +r_half 3.05; fitted LOO 1.18 | — | — | 0.66 | not systematic | scatter SD 0.142 Ah is not reduced by either correction |
| H10 | R_cyc_slot top-of-charge Ah, first block after anchor − other | −0.521 | [−0.794, −0.249] | 0/8 | 0.006 | systematic (opposite sign) — **artifact** | medians 0.000 in both groups; complete blocks: \|R\| median 0.0008 Ah, max 0.12 Ah (exploratory-unregistered) |
| H10b | R_cyc_slot V_bottom, first block after anchor − other | +6.5 mV | [1.4, 12.3] mV | 2/8 | 0.05 | systematic (opposite sign) | loaded bottom voltage is about 6 mV higher in the first block after an anchor, not lower |

\* H1's permutation p is degenerate: the registered strata (branch) hold the flag constant (D5.2).

## H1 diagnostics (diagnostic-only, never scored)

The table gives inc_resid (Ah) for the 10 first-program cases; the full table is [outputs/h1_counterfactuals_diagnostic_only.csv](outputs/h1_counterfactuals_diagnostic_only.csv).

| case | original | (a) after[1] | (b) after[0] − 3c offset | (c) increment / b |
|---|---|---|---|---|
| real CK1 | +0.621 | +1.965 | +1.455 | −0.234 |
| real CK3 (= CS CK3) | +0.081 | +0.630 | +0.630 | −0.243 |
| PC5 CK3 | +0.263 | +0.811 | +0.811 | +0.001 |
| CS CK4 / CK5 / CK6 / CK7 | +0.284 / −0.114 / −0.411 / −0.286 | +0.700 / +0.478 / +0.109 / +0.198 | +0.700 / +0.478 / −0.057 / −0.075 | +0.075 / −0.380 / −0.704 / −0.618 |
| PG2 CK7 | −0.037 | +0.447 | +0.174 | −0.283 |

Removing the first-program offset makes the fallback **worse**. The offset partly cancels the β = 1 shortfall, so it is not a cause of error to strip. Scaling by 1/b fixes the early months (CK1, CK3) but overshoots in the cold-start months 5–7 (CS), where increments are smaller and noisier.

## Worst-20 % dossier

[dossier/worst_sets.csv](dossier/worst_sets.csv) lists the sets; [dossier/enrichment.csv](dossier/enrichment.csv) gives two-sided Fisher tests per category level. There is one panel per item.
- **Cases (10, by |inc_resid|).** real CK1 +0.62 (fallback from the 45 °C anchor); CS CK6 −0.41 and CS CK7 −0.29 (cold-start fallback); PC5/PC5_all CK4 +0.33 (phase); and the CK6 one-month extrapolation −0.32 (sqrt_gap, the same case in PG1/PG2/PC10/PC10_all/CSE). No category is enriched.
- **Events by |R_anc| (8 of 40).** E01–E04 and E00 (month 0, 45 °C campaign start), E06 (month 1), E32 and E39 (late 25 °C first programs). Enriched: campaign_start (5/8 vs 5/40, p < 0.001), month group m0–2 (p = 0.008), low sharpness (8/8 vs 23/40, p = 0.013).
- **Events by |R_seg| (5 of 25).** E00, E04, E02, E01 (month 0) and E18. Enriched: campaign_start (p = 0.002), low sharpness (p = 0.023).

## Figures

- [figures/events_R_seg_vs_slices.png](figures/events_R_seg_vs_slices.png), [events_R_anc_vs_slices.png](figures/events_R_anc_vs_slices.png), [events_R_anc_b_vs_slices.png](figures/events_R_anc_b_vs_slices.png): each event residual against each registered slice variable, coloured by set point, labelled by month.
- [figures/cases_inc_resid_vs_slices.png](figures/cases_inc_resid_vs_slices.png) and [figures/cases_inc_resid_by_branch_bars.png](figures/cases_inc_resid_by_branch_bars.png): the per-branch inc_resid bars for every scenario.
- [figures/events_R_cell_by_cell.png](figures/events_R_cell_by_cell.png), [figures/cycles_R_cyc_slot.png](figures/cycles_R_cyc_slot.png).

Decisions D5.1–D5.4 are in [../notes/DECISIONS.md](../notes/DECISIONS.md).

---

<a id="zh"></a>

# WP5——登记切片与最差 20 % 档案

> **语言：** [English](#en) · 中文

**登记。** [protocol.json](protocol.json)（SHA256 见 [protocol.sha256](protocol.sha256)）在提交 `16168a1` 中登记，早于任何按切片对残差的分组。登记前的曝光记于 D2.2：每个事件的 pack 级 R_anc/R_seg、R_cell 按单元的汇总，以及 WP1 按分支的汇总。脚本：[run_wp5.py](run_wp5.py)（统计）和 [plot_wp5.py](plot_wp5.py)（图、档案）。重跑时 CSV/JSON 逐字节相同。

## 结论先行

1. **最大、最稳健的模式是台阶深度的比例关系，模型只在 phase 分支中处理了它。**
   - 石墨台阶深度随锚点衰减每 Ah 只移动 **0.745 Ah**（WP2 自由斜率拟合，90 % CI 0.674–0.765）。
   - phase 分支用 β（1.06–1.51）修正了这一点。fallback 用 β = 1，所以增量大时会低估容量损失。
   - 解释 fallback 误差的是这一点，**而不是**首个程序偏移。H1 不成立；把 fallback 增量除以 b，真实 CK1 从 +0.62 变为 −0.23 Ah，CK3 从 +0.08 变为 −0.24 Ah（仅诊断）。
   - b = 1 的残差 R_anc 被这一伪影主导，因此所有事件结论都使用登记的次要残差 R_anc_b。
2. **单体异质性是系统性的（H6），但单体符号部分在登记前已被看到。**
   - 单体 1 比单体中位数浅 0.36 Ah，单体 3 深 0.25 Ah，单体 2 深 0.13 Ah，单体 4 浅 0.13 Ah，8 个月中 8 个月如此。
   - 四个单体深度的离散从 0.56 增至 0.72 Ah（m0–2 → m6–7，+0.16 Ah，CI [0.06, 0.21]）。
   - 最大深度处的最弱单体一直是单体 1。
3. **案例残差随衰减呈趋势（H4）。**
   - inc_resid 每 Ah 衰减下降 0.078 Ah（CI [−0.137, −0.023]；去掉 CK1 为 −0.067 [−0.163, −0.004]）。CI 包含 −0.031，因此按登记规则标注：**"与 ε 漂移不可区分，代理不可见"**。
   - 注意：inc_resid 是以 Q_fc 为参照的，所以这一趋势*可以*被基于 Q_fc 的代理看到。该标注只说明它的大小与合理的 ε 漂移相当。
   - 分箱效应（−0.71 Ah，"系统性"）依赖 0–3 % 箱中唯一的案例（真实 CK1）。
4. **不支持**以下效应：温度偏差（H3）、内阻机制（H7）、锚点起始状态或 CV 截止修正（H9）、月份 0 之外的台阶质量效应（H5 不确定）。**H10 按构造无效**（WP4）。
5. **最差 20 % 集中在两处。**
   - 最差事件：月份 0（45 °C 试验开始段）占 |R_anc| 最差 8 个中的 6 个（Fisher p = 0.008），以及 |R_seg| 最差 5 个中的 4 个。
   - 最差案例：fallback CK1、冷启动 fallback CS CK6/CK7、PC5 CK4，以及 CK6 的一个月外推（−0.32 Ah，在 5 个场景中相同）。没有案例类别富集（所有 Fisher p ≥ 0.17）。

## 各假设结论

各假设的效应、CI、符号比例、p 和结论见英文表格。要点：
- H1 不成立（+0.084 Ah，与预期相反且很小）。
- H2：45 °C 时 R_seg 有真实但很小的瞬态（+0.023 Ah，不确定），R_anc_b 不成立；25 °C 的"系统性"结果是已知的首个程序偏移被再次检出。
- H3 不成立（R_anc_b +0.016）。
- H4 带 ε 漂移标注（见上）。
- H5 不确定（低尖锐度三分位集中在月份 0）。
- H6a/H6b 系统性，H6c 最弱单体不变。
- H7 不确定（内阻量化，没有一致趋势）。
- H8：缺口天数为"系统性（反号）"，但 >10 d 箱全是 sqrt_gap，实为分支比较；锚点到 CK 天数不确定。
- H9 不成立（方差比 0.96 / 3.05 / 1.18）。
- H10 的"系统性（反号）"是不完整周期中槽位错位造成的**伪影**（两组中位数都为 0.000）；H10b：锚点后首个周期的带载底部电压高约 6.5 mV（与预期方向相反）。

H1 诊断反事实（仅诊断，不计分）：去掉首个程序偏移会让 fallback **更差**，因为该偏移部分抵消了 β = 1 的不足；按 1/b 缩放修好了早期月份（CK1、CK3），但在冷启动的第 5–7 个月过度修正。

档案、富集表和图的位置见英文部分。决策 D5.1–D5.4 见 [../notes/DECISIONS.md](../notes/DECISIONS.md)。
