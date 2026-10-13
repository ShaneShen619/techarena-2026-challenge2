<a id="en"></a>

# Stage C — Forward state-space fusion

> **Language:** English · [中文](#zh)

**Result: the registered state-space model (SS) fails every gate against V2.** MAE at ε0+0.4 is 0.355 vs 0.216, and it beats V2 in 0 of 6 step variants. The model is rejected.

Protocol: `protocol.json`.

**Model.** Capacity Q(t) is piecewise linear, with a 25 °C rate and a 45 °C rate per month and random-walk priors between months.

- **Anchors** observe Q (SD 0.05 Ah).
- **Steps** observe s0 + ΔQ/β + δ·[45 °C] + A_m·exp(−Δt/τ) (SD 0.15 Ah).
- **Fit:** MAP at every cutoff on visible data only.

## Results (`outputs/C_metrics.csv`, `C_long.csv`, `C_gates.json`)

Per-checkup error at ε0+0.4, in pp:

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 | MAE |
|---|---|---|---|---|---|---|---|---|
| V2 | +0.22 | +0.67 | +0.08 | +0.23 | +0.15 | −0.16 | −0.00 | 0.216 |
| SS (main, τ = 5 d) | +0.48 | +0.50 | −0.04 | +0.70 | +0.46 | −0.07 | −0.23 | 0.355 |
| SS, τ = 8 d (variant) | +0.29 | +0.04 | +0.05 | +0.70 | +0.46 | −0.00 | −0.16 | 0.243 |
| SS, β = 1 (variant) | +0.48 | +0.50 | +0.68 | +0.83 | +1.00 | +0.79 | +0.91 | 0.740 |

**Pseudo scenarios (MAE).**

| | PG1 | PG2 | PC5 | PC10 |
|---|---|---|---|---|
| SS | 0.136 | 0.225 | 0.336 | 0.353 |
| V2 | 0.251 | 0.207 | 0.302 | 0.340 |

SS handles the hard PG1 gap better, but loses elsewhere.

**Fitted structure.**

- The temperature offset δ is fitted at 0.15–0.22 Ah, consistent with the +0.18 Ah found by hand.
- The post-checkup transient amplitude A_m is fitted at +0.5 to +0.8 Ah. The step is deeper right after a checkup and decays.

Both effects are real in the data.

**Calibration (descriptive, 7 points).** Mean |z| = 1.52, and 71 % of errors are within 2 SD. The predicted SD is too small.

## Why it fails

1. **ε leaks into the rates.** Anchor 0 is fixed at 100.41 Ah, while the 25 °C anchors move with ε. The model explains the resulting offset as month-0 degradation, and the random-walk prior carries it forward. The error is therefore not ε-free (CK2–7 MAE 0.414 / 0.334 / 0.267 for the three ε values), unlike V2. This is a structural flaw of the registered design.
2. **CK4 and CK5 get worse (+0.70, +0.46).** The model fits a single, mostly linear in-month path with an exponential transient. The phase-matched difference of V2 avoids having to model the transient at all.
3. **The β = 1 variant is far worse.** The step-to-capacity ratio matters, as in V2.

## Lead for a future, pre-registered test (not evaluated as a candidate)

- **Remove the ε leak:** give anchor 0 its own free offset, or fit the rates only between 25 °C anchors.
- **Use a longer transient time constant** (τ ≈ 8 d did best of the three).

Both were seen only as variants here, so they cannot be claimed as improvements.

---

<a id="zh"></a>

# 阶段 C——前向状态空间融合

> **语言：** [English](#en) · 中文

**结果：登记的状态空间模型（SS）相对 V2 的接纳门全部不通过。** ε0+0.4 下 MAE 为 0.355（V2 为 0.216），6 种台阶变体中 0 种优于 V2，模型被淘汰。

协议：`protocol.json`。

**模型。** 容量 Q(t) 分段线性，每月各有一个 25 °C 速率和一个 45 °C 速率，月与月之间是随机游走先验。

- **锚点**直接观测 Q（标准差 0.05 Ah）。
- **台阶**观测 s0 + ΔQ/β + δ·[45 °C] + A_m·exp(−Δt/τ)（标准差 0.15 Ah）。
- **拟合：**每个截断点只用可见数据做 MAP 拟合。

## 结果（`outputs/C_metrics.csv`、`C_long.csv`、`C_gates.json`）

ε0+0.4 下的逐检查点误差（pp）：

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 | MAE |
|---|---|---|---|---|---|---|---|---|
| V2 | +0.22 | +0.67 | +0.08 | +0.23 | +0.15 | −0.16 | −0.00 | 0.216 |
| SS（主，τ = 5 天） | +0.48 | +0.50 | −0.04 | +0.70 | +0.46 | −0.07 | −0.23 | 0.355 |
| SS，τ = 8 天（变体） | +0.29 | +0.04 | +0.05 | +0.70 | +0.46 | −0.00 | −0.16 | 0.243 |
| SS，β = 1（变体） | +0.48 | +0.50 | +0.68 | +0.83 | +1.00 | +0.79 | +0.91 | 0.740 |

**伪情景（MAE）。**

| | PG1 | PG2 | PC5 | PC10 |
|---|---|---|---|---|
| SS | 0.136 | 0.225 | 0.336 | 0.353 |
| V2 | 0.251 | 0.207 | 0.302 | 0.340 |

SS 在较难的 PG1 缺口上表现更好，其他情景则更差。

**拟合出的结构。**

- 温度偏移 δ 拟合为 0.15–0.22 Ah，与手算的 +0.18 Ah 一致。
- 检查后瞬态幅度 A_m 拟合为 +0.5 至 +0.8 Ah：检查刚结束时台阶更深，随后衰减。

这两个效应在数据中都真实存在。

**校准（描述性，7 个点）。** |z| 平均 1.52，71 % 的误差落在 2 倍标准差以内，说明预测标准差偏小。

## 失败原因

1. **ε 泄漏进了速率。** 锚点 0 固定为 100.41 Ah，而 25 °C 锚点随 ε 移动。模型把由此产生的偏移解释成第 0 月的老化，再经随机游走先验传到之后各月。因此误差不再与 ε 无关（三个 ε 下 CK2–7 MAE 依次为 0.414 / 0.334 / 0.267），这一点与 V2 不同。这是登记方案本身的结构缺陷。
2. **CK4、CK5 变差（+0.70、+0.46）。** 模型只用一条基本线性的月内轨迹加指数瞬态去拟合；V2 的同相位差分则根本不需要对瞬态建模。
3. **β = 1 的变体差得多。** 和 V2 一样，台阶与容量之间的比例很重要。

## 留给以后预登记测试的线索（未作为候选评估）

- **消除 ε 泄漏：**给锚点 0 单独一个自由偏置，或只在 25 °C 锚点之间拟合速率。
- **用更长的瞬态时间常数**（三个取值中 τ ≈ 8 天最好）。

这两点在本轮只是作为变体看到的，因此不能当作改进来宣称。
