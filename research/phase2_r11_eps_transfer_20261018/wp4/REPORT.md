<a id="en"></a>

# WP4 — Our pack's own driver series (no 100.41, no proxies)

> English · [中文](#zh)

- **Protocol:** `wp1/protocol.json` (`d183743`), pointer in `928654d`.
- **Script:** `src/wp4_pack.py`.
- **Outputs:** [pack_drivers.csv](pack_drivers.csv), [pack_driver_trends.json](pack_driver_trends.json), [pack_vs_lic_drivers.png](pack_vs_lic_drivers.png).
- The trends use the 25 °C anchors 1–7 (Spearman ρ vs anchor index). Anchor 0 (seg1, 45 °C, 0.5 h rest, unrelaxed) is reported but not used in any trend. Anchor 3 (seg6) has an unrelaxed start (+53 mV/h) and is flagged.

## Conclusions first

1. **Neither registered factor condition holds, so the T_path transfer factor stays in [0, 1].**

| Driver | LIC ρ vs k | LIC ρ vs T_path | Pack ρ (anchors 1–7) | Pack range | Same behaviour? |
|---|---|---|---|---|---|
| CV Ah | +0.83 | −0.84 | **+0.93** | 1.17 → 1.44 Ah | **yes** |
| End current | −0.80 | +0.77 | +0.04 | 5.094–5.100 A | **no** (our cutoff is exact) |
| Relaxed top voltage (LIC 0.25 h, pack 30 min) | +0.82 | −0.61 | −0.65 | 13.439 → 13.435 V | **no** (opposite sign, −4 mV) |
| Start voltage | −0.10 | +0.31 | +0.79 | 11.805 → 11.921 V | pack-only trend |
| Charge temperature / ΔT | −0.48 | +0.60 | −0.49 | 26.6–26.9 °C | flat |
| Rest before | 0 (const.) | — | 0 (const. 2.0 h) | — | — |

   - **Factor 1 fails:** end current and relaxed voltage do not follow LIC.
   - **Factor 0 fails:** CV Ah, a strong T_path driver in LIC, trends strongly in our pack too.
2. **Physical reading. This is descriptive and not part of the rule.**
   - In LIC, the aged 1C charge reaches a *fuller* top: a lower end current and a higher relaxed voltage. That is what makes T_path negative.
   - In our pack, the anchor charge ends at the same 5.10 A every time and relaxes to the same top voltage, 4 mV lower if anything. The growing CV Ah is the fixed cutoff absorbing a growing resistance: the CV phase gets longer and τ goes from 179 to 217 s, but the top state is unchanged.
   - So the top-state part of LIC's T_path probably does **not** carry over. The CV-Ah correlation does. The registered rule cannot decide between these, which is why f is not pinned.
3. **Pack-specific signals that LIC cannot represent:**
   - The start voltage rises by 0.12 V over anchors 1–7.
   - The cell spread at the start grows from 22 to 35 mV, while the spread at the top shrinks from 88 to 52 mV.
   - Both concern the **bottom** (empty) end and **cell imbalance** under pack-voltage limits. They go into the round-12 hand-off as unassessed terms.
4. **Check:** Q_fc is 100.164, 97.045, 95.707, 94.685, 93.790, 93.124, 92.678, 91.996 Ah, consistently 0.04–0.05 Ah above earlier rounds. That is the forward-rectangle convention at the step-start duplicate row. Trends are unaffected. The CV fit of anchor 0 fails because its CV phase lasts only 36 s.

---

<a id="zh"></a>

# WP4 — 本电池组自身的驱动量序列（不用 100.41，不用代理标签）

> [English](#en) · 中文

- 趋势只用 25 °C 的锚点 1–7（对锚点序号算 Spearman ρ）。锚点 0（seg1：45 °C、静置 0.5 h、未弛豫）只报告，不进入任何趋势。锚点 3（seg6）起点未弛豫（+53 mV/h），已标记。

## 结论先读

1. **两个登记的系数条件都不成立，所以 T_path 的迁移系数保持在 [0, 1]。**
   - **CV Ah：** 趋势与 LIC 相同（本题 ρ = +0.93，从 1.17 Ah 到 1.44 Ah；LIC 为 +0.83）。
   - **结束电流：** 本题平坦（5.094–5.100 A，截止很准）；LIC 在下降（ρ = −0.80）。
   - **弛豫后的顶部电压：** 本题略降 4 mV（ρ = −0.65）；LIC 在上升（+0.82），方向相反。
   - **起点电压：** 本题在上升（ρ = +0.79，11.805 → 11.921 V）；LIC 没有趋势。
   - **系数 1 不成立：** 结束电流和弛豫电压与 LIC 不同。**系数 0 也不成立：** CV Ah 在 LIC 中是 T_path 的强驱动量，在本题中也有强趋势。
2. **物理解读（描述性，不属于登记规则）。**
   - LIC 老化后的 1C 充电到达一个*更满*的顶部：结束电流更低、弛豫电压更高，这正是 T_path 变负的原因。
   - 本题的锚点充电每次都在 5.10 A 结束，弛豫到同样的顶部电压（若有变化也是低 4 mV）。CV Ah 增长是固定截止电流吸收了电阻增长的结果：CV 段变长，τ 从 179 s 增到 217 s，但顶部状态没有变。
   - 所以 LIC 的 T_path 中顶部状态那部分很可能**不能**迁移过来，而 CV Ah 的相关性可以。登记规则无法在这两者之间做判断，所以 f 没有被固定。
3. **LIC 无法代表的电池组特有信号：**
   - 锚点 1–7 的起点电压上升了 0.12 V。
   - 起点处的电芯离散度从 22 mV 增到 35 mV，而顶部的离散度从 88 mV 降到 52 mV。
   - 两者都与**底部**（放空端）以及电池组电压限制下的**电芯不一致**有关，作为未评估项写入第 12 轮的交接文件。
4. **核对：** Q_fc 为 100.164、97.045、95.707、94.685、93.790、93.124、92.678、91.996 Ah，比之前各轮一致地高 0.04–0.05 Ah，原因是在工步起点重复行上用了前向矩形法。趋势不受影响。锚点 0 的 CV 段只有 36 s，CV 拟合失败。
