<a id="en"></a>

# Round 3 capacity-model study

> English · [中文](#zh)

Exposed-exploratory; proxies are not hidden capacity truth. Read [FINAL_REPORT.md](FINAL_REPORT.md) for conclusions, all candidates and exact reproduction commands. The task is [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md).

The shared causal evaluator is src/harness.py; src/harness_extended.py preserves the supplementary baseline evaluation. Stage directories contain frozen protocols/hashes, research runners, CSV/JSON outputs and bilingual reports. Late physical diagnostics have separate protocols and are not promoted to primary models. stage_F/outputs/independent_* consolidates all variants with sample counts and epsilon-dependence. notes/STATUS.md and notes/DECISIONS.md record restart state and decisions; notes/INDEPENDENT_REVIEW.md records deviations.

Research uses Python3.13 with numpy/pandas (installed scipy/matplotlib are available but not required by the added models). Candidate validation uses Python3.11.14 in /tmp/arena-round3-py311, numpy2.4.6 and pandas3.0.6. candidate_model/v2_reference_model.py is an unchanged reference copy with the MyModel interface. No newly passing model was produced.

Data/framework and earlier studies are imported unchanged. cache/ is git-ignored. Use python -B to avoid bytecode writes in reused directories. All work is on exp/phase2-round3-models-20261014; nothing is wired into the active submission.

---

<a id="zh"></a>

# Round 3 capacity-model study

> [English](#en) · 中文

已曝光探索性研究；代理不是隐藏容量真值。结论、全部候选和精确复现命令见 [FINAL_REPORT.md](FINAL_REPORT.md)，任务见 [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md)。

共享因果评估器为 src/harness.py；src/harness_extended.py 保留补充基线评估。阶段目录含冻结协议/哈希、运行脚本、CSV/JSON 和双语报告。后补物理诊断单独登记，不提升为主模型。stage_F/outputs/independent_* 汇总全部变体、有效样本数和 ε 依赖。notes/STATUS.md 和 notes/DECISIONS.md 记录续跑状态/决定，notes/INDEPENDENT_REVIEW.md 记录偏差。

研究使用 Python3.13、numpy/pandas；环境中的 scipy/matplotlib 可用，但新增模型不依赖它们。候选验证使用 /tmp/arena-round3-py311，Python3.11.14、numpy2.4.6/pandas3.0.6。candidate_model/v2_reference_model.py 是原参考类的未改动复制，具备 MyModel 接口，没有新增通过模型。

数据/框架及前期研究原样导入。cache 被忽略，使用 python -B 避免向复用目录写字节码。全部工作位于新分支，不接入当前提交模型。
