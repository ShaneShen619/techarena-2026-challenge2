# 四方法测试复现

运行环境：Python 3.13，本机numpy/pandas/scipy/matplotlib。独立研究实现，不是比赛提交包（比赛指定3.11/3.12，未在其环境验收）。

从项目根目录顺序运行：

```sh
python3 research/phase2_initial_soc_four_methods_20261011/src/audit.py
python3 research/phase2_initial_soc_four_methods_20261011/src/run.py prepare
python3 research/phase2_initial_soc_four_methods_20261011/src/run.py develop
python3 research/phase2_initial_soc_four_methods_20261011/src/run.py evaluate
python3 research/phase2_initial_soc_four_methods_20261011/src/report.py
```

v1已有EVALUATION_COMPLETE，evaluate拒绝覆盖评分。复现需先复制本研究目录为独立版本，并将audit.py的RUN指向新的输出目录；保留原始配置、种子及代码以比较数值。不要重开旧评分用于调参。依赖见requirements.txt。主结果FINAL_REPORT.md，结构化决策decision.json；逐事件评分、模拟评分、参数见证、原始审计及科学检查位于runs/v1。

评分后的探索诊断和只读报告可运行：

```sh
python3 research/phase2_initial_soc_four_methods_20261011/src/supplement.py
python3 research/phase2_initial_soc_four_methods_20261011/src/report.py
```

supplement.py有缓存；该命令不重新打开主测试、不修改主算法或评分。postprocess.py由report.py调用，读取保存输出，计数超域/无输出并生成补充图表。主报告明确记录评分后探索边界。`false_capacity_updates.csv`是原始优化旗标汇总，最终容量结论使用`false_capacity_updates_coverage_audited.csv`，其中无投影结果是失败/无输出。`daily_relative_charge_qualified_trace.csv`在缺口后留空。
