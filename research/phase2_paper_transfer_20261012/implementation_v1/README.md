# 四篇论文迁移研究 implementation_v1

执行日期：2026-10-13。此目录是独立研究版本；正式模型、原四方法冻结结果只读。

## 阅读入口

- `FINAL_REPORT.md`：完整中文结论，包含失败、拒绝和证据边界。
- `decision.json`：机器可读接纳结论。
- `protocol.md` / `config.json`：评分前登记的模型、参数、阈值及种子。
- `freeze_manifest.json`：105 项源码、输入和旧基线依赖指纹。
- `literature_evidence.json`：全文获取状态；本轮是受论文启发的改造，不冒充全文复现。
- `science_checks.json`：数值、因果、边界及原始缓存核验。

## 结果文件

`pulse_registry.csv` 保留全部电流跳变、时间对齐、延迟、接受/拒绝理由。其 R 是延迟表观电阻，非瞬时 R0。

`rest_registry.csv` 使用前60%拟合、后40%验证，比较末值保持；无独立OCV/SOC标尺。

`event_registry.csv`、`raw_reaudit.csv`、`raw_voltage_verification.csv` 记录75条事件与原始电流/四芯电压的核验。`raw_manifest.json` 记录原始文件指纹。

`forward_evaluation_metrics.csv` 和 `forward_summary.csv` 分开 A（无目标电压）、B（首1Ah）预算；2Ah后评分。总结果含公共回退，直接覆盖单列。`historical_evaluation_profiles.csv` 是预测前可见历史的尺度误差剖面。

`synthetic_evaluation_metrics.csv` 和 `synthetic_by_scenario.csv` 包含16类机制、每类10个固定种子及四个损失/约束组合；种子不是独立物理电池。容量投影拒绝和错误接受分别统计。

`paired_evaluation_metrics.csv` 仅用两条完成历史轨迹估计健康参数，预测第三条轨迹的后缀；5类机制×2种子的小面板不能当大样本结论。

`identifiability.csv`、`sensitivity_best_states.csv`、`joint_witnesses.csv` 是条件剖面、干扰敏感性及非穷尽反例搜索，不是95%置信区间。

`conditional_capacity_windows.csv` 只是在明确CK0参考状态假设下的条件范围，不是新的CK1–CK7真实SOH预测。

`CK0_derivative_features.csv` 和 `feature_feasibility.csv` 是带载曲线特征审核，未冒充OCV或复现Sun重构公式。

## 执行过程

原始审核 → 官方/模拟开发 → 科学检查 → 冻结 → 官方前向回放和独立模拟 → 敏感性/特征审核 → 固定规则汇总。

评分完成后不要删除 `EVALUATION_STARTED`、`SYNTHETIC_STARTED` 或完成标记重调参数。复现须复制源码、配置和输入登记到新的同级目录，使用相同配置完成开发、检查，重新建立该目录指纹后评分。

直接执行新 `run.py` 的入口：

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 research/phase2_paper_transfer_20261012/implementation_v1/run.py development
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 research/phase2_paper_transfer_20261012/implementation_v1/run.py freeze
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 research/phase2_paper_transfer_20261012/implementation_v1/run.py evaluation
```

复用旧模块会把旧src目录放到导入路径前面，其他脚本中的 `from run` 因而可能命中旧执行器。执行 `mechanisms.py`、`paired_mechanisms.py`、`diagnostics.py`、`summarize.py` 时，使用下面的固定路径加载方式；本次已记录于 `runtime_import_audit.json`，未修改冻结算法。

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 - mechanisms.py evaluation <<'PY'
import importlib.util, runpy, sys
from pathlib import Path
script, args = sys.argv[1], sys.argv[2:]
p = Path('research/phase2_paper_transfer_20261012/implementation_v1').resolve()
sys.path.insert(0, str(p))
spec = importlib.util.spec_from_file_location('run', p/'run.py')
runner = importlib.util.module_from_spec(spec)
sys.modules['run'] = runner
spec.loader.exec_module(runner)
runner.verify_freeze()
sys.argv = [str(p/script), *args]
runpy.run_path(str(p/script), run_name='__main__')
PY
```

将 `mechanisms.py evaluation` 换为 `paired_mechanisms.py evaluation`、`diagnostics.py` 或 `summarize.py` 即为对应入口。主机制和配对机制共享确定性缓存，复现时建议先后运行这两项。

## 实施修订和范围

三个开发阶段修订目录保留早期输出：日期时间单位、日志去重、电压与电流对齐。全部修订发生于冻结前，不使用评分结果改变模型。

`runtime_import_audit.json` 记录冻结后的模块重名导入修复；通过按绝对路径绑定同一冻结执行器完成，不改变阈值、种子或预测公式。

真实逐芯SOC和后续同协议容量标签不可用；模拟与电压结果不能代替真实SOH精度。实验完成不等于容量更新接纳。
