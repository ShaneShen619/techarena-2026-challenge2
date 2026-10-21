<a id="en"></a>

# WP3 — Combination and ensemble weights (causal only)

> **Language:** English · [中文](#zh)

Protocol: `protocol.json`, committed before the outputs. Only causal cases (28; Δ = 0.4 unless stated) were used.

## Conclusions first

1. **No combination; M = R3_T; FINAL = REF.**
   - Nothing passed the WP2 improvement rule, so there is no M_comb.
   - D is accepted as non-inferior but not applied alone (D3.1).
   - E2 (two-regime weights) is not run: only 4 causal cases are in V2's `phase` regime (D3.0).
   - FINAL is the pre-registered 0.75·R3_T + 0.25·V2, which is r5c's REF.
2. **FINAL is not causally better than SUB.**
   - Paired r = |err_FINAL| − |err_SUB| over 28 matching cases:

     | Statistic | Value |
     |---|---|
     | Mean | −0.018 pp |
     | Share < 0 | 0.57 |
     | k-block means (k3…k7) | −0.068, +0.038, −0.047, −0.062, +0.031 |
     | Max LOKO | −0.006 |
     | Worst | +0.123 |

   - Criteria 3 (LOKO) and 4 (worst) hold. Criterion 1 fails (mean −0.018 > −δ = −0.028), and so does criterion 2 (two positive blocks).
   - FINAL is better than SUB on average, but by less than the noise floor, and not in every month. **WP5 is skipped by rule.**
3. **E1 curves** (causal mean MAE over the 28 cases, Δ = 0.4; a curve, not a selection):

   | w (weight on R3_T) | 0 | 0.25 | 0.5 | 0.75 | 1 |
   |---|---|---|---|---|---|
   | w·R3_T + (1−w)·V2 | 0.245 | 0.197 | 0.156 | **0.126** | 0.128 |
   | w·R3_T + (1−w)·SUB | 0.145 | 0.132 | **0.124** | 0.123 | 0.128 |

   - **With V2:** the curve is flat between w = 0.75 and 1. LOKO re-picks w = 0.75 in 3 folds and 1.0 in 2.
   - **With SUB:** it is flat between 0.5 and 0.75. LOKO re-picks 0.5 in 3 folds, 0.75 in 1 and 1.0 in 1.
   - **Mixing R3_T with SUB** (0.5–0.75) gives about 0.123 pp, the same as REF (0.126). It is the same idea expressed with the submitted model as partner. It is not a registered candidate.
   - **Δ:** the curves are identical at Δ = 0/0.4/0.8, for the same reason as in WP2 (ε cancels in causal cases). Full table: `outputs/e1_curves.csv`.

---

<a id="zh"></a>

# WP3 — 组合与集成权重（只用因果情景）

> **语言：** [English](#en) · 中文

协议：`protocol.json`，在输出之前提交。只用因果案例（28 个；除特别说明外 Δ = 0.4）。

## 结论在前

1. **没有组合；M = R3_T；FINAL = REF。**
   - 没有设计通过 WP2 的改进规则，所以没有 M_comb。
   - D 判为非劣并接受，但不单独应用（D3.1）。
   - E2（两档权重）不运行：只有 4 个因果案例处于 V2 的 `phase` 情形（D3.0）。
   - FINAL 是预先登记的 0.75·R3_T + 0.25·V2，即 r5c 的 REF。
2. **FINAL 在因果上并不优于 SUB。**
   - 在 28 个一致的案例上，配对差 r = |err_FINAL| − |err_SUB|：

     | 统计量 | 值 |
     |---|---|
     | 均值 | −0.018 pp |
     | < 0 的比例 | 0.57 |
     | k 块均值（k3…k7） | −0.068, +0.038, −0.047, −0.062, +0.031 |
     | LOKO 最大 | −0.006 |
     | 最差 | +0.123 |

   - 条件 3（LOKO）和 4（最差）满足；条件 1 不满足（均值 −0.018 > −δ = −0.028），条件 2 也不满足（两个块为正）。
   - FINAL 平均略好于 SUB，但差距小于噪声底，而且不是每个月都好。**WP5 按规则跳过。**
3. **E1 曲线**（28 个因果案例的平均 MAE，Δ = 0.4；是一条曲线，不是一次选择）：

   | w（R3_T 的权重） | 0 | 0.25 | 0.5 | 0.75 | 1 |
   |---|---|---|---|---|---|
   | w·R3_T + (1−w)·V2 | 0.245 | 0.197 | 0.156 | **0.126** | 0.128 |
   | w·R3_T + (1−w)·SUB | 0.145 | 0.132 | **0.124** | 0.123 | 0.128 |

   - **与 V2 组合：** 曲线在 w = 0.75 到 1 之间是平的。逐一留出 k 重新选，3 折选 w = 0.75，2 折选 1.0。
   - **与 SUB 组合：** 曲线在 0.5 到 0.75 之间是平的。逐一留出 k 重新选，3 折选 0.5，1 折选 0.75，1 折选 1.0。
   - **R3_T 与 SUB 混合**（0.5–0.75）约为 0.123 pp，与 REF（0.126）相同。这是同一个思路，只是把搭档换成了提交模型。它不是登记的候选。
   - **Δ：** 曲线在 Δ = 0/0.4/0.8 下完全相同，原因与 WP2 一样（因果案例中 ε 相互抵消）。完整表格：`outputs/e1_curves.csv`。
