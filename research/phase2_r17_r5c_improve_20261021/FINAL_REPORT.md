<a id="en"></a>

# Round 17: Physics Improvements to the r5c Stress Model — Final Report

> **Language:** English · [中文](#zh)

- **Run:** 2026-10-21, unattended, following [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md).
- **Where:** worktree `/Users/shane/Desktop/Arena_1021_r17_r5c`, branch `exp/phase2-r17-r5c-improve-20261021`, from r5c `348af0b`.
- **Selection:** causal cases only (pseudo PG1/PG2/PC5/PC10 + cold start CS/CSE, 28 cases). The real scenario ran once, after every selection was committed. All proxies are exposed.
- **Untouched:** every submission file and package, every earlier study. No zip, no upload.

## Conclusions first

1. **No design improves r5c. The submission is unchanged.**
   - Four of the six literature-based changes are **inert**: their prediction changes are below the step-variant noise floor (T_move = 0.110 pp). These are the switch fix B0, the SOC-weighted calendar clock S, the calendar Ea on k (C), and dropping the cycle term (D).
   - The two that move predictions, τ_b model averaging (O1) and the reversible overhang state (O2), make R3_T slightly *worse* on the causal cases. Mean paired change +0.008 / +0.007 pp; each helps month 3 and hurts months 4–5.
   - **FINAL = REF** (0.75·R3_T + 0.25·V2, r5c as it was). It is not causally better than SUB: mean paired difference −0.018 pp, smaller than δ = 0.028 pp, with two of five month blocks worse.
2. **Why the 10-21 effects do not survive:**
   - **The operating SOC is the same every month.** The monthly mean SOC is 0.57–0.63, with SD 0.008 at 25 °C. Any SOC weight on operation time is therefore absorbed by A_cal. Checkups and switches are only 7 % of the Arrhenius clock.
   - **The calendar Arrhenius convention barely matters.** Changing it for the calendar term alone moves real CK2 by 0.013 pp.
   - **The large 10-21 movements came from the break-in timescale τ_b.** It is **not identified**: the top Laplace weight is ≥ 0.8 in 0 of 28 causal cases. Shortening the break-in (O1, O2) shifts loss from later months into earlier ones. That fixes the real CK2 (−0.64 → −0.35/−0.40 pp) but worsens the causal month-4/5 blocks.
   - **The 10-21 pseudo/cold gains from switching off checkup ageing** (0.004–0.012 pp) were below this round's noise threshold δ = 0.028 pp.
3. **The real proxies would have chosen O2/O1, for the wrong reason.** O2_ens and O1_ens score MAE 0.103 / 0.108 pp on the real proxies, against REF 0.131 and SUB 0.120. The gain is entirely CK2; without CK2 they are 0.105 vs REF 0.102. Labelled **exposed-CK2**; not recommended.
4. **New facts:**
   - F1: the real chamber switches total only 3.1 days. A day-resolution bug would have mislabelled three real checkups as switches (D0.3).
   - F4: **Yagci's 37.3 kJ/mol is an Ea on k**, from an Arrhenius plot of end-of-test losses at equal time. r5c applies it to time, so r5c's clock is 18.65 kJ/mol on k. That is close to Schimpe's 20.6 by coincidence.
   - WP1: Naumann 2018's k_SOC cubic deviates from its own TUM data by up to 40 %. Lewerenz 2018's compensation time at 50 °C is 100 d, not 150 d.
5. **Scope.** Nothing here addresses the 0.7–1.0 pp level suggested by the leaderboard. Every r5c-family model sits 0.06–0.19 pp **below** SUB (CK1–7 mean). That is far from both readings (truth ~1 pp below SUB, or CK2–7 ~+0.65 pp above), so none of them would serve as a level probe either.

## One table

pp; Δ = 0.4. p = |err_X| − |err_R3_T| and q = |err_X_ens| − |err_REF| over causal cases. Real columns are exposed. The level column is the ensemble's mean SOH shift against SUB over CK1–7.

| Design | Moves? S_causal / S_real | Causal pass | mean p / q | max LOKO (p) | Real MAE alone / ens | Real CK2 ens | Label | Level vs SUB (ens) |
|---|---|---|---|---|---|---|---|---|
| B0 switch fix | no, 0.008 / 0.009 | inert | — | — | 0.181 / 0.133 | −0.311 | | −0.125 |
| S SOC-weighted calendar (k_SOC², TUM) | no, 0.022 / 0.022 | inert | — | — | 0.181 / 0.133 | −0.297 | | −0.118 |
| C calendar Ea on k (41.2 on time) | no, 0.007 / 0.013 | inert | — | — | 0.178 / 0.129 | −0.302 | exposed-CK2 | −0.121 |
| O1 τ_b Laplace averaging | yes, 0.115 / 0.242 | **fail** (1, 2, 3, 5, 6) | +0.008 / +0.020 | +0.023 | 0.155 / 0.108 | −0.130 | exposed-CK2; τ_b unidentified | −0.080 |
| O2 overhang state | yes, 0.147 / 0.288 | **fail** (1, 2, 3, 5, 6) | +0.007 / +0.001 | +0.017 | 0.158 / 0.103 | −0.096 | exposed-CK2 | −0.104 |
| D no cycle term | no, 0.034 / 0.035 | non-inferior (accepted, not applied) | — | — | 0.176 / 0.129 | −0.285 | exposed-CK2 | −0.109 |
| M_comb | — | none (nothing passed) | | | | | | |
| E2 regime weights | — | not run (4 `phase` cases < 6) | | | | | | |
| **FINAL = REF** | — | vs SUB: mean r −0.018, criteria 1 and 2 fail | | −0.006 | — / 0.131 | −0.311 | all r5c gates pass | −0.124 |

## Expectations against outcomes

| Written before running | Outcome |
|---|---|
| C changes predictions little | **Confirmed.** S_causal 0.007, real CK2 +0.013 pp |
| S moves only through switch/checkup/gap rows, much less than the 10-21 test | **Confirmed, and more strongly: inert** (0.022). Even true checkups at 0 % SOC move only 0.024 |
| O2 behaves like a break-in with τ ≈ 50–75 d (WP1 gives 48.6 d at 45 °C); CK2 between the 10-21 τ_b = 60 and 134 d rows, which had worse pseudo scores | **Confirmed.** Ensemble CK2 −0.096 lies between +0.08 and −0.31. Alone, pseudo is worse than R3_T (0.123 vs 0.119); in the ensemble, pseudo improves (0.115 vs REF 0.123) but cold start worsens (0.151 vs 0.134). Net q ≈ 0 |
| D likely inert | **Confirmed** (0.034) |
| "No design beats REF causally" is likely | **Confirmed** |

## What the 10-21 analysis got right and wrong

- **Right:**
  - The r5c CK2 is a cancellation (R3_T −0.638 vs V2 +0.669).
  - CK2 depends on an unidentifiable break-in time constant. The Laplace evidence confirms τ_b is not identified.
  - The cycle term does little: 0.40 Ah by CK7 at the MAP (F3).
  - Changing τ_b is a trade-off, not a free gain.
- **Wrong or overstated:**
  - **"Checkup periods are empty storage; skip their calendar ageing."** The test also switched off the chamber switches, which r5c labels "checkup". After the day-resolution fix, those switches are only 3.1 days. The pack enters checkups at mid SOC, not empty. A physical SOC weight (S) is inert, and its pseudo/cold gains were below noise.
  - **"Arrhenius on k changes CK2 a lot."** For the calendar term alone it does not (0.013 pp). The 10-21 aT² test probably also changed the break-in clock.
  - **"Replace break-in with a literature overhang term."** Done with frozen literature parameters (O2). It moves real CK2 the "right" way but fails causally, as O1 does.
  - **The literature k(SOC) values were unverified.** Naumann's cubic misfits its own data by up to 40 %. The TUM data table was used instead.

## Recommendation

**No design improves r5c.** Keep the submission unchanged.
- Do not adopt O1/O2 on the strength of their real-proxy CK2 gains (exposed-CK2).
- Further work on r5c's break-in or calendar physics is unlikely to pay off with the current labels. τ_b cannot be identified from 7 anchors, and the causal cases cannot separate a CK2 fix from month-4/5 damage.
- The open problem remains the common-mode level (leaderboard), which this study cannot see.

## Files

- `wp0/REPORT.md`: reproduction, noise floor, facts F1–F6.
- `wp1/REPORT.md` and `wp1/outputs/external_params.json`: frozen parameters.
- `wp2/REPORT.md`: screen and paired check.
- `wp3/REPORT.md`: E1 curves; FINAL against SUB.
- `wp4/REPORT.md`: the real run.
- `notes/DECISIONS.md`: D0.1–D3.1. `notes/STATUS.md`.
- WP5 was skipped by rule (FINAL is not causally better than SUB).

---

<a id="zh"></a>

# 第 17 轮：r5c 压力模型的物理改进——最终报告

> **语言：** [English](#en) · 中文

- **运行：** 2026-10-21，无人值守，按 [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md) 执行。
- **位置：** 工作树 `/Users/shane/Desktop/Arena_1021_r17_r5c`，分支 `exp/phase2-r17-r5c-improve-20261021`，基于 r5c `348af0b`。
- **选择：** 只用因果案例（伪情景 PG1/PG2/PC5/PC10 + 冷启动 CS/CSE，共 28 个）。真实场景在所有选择都提交之后只运行了一次。所有代理都已曝光。
- **未改动：** 任何提交文件和提交包、任何更早的研究。没有打 zip，没有上传。

## 结论在前

1. **没有设计能改进 r5c，提交版本不变。**
   - 六个基于文献的改动中有四个是**惰性**的：预测变化低于台阶变体的噪声底（T_move = 0.110 pp）。它们是换温箱修正 B0、按 SOC 加权的日历时钟 S、日历 Ea 加在 k 上（C）、去掉循环项（D）。
   - 两个能动预测的设计——τ_b 模型平均（O1）和可逆 overhang 状态（O2）——在因果案例上让 R3_T 略微*变差*：配对变化均值 +0.008 / +0.007 pp；各自都对第 3 月有帮助，对第 4–5 月有损害。
   - **FINAL = REF**（0.75·R3_T + 0.25·V2，即 r5c 原样）。它在因果上并不优于 SUB：配对差均值 −0.018 pp，小于 δ = 0.028 pp，而且五个月份块中有两个更差。
2. **10-21 的效应为什么站不住：**
   - **运行 SOC 每个月都一样。** 各月平均 SOC 为 0.57–0.63，25 °C 下标准差 0.008。所以运行时间上的任何 SOC 权重都会被 A_cal 吸收。检测期和换温箱只占 Arrhenius 时钟的 7%。
   - **日历 Arrhenius 的写法几乎无关紧要。** 只改日历项时，真实 CK2 只动 0.013 pp。
   - **10-21 的大幅变化来自磨合时间尺度 τ_b。** 它**识别不出来**：28 个因果案例中，Laplace 最大权重 ≥ 0.8 的有 0 个。缩短磨合（O1、O2）会把损失从后面的月份挪到前面。这修好了真实 CK2（−0.64 → −0.35/−0.40 pp），却让因果的第 4/5 月块变差。
   - **10-21 中关掉检测期老化带来的伪情景/冷启动收益**（0.004–0.012 pp）低于本轮的噪声门槛 δ = 0.028 pp。
3. **真实代理本会选中 O2/O1，但理由是错的。** O2_ens 和 O1_ens 在真实代理上的 MAE 为 0.103 / 0.108 pp，REF 为 0.131，SUB 为 0.120。收益全部来自 CK2；去掉 CK2 后它们是 0.105，REF 是 0.102。标为 **exposed-CK2**，不推荐。
4. **新发现的事实：**
   - F1：真实的换温箱一共只有 3.1 天。如果按严格时刻判断，会把三次真实检测误标为换温箱（D0.3）。
   - F4：**Yagci 的 37.3 kJ/mol 是加在 k 上的 Ea**，来自同等时长下试验结束时损失的 Arrhenius 图。r5c 把它加在时间上，所以 r5c 的时钟在 k 上只有 18.65 kJ/mol。它接近 Schimpe 的 20.6 只是巧合。
   - WP1：Naumann 2018 的 k_SOC 三次式与它自己的 TUM 数据最多相差 40%。Lewerenz 2018 在 50 °C 下的补偿时间是 100 天，不是 150 天。
5. **范围。** 本轮没有任何内容涉及排行榜暗示的 0.7–1.0 pp 水平误差。r5c 系列的每个模型都比 SUB **低** 0.06–0.19 pp（CK1–7 均值），离两种解读（真值比 SUB 低约 1 pp，或 CK2–7 比 SUB 高约 +0.65 pp）都很远，所以它们也不能拿来做水平探针。

## 总表

单位 pp；Δ = 0.4。p = |err_X| − |err_R3_T|，q = |err_X_ens| − |err_REF|，在因果案例上计算。真实各列已曝光。水平一列是集成相对 SUB 在 CK1–7 上的平均 SOH 偏移。

| 设计 | 能动？S_causal / S_real | 因果是否通过 | p / q 均值 | LOKO 最大（p） | 真实 MAE 单独 / 集成 | 真实 CK2（集成） | 标签 | 相对 SUB 的水平（集成） |
|---|---|---|---|---|---|---|---|---|
| B0 换温箱修正 | 否，0.008 / 0.009 | 惰性 | — | — | 0.181 / 0.133 | −0.311 | | −0.125 |
| S 按 SOC 加权的日历项（k_SOC²，TUM） | 否，0.022 / 0.022 | 惰性 | — | — | 0.181 / 0.133 | −0.297 | | −0.118 |
| C 日历 Ea 加在 k 上（时间上 41.2） | 否，0.007 / 0.013 | 惰性 | — | — | 0.178 / 0.129 | −0.302 | exposed-CK2 | −0.121 |
| O1 τ_b 的 Laplace 平均 | 是，0.115 / 0.242 | **不通过**（1、2、3、5、6） | +0.008 / +0.020 | +0.023 | 0.155 / 0.108 | −0.130 | exposed-CK2；τ_b 不可识别 | −0.080 |
| O2 overhang 状态 | 是，0.147 / 0.288 | **不通过**（1、2、3、5、6） | +0.007 / +0.001 | +0.017 | 0.158 / 0.103 | −0.096 | exposed-CK2 | −0.104 |
| D 去掉循环项 | 否，0.034 / 0.035 | 非劣（接受，但不应用） | — | — | 0.176 / 0.129 | −0.285 | exposed-CK2 | −0.109 |
| M_comb | — | 无（没有设计通过） | | | | | | |
| E2 两档权重 | — | 不运行（`phase` 案例 4 个 < 6） | | | | | | |
| **FINAL = REF** | — | 对 SUB：r 均值 −0.018，条件 1 和 2 不满足 | | −0.006 | — / 0.131 | −0.311 | r5c 的门槛全部通过 | −0.124 |

## 预期与结果对照

| 运行前写下的预期 | 结果 |
|---|---|
| C 对预测影响很小 | **证实。** S_causal 0.007，真实 CK2 +0.013 pp |
| S 只通过换温箱/检测期/缺失段改变预测，远小于 10-21 的测试 | **证实，而且更强：惰性**（0.022）。即使真实检测期全按 0% SOC，也只动 0.024 |
| O2 像一个 τ ≈ 50–75 天的磨合项（WP1 给出 45 °C 下 48.6 天）；CK2 落在 10-21 表中 τ_b = 60 与 134 天两行之间，而那两行的伪情景更差 | **证实。** 集成的 CK2 为 −0.096，落在 +0.08 和 −0.31 之间。单独时伪情景比 R3_T 差（0.123 对 0.119）；在集成中伪情景变好（0.115 对 REF 0.123），但冷启动变差（0.151 对 0.134）。净 q ≈ 0 |
| D 很可能惰性 | **证实**（0.034） |
| "没有设计在因果上优于 REF"很可能 | **证实** |

## 10-21 分析说对了什么、说错了什么

- **说对的：**
  - r5c 的 CK2 是抵消出来的（R3_T −0.638 对 V2 +0.669）。
  - CK2 依赖一个识别不出来的磨合时间常数。Laplace 证据证实 τ_b 不可识别。
  - 循环项作用很小：MAP 下到 CK7 只有 0.40 Ah（F3）。
  - 改 τ_b 是一种取舍，不是白给的提升。
- **说错或夸大的：**
  - **"检测期是放空停放，应不计日历老化"。** 那次测试把 r5c 标为"checkup"的换温箱也一起关掉了。按天修正后，换温箱只有 3.1 天。电池组进入检测时处于中等 SOC，而不是空的。物理上合理的 SOC 权重（S）是惰性的，那次测试的伪情景/冷启动收益也低于噪声。
  - **"Arrhenius 加在 k 上会大幅改变 CK2"。** 只对日历项而言并不会（0.013 pp）。10-21 的 aT² 测试很可能也改了磨合项的时钟。
  - **"用文献 overhang 项替换磨合项"。** 本轮用冻结的文献参数做了（O2）。它让真实 CK2 朝"正确"方向移动，但和 O1 一样在因果上不通过。
  - **文献 k(SOC) 数值没有核实过。** Naumann 的三次式与它自己的数据最多差 40%，本轮改用 TUM 数据表。

## 建议

**没有设计能改进 r5c**，提交版本保持不变。
- 不要因为 O1/O2 在真实代理上的 CK2 收益而采用它们（exposed-CK2）。
- 在现有标签下，继续研究 r5c 的磨合或日历物理不太可能有回报：τ_b 无法从 7 个锚点中识别，而因果案例也分不清"修好 CK2"和"损害第 4/5 月"。
- 真正悬而未决的仍是共模的水平问题（排行榜），而本研究看不见它。

## 文件

- `wp0/REPORT.md`：复现、噪声底、事实 F1–F6。
- `wp1/REPORT.md` 和 `wp1/outputs/external_params.json`：冻结的参数。
- `wp2/REPORT.md`：筛查和配对检查。
- `wp3/REPORT.md`：E1 曲线；FINAL 与 SUB 的比较。
- `wp4/REPORT.md`：真实运行。
- `notes/DECISIONS.md`：D0.1–D3.1。`notes/STATUS.md`。
- WP5 按规则跳过（FINAL 在因果上并不优于 SUB）。
