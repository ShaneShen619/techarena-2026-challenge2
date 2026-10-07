# C_Silva2026_Conformal — 仿真迁移与区间覆盖边界

- 书目：Silva, Ozkan, El Idrissi, Canova, “Conformalized Transfer Learning for Li-ion Battery State of Health Forecasting under Manufacturing and Usage Variability,” [arXiv:2603.24475](https://arxiv.org/abs/2603.24475)。2026-09-29 读 13 页预印本 PDF，`papers/C_fulltexts/C_Silva2026_Conformal.pdf`；出版状态按预印本，许可依 arXiv 页面。
- 数据/标签：A123 26650 LFP 相关参数化的 SPMe 加 SEI/LAM 模型生成源域 1/3/4 批和目标域 2 批**虚拟电芯**，输入只是充放倍率协议与历史 SOH（式 6），标签为仿真 SOH 轨迹；不是现场未知容量的只读观测。Table 1 批次倍率不同；多仿真芯共享同一生成器，不构成独立实测确认。
- 方法：LSTM 单步预测下一 SOH，MMD 对齐源/目标潜表示（式 11–14），仅源批次 Leave-One-Batch-Out 选 λ；源训练均值/方差标准化（式 15–16）。预测区间用校准残差绝对值的 `ceil((n+1)(1−α))` 顺序统计量（式 17–21）。该 conformal 有可交换/条件稳定性要求；在线时间序列、工况移位下“distribution-free”不能无条件推出目标覆盖。
- 划分/结果：每个源批另留 10 个仿真芯作校准，目标批有截至 20 kAh 的少量**有标签目标样本**用于适配，后续目标样本无标签参与 MMD（原文 §3.2.2）；不能称纯无监督目标域；设 90% 目标覆盖，Fig. 5/Table 3 报告目标平均经验覆盖 98.8%、平均宽 4.08 个 SOH 百分点。**这只是该仿真目标批的经验覆盖**，校准样本来自源域，同组时间片相关，不能作为官方 4S 保证。作者 Discussion 明示尚需真实测量噪声和现场变异验证。
- 适配/反证：可迁移“异常/OOD 时扩大区间或拒绝高权重更新”的决策规则；绝不能用其数值区间直接为官方隐藏点打包票。真实校准应按物理组留出、按时间前缀取残差并报告组级、尾部、温度条件覆盖，容量真值定义一致；小于足够独立组数时只报告探索区间或保守界。最小反证是温度/容量/组拓扑全留出时固定模型和区间，检验覆盖与宽度；缺目标标签则不可称已校准。
- 核验等级：E2 原文公式、Table 1/3、Fig. 5 核查；无真实数据验证。
