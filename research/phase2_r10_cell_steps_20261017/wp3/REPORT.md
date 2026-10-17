<a id="en"></a>

# WP3 — Idea C: remove the cells' top-state drift

> **Language:** English · [中文](#zh)

**Result: WP3 exits by its registered rule ("top-state mechanism not supported"). Neither covariate explains the per-cell drift, so no WP3b candidate was built.** Protocol [protocol_3a.json](protocol_3a.json) was committed in `b245892` before computing. Script [run_wp3a.py](run_wp3a.py); outputs [outputs/wp3a_result.json](outputs/wp3a_result.json), [outputs/wp3a_table.csv](outputs/wp3a_table.csv). Rerun byte-identical.

| Covariate (within-cell, pooled, 164 cell-programs) | slope | 90 % CI (month blocks) | cells with + sign | within-cell R² | pass |
|---|---|---|---|---|---|
| u: cell voltage minus the cell mean at the program's CV end (mV) | +0.00002 Ah/mV | [−0.0007, +0.0004] | 2 / 4 | 0.00002 | no |
| w: per-cell charge-side step→top at the month's anchor minus the cell mean (Ah) | +0.069 | [−0.042, +0.113] | 2 / 4 | 0.065 | no |

**What the tables show instead** (month means, descriptive):

| month | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| R_cell cell1 (Ah) | −0.18 | −0.28 | −0.25 | −0.38 | −0.34 | −0.48 | −0.43 | −0.51 |
| R_cell cell2 | +0.15 | +0.32 | +0.15 | +0.16 | +0.10 | +0.09 | +0.09 | +0.15 |
| R_cell cell3 | +0.29 | +0.15 | +0.31 | +0.21 | +0.26 | +0.17 | +0.28 | +0.23 |
| R_cell cell4 | −0.19 | −0.21 | −0.15 | −0.15 | −0.10 | −0.08 | −0.09 | −0.15 |
| u cell3 (mV) | +133 | +41 | +65 | +59 | +54 | +43 | +39 | +18 |

- **The divergence is cell 1.** Its step moves towards the top faster than the other cells' (relative depth −0.18 → −0.51 Ah over 8 months). Cells 2–4 keep roughly fixed offsets.
- **Cell 1 is also the weakest cell at maximum depth** (round 8), so the most plausible reading is that cell 1 loses lithium faster than the others. This is a real per-cell ageing difference, not a measurement artefact of the top state.
- **The top state does change, but on its own path.** The top imbalance converges (cell 3's CV-end lead falls 133 → 18 mV), while the step offsets do not follow it.

Consequence: re-referencing to the top state cannot remove the divergence. Which cell's ageing the pack capacity follows is the open question. In a series pack the weakest cell limits the capacity, but round 9's minimum-cell candidate failed every gate. **C1/C2 would have been degenerate in any case:** both corrections are deviations from the cell mean, so they cancel exactly in the 4-cell mean (recorded as D3.1).

---

<a id="zh"></a>

# WP3——想法 C：消除单体顶部状态的漂移

> **语言：** [English](#en) · 中文

**结论：WP3 按登记规则退出（"顶部状态机制不成立"）。两个协变量都解释不了单体漂移，所以没有构建 WP3b 候选。** 协议在计算前已提交（`b245892`）。
- **u（CV 结束时单体电压相对均值）：** 单体内 R² 仅 0.00002，CI 包含 0，只有 2/4 个单体为正号。
- **w（当月锚点充电侧台阶→顶部距离相对均值）：** R² 0.065，CI 包含 0，只有 2/4 个单体为正号。

**表格显示的实际情况：**
- **走散的是单体 1。** 它的相对台阶深度 8 个月里从 −0.18 降到 −0.51 Ah，单体 2–4 的偏移基本固定。
- **单体 1 同时也是最大深度处最弱的单体**（第 8 轮），最合理的解释是单体 1 的锂损失比其他单体快。这是真实的单体老化差异，不是顶部状态造成的测量假象。
- **顶部状态确实在变，但走的是另一条路。** 顶部不平衡在收敛（单体 3 的 CV 结束电压领先从 133 mV 降到 18 mV），台阶偏移并没有跟着变。

因此，按顶部状态重新定基无法消除拉开。真正待解的问题是：电池组容量跟随哪个单体的老化？串联电池组的容量受最弱单体限制，但第 9 轮的最弱单体候选所有检验都没通过。另外，**C1/C2 本来就会退化**：两种修正都是相对单体均值的偏差，在四单体均值里恰好相互抵消（记为 D3.1）。
