<a id="en"></a>

# WP1 — Protocol audit (no ε values)

> English · [中文](#zh)

## LIC 280 Ah ([lic_sequence.csv](lic_sequence.csv), [lic_rpt_summary.csv](lic_rpt_summary.csv))

**Answers to the registered questions.**

1. **Does each RPT contain a 0.1C CCCV charge as well as the 0.1C discharge?** Yes, in all 15 complete RPTs. The charge is 28 A CC to 3.65 V, then CV to 13.9–14.4 A (0.05C).
2. **In which order?** Every RPT runs the same sequence:
   - last 1C discharge of the block (ends at ≈2.57 V);
   - 1.25 h rest;
   - in some RPTs, a short 0.1C discharge to 2.5 V;
   - 0.1C CC charge for 5.387 h (sets ≈50 % SOC);
   - 24 h rest;
   - ±56/140/280 A 10-s pulses at 50 % SOC;
   - 0.1C discharge to 2.5 V;
   - 0.983 h rest;
   - **0.1C CCCV charge (reference charge)**;
   - 0.25 h rest;
   - **0.1C discharge to 2.5 V (reference capacity)**;
   - 0.25 h rest;
   - **1C CCCV charge (first operating charge)**.
3. **Does the first 1C charge start from the 0.1C-empty state?** Yes, after a 0.25 h rest; start voltage 2.80–2.85 V. The reference charge also starts from a 0.1C-empty state, but after a 0.983 h rest (start voltage 2.67–2.70 V). Both charges end with CV to ≈0.05C, so both reach the same nominal top state. After RPT 14 the file ends with a 0.1C charge, so 14 operating-charge pairs exist (k = 0..13).
4. **Pulse tests:** the 10-s segments at ±56, ±140 and ±280 A between the 50 %-SOC set and the discharge to empty.

**Protocol changes and anomalies found.**

- **RPT temperature changes twice.** It is 24.7 °C for k = 0–1, 29.7 °C for k = 2–4 and 35.1 °C for k = 5–14. The first 1C charge self-heats to 32 / 36 / 40.4 °C respectively.
- **Before RPT 5:** during the rest after the last 1C discharge, the voltage jumps 2.820 → 3.329 V between two samples at I = 0. This is an unrecorded charge. An extra 0.1C discharge from that state then hits the 10 h limit at 280.0 Ah, ending at 2.739 V. This is the "truncated RPT" of the earlier screening. It is not one of the 15 RPTs; it precedes RPT 5.
- **Before RPT 10:** the same kind of unrecorded jump, 2.821 → 3.007 V. A 0.1C discharge of 6.9 Ah follows, before the normal sequence.
- **The registered event** (step between k = 4 and k = 5) therefore combines three things: the extra truncated test, an unrecorded charge, and the 29.7 → 35.1 °C RPT temperature step.

## Yagci 180 Ah ([yagci_ck100_cell19_steps.csv](yagci_ck100_cell19_steps.csv))

- **RPT** (raw file of CA-181103-19, checkup 100):
  - 48 h pause, then a 50 A discharge to 2.5 V with CV to ≈9 A;
  - two cycles of 50 A CC charge to 3.65 V with CV to ≈8.4–8.7 A, a 0.5 h pause, and a 50 A CCCV discharge to 2.5 V with CV to ≈9 A;
  - temperature 21–23 °C.
- **Summary values.** `max_CCCV_CHA` and `max_CCCV_DIS` in the summary file equal the **second** cycle's charge (194.397 + 0.800 Ah) and discharge (195.219 + 0.361 Ah). The charge precedes the discharge, so **T_CE is identifiable**.
- **Operating cycles** (`Analysis individual cycles` file): 50 A CCCV charge and discharge, i.e. the **same current** as the RPT, at 35 or 50 °C. T_path therefore mainly carries temperature (RPT at about 22 °C vs operation at 35/50 °C) and the start state.
- **Differences from our pack.** Here the reference discharge is CCCV, with a CV phase at 2.5 V. Our reference is a C/20 CC discharge.

## Gotion 53 Ah

- The calibration table gives only cycle number and capacity (0.1 Ah resolution); no protocol is stated and no raw calibration steps are in the data.
- **Only ε_total is identifiable. T_CE and T_path are not.** The module is excluded, as in `DATA_MANIFEST.md`.

---

<a id="zh"></a>

# WP1 — 协议审查（不含 ε 值）

> [English](#en) · 中文

## LIC 280 Ah

**对登记问题的回答。**

1. **每次 RPT 除了 0.1C 放电，是否还有 0.1C CCCV 充电？** 是，15 次完整 RPT 都有。充电为 28 A 恒流到 3.65 V，然后恒压到 13.9–14.4 A（0.05C）。
2. **顺序是什么？** 每次 RPT 的流程相同：
   - 循环块的最后一次 1C 放电（约 2.57 V 结束）；
   - 静置 1.25 h；
   - 部分 RPT 有一段短的 0.1C 放电到 2.5 V；
   - 0.1C 恒流充电 5.387 h（设到约 50% SOC）；
   - 静置 24 h；
   - 在 50% SOC 下做 ±56/140/280 A 的 10 s 脉冲；
   - 0.1C 放电到 2.5 V；
   - 静置 0.983 h；
   - **0.1C CCCV 充电（参考充电）**；
   - 静置 0.25 h；
   - **0.1C 放电到 2.5 V（参考容量）**；
   - 静置 0.25 h；
   - **1C CCCV 充电（第一次运行充电）**。
3. **第一次 1C 充电是否从 0.1C 放空状态开始？** 是，静置 0.25 h 后开始，起点电压 2.80–2.85 V。参考充电也从 0.1C 放空状态开始，但静置 0.983 h（起点电压 2.67–2.70 V）。两次充电都以恒压到约 0.05C 结束，名义上到达同一个顶部状态。RPT 14 之后文件以一次 0.1C 充电结束，所以运行充电配对共 14 组（k = 0..13）。
4. **脉冲测试：** 在设定 50% SOC 和放电到空之间的 ±56、±140、±280 A 的 10 s 段。

**发现的协议变化和异常。**

- **RPT 温度变化了两次：** k = 0–1 为 24.7 °C，k = 2–4 为 29.7 °C，k = 5–14 为 35.1 °C。第一次 1C 充电的自热温度分别为 32、36、40.4 °C。
- **RPT 5 之前：** 最后一次 1C 放电后的静置中，电压在电流为 0 的两个采样点之间从 2.820 V 跳到 3.329 V，即一次未记录的充电。随后从这个状态做的一次 0.1C 放电在 280.0 Ah 处触发 10 h 上限，结束于 2.739 V。这就是之前筛选中所说的"被截断的 RPT"。它不属于 15 次 RPT，而是在 RPT 5 之前。
- **RPT 10 之前：** 同类的未记录跳变，2.821 → 3.007 V，之后先做一次 6.9 Ah 的 0.1C 放电，再进入正常流程。
- **登记的事件**（k = 4 与 k = 5 之间的台阶）因此同时包含三件事：额外的截断测试、一次未记录的充电、RPT 温度从 29.7 °C 升到 35.1 °C。

## Yagci 180 Ah

- **RPT**（CA-181103-19 第 100 次检查的原始文件）：
  - 暂停 48 h，然后 50 A 放电到 2.5 V，恒压到约 9 A；
  - 两个循环：50 A 恒流充电到 3.65 V，恒压到约 8.4–8.7 A，暂停 0.5 h，再 50 A CCCV 放电到 2.5 V，恒压到约 9 A；
  - 温度 21–23 °C。
- **汇总值。** 汇总表中的 `max_CCCV_CHA` 和 `max_CCCV_DIS` 分别等于**第二个**循环的充电量（194.397 + 0.800 Ah）和放电量（195.219 + 0.361 Ah）。充电在放电之前，所以 **T_CE 可识别**。
- **运行循环**（`Analysis individual cycles` 文件）：50 A CCCV 充放电，与 RPT **电流相同**，温度 35 或 50 °C。因此 T_path 主要反映温度（RPT 约 22 °C，运行 35/50 °C）和起点状态。
- **与本题的差异。** 这里的参考放电是带 2.5 V 恒压段的 CCCV 放电，而本题参考是 C/20 恒流放电。

## 国轩 53 Ah

- 标定表只有循环号和容量（精度 0.1 Ah），没有说明协议，数据中也没有原始标定工步。
- **只能识别 ε_total，T_CE 和 T_path 不可识别。** 模组按 `DATA_MANIFEST.md` 排除。
