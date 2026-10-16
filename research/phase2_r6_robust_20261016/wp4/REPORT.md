<a id="en"></a>

# WP4 — Open-data prior for the stress model

> **Language:** English · [中文](#zh)

- **Protocol:** [protocol.json](protocol.json), committed `b3108bd` before any download or fit.
- **Runs:**
  - Fallback run (Yagci not yet obtained): pseudo/cold-start committed in `a85f8af` before real; outputs in [outputs/fallback_no_yagci/](outputs/fallback_no_yagci/).
  - Yagci supplement (same protocol): table, prior3 fit and pseudo/cold-start committed in `52e4b25` before the real run.
- **State:** done. The supplement was completed after the 3 h cap ([cap record](CAP_RECORD.md)). No registered rule was changed.
- **Code:**
  - [axes_cycling.py](axes_cycling.py), [build_yagci_table.py](build_yagci_table.py), [fit_prior3.py](fit_prior3.py), [run_wp4.py](run_wp4.py);
  - diagnostics: [check_yagci_calendar.py](check_yagci_calendar.py), [explore_yagci_unruled.py](explore_yagci_unruled.py) (exploratory).

## Conclusions first

1. **No candidate. SUB stays.** With the Yagci data, prior3 differs from prior2 only in A_cal. S_A3, F2_S_A3 and F1_S_A3 fail the gates against SUB: G-proxy, G-epsfree, G-robust and G-hyp. S_A3 and F2_S_A3 also fail G-regress ([gates](outputs/wp4_gates.json), [summary](outputs/wp4_summary_table.csv)).
2. **The open data agree that prior2 is too pessimistic, and this is not exposed (no pack data used).**
   - Over each dataset's own history, prior2 over-predicts the measured loss:

     | Dataset | Prior2 over-prediction |
     |---|---|
     | LIC 280 Ah cycling | +50 % |
     | Gotion 53 Ah cycling | +24 % |
     | Yagci 180 Ah storage cells | 1.5–2.6× (mean +5.7 Ah on a 102 Ah scale) |

   - Most of the excess is the break-in term. At the first checkup (about 85 days), the Yagci storage cells lost 2.7 Ah (35 °C) and 4.8 Ah (50 °C). Prior2 predicts 6.9 Ah and 9.5 Ah.
3. **The open data cannot identify the break-in term, so the registered rule keeps prior2's break-in.**
   - The Yagci storage fit sends τ_b to its upper bound (3000 effective days): the early loss is almost linear, not a fast transient.
   - A_b's cell-jackknife SD is 1.23, above ln 3.
   - A_b and τ_b therefore fall back to prior2.
   - Only A_cal is identified: 0.194 Ah/d^0.5, 18 % below prior2's 0.237.
   - On the cycling data, calendar + break-in alone already exceeds the measured loss for LIC, Gotion and the two 35 °C Yagci cells, so the A_cyc estimate sits at its floor. A_cyc falls back to prior2; that rule is now written into [fit_prior3.py](fit_prior3.py).
4. **The prior is not what drives the CK1 cold-start error (exploratory check).**
   - Rerunning S_A with the unruled Yagci break-in (A_b 6.0 Ah, τ_b 3000 d) moves CK1 only from −0.56 to −0.52 pp. That is a prior whose early loss is less than half of prior2's.
   - The same run makes pseudo worse: 0.154 vs 0.119, and SUB is 0.148.
   - The CK1 error is set by the pack's own data under the gap-endpoint step likelihood, not by the prior centre. A better open-data prior cannot fix it. It is a candidate only in the WP3 sense (path effect / labels).

## Yagci 2025 table

[build_yagci_table.py](build_yagci_table.py) → [wp4_yagci_table.csv](outputs/wp4_yagci_table.csv). It covers 12 cells of 180 Ah LFP: 8 storage cells (35/50 °C × 75/100 % SOC, 2 per group) and 4 cycling cells (35/50 °C).

| Item | Choice |
|---|---|
| Capacity | `max_CCCV_DIS` from "Capacities in checkups – all cells.xlsx", checkups #0, #100, #500 and #1000 |
| Excluded | sheet #1500, which is a byte-for-byte copy of #1000 (asserted in the script) |
| Day 0 | the Checkup_0 IR test date (file name): the end of the initial checkup |
| Later days | "Start of Test" in each cell's standard capacity-check file header (not the 18 A variant); last checkup at 511–551 days |
| Throughput | cycle count × 2 × nominal capacity, scaled to 102 Ah (D4.5) |
| Loss | 102 × (1 − C/C₀) |

## Fit and fallback

| Term | Yagci fit | Jackknife SD (n = 8) | Rule | prior3 |
|---|---|---|---|---|
| log A_b | 1.80 (6.0 Ah) | 1.23 > ln 3 | unidentified → prior2 | 1.857 (6.4 Ah), SD ln 3 |
| log τ_b | 8.01 (3000 d, upper bound) | ~0 | at bound → prior2 | 4.90 (134 d), SD 5.35 |
| log A_cal | −1.64 (0.194) | 0.27 | **identified** | −1.64, SD ln 3 |
| log A_cyc | median at 1e-12 floor (4 of 6 datasets at the floor; Yagci 50 °C cells 5.7e-6 and 3.6e-6) | — | at bound → prior2 | −11.75, SD ln 3 |

The calendar check ([CSV](outputs/wp4_yagci_calendar_check.csv)) gives the mean loss on the storage cells, in Ah on a 102 Ah scale:

| Group | Days | Observed | prior2 | prior3 |
|---|---|---|---|---|
| 35 °C, checkup #100 | 85 | 2.66 | 6.90 | 6.40 |
| 35 °C, checkup #1000 | 536 | 6.12 | 13.39 | 12.14 |
| 50 °C, checkup #100 | 86 | 4.77 | 9.49 | 8.79 |
| 50 °C, checkup #1000 | 535 | 10.81 | 16.21 | 14.45 |

- **Caveat:** checkup #0 is a formation test, a different procedure from the later capacity checks. Part of the 3 % drop to checkup #100 may come from the protocol change rather than ageing. That would make the open-data break-in even smaller and does not change any conclusion.

## Evaluation (as registered)

| Model | Pseudo | Cold start | Real MAE Δ0 / .4 / .8 (pp) | MAX Δ0.4 | CK1 / CK2 (Δ0.4) | Max regret |
|---|---|---|---|---|---|---|
| **SUB** | 0.148 | 0.174 | 0.207 / 0.123 / 0.140 | 0.228 | +0.22 / −0.02 | **0.027** |
| S_A (prior2) | 0.119 | 0.144 | 0.202 / 0.258 / 0.314 | 0.638 | −0.56 / −0.64 | 0.097 |
| S_A3 | 0.119 | 0.144 | 0.207 / 0.263 / 0.319 | 0.669 | −0.56 / −0.67 | 0.100 |
| F2_S_A3 | 0.107 | 0.142 | 0.169 / 0.219 / 0.275 | 0.669 | −0.37 / −0.67 | 0.092 |
| F1_S_A3 (report only) | 0.119 | 0.140 | 0.142 / 0.130 / 0.173 | 0.236 | −0.24 / −0.13 | 0.042 |
| *exploratory: unruled Yagci break-in* | 0.154 | 0.151 | – / 0.211 / – | 0.522 | −0.52 / −0.28 | – |

- The F2 class weights were re-estimated by the WP2 procedure: cold 0.75 (was 1.0), phase 1.0, √t gap 1.0, fallback 0.5.
- The fallback-run numbers are in [outputs/fallback_no_yagci/](outputs/fallback_no_yagci/). The supplement moves S_A3 and F1_S_A3 by at most 0.03 pp. F2_S_A3 changes more (MAE Δ0.4 0.242 → 0.219, MAX Δ0.8 0.953 → 0.761) because its cold-start weight changed.

## Data qualification

| Dataset | Licence | Independent capacity points | Duty | Identifies |
|---|---|---|---|---|
| LIC 280 Ah (TEMPEST), doi 10.5281/zenodo.20813753 | CC BY 4.0 | 15 (0.1C RPT every 50 cycles) | 1C cycling, 1-day rest per block, 25 → 38 °C self-heating | total loss under continuous cycling; calendar and cycle collinear |
| Gotion 53 Ah cell, doi 10.17632/4nww8p6vxf.1 | CC BY 4.0 | 21 (every 50 cycles) | continuous cycling at ~26.7 °C | as above |
| Gotion 53 Ah 10S module | CC BY 4.0 | 21 | as above; capacity first rises 1.1 % | robustness only |
| Yagci 2025, doi 10.5281/zenodo.22939281 | CC BY 4.0 (verified on the record API) | 4 checkups per cell used (#1500 duplicated) | storage at 35/50 °C, 75/100 % SOC, plus full cycling | A_cal (identified); break-in not identified |

The cycling axes ([CSV](outputs/wp4_cycling_axes.csv)) match each LIC capacity point to its reference test by throughput, because one reference test was repeated without cycling in between.

## Attribution (for the report)

- Yagci, M. C., Richter, O., Behmann, R., Bessler, W. G., J. Energy Storage 124, 116774 (2025). Data: doi 10.5281/zenodo.22939281; the readme asks to also cite 10.5281/zenodo.22010995. CC BY 4.0. Used: the checkup capacity summary and test dates for the calendar fit (A_cal) and the calendar check.
- TEMPEST LIC 280 Ah, doi 10.5281/zenodo.20813753, CC BY 4.0. Used: prior check, cycle term and ε drift.
- Gotion 53 Ah, doi 10.17632/4nww8p6vxf.1, CC BY 4.0. Used: prior check, cycle term and ε drift.

---

<a id="zh"></a>

# WP4——为应力模型构建开放数据先验

> **语言：** [English](#en) · 中文

- **协议：** [protocol.json](protocol.json)，在任何下载或拟合之前于 `b3108bd` 提交。
- **运行：**
  - 回退运行（当时还没拿到 Yagci）：伪场景 / 冷启动结果在真实运行之前于 `a85f8af` 提交；输出在 [outputs/fallback_no_yagci/](outputs/fallback_no_yagci/)。
  - Yagci 补充运行（同一份协议）：数据表、prior3 拟合和伪场景 / 冷启动结果在真实运行之前于 `52e4b25` 提交。
- **状态：** 完成。补充运行是在 3 小时上限之后完成的（[上限记录](CAP_RECORD.md)）。没有修改任何登记规则。
- **代码：**
  - [axes_cycling.py](axes_cycling.py)、[build_yagci_table.py](build_yagci_table.py)、[fit_prior3.py](fit_prior3.py)、[run_wp4.py](run_wp4.py)；
  - 诊断：[check_yagci_calendar.py](check_yagci_calendar.py)、[explore_yagci_unruled.py](explore_yagci_unruled.py)（探索性）。

## 结论先读

1. **没有候选，保留 SUB。** 加入 Yagci 数据后，prior3 与 prior2 只在 A_cal 上不同。S_A3、F2_S_A3、F1_S_A3 对 SUB 都没过门槛：G-proxy、G-epsfree、G-robust、G-hyp。S_A3 和 F2_S_A3 还没过 G-regress（[门槛](outputs/wp4_gates.json)、[汇总](outputs/wp4_summary_table.csv)）。
2. **开放数据一致表明 prior2 过于悲观，这一点没有曝光（没有用到电池组数据）。**
   - 按各数据集自己的历史，prior2 高估了实测损失：

     | 数据集 | prior2 高估幅度 |
     |---|---|
     | LIC 280 Ah 循环 | +50 % |
     | Gotion 53 Ah 循环 | +24 % |
     | Yagci 180 Ah 存储电芯 | 1.5–2.6 倍（按 102 Ah 折算平均多 5.7 Ah） |

   - 多出来的部分主要是磨合项。在第一次检查（约 85 天）时，Yagci 存储电芯实际损失 2.7 Ah（35 °C）和 4.8 Ah（50 °C），prior2 却预测 6.9 Ah 和 9.5 Ah。
3. **开放数据辨识不出磨合项，所以按登记规则保留 prior2 的磨合项。**
   - Yagci 存储电芯的拟合把 τ_b 推到上限（3000 等效天）：早期损失几乎是线性的，而不是快速的瞬态。
   - A_b 按电芯 jackknife 的 SD 为 1.23，超过 ln 3。
   - 因此 A_b 和 τ_b 都回退到 prior2。
   - 只有 A_cal 能被辨识：0.194 Ah/d^0.5，比 prior2 的 0.237 低 18 %。
   - 在循环数据上，单是日历项加磨合项就已经超过 LIC、Gotion 以及两颗 35 °C Yagci 电芯的实测损失，所以 A_cyc 的估计停在下限，回退到 prior2。这条规则现在已经写进 [fit_prior3.py](fit_prior3.py)。
4. **先验不是 CK1 冷启动误差的来源（探索性检查）。**
   - 改用不受规则约束的 Yagci 磨合项（A_b 6.0 Ah，τ_b 3000 天）重跑 S_A，CK1 只从 −0.56 变到 −0.52 pp。而这个先验的早期损失还不到 prior2 的一半。
   - 同一次运行让伪场景变差：0.154 对 0.119，SUB 为 0.148。
   - CK1 误差是由电池组自身数据在缺口端点台阶似然下决定的，而不是由先验中心决定的。更好的开放数据先验修不了它。它只在 WP3 的意义上（路径效应 / 标签）才有候选的可能。

## Yagci 2025 数据表

[build_yagci_table.py](build_yagci_table.py) → [wp4_yagci_table.csv](outputs/wp4_yagci_table.csv)。共 12 颗 180 Ah LFP 电芯：8 颗存储电芯（35/50 °C × 75/100 % SOC，每组 2 颗）和 4 颗循环电芯（35/50 °C）。

| 项目 | 取法 |
|---|---|
| 容量 | "Capacities in checkups – all cells.xlsx" 中的 `max_CCCV_DIS`，检查 #0、#100、#500、#1000 |
| 排除 | #1500 表，它与 #1000 逐字节相同（脚本中有断言） |
| 第 0 天 | Checkup_0 内阻测试的日期（取自文件名），即初始检查结束的时间 |
| 之后的天数 | 每颗电芯标准容量检查文件（不是 18 A 版本）文件头中的 "Start of Test"；最后一次检查在第 511–551 天 |
| 吞吐 | 循环数 × 2 × 标称容量，折算到 102 Ah（D4.5） |
| 损失 | 102 × (1 − C/C₀) |

## 拟合与回退

| 项 | Yagci 拟合 | Jackknife SD（n = 8） | 规则 | prior3 |
|---|---|---|---|---|
| log A_b | 1.80（6.0 Ah） | 1.23 > ln 3 | 不可辨识 → prior2 | 1.857（6.4 Ah），SD ln 3 |
| log τ_b | 8.01（3000 天，上限） | 约 0 | 撞到边界 → prior2 | 4.90（134 天），SD 5.35 |
| log A_cal | −1.64（0.194） | 0.27 | **可辨识** | −1.64，SD ln 3 |
| log A_cyc | 中位数在 1e-12 下限（6 个数据集中 4 个在下限；Yagci 50 °C 电芯为 5.7e-6 和 3.6e-6） | — | 撞到边界 → prior2 | −11.75，SD ln 3 |

日历项检查（[CSV](outputs/wp4_yagci_calendar_check.csv)）给出存储电芯上的平均损失，单位为按 102 Ah 折算的 Ah：

| 组 | 天数 | 实测 | prior2 | prior3 |
|---|---|---|---|---|
| 35 °C，检查 #100 | 85 | 2.66 | 6.90 | 6.40 |
| 35 °C，检查 #1000 | 536 | 6.12 | 13.39 | 12.14 |
| 50 °C，检查 #100 | 86 | 4.77 | 9.49 | 8.79 |
| 50 °C，检查 #1000 | 535 | 10.81 | 16.21 | 14.45 |

- **注意：** 检查 #0 是化成测试，和之后的容量检查流程不同。到检查 #100 的 3 % 下降里，可能有一部分来自流程变化而不是老化。如果是这样，开放数据给出的磨合项会更小，任何结论都不受影响。

## 评估（按登记执行）

| 模型 | 伪场景 | 冷启动 | 真实 MAE Δ0 / .4 / .8（pp） | MAX Δ0.4 | CK1 / CK2（Δ0.4） | 最大后悔值 |
|---|---|---|---|---|---|---|
| **SUB** | 0.148 | 0.174 | 0.207 / 0.123 / 0.140 | 0.228 | +0.22 / −0.02 | **0.027** |
| S_A（prior2） | 0.119 | 0.144 | 0.202 / 0.258 / 0.314 | 0.638 | −0.56 / −0.64 | 0.097 |
| S_A3 | 0.119 | 0.144 | 0.207 / 0.263 / 0.319 | 0.669 | −0.56 / −0.67 | 0.100 |
| F2_S_A3 | 0.107 | 0.142 | 0.169 / 0.219 / 0.275 | 0.669 | −0.37 / −0.67 | 0.092 |
| F1_S_A3（只报告） | 0.119 | 0.140 | 0.142 / 0.130 / 0.173 | 0.236 | −0.24 / −0.13 | 0.042 |
| *探索性：不受规则约束的 Yagci 磨合项* | 0.154 | 0.151 | – / 0.211 / – | 0.522 | −0.52 / −0.28 | – |

- F2 的类别权重按 WP2 的流程重新估计：冷启动 0.75（原为 1.0），相位 1.0，√t 缺口 1.0，回退 0.5。
- 回退运行的数字见 [outputs/fallback_no_yagci/](outputs/fallback_no_yagci/)。补充运行使 S_A3 和 F1_S_A3 的变化都不超过 0.03 pp。F2_S_A3 变化更大（MAE Δ0.4 0.242 → 0.219，MAX Δ0.8 0.953 → 0.761），因为它的冷启动权重变了。

## 数据资格

| 数据集 | 许可证 | 独立容量点 | 工况 | 能辨识什么 |
|---|---|---|---|---|
| LIC 280 Ah（TEMPEST），doi 10.5281/zenodo.20813753 | CC BY 4.0 | 15（每 50 循环一次 0.1C RPT） | 1C 循环，每块后静置 1 天，自热从 25 °C 升到 38 °C | 连续循环下的总损失；日历与循环共线 |
| Gotion 53 Ah 单芯，doi 10.17632/4nww8p6vxf.1 | CC BY 4.0 | 21（每 50 循环） | 约 26.7 °C 下连续循环 | 同上 |
| Gotion 53 Ah 10 串模组 | CC BY 4.0 | 21 | 同上；容量先上升 1.1 % | 只用于稳健性 |
| Yagci 2025，doi 10.5281/zenodo.22939281 | CC BY 4.0（已在记录 API 上核实） | 每芯使用 4 次检查（#1500 重复） | 35/50 °C、75/100 % SOC 存储，加上满充满放循环 | A_cal（可辨识）；磨合项不可辨识 |

循环数据的时间轴（[CSV](outputs/wp4_cycling_axes.csv)）按吞吐把每个 LIC 容量点与其参考测试对应起来，因为其中有一次参考测试是在没有循环的情况下重复做的。

## 来源说明（供报告使用）

- Yagci, M. C., Richter, O., Behmann, R., Bessler, W. G., J. Energy Storage 124, 116774 (2025)。数据：doi 10.5281/zenodo.22939281；readme 要求同时引用 10.5281/zenodo.22010995。CC BY 4.0。用途：用检查容量汇总表和测试日期拟合日历项（A_cal）并做日历项检查。
- TEMPEST LIC 280 Ah，doi 10.5281/zenodo.20813753，CC BY 4.0。用途：先验检查、循环项和 ε 漂移。
- Gotion 53 Ah，doi 10.17632/4nww8p6vxf.1，CC BY 4.0。用途：先验检查、循环项和 ε 漂移。
