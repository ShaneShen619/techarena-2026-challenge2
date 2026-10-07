# 恢复入口

2026-09-29：R0–R6 实验、统一表格、Markdown/Word 报告、独立审查、无上下文读者测试和候选封装均已完成。最终 Word 在 `rendered_verified/` 渲染为 13 页并逐页检查。若会话中断，不重跑训练；先检查：

1. `outputs/acceptance_results.json`；
2. `notes/INDEPENDENT_AUDIT.md` 与 `notes/READER_TEST.md`；
3. Word、`rendered_verified/` 和 `outputs/artifact_hashes.csv`；
4. `research_closed=true`、`correctness_pass=true`、`d1_target_met=false` 和 `official_capacity_accuracy_verified=false` 是否保持一致。

候选压缩包及哈希位于 `outputs/candidate_package_manifest.json`。根目录 ActiveModel 不得因恢复而自动切换。
