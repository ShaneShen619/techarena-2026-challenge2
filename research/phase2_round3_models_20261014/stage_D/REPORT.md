<a id="en"></a>

# Stage D — Gap extrapolation with pseudo-gap selection

> **Language:** English · [中文](#zh)

Exposed-exploratory. Proxy values have already been seen and are not hidden capacity truth.

**Result: no rule beat "no extrapolation" (D0) on the pseudo-gaps, so the registered selection keeps D0 = V2. CK2 stays at +0.67 pp. Stage D brings no change to the model.**

Protocol: `protocol.json` (SHA256 in `protocol.sha256`). Extrapolation applies only on V2's fallback branch, and only when the last visible step is more than 10 days before the checkup.

## Pseudo-gap selection (`run_select.py`, `selection.json`)

PG1/PG2 truncate month k−1's 45 °C segment after its first / second deep discharge, for k = 4..7. MAE in pp at δ = ε0+0.4:

| Rule | PG1+PG2 | PC5 | PC10 |
|---|---|---|---|
| D0 no extrapolation | **0.229** | 0.302 | 0.340 |
| D1 45 °C step rate × β × gap | 0.361 | 0.428 | 0.687 |
| D2 Arrhenius √t + throughput model | 0.381 | 0.365 | 0.473 |
| D3 anchor √t trend (undefined for CK2, not selectable) | 0.217 | 0.229 | 0.176 |

- **D1 and D2 over-correct.** On the pseudo-gaps they add −0.3 to −0.9 Ah, which flips the errors from positive to negative.
- **Why, most likely.** The missing part of a truncated month changes the anchor-to-anchor capacity much less than "rate × days". Part of the month's loss is already in the truncated difference (the 25 °C transient), and part is offset by the +0.18 Ah temperature step that the fallback difference contains.

## Real data (`run_eval.py`, `outputs/D_*`)

Per-checkup error at ε0+0.4, in pp:

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| D0 (= V2) | +0.22 | +0.67 | +0.08 | +0.23 | +0.15 | −0.16 | −0.00 |
| D1 | +0.22 | −1.43 | +0.08 | +0.23 | +0.15 | −0.16 | −0.00 |
| D2 | +0.22 | −1.05 | +0.08 | +0.23 | +0.15 | −0.16 | −0.00 |

- **Leave-one-anchor-out** (anchor of month k−1 removed, k = 2..7): MAE D0 0.336, D1 0.514, D2 0.466, D3 0.301 (D3 again without CK2).
- **Gates:** no improvement against V2, so G-proxy and G-epsfree fail and the CK2 and PG gates fail; G-regress passes trivially.

## Exposure note

PC5 and PC10 at k = 2 contain no rows after 17 February, so they equal the real CK2 cut. Their D1/D2 CK2 values were printed by the selection script before the selection was committed. The selection rule used PG1 + PG2 only (`notes/DECISIONS.md`, DD.2).

## What this means

- The CK2 error cannot be fixed with a time- or throughput-based rate learned from other months.
- D3's good pseudo-cut numbers suggest that an anchor-level trend helps *pseudo-cutoffs* (missing recent data). It cannot be used for CK2, which has only one 25 °C anchor before it. This matters for the reduced-data-budget run and is passed on to stage C, where the state-space model carries a trend.

---

<a id="zh"></a>

# 阶段 D——缺段外推与伪缺口选择

> **语言：** [English](#en) · 中文

已曝光探索性研究。代理值已被查看，不是隐藏容量真值。

**结果：在伪缺口上没有规则胜过"不外推"（D0），按登记的选择规则保留 D0，即 V2。CK2 仍为 +0.67 pp，本阶段对模型没有改动。**

协议：`protocol.json`（SHA256 见 `protocol.sha256`）。外推只在 V2 的回退分支上使用，并且要求最后一次可见台阶距检查日超过 10 天。

## 伪缺口选择（`run_select.py`、`selection.json`）

PG1/PG2：对 k = 4..7，把第 k−1 月的 45 °C 段截断到第一次 / 第二次深放电之后。δ = ε0+0.4 下的 MAE（pp）：

| 规则 | PG1+PG2 | PC5 | PC10 |
|---|---|---|---|
| D0 不外推 | **0.229** | 0.302 | 0.340 |
| D1 45 °C 台阶速率 × β × 缺口天数 | 0.361 | 0.428 | 0.687 |
| D2 Arrhenius √t + 吞吐量模型 | 0.381 | 0.365 | 0.473 |
| D3 锚点 √t 趋势（CK2 处无定义，不可选） | 0.217 | 0.229 | 0.176 |

- **D1、D2 修正过头。** 在伪缺口上它们加入 −0.3 到 −0.9 Ah，把误差从正翻成负。
- **最可能的原因。** 被截断月份中缺失的那部分，对锚点间容量的影响远小于"速率 × 天数"：本月的部分损失已经包含在截断后的差分里（25 °C 瞬态），另有一部分被回退差分里 +0.18 Ah 的温度平移抵消。

## 真实数据（`run_eval.py`、`outputs/D_*`）

ε0+0.4 下的逐检查点误差（pp）：

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| D0（= V2） | +0.22 | +0.67 | +0.08 | +0.23 | +0.15 | −0.16 | −0.00 |
| D1 | +0.22 | −1.43 | +0.08 | +0.23 | +0.15 | −0.16 | −0.00 |
| D2 | +0.22 | −1.05 | +0.08 | +0.23 | +0.15 | −0.16 | −0.00 |

- **留一锚点**（去掉第 k−1 月的锚点，k = 2..7）：MAE 依次为 D0 0.336、D1 0.514、D2 0.466、D3 0.301（D3 同样不含 CK2）。
- **接纳门：** 相对 V2 没有改进，所以 G-proxy、G-epsfree 以及 CK2 门和 PG 门都不通过；G-regress 自然通过。

## 曝光说明

k = 2 时，PC5 和 PC10 在 2 月 17 日之后没有任何数据，等同于真实的 CK2 截断。它们在 D1/D2 下的 CK2 数值，在选择提交之前已由选择脚本打印出来。选择规则只用了 PG1 + PG2（见 `notes/DECISIONS.md` 的 DD.2）。

## 结论

- 用从其他月份学到的时间或吞吐量速率，修不好 CK2 的误差。
- D3 在伪截断上的好结果说明，锚点层面的趋势对*伪截断*（缺少近期数据）有帮助；但 CK2 之前只有一个 25 °C 锚点，D3 用不上。这与数据削减评估有关，也作为线索交给阶段 C：阶段 C 的状态空间模型带有趋势项。
