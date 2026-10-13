# 方案 2：四串动态模型与容量联合估计

2026-10-13。执行依据为上一轮方案2 Prompt，工作分支 `exp/phase2-ecm-joint-20261012`。本目录是独立研究实现。

主结果：[完整执行验证报告](完整执行验证报告.md)。当前版本拒绝容量更新；正式 `my_model/`、框架及旧研究评分保留。图、逐事件预测、容量剖面、机制与科学检查位于 `runs/v1/`。

## 本轮实际完成

75个事件原始认证，71条连续操作锚点连接；前25事件开发，后50事件冻结向前回放。实现共同容量伸缩、跨事件共享逐芯动态/起点/偏置、实际温度项与真实充电电流历史。OCV资格不足时按参考Ah位置建模，充电电压用于操作锚点/A窗口，没有伪造全天OCV/SOC模型。

完成每CK合法前缀及10种结构参数剖面，110个独立机制组合、10种子温度返回控制、模板扰动和完整均压输入补充。参考组压映射的共同位置平移细节作了数值修正，保存原源码，证明主零移位预测/容量不变。通过24项科学不变量；动态和机制/辨识门失败，独立真实容量准确率未验证。

## 环境

本次使用 `research/phase2_validation/.venv/bin/python`，Python3.12.14；依赖版本在 `requirements.txt`、运行记录在 `runs/v1/environment.json`。这是研究代码，不是比赛候选包；因为接纳门失败，没有接入正式提交。

## 复现

已有v1评分有完成标志；执行器拒绝覆盖评价和机制结果。用新run_id复现完整流程，不删除旧标记。

从项目根目录运行：

```bash
export ECM_RUN_ID=repro_20261013
export OPENBLAS_NUM_THREADS=1
research/phase2_validation/.venv/bin/python research/phase2_ecm_joint_20261012/src/audit_events.py
research/phase2_validation/.venv/bin/python research/phase2_ecm_joint_20261012/src/calibration.py
research/phase2_validation/.venv/bin/python research/phase2_ecm_joint_20261012/src/reproduce_prior.py
research/phase2_validation/.venv/bin/python research/phase2_ecm_joint_20261012/src/evaluate.py develop
research/phase2_validation/.venv/bin/python research/phase2_ecm_joint_20261012/tests/check_science.py
research/phase2_validation/.venv/bin/python research/phase2_ecm_joint_20261012/src/mechanisms.py develop
research/phase2_validation/.venv/bin/python research/phase2_ecm_joint_20261012/src/evaluate.py evaluate
research/phase2_validation/.venv/bin/python research/phase2_ecm_joint_20261012/src/checkup_diagnostics.py
research/phase2_validation/.venv/bin/python research/phase2_ecm_joint_20261012/src/mechanisms.py test
research/phase2_validation/.venv/bin/python research/phase2_ecm_joint_20261012/src/thermal_supplement.py
research/phase2_validation/.venv/bin/python research/phase2_ecm_joint_20261012/src/template_supplement.py
research/phase2_validation/.venv/bin/python research/phase2_ecm_joint_20261012/src/mean_channel_supplement.py
research/phase2_validation/.venv/bin/python research/phase2_ecm_joint_20261012/src/report.py
```

补充模块不选择主模型、不改变阈值或旧评分。首次v1的参考映射纠错记录在 `reference_projection_correction.json`，此后使用已纠正的源码；新run不需要重复执行这个历史纠错脚本。新run报告写到各自 `runs/<run_id>/完整执行验证报告.md`，保留顶层v1报告。输入缓存 `events.pkl` 可重建；它包含原始已审核波形，未纳入版本管理。

## 证据与关键文件

- `protocol.md`：科学假设/预算/停止条件；`configs/protocol.json` 为机器配置，根 `protocol.yaml` 是相同JSON内容的YAML1.2兼容快照。
- `paper_to_project.md`：Zhou/Yi原文到本项目的映射、标定缺项和数学式核对。
- `runs/v1/data_manifest.json` 为初始原始审计指纹；`data_manifest_final.json` 与首评分前 `freeze_manifest.json` 的最终配置哈希对齐。初审后、开发前补充的温度项/前静置设置见 `config_registration_history.json`，原清单保留。实际数据、论文、评分选择未改。
- `event_ledger.csv`、`stages.csv`、`charge_anchors.csv`、`counter_audit.csv`：原始事件、重复阶段边界、锚点及计数器方向核对。
- `forward_event_metrics.csv`、`forward_summary.csv`、`forward_strata.csv`：输入预算A=0Ah、B=首1Ah；这两个预算字母与健康方案A不同。
- `checkup_profiles.csv`、`profile_curves.csv`、`independent_optimizer_witnesses.json`：条件容量与替代解释，不是隐藏容量精度。
- `checkup_decisions.csv`：仅CK0有可信容量锚，之后拒绝容量更新；固定CK0接口回退独立标记。
- `mechanism_test_scores.csv`、`mechanism_test_decision.json`：测试种子与完整失败/拒绝分母。
- `thermal_return_controls.csv`、`template_supplement.csv`、`mean_channel_summary.csv`：单列补充，未用于主选择。
- `A_quality_diagnostics.csv`：过去充电窗口趋势，只作相关质量指示，不是容量衰减率标定。
- `science_checks.json`、`final_integrity.json`：数值/因果不变量和保护文件哈希检查。
- `validation_overview.png/.svg`：可导出研究图；交互展示从 `canvas_data.json` 同一结果生成。

参数中的d为参考Ah位置偏移，r0/r1为10s分辨率的表观项；在线区间条件于固定慢参数，尚未校准。四芯共享一组物理实验，不按独立实体计分。后续真实容量误差留空，不以电压小误差或模拟成功冒充容量准确率。
