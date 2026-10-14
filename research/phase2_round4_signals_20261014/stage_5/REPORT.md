<a id="en"></a>

# Stage 5 — Physics of the post-checkup recovery

> **Language:** English · [中文](#zh)

Exposed-exploratory and descriptive: nothing was tuned, and no model was changed. Code: `run_5.py`. Outputs: `outputs/jumps.csv`, `tau_profile.csv`, `ranking_sensitivity.csv`, `summary.json`.

## Conclusions first

1. **The recovery grows over the campaign.**
   - Method: step jump across each checkup, plus the 25/45 °C offset (δ = 0.18 Ah), plus ageing during the gap (−0.025 Ah/day).
   - Size: about 0.02 Ah at CK1, 0.25–0.34 Ah at CK2–CK3, 0.71–0.87 Ah at CK4–CK7.
2. **It decays fast once operation resumes.** The pooled transient fit (months 2–6, 32 steps) gives τ ≈ 2.5 days (95 % profile 0.5–9.8 days) and amplitude ≈ 0.43 Ah.
3. **Mechanism.** A capacity that grows with cycling, comes back after a rest, and is consumed again within days of cycling matches *cycling-induced lithium/salt inhomogeneity and rehomogenisation during rest* better than anode overhang alone. Overhang equalisation runs over weeks to months; τ = 2.5 d only overlaps the shortest overhang-driven time scales reported for LFP.
4. **This is the largest open risk for the real score.**
   - The proxies are post-recovery charges. If the hidden C/20 reflects a pre-recovery or partly recovered state, every anchor-based model is biased high by up to about 0.9 pp late in the campaign.
   - Under that hypothesis **V1/M4 ranks above V2** (table below).
   - Only the leaderboard can tell which hypothesis holds.

## 1. Recovery per checkup (Ah of step depth)

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| raw jump (last pre → first post step) | −0.38 | −0.40 | −0.04 | +0.34 | +0.43 | +0.45 | +0.54 |
| + δ (45 → 25 °C) | −0.20 | −0.40 | +0.14 | +0.52 | +0.61 | +0.63 | +0.72 |
| + ageing during the gap | +0.02 | +0.25 | +0.34 | +0.71 | +0.83 | +0.80 | +0.87 |

CK2's gap spans the missing segment (26 days), so its values are least reliable.

## 2. Literature comparison

- **Anode overhang.**
  - [Lewerenz et al. 2018](https://www.sciencedirect.com/science/article/abs/pii/S2352152X18301191): equalisation between overhang and active anode is slow, from days to hundreds of days, and complete only after about 150 days at 50 °C.
  - [The 0D overhang model](https://www.sciencedirect.com/science/article/abs/pii/S2352152X19316731): only part of the overhang participates on short time scales. A reported LFP float study puts the overhang-dominated phase at about 5–30 days.
  - τ ≈ 2.5 d is therefore at or below the fastest overhang time scale.
- **Cycling-induced inhomogeneity, recovered by rest.**
  - [Morales Torricos, Endisch, Lewerenz (Batteries 2023)](https://doaj.org/article/802288dae0454a32aa5a9e1a94dafd50): removing rest periods produces an apparent capacity loss that is recovered during a later rest.
  - Their 2025 follow-up (Batteries & Supercaps, doi 10.1002/batt.202500559, as cited in their announcement): up to 81 % of apparent loss is recoverable, attributed to electrolyte-motion-induced salt inhomogeneity; higher temperature promotes rehomogenisation.
  - [WEVJ 16(5) 2025](https://doi.org/10.3390/wevj16050255): the recovered capacity grows with cycling.
  - For LFP/graphite, [JES 10.1149/1945-7111/ab7900](https://iopscience.iop.org/article/10.1149/1945-7111/ab7900) attributes up to about 20 % of lost capacity to recoverable non-uniform lithium distribution.
  - These match the observed growth, the recovery during the checkup, and the fast re-formation during cycling.

## 3. Which state does the hidden C/20 measure?

**Timing.** The last operating step is 1–4 days before each checkup date, and the first post-checkup step 3–6 days after it. The checkup sits between them. It takes at least a full charge, a 20-hour C/20 discharge, and presumably moving and resting the pack.

**Two hypotheses.**

- **H_post (the proxy hypothesis).** The pack rests long enough before or during the checkup (several τ) that the C/20 measures the rehomogenised state. The post-checkup anchor sees the same state. V2's design (anchor to anchor) is then right.
- **H_pre / partial.** The C/20 starts within about a day of the end of operation, so only 1 − exp(−t/τ) of the recovery has happened. With τ ≈ 2.5 d and t ≈ 1–2 d, that is about 33–55 %. The rest happens later, mainly while the pack sits near empty after the C/20. The truth would then be lower than the proxy by 0.45–0.67 of the recovery.

**Ranking sensitivity** (descriptive). Proxies are shifted down by a fraction f of the recovery:

| f (unrecovered share) | M4 (V1) MAE / MAX | V2 MAE / MAX |
|---|---|---|
| 0 (H_post) | 0.291 / 0.669 | **0.216** / 0.669 |
| 0.5 | **0.333** / 0.789 | 0.434 / 0.789 |
| 1.0 | **0.596** / 0.972 | 0.700 / 0.961 |

**Reading.**

- V2 wins only if the checkup measures a fully recovered state. Under partial recovery, V1 is better, and both models are biased high late in the campaign.
- The checkup procedure (rest time, temperature, and the order of full charge and C/20) decides this, and it is not in the released material.
- **Practical implication.**
  - Before switching the submission from V1 to V2, a leaderboard comparison of V1 and V2 is itself informative: V2 scoring better supports H_post, while V1 scoring better supports partial recovery.
  - Do not assume H_post silently.

---

<a id="zh"></a>

# 阶段 5——检查后回弹的物理

> **语言：** [English](#en) · 中文

已曝光的探索性研究，仅作描述：没有调任何参数，也没有改动任何模型。代码：`run_5.py`。输出：`outputs/jumps.csv`、`tau_profile.csv`、`ranking_sensitivity.csv`、`summary.json`。

## 结论先读

1. **回弹在整个试验期间不断变大。**
   - 算法：每次检查前后的台阶跳变，加上 25/45 °C 偏移（δ = 0.18 Ah），再加上缺口期间的老化（−0.025 Ah/天）。
   - 大小：CK1 约 0.02 Ah，CK2–CK3 为 0.25–0.34 Ah，CK4–CK7 为 0.71–0.87 Ah。
2. **恢复运行后衰减很快。** 合并的瞬态拟合（第 2–6 月，32 次台阶）给出 τ ≈ 2.5 天（95 % 剖面区间 0.5–9.8 天），幅度约 0.43 Ah。
3. **机理。** "随循环增长、静置后恢复、循环几天内又被消耗"的容量，与*循环引起的锂/盐分布不均及静置时的再均匀化*更吻合，单靠负极 overhang 解释不了。overhang 的平衡过程以数周到数月计；τ = 2.5 天只与文献中 LFP 最短的 overhang 时间尺度有重叠。
4. **这是真实分数最大的未决风险。**
   - 代理是回弹之后的充电量。如果隐藏的 C/20 反映的是回弹前或部分回弹的状态，所有基于锚点的模型在试验后期都会系统偏高，最多约 0.9 pp。
   - 在这一假设下，**V1/M4 排在 V2 之前**（见下表）。
   - 只有排行榜能判断哪个假设成立。

## 1. 每次检查的回弹（台阶深度 Ah）

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| 原始跳变（检查前最后一次 → 检查后第一次台阶） | −0.38 | −0.40 | −0.04 | +0.34 | +0.43 | +0.45 | +0.54 |
| + δ（45 → 25 °C） | −0.20 | −0.40 | +0.14 | +0.52 | +0.61 | +0.63 | +0.72 |
| + 缺口期间的老化 | +0.02 | +0.25 | +0.34 | +0.71 | +0.83 | +0.80 | +0.87 |

CK2 的缺口跨越了缺失的那一段（26 天），所以它的数值最不可靠。

## 2. 与文献对照

- **负极 overhang。**
  - [Lewerenz 等 2018](https://www.sciencedirect.com/science/article/abs/pii/S2352152X18301191)：overhang 与有效负极之间的平衡很慢，从数天到数百天，在 50 °C 下约 150 天后才完全平衡。
  - [0D overhang 模型](https://www.sciencedirect.com/science/article/abs/pii/S2352152X19316731)：短时间尺度上只有部分 overhang 参与。有报道的一项 LFP 浮充研究把 overhang 主导阶段定在约 5–30 天。
  - 因此 τ ≈ 2.5 天处于 overhang 最快时间尺度的下限，甚至更短。
- **循环引起的不均匀、静置后恢复。**
  - [Morales Torricos、Endisch、Lewerenz（Batteries 2023）](https://doaj.org/article/802288dae0454a32aa5a9e1a94dafd50)：去掉静置段会造成表观容量损失，之后静置时可以恢复。
  - 他们 2025 年的后续研究（Batteries & Supercaps，doi 10.1002/batt.202500559，据其发布信息）：表观损失最多 81 % 可恢复，原因是电解液流动引起的盐分布不均；温度越高，再均匀化越快。
  - [WEVJ 16(5) 2025](https://doi.org/10.3390/wevj16050255)：可恢复的容量随循环增长。
  - 对 LFP/石墨，[JES 10.1149/1945-7111/ab7900](https://iopscience.iop.org/article/10.1149/1945-7111/ab7900) 把最多约 20 % 的容量损失归因于可恢复的锂分布不均。
  - 这些与观测到的增长、检查期间的恢复以及循环中的快速再形成都吻合。

## 3. 隐藏的 C/20 测的是哪个状态？

**时间线。** 最后一次运行中的台阶测量在检查日前 1–4 天，检查后的第一次在检查日后 3–6 天，检查位于两者之间。检查至少包括一次满充、一次 20 小时的 C/20 放电，大概还有搬运和静置。

**两种假设。**

- **H_post（代理假设）。** 检查前或检查中静置足够久（数倍 τ），C/20 测到的是再均匀化后的状态，检查后的锚点看到的也是同一状态。这时 V2 的设计（锚点对锚点）是对的。
- **H_pre / 部分恢复。** C/20 在运行结束后约一天内就开始，恢复只完成了 1 − exp(−t/τ)。取 τ ≈ 2.5 天、t ≈ 1–2 天，约为 33–55 %。其余恢复发生在之后，主要是 C/20 结束、电池组停在近空状态的时候。这时真值会比代理低回弹量的 0.45–0.67。

**排名敏感性**（描述性）。把代理下调回弹量的一个比例 f：

| f（未恢复部分） | M4（V1）MAE / MAX | V2 MAE / MAX |
|---|---|---|
| 0（H_post） | 0.291 / 0.669 | **0.216** / 0.669 |
| 0.5 | **0.333** / 0.789 | 0.434 / 0.789 |
| 1.0 | **0.596** / 0.972 | 0.700 / 0.961 |

**解读。**

- 只有检查测的是完全恢复的状态时，V2 才更好；部分恢复时 V1 更好，而且两者在试验后期都偏高。
- 决定这一点的是检查流程（静置时间、温度、满充与 C/20 的顺序），而这些不在已发布的材料里。
- **实际含义。**
  - 在把提交从 V1 换成 V2 之前，V1 与 V2 在排行榜上的对比本身就有信息量：V2 得分更好支持 H_post；V1 得分更好则支持部分恢复。
  - 不要默认 H_post 成立。
