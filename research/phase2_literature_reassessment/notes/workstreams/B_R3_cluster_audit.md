# R3 独立单位复核

先读取冻结汇总 research/phase2_next_round/outputs/r3_voltage_scores_all.csv（SHA256 8e9f7d5e570d7fd6cf005c6312db66415a2a125f20efa8ae0ab083ee75cf3075），再从其对应原始逐点文件 research/phase2_method_exploration/runs/M1_voltage_forecast_v1/forward_voltage_predictions.csv（SHA256 6227923420017adec5fa2dbb419c599fc15121f6475339d13862e38d96a9338e）核对 fixed_ECM、matched_last_shift 各 11,988 点及 MAE 完全一致，随后重采样。未改任何旧产物。命令：python3 research/phase2_literature_reassessment/notes/workstreams/B_R3_cluster_audit.py。运行环境系统 Python + NumPy/Pandas，随机种子 20260929，10,000 次 bootstrap；JSON 实测输出 B_R3_cluster_audit.json。

按 start+cell+method 先平均绝对电压误差，再做固定 ECM 减 matched-last-shift 的配对差。37 个 start 各有 4 芯，共 148 个逐芯事件；物理激励单元为 37 次同一四串组脉冲。优势均值 10.0423 mV。错误地按 148 个逐芯事件独立重采样，95% 百分位区间 9.3619–10.7687 mV、宽 1.4069 mV；按 37 次组脉冲均值重采样，9.5685–10.5178 mV、宽 0.9493 mV。原 R3 代码已按 start 重采样 2,000 次，报告 9.5789–10.5278 mV，与本轮复核吻合。区间方向并非总会按“更少单位”变宽；此样本逐芯差异使其反向，关键是按真实共同激励单元评估。

限制：37 次脉冲仍来自同一物理电池组，存在时间相关；bootstrap 区间不是跨组泛化不确定性，更不是容量 SOH 区间。matched-last-shift 观察目标脉冲早期 0.2–1.0 Ah 后预测 2–10 Ah 后段；没有对同脉冲未见早期的预测，也没有匹配的容量真值。
