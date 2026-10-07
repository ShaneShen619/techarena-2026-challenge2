# 复现与版本

工作目录：`/Users/shane/Desktop/Arena 阶段 2 官方材料`。运行时使用 `research/phase2_validation/.venv/bin/python`，NumPy/SciPy/Pandas 已在 V0 实测。所有原始 `data/`、P1/Che/TU、官方框架和历史成果只读；新输出都在 `research/phase2_evidence_validation/`。`data_manifests/input_manifest.csv` 保存路径/哈希，`outputs/artifact_manifest.csv` 保存产物哈希。

以下是本轮的执行顺序记录。现有 run 已设 `COMPLETED`，脚本拒绝直接覆盖；**重新运行前须复制 TASK 到新的实验目录或把脚本内 `RUN` 常量改为新 run ID，并记录新代码哈希**，不得直接执行下列命令覆盖旧结果。

```bash
research/phase2_validation/.venv/bin/python research/phase2_evidence_validation/scripts/v0_preflight.py
research/phase2_validation/.venv/bin/python research/phase2_evidence_validation/scripts/v1_event_coverage.py
research/phase2_validation/.venv/bin/python -m unittest discover -s research/phase2_evidence_validation/tests -v
research/phase2_validation/.venv/bin/python research/phase2_evidence_validation/scripts/v2_r02.py
research/phase2_validation/.venv/bin/python research/phase2_evidence_validation/scripts/v2b_r02_sensitivity.py
research/phase2_validation/.venv/bin/python research/phase2_evidence_validation/scripts/v3_r05_d1.py
research/phase2_validation/.venv/bin/python research/phase2_evidence_validation/scripts/v3_r05_controls.py
research/phase2_validation/.venv/bin/python research/phase2_evidence_validation/scripts/v4_compare.py
research/phase2_validation/.venv/bin/python research/phase2_evidence_validation/scripts/v6_hard_tests.py
```

用于正式核对的完成记录是 `V1_event_coverage_20260929_v2`、`V2_R02_sensitivity_20260929_v3`、`V3_R05_D1_20260929_v1`、`V3_R05_controls_20260929_v2`、`V4_comparison_20260929_v1`、`V6_official_candidate_20260929_v1` 和 `V6_hard_tests_20260929_v1`。V1 初版计数器跨度造成脉冲 Ah 错误；V2 初版 R02 网格单位不符；V2b v2 稀疏/密集噪声未严格配对，均保留但不作最终主分析。严格原始事件重建、CK0 积分与文档渲染实测在 `runs/V0_preflight_20260929/`、`notes/READINESS.md`。

官方研究候选在 `candidates/official_gated/`：从项目根运行副本 `run_model.py --model train/test --input data`，本轮真实运行记录及输出在 V6；`validate_submission.py` 使用 `sample_data` 已通过，但该候选仅返回冻结 CK0 常数，**没有官方 CK1–CK7 准确率证据**。验证器与框架副本是隔离副本，根目录活动模型未修改。

CSV 的空值含义：`NaN`/空是未公开标签、不能测/不适用或被拒绝，不代表 0；`error_pp` 仅 D1 有真实代理目标；`cell_id` 是 P1 单芯物理实体，`pack_id` 在 D2 模板才代表四串组；`evidence_tier` 必须随每行保留。所有百分比误差单位为百分点（pp）；阿时、摄氏度、伏特与毫伏不得混用。当前参考测量温度和新组容量噪声没有实测值。
