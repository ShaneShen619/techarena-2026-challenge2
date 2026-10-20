<a id="en"></a>

# Round 12 — ε-level measurement

> **Language:** English · [中文](#zh)

**L3: keep SUB (`6525edf`) and `EPS_EXTRA_AH = 0.4` as an assumption.** The registered budget is +4.48 Ah [2.35, 6.34], with neither T_top nor a_0 identified. It does not justify replacing 0.4. No P_level probe is recommended; SUB_A3fix remains a research candidate without a demonstrated leaderboard gain.

Read the [final report](FINAL_REPORT.md) for the evidence, all five SOH variants, limitations and verification. The [machine-readable decision](wp4/budget_decision.json) and [Round 13 handoff](wp4/R13_HANDOFF.json) preserve the registered outcome and unresolved terms.

| Model | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| SUB — retained | 95.984 | 94.507 | 93.600 | 92.821 | 92.015 | 91.426 | 90.765 |
| SUB_A3fix — candidate only | 95.984 | 94.507 | 93.600 | 92.461 | 91.987 | 91.410 | 90.750 |

SOH is in percent. The candidate subtracts 0.3047 Ah from anchor 3's Q_fc after preserving its step-to-top distance; it is not wired into the submission. The three ε-budget sensitivity rows in [SOH_variants.csv](wp4/SOH_variants.csv) are not recommended candidates.

- [WP0](wp0/REPORT.md): reproduction, sensitivity and event inventory.
- [WP1](wp1/REPORT.md): registration and synthetic verification.
- [WP2](wp2/REPORT.md): bottom mismatch and shared-bottom gates.
- [WP3](wp3/REPORT.md): anchor-top offset and Ah-chain limitations.
- [WP4](wp4/REPORT.md): L3 decision, candidate and README wording for possible future use.
- [Status](notes/STATUS.md), [decisions](notes/DECISIONS.md) and [sources](sources/SOURCES.md): execution record and provenance.

Closeout verification: 5/5 registered hashes match, 15/15 synthetic tests pass, budget arithmetic and SOH agree with their source files, and the submission is unchanged. Documentation is complete locally; no upload or Git push was performed, as requested. This is the study README, not a change to the submission package README.

**Update 2026-10-20:** the user later authorised the push (D45); the branch is now pushed to `origin exp/phase2-r12-eps-level-20261019`.

---

<a id="zh"></a>

# 第 12 轮 — ε 水平测量

> [English](#en) · 中文

**L3：保留 SUB（`6525edf`），`EPS_EXTRA_AH = 0.4` 仍为假设。** 登记预算为 +4.48 Ah [2.35, 6.34]，T_top 和 a_0 均未识别，不能据此替换 0.4。不推荐 P_level 探针；SUB_A3fix 仅为研究候选，尚无已证明的排行榜收益。

[最终报告](FINAL_REPORT.md)包含证据、五行 SOH 变体、局限与核验。[机器可读决策](wp4/budget_decision.json)及[第 13 轮交接](wp4/R13_HANDOFF.json)保存登记结论和未解决项。

各检查点 SOH（%）见英文部分表格：保留 SUB；SUB_A3fix 保留锚点 3 的台阶至顶部距离，再从其 Q_fc 减去 0.3047 Ah，尚未接入提交。其 CK4 为 92.461%，相对 SUB 下降 0.360 个百分点；其余变化较小。[SOH_variants.csv](wp4/SOH_variants.csv) 中三行 ε 预算敏感性变体不是推荐候选。

WP0–WP4 报告链接见上方，分别覆盖事实复核、登记、底部、顶部和最终决策；[状态](notes/STATUS.md)、[决策记录](notes/DECISIONS.md)及[来源](sources/SOURCES.md)记录执行与溯源。

收尾核验：5 项登记哈希全部一致，15/15 合成测试通过，预算与 SOH 均与源文件一致，提交包未改变。文档在本地完成；按用户要求未上传、未 Git push。这是研究目录的 README，没有改动提交包 README。

**2026-10-20 更新：** 用户随后授权推送（D45），本分支已推送到 `origin exp/phase2-r12-eps-level-20261019`。
