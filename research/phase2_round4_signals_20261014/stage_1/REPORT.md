<a id="en"></a>

# Stage 1 — Month-end denoising by in-segment regression

> **Language:** English · [中文](#zh)

Exposed-exploratory; proxies are not hidden capacity truth.

**Result: S1 fails the common gates** (MAE 0.242 vs V2's 0.216 at Δ = 0.4; better than V2 in 1 of 6 step variants). **Key diagnostic:** within a 45 °C segment, the step depths scatter around a straight line by only 0.012–0.036 Ah (residual SD). Single-point measurement noise is therefore an order of magnitude smaller than V2's remaining errors (about 0.2 Ah). V2's error is systematic, not measurement noise.

Protocol: `protocol.json` (registered before any stage-1 code ran). Code: `../src/endfit.py`, `run_1.py`. Outputs: `outputs/S1_*`.

## Results (Δ = 0.4, pp)

| Model | CK4 | CK5 | CK6 | CK7 | MAE | ε-free CK2–7 |
|---|---|---|---|---|---|---|
| V2 | +0.228 | +0.150 | −0.163 | −0.004 | 0.216 | 0.216 |
| **S1** (Theil–Sen line at the checkup date) | +0.364 | +0.149 | −0.209 | −0.008 | 0.242 | 0.247 |
| S1, OLS | +0.378 | +0.130 | −0.229 | +0.006 | 0.244 | 0.249 |
| S1, last 3 steps | +0.327 | +0.134 | −0.156 | −0.019 | 0.229 | 0.231 |
| S1, at last step + V2 rate | +0.253 | +0.159 | −0.203 | −0.001 | 0.226 | 0.227 |
| S1, β = 1 | +0.393 | +0.247 | −0.021 | +0.219 | 0.264 | 0.272 |

CK1–CK3 use the fallback and are identical to V2 (+0.217, +0.669, +0.080).

**Gates.** G-proxy fail; G-epsfree fail (0.247 vs 0.216); G-robust 1/6; G-regress pass (max increase 0.136 pp, CK4); G-pseudo pass (0.250 vs 0.240). A4 smoothing 1/2/3 Ah gives S1 0.249/0.242/0.232 against V2 0.224/0.216/0.205.

## What drives the change

- **Fitted slopes are stable:** −0.022 to −0.044 Ah/day. Residual SD around the line is 0.012–0.036 Ah.
- **Extrapolation, not denoising, causes the change.** Fitting the line and then extrapolating it to the checkup date (S1) moves CK4 the most (+0.23 → +0.36). The "at last step + V2 rate" variant stays close to V2. The difference therefore comes from how each month-end is carried to its checkup date, not from denoising the measured value.
- **Consequence for the next stages.** Directions 2–4 aim to add measurements, which helps only if measurement noise matters. Their audits still run as registered, but the expected gain is small.

---

<a id="zh"></a>

# 阶段 1——用段内回归给月末值去噪

> **语言：** [English](#en) · 中文

已曝光的探索性结果；代理不是隐藏容量真值。

**结果：S1 未通过通用接纳门**（Δ = 0.4 下 MAE 0.242，V2 为 0.216；6 种台阶变体中只有 1 种优于 V2）。**关键诊断：** 在同一个 45 °C 段内，台阶深度相对拟合直线的残差标准差只有 0.012–0.036 Ah。单点测量噪声因此比 V2 剩余误差（约 0.2 Ah）小一个数量级，V2 的误差是系统性的，不是测量噪声。

协议：`protocol.json`（在阶段 1 任何代码运行之前登记）。代码：`../src/endfit.py`、`run_1.py`。输出：`outputs/S1_*`。

## 结果（Δ = 0.4，pp）

| 模型 | CK4 | CK5 | CK6 | CK7 | MAE | 与 ε 无关的 CK2–7 |
|---|---|---|---|---|---|---|
| V2 | +0.228 | +0.150 | −0.163 | −0.004 | 0.216 | 0.216 |
| **S1**（Theil–Sen 直线在检查日的值） | +0.364 | +0.149 | −0.209 | −0.008 | 0.242 | 0.247 |
| S1，OLS | +0.378 | +0.130 | −0.229 | +0.006 | 0.244 | 0.249 |
| S1，只用最后 3 次台阶 | +0.327 | +0.134 | −0.156 | −0.019 | 0.229 | 0.231 |
| S1，取最后一次台阶时刻 + V2 速率项 | +0.253 | +0.159 | −0.203 | −0.001 | 0.226 | 0.227 |
| S1，β = 1 | +0.393 | +0.247 | −0.021 | +0.219 | 0.264 | 0.272 |

CK1–CK3 走回退分支，与 V2 相同（+0.217、+0.669、+0.080）。

**接纳门。** G-proxy 不通过；G-epsfree 不通过（0.247 对 0.216）；G-robust 1/6；G-regress 通过（最大增加 0.136 pp，CK4）；G-pseudo 通过（0.250 对 0.240）。A4 平滑 1/2/3 Ah 下，S1 为 0.249/0.242/0.232，V2 为 0.224/0.216/0.205。

## 变化的来源

- **拟合斜率很稳定：** −0.022 至 −0.044 Ah/天；相对直线的残差标准差为 0.012–0.036 Ah。
- **变化来自外推，而不是去噪。** 拟合直线后再外推到检查日（S1）对 CK4 影响最大（+0.23 → +0.36）；"取最后一次台阶时刻 + V2 速率项"的变体则与 V2 接近。所以差异来自如何把各月末值推到检查日，而不是对测量值去噪。
- **对后续阶段的影响。** 方向 2–4 的目标是增加测量次数，只有在测量噪声起作用时才有帮助。它们的审计仍按登记执行，但预期收益很小。
