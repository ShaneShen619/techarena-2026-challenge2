<a id="en"></a>

# WP4 — Daily cycle table (optional)

> **Language:** English · [中文](#zh)

**Result: done, and the main finding is negative.** The usage profile is a current-controlled script that **repeats exactly** in every 116 h program block. Integrated Ah quantities of the daily cycles therefore carry no state information, and only the loaded voltages vary. [../outputs/table_cycles.csv](../outputs/table_cycles.csv) has 430 cycles. Script [run_wp4.py](run_wp4.py); summary [outputs/wp4_summary.json](outputs/wp4_summary.json). Rerun byte-identical. Diagnostic: full data.

**Cycle definition (D4.1).** The profile has no daily rhythm: it is a sequence of SOC swings with a period of 5.5–14 h. So a cycle is one swing, from an SOC top (local maximum of integrated Ah, prominence ≥ 10 Ah) through its lowest point to the next top, inside one segment.
- A complete program block has 12 swings (slots 0..11). Slot 0 contains the deep discharge, and slot 11 ends with the CCCV charge that opens the next program.
- 28 of 39 blocks are complete; blocks cut by segment ends or checkups have fewer swings.

**What varies and what does not.**
- **Ah is fixed by the script.** Ah discharged/charged, swing depth and top-of-charge Ah relative to the last CV end are identical, slot by slot, in every block. The phase-matched residual R_cyc_slot (same slot, ±3 blocks, same set point) has median |R| = 0.001 Ah and 90th percentile 0.009 Ah, apart from slot misalignment in incomplete blocks.
- **The CV is reached** only in the program-opening charge (7.7 % of cycles). No other top touches the 13.95 V limit, so no cycle charge is ever truncated.
- **The registered residual is dominated by phase.** R_cyc (leave-one-out median of the centred 7-cycle window, same set point, as the prompt defines it) mixes different slots. Its median |R| is 20 Ah: profile phase, not state.
- **Loaded voltages carry the state.** V_bottom, V_top and the cell spreads carry the state signal (R_cyc_slot of V_bottom: median |R| 2.5 mV, 90th percentile 22 mV).
- **No 1 h rest follows any top**, so `V_rest_1h_after_top` is always NaN; the profile never rests at a top.

**Consequence for WP5.** H10 as stated (R_cyc of top-of-charge Ah follows the post-anchor and post-switch pattern) cannot be met by construction: the quantity is set by the cycler script. WP5 registers H10 on the phase-matched residual, expecting "not systematic", and adds the loaded bottom voltage as its state-bearing companion (D4.2).

---

<a id="zh"></a>

# WP4——日循环表（可选）

> **语言：** [English](#en) · 中文

**结果：已完成，主要发现是否定性的。** 工况是电流控制的脚本，在每个 116 h 程序周期中**完全重复**。因此日循环的积分 Ah 量不携带状态信息，只有带载电压在变化。[../outputs/table_cycles.csv](../outputs/table_cycles.csv) 共 430 个循环。脚本 [run_wp4.py](run_wp4.py)，摘要 [outputs/wp4_summary.json](outputs/wp4_summary.json)；重跑逐字节相同。属诊断量（全量数据）。

**循环定义（D4.1）。** 工况没有按天的节律，而是一串周期 5.5–14 h 的 SOC 摆动。因此一个循环就是一次摆动：在同一段内，从一个 SOC 顶点（积分 Ah 的局部极大值，显著性 ≥ 10 Ah）经最低点到下一个顶点。
- 一个完整的程序周期有 12 次摆动（槽位 0..11）。槽位 0 包含深放，槽位 11 以开启下一个程序的 CCCV 充电结束。
- 39 个周期中 28 个完整；被段尾或检查截断的周期摆动次数较少。

**哪些在变，哪些不变。**
- **Ah 由脚本固定。** 放电/充电 Ah、摆动深度以及相对上一次 CV 结束的充电顶点 Ah，在每个周期中逐槽位完全相同。相位匹配残差 R_cyc_slot（同槽位、前后各 3 个周期、同设定点）的 |R| 中位数为 0.001 Ah，90 分位数为 0.009 Ah，不完整周期中的槽位错位除外。
- **只有开启程序的充电会到达 CV**（占循环的 7.7 %）。其他顶点都没有触及 13.95 V 限压，所以循环充电从未被截断。
- **登记的残差被相位主导。** R_cyc（同设定点、居中 7 个循环窗口的留一中位数，即 prompt 中的定义）混合了不同槽位，|R| 中位数为 20 Ah：这是工况相位，而不是状态。
- **带载电压承载状态。** V_bottom、V_top 和单体电压差携带状态信号（V_bottom 的 R_cyc_slot：|R| 中位数 2.5 mV，90 分位数 22 mV）。
- **没有任何顶点之后有 1 h 静置**，所以 `V_rest_1h_after_top` 全为 NaN；工况在顶点处从不静置。

**对 WP5 的影响。** 按原表述的 H10（充电顶点 Ah 的 R_cyc 呈现锚点后和切换后的模式）按构造不可能成立，因为该量由充放电脚本决定。WP5 在相位匹配残差上登记 H10，预期为"非系统性"，并加入带载底部电压作为携带状态的配套量（D4.2）。
