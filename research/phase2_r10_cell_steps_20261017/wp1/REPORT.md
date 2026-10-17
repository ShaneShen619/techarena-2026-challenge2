<a id="en"></a>

# WP1 — Idea A: stabilise per-cell detection

> **Language:** English · [中文](#zh)

**Result: A3 passes every gate and is adopted for WP1.** A3 takes each cell's step location as the **median over the 6 detection variants**, then the **median over the 4 cells**. A1 and A2, which use the mean over variants, fail. Protocol [protocol.json](protocol.json) was committed in `51c7772` before evaluation. Script [run_wp1.py](run_wp1.py); outputs in [outputs/](outputs/). Rerun byte-identical.

| Gate (Δ 0.4) | SUB | A1 (mean, mean) | A2 (mean, median) | **A3 (median, median)** |
|---|---|---|---|---|
| pseudo | 0.1439 | 0.1348 ✓ | 0.1394 ✓ | **0.1342 ✓** |
| cold | 0.1703 | 0.1829 ✗ | 0.1776 ✗ | **0.1599 ✓** |
| changed non-real cases (16): SUB → cand, worst | 0.2172 | 0.2033, +0.094 ✗ | 0.2110, +0.112 ✗ | **0.1895, +0.060 ✓** |
| G_robust: LOVO ensembles within +0.005 / max Δcausal / max Δreal | — | 5/6, +0.005, +0.047 ✓ | 5/6, +0.006, +0.050 ✗ | **6/6, −0.004, +0.005 ✓** |
| G_event: SD of R_anc_b (40 events) | 0.2625 | 0.2589 ✓ | 0.2646 ✓ | **0.2621 ✓** |
| real MAE Δ0 / 0.4 / 0.8 | 0.197 / 0.126 / 0.146 | 0.236 / 0.165 / 0.139 | 0.236 / 0.165 / 0.144 | **0.191 / 0.120 / 0.142** |
| real MAX Δ0.4 (safety) | 0.228 | 0.378 ✗ | 0.362 ✗ | **0.237 ✓** |

**Real errors and SOH at Δ 0.4 (A3 vs SUB; real numbers are exposed, and differences < 0.25 pp are unresolvable):**

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| SUB err (pp) | +0.217 | +0.039 | +0.080 | +0.228 | +0.150 | −0.163 | −0.004 |
| A3 err (pp) | +0.210 | +0.039 | +0.140 | +0.237 | +0.084 | −0.068 | −0.060 |
| SUB SOH | 95.992 | 94.507 | 93.541 | 92.811 | 92.081 | 91.331 | 90.821 |
| A3 SOH | 95.984 | 94.507 | 93.600 | 92.821 | 92.015 | 91.426 | 90.765 |

**Causal cases.** Of the 16 cases that change, 11 improve; the worst change is CS CK3, +0.060 pp. The largest gains are CS CK6 (−0.402 → −0.302), PC5 CK6 (−0.274 → −0.197) and PC5 CK5 (+0.238 → +0.171).

**Diagnostics** ([outputs/wp1_decision.json](outputs/wp1_decision.json)):
- **Noise.** Per-cell detection noise σ is 0.083 Ah for the A3 ensemble, against 0.090 for main and 0.37 for dvdq_peak. The mean ensemble (A1/A2) is 0.091, because averaging lets dvdq_peak's 0.25 Ah grid noise in, while the median over variants does not. This is why only A3 survives.
- **Cell picture.** The round 8 cell picture survives the ensemble unchanged. Cell offsets are cell1 −0.37, cell2 +0.12, cell3 +0.23 and cell4 −0.12 Ah, each in 8/8 months. The spread is 0.56 / 0.61 / 0.69 Ah over months 0–2 / 3–5 / 6–7. **The divergence is real, not detection noise.** What A3 changes is how robustly it is combined.

---

<a id="zh"></a>

# WP1——想法 A：先把单体检测做稳

> **语言：** [English](#en) · 中文

**结论：A3 通过全部检验，作为 WP1 的采用候选。** A3 的做法是：每个电芯的台阶位置先在 **6 种检测变体上取中位数**，再对 **4 个电芯取中位数**。在变体上取平均的 A1 和 A2 没有通过。协议在评估前已提交（`51c7772`）。

- **因果指标：** 伪场景 0.144 → 0.134，冷启动 0.170 → 0.160，变化的 16 个非真实案例平均 |误差| 0.217 → 0.190（11 个变好，最差变化 +0.060）。
- **稳健性：** 6 个留一变体组合全部优于 SUB。
- **真实场景（已曝光）：** MAE 0.126 → 0.120，MAX 0.228 → 0.237。逐检查点见英文表格：CK5、CK6 改善，CK3、CK7 变差，都在 0.25 pp 的不可分辨范围内。
- **诊断：**
  - **噪声：** 中位数集成的检测噪声为 0.083 Ah（主变体 0.090，dvdq_peak 0.37）。平均集成会把 dvdq_peak 的网格噪声带进来，中位数则不会，这就是只有 A3 通过的原因。
  - **单体图景：** 第 8 轮的单体偏移和拉开在集成后依然存在。**拉开是真实的，不是检测噪声**；A3 改变的只是合并方式的稳健性。
