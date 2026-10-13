<a id="en"></a>

# Stage A — Full-curve registration of the anchor charges

> **Language:** English · [中文](#zh)

Exposed-exploratory. Proxy values have already been seen and are not hidden capacity truth.

**Result: registration-based β fails the gates (MAE 0.242 vs V2's 0.216 at ε0+0.4; better than V2 in 0 of 6 step variants). V2's β is kept. The exploratory start-state diagnostic indicates substantial confounding: the registered bottom section cannot isolate active-material loss from the initial charge state.**

Protocol: `protocol.json`.

**Method.** Per cell, the CC part of each 25 °C anchor j ≥ 2 is registered to anchor 1 with a piecewise-linear Ah map:

- a bottom scale s_b up to the anchor-1 charge-side step;
- a top scale s_t above it;
- a free voltage offset.

The fit is a grid search on V(q).

## Registration (`outputs/A_registration.csv`, `A_split.csv`)

- **Identifiability.** The bottom scale is identified in 60 % of anchor-cells and the top scale in 85 %. The exit rule (≤ 50 %) was not triggered. On dV/dQ the figures are 100 % / 75 %.
- **Split of the anchor-to-anchor loss (four-cell mean, relative to anchor 1):**

| Anchor | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|
| ΔQ_fc (Ah) | −1.33 | −2.36 | −3.26 | −3.92 | −4.37 |
| Δbottom (Ah) | −0.38 | **+0.65** | −1.41 | −2.03 | −1.77 |
| top share | 0.72 | 1.27 | 0.57 | 0.48 | 0.60 |

- **β_reg** by checkup: 0.86 (CK4), 1.07, 1.27, 1.38 (CK7). These are lower than V2's 1.06–1.51.

## Evaluation (`outputs/A_metrics.csv`, `A_gates.json`)

| Model | MAE ε0 / +0.4 / +0.8 | MAX | ε-free CK2–7 |
|---|---|---|---|
| V2 | 0.272 / 0.216 / 0.210 | 0.669 | 0.216 |
| V2_reg (main) | 0.298 / 0.242 / 0.236 | 0.669 | 0.246 |
| V2_reg, dV/dQ | 0.330 / 0.274 / 0.268 | 0.669 | — |
| V2_reg, bottom-focused fit | 0.296 / 0.240 / 0.234 | 0.669 | — |

Gates: G-proxy fail, G-epsfree fail, G-robust 0/6, G-regress pass.

## Exploratory, not pre-registered: start state (`explore_start_state.py`)

- **The post-CK3 anchor started deeper than the others:** mean rest voltage 2.907 V/cell, against 2.95–2.99 V. Its registered bottom section is 0.65 Ah *longer*.
- **Across anchors, Δbottom correlates with the start voltage at r = −0.975.** This is consistent with start-state confounding of the bottom-section change; it does not establish a unique degradation mechanism, and β_reg may inherit that confounding.
- **No linear association was detected for Q_fc in this small diagnostic:** its residual from a √t trend has r = 0.04 against the CK0-tail conversion of the start voltage. This does not validate Q_fc as hidden C/20 capacity or rule out a start-state effect.
- **Idea for later, not evaluated.** A bottom section corrected for start state could make a registration β usable. It was not tried in this round, to avoid choosing a variant after seeing the results.

---

<a id="zh"></a>

# 阶段 A——锚点充电的全曲线配准

> **语言：** [English](#en) · 中文

已曝光探索性研究。代理值已被查看，不是隐藏容量真值。

**结果：配准得到的 β 未通过接纳门（ε0+0.4 下 MAE 0.242，V2 为 0.216；6 种台阶变体中 0 种优于 V2），保留 V2 的 β。探索性起点诊断提示明显混淆：配准底部段不能把活性物质损失与初始充电状态独立分开。**

协议：`protocol.json`。

**方法。** 对每颗电芯，把每个 25 °C 锚点 j ≥ 2 的 CC 部分用分段线性 Ah 映射配准到锚点 1：

- 底部缩放 s_b，作用到锚点 1 的充电方向台阶为止；
- 顶部缩放 s_t，作用于台阶以上；
- 一个自由电压偏置。

在 V(q) 上做网格搜索。

## 配准结果（`outputs/A_registration.csv`、`A_split.csv`）

- **可辨识性。** 底部缩放在 60 % 的锚点-电芯组合中可辨识，顶部缩放为 85 %，未触发退出规则（≤ 50 %）。在 dV/dQ 上分别为 100 % / 75 %。
- **锚点间损失的拆分（四芯平均，相对锚点 1）：**

| 锚点 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|
| ΔQ_fc（Ah） | −1.33 | −2.36 | −3.26 | −3.92 | −4.37 |
| Δ底部（Ah） | −0.38 | **+0.65** | −1.41 | −2.03 | −1.77 |
| 顶部占比 | 0.72 | 1.27 | 0.57 | 0.48 | 0.60 |

- **β_reg** 依次为 0.86（CK4）、1.07、1.27、1.38（CK7），低于 V2 的 1.06–1.51。

## 评估（`outputs/A_metrics.csv`、`A_gates.json`）

| 模型 | MAE ε0 / +0.4 / +0.8 | 最大误差 | 与 ε 无关的 CK2–7 |
|---|---|---|---|
| V2 | 0.272 / 0.216 / 0.210 | 0.669 | 0.216 |
| V2_reg（主） | 0.298 / 0.242 / 0.236 | 0.669 | 0.246 |
| V2_reg，dV/dQ | 0.330 / 0.274 / 0.268 | 0.669 | — |
| V2_reg，只拟合底部 | 0.296 / 0.240 / 0.234 | 0.669 | — |

接纳门：G-proxy 不通过，G-epsfree 不通过，G-robust 0/6，G-regress 通过。

## 探索性分析（未预登记）：起点状态（`explore_start_state.py`）

- **CK3 之后的锚点充电起点比其他锚点更深：** 平均静置电压 2.907 V/芯，其他为 2.95–2.99 V。它配准得到的底部段*长了* 0.65 Ah。
- **在各锚点之间，Δ底部与起点电压的相关系数为 r = −0.975。** 这个相关性与起点状态混淆相符，但不能唯一确定退化机制；β_reg 可能继承该混淆。
- **本小样本诊断未发现 Q_fc 的线性关联：** 它相对 √t 趋势的残差，与按 CK0 尾段换算的起点电压之间 r = 0.04。这不能验证 Q_fc 等于隐藏 C/20 容量，也不能排除起点状态效应。
- **留待以后的想法（未评估）。** 对底部段做起点状态修正，或许能让配准 β 变得可用。为避免看到结果后再挑变体，本轮没有尝试。
