# 恢复入口

项目根目录 `/Users/shane/Desktop/Arena 阶段 2 官方材料`。先读取 `research/phase2_method_exploration/START_PROMPT.md`、`notes/STATUS.md`、`notes/M9_FINDINGS.md`、`notes/FINAL_AUDIT.md`、`notes/READER_TEST.md`、`notes/EXPERIMENT_INDEX.csv`、`REPRODUCE.md` 和 `outputs/acceptance_results.json`。检查当前 Goal 状态；已有活动 Goal 时沿用，不重复创建。当前没有登记的长跑训练进程。历史所有 `runs/<run_id>/` 不可覆盖；恢复先检查产物及活跃进程，避免重跑。

最后完整检查点：M0–M10 全部冻结必做路线及已接受高优先级补充完成；D1 v1.4 退役、v1.5 全量重建和重训；3.45/3.55 V 严格终点敏感性、电流/电压/窗口消融、统一比较已完成。两候选包的干净提取 validator、各九项硬测试、独立代码/证据审查及补充审查、读者测试均完成。报告、摘要、测量计划与复现文档已写；最终独立验收 `correctness_pass=true`、`research_closed=true`，性能与官方确认仍为 false。

恢复后执行 `REPRODUCE.md` 的只读/派生核验命令；特别重跑 `scripts/m9_compile_comparison.py` 与 `scripts/m10_score_acceptance.py`，检查 `research_closed` 是否与实际交付一致。逐点比较：`outputs/predictions_long.csv`、`outputs/method_comparison.csv`。官方无标签回放：`outputs/official_predictions.csv`、`outputs/official_diagnostics.csv`。报告：`outputs/LFP_SOH_多路线设计验证与比较报告.md`。

完成判据：M0–M10 与 backlog 已接受高优先级假设均有产物/反证，严重正确性问题解决，最终读者测试记录、必交文件和独立验收一致。性能未达标允许科学负结论的研究闭环，但不能把 `performance_target_met`、独立容量确认或官方准确度改为 true。D2 未找到兼容独立四串容量标签；最小新测量见 `outputs/MEASUREMENT_PLAN.md`。
