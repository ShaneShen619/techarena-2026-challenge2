# Word/PDF 最终视觉验收（2026-09-29）

两个 `.docx` 都由最终 Markdown 经 `scripts/build_word_reports.py` 构建，再由本机 Microsoft Word 实际排版导出 PDF。技能提供的 `render_docx.py` 已尝试，但本机缺少 LibreOffice `soffice`，故采用经端到端验证的 Word 导出与 Poppler 逐页 PNG 路径；命令和限制见 `outputs/REPRODUCE.md`、`notes/READINESS.md`。

- 主报告：12 页，`outputs/LFP_SOH_第二阶段文献综述与技术路线_深度重评.pdf`，逐页图在 `rendered/main_pages/`。
- 附册：31 页，Word 排版 QA PDF 在 `rendered/LFP_SOH_核心论文精读与证据附册_QA.pdf`，逐页图在 `rendered/annex_pages/`。QA PDF 不作为正式交付项。

主报告 1–12 页、附册 1–31 页都按原分辨率逐页人工查看；检查标题层级、中文和数学符号、页眉页码、行距、跨页、裁切、重叠与空白页。末页为正常收尾，没有纯空白页。最后修订的 Bilfinger 卡出现在附册第 29 页，已再次查看；其措辞明确区分 BMS 版本更新后的观测与未证实因果。两份 PDF 还做了自动文本检查：每页可抽取超过 100 个字符，没有 U+FFFD 替换字符或 U+25A0 方块；主 PDF 有 CK0、R02、R05、Bilfinger 等决策锚点，附册有 33 项卡片且末项 Deng 可定位。Word 与 Markdown 共享构建源；Word 的引用链接转为可读 URL 文字。

唯一渲染环境限制是 LibreOffice 路径不可用；本机 Word 导出的实际交付 PDF 和附册 QA PDF 均已完整验收。未将视觉验收或全文精读称为官方隐藏容量性能验证。
