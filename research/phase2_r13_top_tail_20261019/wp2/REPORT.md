<a id="en"></a>

# WP2 — Measurements

> English · [中文](#zh)

Everything here was computed by the registered `src/tail.py` (protocol commit `7960a99`), called from `src/run_wp2.py`. Figures come from `src/wp2_fig.py`. No decision rule is applied here (that is WP3), and no P_k or proxy is used.

**Conclusions first.**

1. **Only M4 (two exponentials) describes the anchors' CV current.** It is admitted on all seven anchors 1–7: RMSE 0.055–0.124 A, last-third mean residual −0.027…+0.001 A. M1, M2 and M3 fail on all seven:
   - **M1:** RMSE 0.38–0.54 A, last-third residual −0.27 to −0.40 A. The real tail is fatter than a single exponential.
   - **M2:** RMSE 0.16–0.28 A, just over the 0.15 A gate. It reproduces round 11's fit exactly (anchor 1: τ = 178.6 s, I∞ = 4.23 A). Its I∞ of 3.6–4.2 A makes it "undefined" for all three cutoffs at every anchor (24 undefined pairs).
   - **M3:** RMSE 0.56–0.61 A, last third +0.67…+0.74 A. A pure diffusion tail fits the window worst of all.
2. **The exposed back-of-envelope, answered.**
   - Under M1's own fit, τ = 328.5 s (anchor 1) and 415.2 s (anchor 7). I_end·τ = **0.465 Ah → 0.588 Ah**, a difference of 0.123 Ah.
   - **M1 does not pass admission** for either anchor (RMSE 0.543 / 0.402 A; last third −0.397 / −0.300 A).
   - The prompt's 0.25 → 0.31 Ah used round 11's τ, which belongs to M2 (with I∞ ≈ 4.2 A), so it mixed two models.
   - Under the only admitted model (M4), the tail to near-zero current (C7, a 2 h hold) is 0.575 → 0.700 Ah, and the drift at anchor 7 is +0.125 Ah. The "≈ 0.05 Ah" guess was about 2.4× too small, though its order of magnitude (~0.1 Ah) holds.
3. **The M4 tail drift is positive under every scenario: d·8.2 = +0.041 Ah (C2) to +0.124 Ah (C7).** The LOO ranges lie within +0.029…+0.186 Ah.
   - The shape is a step from anchor 1 to anchor 2 (+0.05…+0.09 Ah), followed by a slow rise.
   - The longer time constant τ2 grows from 412 s to 503 s.
4. **T2 (relaxed top voltage, pack, main window) gives +0.412 Ah (LOO +0.292…+0.566).** This is the largest number in the round, but it is fragile.
   - V30 moves by only 7 mV in total, at 1 mV resolution: 13.439, 13.438, 13.435, 13.434, 13.432, 13.434, 13.435 V.
   - s_top on [0.5, 2.0] Ah is 0.0223 V/Ah, so each 1 mV becomes 0.045 Ah.
   - The CK0 curve falls steeply from 0 to 1.3 Ah (13.590 → 13.258 V), then is flat. The main window straddles both regimes.
   - With the [0.25, 1.0] window, s_top = 0.148 V/Ah and T2 = +0.062 Ah. The [1.0, 3.0] window is on the plateau with a slightly negative slope, so it cannot be inverted (−6.5 Ah, meaningless).
5. **T3 (pulse resistance, a check only): +0.103 Ah (LOO +0.052…+0.143).** It has the same sign as M4 and T2.
6. **The top-ups do not show the anchors' drift (descriptive, not used).**
   - M4 is admitted on 30 of 33 top-ups (7 of 9 at 25 °C); M2 on 10; M1 and M3 on none.
   - The monthly medians of the 25 °C top-ups are flat: Q_tail(C4) = 0.31–0.36 Ah over months 1–6, a slope of +0.003 Ah at CK7. Month 7's only 25 °C top-up (E40) is not admitted.
   - So the growing tail is specific to the from-empty anchor charge, which is a path question (round 14).
7. **Cell3 limits the top in every case.** CK0 start: cell3 leads the next cell by 137 mV. Anchors 1–7: by 51 → 20 mV at the CV end, 14 → 7 mV after 30 min of rest, and 12 → 5 mV in the 20 A pulse. At CK0, cell3 sits far higher above the other cells than at any 25 °C anchor's top; the only comparable case is anchor 0 (45 °C, campaign start: 216 / 145 / 106 mV).
8. **The admitted set A for WP3** therefore has 8 members: C1 (≡ 0), T2 (pack, main window), and M4 × {C2, …, C7}.

## Per-anchor table (anchors 1–7)

| k | fade (Ah) | CV samples | t_end (s) | M4 RMSE (A) | τ1 (s) | τ2 (s) | A2 (A) | Q_tail C2 (Ah) | Q_tail C4 (Ah) | Q_tail C7 (Ah) | Δ_tail C4 (Ah) | V30 (V) | T2 −ΔF_V (Ah) | R_pack (mΩ) | T3 Δε (Ah) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 45 | 438 | 0.121 | 47 | 412 | 14.5 | 0.283 | 0.516 | 0.575 | +0.000 | 13.439 | +0.000 | 5.834 | +0.000 |
| 2 | 1.34 | 47 | 456 | 0.057 | 69 | 468 | 13.5 | 0.331 | 0.596 | 0.662 | +0.079 | 13.438 | +0.045 | 5.637 | −0.045 |
| 3 | 2.36 | 47 | 455 | 0.055 | 64 | 465 | 13.6 | 0.330 | 0.593 | 0.659 | +0.077 | 13.435 | +0.180 | 5.736 | −0.022 |
| 4 | 3.26 | 52 | 505 | 0.055 | 66 | 494 | 14.0 | 0.340 | 0.620 | 0.690 | +0.104 | 13.434 | +0.225 | 5.833 | −0.000 |
| 5 | 3.92 | 54 | 522 | 0.124 | 46 | 479 | 14.8 | 0.325 | 0.596 | 0.664 | +0.080 | 13.432 | +0.314 | 5.833 | −0.000 |
| 6 | 4.37 | 53 | 514 | 0.056 | 63 | 496 | 14.1 | 0.339 | 0.620 | 0.690 | +0.103 | 13.434 | +0.225 | 5.931 | +0.022 |
| 7 | 5.05 | 54 | 530 | 0.061 | 63 | 503 | 14.4 | 0.344 | 0.629 | 0.700 | +0.112 | 13.435 | +0.180 | 5.883 | +0.011 |

## Drift slopes (effect at CK7 = slope × 8.2 Ah)

| Member | slope (Ah/Ah) | d·8.2 (Ah) | LOO d·8.2 (Ah) | in A |
|---|---|---|---|---|
| C1 (≡ 0) | 0 | 0 | [0, 0] | yes |
| M4 / C2 (2.55 A) | 0.0050 | +0.041 | [+0.029, +0.088] | yes |
| M4 / C3 (1.02 A) | 0.0111 | +0.091 | [+0.062, +0.147] | yes |
| M4 / C4 (0.51 A) | 0.0131 | +0.108 | [+0.072, +0.167] | yes |
| M4 / C5 (30 min) | 0.0130 | +0.107 | [+0.072, +0.169] | yes |
| M4 / C6 (60 min) | 0.0151 | +0.124 | [+0.083, +0.186] | yes |
| M4 / C7 (120 min) | 0.0152 | +0.124 | [+0.083, +0.186] | yes |
| T2 pack, s_top [0.5, 2.0] | 0.0502 | +0.412 | [+0.292, +0.566] | yes |
| T2 pack, s_top [0.25, 1.0] | 0.0076 | +0.062 | [+0.044, +0.085] | no (sensitivity) |
| T2 pack, s_top [1.0, 3.0] | s_top < 0 | −6.49 | — | no (window not invertible) |
| T2 cell3 (top cell), main / [0.25, 1.0] | 0.0632 / 0.0123 | +0.518 / +0.100 | — | no |
| T3 pack | 0.0125 | +0.103 | [+0.052, +0.143] | no (check) |
| M1, M2, M3 × all C | — | — | — | no: 0 of 7 anchors admitted |

Per-cell T2 for cells 1, 2 and 4 is not informative. Cells 1 and 2 have V30 constant to 1 mV, and their CK0 slopes are 0.001–0.003 V/Ah, so a 1–2 mV change in cell4 becomes −2.5 Ah. All values are in [top_state_slopes.csv](top_state_slopes.csv).

## Files

- [fits.csv](fits.csv): every charge × model; parameters, RMSE, last-third residual, convergence, bound flag, admission; `Iend_x_tau_Ah` for M1.
- [tails.csv](tails.csv): every charge × model × scenario; Q_tail, defined, usable; Δ_tail and fade for anchors 1–7.
- [pairs.csv](pairs.csv): every (M, C) with membership, usable anchors, slope, LOO.
- [top_state.csv](top_state.csv) and [top_state_slopes.csv](top_state_slopes.csv): T2 (pack and per cell, three windows) and T3, per anchor and as slopes.
- [topup_monthly.csv](topup_monthly.csv) and [topup_monthly_slopes.csv](topup_monthly_slopes.csv): the top-up cross-check.
- [ck0_comparison.csv](ck0_comparison.csv): top cell at the CK0 start versus each anchor's CV end, +30 min and pulse.
- [measurements.json](measurements.json): admission counts, the M1 back-of-envelope, the undefined pairs.
- Figures:
  - [fig_cv_fits.png](fig_cv_fits.png): the CV current of every anchor with each admitted model's fit and extrapolation;
  - [fig_drift_vs_fade.png](fig_drift_vs_fade.png): Δ_tail(k) and −ΔF^A_V(k) against fade;
  - [fig_residuals_anchor1_7.png](fig_residuals_anchor1_7.png): the residuals of all four models for anchors 1 and 7.

Non-admitted (charge, model) pairs:
- anchors 1–7: M1, M2 and M3 at all seven (21 pairs);
- anchor 0 (excluded anyway): M1 and M3;
- top-ups: M1 33/33, M3 33/33, M2 23/33, M4 3/33 (E21 at 45 °C; E26 and E40 at 25 °C; RMSE 0.154–0.179 A).

---

<a id="zh"></a>

# WP2 — 测量

> [English](#en) · 中文

所有结果都由登记的 `src/tail.py`（协议提交 `7960a99`）计算，经 `src/run_wp2.py` 调用；图由 `src/wp2_fig.py` 生成。这里不应用任何决策规则（那是 WP3 的事），也不使用任何 P_k 或代理。

**结论先读。**

1. **只有 M4（双指数）能描述锚点的 CV 电流。** 它在锚点 1–7 全部 7 个上准入：RMSE 0.055–0.124 A，最后三分之一的平均残差 −0.027…+0.001 A。M1、M2、M3 在这 7 个锚点上全部不准入：
   - **M1：** RMSE 0.38–0.54 A，最后三分之一残差 −0.27 到 −0.40 A。真实的尾巴比单指数更"胖"。
   - **M2：** RMSE 0.16–0.28 A，刚好超过 0.15 A 的门槛。它精确复现了第 11 轮的拟合（锚点 1：τ = 178.6 s，I∞ = 4.23 A）。它的 I∞ 为 3.6–4.2 A，所以在每个锚点上三个截止电流都"未定义"（共 24 个未定义组合）。
   - **M3：** RMSE 0.56–0.61 A，最后三分之一残差 +0.67…+0.74 A。纯扩散型尾巴对窗口的拟合最差。
2. **对已曝光粗算的回应。**
   - 用 M1 自己的拟合，τ = 328.5 s（锚点 1）和 415.2 s（锚点 7）。I_end·τ = **0.465 Ah → 0.588 Ah**，差 0.123 Ah。
   - **M1 在这两个锚点上都没有通过准入**（RMSE 0.543 / 0.402 A；最后三分之一残差 −0.397 / −0.300 A）。
   - prompt 中的 0.25 → 0.31 Ah 用的是第 11 轮的 τ，而那个 τ 属于 M2（I∞ ≈ 4.2 A），因此混用了两个模型。
   - 在唯一准入的模型 M4 下，充到电流接近零的尾巴（C7，保持 2 h）为 0.575 → 0.700 Ah，锚点 7 的漂移为 +0.125 Ah。"约 0.05 Ah"的估计小了约 2.4 倍，但数量级（约 0.1 Ah）没错。
3. **M4 尾巴漂移在每个情景下都为正：d·8.2 = +0.041 Ah（C2）到 +0.124 Ah（C7）。** LOO 范围落在 +0.029…+0.186 Ah 之内。
   - 形状是从锚点 1 到锚点 2 的一个台阶（+0.05…+0.09 Ah），之后缓慢上升。
   - 较长的时间常数 τ2 从 412 s 增长到 503 s。
4. **T2（静置顶部电压，电池组，主窗口）给出 +0.412 Ah（LOO +0.292…+0.566）。** 这是本轮最大的数，但很脆弱。
   - V30 总共只变化 7 mV，分辨率为 1 mV：13.439、13.438、13.435、13.434、13.432、13.434、13.435 V。
   - [0.5, 2.0] Ah 上的 s_top 为 0.0223 V/Ah，所以每 1 mV 对应 0.045 Ah。
   - CK0 曲线在 0–1.3 Ah 内陡降（13.590 → 13.258 V），之后平坦。主窗口跨越了这两个区段。
   - 用 [0.25, 1.0] 窗口，s_top = 0.148 V/Ah，T2 = +0.062 Ah。[1.0, 3.0] 窗口落在平台上，斜率略为负，无法反演（−6.5 Ah，没有意义）。
5. **T3（脉冲内阻，只作检查）：+0.103 Ah（LOO +0.052…+0.143）。** 与 M4 和 T2 同号。
6. **补电没有表现出锚点那样的漂移（描述性，不使用）。**
   - M4 在 33 次补电中准入 30 次（25 °C 的 9 次中准入 7 次）；M2 准入 10 次；M1 和 M3 一次也没有。
   - 25 °C 补电的月中位数持平：第 1–6 月 Q_tail(C4) = 0.31–0.36 Ah，斜率对应 CK7 处 +0.003 Ah。第 7 月唯一的 25 °C 补电（E40）未准入。
   - 因此，尾巴的增长是从空开始的锚点充电所特有的，这属于路径问题（第 14 轮）。
7. **每种情况下都由 cell3 限制顶部。** CK0 起点：cell3 比第二高的电芯高 137 mV。锚点 1–7：CV 结束时高 51 → 20 mV，静置 30 min 后高 14 → 7 mV，20 A 脉冲中高 12 → 5 mV。在 CK0，cell3 高出其他电芯的幅度远大于任何 25 °C 锚点顶部时的情况；唯一可比的是锚点 0（45 °C，实验开始时：216 / 145 / 106 mV）。
8. **因此 WP3 的准入集 A** 有 8 个成员：C1（≡ 0）、T2（电池组，主窗口），以及 M4 × {C2, …, C7}。

## 逐锚点表（锚点 1–7）

（表格同英文部分。）

## 漂移斜率（CK7 处影响 = 斜率 × 8.2 Ah）

（表格同英文部分。）

电芯 1、2、4 的分电芯 T2 没有信息量。电芯 1 和 2 的 V30 在 1 mV 内不变，它们的 CK0 斜率只有 0.001–0.003 V/Ah，因此 cell4 1–2 mV 的变化会变成 −2.5 Ah。全部数值见 [top_state_slopes.csv](top_state_slopes.csv)。

## 文件

- [fits.csv](fits.csv)：每次充电 × 模型；参数、RMSE、最后三分之一残差、收敛、是否触界、是否准入；M1 另有 `Iend_x_tau_Ah`。
- [tails.csv](tails.csv)：每次充电 × 模型 × 情景；Q_tail、是否有定义、是否可用；锚点 1–7 另有 Δ_tail 和 fade。
- [pairs.csv](pairs.csv)：每个（M, C）组合的成员资格、可用锚点、斜率和 LOO。
- [top_state.csv](top_state.csv) 和 [top_state_slopes.csv](top_state_slopes.csv)：T2（电池组和各电芯，三个窗口）和 T3，逐锚点及斜率。
- [topup_monthly.csv](topup_monthly.csv) 和 [topup_monthly_slopes.csv](topup_monthly_slopes.csv)：补电交叉检验。
- [ck0_comparison.csv](ck0_comparison.csv)：CK0 起点与各锚点 CV 结束、+30 min 和脉冲时的顶部电芯。
- [measurements.json](measurements.json)：准入计数、M1 粗算、未定义组合。
- 图：
  - [fig_cv_fits.png](fig_cv_fits.png)：每个锚点的 CV 电流，以及每个准入模型的拟合和外推；
  - [fig_drift_vs_fade.png](fig_drift_vs_fade.png)：Δ_tail(k) 和 −ΔF^A_V(k) 随衰减的变化；
  - [fig_residuals_anchor1_7.png](fig_residuals_anchor1_7.png)：锚点 1 和 7 上四个模型的残差。

未准入的（充电, 模型）组合：
- 锚点 1–7：M1、M2、M3 在全部 7 个锚点上（21 个组合）；
- 锚点 0（本来就排除）：M1 和 M3；
- 补电：M1 33/33，M3 33/33，M2 23/33，M4 3/33（45 °C 的 E21；25 °C 的 E26 和 E40；RMSE 0.154–0.179 A）。
