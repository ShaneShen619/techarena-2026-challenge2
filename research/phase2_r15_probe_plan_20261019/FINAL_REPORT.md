<a id="en"></a>

# Round 15 — Leaderboard probe plan: final report

> **Language:** English · [中文](#zh)

## Conclusions

1. **Plan: at most one probe, P_A3fix.** It is SUB with round 12's anchor-3 bottom correction, a single constant (a_3^rel = 0.3047 Ah). It lowers CK4 by 0.36 pp and CK5–CK7 by 0.02 pp. A validated zip is ready; nothing was uploaded.
2. **Why this one.** It is the only eligible probe:
   - P_level is not eligible (round 12 = L3);
   - P_drift is not eligible (rounds 13 and 14 both O3);
   - P_stress_early was dropped (it cannot be rebuilt without refitting against proxies, and it is not a one-scalar change).
   
   On round 6's 18 truth hypotheses, P_A3fix is expected to beat SUB under every metric of the family (E[Δs] −0.0085 to −0.0097 for s, nMAE, nRMSE, nMAX). It wins clearly on 14/18 and loses by at most +0.017. All four metrics agree in sign on 17/18 hypotheses, and on 24/27 under round 11's wider drift range.
3. **Conditions for using it.** Upload it only if SUB's own board value is already logged **and** the next evaluation is at least 3 days before a known deadline. Re-upload SUB right after the probe's evaluation unless it wins. The deadline is currently unknown, so **today the plan reads: keep SUB; learn the deadline first.**
4. **What a reading would mean.** A win says the hidden CK4 lies more than ≈ 0.18 pp below SUB's CK4. That is consistent with anchor 3's charge being inflated by its unrelaxed start, and also with a generally lower truth. A loss says the truth at CK4 is at or above SUB. A difference within the display precision carries no information.
5. **Leaderboard observations: none.** `inputs/leaderboard_log.csv` did not exist when the round started; it is now an empty template. WP4 status: see the dated sections below.
6. **Risks to keep in mind.**
   - The zip carries the template presentation.
   - The hook is keyed to segment 6, so in the reduced-budget run its effect depends on which part of segment 6 is kept.
   - A reading mostly informs about CK4. This is disclosed, and it is one bit, not a reconstruction.

## What was done

| WP | Result |
|---|---|
| WP0 | Rules audit: 13 verbatim rule sentences, 9 open points. The cadence conflict is recorded: PDF weekly, guide every two weeks. Three existing zips identified (`6525edf` = current SUB, `5cd305c`, `21a7a55`), all with the template deck. SUB reproduces through the CLI. |
| WP1 | Protocol registered (sha256 `f4cf3da6…`) with the registered code; round 6's machinery reproduced exactly (7/7 tests). |
| WP2 | Probe vectors, Δs on 3 grids × 4 metrics, readability, ranking; plan = P_A3fix; organiser question drafted (not sent). |
| WP3 | P_A3fix zip built and validated (fresh venv: validator PASSED; full-data output = expected); SHA256 `3d792662…72e6`; hand-over written. |
| WP4 | 2026-10-20: waiting for leaderboard (log has no rows) |

**Git.** All work is committed on `exp/phase2-r15-probe-plan-20261019` in `/Users/shane/Desktop/Arena_1019_r15_probe` and pushed to origin (D26, superseding D4). The zips are git-ignored and were not pushed or uploaded.

## Files

- Rules and inventory: [wp0/RULES.md](wp0/RULES.md), [wp0/existing_packages.csv](wp0/existing_packages.csv), [wp0/candidates.md](wp0/candidates.md)
- Protocol: [wp1/protocol.json](wp1/protocol.json), [wp1/protocol.sha256](wp1/protocol.sha256), [wp1/REPORT.md](wp1/REPORT.md)
- Plan: [wp2/PROBE_PLAN.md](wp2/PROBE_PLAN.md), [wp2/ranking.csv](wp2/ranking.csv), [wp2/ORGANIZER_QUESTION.md](wp2/ORGANIZER_QUESTION.md)
- Package and hand-over: [wp3/packages.csv](wp3/packages.csv), [wp3/HANDOVER.md](wp3/HANDOVER.md)
- Decisions: [notes/DECISIONS.md](notes/DECISIONS.md)

## WP4 runs

### 2026-10-20 — waiting for leaderboard

The log has no data rows, so the status is **waiting for leaderboard**. The session goal said that results had been recorded, but `inputs/leaderboard_log.csv` did not exist before WP0 created it and is still header-only. Keep SUB as the active and last submission. Log the next board evaluation (format in [wp3/HANDOVER.md](wp3/HANDOVER.md)), then rerun WP4. Details: [wp4/REPORT.md](wp4/REPORT.md).

---

<a id="zh"></a>

# 第 15 轮——排行榜探针计划：最终报告

> [English](#en) · 中文

## 结论

1. **计划：最多一个探针，P_A3fix。** 它是加上第 12 轮锚点 3 底部修正的 SUB，只有一个常数（a_3^rel = 0.3047 Ah）。它把 CK4 下调 0.36 pp，把 CK5–CK7 下调 0.02 pp。通过验证的 zip 已准备好；没有上传任何东西。
2. **为什么是它。** 它是唯一合格的探针：
   - P_level 不合格（第 12 轮 = L3）；
   - P_drift 不合格（第 13、14 轮都是 O3）；
   - P_stress_early 被放弃（不对代理标签重新拟合就无法重建，而且不是单标量改动）。
   
   在第 6 轮的 18 个真值假设下，P_A3fix 在指标族的每个指标下都预期优于 SUB（s、nMAE、nRMSE、nMAX 的 E[Δs] 为 −0.0085 至 −0.0097）。它在 14/18 上明显胜出，最多输 +0.017。四个指标在 17/18 个假设上符号一致；在第 11 轮更宽的漂移范围下为 24/27。
3. **使用条件。** 只有在 SUB 自己的榜单值已经记录，**并且**下一次评估在已知截止时间之前至少 3 天时，才上传它。探针评估之后，除非它胜出，立即重新上传 SUB。目前截止时间未知，所以**今天的计划是：保留 SUB；先弄清截止时间。**
4. **读数意味着什么。** 胜出说明隐藏的 CK4 比 SUB 的 CK4 低 ≈ 0.18 pp 以上，这与锚点 3 的充电因未松弛的起点而偏高一致，也与真值整体偏低一致。落败说明 CK4 的真值等于或高于 SUB。在显示精度以内的差异不携带信息。
5. **排行榜观测：没有。** 本轮开始时 `inputs/leaderboard_log.csv` 不存在；现在它是一个空模板。WP4 状态见下面带日期的小节。
6. **需要记住的风险。**
   - zip 里是模板演示文稿。
   - 钩子绑定第 6 段，所以在缩减数据量运行中，它的效果取决于第 6 段保留了哪一部分。
   - 读数主要反映 CK4 的信息。这一点已披露；它只是一比特，不是重建。

## 完成的工作

| 工作包 | 结果 |
|---|---|
| WP0 | 规则审查：13 条原文规则，9 个未决事项。记录了频率矛盾：PDF 每周，指南每两周。识别出三个现有 zip（`6525edf` = 当前 SUB、`5cd305c`、`21a7a55`），都带模板演示文稿。SUB 通过 CLI 复现。 |
| WP1 | 协议已登记（sha256 `f4cf3da6…`），连同登记代码；完全复现第 6 轮的方法（7/7 测试）。 |
| WP2 | 探针向量、3 个网格 × 4 个指标的 Δs、可解读性、排名；计划 = P_A3fix；起草了给主办方的问题（未发送）。 |
| WP3 | 构建并验证了 P_A3fix 的 zip（全新 venv：验证器 PASSED；全量输出 = 预期）；SHA256 `3d792662…72e6`；写好了交接说明。 |
| WP4 | 2026-10-20：等待排行榜（记录没有数据行） |

**Git。** 所有工作都提交在 `/Users/shane/Desktop/Arena_1019_r15_probe` 的 `exp/phase2-r15-probe-plan-20261019` 分支上，并已推送到 origin（D26，取代 D4）。zip 被 git 忽略，没有推送也没有上传。

## 文件

见英文部分的链接列表。

## WP4 运行记录

### 2026-10-20 — 等待排行榜

记录里没有数据行，所以状态是**等待排行榜**。本会话目标说已记录了结果，但 `inputs/leaderboard_log.csv` 在 WP0 创建之前并不存在，现在仍然只有表头。保持 SUB 为当前有效的提交和最后一次提交。记录下一次榜单评估（格式见 [wp3/HANDOVER.md](wp3/HANDOVER.md)）之后再运行 WP4。详情见 [wp4/REPORT.md](wp4/REPORT.md)。
