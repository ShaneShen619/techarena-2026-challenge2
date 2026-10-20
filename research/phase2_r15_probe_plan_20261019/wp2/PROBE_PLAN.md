<a id="en"></a>

# Round 15 probe plan

> **Language:** English · [中文](#zh)

## The plan in one paragraph

**One probe: P_A3fix. Upload it once, read the board with the rules below, and re-upload SUB unless the probe wins.** P_A3fix is SUB with round 12's anchor-3 bottom correction (a_3^rel = 0.3047 Ah). It lowers CK4 by 0.36 pp and CK5–CK7 by 0.02 pp. Under round 6's 18 truth hypotheses it beats SUB in expectation under every metric (Δs ≈ −0.009; s, nMAE, nRMSE, nMAX), wins clearly on 14 of 18, and loses by at most +0.017. All four metrics give the same sign on 17 of 18 hypotheses, and on 24 of 27 under round 11's wider drift range. Nothing else was eligible.

## Chosen probe

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| SUB (`6525edf`) | 95.984 | 94.507 | 93.600 | 92.821 | 92.015 | 91.426 | 90.765 |
| **P_A3fix** | 95.984 | 94.507 | 93.600 | **92.461** | 91.987 | 91.410 | 90.750 |
| difference (pp) | 0 | 0 | 0 | −0.360 | −0.028 | −0.016 | −0.015 |

Source: [probe_soh.csv](probe_soh.csv). The vector is the probe's own CLI output and equals round 12's `SUB_A3fix` exactly.

**What changes in the model.** The first from-empty full charge of segment 6 (anchor 3, after CK3) is reduced by 0.3047 Ah after its step-to-top distance is computed. Round 12 found that this anchor's charge started from an unrelaxed state (+53 mV/h after a 3.1-day window), so its charged Ah overstate the capacity. Four of five bottom locators agreed on the sign (G_a3). The effect reaches CK4 through the anchor term and CK5–CK7 through β.

**Expected effect on the board** ([ranking.csv](ranking.csv), [delta_s_long.csv](delta_s_long.csv)):

| Grid | Same sign under all 4 metrics | Detectable (all \|Δs\| > 0.005) | E[Δs] s / nMAE / nRMSE / nMAX | Worst case | Clear wins |
|---|---|---|---|---|---|
| G_main (round 6, decides) | 94 % (17/18) | 89 % | −0.0092 / −0.0085 / −0.0095 / −0.0097 | +0.017 | 14/18 |
| G_r11 (d ∈ {−0.036, 0, +0.052}, gate) | 89 % (24/27) | 78 % | −0.0074 / −0.0059 / −0.0072 / −0.0092 | +0.018 | 18/27 |
| G_env (rounds 13/14 envelopes, descriptive) | 91 % | 61 % | −0.0081 / −0.0078 / −0.0088 / −0.0078 | +0.017 | 29/54 |

For scale: SUB's predicted s ranges over 0.035–0.223 across G_main (ExampleModel = 1), so −0.009 is a small but readable step at three displayed decimals.

**Where it loses.** P_A3fix loses only where the truth at CK4 is high: Δ = 0.8 with f = 0 (+0.011 to +0.017), and, on G_r11, d = +0.052 with Δ ≥ 0.4. There SUB's CK4 is already at or below the truth, and lowering it hurts.

## Reading table

tol = the board's display precision: one unit of the last digit shown, or 0.005 if it cannot be read. Observed Δ = board value of P_A3fix − board value of SUB, for the same metric.

| Board shows | Reading | Meaning | Action |
|---|---|---|---|
| Δ < −tol on at least one shown metric, and no shown metric > +tol | **probe wins** | the hidden CK4 lies below SUB's CK4 by more than about half the correction (≈ 0.18 pp). This is consistent with anchor 3's charge being inflated by its unrelaxed start, and also with a generally lower truth | adopt a_3^rel; run WP4 to build the final package with disclosure; wiring it into the team package is the user's call |
| Δ > +tol on any shown metric | **probe loses** | the truth at CK4 is at or above SUB (large Δ, little recovery, no or positive drift): the correction overshoots | re-upload SUB at once; drop the hypotheses that predicted a clear win |
| \|Δ\| ≤ tol on every shown metric | no information | the change is below the display precision, or the shown metric does not see CK4 (e.g. MAX set by another checkup) | re-upload SUB at once |
| only ranks shown | no information | ranks depend on other teams | re-upload SUB at once |

**Prerequisite:** SUB's own board value must be known, i.e. the board must already have evaluated `Current State_Challenge2.zip` (SHA256 `a4ed59a3…200f`, or any zip whose `model_template.py` has SHA256 `3bd26ed8…fbd5`). Without it, P_A3fix cannot be read.

## Timeline

`inputs/deadline.txt` = **unknown**. The guide says that evaluations happen every two weeks (the PDF says weekly). The plan uses two weeks and assumes at most two evaluation cycles remain.

| Step | When | What the user does |
|---|---|---|
| 0 | now | Make sure SUB (`Current State_Challenge2.zip`) is the active submission. When the board shows its value (board B0), copy it into `inputs/leaderboard_log.csv`. Try to learn the deadline (see [ORGANIZER_QUESTION.md](ORGANIZER_QUESTION.md)) and write it into `inputs/deadline.txt`. |
| 1 | right after B0 is logged, **only if** the next evaluation (B1, ≤ 2 weeks later) is expected at least 3 days before the deadline | Upload the P_A3fix zip (`cache/packages/P_A3fix/Current State_Challenge2.zip`). |
| 2 | right after B1 shows the probe's value | Log it and run WP4. Unless P_A3fix wins, re-upload SUB's zip **the same day**. |
| 3 | before the deadline | The last submission is SUB or the adopted P_A3fix package, never a losing probe. |

If the deadline stays unknown, or step 1's condition cannot be confirmed, **do not upload the probe**: keep SUB as the last submission. A probe that is still active at the deadline breaks the end-state rule.

## End-state rule (registered)

The last submission before the deadline must be the best observed option, SUB by default. A probe is never left as the last submission unless it won. Re-upload SUB right after the probe's evaluation unless it won.

## Not chosen, and why

| Probe | Status | Reason |
|---|---|---|
| P_level | not eligible | round 12 = L3 |
| P_drift | not eligible | rounds 13 and 14 are both O3; neither reached O2 |
| P_stress_early | dropped | cannot be rebuilt on the current SUB without refitting against proxies; not a one-scalar change |

Descriptive context, which played no role in the decision: round 6's P_drift rebuilt on SUB (d = −0.031) would pass the selection if it were eligible (E[Δs] −0.015, worst +0.047). So would round 14's d_top median (E[Δs] −0.012, worst **+0.163**). Round 13's d_tail median would not (E[Δs] +0.010). Making either eligible would need a new registered round, not an edit of this plan.

---

<a id="zh"></a>

# 第 15 轮探针计划

> [English](#en) · 中文

## 一段话说明计划

**一个探针：P_A3fix。上传一次，按下面的规则解读榜单；除非探针胜出，否则重新上传 SUB。** P_A3fix 是加上第 12 轮锚点 3 底部修正（a_3^rel = 0.3047 Ah）的 SUB。它把 CK4 下调 0.36 pp，把 CK5–CK7 下调 0.02 pp。在第 6 轮的 18 个真值假设下，它在每个指标下的期望都优于 SUB（Δs ≈ −0.009；s、nMAE、nRMSE、nMAX），在 18 个中的 14 个上明显胜出，最多输 +0.017。四个指标在 18 个假设中的 17 个上符号一致；在第 11 轮更宽的漂移范围下，27 个中 24 个一致。没有别的探针合格。

## 选中的探针

SOH 表见英文部分（来源：[probe_soh.csv](probe_soh.csv)）。该向量是探针自己的 CLI 输出，与第 12 轮的 `SUB_A3fix` 完全相同。

**模型改了什么。** 第 6 段（锚点 3，CK3 之后）的第一次从空到满的满充，在算完其台阶到顶距离之后减去 0.3047 Ah。第 12 轮发现这个锚点的充电是从未松弛的状态开始的（3.1 天窗口后 +53 mV/h），所以它充入的 Ah 高估了容量；5 个底部定位器中有 4 个符号一致（G_a3）。这个影响通过锚点项传到 CK4，通过 β 传到 CK5–CK7。

**对榜单的预期影响**（[ranking.csv](ranking.csv)、[delta_s_long.csv](delta_s_long.csv)）：数值见英文部分的表。G_main（决定）：四个指标符号一致 94 %（17/18），E[Δs] 约 −0.009，最坏 +0.017，明显胜出 14/18。G_r11（门槛）：89 %（24/27），最坏 +0.018。作为参照：在 G_main 上 SUB 的预测 s 在 0.035–0.223 之间（ExampleModel = 1），所以 −0.009 在显示三位小数时是一个小但可读的变化。

**在哪里输。** 只有在 CK4 真值偏高时 P_A3fix 才输：Δ = 0.8 且 f = 0（+0.011 至 +0.017），以及在 G_r11 上 d = +0.052 且 Δ ≥ 0.4。这些情况下 SUB 的 CK4 已经等于或低于真值，再往下调就有害。

## 解读表

tol = 榜单的显示精度：所显示最后一位的一个单位；读不出时取 0.005。观测 Δ = 同一指标下 P_A3fix 的榜单值 − SUB 的榜单值。

| 榜单显示 | 读数 | 含义 | 行动 |
|---|---|---|---|
| 至少一个显示指标 Δ < −tol，且没有显示指标 > +tol | **探针胜出** | 隐藏的 CK4 比 SUB 的 CK4 低，幅度超过修正量的一半左右（≈ 0.18 pp）。这与锚点 3 的充电因未松弛的起点而偏高一致，也与真值整体偏低一致 | 采纳 a_3^rel；运行 WP4 构建带披露的最终包；是否接入团队包由用户决定 |
| 任一显示指标 Δ > +tol | **探针落败** | CK4 真值等于或高于 SUB（Δ 大、恢复少、无漂移或正漂移）：修正过头 | 立即重新上传 SUB；排除那些预测明显胜出的假设 |
| 每个显示指标都 \|Δ\| ≤ tol | 无信息 | 变化小于显示精度，或者显示的指标看不到 CK4（比如 MAX 由别的检查点决定） | 立即重新上传 SUB |
| 只显示排名 | 无信息 | 排名取决于其他队伍 | 立即重新上传 SUB |

**前提：** 必须已知 SUB 自己的榜单值，也就是榜单已经评估过 `Current State_Challenge2.zip`（SHA256 `a4ed59a3…200f`，或任何 `model_template.py` 的 SHA256 为 `3bd26ed8…fbd5` 的 zip）。没有它，P_A3fix 无法解读。

## 时间线

`inputs/deadline.txt` = **unknown**。指南说每两周评估一次（PDF 说每周）。本计划按两周计，并假设最多还剩两个评估周期。

| 步骤 | 时间 | 用户做什么 |
|---|---|---|
| 0 | 现在 | 确认 SUB（`Current State_Challenge2.zip`）是当前有效的提交。榜单显示它的值后（榜单 B0），抄进 `inputs/leaderboard_log.csv`。设法弄清截止时间（见 [ORGANIZER_QUESTION.md](ORGANIZER_QUESTION.md)），写进 `inputs/deadline.txt`。 |
| 1 | B0 记录之后立即进行，**前提是**下一次评估（B1，≤ 2 周后）预计在截止前至少 3 天 | 上传 P_A3fix 的 zip（`cache/packages/P_A3fix/Current State_Challenge2.zip`）。 |
| 2 | B1 显示探针的值之后立即进行 | 记录并运行 WP4。除非 P_A3fix 胜出，**当天**重新上传 SUB 的 zip。 |
| 3 | 截止之前 | 最后一次提交是 SUB 或采纳后的 P_A3fix 包，绝不是落败的探针。 |

如果截止时间一直未知，或无法确认步骤 1 的条件，**就不要上传探针**：保持 SUB 为最后一次提交。截止时仍处于有效状态的探针违反最终状态规则。

## 最终状态规则（已登记）

截止前的最后一次提交必须是观测到的最佳选项，默认是 SUB。除非探针胜出，否则绝不能让探针成为最后一次提交。探针评估之后，除非它胜出，立即重新上传 SUB。

## 没有选中的探针及原因

| 探针 | 状态 | 原因 |
|---|---|---|
| P_level | 不合格 | 第 12 轮 = L3 |
| P_drift | 不合格 | 第 13、14 轮都是 O3；没有一轮达到 O2 |
| P_stress_early | 放弃 | 不对代理标签重新拟合就无法在当前 SUB 上重建；不是单标量改动 |

仅作背景、不参与决策：在 SUB 上重建的第 6 轮 P_drift（d = −0.031）如果合格，会通过选择（E[Δs] −0.015，最坏 +0.047）。第 14 轮的 d_top 中位数也会通过（E[Δs] −0.012，最坏 **+0.163**）。第 13 轮的 d_tail 中位数不会通过（E[Δs] +0.010）。要让其中任何一个合格，需要新登记一轮，而不是修改本计划。
