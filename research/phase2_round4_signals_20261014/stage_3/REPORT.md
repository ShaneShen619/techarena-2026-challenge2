<a id="en"></a>

# Stage 3 — Rest-point pseudo-OCV step

> **Language:** English · [中文](#zh)

Exposed-exploratory; no proxy metric was computed in this stage.

**Result: the registered exit rule triggers.** The operating profile has no rest periods near the graphite step, so no pseudo-OCV step can be fitted, and stage 3b was not run.

Protocol: `audit_protocol.json` (registered before the audit). Code: `audit_3.py`. Outputs: `outputs/audit_rests.csv`, `audit_fits.csv`, `audit_summary.json`.

## Audit results

- **Rests found.** There are 110 rest periods of ≥ 10 min (median 30.7 min) after a CV end in the same segment.
- **They all sit above the step.**
  - Rests after a charge lie 0–21.9 Ah below the CV end.
  - Rests after a discharge all lie at 10.2 Ah, right after the 20 A pulse.
  - The graphite step is at 26–33 Ah below the CV end.
- **No month qualifies.** Of the 28 rests in the 15–45 Ah window, none lies on the far side of the step (deeper than exp + 3 Ah). At most 3 points per month and temperature fall in the window, so no month qualifies (limit: ≥ 5 months at 45 °C with ≥ 8 points spanning the step).

## Meaning

The simulated storage profile rests only near the top of charge. Polarisation-free information about the graphite step is therefore not available during operation; only the anchor charges and the ~10 A program discharges see it.

---

<a id="zh"></a>

# 阶段 3——静置点伪 OCV 台阶

> **语言：** [English](#en) · 中文

已曝光的探索性研究；本阶段没有计算任何代理指标。

**结果：触发登记的退出规则。** 运行工况在石墨台阶附近没有静置段，无法拟合伪 OCV 台阶，因此没有进行 3b。

协议：`audit_protocol.json`（审计前登记）。代码：`audit_3.py`。输出：`outputs/audit_rests.csv`、`audit_fits.csv`、`audit_summary.json`。

## 审计结果

- **找到的静置段。** 同一段内、CV 末端之后时长 ≥ 10 分钟的静置共 110 个（中位时长 30.7 分钟）。
- **它们全部位于台阶之上。**
  - 充电之后的静置位于 CV 末端以下 0–21.9 Ah。
  - 放电之后的静置全部位于 10.2 Ah，即 20 A 脉冲刚结束处。
  - 石墨台阶位于 CV 末端以下 26–33 Ah。
- **没有合格的月份。** 15–45 Ah 窗口内的 28 个静置点，没有一个落在台阶另一侧（比 exp + 3 Ah 更深）。每月每个温度在窗口内最多 3 个点，所以没有月份合格（要求：45 °C 下至少 5 个月、每月 ≥ 8 个跨越台阶的点）。

## 含义

模拟的储能工况只在满充附近静置，所以运行中拿不到关于石墨台阶的去极化信息；能看到台阶的只有锚点充电和约 10 A 的程序放电。
