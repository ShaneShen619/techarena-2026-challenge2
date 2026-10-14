<a id="en"></a>

# Stage 4 — CK2 analysis (descriptive, exposed)

> **Language:** English · [中文](#zh)

Run after the stage 3 results were committed (`492ab9c`). Code: [ck2.py](ck2.py); output: [outputs/S4_ck2.json](outputs/S4_ck2.json). CK2 is a single, already-exposed point; nothing here was tuned.

## CK2 errors at Δ = 0.4 (pp)

| Model | CK2 error |
|---|---|
| V2 (fallback = M4) | +0.669 |
| **S_main (z = 0.2)** | **+0.565** |
| S, z free (G1) | +0.616 |
| S, z = 0.5 (report only) | −0.206 |
| S, prior only | +0.393 |
| S, z = 1 (linear law, G4) | −2.134 |
| D1 (round 3, linear rate extrapolation) | −1.427 |
| D2 (round 3) | −1.049 |

## Decomposition of S_main's CK2 prediction

At the CK2 cutoff, S_main is fitted on one anchor pair (0 → 1): A_cal = 1.82 Ah/d^0.2, and A_cyc stays at its prior (7.8 × 10⁻⁶). The predicted loss from anchor 1 (02-11 23:08) to the horizon (03-14 23:08) is 0.756 Ah:

| Part | Interval | Effective days | Effective kAh | Loss (Ah) |
|---|---|---|---|---|
| segment 2, observed | 02-11 23:08 → 02-19 09:50 | 7.8 | 1.27 | 0.116 |
| segment 3, extrapolated | 02-19 09:50 → 03-11 15:36 | 54.6 | 8.57 | 0.614 |
| checkup interval | 03-11 15:36 → 03-14 23:08 | 3.3 | 0 | 0.026 |

The proxy implies a month-1 loss of about 0.756 + 0.565 × 1.02 ≈ 1.33 Ah. S_main therefore under-predicts the month's loss by about 0.58 Ah.

## Was the extrapolation of segment 3 the problem? No.

- Once segment 3 becomes visible (after the CK2 cutoff): it lasted 19.8 days with 3074 Ah. The registered rule extrapolated 20.2 days and 3173 Ah (+3 %).
- With the same fitted parameters but the true segment-3 stress, the predicted loss changes by only −0.013 pp.
- The CK2 error comes from the **law's shape and scale**, not from the missing stress data. With one pair from a break-in month, a strongly concave law (z = 0.2) under-predicts month 1. z = 0.5 slightly over-predicts, and the linear law (z = 1) over-predicts by a factor of about 2.6, which is the same failure as round 3's D1/D2.

## Verdict on H-A

**Supported in direction, weak in size, and inconclusive as evidence.**

- A sublinear law avoids the over-correction of linear extrapolation: the error sign stays positive and the size falls from 0.669 to 0.565 pp.
- The registered main configuration gains only 0.10 pp, and the result hinges on z, which this single exposed point cannot pin down: z = 0.2 → +0.57, z = 0.5 → −0.21.

---

<a id="zh"></a>

# 第 4 阶段——CK2 分析（描述性，已曝光）

> **语言：** [English](#en) · 中文

在第 3 阶段结果提交（`492ab9c`）之后运行。代码：[ck2.py](ck2.py)；输出：[outputs/S4_ck2.json](outputs/S4_ck2.json)。CK2 只是一个已曝光的点；这里没有调任何参数。

## Δ = 0.4 时的 CK2 误差（pp）

| 模型 | CK2 误差 |
|---|---|
| V2（回退 = M4） | +0.669 |
| **S_main（z = 0.2）** | **+0.565** |
| S，z 自由（G1） | +0.616 |
| S，z = 0.5（仅报告） | −0.206 |
| S，仅先验 | +0.393 |
| S，z = 1（线性律，G4） | −2.134 |
| D1（第三轮，线性速率外推） | −1.427 |
| D2（第三轮） | −1.049 |

## S_main 的 CK2 预测分解

CK2 截断时，S_main 只用一个锚点对（0 → 1）拟合：A_cal = 1.82 Ah/d^0.2，A_cyc 停在先验值（7.8 × 10⁻⁶）。从锚点 1（02-11 23:08）到预测时点（03-14 23:08），预测损失为 0.756 Ah：

| 部分 | 区间 | 有效天数 | 有效 kAh | 损失（Ah） |
|---|---|---|---|---|
| 第 2 段，观测 | 02-11 23:08 → 02-19 09:50 | 7.8 | 1.27 | 0.116 |
| 第 3 段，外推 | 02-19 09:50 → 03-11 15:36 | 54.6 | 8.57 | 0.614 |
| 检查区间 | 03-11 15:36 → 03-14 23:08 | 3.3 | 0 | 0.026 |

代理隐含的第 1 月损失约为 0.756 + 0.565 × 1.02 ≈ 1.33 Ah，因此 S_main 把这个月的损失少算了约 0.58 Ah。

## 问题出在第 3 段的外推吗？不是。

- 第 3 段在 CK2 截断之后才可见：实际持续 19.8 天、3074 Ah。登记的规则外推为 20.2 天、3173 Ah（+3 %）。
- 用同样的拟合参数、但换成第 3 段的真实应力，预测损失只变化 −0.013 pp。
- CK2 的误差来自**定律的形状和尺度**，而不是缺失的应力数据。只有一个来自磨合月的锚点对时，强凹的定律（z = 0.2）少算了第 1 月；z = 0.5 略微多算；线性律（z = 1）多算约 2.6 倍，与第三轮 D1/D2 的失败一样。

## 对 H-A 的结论

**方向上得到支持，幅度较弱，作为证据无定论。**

- 次线性定律避免了线性外推的过度修正：误差符号保持为正，大小从 0.669 降到 0.565 pp。
- 登记的主配置只改进了 0.10 pp，而且结果取决于 z，这一个已曝光的点定不下 z：z = 0.2 → +0.57，z = 0.5 → −0.21。
