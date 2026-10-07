# 复现说明

本文件复现的是本轮汇总与冻结实验；R4 明确是对上一轮锁定产物的哈希复核和重汇总，不是从原始数据重新训练或重新模拟。建议先核对环境，再在项目的隔离副本中运行。当前验证环境为：

- R1：Python 3.13.0、Torch 2.12.1、NumPy 2.4.2、pandas 3.0.0，CPU 后端；
- 其余脚本：`research/phase2_validation/.venv`，Python 3.12.14、NumPy 2.3.5、pandas 2.2.3、SciPy 1.18.1；
- validator 的依赖以各候选目录中的 `requirements.txt` 为准。

现有虚拟环境已可运行；若在新机器从零搭建，应使用相同 Python 小版本并按上述版本锁定依赖。不要在当前冻结目录中升级依赖后原位覆盖结果。

从项目根目录运行：

```bash
cd "/Users/shane/Desktop/Arena 阶段 2 官方材料"
```

R0 与历史基线复核：

```bash
research/phase2_validation/.venv/bin/python research/phase2_next_round/scripts/r0_inventory.py
research/phase2_validation/.venv/bin/python research/phase2_next_round/scripts/r0_smoke.py
research/phase2_validation/.venv/bin/python research/phase2_next_round/scripts/r0_recompute.py
```

R1 使用系统 Python 3.13 的 Torch CPU 后端。每个条件有逐芯/种子检查点，同一命令恢复时会跳过已完成组合：

```bash
OMP_NUM_THREADS=2 python3 research/phase2_next_round/scripts/r1_paired_tcn.py --condition full
OMP_NUM_THREADS=2 python3 research/phase2_next_round/scripts/r1_paired_tcn.py --condition no_voltage
OMP_NUM_THREADS=2 python3 research/phase2_next_round/scripts/r1_paired_tcn.py --condition meta_only
OMP_NUM_THREADS=2 python3 research/phase2_next_round/scripts/r1_paired_tcn.py --condition no_temperature
OMP_NUM_THREADS=2 python3 research/phase2_next_round/scripts/r1_paired_tcn.py --condition no_temperature_strict
OMP_NUM_THREADS=2 python3 research/phase2_next_round/scripts/r1_paired_tcn.py --condition full_tail_weight2
research/phase2_validation/.venv/bin/python research/phase2_next_round/scripts/r1_compile.py
```

其中 `no_temperature` 只清零序列温度，是审查后保留的失败记录；`no_temperature_strict` 同时清零序列温度与元数据列 `current_temp_C`，生成报告中的“严格去温度”。R1 的 `R1_paired_TCN_<condition>_v1` 目录支持逐芯、逐种子续跑：已有预测组合会跳过；它不会删除已有模型或逐点结果。

R2–R5：

```bash
research/phase2_validation/.venv/bin/python research/phase2_next_round/scripts/r2_counterfactual_reanalysis.py
research/phase2_validation/.venv/bin/python research/phase2_next_round/scripts/r3_pulse_reanalysis.py
research/phase2_validation/.venv/bin/python research/phase2_next_round/scripts/r4_state_pack_decision.py
research/phase2_validation/.venv/bin/python research/phase2_next_round/scripts/r5_validate_measurement.py --self-test
research/phase2_validation/.venv/bin/python research/phase2_next_round/scripts/r5_sample_size_sensitivity.py
```

R6：

```bash
research/phase2_validation/.venv/bin/python research/phase2_next_round/scripts/r6_candidate_hard_tests.py --candidate ck0_hold
research/phase2_validation/.venv/bin/python research/phase2_next_round/scripts/r6_candidate_hard_tests.py --candidate exploratory_fallback
research/phase2_validation/.venv/bin/python research/phase2_next_round/scripts/r6_official_replay.py --candidate ck0_hold
research/phase2_validation/.venv/bin/python research/phase2_next_round/scripts/r6_official_replay.py --candidate exploratory_fallback
research/phase2_validation/.venv/bin/python research/phase2_next_round/scripts/r6_compile.py
research/phase2_validation/.venv/bin/python research/phase2_next_round/scripts/r6_package_candidates.py
```

R2、R3、R4 是确定性重汇总；R5 自测和样本量脚本可重复运行。R6 的硬测试、回放和打包脚本以固定 run 名称写出，有些在目录存在时拒绝覆盖。请在隔离副本中复现，或先给脚本增加新的版本化 run_id。不得删除冻结结果后原位重跑。

R4 的上游生成不属于本轮执行边界。`outputs/r4_upstream_sources.csv` 列出了上一轮 M4/M5 产物、SHA256 和用途；应先核对这些哈希，再运行 `r4_state_pack_decision.py`。若要从原始数据重建 M4/M5，须回到对应上一轮研究目录及其复现说明，不能把本轮重汇总称为端到端重建。

两个候选的官方 validator 完整命令如下；在隔离副本执行可避免污染冻结报告：

```bash
cd research/phase2_next_round/candidates/ck0_hold
../../../phase2_validation/.venv/bin/python validate_submission.py
cd ../exploratory_fallback
../../../phase2_validation/.venv/bin/python validate_submission.py
cd ../../../../
research/phase2_validation/.venv/bin/python research/phase2_next_round/scripts/compile_deliverables.py
```

`exploratory_fallback` 是上一轮 P1 六芯多窗口 Ridge 与官方四串浅充诊断回退的接口包，不是 R1 的全信号 TCN、严格去温度 TCN 或末期加权 TCN。后三者是 D1 研究比较器，没有被部署到官方接口包。

关键输入和输出哈希见 `outputs/artifact_hashes.csv`；重跑汇总后可用下面的命令逐项核对。哈希清单本身不包含自己的哈希。

```bash
research/phase2_validation/.venv/bin/python - <<'PY'
import hashlib, pathlib, pandas as pd
root = pathlib.Path('.')
rows = pd.read_csv('research/phase2_next_round/outputs/artifact_hashes.csv')
for row in rows.itertuples(index=False):
    got = hashlib.sha256((root / row.path).read_bytes()).hexdigest()
    assert got == row.sha256, (row.path, got, row.sha256)
print(f'hash verification passed: {len(rows)} files')
PY
```

最后检查 `outputs/acceptance_results.json` 的 `correctness_pass=true` 和 `research_closed=true`。`predictions_long.csv` 中 D3 的 CK1–CK7 真值与误差必须为空；这项检查不表示官方容量准确度已经验证。
