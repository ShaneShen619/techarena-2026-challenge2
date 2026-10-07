# 复现与独立核验

在项目根目录 `/Users/shane/Desktop/Arena 阶段 2 官方材料` 运行。既有 `runs/` 使用不可覆盖 run_id；以下先给**不会重训或覆盖冻结模型**的核验命令。完整重建需在具有相同原始输入、尚无对应 `runs/<run_id>/` 的独立项目副本执行，不要删除本目录中的旧运行。

```bash
bash research/phase2_validation/run_python.sh research/phase2_method_exploration/tests/test_visibility_boundary.py
bash research/phase2_validation/run_python.sh research/phase2_method_exploration/tests/test_visibility_v15.py
bash research/phase2_validation/run_python.sh research/phase2_method_exploration/tests/test_m4_audit.py
bash research/phase2_validation/run_python.sh research/phase2_method_exploration/tests/test_m5_pack.py
bash research/phase2_validation/run_python.sh research/phase2_method_exploration/tests/test_m5_outputs.py
bash research/phase2_validation/run_python.sh research/phase2_method_exploration/tests/test_m6_audit.py
bash research/phase2_validation/run_python.sh research/phase2_method_exploration/tests/test_endpoint_v15.py
bash research/phase2_validation/run_python.sh research/phase2_method_exploration/scripts/m9_compile_comparison.py
bash research/phase2_validation/run_python.sh research/phase2_method_exploration/scripts/m10_score_acceptance.py
```

`m9_compile_comparison.py` 会重写两份派生比较 CSV，不更改实验逐点文件；`m10_score_acceptance.py` 重新读取 SHA256 锁定的 P1 面板、验证每方法 180 个唯一目标、运行六个本地审计测试并重写验收结果。输入面板 SHA256 应为 `7188b662900f84312292a7062d6023e5eeb4f2e32798b6d61a3547ed40cdc59c`。严格 v1.5 模型输入清单和原生序列 SHA256 在 `runs/M9_D1_v15_inputs_v1/summary.json`；全原始扫描与前缀停止的相等性在 `runs/M9_prefix_stop_replay_v2/summary.json`。某实验的代码、配置、输入哈希与逐点产物查 `notes/EXPERIMENT_INDEX.csv`。

完整重建的顺序：M0 数据哈希/旧面板复现及冒烟 → M1 标准脉冲认证与未来电压 → M2–M6 参照各 `scripts/m*_register.py` 与模块发现文件 → M7 线性/TCN 与 M8 融合 → D1 v1.5 前缀扫描与样本重建 → v1.5 基线/TCN/消融/融合 → M9 官方逐前缀回放、统一编译 → M10 两包硬测试、干净提取验证、独立验收。v1.5 原始重建依次运行 `m9_shallow_prefix_eligibility_audit.py`、`m9_build_d1_v15_manifest.py`、`m9_crop_d1_v15.py`、`m9_d1_v15_target_map.py`，再运行独立 `m9_prefix_stop_replay_v2.py` 检查与冻结 1,080 视图相等。**基准生成脚本仍调用完整事件提取器；它的选样已由独立前缀停止扫描证明等价，但真正在线部署须直接采用前缀停止逻辑。**

3.45/3.55 V 的严格前缀终点敏感性可在**没有相同 run_id 的独立副本**中按以下精确命令重建；当前项目已有这些不可覆盖的运行目录。它们分别从 P1 原始行识别各阈值首次越线，再以相同 20 Ah 持续历史和整芯嵌套验证训练五种基线。输出逐点文件为 `runs/M9_D1_v15_M2_3p45_20Ah_persistent_v1/predictions.csv` 与 `runs/M9_D1_v15_M2_3p55_20Ah_persistent_v1/predictions.csv`，输入清单与资格审计在对应的 `M9_D1_v15_endpoint_3p45_v1` 和 `M9_D1_v15_endpoint_3p55_v1` 目录。

```bash
bash research/phase2_validation/run_python.sh research/phase2_method_exploration/scripts/m9_endpoint_sensitivity_v15.py --endpoint 3p45
bash research/phase2_validation/run_python.sh research/phase2_method_exploration/scripts/m9_d1_v15_endpoint_baselines.py --endpoint 3p45 --budget 20 --mode persistent
bash research/phase2_validation/run_python.sh research/phase2_method_exploration/scripts/m9_d1_v15_endpoint_signal_ablation.py --endpoint 3p45
bash research/phase2_validation/run_python.sh research/phase2_method_exploration/scripts/m9_endpoint_sensitivity_v15.py --endpoint 3p55
bash research/phase2_validation/run_python.sh research/phase2_method_exploration/scripts/m9_d1_v15_endpoint_baselines.py --endpoint 3p55 --budget 20 --mode persistent
bash research/phase2_validation/run_python.sh research/phase2_method_exploration/scripts/m9_d1_v15_endpoint_signal_ablation.py --endpoint 3p55
bash research/phase2_validation/run_python.sh research/phase2_method_exploration/tests/test_endpoint_v15.py
```

TCN/纯标量实验依赖本机可导入 PyTorch 的 Python 3.13，运行时使用 `PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 <脚本>`；验证脚本和低维模型可使用 `research/phase2_validation/.venv` 中的 Python 3.12。所有三种子为 20260928、20260929、20260930。若使用另一环境，先在独立副本记录包版本/CPU 与随机种子并比对逐点结果，不把运行时浮点差异冒称新的确认集。

官方接口验证收据在 `runs/M10_clean_extract_v1/{ck0_hold,exploratory_fallback}/validation_report.txt`，每包九项硬测试结果在 `runs/M10_*_hard_tests_v2/summary.json`。这些证据只覆盖可运行、因果、数值和格式；CK1–CK7 真值隐藏，任何复现者都不能从本地文件计算官方容量 MAE。D1 v1.4 的历史分数在汇总中专门标为退役层级，不可作为 v1.5 严格主结论。
