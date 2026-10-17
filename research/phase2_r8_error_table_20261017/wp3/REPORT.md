<a id="en"></a>

# WP3 — Anchor table

> **Language:** English · [中文](#zh)

**Result.** [../outputs/table_anchors.csv](../outputs/table_anchors.csv) has one row per anchor 0..7 (round 7 `anchor_state_table.csv` plus the new columns). Script [run_wp3.py](run_wp3.py), figure [figures/wp3_anchor_overview.png](figures/wp3_anchor_overview.png). Rerun byte-identical. Diagnostic: built from the full data. This page is descriptive; nothing is compared with case errors here.

## Descriptive summary

1. **A common CV cut-off at the largest end current changes nothing.** Every anchor charge already stops at the first 10 s sample at or below 5.10 A (end currents 5.093–5.100 A). With I_cut = 5.10 A, Q_fc(cut) = Q_fc exactly for all 8 anchors (D3.1). The informative column is the **6.0 A cut**:
   - it removes 0.099–0.129 Ah at 25 °C and 0.010 Ah for the 45 °C anchor 0;
   - the removed tail grows from about 0.10 Ah (anchors 1–3) to 0.12–0.13 Ah (anchors 4–7);
   - the month-to-month ΔQ_fc at 25 °C barely changes (SD 0.314 → 0.314 Ah).
2. **The CV charge grows with age.** It rises from 1.35 Ah (anchor 1) to 1.57 Ah (anchors 5–7), with CV time 0.130 → 0.156 h. Anchor 0 at 45 °C has only 0.16 Ah. At 25 °C, CC charge falls 95.65 → 90.38 Ah, faster than Q_fc.
3. **The ΔQ_fc to the next anchor shrinks** from −3.12 (0→1, includes the 45→25 °C change) through −1.33, −1.03, −0.90, −0.67, −0.45 to −0.68 Ah (6→7). This is the sqrt-like decay plus one non-monotone step at 5→6→7.
4. **Start state.** Pack rest voltage before the anchor charge is 11.57–11.95 V. r_upper rises from 0.77 (anchor 0) to 1.5–2.1 Ah, with a dip at anchor 3 (0.995 Ah). The per-cell rest spread grows steadily from 7 mV to 35 mV.
5. **Pulse resistance is flat after anchor 1** (cell mean 1.41–1.48 mΩ).
   - It is quantised: one 1 mV voltage step at about 20.4 A is 0.049 mΩ, so per-cell values move in 0.049 mΩ steps.
   - Anchor 0 (45 °C) is high (1.96 mΩ) because of cell 3 (4.17 mΩ), a single-sample outlier.
   - Relative to anchor 1, cells 2 and 4 rise by 1–2 quanta and cells 1 and 3 do not move. **There is no resolvable resistance trend at the anchors.**
6. **Cells.** The CV-end cell spread falls from 88 mV (anchor 1) to 52 mV (anchor 7).
   - Cell 3 is highest at the CV end, but its lead shrinks: 3.552 → 3.525 V while the other cells rise.
   - The charge-direction step→top distance per cell is on a 0.25 Ah grid. Its spread over cells is 0.75–2.0 Ah, largest at anchors 6–7, and cell 1 has the shortest step→top from anchor 3 on.

Columns (see `DATA_DICTIONARY.md`): the round 7 columns (start, set point, Q_fc, dwell, end state, rest, r_upper/r_half, round 6/7 offsets, step split); `Q_fc_cut_common`, `Q_fc_cut6A` and their differences; `cv_Ah`, `cv_h`, `cc_Ah`; temperature during the charge; per-cell start rest voltages and spread; per-cell step→top and spread; pulse R of the deep program that starts at the anchor CV end (lag 0 h for all 8) and its change from anchor 0; CV-end cell voltages and spread; ΔQ_fc to the next anchor (raw, common cut, 6 A cut); cumulative fade.

---

<a id="zh"></a>

# WP3——锚点表

> **语言：** [English](#en) · 中文

**结果。** [../outputs/table_anchors.csv](../outputs/table_anchors.csv) 每个锚点 0..7 一行（第 7 轮 `anchor_state_table.csv` 加新列）。脚本 [run_wp3.py](run_wp3.py)，图 [figures/wp3_anchor_overview.png](figures/wp3_anchor_overview.png)；重跑逐字节相同。属诊断量（由全量数据构建）。本页只做描述，不与案例误差比较。

## 描述性摘要

1. **用最大终止电流作公共 CV 截止没有任何变化。** 每次锚点充电都已在第一个 ≤ 5.10 A 的 10 s 采样点停止（终止电流 5.093–5.100 A）。取 I_cut = 5.10 A 时，8 个锚点的 Q_fc(截止) 都恰好等于 Q_fc（D3.1）。有信息量的是 **6.0 A 截止**列：
   - 25 °C 时去掉 0.099–0.129 Ah，45 °C 的锚点 0 去掉 0.010 Ah；
   - 去掉的尾段从约 0.10 Ah（锚点 1–3）增大到 0.12–0.13 Ah（锚点 4–7）；
   - 25 °C 下逐月 ΔQ_fc 几乎不变（标准差 0.314 → 0.314 Ah）。
2. **CV 充电量随老化增大。** 从 1.35 Ah（锚点 1）增至 1.57 Ah（锚点 5–7），CV 时间 0.130 → 0.156 h。45 °C 的锚点 0 只有 0.16 Ah。25 °C 下 CC 充电量从 95.65 降到 90.38 Ah，降得比 Q_fc 快。
3. **到下一锚点的 ΔQ_fc 逐渐变小**：−3.12（0→1，含 45→25 °C 的变化）、−1.33、−1.03、−0.90、−0.67、−0.45，到 −0.68 Ah（6→7）。这是类 √t 的衰减，加上 5→6→7 处一次非单调。
4. **起始状态。** 锚点充电前的电池组静置电压为 11.57–11.95 V。r_upper 从 0.77（锚点 0）升到 1.5–2.1 Ah，锚点 3 处有一次低谷（0.995 Ah）。单体间静置电压差从 7 mV 稳步增到 35 mV。
5. **锚点 1 之后脉冲内阻平稳**（单体均值 1.41–1.48 mΩ）。
   - 数值是量化的：约 20.4 A 下 1 mV 电压步长对应 0.049 mΩ，所以单体值以 0.049 mΩ 为步长变化。
   - 锚点 0（45 °C）偏高（1.96 mΩ），来自单体 3 的单点离群值（4.17 mΩ）。
   - 相对锚点 1，单体 2 和 4 升高 1–2 个量化步长，单体 1 和 3 没有变化。**锚点处没有可分辨的内阻趋势。**
6. **单体。** CV 结束时的单体电压差从 88 mV（锚点 1）降到 52 mV（锚点 7）。
   - CV 结束时单体 3 最高，但领先幅度在缩小：从 3.552 降到 3.525 V，而其他单体在升高。
   - 充电方向的台阶→顶部距离按单体计算，位于 0.25 Ah 网格上。单体间差值为 0.75–2.0 Ah，锚点 6–7 最大；从锚点 3 起，单体 1 的台阶→顶部距离最短。

各列说明见 `DATA_DICTIONARY.md`。
