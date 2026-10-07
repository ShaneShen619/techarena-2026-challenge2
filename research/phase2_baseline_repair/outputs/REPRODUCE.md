# 本轮可复现命令与版本

工作根目录为 `/Users/shane/Desktop/Arena 阶段 2 官方材料`。以下命令只写 `research/phase2_baseline_repair/`；运行前确认根目录 `data/` 和历史包哈希与 `data_manifests/input_manifest.csv` 一致。官方操作原始数据和根目录活动模型只读。

```bash
research/phase2_validation/.venv/bin/python research/phase2_baseline_repair/scripts/b0_preflight.py
research/phase2_validation/.venv/bin/python research/phase2_baseline_repair/scripts/b1_audit.py
research/phase2_validation/.venv/bin/python research/phase2_baseline_repair/scripts/b1_counter.py
research/phase2_validation/.venv/bin/python research/phase2_baseline_repair/scripts/b2_compare.py
research/phase2_validation/.venv/bin/python research/phase2_baseline_repair/scripts/b3_stress.py
research/phase2_validation/.venv/bin/python research/phase2_baseline_repair/scripts/b5_package.py
research/phase2_validation/.venv/bin/python research/phase2_baseline_repair/scripts/b6_finalize.py
```

最终候选 ZIP 为 `candidates/causal_baseline_research_only_v2.zip`，SHA256 见 `runs/B5_official_candidate_20260930_v2/package_manifest.json`。解压、加入官方仅本地验证用 `sample_data/`、新建 venv 并安装 `requirements.txt` 后运行 `validate_submission.py`；再以根目录 `data/` 训练、测试 `--eval-point all`。对应干净运行在 `runs/B5_clean_extract_20260930_v2/`，八点输出在 `official_full/output.csv`，与隔离初测逐字节相同。

报告 Markdown 是内容源；DOCX 由 `scripts/b8_build_docx.py` 构建，PDF 由 Microsoft Word 导出。`rendered/word_pdf_v3/` 的三张页面 PNG 已用于逐页检查。`render_docx.py` 可运行但其非 Word 渲染器在本机丢失中文字符，因此 Word 原生 PDF 是中文排版质量的准据。PDF 已经 `pdftoppm` 渲染、逐页检查；这些 PNG 是内部 QA，不是交付正文。
