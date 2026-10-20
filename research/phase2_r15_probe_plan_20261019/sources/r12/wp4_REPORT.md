<a id="en"></a>

# WP4 — ε-level budget and decision: report

> **Language:** English · [中文](#zh)

## Conclusions

1. **Decision L3, "inconclusive": keep SUB.**
   - EPS_EXTRA_hat = T_top + a_0 = **+4.48 Ah [2.35, 6.34]**, width 3.99 Ah.
   - 0.4 lies outside the interval, the width exceeds 0.50 Ah, and G_SB failed (which alone would block L2). Neither L1 nor L2 applies.
   - EPS_EXTRA_AH = 0.4 stays an **assumption**. The submission is unchanged.
2. **Neither component is identified.**
   - T_top = +1.11 Ah [0.60, 1.62]; G_T fails with a half-width of 0.51 Ah.
   - a_0 = +3.37 Ah [1.74, 4.72]; G_B3 fails with a width of 2.98 Ah.
   - The budget point is not credible. It would put CK2 at **100.41 % SOH, above CK0's 98.44 %**.
   - WP2 traces it to h, measured on 25 °C anchors and applied to the 45 °C anchor 0. At anchor 0's own top, h differs by 3.7–3.9 Ah.
3. **Exploratory readings (not registered, not decision inputs) neither support nor contradict 0.4.**
   - T_top with time-matched λ is ≈ 0.68 Ah.
   - a_0 with anchor 0's own 45 °C h1 is ≈ −0.31 … −0.51 Ah. These values still carry the first-program offset in h1, which pushes a_0 down by roughly 0.4 Ah.
   - Taken together they put EPS_EXTRA roughly in 0.2–1.2 Ah. That is a range, not a measurement.
4. **Anchor-3 rule: G_a3 passed, so SUB_A3fix is a leaderboard-only candidate.**
   - It subtracts a_3^rel = 0.305 Ah from anchor 3's Q_fc.
   - CK4 moves by −0.360 pp. CK5–CK7 move by −0.028 / −0.016 / −0.015 pp through β, and CK1–CK3 do not move.
   - It is not wired. Its evidence is marginal: a_3^rel is just above the 0.264 Ah threshold, and the same size as the residuals of the relaxed anchors 5 and 7 that made G_SB fail.
5. **Probe: no P_level probe.**
   - The measured shift (+4.08 Ah, i.e. +4.0 pp on CK3–CK7 and +5.9 pp on CK2) is an artefact.
   - The exploratory range gives no direction.
   - Round 7's order **P_stress_early → P_start → P_drift** stays. SUB_A3fix is a registered single-anchor instance of P_start's question; the user decides.
6. **Hand-off (`R13_HANDOFF.json`).** It carries T_top with its terms, a_0, a_3^rel and the H_SB status (rejected for anchors 5, 7). Open terms:
   - the drift d;
   - self-discharge in the checkup rests;
   - the checkup protocol and temperature;
   - the non-stationary loss ratio λ;
   - the temperature dependence of h;
   - locator resolution;
   - the unrecorded events before anchors 0 and 3.

## 1. Budget (`budget_decision.json`)

| Component | Point (Ah) | Interval (Ah) | Status |
|---|---|---|---|
| T_top (WP3) | +1.108 | [0.602, 1.616] | not identified (G_T: half-width 0.507 > 0.25) |
| a_0 (WP2) | +3.374 | [1.745, 4.722] | not identified (G_B3: width 2.977 > 0.40) |
| **EPS_EXTRA_hat** | **+4.483** | **[2.347, 6.338]** | width 3.991 |

## 2. Decision

| Rule | Condition | Result |
|---|---|---|
| L1 | 0.4 ∈ interval and width ≤ 0.50 | no (0.4 outside, width 3.99) |
| L2 | 0.4 ∉ interval, width ≤ 0.50, G_noise passed, G_SB not failed | no (width 3.99; G_SB failed) |
| **L3** | any other case | **yes → keep SUB** |
| Anchor-3 rule | G_a3 passes | **yes → SUB_A3fix** (leaderboard-only) |

## 3. SOH variants (`SOH_variants.csv`, leaderboard-only, never scored against proxies)

Each variant is a research copy under `cache/variants/` run through the package CLI. The diffs are in `budget_decision.json`.

| Variant | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| **SUB** (EPS_EXTRA 0.4) | 95.984 | 94.507 | 93.600 | 92.821 | 92.015 | 91.426 | 90.765 |
| SUB, EPS_EXTRA = 4.483 (point) | 95.984 | 100.413 | 97.603 | 96.824 | 96.018 | 95.429 | 94.768 |
| SUB, EPS_EXTRA = 2.347 (lo) | 95.984 | 97.324 | 95.509 | 94.730 | 93.924 | 93.335 | 92.674 |
| SUB, EPS_EXTRA = 6.338 (hi) | 95.984 | 103.096 | 99.422 | 98.642 | 97.837 | 97.248 | 96.587 |
| **SUB_A3fix** | 95.984 | 94.507 | 93.600 | **92.461** | 91.987 | 91.410 | 90.750 |

- SUB_L and the SUB_L + SUB_A3fix combination are not built, because they only apply under L2.
- CK2 moves 1.45 pp per Ah of EPS_EXTRA, against 0.98 for CK3–CK7, through the √t gap branch (WP0).

## 4. Probe

**What `CHALLENGE2_DESCRIPTION.pdf` says** (verbatim):
- "Package and submit as often as you like. Standardized command-line interface and output CSV (identical to Challenge 1: run_model.py --model train / test); a public leaderboard is updated weekly; only submissions that run successfully through the automated pipeline are scored."
- "A reference baseline (partial-charge coulomb counting anchored at CK0) is provided and defines the score of 1.0."
- "Every submission is additionally evaluated in a reduced-budget run with only part of the operating data (exact budget in the Submission & Validation Guide). Models that keep their accuracy with less data earn a data-efficiency bonus on top of their score."
- "Estimates are evaluated against the hidden C/20 capacities measured at those checkups."
- "Timeline, submission platform and deadline: see the Submission & Validation Guide shared with this document."

**Assessment.**
- A single-submission P_level probe would shift CK2–CK7 by the measured EPS_EXTRA change: +4.08 Ah, which is +4.0 pp on CK3–CK7 and +5.9 pp on CK2. That shift comes from a non-identified budget whose point is physically implausible (CK2 above CK0). **It is not worth a submission.**
- Submissions themselves are cheap ("as often as you like"). But the leaderboard updates only weekly and returns one aggregate score per submission, which also includes the reduced-budget run. A level probe therefore costs a week and is confounded by every other error of the model.
- **Place in the order:** none, so the order stays P_stress_early → P_start → P_drift.
- SUB_A3fix changes only CK4 noticeably (−0.36 pp). It is a narrow, registered case of P_start's question ("do anchor start states bias the anchors?"), so it could be submitted as the P_start probe or alongside it.
- Nothing is submitted in this round. **The user decides.**

## 5. README draft (not applied to the package)

> `EPS_EXTRA_AH = 0.4` is an assumption, not a measurement: a registered measurement on the pack's own data (round 12) bounded the 45/25 °C anchor-top offset at 1.11 Ah (interval 0.60–1.62 Ah) but could not identify the bottom term (1.74–4.72 Ah, dominated by the temperature dependence of the graphite-step reference), so the combined interval of 2.35–6.34 Ah neither supports nor replaces 0.4. The value therefore stays at its registered prior, and CK2–CK7 share a level uncertainty of about 0.98 pp per Ah of EPS_EXTRA (1.45 pp per Ah at CK2).

## 6. Hand-off

`wp4/R13_HANDOFF.json`: decision, budget, T_top (terms, event values, gates, excluded pairs), a_0 (components, h, exploratory h1_0, diagnosis), a_3^rel (per locator, candidate effect), H_SB status and anomaly list, SOH of SUB and SUB_A3fix, the open terms listed above, constraints, and the probe advice.

---

<a id="zh"></a>

# WP4 — ε 水平预算与决策：报告

> [English](#en) · 中文

## 结论

1. **决策 L3"无定论"：保留 SUB。**
   - EPS_EXTRA_hat = T_top + a_0 = **+4.48 Ah [2.35, 6.34]**，宽度 3.99 Ah。
   - 0.4 不在区间内，宽度超过 0.50 Ah，而且 G_SB 已失败（单这一条就排除了 L2）。L1 和 L2 都不成立。
   - EPS_EXTRA_AH = 0.4 仍是**假设**，提交不变。
2. **两个分项都未识别。**
   - T_top = +1.11 Ah [0.60, 1.62]，G_T 未通过，半宽 0.51 Ah。
   - a_0 = +3.37 Ah [1.74, 4.72]，G_B3 未通过，宽度 2.98 Ah。
   - 预算的点估计不可信：它会使 CK2 的 SOH 达到 **100.41 %，高于 CK0 的 98.44 %**。
   - WP2 已把原因追溯到 h：它在 25 °C 锚点上测得，却用于 45 °C 的锚点 0；在锚点 0 自己的顶部，h 相差 3.7–3.9 Ah。
3. **探索性结果（未登记、不作为决策依据）既不支持也不否定 0.4。**
   - 用时间匹配 λ 的 T_top ≈ 0.68 Ah。
   - 用锚点 0 自己 45 °C 的 h1 得到的 a_0 ≈ −0.31 … −0.51 Ah。这些值仍含有 h1 中的首个程序偏移，它会把 a_0 拉低约 0.4 Ah。
   - 合起来，EPS_EXTRA 大致在 0.2–1.2 Ah 之间。这只是一个范围，不是测量值。
4. **锚点 3 规则：G_a3 通过，因此 SUB_A3fix 成为只用于排行榜的候选。**
   - 它从锚点 3 的 Q_fc 中减去 a_3^rel = 0.305 Ah。
   - CK4 变化 −0.360 pp；CK5–CK7 经 β 分别变化 −0.028 / −0.016 / −0.015 pp；CK1–CK3 不变。
   - 它不接入提交。证据也只是勉强够格：a_3^rel 仅略高于 0.264 Ah 的阈值，与导致 G_SB 失败的已静置锚点 5、7 的残差大小相当。
5. **探针：不做 P_level 探针。**
   - 测得的平移（+4.08 Ah，即 CK3–CK7 +4.0 pp、CK2 +5.9 pp）是假象。
   - 探索性范围也给不出方向。
   - 第 7 轮的顺序 **P_stress_early → P_start → P_drift** 保持不变。SUB_A3fix 是 P_start 所问问题的一个登记过的单锚点实例，由用户决定。
6. **交接（`R13_HANDOFF.json`）。** 包括 T_top 及其各项、a_0、a_3^rel，以及 H_SB 的状态（对锚点 5、7 不成立）。未解决的项：
   - 漂移 d；
   - 检查静置期间的自放电；
   - 检查协议与温度；
   - 不平稳的损耗比 λ；
   - h 的温度依赖；
   - 定位器分辨率；
   - 锚点 0 和 3 之前未记录的事件。

## 1–3. 预算、决策与 SOH 变体

表格与英文部分第 1–3 节相同（`budget_decision.json`、`SOH_variants.csv`）。各变体的 SOH 只用于排行榜，从不与代理标签对比打分。

## 4. 探针

**`CHALLENGE2_DESCRIPTION.pdf` 原文**（英文原句见英文部分）：
- 可以随意多次打包提交，CLI 和输出 CSV 是标准化的；公开排行榜每周更新；只有在自动流水线中成功运行的提交才会计分。
- 参考基线（以 CK0 为锚的部分充电库仑计数）定义了 1.0 分。
- 每次提交还会在只用部分运行数据的缩减预算下额外评估；数据减少时仍保持精度的模型可以获得数据效率加分。
- 估计值与各检查点测得的隐藏 C/20 容量比较。
- 时间线、提交平台和截止日期见随附的 Submission & Validation Guide。

**评估。**
- 单次提交的 P_level 探针会把 CK2–CK7 按测得的 EPS_EXTRA 变化平移：+4.08 Ah，即 CK3–CK7 +4.0 pp、CK2 +5.9 pp。这个平移来自一个未识别的预算，其点估计在物理上不可信（CK2 高于 CK0）。**不值得用一次提交。**
- 提交本身成本很低（"随意多次"）。但排行榜每周才更新一次，每次只返回一个总分，而且包含缩减预算的评估。因此水平探针要花一周时间，结果还会被模型的其他误差混淆。
- **在顺序中的位置：** 不加入，顺序保持 P_stress_early → P_start → P_drift。
- SUB_A3fix 只明显改变 CK4（−0.36 pp），是 P_start 所问问题（"锚点的起点状态是否带偏了锚点？"）的一个窄而登记过的情形，可以作为 P_start 探针提交，或与之并列。
- 本轮不提交任何东西。**由用户决定。**

## 5. README 草稿（不改动包）

> `EPS_EXTRA_AH = 0.4` 是假设，而不是测量值：第 12 轮在电池组自身数据上的登记测量把 45/25 °C 锚点顶部偏移限定在 1.11 Ah（区间 0.60–1.62 Ah），但无法识别底部项（1.74–4.72 Ah，主要受石墨台阶参照随温度变化的影响），因此合并区间 2.35–6.34 Ah 既不支持也不能取代 0.4。所以该值保持其登记先验，CK2–CK7 共有约每 Ah EPS_EXTRA 0.98 pp 的水平不确定度（CK2 为每 Ah 1.45 pp）。

## 6. 交接

`wp4/R13_HANDOFF.json`：决策、预算、T_top（各项、事件值、门槛、被排除的配对）、a_0（各分量、h、探索性 h1_0、诊断）、a_3^rel（各定位器值、候选的影响）、H_SB 状态与异常列表、SUB 和 SUB_A3fix 的 SOH、上面列出的未解决项、约束条件以及探针建议。
