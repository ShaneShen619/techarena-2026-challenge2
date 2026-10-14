<a id="en"></a>

# Stage 4 — A feature inside the top 21 Ah of the ~5-day CCCV charges

> **Language:** English · [中文](#zh)

Exposed-exploratory; no proxy metric was computed in this stage.

**Result: the registered exit rule triggers.** No reproducible, monotonically moving dV/dQ feature exists 3–19 Ah below the CV end, so this direction is diagnostic only.

Protocol: `audit_protocol.json`. Code: `audit_4.py`. Outputs: `outputs/audit_features.csv`, `audit_summary.json`.

## Audit results (main smoothing 2 Ah; the ~5-day charges, anchors excluded)

| Feature | Located | Max within-month SD | Month medians (Ah below CV end) | Spearman vs month | Pass |
|---|---|---|---|---|---|
| dV/dQ maximum | 100 % | 0.00 | 5.0 in every month | — | no |
| dV/dQ minimum | 100 % | 0.58 | 16.4–16.8, no trend | −0.21 | no |

- **The "maximum" is an artefact.** It sits on the inner edge of the search window in every charge (5.0 Ah = 3 Ah + the smoothing half-width). dV/dQ simply keeps rising towards the end of charge, so there is no interior peak.
- **The minimum moves by less than its own scatter and has no trend.** With 1 Ah smoothing it drifts from 16.9 to 17.9 Ah (Spearman 0.86, still below 0.9). With 3 Ah it varies by ≤ 0.26 Ah within months but also shows no clear trend (Spearman 0.75).
- **Consequence.** The ~5-day charges carry no usable LLI marker above the graphite step. The step at 26–33 Ah below full remains the only in-month capacity feature, and only the program discharges reach it.

---

<a id="zh"></a>

# 阶段 4——约每 5 天一次的 CCCV 充电顶部 21 Ah 内的特征

> **语言：** [English](#en) · 中文

已曝光的探索性研究；本阶段没有计算任何代理指标。

**结果：触发登记的退出规则。** 在 CV 末端以下 3–19 Ah 内，不存在可重复、跨月单调移动的 dV/dQ 特征，因此该方向只作诊断。

协议：`audit_protocol.json`。代码：`audit_4.py`。输出：`outputs/audit_features.csv`、`audit_summary.json`。

## 审计结果（主平滑 2 Ah；约每 5 天一次的充电，不含锚点）

| 特征 | 定位率 | 最大月内标准差 | 各月中位数（CV 末端以下 Ah） | 与月份的 Spearman | 是否通过 |
|---|---|---|---|---|---|
| dV/dQ 最大值 | 100 % | 0.00 | 每个月都是 5.0 | — | 否 |
| dV/dQ 最小值 | 100 % | 0.58 | 16.4–16.8，没有趋势 | −0.21 | 否 |

- **"最大值"是假象。** 它在每次充电中都落在搜索窗口的内边界（5.0 Ah = 3 Ah + 平滑半宽）。dV/dQ 只是朝充电末端一路上升，窗口内部并没有峰。
- **最小值的移动小于它自身的离散，也没有趋势。** 1 Ah 平滑时它从 16.9 漂到 17.9 Ah（Spearman 0.86，仍低于 0.9）；3 Ah 平滑时月内变化 ≤ 0.26 Ah，但同样没有明显趋势（Spearman 0.75）。
- **结论。** 约每 5 天一次的充电在石墨台阶以上没有可用的 LLI 标志。满充以下 26–33 Ah 的台阶仍是唯一的月内容量特征，而只有程序放电能到达那里。
