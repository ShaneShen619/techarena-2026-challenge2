<a id="en"></a>

# WP2 — Idea B: combine per-cell changes

> **Language:** English · [中文](#zh)

**Result: B3 passes every gate and is WP2's adopted candidate. But the rejection rule never fires on it, so B3 is in effect "A3's per-cell locations, mean of the per-cell changes". It adds nothing beyond idea A, and it is weaker than A3** (causal 0.1515 vs A3 0.1470, real MAE 0.135 vs A3 0.120). B1 and B2 fail. Protocol committed in `6681058` before evaluation. Script [run_wp2.py](run_wp2.py); outputs in [outputs/](outputs/). Rerun byte-identical.

| Gate (Δ 0.4) | SUB | B1 median of changes | B2 one-cell rejection (τ 0.38) | **B3 = B2 on A3 locations (τ 0.35)** |
|---|---|---|---|---|
| pseudo / cold | 0.1439 / 0.1703 | 0.1402 / 0.1696 ✓✓ | 0.1439 / 0.1786 ✓✗ | **0.1331 / 0.1698 ✓✓** |
| changed non-real cases: n, SUB → cand, worst | — | 16: 0.217 → 0.208, +0.029 ✗ (< 0.02 gain) | 1: 0.402 → 0.486 ✗ | **16: 0.217 → 0.192, +0.029 ✓** |
| G_robust: within +0.005 / max Δcausal / max Δreal | — | 4/6, +0.007, +0.027 ✗ | 5/6, +0.006, +0.000 ✓ | **6/6 (LOVO), +0.000, +0.019 ✓** |
| G_event SD (chained series, D2.1) | 0.2625 | 0.2631 ✓ | 0.2625 ✓ | **0.2527 ✓** |
| real MAE Δ0 / 0.4 / 0.8 | 0.197 / 0.126 / 0.146 | 0.199 / 0.128 / 0.142 | 0.198 / 0.126 / 0.147 | 0.206 / 0.135 / 0.151 |
| real MAX Δ0.4 | 0.228 | 0.241 ✓ | 0.227 ✓ | 0.231 ✓ |

**The "one drifting cell" hypothesis is not supported** ([outputs/wp2_rejections_B2.csv](outputs/wp2_rejections_B2.csv)).
- On the main variant, the largest deviation of one cell's change from the other three's median is below τ = 0.38 Ah in 21 of 22 distinct cases (typically 0.12–0.30 Ah). The only rejection is cell2 in CS CK6 (0.43 Ah).
- On the A3 ensemble, no case exceeds 0.29 Ah, so there are no rejections at all.
- The cell divergence of round 8 accumulates slowly over months. In a single month it is smaller than the detection noise, so rejection has nothing to act on.

**Real errors at Δ 0.4 (exposed):** B3 gives CK1 +0.231, CK3 +0.092, CK4 +0.183, CK5 +0.170, CK6 −0.219, CK7 −0.007 (SUB: +0.217, +0.080, +0.228, +0.150, −0.163, −0.004). See [outputs/wp2_real_err_d04.csv](outputs/wp2_real_err_d04.csv) and [outputs/wp2_real_SOH_d04.csv](outputs/wp2_real_SOH_d04.csv).

---

<a id="zh"></a>

# WP2——想法 B：合并单体变化量

> **语言：** [English](#en) · 中文

**结论：B3 通过全部检验，是 WP2 的采用候选。但它的剔除规则一次都没有触发，所以 B3 实际上就是"A3 的单体位置 + 单体变化量取平均"，没有在想法 A 之外增加任何东西，而且比 A3 弱**（因果 0.1515 对 A3 的 0.1470，真实 MAE 0.135 对 0.120）。B1（变化量中位数）稳健性只有 4/6、改进不足 0.02，未通过；B2 只改变了 1 个案例，而且冷启动变差，未通过。

**"某个电芯在某个月突然跑偏"的假设不成立。**
- 主变体上，22 个不同案例中有 21 个的最大单体偏离都低于阈值 0.38 Ah（通常为 0.12–0.30 Ah），唯一一次剔除是 CS CK6 的 cell2（0.43 Ah）。
- 在 A3 集成上没有任何案例超过 0.29 Ah。
- 第 8 轮看到的单体拉开是逐月慢慢累积的，单个月内的拉开小于检测噪声，所以剔除规则无从下手。
