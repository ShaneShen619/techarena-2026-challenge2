# 恢复说明

先读 `notes/STATUS.md`、`notes/EXPERIMENT_INDEX.csv` 与各 run 的 `COMPLETED` 标记；核代码/配置/输入 SHA256，不覆盖已完成 run。未完成 run 可在确认无并发进程后按日志恢复。研究结论只引用已完成且未被 supersede 的 run；CK1–CK7 真容量留空。
# 恢复检查点

当前最可信已完成 run：B0 `B0_preflight_20260930_v1`、`B0_example_20260930_v1`、`B0_ck0_constant_20260930_v1`；B1 `B1_event_causality_20260930_v1` 和 `outputs/counter_audit.csv`；B2 `B2_candidate_comparison_20260930_v4`；B3 `B3_mechanism_stress_20260930_v3`；B5 `B5_clean_extract_20260930_v2`；B7 `notes/INDEPENDENT_AUDIT.md`。B2 v1–v3、B5 v1 是历史/失败或被后续源码覆盖，不作最终结论。

已冻结配置：`configs/protocol.json`、`acceptance.json`、`event_rules.json` 和观察后 `event_rules_v2.json`。最终研究候选为 `candidates/causal_baseline_research_only_v2.zip`，不含数据，`ActiveModel` 默认 `gate='none'`。根目录官方文件与活动模型未改，未提交。

本轮 B8 已完成：独立陌生读者 12 问全答，三页 Word 原生 PDF 逐页检查，`acceptance_results.json` 与 `artifact_manifest.csv` 最终封存。若下一轮要做容量验证，必须先新 D2 或合法官方真值并按 `outputs/NEXT_STEPS.md` 封存物理组。没有新标签时不用继续同一组无真值曲线上的阈值搜索。
