# 证据、核验与文档复现说明

工作根目录：`/Users/shane/Desktop/Arena 阶段 2 官方材料`。本轮目录：`research/phase2_literature_reassessment/`。使用 2026-09-29 版本 `START_PROMPT.md`。所有原始官方、P1、Che、TU 和历史结果仅只读；本轮生成物在本目录。论文源文件及对应许可/版本/哈希分别保存在 `papers/`、工作流 `source_manifest.csv` 和各张卡。未下载的 1.7/2.5 GB 包不能按已本地复现描述。

## 运行环境与可重建顺序

macOS；系统 `python3` 约 3.13、`curl`、`pdftotext`、`pdftoppm`、`pdfinfo`；Word 由本机 Microsoft Word 导出 PDF。隔离文档环境位于 `tmp/docenv/`，装 `python-docx`、`pdf2image`、Pillow、pypdf 等。详细实测与限制见 `notes/READINESS.md`。先按 `notes/SEARCH_PROTOCOL.md` 确认范围和纳排，再按 `notes/STATUS.md` 与 `RESUME.md` 恢复，不盲目重复下载。

以下命令从工作根目录运行，均只生成本轮目录中的文件：

```text
python3 research/phase2_literature_reassessment/scripts/build_paper_registry.py
python3 research/phase2_literature_reassessment/scripts/build_references.py
python3 research/phase2_literature_reassessment/scripts/merge_search_records.py
python3 research/phase2_literature_reassessment/scripts/merge_evidence.py
python3 research/phase2_literature_reassessment/scripts/build_dataset_registry.py
python3 research/phase2_literature_reassessment/scripts/build_synthesis_tables.py
python3 research/phase2_literature_reassessment/scripts/build_citation_coverage.py
python3 research/phase2_literature_reassessment/scripts/build_route_cards.py
python3 research/phase2_literature_reassessment/scripts/build_annex.py
python3 research/phase2_literature_reassessment/scripts/l0_measurement_audit.py
python3 research/phase2_literature_reassessment/scripts/l6_window_and_table_checks.py
research/phase2_literature_reassessment/tmp/docenv/bin/python research/phase2_literature_reassessment/scripts/build_word_reports.py
python3 research/phase2_literature_reassessment/scripts/build_artifact_manifest.py
```

`build_paper_registry.py` 的 Crossref 回复会缓存于 `runs/L1_crossref_20260929/`；`build_citation_coverage.py` 的 OpenAlex 12 核心前向/后向第一批元数据缓存于 `runs/L1_citation_sweep_20260929/`，离线复现只要保留缓存即可。`citation_chains.csv` 中 `metadata_candidate_only` 仅是引文候选，不能用作全文方法证据；`source_reference_verified` 才是人工核原文参考文献。大范围 OpenAlex 原始页存于 `runs/L1_openalex_20260929/`。单个搜索 API 的首 100 条前向引用不代表完整引用网络。33 项深读卡来自正式/作者全文，5 个重复工作流版本不计独立研究。

## Word 和 PDF 渲染

文档构建源码为 `scripts/build_word_reports.py`，直接从最终 Markdown 生成两个 Word。Word 技能的 `render_docx.py` 在本机因未安装 LibreOffice `soffice` 无法完成；实测替代路径是本机 Microsoft Word 的真实排版导出，然后用 Poppler 把**每页**转 PNG，保存在 `rendered/`，并逐页检查中文、符号、标题、页眉页码、裁切、孤页及表格。主 PDF 与主 Word 的内容来自同一个 Markdown 源，附册 QA PDF 仅供 Word 视觉核查。导出脚本 `scripts/export_word_pdf.applescript`；主 PDF 在 `outputs/`，附册临时 QA PDF 在 `rendered/`。若没有 Word，请安装 LibreOffice 并使用技能渲染器，核对两种引擎的分页差异后再交付。

## 输入、统计及数据契约

本轮实际轻量重算：`runs/L0_measurement_20260929/result.json`（CK0 计量、时间戳/组压通道）和 `runs/L6_window_table_20260929/result.json`（26 小窗的假设 ±2 mV 敏感性、Yagci 表 3 算术），以及 `notes/workstreams/B_R3_cluster_audit.json`（37 组脉冲事件聚类）。它们是**本地检查**，不是官方 CK1–CK7 容量实验。脚本/运行产物应按运行目录的源哈希、参数和结果对读；任何手工修改输入后应开新 run_id，不覆盖既有记录。D1 旧结果只读，核对位置见 `PROJECT_EVIDENCE_AUDIT.md`。

CSV 均 UTF-8（无 BOM），首行为列名，缺失值用空字符串；`paper_id` 对应 `paper_registry.csv` 唯一行，`version_duplicate_of` 指向规范研究；论文 DOI 去重但作者稿/正式版及冲突保留卡。`claim_evidence.csv` 的特殊 ID `OFFICIAL_CONSTRAINTS`、`B_R3_cluster_audit` 指本地或官方一手证据，非论文；`research_questions.csv` 和 `method_comparison.csv` 中 `C_DATA_QUALIFICATION` 指本轮数据资格说明。`search_queries.csv` 和 `screening.csv` 按**访问/发现记录**保留多入口重复，不能把行数称独立论文数。`citation_chains.csv` 的未读元数据候选没有页码。`dataset_registry.csv` 的资格/许可对特定版本有效，下载状态必须原样转述。缺页码的 HTML 用节、式、表号和来源 URL 定位；不编造分页。

`review_acceptance.json` 记录独立证据审查、无聊天上下文读者测试、视觉 QA、旧目录替换与性能验证分别是否完成。`artifact_manifest.csv` 按 SHA256 列出正式输出，`replacement_manifest.json` 另跟踪旧文献成果的逐文件备份/替换；两个 manifest 的含义不同。若外部修改了旧文件，替换脚本须检测哈希冲突并停在未完成状态，不强行覆盖。

2026-09-29 最终验收后，`scripts/replace_old_review.py prepare` 将旧 `outputs/`、`notes/`、`START_PROMPT.md`、`ENVIRONMENT.md` 的 12 个文件备份到 `archive/phase2_literature_before_20260929T230323/`，逐文件核 SHA256；`apply` 以临时文件和 `os.replace` 完成 7 个入口映射，并逐文件/整批复核新哈希。准确映射及回滚前置条件见 `outputs/replacement_manifest.json`；旧 `notes/` 和旧启动原文未修改。旧 `方法对比.csv` 的 schema 已从按论文 `来源ID` 行变成按 12 方法族 `family_id` 行，论文级映射请查新 `paper_registry.csv` 与 `claim_evidence.csv`；旧目录的 `CURRENT_REVIEW.md` 也注明这一点。`rollback` 仅在目标仍等于本次新哈希时才恢复旧备份。
