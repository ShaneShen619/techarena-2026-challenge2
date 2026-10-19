<a id="en"></a>

# WP3 — Top: the 45/25 °C anchor-top offset T_top: report

> **Language:** English · [中文](#zh)

Protocol v1 (`wp1/protocol.json`, registered in `b3f3e7a`). `src/ahchain.py` and `src/locators.py` are imported unchanged (`shasum -c wp1/protocol.sha256`: OK). Figure: `wp3/wp3_top.png`.

## Conclusions

1. **T_top = +1.11 Ah [0.60, 1.62]. Half-width 0.51 Ah > 0.25 → G_T: not identified.**
   - The 45 °C from-empty anchor 0 ends its CV holding about 0.6–1.6 Ah more charge than a 25 °C from-empty anchor.
   - The interval is the registered one: the terms' intervals added, with no G_E2 widening.
   - The sensitivity without k = 3 is identical, because k = 3 has no admissible AT pair (recording gap).
2. **The three terms.**
   - **Term1** = F^A_0 − F^T_45 = +0.074 Ah [0.022, 0.127], with SE = σ_TT,45.
   - **Term2** = F^T_45 − F^T_25 = +0.616 Ah [0.405, 0.829], median of 5 switches. It is the largest part.
   - **Term3** = F^T_25 − F^A_k = +0.418 Ah [0.175, 0.660], median of k = 1, 2, 4, 5, 6. Anchors 3 and 7 are excluded by the registered gap rule (WP0 D9).
3. **G_noise passes:** σ_TT,25 = 0.125 Ah (2 TT pairs) and σ_TT,45 = 0.026 Ah (17 TT pairs), both ≤ 0.30 Ah.
4. **G_E2: consistent.**
   - median J_DL1 = 0.705 Ah against median Term2 = 0.616 Ah, |diff| = 0.089 ≤ 0.20, so nothing is widened.
   - The A3 jump is smaller: median 0.319 Ah after the r_45 correction, 0.185 Ah raw. The raw value reproduces the V2 study's ≈ +0.18 Ah.
   - J also contains the step's own shift with temperature, and its DL1 version scatters widely (0.22–1.19 Ah). The agreement is therefore loose support, not a confirmation.
5. **λ is not stationary, and this dominates the interval.**
   - The TT-block ratio λ = N/thr drifts from −0.97·10⁻³ (month 0) to −2.82·10⁻³ (month 6) in the 45 °C segments. Every block has a throughput of 377.4 Ah, so 10⁻³ of λ is 0.38 Ah.
   - The registered loss rule gives the five 25 °C segments without TT pairs the pooled 25 °C λ (−2.45·10⁻³), which comes from months 5–6 only.
   - As a result, Term3 for k = 1, 2, 4 (0.42–0.60) and Term2 for j = 1–3 read high. Both fall with month (Spearman −0.9).
   - An **exploratory, non-registered** variant uses the time-nearest TT segment's λ. It gives Term3 ≈ 0.13, Term2 ≈ 0.47 and **T_top ≈ 0.68 Ah**, inside the registered interval near its lower end.
   - The λ drift is itself unexplained. The per-block imbalance between equal tops grows from −0.36 to −1.13 Ah, the wrong sign for side reactions, so it is a time-varying measurement bias. This is open for round 13.
6. **E3 (physics diagnostic) is not informative.**
   - ΔV (pack, 30 min after CV end, first 45 °C top-up minus last 25 °C top-up) = 42–61 mV at ΔT ≈ 20 K. Up to ±24 mV of that could be entropic (assumed ±0.3 mV/K per cell).
   - The CK0 C/20 curve falls 330 mV in the first 1 Ah and then is flat, so s = 148, 22 and −1.4 mV/Ah on the three windows.
   - Term2_E3 has a point of 1.9–2.7 Ah and an interval unbounded below. It cannot test Term2.
7. **Which cell sets the top.**
   - Cell 3, at both temperatures, in all 41 CV events (anchor 0 included), both at the CV end and 30 min later.
   - The 30-min top spread is 65–88 mV at 45 °C and 19–24 mV at 25 °C (first 45 °C vs last 25 °C top-ups around each switch).
8. **Term2 vs idle hours:** Spearman ρ = −0.40, Theil–Sen −11 mAh/h (n = 5). There is no self-discharge signal, and it is confounded with month.

## E1 — pairs and loss rule (`pairs.csv`, `e1_chain.json`)

**Pairs.** There are 40 consecutive CV-end pairs:
- 19 TT, 8 AT, 5 X and 8 not paired: 7 across a checkup date, and 1 across the segment 1 → 2 boundary (E05–E06), which is not a chamber switch.
- One of the 7 is E04–E05: both events lie inside segment 1, but segment 1 runs past the CK1 date (2025-02-08 00:00), so the registered rule "no checkup date in (t_i, t_j]" removes it. Segment 1 keeps 2 TT pairs.
- Admissible: 19 TT, 6 AT and 5 X.
- Excluded:
  - E14–E15 (anchor 3, recording gap 59 909 s);
  - E40–E41 (anchor 7, recording gap 1 753 s).
- All five switch idles have exactly flat counters.

**λ by segment.**

| Segment | Set °C | λ (×10⁻³) | Source | TT pairs |
|---|---|---|---|---|
| 1 | 45 | −0.969 | segment | 2 |
| 2 | 25 | −2.451 | pooled same set point | 0 |
| 4 | 25 | −2.451 | pooled same set point | 0 |
| 5 | 45 | −1.424 | segment | 3 |
| 6 | 25 | −2.451 | pooled same set point | 0 |
| 7 | 45 | −1.442 | segment | 3 |
| 8 | 25 | −2.451 | pooled same set point | 0 |
| 9 | 45 | −1.688 | segment | 3 |
| 10 | 25 | −2.562 | segment | 1 |
| 11 | 45 | −2.489 | segment | 3 |
| 12 | 25 | −2.339 | segment | 1 |
| 13 | 45 | −2.823 | segment | 3 |
| 14 | 25 | −2.451 | pooled same set point | 0 |

TT residuals (leave-one-out λ): 25 °C ±0.084 Ah (n = 2); 45 °C −0.112 … +0.124 Ah (n = 17).

## Chain terms (`terms.csv`)

| Term | Pair | k / month | N Ah | thr Ah | λ (×10⁻³) | value (registered) | λ25 / λ45 alone | pooled λ (descr.) | time-matched λ (exploratory) |
|---|---|---|---|---|---|---|---|---|---|
| Term1 | E01–E02 | k=0 | −0.440 | 377.47 | −0.969 | +0.074 | — | −0.182 | +0.074 |
| Term3 | E06–E07 | k=1 | −0.325 | 377.41 | −2.451 | +0.600 | — | +0.600 | +0.041 |
| Term3 | E08–E09 | k=2 | −0.346 | 377.41 | −2.451 | +0.579 | — | +0.579 | +0.192 |
| Term3 | E20–E21 | k=4 | −0.507 | 377.42 | −2.451 | +0.418 | — | +0.418 | +0.130 |
| Term3 | E26–E27 | k=5 | −0.874 | 377.41 | −2.562 | +0.093 | — | +0.051 | +0.093 |
| Term3 | E33–E34 | k=6 | −0.748 | 377.41 | −2.339 | +0.135 | — | +0.177 | +0.135 |
| Term2 | E09–E10 | m2 | −0.063 | 377.40 | −1.937 | +0.668 | 0.862 / 0.475 | — | +0.475 |
| Term2 | E15–E16 | m3 | −0.070 | 377.46 | −1.946 | +0.665 | 0.855 / 0.474 | — | +0.474 |
| Term2 | E21–E22 | m4 | −0.165 | 377.41 | −2.069 | +0.616 | 0.760 / 0.473 | — | +0.473 |
| Term2 | E28–E29 | m5 | −0.508 | 377.41 | −2.525 | +0.445 | 0.459 / 0.431 | — | +0.459 |
| Term2 | E35–E36 | m6 | −0.454 | 377.39 | −2.581 | +0.520 | 0.429 / 0.611 | — | +0.429 |

| | Point | Lambda range of the point | SE | Interval |
|---|---|---|---|---|
| Term1 | +0.074 | — | 0.026 (σ_TT,45) | [0.022, 0.127] |
| Term2 | +0.616 | 0.474 … 0.760 | 0.034 | [0.405, 0.829] |
| Term3 | +0.418 | — | 0.121 | [0.175, 0.660] |
| **T_top** | **+1.108** | | | **[0.602, 1.616]**, half-width 0.507 |

## E2 and E3 (`e2_e3.csv`, `e2_e3_summary.json`)

| Switch | Month | Idle h | d25 / d45 A3 | r45 A3 Ah/d | J A3 (raw) | d25 / d45 DL1 | r45 DL1 | J DL1 (raw) | Term2 | ΔV mV | ΔT K | Term2_E3 [lo, hi] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E09–E10 | 2 | 21.2 | 28.31 / 28.57 | −0.042 | +0.496 (+0.256) | 27.60 / 28.43 | −0.063 | +1.192 (+0.833) | +0.668 | 61 | 20.12 | 2.74 [−60, 3.82] |
| E15–E16 | 3 | 6.9 | 27.46 / 27.62 | −0.018 | +0.245 (+0.155) | 27.41 / 27.49 | −0.028 | +0.224 (+0.078) | +0.665 | 61 | 19.95 | 2.74 [−60, 3.82] |
| E21–E22 | 4 | 9.7 | 27.06 / 27.25 | −0.026 | +0.319 (+0.185) | 26.57 / 27.07 | −0.038 | +0.705 (+0.506) | +0.616 | 61 | 19.94 | 2.74 [−60, 3.81] |
| E28–E29 | 5 | 25.3 | 26.71 / 26.85 | −0.025 | +0.287 (+0.141) | 26.14 / 26.49 | −0.047 | +0.636 (+0.358) | +0.445 | 47 | 20.25 | 2.11 [−51, 3.20] |
| E35–E36 | 6 | 12.1 | 26.10 / 26.35 | −0.028 | +0.403 (+0.251) | 25.34 / 26.00 | −0.039 | +0.868 (+0.661) | +0.520 | 42 | 20.12 | 1.89 [−47, 2.97] |

- **s windows.** The CK0 top slope s is 22.3 mV/Ah on [0.5, 2.0] (main), 148.0 on [0.25, 1.0] and −1.4 on [1.0, 3.0].
- **dU/dT.** ±0.3 mV/K per cell, an **assumption**. No cited LFP/graphite full-cell high-SOC value was available offline; the repository review quotes electrode-level magnitudes of graphite ~0.2 and LFP ~0.1 mV/K (Spingler 2020).

## Gates (`T_top.json`)

| Gate | Result |
|---|---|
| G_noise | **passed** (σ_TT,25 0.125, σ_TT,45 0.026 ≤ 0.30) |
| G_E2 | **consistent** (\|0.705 − 0.616\| = 0.089 ≤ 0.20), no widening |
| G_T | **not identified** (half-width 0.507 > 0.25) |

---

<a id="zh"></a>

# WP3 — 顶部：45/25 °C 锚点顶部偏移 T_top：报告

> [English](#en) · 中文

使用协议第 1 版（`wp1/protocol.json`，在 `b3f3e7a` 中登记），原样导入 `src/ahchain.py` 和 `src/locators.py`（`shasum -c wp1/protocol.sha256` 通过）。图：`wp3/wp3_top.png`。

## 结论

1. **T_top = +1.11 Ah [0.60, 1.62]，半宽 0.51 Ah > 0.25 → G_T：未识别。**
   - 45 °C 下从空充满的锚点 0 在 CV 结束时，比 25 °C 下从空充满的锚点多存约 0.6–1.6 Ah。
   - 区间是登记区间，即各项区间相加，没有经过 G_E2 放宽。
   - 排除 k = 3 的敏感性结果与之完全相同，因为 k = 3 没有可用的 AT 配对（记录间隙）。
2. **三个分项。**
   - **Term1** = F^A_0 − F^T_45 = +0.074 Ah [0.022, 0.127]，SE 取 σ_TT,45。
   - **Term2** = F^T_45 − F^T_25 = +0.616 Ah [0.405, 0.829]，为 5 次切换的中位数，是最大的一项。
   - **Term3** = F^T_25 − F^A_k = +0.418 Ah [0.175, 0.660]，为 k = 1、2、4、5、6 的中位数。锚点 3 和 7 按登记的间隙规则被排除（WP0 D9）。
3. **G_noise 通过：** σ_TT,25 = 0.125 Ah（2 个 TT 配对），σ_TT,45 = 0.026 Ah（17 个 TT 配对），都 ≤ 0.30 Ah。
4. **G_E2：一致。**
   - J_DL1 中位数 0.705 Ah，Term2 中位数 0.616 Ah，|差| = 0.089 ≤ 0.20，不放宽。
   - A3 的跳变更小：经 r_45 修正后中位数 0.319 Ah，未修正 0.185 Ah；未修正值重现了 V2 研究的约 +0.18 Ah。
   - J 还包含台阶本身随温度的移动，而且 DL1 版本离散很大（0.22–1.19 Ah），所以这种一致只是较弱的支持，不是证实。
5. **λ 不平稳，它主导了区间宽度。**
   - TT 块的比值 λ = N/thr 在 45 °C 段从 −0.97·10⁻³（第 0 月）漂移到 −2.82·10⁻³（第 6 月）。每块的电量都是 377.4 Ah，所以 λ 每差 10⁻³ 对应 0.38 Ah。
   - 按登记的损耗规则，没有 TT 配对的五个 25 °C 段使用 25 °C 合并值 λ（−2.45·10⁻³），而这个值只来自第 5–6 月。
   - 结果，k = 1、2、4 的 Term3（0.42–0.60）和 j = 1–3 的 Term2 偏高；两者都随月份下降（Spearman −0.9）。
   - 一个**探索性、未登记**的变体改用时间上最近的 TT 段的 λ，得到 Term3 ≈ 0.13、Term2 ≈ 0.47、**T_top ≈ 0.68 Ah**，落在登记区间内、靠近下端。
   - λ 的漂移本身尚无解释：同样顶部之间的逐块不平衡从 −0.36 增大到 −1.13 Ah，符号与副反应相反，是一个随时间变化的测量偏差，留给第 13 轮。
6. **E3（物理诊断）没有信息量。**
   - ΔV（电池组，CV 结束 30 min 后，第一次 45 °C 补电减最后一次 25 °C 补电）= 42–61 mV，ΔT ≈ 20 K；其中最多 ±24 mV 可能来自熵项（假设每个电芯 ±0.3 mV/K）。
   - CK0 的 C/20 曲线在第 1 Ah 内下降 330 mV，之后是平的，所以三个窗口上的 s 为 148、22 和 −1.4 mV/Ah。
   - Term2_E3 的点估计为 1.9–2.7 Ah，区间下界无界，无法用来检验 Term2。
7. **哪个电芯决定顶部。**
   - 两种温度下，全部 41 次 CV 事件（包括锚点 0）都是 cell3，无论在 CV 结束时还是 30 min 后。
   - 30 min 后的顶部压差在 45 °C 为 65–88 mV，在 25 °C 为 19–24 mV（每次切换前后的最后一次 25 °C 补电与第一次 45 °C 补电）。
8. **Term2 与停机时长：** Spearman ρ = −0.40，Theil–Sen −11 mAh/h（n = 5）。没有自放电信号，且与月份混杂。

## 表格

- E1 共有 40 个相邻 CV 结束配对：19 个 TT、8 个 AT、5 个 X，另有 8 个不成对——7 个跨过检查日期，1 个跨过第 1 → 2 段边界（E05–E06，不是换温箱切换）。
- 7 个中的 E04–E05 两端都在第 1 段内，但第 1 段一直运行到 CK1 日期（2025-02-08 00:00）之后，所以按登记规则"(t_i, t_j] 内没有检查日期"被排除；第 1 段因此只剩 2 个 TT 配对。

E1 的配对与 λ、电量链分项、E2/E3 以及门槛的表格与英文部分相同（`pairs.csv`、`e1_chain.json`、`terms.csv`、`e2_e3.csv`、`e2_e3_summary.json`、`T_top.json`）。

| 门槛 | 结果 |
|---|---|
| G_noise | **通过**（σ_TT,25 0.125，σ_TT,45 0.026 ≤ 0.30） |
| G_E2 | **一致**（\|0.705 − 0.616\| = 0.089 ≤ 0.20），不放宽 |
| G_T | **未识别**（半宽 0.507 > 0.25） |
