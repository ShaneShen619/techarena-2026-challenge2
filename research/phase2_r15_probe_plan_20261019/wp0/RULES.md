<a id="en"></a>

# WP0 — Rules audit

> **Language:** English · [中文](#zh)

## Conclusions

- **Probing is not forbidden, but nothing invites it.** Resubmission is unlimited and "the last submission counts". The only explicit prohibition on the hidden checkups is about reconstructing them "from external sources".
- **Five facts we need are not published:** the deadline, the platform, the cadence (the PDF says weekly, the guide says every two weeks), the metric set, and whether the board shows one score or several. The reduced-budget size is also missing, although the PDF says the guide gives it.
- **What is known about the metric:** errors on CK1..CK7 only, "including the worst-case error", each normalised by the ExampleModel (baseline = 1.0, lower is better). So a MAX-type metric is in the set; the rest is open. This is why round 15 requires every reading rule to hold under s, nMAE, nRMSE and nMAX.
- **The presentation inside the last zip is the final presentation.** Every probe zip therefore carries a presentation risk: the existing zips and the input default (`template`) both use the template deck.

## 1. Rule sentences, verbatim

Files: `TechArena_Challenge2_Team_Package/submission_instructions_2026.md` ("guide", line numbers from `cat -n`) and `TechArena_Challenge2_Team_Package/CHALLENGE2_DESCRIPTION.pdf` ("PDF", 2 pages, `pdftotext -layout`), both at base `6525edf`.

| # | Topic | Source | Verbatim text |
|---|---|---|---|
| R1 | Resubmission | PDF p. 1, §1 item 6 | "Package and submit as often as you like. Standardized command-line interface and output CSV (identical to Challenge 1: run_model.py --model train / test); a public leaderboard is updated weekly; only submissions that run successfully through the automated pipeline are scored." |
| R2 | Reduced-budget run | PDF p. 1, §1 item 5 | "Do more with less (bonus). Every submission is additionally evaluated in a reduced-budget run with only part of the operating data (exact budget in the Submission & Validation Guide). Models that keep their accuracy with less data earn a data-efficiency bonus on top of their score." |
| R3 | Baseline | PDF p. 1, §1 item 4 | "A reference baseline (partial-charge coulomb counting anchored at CK0) is provided and defines the score of 1.0." |
| R4 | Truth | PDF p. 1, "Wanted" | "Estimates are evaluated against the hidden C/20 capacities measured at those checkups." |
| R5 | Logistics | PDF p. 2, end of §2.3 | "Timeline, submission platform and deadline: see the Submission & Validation Guide shared with this document." |
| R6 | Only CK0 is a target | guide l. 119–122 | "**Only CK0 is a target.** The beginning-of-life capacity (100.41 Ah = 98.44 % SOH of the nominal 102 Ah) is the only capacity value you receive. Checkups CK1 to CK7 are hidden and scored; their dates are known (`evaluation_points.csv`), their values are not. Do not attempt to reconstruct them from external sources." |
| R7 | Deadline, last submission | guide l. 235–237 | "`<<TODO: submission platform / upload link>>`. There is no limit on how many times you may resubmit before the deadline (`<<TODO: deadline date/time and timezone>>`); the last submission counts." |
| R8 | Presentation | guide l. 239–242 | "The final TechArena presentation may also be updated with each resubmission. The version of `<TeamName>_Final_Presentation.pptx` included in your last Challenge 2 submission before the deadline will be used as the final version for the TechArena final event. No separate presentation upload is required." |
| R8b | Presentation | guide l. 44–47 | "The presentation included in your final Challenge 2 submission zip before the submission deadline will be used as your final presentation for the TechArena final event." |
| R9 | Cadence | guide l. 244–245 | "Submissions are evaluated every two weeks and the public leaderboard is updated accordingly." |
| R10 | Scoring | guide l. 257–264 | "Model performance is scored on the hidden checkups CK1..CK7 only, as error metrics of your SOH estimates (including the worst-case error), each normalised by the reference baseline - **baseline = 1.0, lower is better**. The exact metric set is not published. Model performance counts 70 % of the final score; Technical Innovation (data efficiency, transferability, use of open data), Interpretability & Explainability, and Code Quality & Reproducibility (PEP 8, documentation) count 10 % each and are assessed from your submission and report." |
| R11 | Presentation not scored here | guide l. 266–268 | "The final TechArena presentation is **not part of the Challenge 2 submission score or leaderboard evaluation**. It will be evaluated separately during the TechArena final event." |
| R12 | One zip | guide l. 123–125 | "**One zip, correctly named**: `<TeamName>_Challenge2.zip`. Nothing is uploaded alongside it. The final TechArena presentation must be included inside this zip." |
| R13 | Framework files | guide l. 56–57 | "Framework files are compared byte-wise against the original and deviations are reported to the jury." |

Differences from the prompt's abridged quotes (§2): R6 and R7 are longer in the source; R7's placeholder reads `<<TODO: deadline date/time and timezone>>`; the PDF's cadence sentence (R1) continues "only submissions that run successfully … are scored". No substantive difference.

## 2. Open points

| Open point | What the documents say | Consequence for round 15 |
|---|---|---|
| Deadline | R7 is a placeholder; R5 points to the guide; `inputs/deadline.txt` = "unknown" | assume at most two evaluation cycles remain (prompt WP1 end-state rule) |
| Platform / upload link | R7 placeholder | user action only; nothing is uploaded by this round |
| Cadence | weekly (R1, PDF) vs every two weeks (R9, guide) | plan with two weeks (the slower, conservative reading) |
| Metric set | R10: not published; includes a worst-case error; each normalised by the baseline | every reading rule must hold under s, nMAE, nRMSE, nMAX |
| One score or several on the board | not stated; "each normalised" suggests several normalised metrics, but the board's display is not described | the reading rule applies to every shown metric (WP1) |
| Display precision of the board | not stated | tol = 0.005 until the log shows the precision |
| Reduced-budget run | R2: "exact budget in the Submission & Validation Guide"; the guide does not give it | unknown whether the board shows it; a probe's effect may differ there |
| Evaluation hardware | guide l. 159: `<<TODO: confirm hardware>>` | not relevant to probes (all variants run in < 1 min locally) |
| Probing | not addressed; R6 forbids reconstructing hidden values "from external sources" | registered stance: ≤ 2 one-scalar probes, disclosed (prompt §2) |

---

<a id="zh"></a>

# WP0 — 规则审查

> [English](#en) · 中文

## 结论

- **探测没有被禁止，但规则也没有鼓励它。** 可以无限次重新提交，"最后一次提交才算数"。关于隐藏检查点，唯一明确的禁止是"从外部来源"重建它们。
- **我们需要的五件事没有公布：** 截止时间、提交平台、评估频率（PDF 说每周，指南说每两周）、指标集，以及排行榜显示一个分数还是多个。缩减数据量运行的数据量也没有给出，尽管 PDF 说指南里有。
- **关于指标已知的：** 只看 CK1..CK7 上的误差，"包括最坏情况误差"，每个都除以 ExampleModel 的值（基线 = 1.0，越低越好）。所以指标集里有一个 MAX 类指标，其余未知。这就是第 15 轮要求每条解读规则在 s、nMAE、nRMSE 和 nMAX 下都成立的原因。
- **最后一个 zip 里的演示文稿就是决赛用的版本。** 所以每个探针 zip 都带有演示文稿风险：现有 zip 和输入默认值（`template`）用的都是模板。

## 1. 规则原文

文件：`TechArena_Challenge2_Team_Package/submission_instructions_2026.md`（"指南"，行号来自 `cat -n`）和 `TechArena_Challenge2_Team_Package/CHALLENGE2_DESCRIPTION.pdf`（"PDF"，2 页，`pdftotext -layout`），均为基点 `6525edf` 的版本。原文为英文，下表保留英文原句。

| # | 主题 | 出处 | 原文 |
|---|---|---|---|
| R1 | 重新提交 | PDF 第 1 页 §1 第 6 条 | "Package and submit as often as you like. … a public leaderboard is updated weekly; only submissions that run successfully through the automated pipeline are scored."（完整原文见英文部分） |
| R2 | 缩减数据量运行 | PDF 第 1 页 §1 第 5 条 | "Every submission is additionally evaluated in a reduced-budget run with only part of the operating data (exact budget in the Submission & Validation Guide). …" |
| R3 | 基线 | PDF 第 1 页 §1 第 4 条 | "A reference baseline … defines the score of 1.0." |
| R4 | 真值 | PDF 第 1 页 "Wanted" | "Estimates are evaluated against the hidden C/20 capacities measured at those checkups." |
| R5 | 日程 | PDF 第 2 页 §2.3 末 | "Timeline, submission platform and deadline: see the Submission & Validation Guide …" |
| R6 | 只有 CK0 是目标 | 指南第 119–122 行 | "… Checkups CK1 to CK7 are hidden and scored … Do not attempt to reconstruct them from external sources." |
| R7 | 截止与最后一次提交 | 指南第 235–237 行 | "There is no limit on how many times you may resubmit before the deadline (`<<TODO: …>>`); the last submission counts." |
| R8 | 演示文稿 | 指南第 239–242 行、第 44–47 行 | 最后一次提交中的 pptx 即决赛版本 |
| R9 | 评估频率 | 指南第 244–245 行 | "Submissions are evaluated every two weeks and the public leaderboard is updated accordingly." |
| R10 | 评分 | 指南第 257–264 行 | "… error metrics of your SOH estimates (including the worst-case error), each normalised by the reference baseline - baseline = 1.0, lower is better. The exact metric set is not published. Model performance counts 70 % …" |
| R11 | 演示文稿不计入本赛题得分 | 指南第 266–268 行 | 决赛另行评估 |
| R12 | 只交一个 zip | 指南第 123–125 行 | "Nothing is uploaded alongside it." |
| R13 | 框架文件 | 指南第 56–57 行 | 逐字节比对，偏差报告给评审 |

与 prompt 中节选引文的差别：R6、R7 原文更长；R7 的占位符为 `<<TODO: deadline date/time and timezone>>`；PDF 的频率句（R1）后面还有"only submissions that run successfully … are scored"。没有实质差别。

## 2. 未决事项

| 未决事项 | 文件怎么说 | 对第 15 轮的影响 |
|---|---|---|
| 截止时间 | R7 是占位符；R5 指向指南；`inputs/deadline.txt` = "unknown" | 假设最多还剩两个评估周期（prompt WP1 最终状态规则） |
| 平台 / 上传链接 | R7 占位符 | 只由用户操作；本轮不上传任何东西 |
| 评估频率 | 每周（R1，PDF）对每两周（R9，指南） | 按两周计划（更慢、更保守的读法） |
| 指标集 | R10：未公布；包含最坏情况误差；每个都按基线归一化 | 每条解读规则必须在 s、nMAE、nRMSE、nMAX 下都成立 |
| 排行榜显示一个还是多个分数 | 没写；"each normalised" 暗示有多个归一化指标，但没有描述榜单的显示方式 | 解读规则对每个显示的指标都适用（WP1） |
| 榜单显示精度 | 没写 | 在记录显示精度之前 tol = 0.005 |
| 缩减数据量运行 | R2 说数据量见指南；指南没给 | 不知道榜单是否显示它；探针在那里的效果可能不同 |
| 评估硬件 | 指南第 159 行占位符 | 与探针无关（所有变体本地运行都不到 1 分钟） |
| 探测 | 没有提到；R6 禁止"从外部来源"重建隐藏值 | 登记的立场：最多 2 个单标量探针，全部披露（prompt §2） |
