<a id="en"></a>

# WP2 — LIC 280 Ah: ε decomposition

> English · [中文](#zh)

- **Protocol:** rules from `wp1/protocol.json` (`d183743`), pointer in [protocol.json](protocol.json), committed in `928654d`.
- **Script:** `src/wp2_lic.py`.
- **Outputs:** [lic_terms.csv](lic_terms.csv), [lic_stats.json](lic_stats.json), [lic_terms.png](lic_terms.png).

## Conclusions first

1. **The LIC drift is almost entirely T_path. T_CE is flat.**

| Term | Theil–Sen slope (Ah/Ah) | OLS | Leave-one-RPT-out (Theil–Sen) | BIC winner | Transfer slope |
|---|---|---|---|---|---|
| T_CE = Q_ref,dis − Q_ref,ch | **−0.0008** | −0.0023 | −0.0011 … +0.0009 | (a) | −0.0008 |
| T_path = Q_ref,ch − Q_op,ch | **−0.0287** | −0.0347 | −0.0306 … −0.0280 | (a) | −0.0287 |
| ε_total | −0.0297 | −0.0345 | −0.0300 … −0.0280 | (a) | −0.0297 |

   T_path carries **97 %** of the slope, so the **dominant term is T_path**. The total reproduces the screening value −0.035 (OLS); every reference discharge matches `lic_eps.csv` exactly.

2. **Step or drift? Not distinguishable; the registered rule keeps the drift.**
   - For T_path, the step model (b) has a BIC 1.2 lower than (a). For ε_total, the difference is 0.05. Both are below the registered margin of 2, so (a) is kept.
   - Without the flagged points (k = 0, 1 from the MAD rule; k = 5, 10 from the audit), the T_path slope is −0.031 and (a) still wins. ε_total switches to (c), with slope −0.034 and step −0.25 Ah.
   - Within the two temperature regimes, T_path still falls: −0.046 (k = 2–4, three points) and −0.027 (k = 5–13).
   - **The drift is therefore not just an artefact of the k = 5 event.**
   - The two largest single values both follow unrecorded charges: k = 5 (T_path −0.88 Ah) and k = 10 (−0.47 Ah).

3. **What carries T_path in LIC is the top of the 1C charge, not its start.** The 1C charge moves capacity from CC to CV as the cell ages: T_path_CC slope +0.13, T_path_CV −0.16. The table lists the drivers (Spearman ρ, k = 0..13):

| Driver (first 1C operating charge) | ρ vs k | ρ vs T_path |
|---|---|---|
| CV duration | +0.82 | **−0.96** |
| CV Ah | +0.83 | **−0.84** |
| median cell temperature | +0.98 | −0.80 |
| end current (CV cutoff reached at) | −0.80 | +0.77 |
| voltage after the 0.25 h rest | +0.82 | −0.61 |
| Tm(op) − Tm(ref) | −0.48 | +0.60 |
| start voltage | −0.10 | +0.31 |

   - **Reading.** As resistance grows, the 1C charge spends longer in CV, ends at a slightly lower current (14.8 → 13.4 A, with 10-s sampling) and relaxes to a higher top voltage. So it fills the cell further than the 0.1C reference charge does, and T_path goes negative.
   - The start voltage has no trend. In LIC, T_path is a **top-state** mechanism.
   - The temperature confound is real. The RPT chamber temperature steps 24.7 → 29.7 → 35.1 °C, and the 1C charge self-heats to 32 → 40 °C. It cannot be separated from k with these data.

4. **What this implies for our pack, ahead of WP5.** Our anchor charge also ends with CV at 0.05C, but at 0.2C instead of 1C. The candidate drivers are our CV Ah, CV duration, end current and relaxed top voltage (WP4). The start voltage is not one of them in LIC.

## Data-handling note

Charge Ah uses the backward-rectangle rule with the global sample spacing (1 s in the 0.1C steps, 10 s in the 1C steps). This is the same rule as the screening and `lic_seg.py`; each record closes its interval. A first version dropped the first interval of each charge (−0.78 Ah at 1C) and was corrected before this report. Slopes were unaffected, because the dropped amount was a constant offset.

---

<a id="zh"></a>

# WP2 — LIC 280 Ah：ε 分解

> [English](#en) · 中文

## 结论先读

1. **LIC 的漂移几乎全部来自 T_path，T_CE 是平的。**
   - T_CE 的 Theil–Sen 斜率为 −0.0008（逐一剔除范围 −0.0011 到 +0.0009）。
   - T_path 为 −0.0287（−0.0306 到 −0.0280）。
   - ε_total 为 −0.0297，OLS 为 −0.0345，复现了筛选值 −0.035。
   - T_path 占斜率的 **97%**，**主导项是 T_path**。
2. **台阶还是漂移？分不开，按登记规则保留漂移。**
   - T_path 的台阶模型 (b) 比 (a) 的 BIC 低 1.2，ε_total 只低 0.05，都没有超过登记的 2，所以保留 (a)。
   - 剔除被标记的点后，T_path 斜率为 −0.031，(a) 仍然胜出；ε_total 变为 (c)，斜率 −0.034，台阶 −0.25 Ah。
   - 在两个温度区间内部 T_path 仍在下降：−0.046（k = 2–4，3 个点）和 −0.027（k = 5–13）。
   - **所以漂移不只是 k = 5 事件造成的假象。**
   - 两个最大的单点都出现在未记录充电之后：k = 5（T_path −0.88 Ah）和 k = 10（−0.47 Ah）。
3. **LIC 里承载 T_path 的是 1C 充电的顶部，而不是起点。**
   - 随着老化，1C 充电把容量从 CC 段挪到 CV 段：T_path_CC 斜率 +0.13，T_path_CV −0.16。
   - CV 时长（与 T_path 的 ρ = −0.96）、CV Ah（−0.84）、结束电流（+0.77）和弛豫后的顶部电压（−0.61）都与 T_path 强相关；起点电压没有趋势。
   - **解读：** 电阻增大后，1C 充电在 CV 段停留更久，以略低的电流结束（14.8 → 13.4 A，10 s 采样），弛豫后的顶部电压更高。也就是说它比 0.1C 参考充电充得更满，T_path 因而变负。
   - 温度混杂确实存在：RPT 箱温从 24.7 °C 升到 29.7 °C 再到 35.1 °C，1C 充电自热从 32 °C 升到 40 °C。用这些数据无法把它与 k 分开。
4. **对本题的含义（WP5 之前）。** 我们的锚点充电也以恒压到 0.05C 结束，但倍率是 0.2C 而不是 1C。候选驱动量是我们的 CV Ah、CV 时长、结束电流和弛豫后的顶部电压（WP4）；在 LIC 中起点电压不是驱动量。

## 数据处理说明

充电 Ah 用后向矩形法，采样间隔取全局采样间隔（0.1C 工步为 1 s，1C 工步为 10 s）。这与筛选和 `lic_seg.py` 的规则相同：每条记录结束它所代表的区间。最初一版漏掉了每次充电的第一个区间（1C 时为 −0.78 Ah），在本报告之前已改正。斜率不受影响，因为漏掉的量是一个常数偏移。
