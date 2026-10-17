<a id="en"></a>

# WP1 — Case table

> **Language:** English · [中文](#zh)

**Result.** [../outputs/table_cases.csv](../outputs/table_cases.csv) has 423 rows: 47 cases × 3 Δ × 3 models (SUB = T_main, V2_sqrt = V2 + calendar √t, V2). [../outputs/table_cases_wide.csv](../outputs/table_cases_wide.csv) has 47 rows (SUB, Δ = 0.4). Script: [run_wp1.py](run_wp1.py), with the instrumented replay in [../src/internals.py](../src/internals.py). A rerun is byte-identical.

**Decomposition.** err_Ah = offset_part + inc_resid, where inc_resid = increment_pred − (Q_fc,k − Q_fc,anchor used).
- **Assertion passed** ([outputs/wp1_offset_assertion.csv](outputs/wp1_offset_assertion.csv)). offset_part depends only on (branch family, Δ, anchor is the 45 °C anchor 0), with spread ≤ 1.4e-14 Ah (tolerance 1e-9).
  - It is 0 in every case except fallback from the 45 °C anchor 0, where the anchor term is Q_CK0 = 100.41 Ah and offset_part = −Δ. These are real CK1 for all three models, n = 3 across the Δ values.
  - So inc_resid is the whole error except at CK1, where err = inc_resid − Δ.
- **Replay check.** For every row, Q_pred from the replay equals the model's own output (< 1e-9 Ah), and the anchor's Q_fc equals the full-data anchor charge. SUB's err_pp equals WP0's to 1e-16 pp, with the same branches.

**Per-branch summary of signed inc_resid (Δ = 0.4; inc_resid does not depend on Δ)** ([outputs/wp1_branch_summary.csv](outputs/wp1_branch_summary.csv)). "causal" pools all non-real scenarios, which include near-duplicates (PC10 = PC10_all, and PG1/PG2/PC10 at the same k share most sqrt_gap anchors), so counts overstate independence.

| model | branch | set | n | mean Ah | median Ah | MAE Ah | MAE pp |
|---|---|---|---|---|---|---|---|
| SUB | fallback | real | 2 | +0.351 | +0.351 | 0.351 | 0.344 |
| SUB | phase | real | 4 | +0.054 | +0.075 | 0.139 | 0.136 |
| SUB | sqrt_gap | real | 1 | +0.040 | +0.040 | 0.040 | 0.039 |
| SUB | fallback | causal | 8 | +0.005 | +0.022 | 0.217 | 0.213 |
| SUB | phase | causal | 8 | +0.062 | +0.097 | 0.226 | 0.221 |
| SUB | sqrt_gap | causal | 24 | −0.045 | −0.020 | 0.111 | 0.109 |
| V2_sqrt | sqrt_gap | real / causal | 1 / 24 | −0.018 / −0.071 | −0.018 / −0.049 | 0.018 / 0.115 | 0.018 / 0.113 |
| V2 | fallback | real / causal | 3 / 32 | +0.462 / +0.185 | +0.621 / +0.135 | 0.462 / 0.285 | 0.453 / 0.280 |

V2_sqrt equals SUB outside sqrt_gap; V2 equals SUB in phase cases. Real SUB inc_resid per checkup (Ah): CK1 +0.621, CK2 +0.040, CK3 +0.081, CK4 +0.232, CK5 +0.153, CK6 −0.166, CK7 −0.004. The table is not sliced here; slicing is WP5's registered job.

**Columns.** Identity, prediction, decomposition, branch internals (β, its raw LS slope, S = Σx², shrinkage weight S/(τ+S); x, E/d/n/r of the current and previous month-end 45 °C step; gap days; √t coefficient a and effective days), the events used (`ev_*`, as CV-end timestamps), flags and context (days and 45 °C-equivalent days anchor→CK, cumulative fade at the anchor, integrated discharge throughput since the anchor, 45 °C time share). See `DATA_DICTIONARY.md`. `uses_first_post_anchor_program` is true for fallback cases with ≥ 2 programs after the anchor (D1.1).

---

<a id="zh"></a>

# WP1——案例表

> **语言：** [English](#en) · 中文

**结果。** [../outputs/table_cases.csv](../outputs/table_cases.csv) 共 423 行：47 个案例 × 3 个 Δ × 3 个模型（SUB = T_main、V2_sqrt = V2 + 日历时间 √t、V2）。[../outputs/table_cases_wide.csv](../outputs/table_cases_wide.csv) 共 47 行（SUB，Δ = 0.4）。脚本 [run_wp1.py](run_wp1.py)，逐步重放见 [../src/internals.py](../src/internals.py)；重跑结果逐字节相同。

**误差分解。** err_Ah = offset_part + inc_resid，其中 inc_resid = increment_pred − (Q_fc,k − 所用锚点的 Q_fc)。
- **断言通过**（[outputs/wp1_offset_assertion.csv](outputs/wp1_offset_assertion.csv)）。offset_part 只取决于（分支族、Δ、是否为 45 °C 的锚点 0），离散度 ≤ 1.4e-14 Ah（容差 1e-9）。
  - 除了从 45 °C 锚点 0 出发的 fallback，其余案例 offset_part 都为 0。这类案例的锚点项为 Q_CK0 = 100.41 Ah，offset_part = −Δ；它们是三个模型的真实 CK1，在各 Δ 下共 n = 3。
  - 因此除 CK1 外，inc_resid 就是全部误差；CK1 上 err = inc_resid − Δ。
- **重放检查。** 每一行重放得到的 Q_pred 都等于模型自身输出（< 1e-9 Ah），所用锚点的 Q_fc 等于全量数据中的锚点充电量。SUB 的 err_pp 与 WP0 相差 1e-16 pp，分支相同。

**按分支汇总的带符号 inc_resid**（Δ = 0.4；inc_resid 与 Δ 无关），数值见英文表格。"causal" 汇总了所有非真实场景，其中有近似重复（PC10 = PC10_all；同一 k 下 PG1/PG2/PC10 的 sqrt_gap 大多用同样的锚点），所以样本数高估了独立性。真实场景 SUB 各检查点 inc_resid（Ah）：CK1 +0.621、CK2 +0.040、CK3 +0.081、CK4 +0.232、CK5 +0.153、CK6 −0.166、CK7 −0.004。本 WP 不做切片，切片是 WP5 登记后的工作。

**列。** 标识、预测、分解、分支内部量（β、原始最小二乘斜率、S = Σx²、收缩权重 S/(τ+S)；x、当月和上月月末 45 °C 台阶的 E/d/n/r；缺口天数；√t 系数 a 和有效天数）、所用事件（`ev_*`，以 CV 结束时间戳表示）、标志和上下文（锚点到 CK 的天数及 45 °C 等效天数、锚点处累计衰减、锚点以来积分得到的放电吞吐量、45 °C 时间占比）。详见 `DATA_DICTIONARY.md`。`uses_first_post_anchor_program` 在锚点后至少有 2 个程序的 fallback 案例上为真（D1.1）。
