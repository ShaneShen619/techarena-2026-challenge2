<a id="en"></a>

# Stage 7 — Round-3 leads

> **Language:** English · [中文](#zh)

Exposed-exploratory; proxies are not hidden truth. Protocol: `protocol.json`. Code: `../src/leads.py`, `run_7.py`. Outputs: `outputs/S7_*`.

**Result: both leads fail the common gates against V2.**

**The two models.**

- **SS_fixed.** Round 3's state-space model plus one free level offset o (prior N(0, 0.5²) Ah), with τ_tr = 8 d. Adding o required a modified copy of round 3's `fit_predict`; this deviation was registered before the run, and the round-3 file is unchanged.
- **V2_startcorr.** V2 with a registration β whose bottom-section change is corrected for the anchor start voltage.

## Results

MAE / MAX for Δ = 0 / 0.4 / 0.8 (pp):

| Model | MAE | MAX |
|---|---|---|
| V2 | 0.272 / 0.216 / 0.210 | 0.669 / 0.669 / 0.669 |
| SS_fixed (main) | 0.271 / 0.228 / 0.216 | 0.687 / 0.569 / 0.552 |
| SS_fixed, τ 5 d | 0.355 / 0.278 / 0.211 | 0.877 / 0.511 / 0.493 |
| SS_fixed, τ 3 d | 0.426 / 0.345 / 0.264 | 0.847 / 0.527 / 0.465 |
| V2_startcorr (main) | 0.282 / 0.226 / 0.220 | 0.669 / 0.669 / 0.669 |
| V2_startcorr, no shrink | 0.280 / 0.224 / 0.218 | 0.669 / 0.669 / 0.669 |

Per-checkup errors at Δ = 0.4 (pp):

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| V2 | +0.217 | +0.669 | +0.080 | +0.228 | +0.150 | −0.163 | −0.004 |
| SS_fixed | +0.295 | **−0.133** | −0.002 | +0.569 | +0.384 | −0.039 | −0.174 |
| V2_startcorr | +0.217 | +0.669 | +0.080 | +0.265 | +0.127 | −0.103 | +0.118 |

**Gates.**

| Model | G-proxy | G-epsfree | G-robust | G-regress | G-pseudo |
|---|---|---|---|---|---|
| SS_fixed | fail | fail (0.202 vs 0.216 − 0.02) | 2/6 | fail (+0.34, CK4) | pass (0.195 vs 0.240) |
| V2_startcorr | fail | fail (0.227) | 1/6 | pass | pass |

## Notes

- **The level offset does not remove SS's ε dependence.** SS_fixed's fitted o drifts from 0 to about −0.96 Ah across cutoffs, absorbing part of the mismatch between the anchor-0 definition and the 25 °C anchors. Its errors still change with Δ (MAE 0.271 → 0.216).
- **SS_fixed moves the error, not removes it.** It is the first model that brings CK2 near zero (−0.13). It also does well on the pseudo-gaps (PG1 0.098). But it gets CK4/CK5 worse in exchange, and it is not robust across step methods (dV/dQ-peak MAE 0.553).
- **The start-voltage correction of the registration β is large but changes little.** The coefficient c is −25 to −41 Ah per V. The resulting β (1.23–1.30) differs little from V2's in effect.

---

<a id="zh"></a>

# 阶段 7——第三轮留下的线索

> **语言：** [English](#en) · 中文

已曝光的探索性研究；代理不是隐藏真值。协议：`protocol.json`。代码：`../src/leads.py`、`run_7.py`。输出：`outputs/S7_*`。

**结果：两条线索相对 V2 都未通过通用接纳门。**

**两个模型。**

- **SS_fixed。** 第三轮的状态空间模型加一个自由水平偏置 o（先验 N(0, 0.5²) Ah），τ_tr = 8 天。加入 o 需要复制并修改第三轮的 `fit_predict`；这一偏离在运行前已登记，第三轮原文件未改动。
- **V2_startcorr。** V2 改用配准 β，其中底部段变化按锚点起点电压做了修正。

## 结果

Δ = 0 / 0.4 / 0.8 下的 MAE / MAX（pp）：

| 模型 | MAE | MAX |
|---|---|---|
| V2 | 0.272 / 0.216 / 0.210 | 0.669 / 0.669 / 0.669 |
| SS_fixed（主） | 0.271 / 0.228 / 0.216 | 0.687 / 0.569 / 0.552 |
| SS_fixed，τ 5 天 | 0.355 / 0.278 / 0.211 | 0.877 / 0.511 / 0.493 |
| SS_fixed，τ 3 天 | 0.426 / 0.345 / 0.264 | 0.847 / 0.527 / 0.465 |
| V2_startcorr（主） | 0.282 / 0.226 / 0.220 | 0.669 / 0.669 / 0.669 |
| V2_startcorr，不收缩 | 0.280 / 0.224 / 0.218 | 0.669 / 0.669 / 0.669 |

Δ = 0.4 下的逐检查点误差（pp）：

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| V2 | +0.217 | +0.669 | +0.080 | +0.228 | +0.150 | −0.163 | −0.004 |
| SS_fixed | +0.295 | **−0.133** | −0.002 | +0.569 | +0.384 | −0.039 | −0.174 |
| V2_startcorr | +0.217 | +0.669 | +0.080 | +0.265 | +0.127 | −0.103 | +0.118 |

**接纳门。**

| 模型 | G-proxy | G-epsfree | G-robust | G-regress | G-pseudo |
|---|---|---|---|---|---|
| SS_fixed | 不通过 | 不通过（0.202，门槛为 0.216 − 0.02） | 2/6 | 不通过（CK4 +0.34） | 通过（0.195 对 0.240） |
| V2_startcorr | 不通过 | 不通过（0.227） | 1/6 | 通过 | 通过 |

## 说明

- **水平偏置没有消除 SS 对 ε 的依赖。** SS_fixed 拟合出的 o 在各截断点之间从 0 漂到约 −0.96 Ah，吸收了锚点 0 定义与 25 °C 锚点之间的部分失配。它的误差仍随 Δ 变化（MAE 0.271 → 0.216）。
- **SS_fixed 只是把误差挪了位置，没有消除。** 它是第一个把 CK2 拉到接近零（−0.13）的模型，在伪缺口上也表现好（PG1 0.098）；但代价是 CK4/CK5 变差，而且在不同台阶方法之间不稳健（dV/dQ 峰方法下 MAE 0.553）。
- **配准 β 的起点电压修正系数很大，但影响很小。** 系数 c 为 −25 至 −41 Ah/V，得到的 β（1.23–1.30）在效果上与 V2 的差别不大。
