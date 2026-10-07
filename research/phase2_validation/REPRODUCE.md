# 双路线复现入口

项目根目录：`/Users/shane/Desktop/Arena 阶段 2 官方材料`。原始 `data/`、`dataset original/`、`Che-Dataset3.mat`、`TU Darmstadt/` 保持原位、只读。运行记录均在 `research/phase2_validation/`。输入 SHA256 索引见 `preflight/original_sha256.json` 与 `preflight/downloaded_data/audit_report.json`；每个脚本源文件可重新哈希。Python 3.12 macOS ARM64 的离线 wheels 在 `wheelhouse/`，锁版本在 `requirements.lock.txt`。其它平台按声明版本安装，不把这些 macOS wheel 当 Linux 构建。

先执行：

```bash
bash research/phase2_validation/run_preflight.sh
bash research/phase2_validation/run_python.sh -m pytest research/phase2_validation/tests -q
```

分别在两个候选副本运行官方接口，避免同名 `my_model` 导入污染：

```bash
bash research/phase2_validation/run_python.sh research/phase2_validation/candidates/route_a/validate_submission.py
bash research/phase2_validation/run_python.sh research/phase2_validation/candidates/route_b/validate_submission.py
bash research/phase2_validation/run_python.sh research/phase2_validation/candidates/route_a/run_model.py --model train --input data --output-dir research/phase2_validation/runs/A_official_v4
bash research/phase2_validation/run_python.sh research/phase2_validation/candidates/route_a/run_model.py --model test --input data --state-dir research/phase2_validation/runs/A_official_v4 --output-dir research/phase2_validation/runs/A_official_v4 --eval-point all
bash research/phase2_validation/run_python.sh research/phase2_validation/candidates/route_b/run_model.py --model train --input data --output-dir research/phase2_validation/runs/B_official_v3
bash research/phase2_validation/run_python.sh research/phase2_validation/candidates/route_b/run_model.py --model test --input data --state-dir research/phase2_validation/runs/B_official_v3 --output-dir research/phase2_validation/runs/B_official_v3 --eval-point all
```

实验与汇总的依赖顺序：

```bash
bash research/phase2_validation/run_python.sh research/phase2_validation/scripts/run_phase1_sixfold.py
bash research/phase2_validation/run_python.sh research/phase2_validation/scripts/run_synthetic.py
bash research/phase2_validation/run_python.sh research/phase2_validation/scripts/run_stress.py
bash research/phase2_validation/run_python.sh research/phase2_validation/scripts/run_ablations.py
bash research/phase2_validation/run_python.sh research/phase2_validation/scripts/run_phase1_a_ablations.py
bash research/phase2_validation/run_python.sh research/phase2_validation/scripts/che_descriptive.py
bash research/phase2_validation/run_python.sh research/phase2_validation/scripts/tu_field_diagnostics.py
bash research/phase2_validation/run_python.sh research/phase2_validation/scripts/summarize_results.py
bash research/phase2_validation/run_python.sh research/phase2_validation/scripts/diagnose_official.py
bash research/phase2_validation/run_python.sh research/phase2_validation/scripts/build_official_outputs.py
bash research/phase2_validation/run_python.sh research/phase2_validation/scripts/plot_results.py
```

部分脚本会覆盖相同的汇总 CSV；首次版本的失败记录保留在 `runs/A_official/` 与 `runs/phase1_sixfold_v1/`。`run_phase1_sixfold.py` 当前 run ID v2，已使用同一六芯开发集，不能称新盲测。若单独重跑官方诊断，请先按上面顺序刷新候选 pickle，避免加载旧模型属性。Che 和 TU 脚本只读原始文件。TU 读取完整文件做窗口定位，但最多保留每系统早/中/晚各 10 万行用于深入诊断。

Word 报告由 `scripts/build_report_docx.py` 从同名 Markdown 与图生成，并用 documents 技能的 `render_docx.py` 转 PNG 逐页检查；最终渲染目录位于 `runs/report_render_v6/`。科学结论以 CSV 与审计说明为准，不凭 Word 图中的像素反推数值。

最终独立环境验收在本机重新建了 `preflight/final_clean_venv`，只从 `wheelhouse/` 的 Python 3.12 macOS ARM64 wheels 安装 `requirements.lock.txt`；`pip check` 与 12 项 pytest 均通过。可复现命令如下（先 `cd` 到项目根目录）：

```bash
/Users/shane/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m venv research/phase2_validation/preflight/final_clean_venv
research/phase2_validation/preflight/final_clean_venv/bin/python -m pip install --no-index --find-links research/phase2_validation/wheelhouse -r research/phase2_validation/requirements.lock.txt
research/phase2_validation/preflight/final_clean_venv/bin/python -m pip check
research/phase2_validation/preflight/final_clean_venv/bin/python -m pytest research/phase2_validation/tests -q
research/phase2_validation/preflight/final_clean_venv/bin/python research/phase2_validation/scripts/package_check.py
research/phase2_validation/preflight/final_clean_venv/bin/python research/phase2_validation/scripts/final_audit.py
```

`package_check.py` 把两套候选分别打成不含官方 `data/` 的 ZIP，解包至 `runs/package_check/`，在同一新环境中运行**解包内**官方样例验证器；输出日志在该目录。这验证的是本机打包/依赖/入口完整性，不代表 Linux 评分机已执行。`final_audit.py` 重新核对官方源文件 SHA256、Che/TU/第一阶段原始文件的大小和修改时间、候选框架字节一致性、逐条指标、隐藏真值留空、B 拒绝漏斗、Word/PDF 页面数，结果为 `notes/final_audit.json`。

新增 B 审计漏斗通过 `bash research/phase2_validation/run_python.sh research/phase2_validation/scripts/build_b_funnel.py` 重建，按 CK 同时给累计和新增事件数。图在重建压力测试后用 `scripts/plot_results.py` 重画。Word 最终版使用项目绝对 `FONTCONFIG_FILE` 和 documents renderer 生成于 `runs/report_render_v6/`，该目录九张 `page-*.png` 已逐页目检；真正交付的可编辑文件在 `outputs/`，PDF 只是版式校验中间件。
