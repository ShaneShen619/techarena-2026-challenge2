# 深度文献重调研状态

2026-09-29 版本已完成研究、写作、独立源证据审查、反方修订、无聊天上下文读者测试、两份 Word 逐页视觉检查和旧入口备份替换。Goal 可在最终一致性复核后标记完成；这表示**文献研究任务完成**，不表示模型容量性能达标。

证据规模：预冻结 L1 检索协议；广泛检索 OpenAlex 12 式 117 去重元数据候选，外加定向和前后向发现；最终 33 项不同研究的可读全文深卡、5 张版本/工作流重复卡不计独立研究，12 方法族、8 研究问题、9 路线、12 数据集资格、48 主张证据、16 冲突。两轮改变检索策略后的前向候选核验没有发现会推翻路线排序的同协议四串单锚点独立容量验证，受限全文和非穷尽范围如实记录。轻量检查为 CK0 计量、小窗偏移敏感性、R3 组事件聚类及若干作者代码/数据静态审查；无新大规模训练或硬件容量采集。

主报告 Word/PDF 12 页、附册 Word 31 页；`notes/DOCX_VISUAL_QA.md` 记录每页检查和 LibreOffice 缺失的 Word 导出替代路径。独立审查及修订见 `notes/INDEPENDENT_EVIDENCE_AUDIT*.md`、`notes/AUDIT_CORRECTIONS.md`；12 问读者测试和复测见 `notes/READER_TEST.md`。验收状态在 `outputs/review_acceptance.json`。

R02 为优先验证假设，R05 为依赖新 D2 容量标签的不同风险备选，R01 为保守回退。`outputs/EXPERIMENT_ROADMAP.md` 现给 E1 配置/冻结契约及 D2 采集模板。CK1–CK7 真值隐藏；D2 独立四串同协议容量标签、仪表重复性及数值盲验阈值尚未取得，所以 `capacity_performance_newly_verified=false`。

旧 `research/phase2_literature/` 的 12 文件原始清单已备份并核哈希到 `archive/phase2_literature_before_20260929T230323/`；7 个正式入口逐项原子替换并做整批哈希复核。旧 notes 与原启动文件保留历史原文。`outputs/replacement_manifest.json` 为准确映射和恢复入口。后续若出现真正同协议 D2 或可改变判断的新全文证据，应开新研究/实验 run_id 继续，不改写本轮冻结记录。
