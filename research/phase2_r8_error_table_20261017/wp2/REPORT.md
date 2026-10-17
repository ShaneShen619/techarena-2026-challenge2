<a id="en"></a>

# WP2 — Event table

> **Language:** English · [中文](#zh)

**Result.** [../outputs/table_events.csv](../outputs/table_events.csv) has 205 rows: 41 deep programs × {cell1..cell4, pack_mean}, 71 columns. Script [run_wp2.py](run_wp2.py), raw-curve helper [../src/eventcurves.py](../src/eventcurves.py). A rerun is byte-identical. Diagnostic: built from the full operation data.

**Column-level check against `events_merged.csv`** ([outputs/wp2_checks.json](outputs/wp2_checks.json)): **passed**.
- **Events.** The same 41 events in the same order (CV-end timestamps identical).
- **Step depths.** The pack-mean depths of all 6 variants match to ≤ 3.6e-15 Ah (floating-point round-off; dvdq_peak exactly).
- **Carried columns.** segment, set point, charge Ah, CV Ah, CV h, CV-end current, CV-end temperature, rest before the charge and mean pulse R are identical.
- **One expected difference.** The pack start voltage differs from the sum of the four cell rest voltages by ≤ 9 mV, because they are separate channels.

**Residuals.** Defined here and frozen in WP5's protocol before any slicing.
- **R_seg.** depth_main minus a leave-one-out Theil–Sen line in time over the other events of the same segment and unit. It is NaN when fewer than 3 others exist, which applies to every 25 °C segment (2–3 programs each): 16 of the 41 events, 80 rows.
- **R_anc.** depth_main − [a_sp,unit + 1·Q_interp(t)]. Q_interp is the linear interpolation in time of Q_fc between the bracketing anchors (t_end). a is the mean of depth − Q_interp over the same set point and unit, leaving the event's month out. NaN for the one event after anchor 7 (E40).
- **R_cell.** Unit depth minus the median of the four cell depths of the same event.
- **Free-slope fit (descriptive).** On the 40 bracketed pack-mean events, depth = a_sp + b·Q_interp gives **b = 0.745**, with a 90 % block-bootstrap CI over months of [0.674, 0.765] (8 months, 2000 resamples, seed 20261017). The step depth moves about 0.75 Ah per Ah of anchor fade, so R_anc (b = 1) carries a fade-proportional component by construction. 1/b ≈ 1.34 sits within the range of SUB's β (1.06–1.51).

**Other derived columns.**
- **Month and program index.** month = the anchor the event follows; program_index counts programs after that anchor.
- **Switch timing.** days_since_switch runs from the start of the current visible segment. `switch_kind` is campaign_start, direct_switch (25→45 °C, gap of 0.3–1.1 days) or after_checkup_gap (gap > 2 days, chamber temperature not observed; D2.1).
- **Throughput.** Integrated discharge since the anchor and since the campaign start.
- **Recording gaps.** `has_recording_gap` is false for all 41 events.
- **Step depths and shape.** Per-cell depth for all 6 variants (the per-cell `locs`). Sharpness is the dV/dQ peak height in mV/Ah, its FWHM in Ah and its position, on a 0.25 Ah grid with a 2 Ah moving average over 18–46 Ah. Upper and lower plateau medians.
- **Cell state.** Pulse R per cell, cell spread at CV end and at maximum depth, voltage rank at maximum depth (1 = lowest) and the weakest cell.
- **Use flags.** Which SUB real-scenario predictions (Δ = 0.4) used each event as end45_E_cur, end45_E_prev, rate_fit, after_first or after_last; values are checkup names.

Exposure note (D2.2): during table QA, the pack-level R_anc/R_seg per event and the per-unit distribution of R_cell were printed before WP5's registration.

---

<a id="zh"></a>

# WP2——事件表

> **语言：** [English](#en) · 中文

**结果。** [../outputs/table_events.csv](../outputs/table_events.csv) 共 205 行：41 个深放程序 × {cell1..cell4, pack_mean}，71 列。脚本 [run_wp2.py](run_wp2.py)，原始曲线工具 [../src/eventcurves.py](../src/eventcurves.py)；重跑逐字节相同。属诊断量（由全量运行数据构建）。

**与 `events_merged.csv` 的逐列核对**（[outputs/wp2_checks.json](outputs/wp2_checks.json)）：**通过**。
- **事件。** 41 个事件相同、顺序相同（CV 结束时间戳一致）。
- **台阶深度。** 6 个变体的 pack 均值深度相差 ≤ 3.6e-15 Ah（浮点舍入；dvdq_peak 完全相同）。
- **沿用的列。** 段号、设定点、充电 Ah、CV Ah、CV 小时、CV 结束电流、CV 结束温度、充电前静置时间和平均脉冲内阻完全一致。
- **一处预期差异。** pack 起始电压与四个单体静置电压之和相差 ≤ 9 mV，因为它们是独立的测量通道。

**残差。** 在此定义，并在 WP5 协议中、任何切片之前冻结。
- **R_seg。** depth_main 减去同一段、同一单元其他事件按时间做的留一 Theil–Sen 直线。其他事件少于 3 个时为 NaN，所有 25 °C 段（每段 2–3 个程序）都属此情况：41 个事件中 16 个，共 80 行。
- **R_anc。** depth_main − [a_sp,unit + 1·Q_interp(t)]。Q_interp 是相邻两个锚点（按 t_end）之间 Q_fc 随时间的线性插值。a 为同一设定点、同一单元上 depth − Q_interp 的均值，留出该事件所在月份。锚点 7 之后的唯一事件（E40）为 NaN。
- **R_cell。** 单元深度减去同一事件四个单体深度的中位数。
- **自由斜率拟合（描述性）。** 在 40 个被锚点夹住的 pack 均值事件上拟合 depth = a_sp + b·Q_interp，得 **b = 0.745**，按月块 bootstrap 的 90 % CI 为 [0.674, 0.765]（8 个月，2000 次重采样，种子 20261017）。台阶深度约随锚点衰减每 Ah 变化 0.75 Ah，因此 R_anc（b = 1）按构造带有与衰减成比例的分量。1/b ≈ 1.34，落在 SUB 的 β 范围（1.06–1.51）内。

**其他派生列。**
- **月份与程序序号。** month 为事件所跟随的锚点；program_index 为该锚点之后的程序序号。
- **切换时间。** days_since_switch 从当前可见段的起点算起。`switch_kind` 取 campaign_start、direct_switch（25→45 °C，间隔 0.3–1.1 天）或 after_checkup_gap（间隔 > 2 天，箱温未观测；D2.1）。
- **吞吐量。** 锚点以来和试验开始以来积分得到的放电量。
- **记录缺口。** 41 个事件的 `has_recording_gap` 全为假。
- **台阶深度与形状。** 6 个变体的单体深度（即单体 `locs`）。尖锐度为 dV/dQ 峰高（mV/Ah）、半高宽（Ah）及峰位，在 0.25 Ah 网格、2 Ah 滑动平均、18–46 Ah 范围上计算。另有上下平台中位数。
- **单体状态。** 单体脉冲内阻、CV 结束和最大深度处的单体电压差、最大深度处的电压排名（1 = 最低）及最弱单体。
- **使用标志。** 记录 SUB 真实场景预测（Δ = 0.4）以何种方式用到每个事件（end45_E_cur、end45_E_prev、rate_fit、after_first、after_last），取值为检查点名称。

曝光说明（D2.2）：表格质检时，在 WP5 登记之前打印过每个事件的 pack 级 R_anc/R_seg 以及 R_cell 按单元的分布。
