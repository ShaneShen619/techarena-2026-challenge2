<a id="en"></a>

# Round 6 — Hypothesis-robust selection, fusion, truth-oriented corrections, open-data prior

> **Language:** English · [中文](#zh)

Branch `exp/phase2-r6-robust-20261016`. Seven work packages (WP0–WP6) re-baselined everything against the submitted model SUB (V2 + √t) and asked which model is safest when the hidden labels may differ from our proxies.

**Result.** Keep SUB: it has the lowest maximum regret over 18 label hypotheses, and no alternative passed the registered gates. The open question is the labels, not the model, so WP6 proposes leaderboard probes, ε drift first. Read [FINAL_REPORT.md](FINAL_REPORT.md).

| Path | Content |
|---|---|
| [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md) | execution brief |
| [FINAL_REPORT.md](FINAL_REPORT.md) | final report |
| [notes/](notes/) | STATUS and DECISIONS |
| [sources/](sources/) | read-only copies from the submission branch (`21a7a55`) with SHA-256 |
| [src/](src/) | round-5C modules (copied) with the round-6 extensions (predictive SD, path rule) |
| [wp0/](wp0/) … [wp6/](wp6/) | one directory per work package: protocol, code, outputs, report |
| [report_material/](report_material/) | bilingual drafts for REPORT.md and the presentation, figure, code audit |

---

<a id="zh"></a>

# 第六轮——多假设稳健选择、融合、真值导向修正、开放数据先验

> **语言：** [English](#en) · 中文

分支 `exp/phase2-r6-robust-20261016`。七个工作包（WP0–WP6）以当前提交的模型 SUB（V2 + √t）为新基准，重新评估了所有方案，并回答一个问题：如果隐藏标签与我们的代理不同，哪个模型最稳妥？

**结果。** 保留 SUB：它在 18 种标签假设下最大后悔值最低，且没有替代方案通过登记的门槛。悬而未决的是标签而不是模型，所以 WP6 提出了排行榜探测计划，先探测 ε 漂移。请读 [FINAL_REPORT.md](FINAL_REPORT.md)。

| 路径 | 内容 |
|---|---|
| [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md) | 执行任务书 |
| [FINAL_REPORT.md](FINAL_REPORT.md) | 最终报告 |
| [notes/](notes/) | STATUS 与 DECISIONS |
| [sources/](sources/) | 从提交分支（`21a7a55`）只读复制的文件，附 SHA-256 |
| [src/](src/) | 复制的第五轮 C 模块，加上第六轮的扩展（预测标准差、路径规则） |
| [wp0/](wp0/) … [wp6/](wp6/) | 每个工作包一个目录：协议、代码、输出、报告 |
| [report_material/](report_material/) | 供 REPORT.md 和演示使用的双语草稿、图、代码审计 |
