<a id="en"></a>

# V2: Phase-Matched 45 °C Step Differencing + Physics β — Validation Report

> **Language:** English · [中文](#zh)

- **Run date:** 2026-10-13.
- **Protocol:** frozen before evaluation in [protocol.json](protocol.json) (SHA256 `072395c8…`). It contains one amendment, made before any code was written.
- **Base study:** [../phase2_anchor_step_20261013/FINAL_REPORT.md](../phase2_anchor_step_20261013/FINAL_REPORT.md). Its event-extraction code `events.py` is reused unchanged.

## Conclusions first

**On the proxy labels, V2 lowers the MAE from M4's 0.29 pp to 0.22 pp (ε0+0.4). The ε-independent MAE on CK2–CK7 falls from 0.30 to 0.22 pp. The pre-registered gates H1–H6 all pass.**

The maximum error does not change: it is still CK2 at 0.67 pp. Under the protocol, CK2 does not meet the phase-matching condition, so it keeps M4.

**Important limits.**

- **This is an exposed, exploratory validation.** The decomposition and the errors for CK3–CK7 were computed by hand on the same data before registration, so the improvement on CK4–CK7 is not a blind result.
- **CK1–CK3 were not tuned on their own results.** Their rules were fixed without looking at their V2 errors, and in practice all three take the fallback branch, identical to M4.
- **All errors are proxy errors.**

## 1. Motivation: where M4's remaining error comes from

Splitting each month's step-depth change (base study, A2 main method) shows four things:

- **Temperature shift.** At each monthly 25 °C → 45 °C switch, the step depth jumps up by +0.14 to +0.22 Ah. In the CK1 → CK2 month the jump is +0.60.
- **Post-checkup transient.** Within 25 °C segments the step falls by 0.07–0.13 Ah/day, but only by 0.02–0.04 Ah/day within 45 °C segments. That is the opposite of temperature-accelerated ageing.
- **M4's difference spans both effects.** The first step after the anchor is at 25 °C and the last one at 45 °C. The two effects partly cancel, by a different amount each month. "Month total − anchor-to-anchor ΔQ" reproduces M4's per-checkup errors almost exactly.
- **β.** A4 shows that only 68–79 % of the loss lies in the step → top section. The step therefore under-reads the total loss by a factor of about 1.3–1.45.

## 2. Method (V2_main)

To predict CK_k, k ≥ 2:

- **Months.** Month m = the step measurements after anchor m and before anchor m+1 (amendment 1).
- **Month-end value.** E45(m) = the last 45 °C step in month m; d(m) = its distance in days to the CK_{m+1} date.
- **Phase-matched branch.** It is taken when both of these hold:
  - the previous month has a complete 45 °C segment (≥ 3 steps) and d(k−2) ≤ 10 days;
  - in the current month, either d(k−1) ≤ 10 days or a rate can be estimated (≥ 3 steps).

```
Q̂ = Q_anchor(k−1) + β_k · [E45(k−1) − E45(k−2) + r · (d(k−1) − d(k−2))]
```

  - r is the Theil–Sen slope (Ah/day) of the current month's 45 °C steps.
  - The difference spans exactly one checkup plus one month, so it lines up with "anchor k−1 → anchor k". The temperature shift and the post-checkup transient cancel in it.
- **β_k.** It is computed in three steps:
  - Use the visible 25 °C anchors j = 2..k−1, each taken relative to anchor 1.
  - Regress their ΔQ_fc through the origin on Δ(charge-direction step → top distance, 2 Ah smoothing).
  - Shrink the result towards β0 = 1 (τ = 1 Ah²).
- **Fallback.** In every other case the prediction is exactly M4 (β = 1, no rate term).

Branches and β as they came out:

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| Branch | fallback | fallback | fallback | phase-matched | phase-matched | phase-matched | phase-matched |
| β | 1 | 1 | 1 (computed 1.27, not used) | 1.06 | 1.24 | 1.41 | 1.51 |
| SOH_est (%) | 95.992 | 95.137 | 93.541 | 92.811 | 92.081 | 91.331 | 90.821 |

## 3. Proxy evaluation

| Model | MAE ε0 / +0.4 / +0.8 (pp) | Max error (pp) | CK2–7 MAE (ε-independent) |
|---|---|---|---|
| M4 (V1, current submission) | 0.347 / 0.291 / 0.285 | 0.669 | 0.304 |
| **V2_main** | **0.272 / 0.216 / 0.210** | 0.669 | **0.216** |
| V2, β = 1 | 0.301 / 0.245 / 0.239 | 0.669 | 0.249 |
| V2, no rate term | 0.275 / 0.219 / 0.213 | 0.669 | 0.219 |
| V2, β also applied to the fallback | 0.285 / 0.229 / 0.223 | 0.669 | 0.231 |
| V2, β calibrated directly on past phase-matched pairs | 0.291 / 0.235 / 0.229 | 0.669 | 0.238 |
| V2, β0 = 1.3 (exposed value) | 0.269 / 0.213 / 0.207 | 0.669 | 0.212 |

Per-checkup errors (ε0+0.4, pp):

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| M4 | +0.22 | +0.67 | +0.08 | +0.28 | −0.11 | −0.40 | −0.28 |
| V2_main | +0.22 | +0.67 | +0.08 | +0.23 | +0.15 | −0.16 | −0.00 |

- **Phase-matched differencing on its own** (β = 1) accounts for about 60 % of the improvement (0.291 → 0.245). The physics β accounts for the rest (→ 0.216).
- **The rate term has very little effect** (0.003 pp), because both ends are a similar number of days before their checkups.
- **CK5 gets slightly worse.** Its error changes from −0.11 to +0.15, so the absolute error grows by 0.04 pp. This is within what H5 allows.

## 4. Robustness

- **Six step-detection methods.** V2 beats M4 on all of them (MAE at ε0+0.4):

| Method | main | band_narrow | windows_minus3 | windows_plus3 | dvdq_peak | ir_corrected |
|---|---|---|---|---|---|---|
| M4 | 0.291 | 0.278 | 0.373 | 0.412 | 0.404 | 0.321 |
| V2 | 0.216 | 0.217 | 0.274 | 0.304 | 0.333 | 0.238 |

- **Other parameters:**
  - τ = 0.25 / 4 gives MAE 0.216 / 0.219.
  - Validity windows of 7 / 14 days both give 0.216.
  - A4 smoothing of 1 / 3 Ah gives 0.224 / 0.205.

## 5. Acceptance gates

| Gate | Result |
|---|---|
| H1 causality | **Pass:** replacing future rows with noise, and fitting on pre-CK1 data only, both give bit-identical output |
| H2 proxy | **Pass:** lower MAE at all three ε values, same maximum error |
| H3 ε-independent | **Pass:** 0.216 ≤ 0.304 − 0.05 |
| H4 robustness | **Pass:** 6/6 detection methods, and every τ and validity-window setting |
| H5 no large regression | **Pass:** the largest increase in a single-point absolute error is 0.04 pp (CK5) |
| H6 reimplementation | **Pass:** the candidate class differs from the research implementation by ≤ 0.0004 pp (three-decimal rounding) |

## 6. Still unverifiable / risks

1. **Exposure.** The direction of the CK4–CK7 improvement was seen before registration. The robustness result holds on every variant, however, which suggests the improvement does not come from picking parameters.
2. **β runs high.**
   - CK7's β = 1.51 is above the whole-campaign A4 ratio (1.27–1.45).
   - It is sensitive to the A4 smoothing window (MAE 0.224 / 0.205 at 1 / 3 Ah).
   - If the LAM share falls later in life, β will overestimate the loss.
3. **No improvement on CK1–CK3.** CK2's 0.67 pp remains the largest error. The missing segment 3 cannot be extrapolated causally, because segment 1's rate reflects first-month break-in and cannot be used.
4. **The same risks as V1:**
   - ε;
   - the post-checkup recovery: whether the hidden C/20 value is before or after it;
   - a single pack.

   The proxy labels are themselves anchors, so only the leaderboard can settle these.

## 7. Reproduction

```bash
cd research/phase2_v2_phase_matched_20261013
python3 stage_v2_eval.py        # research implementation + proxy evaluation + gates -> outputs/V2_*
python3 stage_v2_candidate.py   # candidate class, causality checks, reimplementation, smoke test -> outputs/V2_candidate_*
```

Runs in about 15 s on Python 3.13 (numpy 2.4.2, pandas 3.0.0). The candidate class depends only on numpy / pandas.

---

<a id="zh"></a>

# V2：同相位 45 °C 台阶差分 + 物理 β：验证报告

> **语言：** [English](#en) · 中文

执行日期：2026-10-13。协议先冻结、后评估：[protocol.json](protocol.json)（SHA256 `072395c8…`，含一次修订，修订在写代码之前完成）。基础研究见 [../phase2_anchor_step_20261013/FINAL_REPORT.md](../phase2_anchor_step_20261013/FINAL_REPORT.md)；事件提取代码 `events.py` 原样复用。

## 结论先读

**V2 在代理标签上把 M4 的 MAE 从 0.29 pp 降到 0.22 pp（ε0+0.4），CK2–CK7 上与 ε 无关的 MAE 从 0.30 降到 0.22 pp。预登记的 H1–H6 门全部通过。** 最大误差没有变化，仍是 CK2 的 0.67 pp：按协议，CK2 不满足同相位条件，沿用 M4。

**重要边界**：这是已曝光的探索性验证。登记前已在同一批数据上手算过 CK3–CK7 的分解和误差，所以 CK4–CK7 的改进不是盲测结果。CK1–CK3 的规则是在没看它们 V2 误差的情况下定的（实际也都走了回退分支，与 M4 相同）。所有误差都是代理误差。

## 1. 动机：M4 的剩余误差从哪来

把每月的台阶深度变化拆开后（基础研究 A2 主方法）：

- **温度平移**：每月 25 °C → 45 °C 切换时，台阶深度上跳 +0.14 ~ +0.22 Ah（CK1→CK2 那个月为 +0.60）。
- **检查后瞬态**：25 °C 段下降 0.07–0.13 Ah/天，45 °C 段只有 0.02–0.04 Ah/天，方向与温度加速老化相反。
- **M4 的差分**跨越了这两种效应（锚点后首个台阶在 25 °C，末个在 45 °C），抵消量逐月不同。"月内合计 − 锚点间 ΔQ"几乎精确复现 M4 的逐点误差。
- **β**：A4 显示损失只有 68–79 % 落在台阶→满充端，所以台阶对总损失少读约 1.3–1.45 倍。

## 2. 方法（V2_main）

预测 CK_k，k ≥ 2：

- **月份**：第 m 月 = 锚点 m 之后、锚点 m+1 之前的台阶测量（修订 1）。
- **月末值**：E45(m) = 第 m 月最后一次 45 °C 台阶；d(m) = 它距 CK_{m+1} 日期的天数。
- **同相位分支**：同时满足以下条件时走这一分支：上月有完整 45 °C 段（≥3 次）且 d(k−2) ≤ 10 天；本月 d(k−1) ≤ 10 天或可估速率（≥3 次）。

```
Q̂ = Q_anchor(k−1) + β_k · [E45(k−1) − E45(k−2) + r · (d(k−1) − d(k−2))]
```

  - r：本月 45 °C 台阶的 Theil–Sen 斜率（Ah/天）。
  - 这个差分正好跨越一次检查加一个月，与"锚点 k−1 → 锚点 k"对齐，温度平移和检查后瞬态在差分中抵消。
- **β_k**：用可见的 25 °C 锚点 j = 2..k−1，相对锚点 1 的 ΔQ_fc 对 Δ（充电方向台阶→顶部距离，2 Ah 平滑）做过原点最小二乘，再向 β0 = 1 收缩（τ = 1 Ah²）。
- **回退**：其他情况与 M4 完全相同（β = 1，无速率项）。

实际分支与 β：

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| 分支 | 回退 | 回退 | 回退 | 同相位 | 同相位 | 同相位 | 同相位 |
| β | 1 | 1 | 1（算出 1.27，未用） | 1.06 | 1.24 | 1.41 | 1.51 |
| SOH_est (%) | 95.992 | 95.137 | 93.541 | 92.811 | 92.081 | 91.331 | 90.821 |

## 3. 代理评估

| 模型 | MAE ε0 / +0.4 / +0.8 (pp) | 最大误差 (pp) | CK2–7 MAE（与 ε 无关） |
|---|---|---|---|
| M4（V1，当前提交） | 0.347 / 0.291 / 0.285 | 0.669 | 0.304 |
| **V2_main** | **0.272 / 0.216 / 0.210** | 0.669 | **0.216** |
| V2，β = 1 | 0.301 / 0.245 / 0.239 | 0.669 | 0.249 |
| V2，无速率项 | 0.275 / 0.219 / 0.213 | 0.669 | 0.219 |
| V2，β 也用于回退 | 0.285 / 0.229 / 0.223 | 0.669 | 0.231 |
| V2，β 直接由历史同相位对标定 | 0.291 / 0.235 / 0.229 | 0.669 | 0.238 |
| V2，β0 = 1.3（曝光值） | 0.269 / 0.213 / 0.207 | 0.669 | 0.212 |

逐检查点误差（ε0+0.4，pp）：

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| M4 | +0.22 | +0.67 | +0.08 | +0.28 | −0.11 | −0.40 | −0.28 |
| V2_main | +0.22 | +0.67 | +0.08 | +0.23 | +0.15 | −0.16 | −0.00 |

- 同相位差分本身（β = 1）贡献了约 60 % 的改进（0.291 → 0.245），物理 β 贡献其余部分（→ 0.216）。
- 速率项影响很小（0.003 pp），因为两端距检查日的天数相近。
- CK5 的误差从 −0.11 变成 +0.15，绝对值增大 0.04 pp，在 H5 允许范围内。

## 4. 稳健性

- **6 种台阶检测方法**：V2 全部优于 M4（ε0+0.4 的 MAE）：

| 方法 | main | band_narrow | windows_minus3 | windows_plus3 | dvdq_peak | ir_corrected |
|---|---|---|---|---|---|---|
| M4 | 0.291 | 0.278 | 0.373 | 0.412 | 0.404 | 0.321 |
| V2 | 0.216 | 0.217 | 0.274 | 0.304 | 0.333 | 0.238 |

- **其他参数**：τ = 0.25 / 4 的 MAE 为 0.216 / 0.219；有效天数 7 / 14 的 MAE 都是 0.216；A4 平滑 1 / 3 Ah 的 MAE 为 0.224 / 0.205。

## 5. 接纳门

| 门 | 结果 |
|---|---|
| H1 因果 | **通过**：未来行替换为噪声、fit 只看 CK1 前数据，输出都逐位一致 |
| H2 代理 | **通过**：三个 ε 下 MAE 都更低，最大误差相同 |
| H3 与 ε 无关 | **通过**：0.216 ≤ 0.304 − 0.05 |
| H4 稳健 | **通过**：6/6 检测方法、全部 τ 与有效天数设置 |
| H5 无大退步 | **通过**：单点绝对误差最大增加 0.04 pp（CK5） |
| H6 重写一致 | **通过**：候选类与研究实现相差 ≤ 0.0004 pp（三位小数舍入） |

## 6. 仍不可验证 / 风险

1. **曝光**：CK4–CK7 的改进方向是在登记前看到的。不过稳健性在所有变体上都成立，说明改进不是参数挑选出来的。
2. **β 偏高**：CK7 的 β = 1.51，高于 A4 全程比例（1.27–1.45），对 A4 平滑窗敏感（1 / 3 Ah 时 MAE 0.224 / 0.205）。如果 LAM 比例在后期下降，β 会高估损失。
3. **CK1–CK3 没有改进**，CK2 的 0.67 pp 仍是最大误差：缺失的第 3 段无法因果外推（第 1 段的速率是首月磨合，不可用）。
4. **与 V1 相同的风险**：ε、检查后回弹（隐藏 C/20 处于回弹前还是回弹后）、单一电池组。代理标签本身就是锚点，这些都只能靠排行榜判断。

## 7. 复现

```bash
cd research/phase2_v2_phase_matched_20261013
python3 stage_v2_eval.py        # 研究实现 + 代理评估 + 门 -> outputs/V2_*
python3 stage_v2_candidate.py   # 候选类、因果检查、重写一致性、冒烟 -> outputs/V2_candidate_*
```

在 Python 3.13（numpy 2.4.2，pandas 3.0.0）上运行，约 15 s。候选类只依赖 numpy / pandas。
