# 当前文献调研版本

截至 2026-09-29，本目录 `outputs/LFP_SOH_第二阶段文献综述与技术路线.md/.docx`、`方法对比.csv`、`references.bib`、`NEXT_STEPS.md` 已按新一轮深度重评替换。研究源、主报告 PDF、33 项全文精读附册、原始论文指针、检索/筛选、数据资格、9 条路线卡、实验路线图、独立审查和无上下文读者测试统一在 [`../phase2_literature_reassessment/`](../phase2_literature_reassessment/)；新版验收见 [`review_acceptance.json`](../phase2_literature_reassessment/outputs/review_acceptance.json)，替换/备份的逐文件哈希见 [`replacement_manifest.json`](../phase2_literature_reassessment/outputs/replacement_manifest.json)。

本目录 `notes/` 是旧版当时的研究记录，不代表新版核验结果；旧 `START_PROMPT.md` 也保留原文供追溯，见 `HISTORICAL_ENTRY.md`。原旧版 `outputs/`、`notes/`、`START_PROMPT.md`、`ENVIRONMENT.md` 已按哈希备份到新版目录 `archive/phase2_literature_before_<timestamp>/`，准确目录和清单在 replacement manifest。

**CSV schema 已改变。**旧 `方法对比.csv` 是每篇论文一行、键为 `来源ID`；新版同名文件来自 `method_comparison.csv`，是 12 个方法族一行、键为 `family_id`。需要论文级映射时请用新版 `paper_registry.csv` 的 `paper_id` 和 `claim_evidence.csv`，不要把旧 `来源ID` 与新 `family_id` 直接联接。本项目仓库检索没有发现读取旧 CSV 的运行脚本；旧 `tmp/build_metadata.py` 只负责生成旧表，历史研究目录中引用旧表的文字保持历史语境。

新版的 R02 是优先**验证假设**，R05 是依赖新增同协议真实容量标签的备选；目前 CK1–CK7 真值隐藏，不能把新版文献完成解释为官方容量性能已证实。
