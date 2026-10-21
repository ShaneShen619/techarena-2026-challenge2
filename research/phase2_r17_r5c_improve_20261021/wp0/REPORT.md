<a id="en"></a>

# WP0 — Setup, reproduction, facts

> **Language:** English · [中文](#zh)

## Conclusions first

1. **The baseline reproduces.** REF, R3_T and V2 match the prompt's §2 rows within 0.0005 pp (real/pseudo/cold MAE and all seven CK errors at Δ = 0.4). The round-17 code paths (`stress_table17`, `LawFit17` at default settings) equal r5c exactly: 35/35 tables are identical, and the largest prediction difference is 0.0 pp over 19 cases. SUB (model `A3` in the round-10 CSV) reproduces its expected SOH, and its 35 causal + real cases match runner5c's case set one-to-one, with identical proxies.
2. **Noise floor.** The median SD of REF's predicted SOH across the six step variants is 0.055 pp over 28 causal cases. So **T_move = 0.110 pp** and **δ = 0.0276 pp** (`outputs/noise.json`). δ is five times larger than the 0.005 pp margins earlier rounds selected on.
3. **F1: most "checkup" rows are real checkups, and the switches are small.** At the real CK7 cut, true checkups total 28.9 days (6.3 % of R3_T's Arrhenius-weighted τ). The intra-month chamber switches are five gaps of 7–25 h, 3.1 days in all (0.7 % of τ). The missing segment 3 (`seg_gap`) carries 11.3 % of τ.
   - A day-resolution fix was needed. CK dates are calendar days at 00:00, and three 45 °C segments end later on the CK day itself. A strict "CK inside (t0, t1]" test labels those three real checkups as switches (D0.3).
   - So the switch fix (B0) can only move predictions a little. The 10-21 "no calendar ageing at checkups" test mostly removed **true** checkups.
4. **F2: the operating SOC is the same every month.** At 25 °C the monthly time-weighted mean SOC is 0.571–0.592 (SD 0.008). At 45 °C it is 0.595–0.625 over the full segments (two fragments of < 1 day excluded). The 10–90 % range is about 0.30–0.87 everywhere. An SOC weight on *operation* time is therefore a constant factor that A_cal absorbs, as the prompt anticipated.
   - The segment-end SOC, which is the switch SOC and the checkup entry SOC, varies widely: 0.18–0.89. Pack voltage there is 12.9–13.4 V. "Enters charged" in the prompt should read "enters at a mid SOC". 13.1–13.3 V is on the LFP plateau, not full.
5. **F3: break-in is small at the MAP and large at the prior.** Contributions to the predicted loss up to CK7 at the real-CK7 MAP:

   | Term | Ah | pp |
   |---|---|---|
   | Break-in (A_b = e^0.74 = 2.1 Ah) | 1.99 | 1.95 |
   | Calendar | 5.58 | 5.47 |
   | Cycle | 0.40 | 0.40 |

   At the prior mean, break-in is 6.07 Ah, calendar 4.96 Ah and cycle 0.52 Ah. The cycle term adds a near-constant ~0.06 Ah per month.
   - Monthly break-in at the MAP: 0.67, 0.55, 0.36, 0.20, 0.12, 0.08, 0.05 Ah (CK1…CK7). It matters for CK1–CK3 only.
6. **F4: Yagci's 37.3 kJ/mol is an Ea on k.** Yagci 2025 §5 and Fig. 12 fit an Arrhenius plot of the *end-of-test capacity losses* of all 12 cells. The cells were tested over equal durations at 35/50 °C, so this is an activation energy of the loss level, i.e. on k. r5c (via round 5A `fit_prior.py`) applies it to *time* before √, which equals 18.65 kJ/mol on k. That is close to Schimpe's 20.6 by coincidence, not by design.
7. **F5: SUB's clock is half strength, as stated.** `_effective_days` weights hours by exp(20.6 kJ/mol …) and `_sqrt_extrapolation` takes `te ** FADE_EXPONENT` (0.5), so the effective Ea on k is 10.3 kJ/mol. SUB's √t gap branch fires at:
   - real k = 2;
   - PG1 k = 4–7, PG2 k = 4–6;
   - PC10 k = 3–7;
   - CSE k = 3–7.
8. **F6: V2's regime is almost fully determined by the scenario.**

   | Scenario | `phase` | `fallback` |
   |---|---|---|
   | PC5 | 4 | 1 |
   | PG1, PG2, PC10, CS, CSE | 0 | all |
   | real | 4 | 3 |

   Across all causal cases, only **4 are `phase`**, below the 6-case minimum, **so E2 is not run** (registered rule, WP3).
9. **Shared month structure (rule 6).** Mean causal error per k:

   | k | R3_T | V2 | REF | SUB |
   |---|---|---|---|---|
   | 3 | −0.170 | +0.319 | −0.048 | +0.095 |
   | 4 | +0.094 | +0.444 | +0.181 | +0.143 |
   | 5 | −0.013 | +0.128 | +0.022 | −0.015 |
   | 6 | −0.236 | −0.208 | −0.229 | −0.291 |
   | 7 | +0.133 | −0.007 | +0.098 | −0.009 |

   k = 6 is negative for every model. k = 4 is positive for every model.

## Details

- `outputs/wp0_reproduction.json`, `outputs/wp0_base_predictions.csv` (all six step variants, Δ ∈ {0, 0.4, 0.8}).
- `outputs/wp0_facts.json` (F1–F6, equivalence checks, SUB case match, month structure); `outputs/f1_checkup_rows.csv`; `outputs/f2_soc_by_month.csv`; `outputs/f2_segment_last_soc.csv`.
- **F2 SOC series.** Ah below the latest CV end (reset at every `events._cv_ends`; rows before a segment's first CV end use that CV end), divided by the latest visible anchor capacity (Q_CK0 before any). 0 % of rows are NaN.
- **Deviations:** D0.1 (harness copied so its cache stays in this study), D0.2 (`A3` = SUB), D0.3 (day-resolution CK containment). See `notes/DECISIONS.md`.

---

<a id="zh"></a>

# WP0 — 准备、复现、事实

> **语言：** [English](#en) · 中文

## 结论在前

1. **基线复现成功。** REF、R3_T、V2 与 prompt §2 各行相差在 0.0005 pp 以内（Δ = 0.4 时的真实/伪情景/冷启动 MAE 和全部 7 个 CK 误差）。第 17 轮的代码路径（默认设置下的 `stress_table17`、`LawFit17`）与 r5c 完全一致：35/35 张表相同，19 个案例的预测最大差为 0.0 pp。SUB（第 10 轮 CSV 中的模型 `A3`）复现其预期 SOH，它的 35 个因果 + 真实案例与 runner5c 的案例集一一对应，代理值也相同。
2. **噪声底。** REF 预测 SOH 在 6 个台阶变体上的标准差，28 个因果案例的中位数为 0.055 pp。所以 **T_move = 0.110 pp**，**δ = 0.0276 pp**（`outputs/noise.json`）。δ 是之前几轮用来做选择的 0.005 pp 余量的五倍。
3. **F1：大部分"检测期"行确实是检测期，换温箱很短。** 在真实 CK7 截断下，真正的检测期共 28.9 天（占 R3_T 的 Arrhenius 加权 τ 的 6.3%）。月内换温箱是 5 段 7–25 小时的空档，共 3.1 天（占 τ 的 0.7%）。缺失的段 3（`seg_gap`）占 τ 的 11.3%。
   - 需要按"天"判断。CK 日期是 00:00 的日历日，而有三段 45 °C 数据在 CK 当天晚些时候才结束。严格的"CK 落在 (t0, t1] 内"检验会把这三次真实检测标成换温箱（D0.3）。
   - 所以换温箱修正（B0）只能让预测动一点点。10-21 那次"检测期不计日历老化"的测试，去掉的主要是**真实**检测期。
4. **F2：运行 SOC 每个月都一样。** 25 °C 下各月时间加权平均 SOC 为 0.571–0.592（标准差 0.008）；45 °C 下按完整段计为 0.595–0.625（剔除两段不到 1 天的碎片）。各处的 10–90% 区间都约为 0.30–0.87。所以对*运行*时间做 SOC 加权只相当于一个常数因子，会被 A_cal 吸收，与 prompt 的预期一致。
   - 每段结束时的 SOC（即换温箱 SOC 和进入检测时的 SOC）变化很大：0.18–0.89，此时电池组电压 12.9–13.4 V。prompt 里"进入检测时是充好电的"应改为"进入检测时处于中等 SOC"：13.1–13.3 V 在 LFP 平台上，不是满充。
5. **F3：磨合项在 MAP 下很小，在先验下很大。** 真实 CK7 MAP 下各项到 CK7 的预测损失：

   | 项 | Ah | pp |
   |---|---|---|
   | 磨合项（A_b = e^0.74 = 2.1 Ah） | 1.99 | 1.95 |
   | 日历项 | 5.58 | 5.47 |
   | 循环项 | 0.40 | 0.40 |

   先验均值下，磨合项 6.07 Ah、日历项 4.96 Ah、循环项 0.52 Ah。循环项每月贡献几乎恒定，约 0.06 Ah。
   - MAP 下各月的磨合项：0.67、0.55、0.36、0.20、0.12、0.08、0.05 Ah（CK1…CK7），只对 CK1–CK3 有影响。
6. **F4：Yagci 的 37.3 kJ/mol 是加在 k 上的 Ea。** Yagci 2025 §5 和图 12 是对全部 12 只电芯*试验结束时的容量损失*做 Arrhenius 拟合。这些电芯在 35/50 °C 下试验时长相同，所以这是损失水平的活化能，即加在 k 上。r5c（经第 5A 轮的 `fit_prior.py`）把它加在*时间*上再开根号，相当于在 k 上只有 18.65 kJ/mol。它接近 Schimpe 的 20.6 只是巧合，不是有意为之。
7. **F5：SUB 的时钟确实只有一半强度。** `_effective_days` 用 exp(20.6 kJ/mol …) 给每小时加权，`_sqrt_extrapolation` 再取 `te ** FADE_EXPONENT`（0.5），所以在 k 上的等效 Ea 是 10.3 kJ/mol。SUB 的 √t 缺口分支在以下案例触发：
   - 真实 k = 2；
   - PG1 k = 4–7，PG2 k = 4–6；
   - PC10 k = 3–7；
   - CSE k = 3–7。
8. **F6：V2 走哪个分支几乎完全由情景决定。**

   | 情景 | `phase` | `fallback` |
   |---|---|---|
   | PC5 | 4 | 1 |
   | PG1、PG2、PC10、CS、CSE | 0 | 全部 |
   | 真实 | 4 | 3 |

   全部因果案例中**只有 4 个是 `phase`**，低于 6 个的下限，**所以 E2 不运行**（WP3 的登记规则）。
9. **共享的月份结构（规则 6）。** 各 k 的因果平均误差：

   | k | R3_T | V2 | REF | SUB |
   |---|---|---|---|---|
   | 3 | −0.170 | +0.319 | −0.048 | +0.095 |
   | 4 | +0.094 | +0.444 | +0.181 | +0.143 |
   | 5 | −0.013 | +0.128 | +0.022 | −0.015 |
   | 6 | −0.236 | −0.208 | −0.229 | −0.291 |
   | 7 | +0.133 | −0.007 | +0.098 | −0.009 |

   所有模型在 k = 6 都偏负，在 k = 4 都偏正。

## 细节

- `outputs/wp0_reproduction.json`、`outputs/wp0_base_predictions.csv`（全部 6 个台阶变体，Δ ∈ {0, 0.4, 0.8}）。
- `outputs/wp0_facts.json`（F1–F6、等价性检查、SUB 案例对应、月份结构）；`outputs/f1_checkup_rows.csv`；`outputs/f2_soc_by_month.csv`；`outputs/f2_segment_last_soc.csv`。
- **F2 的 SOC 序列。** 相对最近一次 CV 结束点的放出 Ah（在每次 `events._cv_ends` 处归零；一段里第一个 CV 结束点之前的行用该 CV 结束点），除以最近一个可见锚点的容量（之前用 Q_CK0）。NaN 行占 0%。
- **偏离：** D0.1（复制 harness，使其缓存留在本研究内）、D0.2（`A3` = SUB）、D0.3（按天判断 CK 是否落在区间内）。见 `notes/DECISIONS.md`。
