# 复现顺序与封存规则

根目录 `/Users/shane/Desktop/Arena 阶段 2 官方材料`。本轮仅在 `research/phase2_capacity_validation/` 写入。原始官方包、旧研究和桌面相关项目只读。推荐 Python `research/phase2_validation/.venv/bin/python`，3.12.14、pandas 2.2.3、numpy 2.3.5；工作簿解析用系统 `python3` + openpyxl 3.1.5。完整输入与代码 SHA 在 `manifests/input_code_config_sha256.csv`，源 ZIP SHA 在 `download_log.csv`。

新环境中按版本脚本运行：

```bash
research/phase2_validation/.venv/bin/python research/phase2_capacity_validation/scripts/n0_causality.py
research/phase2_validation/.venv/bin/python research/phase2_capacity_validation/scripts/n5_causality_candidate.py
research/phase2_validation/.venv/bin/python research/phase2_capacity_validation/scripts/n0_hit_audit.py
research/phase2_validation/.venv/bin/python research/phase2_capacity_validation/scripts/n3_n4_mechanisms.py
research/phase2_validation/.venv/bin/python -m unittest discover -s research/phase2_capacity_validation/tests -v
```

`capacity_pipeline.py` 的无敏感读取阶段可重跑：`inventory`、`qualify`、`extract`、`predict`、`report`。现存 `configs/freeze_manifest.json` 已冻结、`sealed/HOLDOUT_SCORED_ONCE` 已写入，因此再次调用 `freeze`/`score` 应失败；这是防止利用封存集重复调参的预期行为。要从零复现一次完整流程，应复制 TASK 到新版本独立目录，使用同一源 ZIP 与预注册分割，先运行 `n2_stage_transfer.py`、`n2_transfer_dev.py`，审查 v2 排除记录并固定配置，最后依序 `inventory → qualify → freeze → extract → predict → score → report`；绝不能在同一封存组上根据已见结果改阈值后再称独立验证。

`outputs/pipeline_result.json` 旧字段 `official_hidden_targets=35` 实为预测行数，已保留原件并由 `pipeline_result_v2.json` 更正为 7 个隐藏 CK 与 35 个预测行。私有标签清单 SHA 为事后独立追溯，不伪称已写入原冻结，见 `sealed/provenance_postscore.json` 与 `notes/INDEPENDENT_AUDIT.md`。

Word 内容源是 `outputs/LFP_SOH_真实容量验证与测量计划.md`，`scripts/n9_build_docx.py` 生成 DOCX；PDF 用 Microsoft Word 原生导出，因为当前 `render_docx.py` 启动时缺 `pdf2image` 且旧轮次曾观察到非 Word 渲染中文缺字。最终 PDF 用 Poppler 渲染 PNG 逐页查看，图像是质量检查中间物。
