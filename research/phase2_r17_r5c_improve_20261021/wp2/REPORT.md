<a id="en"></a>

# WP2 — Single-factor designs: prediction screen, then paired causal check

> **Language:** English · [中文](#zh)

Protocol: `protocol.json` (sha `701ec6ef…`), committed in 87ed904, before any WP2 output. Selection used causal cases only; the real scenario was not run. The real-k rows below are *predictions* (ΔSOH), not errors.

## Conclusions first

1. **No design passes.** Four of the six main designs are **inert**: their prediction changes stay below the noise floor (T_move = 0.110 pp).

   | Design | S_causal (pp) | S_real (pp, at k) | Moves? |
   |---|---|---|---|
   | B0 switch fix | 0.008 | 0.009 (k3) | no |
   | S SOC-weighted calendar clock | 0.022 | 0.022 (k5) | no |
   | C calendar Ea on k (41.2 on time) | 0.007 | 0.013 (k2) | no |
   | D no cycle term | 0.034 | 0.035 (k2) | no → accepted as non-inferior |
   | **O1** τ_b averaging | 0.115 | 0.242 (k2) | **yes** |
   | **O2** overhang state | 0.147 | 0.288 (k2) | **yes** |

   The two movers fail the registered rule in the paired causal check (Δ = 0.4, 28 cases; p = |err_X| − |err_R3_T|, q = the same for the 0.75/0.25 ensemble against REF):

   | Design | mean p | share p < 0 | k-block means of p (k3…k7) | max LOKO | worst p | mean q | Passes |
   |---|---|---|---|---|---|---|---|
   | O1 | +0.0080 | 0.54 | −0.083, +0.102, −0.001, +0.005, −0.014 | +0.023 | +0.180 | +0.020 | no (criteria 1, 2, 3, 5, 6 fail) |
   | O2 | +0.0067 | 0.50 | −0.044, +0.033, +0.045, −0.031, +0.014 | +0.017 | +0.148 | +0.001 | no (criteria 1, 2, 3, 5, 6 fail) |

   Both make R3_T slightly *worse* on average. Each helps one month block (k = 3) and hurts others.
2. **τ_b is not identified.** The top Laplace weight is ≥ 0.8 in **0 of 28** causal cases. The weight goes most often to τ_b = 67 d (22 cases), then 33.6 d (3), 134.5 d (2) and 269 d (1), but with top weights of only 0.3–0.5. O1 is therefore an "uncertainty band, not a model".
3. **The 10-21 effects were mostly not calendar-clock effects.**
   - The calendar-only Arrhenius change (C) moves real CK2 by +0.013 pp, and the Yagci-on-k reading (74.6 on time) by +0.104 pp. The 10-21 "aT²" test moved the ensemble's CK2 by about +0.46 pp, which suggests it changed the break-in clock as well.
   - The SOC weight (S) moves at most 0.022 pp, and switching off the true checkups entirely (sensitivity "true_ck at 0 %") still only 0.024 pp. As WP0 F2 predicted, the operating SOC is the same every month, so A_cal absorbs any SOC weight on operation time. The checkups and switches are only 7 % of τ.
   - The large 10-21 effects came from the break-in timescale (τ_b), which is exactly the unidentified quantity.
4. **What moves CK2 also moves the month-3/4 structure.** O1 and O2 raise real CK2 by +0.24/+0.29 pp (toward fixing R3_T's −0.64). They do the same in the causal cases, at k = 4 (+0.10 block mean for O1) and k = 5 (+0.045 for O2), where R3_T was already positive. A shorter break-in shifts loss from later months into earlier ones. The causal data cannot tell whether that is right for CK2.
5. **Inputs to WP3:**
   - No design passed the improvement rule, so there is no M_comb and **M = R3_T** (D3.1).
   - D is accepted as non-inferior (inert), but not applied on its own: it would change M without any causal gain.
   - E2 is not run (D3.0).

## Details

- **Screen** (`outputs/screen.json`, `screen_summary.csv`, `screen_predictions.csv`). ΔSOH = SOH(X) − SOH(R3_T). The screen script asserts that it never mentions the label columns. `grep -n -i "proxy\|qfc\|err_pp" wp2/run_screen.py` returns no line.
- **Sensitivities** (report only):

  | Sensitivity | S_causal (pp) |
  |---|---|
  | S true_ck at entry SOC / at 0 % | 0.024 / 0.024 |
  | S linear k_SOC | 0.013 |
  | S Naumann k_SOC² | 0.012 |
  | C Naumann 2×17.1 | 0.006 |
  | C Yagci-on-k 74.6 | 0.044 |
  | O1 uniform weights | 0.069 (moves through S_real 0.325) |
  | O2 SOC_0 = 0.10 / 0.50 | 0.106 / 0.178 |
  | O2 fitted τ line | 0.142 |
  | O2 x(CK0) = xe | 0.190 |

  None of the moving sensitivities would pass. Their mean p is O1_uniform −0.002 (fails criteria 1, 2, 3, 5), O2_fitline +0.007, O2_soc0_050 +0.014 and O2_x0eq +0.022 (`paired.json`).
- **Paired check** (`outputs/paired.json`, `paired_p_*.csv`).
  - **Δ-invariance:** p and q are identical at Δ = 0/0.4/0.8. Every causal case predicts from an anchor plus ε, and its proxy carries the same ε, so Δ cancels. Criterion 6 therefore repeats criterion 1 here.
  - **Demeaned error correlation with V2** (rule 6, demeaned over {X, R3_T, V2, SUB}): O1 −0.79, O2 −0.85.
- **Per-k causal signed means** (Δ = 0.4):

  | k | R3_T | O1 | O2 | V2 | SUB |
  |---|---|---|---|---|---|
  | 3 | −0.171 | −0.069 | −0.126 | +0.319 | +0.095 |
  | 4 | +0.094 | +0.196 | +0.108 | +0.444 | +0.143 |
  | 5 | −0.013 | +0.008 | +0.021 | +0.128 | −0.015 |
  | 6 | −0.236 | −0.241 | −0.205 | −0.208 | −0.291 |
  | 7 | +0.133 | +0.120 | +0.148 | −0.007 | −0.009 |

---

<a id="zh"></a>

# WP2 — 单因素设计：先筛预测，再做配对因果检查

> **语言：** [English](#en) · 中文

协议：`protocol.json`（sha `701ec6ef…`），在 87ed904 中提交，早于任何 WP2 输出。选择只用了因果案例，没有运行真实场景。下面真实 k 的那些行是*预测变化*（ΔSOH），不是误差。

## 结论在前

1. **没有设计通过。** 六个主设计中有四个是**惰性**的：预测变化低于噪声底（T_move = 0.110 pp）。

   | 设计 | S_causal (pp) | S_real (pp, 在 k) | 能动？ |
   |---|---|---|---|
   | B0 换温箱修正 | 0.008 | 0.009 (k3) | 否 |
   | S 按 SOC 加权的日历时钟 | 0.022 | 0.022 (k5) | 否 |
   | C 日历 Ea 加在 k 上（时间上 41.2） | 0.007 | 0.013 (k2) | 否 |
   | D 去掉循环项 | 0.034 | 0.035 (k2) | 否 → 判为非劣并接受 |
   | **O1** τ_b 平均 | 0.115 | 0.242 (k2) | **是** |
   | **O2** overhang 状态 | 0.147 | 0.288 (k2) | **是** |

   两个能动的设计在配对因果检查中都没通过登记规则（Δ = 0.4，28 个案例；p = |err_X| − |err_R3_T|，q 为 0.75/0.25 集成相对 REF 的同一量）：

   | 设计 | p 均值 | p < 0 比例 | p 的 k 块均值（k3…k7） | LOKO 最大 | 最差 p | q 均值 | 通过 |
   |---|---|---|---|---|---|---|---|
   | O1 | +0.0080 | 0.54 | −0.083, +0.102, −0.001, +0.005, −0.014 | +0.023 | +0.180 | +0.020 | 否（条件 1、2、3、5、6 不满足） |
   | O2 | +0.0067 | 0.50 | −0.044, +0.033, +0.045, −0.031, +0.014 | +0.017 | +0.148 | +0.001 | 否（条件 1、2、3、5、6 不满足） |

   两者平均都让 R3_T 略微*变差*：都只在一个月份块（k = 3）有帮助，在其他块有损害。
2. **τ_b 识别不出来。** 28 个因果案例中，Laplace 最大权重 ≥ 0.8 的有 **0 个**。最大权重最常落在 τ_b = 67 天（22 例），其次 33.6 天（3 例）、134.5 天（2 例）、269 天（1 例），但最大权重只有 0.3–0.5。所以 O1 是"不确定度带，不是模型"。
3. **10-21 的效应大多不是日历时钟的效应。**
   - 只改日历项的 Arrhenius 写法（C）让真实 CK2 只动 +0.013 pp；把 Yagci 的值当作加在 k 上（时间上 74.6）也只动 +0.104 pp。10-21 那次"aT²"测试让集成的 CK2 动了约 +0.46 pp，说明它很可能连磨合项的时钟也一起改了。
   - SOC 加权（S）最多动 0.022 pp；即使把真实检测期完全按 0% SOC 处理（敏感性"true_ck 取 0%"），也只动 0.024 pp。正如 WP0 F2 所预料的，运行 SOC 每月相同，运行时间上的任何 SOC 权重都会被 A_cal 吸收；而检测期和换温箱只占 τ 的 7%。
   - 10-21 的大效应来自磨合时间尺度（τ_b），而它恰恰识别不出来。
4. **能动 CK2 的改动，同时也会动第 3/4 月的结构。** O1 和 O2 把真实 CK2 抬高 +0.24/+0.29 pp（朝修正 R3_T 的 −0.64 的方向）。它们在因果案例中也做了同样的事：在 k = 4（O1 的块均值 +0.10）和 k = 5（O2 的 +0.045），而 R3_T 在那里本来就偏正。更短的磨合把损失从后面的月份挪到前面。因果数据无法判断这样做对 CK2 是否正确。
5. **交给 WP3 的结论：**
   - 没有设计通过改进规则，所以没有 M_comb，**M = R3_T**（D3.1）。
   - D 判为非劣（惰性）并接受，但不单独应用：单独应用会改变 M 而没有任何因果收益。
   - E2 不运行（D3.0）。

## 细节

- **筛查**（`outputs/screen.json`、`screen_summary.csv`、`screen_predictions.csv`）。ΔSOH = SOH(X) − SOH(R3_T)。筛查脚本内有断言，保证它不提及标签列；`grep -n -i "proxy\|qfc\|err_pp" wp2/run_screen.py` 没有任何匹配行。
- **敏感性**（只报告）：

  | 敏感性 | S_causal (pp) |
  |---|---|
  | S true_ck 取进入时 SOC / 取 0% | 0.024 / 0.024 |
  | S 线性 k_SOC | 0.013 |
  | S Naumann k_SOC² | 0.012 |
  | C Naumann 2×17.1 | 0.006 |
  | C Yagci 加在 k 上 74.6 | 0.044 |
  | O1 等权 | 0.069（靠 S_real 0.325 判为能动） |
  | O2 SOC_0 = 0.10 / 0.50 | 0.106 / 0.178 |
  | O2 拟合的 τ 直线 | 0.142 |
  | O2 x(CK0) = xe | 0.190 |

  能动的敏感性也都通不过。它们的 p 均值：O1_uniform −0.002（条件 1、2、3、5 不满足），O2_fitline +0.007，O2_soc0_050 +0.014，O2_x0eq +0.022（`paired.json`）。
- **配对检查**（`outputs/paired.json`、`paired_p_*.csv`）。
  - **与 Δ 无关：** p 和 q 在 Δ = 0/0.4/0.8 下完全相同。每个因果案例都是从锚点加 ε 出发预测的，它的代理也带着同一个 ε，所以 Δ 相互抵消。条件 6 在这里只是重复条件 1。
  - **与 V2 去均值后的误差相关**（规则 6，在 {X, R3_T, V2, SUB} 上去均值）：O1 −0.79，O2 −0.85。
- **各 k 的因果平均带符号误差**（Δ = 0.4）：

  | k | R3_T | O1 | O2 | V2 | SUB |
  |---|---|---|---|---|---|
  | 3 | −0.171 | −0.069 | −0.126 | +0.319 | +0.095 |
  | 4 | +0.094 | +0.196 | +0.108 | +0.444 | +0.143 |
  | 5 | −0.013 | +0.008 | +0.021 | +0.128 | −0.015 |
  | 6 | −0.236 | −0.241 | −0.205 | −0.208 | −0.291 |
  | 7 | +0.133 | +0.120 | +0.148 | −0.007 | −0.009 |
