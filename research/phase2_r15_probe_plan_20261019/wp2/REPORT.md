<a id="en"></a>

# WP2 — Plan

> **Language:** English · [中文](#zh)

## Conclusions

- **The plan is one probe, P_A3fix** ([PROBE_PLAN.md](PROBE_PLAN.md)). It passes every registered condition:
  - eligible, because round 12's G_a3 passed;
  - rebuilt exactly, because its CLI vector equals round 12's `SUB_A3fix`;
  - readable on G_main (17/18 hypotheses with one sign under all four metrics) and on the G_r11 gate (24/27);
  - expected to beat SUB under every metric (E[Δs] −0.0085 to −0.0097 on G_main; least favourable metric −0.0085 < 0).
- **Its risk is small and located:** the worst case is +0.017, only where the truth at CK4 is high (Δ = 0.8, f = 0). It wins clearly on 14 of 18 hypotheses.
- **Upload it only if** SUB's own board value is already known **and** the next evaluation is at least 3 days before a known deadline. Otherwise keep SUB. The deadline is currently unknown, so step 0 of the timeline is to learn it.
- **No observations yet**, so the surviving set is the full grid. A predicted-score lookup for every known zip is ready for WP4 ([predicted_scores.csv](predicted_scores.csv)).
- The organiser question is drafted, not sent ([ORGANIZER_QUESTION.md](ORGANIZER_QUESTION.md)).

## Outputs

| File | Content |
|---|---|
| [probe_soh.csv](probe_soh.csv) | SUB, EX (normaliser), P_A3fix and three descriptive vectors, all through the CLI or from their rounds' CSVs |
| [delta_s_long.csv](delta_s_long.csv) | Δs per probe × grid × hypothesis × metric (3 grids, 99 hypotheses, 4 metrics) |
| [ranking.csv](ranking.csv) | readability, detectability, E[Δs] and worst case per metric, ranking keys, chosen flag |
| [selection.json](selection.json) | hash check, rebuild check, the registered selection, descriptive counterfactual |
| [predicted_scores.csv](predicted_scores.csv) | predicted s, nMAE, nRMSE, nMAX of SUB, P_A3fix and the three existing zips per hypothesis (G_main, G_r11) |
| [PROBE_PLAN.md](PROBE_PLAN.md) | chosen probe, SOH and reading tables, timeline, end-state rule |
| [ORGANIZER_QUESTION.md](ORGANIZER_QUESTION.md) | draft question (not sent) |

## Checks

- All four registered hashes match (`wp1/protocol.sha256`) at WP2 run time.
- SUB through the CLI = `EXPECTED_SOH`. EX through the CLI: CK1..CK7 = 98.416, 98.878, 97.612, 97.634, 97.207, 95.718, 95.148 (CK1 equals round 6's EX, 98.4156).
- P_A3fix's diff against SUB is round 12's registered hook only (5 lines in `_first_full_charge`).

| Probe | Grid | One sign under 4 metrics | E[Δs] s | E[Δs] nMAE | E[Δs] nRMSE | E[Δs] nMAX | Worst | Chosen |
|---|---|---|---|---|---|---|---|---|
| P_A3fix | G_main | 0.944 | −0.0092 | −0.0085 | −0.0095 | −0.0097 | +0.0173 | **yes** |
| P_A3fix | G_r11 | 0.889 | −0.0074 | −0.0059 | −0.0072 | −0.0092 | +0.0181 | (gate passed) |
| P_drift_r6 (not eligible) | G_main | 1.000 | −0.0170 | −0.0181 | −0.0179 | −0.0151 | +0.0471 | — |
| R13 d_tail median (not eligible) | G_main | 1.000 | +0.0096 | +0.0096 | +0.0101 | +0.0090 | +0.0159 | — |
| R14 d_top median (not eligible) | G_main | 0.944 | −0.0183 | −0.0224 | −0.0203 | −0.0124 | +0.1630 | — |

---

<a id="zh"></a>

# WP2 — 计划

> [English](#en) · 中文

## 结论

- **计划是一个探针：P_A3fix**（[PROBE_PLAN.md](PROBE_PLAN.md)）。它满足所有登记条件：
  - 合格，因为第 12 轮的 G_a3 通过了；
  - 精确重建，因为它的 CLI 向量与第 12 轮的 `SUB_A3fix` 完全相同；
  - 在 G_main 上可解读（18 个假设中 17 个在四个指标下符号一致），在 G_r11 门槛上也可解读（27 个中 24 个）；
  - 在每个指标下都预期优于 SUB（G_main 上 E[Δs] 为 −0.0085 至 −0.0097；最不利指标为 −0.0085 < 0）。
- **风险小且位置明确：** 最坏情况 +0.017，只出现在 CK4 真值偏高时（Δ = 0.8，f = 0）。在 18 个假设中的 14 个上明显胜出。
- **只有在以下条件同时满足时才上传：** SUB 自己的榜单值已知，**并且**下一次评估在已知截止时间之前至少 3 天。否则保留 SUB。目前截止时间未知，所以时间线的第 0 步就是弄清截止时间。
- **目前没有观测**，存活集是整个网格。所有已知 zip 的预测得分查询表已为 WP4 准备好（[predicted_scores.csv](predicted_scores.csv)）。
- 给主办方的问题已起草，未发送（[ORGANIZER_QUESTION.md](ORGANIZER_QUESTION.md)）。

## 输出

| 文件 | 内容 |
|---|---|
| [probe_soh.csv](probe_soh.csv) | SUB、EX（归一化基准）、P_A3fix 和三个描述性向量，都来自 CLI 或各轮的 CSV |
| [delta_s_long.csv](delta_s_long.csv) | 每个探针 × 网格 × 假设 × 指标的 Δs（3 个网格、99 个假设、4 个指标） |
| [ranking.csv](ranking.csv) | 每个指标的可解读性、可检测性、E[Δs] 和最坏情况、排序键、是否选中 |
| [selection.json](selection.json) | 哈希核对、重建核对、登记的选择、描述性的反事实 |
| [predicted_scores.csv](predicted_scores.csv) | SUB、P_A3fix 和三个现有 zip 在每个假设下（G_main、G_r11）的预测 s、nMAE、nRMSE、nMAX |
| [PROBE_PLAN.md](PROBE_PLAN.md) | 选中的探针、SOH 表和解读表、时间线、最终状态规则 |
| [ORGANIZER_QUESTION.md](ORGANIZER_QUESTION.md) | 问题草稿（未发送） |

## 核对

- WP2 运行时，四个登记哈希全部一致（`wp1/protocol.sha256`）。
- 通过 CLI 的 SUB = `EXPECTED_SOH`。通过 CLI 的 EX：CK1..CK7 = 98.416、98.878、97.612、97.634、97.207、95.718、95.148（CK1 与第 6 轮的 EX 98.4156 一致）。
- P_A3fix 相对 SUB 的差异只有第 12 轮登记的钩子（`_first_full_charge` 中 5 行）。
- 各探针的数值表见英文部分。
