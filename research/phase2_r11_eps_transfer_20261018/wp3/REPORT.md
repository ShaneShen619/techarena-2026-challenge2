<a id="en"></a>

# WP3 — Yagci and Gotion: ε decomposition

> English · [中文](#zh)

- **Protocol:** `wp1/protocol.json` (`d183743`), pointer in `928654d`.
- **Scripts:** `src/eps_yagci_r7copy.py` (round 7's script, unchanged) and `src/wp3_ext.py`.
- **Outputs:** [yagci_terms.csv](yagci_terms.csv), [gotion_terms.csv](gotion_terms.csv), [ext_stats.json](ext_stats.json), [ext_terms.png](ext_terms.png).

## Conclusions first

1. **Reproduction passes.** The ε_total group slopes are +0.1776 (35 °C) and −0.0570 (50 °C), identical to round 7 (tolerance 0.005).
2. **Yagci does not resolve the terms.** Signs disagree between cells and between groups, and checkup 0 dominates.

| Group (transfer slope = mean of the two cells' Theil–Sen slopes) | T_CE | T_path | ε_total |
|---|---|---|---|
| Yagci 35 °C, all checkups (main) | +0.099 | +0.035 | +0.147 |
| Yagci 50 °C, all checkups (main) | −0.037 | −0.006 | −0.043 |
| Yagci 35 °C, without checkup 0 | −0.019 | +0.005 | −0.014 |
| Yagci 50 °C, without checkup 0 | −0.008 | +0.028 | +0.020 |

   - **Checkup 0 is a formation test**, a different file type (`*_Formation_*`). Its T_CE ranges from −2.2 to +3.4 Ah (102 Ah scale), against −0.36 … +0.22 Ah at the later checkups.
   - Even without checkup 0, the per-cell T_path slopes range from −0.15 to +0.16 Ah/Ah, so 4 points per cell cannot resolve slopes below about 0.05.
   - In Yagci the operating charge runs at the **same 50 A** as the RPT. T_path there tests temperature (22 vs 35/50 °C) and start state, not rate. **No consistent drift of either term** is visible.
3. **Gotion cell (ε_total only):** Theil–Sen −0.0275, OLS −0.031 (leave-one-out −0.031 … −0.021), BIC (a). This agrees with LIC's total, but it cannot say which term carries the drift. Its calibration has 0.1 Ah resolution.

**Implication for WP5.** Under the registered pooling, the terms are pooled over {LIC, Yagci35, Yagci50}. LIC is the only dataset that resolves the terms cleanly. The Yagci groups widen the leave-one-dataset-out range in both directions.

---

<a id="zh"></a>

# WP3 — Yagci 与国轩：ε 分解

> [English](#en) · 中文

## 结论先读

1. **复现通过。** ε_total 的组斜率为 +0.1776（35 °C）和 −0.0570（50 °C），与第 7 轮一致（容差 0.005）。
2. **Yagci 分辨不出各项。** 各电芯之间、各组之间的符号都不一致，并且第 0 次检查起主导作用。
   - 含全部检查（主估计）：35 °C 组 T_CE +0.099、T_path +0.035；50 °C 组 T_CE −0.037、T_path −0.006。
   - 不含第 0 次检查：35 °C 组 T_CE −0.019、T_path +0.005；50 °C 组 T_CE −0.008、T_path +0.028。
   - **第 0 次检查是化成测试**，文件类型不同（`*_Formation_*`）。它的 T_CE 在 −2.2 到 +3.4 Ah 之间（按 102 Ah 折算），而之后各次检查只有 −0.36 到 +0.22 Ah。
   - 即使不含第 0 次检查，各电芯的 T_path 斜率也在 −0.15 到 +0.16 之间。每只电芯只有 4 个点，分辨不了小于约 0.05 的斜率。
   - Yagci 的运行充电与 RPT 电流**相同（50 A）**，所以这里的 T_path 检验的是温度（22 °C 对 35/50 °C）和起点状态，而不是倍率。两项都**看不到一致的漂移**。
3. **国轩单芯（只有 ε_total）：** Theil–Sen −0.0275，OLS −0.031（逐一剔除范围 −0.031 到 −0.021），BIC 选 (a)。与 LIC 的总量一致，但它说不出漂移由哪一项承载。标定精度只有 0.1 Ah。

**对 WP5 的含义。** 按登记的合并方式，各项在 {LIC, Yagci35, Yagci50} 上合并。只有 LIC 能干净地分辨各项；Yagci 两组让逐一剔除数据集的范围向两个方向都变宽。
