<a id="en"></a>

# Risk addendum for the submission report (draft, round 7)

> **Language:** English · [中文](#zh)

*For the user to paste into the REPORT's risk section; the package itself was not edited. Numbers refer to the submitted model SUB (V2 + √t gap branch) unless stated.*

**Post-checkup step offset.**
- The first deep discharge after each from-empty anchor charge finds the graphite step 0.2–0.65 Ah deeper than later programs (0.71 Ah after CK0 at 45 °C).
- We tested whether this is lithium released from the anode overhang during the near-empty rest after the checkup (Lewerenz et al., J. Power Sources 345 (2017) 254, [doi](https://doi.org/10.1016/j.jpowsour.2017.01.133); J. Energy Storage 18 (2018) 149, [doi](https://doi.org/10.1016/j.est.2018.04.029)). The offset does not grow with the rest duration or with the start state (Spearman ρ −0.18 and −0.29 over 7 anchors), so the data do not support it.
- The LFP memory effect is excluded: it appears mainly on charge and is erased by one full charge (Sasaki et al., Nat. Mater. 12 (2013) 569, [doi](https://doi.org/10.1038/nmat3623)), and every deep program starts with a full charge.
- Homogenisation of the lithium distribution would sharpen the step (Lewerenz et al., J. Power Sources 368 (2017) 57, [doi](https://doi.org/10.1016/j.jpowsour.2017.09.059)), which is not observed.
- We treat the offset as a reproducible charge-path effect. The model compares only phase-matched month-end steps, so the offset cancels. The pack enters every checkup charged (13.1–13.3 V), so the hidden C/20 is most likely measured without a preceding near-empty rest.

**Anchor-to-checkup offset ε.**
- If all of the pack's roughly 1 Ah/month fade were side reactions, one 5 h full charge would consume only about 0.007 Ah of parasitic charge (Li-inventory model of Smith et al., J. Electrochem. Soc. 158 (2011) A1136, [doi](https://doi.org/10.1149/1.3625232)). So ε (0.3–1.1 Ah) is a protocol effect (rate, CV termination, temperature, start state), not a Coulomb-efficiency effect.
- The start state alone can change a measured capacity by 0.8 % (Lewerenz 2017).
- Field data show the same pattern: LFP home-storage capacity tests sit systematically below operational estimates because of the test rate (Figgener et al., Nat. Energy 9 (2024) 1438, [doi](https://doi.org/10.1038/s41560-024-01620-9)).

**ε drift.**
- Independent capacity minus full-charge Ah drifts by −0.035 (LIC 280 Ah) and −0.031 (Gotion 53 Ah) Ah per Ah of fade, and by −0.057 on the Yagci 180 Ah cells at 50 °C (Yagci et al., J. Energy Storage 124 (2025) 116774, [doi](https://doi.org/10.1016/j.est.2025.116774); data [doi](https://doi.org/10.5281/zenodo.22010995)).
- The Yagci 35 °C cells give +0.18, driven by the first checkup.
- If the drift is real, late estimates read up to about 0.25–0.3 pp high by CK7. Because the sign is not robust across datasets, we report it as a risk and do not correct for it.

**CK2 (missing segment 3).**
- CK2 is extrapolated from the anchors with a √t calendar law. That is the usual form for LFP calendar ageing (Naumann et al., J. Energy Storage 17 (2018) 153, [doi](https://doi.org/10.1016/j.est.2018.01.019); Schimpe et al., J. Electrochem. Soc. 165 (2018) A181, [doi](https://doi.org/10.1149/2.1181714jes)), but some LFP cells fade closer to linearly at 40–45 °C (Kassem et al., J. Power Sources 208 (2012) 296; Lewerenz 2017).
- On the TUM Sony LFP storage data (Mendeley kxh42bfgtj), √t over-predicts the day-25 → day-56 loss by a median of 13 % under comparable early fade.
- Weighting time by temperature (Arrhenius "virtual time", Naumann 2018; Ea 20.6 kJ/mol) is supported by causal hold-out tests and moves CK2 from 94.45 % to 94.51 % SOH. Ea 37.3 kJ/mol gives 94.54 %.
- The main assumption is that the missing segment 3 ran at 45 °C (public schedule). At 25 °C, CK2 would be 94.84 %.

**β (step-to-capacity ratio).**
- On the TUM storage data, capacity loss per Ah of graphite-step → top shortening is 1.1–1.3 (40–60 °C).
- The model's β reaches 1.41–1.51 at CK6–CK7, above this range. Capping β at 1.2 would raise CK6/CK7 by +0.09/+0.14 pp, which is opposite in direction to the ε-drift risk.

---

<a id="zh"></a>

# 提交报告的风险补充（草稿，第七轮）

> **语言：** [English](#en) · 中文

*供用户粘贴到 REPORT 的风险一节；提交包本身没有改动。除特别说明外，数字都针对提交的模型 SUB（V2 + √t 缺口分支）。*

**检查后的台阶偏移。**
- 每次从空态满充（锚点）之后的第一次深放电，台阶比之后的程序深 0.2–0.65 Ah（CK0 之后在 45 °C 下为 0.71 Ah）。
- 我们检验了它是否来自检查后近空停放期间负极 overhang 释放的锂（Lewerenz 等 2017、2018）。偏移并不随停放时长或起点状态增大（7 个锚点上 Spearman ρ 分别为 −0.18 和 −0.29），数据不支持这一解释。
- LFP 记忆效应可以排除：它主要出现在充电方向，一次满充即清除（Sasaki 等 2013），而每个深放电程序都从满充开始。
- 锂分布的均匀化会让台阶变尖（Lewerenz 等 2017 DVA），实际没有观测到。
- 我们把这一偏移视为可重复的充电路径效应。模型只比较同相位的月末台阶，偏移相互抵消。电池组每次进入检查时都是充电状态（13.1–13.3 V），所以隐藏的 C/20 很可能是在没有近空停放的情况下测得的。

**锚点与检查之间的偏置 ε。**
- 即使本电池组约每月 1 Ah 的衰减全部来自副反应，一次 5 h 的满充也只消耗约 0.007 Ah 的副反应电荷（Smith 等 2011 的锂库存模型）。所以 ε（0.3–1.1 Ah）是协议效应（倍率、CV 截止、温度、起点状态），不是库仑效率效应。
- 仅起点状态不同就能让测得的容量相差 0.8 %（Lewerenz 2017）。
- 现场数据也呈现同样的规律：LFP 家储系统的容量测试结果因测试倍率而系统性地低于运行估计（Figgener 等 2024）。

**ε 漂移。**
- 独立容量减满充 Ah 的漂移：LIC 280 Ah −0.035、Gotion 53 Ah −0.031、Yagci 180 Ah 电芯 50 °C −0.057 Ah/Ah（Yagci 等 2025）。
- Yagci 35 °C 电芯为 +0.18，由第一次检查主导。
- 如果漂移真实存在，到 CK7 时后期估计最多偏高约 0.25–0.3 pp。由于不同数据集之间符号不稳健，我们把它作为风险报告，不做修正。

**CK2（缺失段 3）。**
- CK2 由锚点按 √t 日历律外推。这是 LFP 日历老化的常用形式（Naumann 2018；Schimpe 2018），但也有 LFP 电芯在 40–45 °C 下接近线性衰减（Kassem 2012；Lewerenz 2017）。
- 在 TUM Sony LFP 存储数据（Mendeley kxh42bfgtj）上，早期衰减可比的条件下，√t 把第 25 → 56 天的损失高估了中位 13 %。
- 按温度加权时间（Arrhenius “虚拟时间”，Naumann 2018；Ea 20.6 kJ/mol）得到因果留出检验的支持，把 CK2 从 94.45 % 调整到 94.51 % SOH；Ea 取 37.3 kJ/mol 时为 94.54 %。
- 主要假设是缺失的段 3 在 45 °C 下运行（公开时间表）；若为 25 °C，CK2 将是 94.84 %。

**β（台阶与容量之比）。**
- 在 TUM 存储数据上，石墨台阶 → 满充端距离每缩短 1 Ah，容量损失 1.1–1.3 Ah（40–60 °C）。
- 模型在 CK6–CK7 的 β 达到 1.41–1.51，高于这一范围。把 β 上限设为 1.2 会让 CK6/CK7 上调 +0.09/+0.14 pp，方向与 ε 漂移风险相反。
