<a id="en"></a>

# Stage B — Charge-direction step measurements

> **Language:** English · [中文](#zh)

**Result: exit condition met. The charge-direction channel stays diagnostic only; no variant was built or evaluated.**

- **Audit** (`audit_coverage.py`, `coverage.csv`): 41 charges end in pack-level CV, all at a dominant CC current of 20.4 A.
- **Only the 8 post-checkup anchor charges** start deep enough (≥ 45 Ah below the CV end) to cross the graphite step.
- **The ~5-day CCCV charges** all start 20.7–21.4 Ah below the CV end, which is above the step (26–33 Ah below full). They never cross it.
- **45 °C months** with ≥ 2 charge-side step events: 0 of 7. The registered exit rule (`protocol.json`) therefore applies.
- **Consequence.** The charge direction adds no in-month step measurements. The only charge-side step information is in the anchors, which A4 already uses and stage A analyses further. Stage C receives no charge-side observations.

---

<a id="zh"></a>

# 阶段 B——充电方向台阶测量

> **语言：** [English](#en) · 中文

**结果：触发退出条件。充电方向通道只作诊断用，没有构建或评估任何变体。**

- **审计**（`audit_coverage.py`、`coverage.csv`）：有 41 次充电以组端 CV 结束，主导 CC 电流都是 20.4 A。
- **只有 8 次检查后的锚点充电**起点足够深（CV 末端以下 ≥ 45 Ah），能越过石墨台阶。
- **约每 5 天一次的 CCCV 充电**起点都在 CV 末端以下 20.7–21.4 Ah，位于台阶（满充以下 26–33 Ah）之上，从不越过台阶。
- **45 °C 月份**中有 ≥ 2 次充电方向台阶事件的：7 个月里 0 个，因此适用登记的退出规则（`protocol.json`）。
- **后果。** 充电方向不能增加月内台阶测量。充电方向的台阶信息只存在于锚点充电中：A4 已在使用，阶段 A 会进一步分析。阶段 C 没有充电侧观测可用。
