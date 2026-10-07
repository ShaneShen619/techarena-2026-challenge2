# 方案 A 温度改进实验复现

工作目录为 `/Users/shane/Desktop/Arena 阶段 2 官方材料`。所有 Python 命令使用 `bash research/phase2_validation/run_python.sh`。结果属于六个 P1 单芯的 180 点开发面板；官方 CK1–CK7 容量真值隐藏，故官方输出只有无标签诊断。

## 输入与冻结证据

- `dataset original/`：六芯原始时序；`research/phase2_validation/preflight/downloaded_data/phase1_label_inventory.csv`：预先审计的放电标签表。
- `/Users/shane/Desktop/项目/Current State_Challenge1/framework/data.py`：P1 标签规则，只读。
- `outputs/panel_manifest.json` 和 `outputs/panel_main.csv`：每芯 30 个固定目标，面板 SHA256 `7188b662900f84312292a7062d6023e5eeb4f2e32798b6d61a3547ed40cdc59c`。
- `runs/M7_frozen_manifest.json`：原始 P1 文件、标签规则、面板、特征配置、严格前缀事件白名单、训练脚本、折模型及交付适配器的哈希。原始数据和第一阶段源码不被修改。

## 依赖顺序

下列命令从工作目录运行；各模块内部清单和结果保留在 `runs/`。完整重跑 M2/M4 和 180 次在线适配器回放需要读取较大的原始数据，避免与其他大任务并发。

```bash
bash research/phase2_validation/run_python.sh research/phase2_temperature_improvement/scripts/build_panel.py
bash research/phase2_validation/run_python.sh research/phase2_temperature_improvement/scripts/run_m1_thermal.py
bash research/phase2_validation/run_python.sh research/phase2_temperature_improvement/scripts/run_m2_repaired.py --method A_bugfix
bash research/phase2_validation/run_python.sh research/phase2_temperature_improvement/scripts/build_m4_features.py
bash research/phase2_validation/run_python.sh research/phase2_temperature_improvement/scripts/build_m4_throughput.py
bash research/phase2_validation/run_python.sh research/phase2_temperature_improvement/scripts/run_m4_fixed_baseline.py
bash research/phase2_validation/run_python.sh research/phase2_temperature_improvement/scripts/run_m4_inner_age.py
bash research/phase2_validation/run_python.sh research/phase2_temperature_improvement/scripts/run_m4_inner_inner_age.py
bash research/phase2_validation/run_python.sh research/phase2_temperature_improvement/scripts/export_m4_models.py
bash research/phase2_validation/run_python.sh research/phase2_temperature_improvement/scripts/register_final_candidate.py
bash research/phase2_validation/run_python.sh research/phase2_temperature_improvement/scripts/run_m6_event_stress.py
bash research/phase2_validation/run_python.sh research/phase2_temperature_improvement/scripts/run_m6_mechanism.py
bash research/phase2_validation/run_python.sh research/phase2_temperature_improvement/scripts/run_m6_curve_variation.py
bash research/phase2_validation/run_python.sh research/phase2_temperature_improvement/scripts/replay_online_final.py
bash research/phase2_validation/run_python.sh research/phase2_temperature_improvement/scripts/run_hard_tests.py
bash research/phase2_validation/run_python.sh research/phase2_temperature_improvement/scripts/freeze_m7.py
bash research/phase2_validation/run_python.sh research/phase2_temperature_improvement/scripts/recompute_m7_independent.py
bash research/phase2_validation/run_python.sh research/phase2_temperature_improvement/scripts/check_acceptance.py --require-pass
```

预先固定和辅助的 M0、M3、消融实验路径见 `notes/EXPERIMENT_INDEX.csv`。`outputs/predictions.csv` 含五个固定基线及最终方案全部 180 点；不可只重跑最后模型后把旧分母或旧折结果随意替换。要获得完全同一结果，请保持面板、版本和所有冻结输入不变；变动时建立新运行版本。

硬传感器压力以 `scripts/run_m6_event_stress.py` 的 `bias_+1C` 与 `bias_-1C` 为准。它分别从空状态重新回放目标芯截至截止时的事件温度；`runs/M6_temperature_stress_v1/` 中 ±0.5、±2、±5°C 的固定特征代数诊断不属于硬验收。`outputs/temperature_stress_evidence.csv` 是各场景重新生成的事件证据。

## 候选包与验证

`outputs/multi_temp_candidate.zip` 是无原始数据的源码包；哈希和成员见 `outputs/candidate_package_manifest.json`。将它解压到空目录，单独放入官方 `sample_data/`，运行 `validate_submission.py`；此次空目录提取测试收据为 `outputs/clean_package_validation.txt`。对官方完整数据的诊断为 `outputs/official_diagnostics.csv`。不得用 CK1–CK7 的预测输出计算 MAE，因为真值不公开。

`outputs/M7_independent_recompute.json` 用独立矩阵算术验证冻结特征和系数，并核对原始输入哈希；`runs/M7_online_replay_v1/predictions.csv` 从原始时序调用交付适配器完成 180 点端到端重放。前者并非第二套独立编写的特征提取或独立重训，完整技术边界见报告第 8 节。
