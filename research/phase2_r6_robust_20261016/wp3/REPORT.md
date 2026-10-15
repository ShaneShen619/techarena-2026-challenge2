<a id="en"></a>

# WP3 — Truth-oriented corrections (leaderboard-only)

> **Language:** English · [中文](#zh)

- **Protocol:** [protocol.json](protocol.json), committed `0163e8e`. Amendment 1 (adding a reference-anchor-1 variant for 3a) was made after the audits and before any evaluation, committed `84134fd`.
- **Code:** [audit_wp3.py](audit_wp3.py), [run_wp3.py](run_wp3.py).
- **Scoring:** these corrections are **never scored as proxy improvements**. They are judged on the WP1 hypothesis grid, and their SOH tables are inputs for leaderboard probes. The grid has no start-state axis, so it cannot reward 3a by construction.

## Conclusions first

1. **3b (ε drift) is the most useful correction.**
   - Applied to SUB with d = −0.031 Ah/Ah, it has the best worst-case score (0.194 vs 0.225) and the best expectations under both priors (uniform 0.097 vs 0.113; diagnosis 0.087 vs 0.095) of all candidates on the grid.
   - It wins when drift exists: at Δ 0.4 / f 0 / d −0.031, s = 0.036 vs SUB's 0.065. It loses mildly when drift is absent (0.051 vs 0.035).
   - Its max regret (0.098) is higher than SUB's (0.058 in this enlarged candidate set). It is therefore a hedge, not a dominant choice, and **a natural first leaderboard probe**.
   - The milder d = −0.020 sits in between: worst 0.205, max regret 0.082.
2. **3a (anchor start state) is material in size but low in confidence.**
   - The audit finds the charge left at the start of each anchor (an upper bound from the CK0 C/20 tail at the pre-charge rest voltage) differs by up to 1.29 Ah from anchor 0, and by −0.54 to +0.53 Ah from anchor 1. The exit rule (< 0.1 Ah) does not fire.
   - Applied with anchor 0 as the reference, SUB's late SOH rises by about 1.1 pp. With anchor 1 as the reference (amendment 1: anchor 0 rested only 0.5 h at 45 °C), CK4 falls by 0.4 pp and CK5–CK7 rise by about 0.35 pp.
   - Confidence is low on three counts: r_j is an upper bound from a loaded curve; the rest voltages also depend on relaxation history; and the proxies, which are anchors themselves, cannot test it. A probe would test it, but a wrong guess costs about 1 pp everywhere.
3. **3c (path effect) is confirmed, but correcting it is not supported.**
   - In 6 of 6 step variants, the first deep program after each anchor charge sits 0.41–0.56 Ah deeper (trend-adjusted median; 0.83 Ah for month 0 at 45 °C). This agrees with the rebound diagnosis.
   - Among SUB's inputs, it affects only the fallback branch (CK1, CK3), which compares the first and last program after the anchor. Removing the first program raises SUB's CK1 by 0.75 pp and CK3 by 0.35 pp.
   - That contradicts the proxies under every grid hypothesis: s rises in each of them. Either the month-0 decline is genuine break-in loss, or the 45 °C offset differs from the 25 °C one. 3c stays a diagnostic. In the stress model it acts only on month 0 (S_C, exposed-CK1).
4. **Combined variants are dominated by the 3a shift** and score worst on the grid. They are not recommended.

## Audits ([wp3_audits.json](outputs/wp3_audits.json))

| Anchor | Set point | Rest before (h) | Pack rest V | r_upper (Ah) | r − r_0 | r − r_1 |
|---|---|---|---|---|---|---|
| 0 | 45 | 0.5 | 11.570 | 0.774 | 0 | — |
| 1 | 25 | 2.0 | 11.805 | 1.530 | 0.756 | 0 |
| 2 | 25 | 2.0 | 11.808 | 1.530 | 0.756 | 0.000 |
| 3 | 25 | 2.0 | 11.629 | 0.995 | 0.221 | −0.535 |
| 4 | 25 | 2.0 | 11.883 | 1.780 | 1.006 | 0.250 |
| 5 | 25 | 2.0 | 11.953 | 2.064 | 1.290 | 0.534 |
| 6 | 25 | 2.0 | 11.892 | 1.851 | 1.077 | 0.321 |
| 7 | 25 | 2.0 | 11.922 | 1.986 | 1.212 | 0.456 |

**Path effect, median trend-adjusted offset (Ah):** main 0.557, band_narrow 0.510, windows−3 0.522, windows+3 0.430, dvdq_peak 0.406, ir_corrected 0.483 ([per anchor](outputs/wp3c_path_offsets.csv)).

## Grid results (selection; full: [decision table](outputs/wp3_hypothesis_decision_table.csv), [s by h](outputs/wp3_s_by_h.csv), [regret by h](outputs/wp3_regret_by_h.csv))

| Model | Worst s | Max regret | E uniform | E diagnosis | s at Δ0.4 f0 d0 | s at Δ0.4 f0 d−0.031 |
|---|---|---|---|---|---|---|
| SUB (base) | 0.225 | **0.058** | 0.113 | 0.095 | **0.035** | 0.065 |
| **SUB + 3b (−0.031)** | **0.194** | 0.098 | **0.097** | **0.087** | 0.051 | **0.036** |
| SUB + 3b (−0.020) | 0.205 | 0.082 | 0.102 | 0.089 | 0.041 | 0.045 |
| SUB + 3a_ref1 | 0.248 | 0.080 | 0.140 | 0.122 | 0.068 | 0.096 |
| SUB + 3a (ref 0) | 0.370 | 0.219 | 0.265 | 0.241 | 0.203 | 0.235 |
| SUB + 3c | 0.243 | 0.129 | 0.151 | 0.142 | 0.115 | 0.133 |
| F1_S_A (base) | 0.214 | 0.078 | 0.113 | 0.095 | 0.035 | 0.050 |
| F1_S_A + 3b (−0.031) | 0.181 | 0.119 | 0.099 | 0.089 | 0.062 | 0.034 |
| F2_S_A (base) | 0.208 | 0.131 | 0.132 | 0.119 | 0.085 | — |

Regrets are relative to the best model per hypothesis within this enlarged set, which includes the corrected variants. That is why SUB's max regret is 0.058 here and 0.027 in WP1.

## Leaderboard-only SOH (%) at the submitted configuration ([all variants](outputs/wp3_leaderboard_only_SOH.csv))

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| SUB | 95.992 | 94.451 | 93.541 | 92.811 | 92.081 | 91.331 | 90.821 |
| SUB + 3b (−0.031) | 95.916 | 94.327 | 93.389 | 92.637 | 91.884 | 91.111 | 90.585 |
| SUB + 3b (−0.020) | 95.943 | 94.371 | 93.443 | 92.698 | 91.954 | 91.189 | 90.668 |
| SUB + 3a_ref1 | 95.992 | 94.451 | 93.541 | 92.179 | 92.301 | 91.865 | 91.159 |
| SUB + 3a (ref 0) | 95.992 | 95.560 | 94.282 | 92.920 | 93.042 | 92.606 | 91.901 |
| SUB + 3c | 96.743 | 94.451 | 93.892 | 92.811 | 92.081 | 91.331 | 90.821 |

---

<a id="zh"></a>

# WP3——真值导向修正（只用于排行榜）

> **语言：** [English](#en) · 中文

- **协议：** [protocol.json](protocol.json)，于 `0163e8e` 提交。修订 1（为 3a 增加以锚点 1 为参照的变体）是在审计之后、任何评估之前做的，于 `84134fd` 提交。
- **代码：** [audit_wp3.py](audit_wp3.py)、[run_wp3.py](run_wp3.py)。
- **评分方式：** 这些修正**绝不作为代理上的改进来评分**。它们在 WP1 的假设网格上评判，其 SOH 表作为排行榜探测的输入。网格里没有"起点状态"这条假设轴，所以按构造它无法给 3a 加分。

## 结论先读

1. **3b（ε 漂移）是最有用的修正。**
   - 以 d = −0.031 Ah/Ah 用在 SUB 上时，它在网格上所有候选中最坏情况最好（0.194 对 0.225），两种先验下的期望也都最好（均匀 0.097 对 0.113；诊断 0.087 对 0.095）。
   - 有漂移时它胜出：在 Δ 0.4 / f 0 / d −0.031 下，s = 0.036，SUB 为 0.065。没有漂移时它小幅落后（0.051 对 0.035）。
   - 它的最大后悔值（0.098）高于 SUB（在这个扩大了的候选集中为 0.058）。所以它是一种对冲，而不是占优的选择，**是排行榜探测的天然首选**。
   - 较温和的 d = −0.020 介于两者之间：最坏 0.205，最大后悔值 0.082。
2. **3a（锚点起点状态）量级可观，但置信度低。**
   - 审计发现，每次锚点开始充电时的残余电量（依据充电前静置电压，在 CK0 C/20 曲线尾部读出的上界）与锚点 0 最多相差 1.29 Ah，与锚点 1 相差 −0.54 至 +0.53 Ah。退出规则（< 0.1 Ah）没有触发。
   - 以锚点 0 为参照时，SUB 后期的 SOH 上调约 1.1 pp。以锚点 1 为参照时（修订 1：锚点 0 在 45 °C 下只静置了 0.5 小时），CK4 下调 0.4 pp，CK5–CK7 上调约 0.35 pp。
   - 置信度低的原因有三：r_j 是从带载曲线读出的上界；静置电压还受弛豫历史影响；而代理本身就是锚点，无法检验它。排行榜探测可以检验它，但如果判断错了，每个检查点都会损失约 1 pp。
3. **3c（路径效应）得到证实，但修正它没有依据支持。**
   - 在 6/6 种台阶检测方法下，每次锚点充电后的第一次深放电程序都偏深 0.41–0.56 Ah（扣除趋势后的中位数；第 0 月 45 °C 下为 0.83 Ah）。这与偏移诊断一致。
   - 在 SUB 的输入中，它只影响 fallback 分支（CK1、CK3）：该分支比较锚点后第一次和最后一次程序。去掉第一次程序后，SUB 的 CK1 上调 0.75 pp，CK3 上调 0.35 pp。
   - 这在网格的每一个假设下都与代理相矛盾：每个假设下 s 都变大了。要么第 0 月的下降确实是磨合造成的真实损失，要么 45 °C 下的偏移与 25 °C 下不同。3c 仍作为诊断保留。在应力模型中，它只作用于第 0 月（S_C，已曝光 CK1）。
4. **组合变体主要由 3a 的偏移主导**，在网格上得分最差。不推荐。

## 审计（[wp3_audits.json](outputs/wp3_audits.json)）

| 锚点 | 设定温度 | 充电前静置（h） | 组端静置电压 | r_upper（Ah） | r − r_0 | r − r_1 |
|---|---|---|---|---|---|---|
| 0 | 45 | 0.5 | 11.570 | 0.774 | 0 | — |
| 1 | 25 | 2.0 | 11.805 | 1.530 | 0.756 | 0 |
| 2 | 25 | 2.0 | 11.808 | 1.530 | 0.756 | 0.000 |
| 3 | 25 | 2.0 | 11.629 | 0.995 | 0.221 | −0.535 |
| 4 | 25 | 2.0 | 11.883 | 1.780 | 1.006 | 0.250 |
| 5 | 25 | 2.0 | 11.953 | 2.064 | 1.290 | 0.534 |
| 6 | 25 | 2.0 | 11.892 | 1.851 | 1.077 | 0.321 |
| 7 | 25 | 2.0 | 11.922 | 1.986 | 1.212 | 0.456 |

**路径效应，扣除趋势后偏移的中位数（Ah）：** main 0.557、band_narrow 0.510、windows−3 0.522、windows+3 0.430、dvdq_peak 0.406、ir_corrected 0.483（[逐锚点](outputs/wp3c_path_offsets.csv)）。

## 网格结果（节选；完整见 [决策表](outputs/wp3_hypothesis_decision_table.csv)、[各假设下的 s](outputs/wp3_s_by_h.csv)、[各假设下的后悔值](outputs/wp3_regret_by_h.csv)）

| 模型 | 最坏 s | 最大后悔值 | 期望（均匀） | 期望（诊断） | Δ0.4 f0 d0 下的 s | Δ0.4 f0 d−0.031 下的 s |
|---|---|---|---|---|---|---|
| SUB（原样） | 0.225 | **0.058** | 0.113 | 0.095 | **0.035** | 0.065 |
| **SUB + 3b（−0.031）** | **0.194** | 0.098 | **0.097** | **0.087** | 0.051 | **0.036** |
| SUB + 3b（−0.020） | 0.205 | 0.082 | 0.102 | 0.089 | 0.041 | 0.045 |
| SUB + 3a_ref1 | 0.248 | 0.080 | 0.140 | 0.122 | 0.068 | 0.096 |
| SUB + 3a（参照锚点 0） | 0.370 | 0.219 | 0.265 | 0.241 | 0.203 | 0.235 |
| SUB + 3c | 0.243 | 0.129 | 0.151 | 0.142 | 0.115 | 0.133 |
| F1_S_A（原样） | 0.214 | 0.078 | 0.113 | 0.095 | 0.035 | 0.050 |
| F1_S_A + 3b（−0.031） | 0.181 | 0.119 | 0.099 | 0.089 | 0.062 | 0.034 |
| F2_S_A（原样） | 0.208 | 0.131 | 0.132 | 0.119 | 0.085 | — |

后悔值是相对于这个扩大了的候选集中每个假设下的最佳模型而言的，而修正后的变体也包含在这个集合里。这就是 SUB 的最大后悔值在这里是 0.058、在 WP1 中是 0.027 的原因。

## 只用于排行榜的 SOH（%），按提交配置（[全部变体](outputs/wp3_leaderboard_only_SOH.csv)）

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| SUB | 95.992 | 94.451 | 93.541 | 92.811 | 92.081 | 91.331 | 90.821 |
| SUB + 3b（−0.031） | 95.916 | 94.327 | 93.389 | 92.637 | 91.884 | 91.111 | 90.585 |
| SUB + 3b（−0.020） | 95.943 | 94.371 | 93.443 | 92.698 | 91.954 | 91.189 | 90.668 |
| SUB + 3a_ref1 | 95.992 | 94.451 | 93.541 | 92.179 | 92.301 | 91.865 | 91.159 |
| SUB + 3a（参照锚点 0） | 95.992 | 95.560 | 94.282 | 92.920 | 93.042 | 92.606 | 91.901 |
| SUB + 3c | 96.743 | 94.451 | 93.892 | 92.811 | 92.081 | 91.331 | 90.821 |
