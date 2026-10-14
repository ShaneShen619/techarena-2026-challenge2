<a id="en"></a>

# Stage 2 — Step crossings in daily dynamic operation

> **Language:** English · [中文](#zh)

Exposed-exploratory; no proxy metric was computed in this stage.

**Result: the registered exit rule triggers, so the channel is diagnostic only and stage 2b was not run.** Coulomb counting between consecutive full charges does not close: the median |closure| is 0.61 Ah, against a limit of 0.2 Ah.

Protocol: `audit_protocol.json` (registered before the audit). Code: `../src/dyncross.py`, `audit_2.py`. Outputs: `outputs/audit_*`.

## Audit results (`outputs/audit_summary.json`)

| Check | Value | Limit | Pass |
|---|---|---|---|
| Program reproduction, median \|diff\| (P90) | 0.219 Ah (0.390) | ≤ 0.3 | yes |
| Coulomb closure between consecutive CV ends, median \|net Ah\| (P90) | 0.608 Ah (0.969) | ≤ 0.2 | **no** |
| Months with ≥ 3 additional located 45 °C crossings | 6 of 7 | ≥ 5 | yes |

- **Candidates.** 71 crossings were found. All are in the ~10 A discharge band and all were located; 41 lie inside program excursions. No charge-direction run spans the step region. The median four-cell range is 0.55 Ah.
- **The "additional" crossings are not new information in time.** All 30 occur 4.0 days after the last CV end. They are the deeper discharge on day 4 of each 5-day cycle, so they add about one point per cycle, measured at the moment when coulomb drift is largest.
- **The closure is systematically negative:** mean −0.66 Ah per 4.8 days, SD 0.26. This looks like a small current offset (about −5 to −6 mA) or a different end-of-charge state, not random noise.

## Lead (not evaluated; the exit rule cannot be changed after the audit)

Estimating the closure drift causally (per day, from past CV-to-CV pairs) and subtracting it could make the day-4 crossings usable. Stage 1 showed, however, that step measurement noise is not V2's bottleneck, so even a corrected channel would mostly add points of the kind V2 does not need.

---

<a id="zh"></a>

# 阶段 2——日常动态运行中的台阶穿越

> **语言：** [English](#en) · 中文

已曝光的探索性研究；本阶段没有计算任何代理指标。

**结果：触发了登记的退出规则，该通道只作诊断，没有进行 2b。** 相邻两次满充之间的库仑计数闭合不上：闭合差绝对值的中位数为 0.61 Ah，上限是 0.2 Ah。

协议：`audit_protocol.json`（审计前登记）。代码：`../src/dyncross.py`、`audit_2.py`。输出：`outputs/audit_*`。

## 审计结果（`outputs/audit_summary.json`）

| 检查项 | 数值 | 上限 | 是否通过 |
|---|---|---|---|
| 程序台阶复现，\|差值\| 中位数（P90） | 0.219 Ah（0.390） | ≤ 0.3 | 是 |
| 相邻 CV 末端之间的库仑闭合，\|净 Ah\| 中位数（P90） | 0.608 Ah（0.969） | ≤ 0.2 | **否** |
| 有 ≥ 3 次额外 45 °C 穿越被定位的月份数 | 7 个月中 6 个 | ≥ 5 | 是 |

- **候选穿越。** 共找到 71 次，全部位于约 10 A 的放电电流带内，并全部定位成功；其中 41 次落在程序放电区间内。充电方向没有任何一段覆盖台阶区。四芯极差中位数为 0.55 Ah。
- **"额外"穿越在时间上并没有带来新信息。** 30 次全部发生在上次 CV 末端之后 4.0 天，即每个 5 天周期第 4 天那次较深的放电。所以每个周期只多一个点，而且恰好是库仑漂移最大的时候。
- **闭合差系统性为负：** 平均每 4.8 天 −0.66 Ah，标准差 0.26。这更像是一个小的电流偏置（约 −5 至 −6 mA）或满充终点状态的差异，而不是随机噪声。

## 线索（未评估；审计后不能修改退出规则）

如果用过去的 CV 到 CV 闭合差因果地估计每天的漂移并扣除，第 4 天的穿越或许可以用上。但阶段 1 已经表明台阶测量噪声不是 V2 的瓶颈，所以即使校正后，这条通道增加的也主要是 V2 并不缺的那类数据点。
