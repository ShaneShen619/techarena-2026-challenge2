<a id="en"></a>

# Round 14 WP0 — Fact sheet

> **Language:** English · [中文](#zh)

Numbers from `wp0/anchor_blocks.csv` and `wp0/facts.json` (scripts `src/wp0_blocks.py`, `src/wp0_facts.py`, full operating data, package rules from `my_model/model_template.py` at `6525edf`). **No Ah balance between CV ends was computed in WP0**; the two facts that are Ah balances are marked "deferred to WP2".

## Conclusions

| # | Fact (§2 of the prompt) | Verdict | Numbers |
|---|---|---|---|
| F1 | After a from-empty anchor the top rest voltage is 7–8 mV lower than after the next top-up | **verified, per cell** | 25 °C anchors 1–7: cell-mean ΔV = V30(T1) − V30(A) = **+7.0 … +8.5 mV**; pack **+28 … +33 mV**. Anchor 0 (45 °C) has the opposite sign: −16 mV cell mean, −62 mV pack |
| F1b | … and the next top-up needs ≈ +0.1 Ah | **deferred to WP2** (Ah balance) | not computed in WP0 |
| F2 | The first deep program after the anchor sits +0.39–0.46 Ah deeper on all 6 detection variants; gone by the next program | **verified in sign and on all variants; size depends on trend adjustment** | raw o = D1 − D2 (A3) = **+0.40 … +0.70 Ah**, median +0.52 (k = 1..7); per-variant medians +0.44 … +0.63. The normal program-to-program change is +0.12 Ah (45 °C median, no anchor) and D2 − D3 = +0.13, +0.25 Ah (anchors 5, 6), so the trend-adjusted offset is ≈ +0.3 … +0.4 Ah. D2 − D3 is back at the normal rate, so the offset is gone by the next program |
| F3 | Anchors run at 25 °C except anchor 0 (segment 1, 45 °C) | **verified** | set points 45, 25×7; CV-end mean cell temperature 46.9 °C (anchor 0), 26.9–27.2 °C (anchors 1–7) |
| F4 | The per-block Ah balance between consecutive CV ends does not close (−0.3 to −1.1 Ah per block) | **deferred to WP2** (Ah balance) | not computed in WP0 |
| F5 | The counters book the 20 A pulse as charge | **verified** | 41 pulses: ∫current_A = −10.20 Ah (median), Δcharge_Ah_cum = **+10.14 … +10.20 Ah**, Δdischarge_Ah_cum = 0 |
| F6 | The pack enters each checkup at 13.1–13.3 V (top-up-type path) | **verified for 5 of 6 visible checkups** | last sample before CK1, CK3, CK4, CK6, CK7: 13.19, 13.22, 13.20, 13.27, 13.26 V; CK5: 13.44 V, but under +7.5 A charge (loaded); CK2 not visible (segment 3 missing). Our top-ups start at 13.358–13.363 V |
| F7 | Anchor 3 (segment 6) has an unrelaxed start | **verified** | pack voltage still rising **+59 mV/h** in the last hour before the charge (anchors 1, 2, 4–7: +2 … +6 mV/h); anchor 0: +85 mV/h after 0.5 h rest |

## Structure that matters for registration (WP1)

- **Top-ups per anchor (same segment).** Anchors 1, 2, 3, 4 and 7 have **one** top-up after the anchor; anchors 5 and 6 have **two**; anchor 0 has four (45 °C).
  - So a second top-up (T2, signal P1b) exists only for anchors 5 and 6 in the 25 °C trend.
  - Top-up → top-up (TT) pairs at 25 °C exist only in segments 10 and 12 (one each). 45 °C segments 1, 5, 7, 9, 11, 13 have three TT pairs each.
- **Recording gaps (dt > 60 s) between the anchor's CV end and T1.**
  - Anchor 3 (segment 6): 2 gaps, 13 127 s and 59 909 s (73 036 s in total), on 2025-04-18/19.
  - Anchor 7 (segment 14): 1 gap of 1 753 s on 2025-09-04.
  - No other A → T1 or T1 → T2 interval has a gap. No 45 °C segment has a gap.
  - The counters are flat across all three gaps (Δcharge_Ah_cum = 0.008, 0.051, 0.006 Ah; Δdischarge_Ah_cum = 0; the 0.051 Ah is the first 10 s sample after the gap at 18.4 A), so the cycler was paused (`facts.json` F9).
- **CV phase (descriptive).** Anchor CV Ah rises from 1.29 Ah (anchor 1) to 1.51 Ah (anchor 7), CV duration from 468 to 560 s. T1 CV Ah stays at 0.71–0.80 Ah and 269–286 s. Every CV end current is 5.092–5.100 A.
- **Top rest voltages (V30).** The anchor's V30 drifts from 13.439 to 13.432–13.435 V; T1's from 13.472 to 13.462–13.466 V.

## Definitions used in WP0

- **Indexing:** events are located by row index, not timestamp: the data has 181 rows with dt = 0 (duplicate timestamps), which the package integration already gives zero weight.

- **CV end:** the package rule in `_step_depths`: last sample of each run with pack ≥ 13.95 V and 0 < I < 6 A.
- **Anchor:** the package's `_first_full_charge` of each segment; Q_fc = its `q` (package `_integrated_ah`).
- **T1, T2:** the next one and two CV ends in the same segment.
- **CV Ah / CV s:** integral of the package's `_integrated_ah` increments over (t_c0, t_e], with c0 the first sample of that charge with pack ≥ 13.95 V.
- **V30:** pack and cell voltages at the last rest sample at or before t_e + 1800 s. The 20 A pulse starts at t_e + 1800–1801 s, so this is the pre-pulse rest sample. It must lie within 30 s of t_e + 1800 s (all 19 events: 1791–1800 s), with no recording gap.
- **o_k:** the package's A3 robust step value (and each of its 6 variants as a median over cells) of the anchor's own deep program minus that of T1's program.

---

<a id="zh"></a>

# 第 14 轮 WP0 — 事实清单

> [English](#en) · 中文

数字来自 `wp0/anchor_blocks.csv` 和 `wp0/facts.json`（脚本 `src/wp0_blocks.py`、`src/wp0_facts.py`，使用完整运行数据，以及 `6525edf` 上 `my_model/model_template.py` 的包内规则）。**WP0 中没有计算任何 CV 结束之间的电量对账**；两条属于电量对账的事实标为"推迟到 WP2"。

## 结论

| # | 事实（prompt 第 2 节） | 判定 | 数字 |
|---|---|---|---|
| F1 | 从空充满的锚点之后，顶部静置电压比下一次补电之后低 7–8 mV | **已核实（按单体）** | 25 °C 锚点 1–7：单体平均 ΔV = V30(T1) − V30(A) = **+7.0 … +8.5 mV**；电池组 **+28 … +33 mV**。锚点 0（45 °C）符号相反：单体平均 −16 mV，电池组 −62 mV |
| F1b | ……下一次补电要多充约 +0.1 Ah | **推迟到 WP2**（电量对账） | WP0 不计算 |
| F2 | 锚点之后第一个深放电程序的台阶深 +0.39–0.46 Ah，6 种检测变体都如此，到下一个程序就消失 | **符号和"所有变体都如此"已核实；大小取决于趋势扣除** | 原始 o = D1 − D2（A3）= **+0.40 … +0.70 Ah**，中位数 +0.52（k = 1..7）；各变体中位数 +0.44 … +0.63。正常的程序间变化为 +0.12 Ah（45 °C、无锚点段的中位数），锚点 5、6 的 D2 − D3 = +0.13、+0.25 Ah，因此扣除趋势后的偏移约 +0.3 … +0.4 Ah。D2 − D3 回到正常速率，所以偏移到下一个程序就消失了 |
| F3 | 除锚点 0（第 1 段，45 °C）外，锚点都在 25 °C | **已核实** | 设定温度 45、25×7；CV 结束时单体平均温度 46.9 °C（锚点 0），26.9–27.2 °C（锚点 1–7） |
| F4 | 相邻 CV 结束之间的逐块电量对账不闭合（每块 −0.3 到 −1.1 Ah） | **推迟到 WP2**（电量对账） | WP0 不计算 |
| F5 | 计数器把 20 A 脉冲记作充电 | **已核实** | 41 个脉冲：∫current_A = −10.20 Ah（中位数），Δcharge_Ah_cum = **+10.14 … +10.20 Ah**，Δdischarge_Ah_cum = 0 |
| F6 | 电池组进入每次检查时为 13.1–13.3 V（补电型路径） | **6 次可见检查中 5 次核实** | CK1、CK3、CK4、CK6、CK7 前最后一个样本：13.19、13.22、13.20、13.27、13.26 V；CK5：13.44 V，但处于 +7.5 A 充电中（带载）；CK2 不可见（缺第 3 段）。我们的补电起点为 13.358–13.363 V |
| F7 | 锚点 3（第 6 段）起点未静置好 | **已核实** | 充电前最后一小时电池组电压仍以 **+59 mV/h** 上升（锚点 1、2、4–7：+2 … +6 mV/h）；锚点 0 只静置 0.5 h，+85 mV/h |

## 对登记（WP1）有影响的结构

- **每个锚点之后的补电（同一段内）。** 锚点 1、2、3、4、7 之后只有**一次**补电；锚点 5、6 有**两次**；锚点 0 有四次（45 °C）。
  - 因此在 25 °C 趋势中，第二次补电（T2，信号 P1b）只在锚点 5、6 存在。
  - 25 °C 的补电 → 补电（TT）配对只在第 10、12 段各有一个。45 °C 的第 1、5、7、9、11、13 段各有三个 TT 配对。
- **锚点 CV 结束与 T1 之间的记录间隙（dt > 60 s）。**
  - 锚点 3（第 6 段）：2 个间隙，13 127 s 和 59 909 s（共 73 036 s），在 2025-04-18/19。
  - 锚点 7（第 14 段）：1 个间隙，1 753 s，在 2025-09-04。
  - 其他 A → T1 或 T1 → T2 区间都没有间隙。45 °C 段都没有间隙。
  - 三个间隙上计数器都几乎不变（Δcharge_Ah_cum = 0.008、0.051、0.006 Ah；Δdischarge_Ah_cum = 0；0.051 Ah 就是间隙后第一个 10 s 样本在 18.4 A 下的电量），说明循环仪暂停了（`facts.json` F9）。
- **CV 阶段（描述）。** 锚点的 CV 电量从 1.29 Ah（锚点 1）升到 1.51 Ah（锚点 7），CV 时长从 468 s 升到 560 s。T1 的 CV 电量保持在 0.71–0.80 Ah、269–286 s。所有 CV 末电流都在 5.092–5.100 A。
- **顶部静置电压（V30）。** 锚点的 V30 从 13.439 V 漂到 13.432–13.435 V；T1 的从 13.472 V 漂到 13.462–13.466 V。

## WP0 使用的定义

- **索引：** 事件按行号定位，而不是按时间戳：数据中有 181 行 dt = 0（时间戳重复），包内积分本来就给它们零权重。

- **CV 结束：** 包内 `_step_depths` 的规则：电池组 ≥ 13.95 V 且 0 < I < 6 A 的每一段连续样本的最后一个。
- **锚点：** 包内每段的 `_first_full_charge`；Q_fc = 它的 `q`（包内 `_integrated_ah`）。
- **T1、T2：** 同一段内接下来的第一、第二个 CV 结束。
- **CV 电量 / CV 时长：** 在 (t_c0, t_e] 上对包内 `_integrated_ah` 增量求和，c0 为该次充电中第一个电池组 ≥ 13.95 V 的样本。
- **V30：** t_e + 1800 s 及之前最后一个静置样本的电池组和单体电压。20 A 脉冲在 t_e + 1800–1801 s 开始，所以这是脉冲前的静置样本。它必须在 t_e + 1800 s 之前 30 s 以内（全部 19 个事件都在 1791–1800 s），且其间没有记录间隙。
- **o_k：** 包内 A3 稳健台阶值（以及它的 6 个变体各自对单体取中位数）在锚点自身深放电程序上的值，减去 T1 程序上的值。
