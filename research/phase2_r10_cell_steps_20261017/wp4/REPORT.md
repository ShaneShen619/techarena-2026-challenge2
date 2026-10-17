<a id="en"></a>

# WP4 — Combination and candidate class

> **Language:** English · [中文](#zh)

**Result: the final candidate is A3. A3 takes each cell's step as the median over the 6 detection variants, then the median over the 4 cells. Its candidate class passes every check. It is not wired.** Protocol [protocol.json](protocol.json) was committed in `3d79b52` before evaluation.

**Combination.**
- The registered combination A → C → B feeds A3's per-cell locations to B3's combination. C is absent because WP3 exited.
- By construction it is the same predictor as WP2's B3: predictions are identical to < 1e-12 Ah ([outputs/wp4_decision.json](outputs/wp4_decision.json)). It passes, but its causal mean of 0.1515 is not lower than A3's 0.1470.
- By the final rule the candidate is therefore **A3** ([run_wp4.py](run_wp4.py)).

**Candidate class** [candidate_model/model_template.py](candidate_model/model_template.py).
- It is a copy of the submitted `5cd305c` class with one change: `_step_depths` returns the robust step value `_robust_step`, which re-implements the 6 detection variants with numpy only (dV/dQ peak and IR correction included).
- Which programs are used, the branches, β, the √t branch and every constant are unchanged.

| Check | Result |
|---|---|
| G_impl: class vs research A3, per checkup | 1.4e-14 pp unrounded; ≤ 0.0005 pp after the package's 3-decimal rounding ([outputs/wp4_candidate_checks.json](outputs/wp4_candidate_checks.json)) |
| G_causal: future rows replaced by noise | identical at all 8 checkups |
| G_causal: fit on CK1-cut data | identical |
| Package: Python 3.11.14, numpy 2.4.6, pandas 3.0.6, `validate_submission.py` | PASSED ([outputs/wp4_package_check.log](outputs/wp4_package_check.log)) |
| Full `run_model.py` train + test | 12 s |

**SOH at Δ 0.4 (% of 102 Ah)** ([outputs/wp4_soh_sub_vs_a3.csv](outputs/wp4_soh_sub_vs_a3.csv)):

| | CK0 | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|---|
| SUB | 98.441 | 95.992 | 94.507 | 93.541 | 92.811 | 92.081 | 91.331 | 90.821 |
| A3 | 98.441 | 95.984 | 94.507 | 93.600 | 92.821 | 92.015 | 91.426 | 90.765 |
| change (pp) | 0 | −0.008 | 0 | +0.060 | +0.010 | −0.066 | +0.095 | −0.056 |

Every change is below 0.1 pp. To wire A3, replace `TechArena_Challenge2_Team_Package/my_model/model_template.py` with the candidate file and update `EXPECTED_SOH` to the A3 row. That decision is the user's.

---

<a id="zh"></a>

# WP4——组合与候选模型类

> **语言：** [English](#en) · 中文

**结论：最终候选为 A3。A3 的做法是：每个电芯的台阶位置先在 6 种检测变体上取中位数，再对 4 个电芯取中位数。它的候选模型类通过了全部检查，但没有接入提交。** 协议在评估前已提交（`3d79b52`）。

**组合。**
- 登记的组合（A → C → B）把 A3 的单体位置交给 B3 的合并方式；WP3 已退出，所以没有 C。
- 在构造上，它与 WP2 的 B3 是同一个预测器，预测完全相同（< 1e-12 Ah）。它通过了检验，但因果指标 0.1515 并不比 A3 的 0.1470 低。
- 因此按最终规则，候选为 **A3**。

**候选模型类。**
- 它是提交版 `5cd305c` 类的副本，只改了一处：每次深放的台阶值换成稳健值，并在包内只用 numpy 重新实现了 6 种检测变体（包括 dV/dQ 峰和 IR 修正）。
- 使用哪些程序、分支、β、√t 分支和所有常数都不变。

**检查结果：**
- 与研究实现相差 1.4e-14 pp；
- 未来数据换成噪声后，8 个检查点的输出都不变；用截至 CK1 的数据拟合，输出也不变；
- Python 3.11 下 `validate_submission.py` 通过；
- 完整运行耗时 12 s。

**SOH 变化**（见英文表格）：CK3 +0.060、CK5 −0.066、CK6 +0.095、CK7 −0.056 pp，其余几乎不变，全部小于 0.1 pp。如要接入，需要替换提交包里的 `model_template.py`，并把 `EXPECTED_SOH` 更新为 A3 这一行。是否接入由你决定。
