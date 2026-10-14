<a id="en"></a>

# Stage 1 — Stress-history extraction (audit, no proxy metric)

> **Language:** English · [中文](#zh)

Code: [src/stress.py](../src/stress.py), [audit_1.py](audit_1.py). Outputs in [outputs/](outputs/).

## What the table contains

`stress_table(op, until, ck, horizon)` returns intervals with time-weighted and throughput-weighted cell temperature, total throughput and a kind flag. Observed rows are binned per hour.

| Kind | Rule |
|---|---|
| observed | consecutive rows within a segment; counters carry throughput across recording gaps |
| checkup | segment end → next segment start; 25 °C, 0 Ah (main) |
| seg_gap | a missing 45 °C segment once the following segment is visible: its counter jump, spread uniformly, at 45 °C + offset |
| extrapolated | last visible row → estimated month end (CK date + median visible end offset), at 45 °C + offset and the median Ah/day of the last 7 visible 45 °C days |

The hidden tail is split at the estimated month end: operation before it, checkup after it (decision D1.3).

## Findings

- **Throughput definition.** On gap-free rows the counters agree with ∫|I|dt to within 0.01 % in every segment ([S1_throughput_check.csv](outputs/S1_throughput_check.csv)). The counters are flat across checkups (checkups are not counted), and they carry segment 3 (3074 Ah).
- **Calendar.** The full campaign covers 235 days and 31,800 Ah of total throughput. Of these, 183 days are observed, 20 days are the missing segment 3 and 32 days are checkups ([S1_per_month_full.csv](outputs/S1_per_month_full.csv)). Month 5's checkup interval is long (12.4 days) because segment 11 ended three days before CK6.
- **Rule parameters.**
  - The 45 °C cell-temperature offset is +0.8 to +1.0 K above the chamber.
  - The 45 °C throughput rate is 150–165 Ah/day.
  - The median segment-end offset is −2.5 to +15.6 h.
  - The horizon lag L is 3.7–4.0 days (3 days before any anchor lag is visible, i.e. at CK1).
- **Extrapolation error** (hidden part vs the full data over the same interval, Arrhenius-weighted at Ea = 37.3 kJ/mol, [S1_extrapolation_audit.csv](outputs/S1_extrapolation_audit.csv)):
  - The effective-time error is within ±1.7 effective days, and the effective-throughput error within ±0.48 kAh, in every audited case except the month that ends at CK6.
  - There, segment 11 stopped three days early, so the rule adds about 4.2 effective days. That is about 8 % of one 45 °C segment's effective time (≈ 54 effective days).
  - This is the error of the extrapolation rule itself, not a model score.

No proxy value was computed in this stage.

---

<a id="zh"></a>

# 第 1 阶段——应力历史提取（审计，不算代理指标）

> **语言：** [English](#en) · 中文

代码：[src/stress.py](../src/stress.py)、[audit_1.py](audit_1.py)。输出在 [outputs/](outputs/)。

## 表中包含什么

`stress_table(op, until, ck, horizon)` 返回一组区间，含按时间加权和按吞吐加权的芯温、总吞吐量和类型标记。观测行按小时分箱。

| 类型 | 规则 |
|---|---|
| observed | 同一段内的相邻行；跨记录缺口的吞吐由计数器提供 |
| checkup | 段末 → 下一段开始；25 °C，0 Ah（主配置） |
| seg_gap | 下一段可见后，缺失的 45 °C 段：其计数器跳变均匀分配，温度为 45 °C + 偏差 |
| extrapolated | 最后可见行 → 估计的月末（CK 日期 + 可见段末偏差的中位数），温度为 45 °C + 偏差，吞吐速率取最近 7 个可见 45 °C 日 Ah/天的中位数 |

隐藏尾段在估计的月末处分开：之前算运行，之后算检查（决策 D1.3）。

## 发现

- **吞吐定义。** 在无缺口的行上，每一段的计数器与 ∫|I|dt 相差不到 0.01 %（[S1_throughput_check.csv](outputs/S1_throughput_check.csv)）。计数器在检查期间不变（检查不计入），并且覆盖了第 3 段（3074 Ah）。
- **日程。** 整个试验共 235 天、总吞吐 31,800 Ah。其中观测 183 天，缺失的第 3 段 20 天，检查 32 天（[S1_per_month_full.csv](outputs/S1_per_month_full.csv)）。第 5 月的检查区间较长（12.4 天），因为第 11 段在 CK6 前三天就结束了。
- **规则参数。**
  - 45 °C 下芯温比箱温高 0.8–1.0 K。
  - 45 °C 吞吐速率为 150–165 Ah/天。
  - 段末偏差中位数为 −2.5 至 +15.6 h。
  - 预测时点滞后 L 为 3.7–4.0 天（在看到任何锚点滞后之前，即 CK1 时，取 3 天）。
- **外推误差**（隐藏部分与完整数据在同一区间上的比较，按 Ea = 37.3 kJ/mol 做 Arrhenius 加权，[S1_extrapolation_audit.csv](outputs/S1_extrapolation_audit.csv)）：
  - 除了在 CK6 结束的那个月，所有审计情形的有效时间误差都在 ±1.7 个有效天以内，有效吞吐误差在 ±0.48 kAh 以内。
  - 那个月第 11 段提前三天停了，所以规则多算了约 4.2 个有效天，约占一个 45 °C 段有效时间（≈ 54 个有效天）的 8 %。
  - 这是外推规则本身的误差，不是模型得分。

本阶段没有计算任何代理值。
