# 阶段 1 B → 四串电池组 + A 趋势反馈

分支：`exp/pack-trend-feedback-20261011`。这是研究原型，没有替换项目正式入口。

先读 [四串电池组与A趋势反馈_验证报告](outputs/四串电池组与A趋势反馈_验证报告.md)。主实验预登记见 `protocol.md`；探索性事件轴见 `event_axis_addendum.md`。

在仓库根目录运行（沿用本项目已安装的 Python 环境）：

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 research/phase2_validation/.venv/bin/python research/phase1_pack_trend_20261011/scripts/run_rate_validation.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 research/phase2_validation/.venv/bin/python research/phase1_pack_trend_20261011/scripts/run_rate_validation.py --event-axis
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 research/phase2_validation/.venv/bin/python research/phase1_pack_trend_20261011/scripts/run_pack_validation.py
research/phase2_validation/.venv/bin/python research/phase1_pack_trend_20261011/scripts/audit_inputs.py
research/phase2_validation/.venv/bin/python -m pytest -q research/phase1_pack_trend_20261011/tests
```

依赖：numpy、pandas、scipy、pytest；沿用上一轮阶段 1 训练实体缓存和已审计的片段输入。脚本只读 `research/phase1_transfer_ab/`，新输出全部保存到本目录。

- `src/pack.py`：四条 CK0 带载曲线、测量链残差、有限外推、首次组端截止。`stretch` 是相对 CK0 的水平伸缩，不能解释为已经识别出的单芯绝对容量。
- `src/trend.py`：局部充电窗口的有符号对数斜率；门控；倍率慢状态；前向增量反馈和历史损伤反馈。
- `outputs/rate_predictions.csv`：每物理电芯和日期的原 B、元数据对照、A 趋势、置乱对照。
- `outputs/nested_audit.json`：趋势映射标签生成的 B 拟合与配置选择排除关系。
- `outputs/inner_prior_diagnostics.csv`：更内层小样本 B 拟合不稳定诊断。
- `outputs/official_4S_prototype.csv`：无标签官方原型输出，不能用于计算精度。
- `outputs/provenance.json`：本轮代码、输入和预登记文档的 SHA256。
- `event_axis/`：按严格前缀合格事件数的第二坐标，保留主实验结果。

模型范围：A→B 仍为冻结决策网格的研究控制器；完整事件级状态估计、MHE/GP、四芯独立参数识别和官方后续容量准确性均未被验证。两种趋势坐标都没有通过门槛；全源研究选型自动选择反馈增益 0。
