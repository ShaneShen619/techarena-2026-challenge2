# C_Fragmented2025 — LFP 碎片充电容量与迁移

- 书目：*Communications Engineering* 4 (2025) 32, “Data-driven available capacity estimation of lithium-ion batteries based on fragmented charge capacity”, DOI [10.1038/s44172-025-00372-y](https://doi.org/10.1038/s44172-025-00372-y)。2026-09-29 读出版社开放 PDF 11 页与 HTML Methods，`papers/C_fulltexts/C_Fragmented2025.pdf`；出版社注明数据和代码须向通讯作者申请，故未复现。
- 数据/标签：Table 1 四个 LFP/石墨单芯库：VALENCE 4 芯、2.5 Ah、11,500 周期样本（1C 充/4C 放）；HUAWEI 4 芯、280 Ah、4574 样本；GOTION 3 芯、27 Ah、4262；A123/MATR 50 芯、1.1 Ah、32,800。可用容量取相应循环 CC 放电容量（Fig. 1），不是官方 4S、C/20 组压截止容量。11,500 是窗口/循环样本，主实验仅 4 个物理实体。
- 方法：从**完整 CC 充电曲线后验分段** 3.0–3.6 V 的 11 个固定电压窗，对各窗积分 `ΔQ_j=∫_{V_j}^{V_{j+1}} I dt`；Pearson 筛选并组合 1–2 个特征，LASSO/XGBoost/LightGBM 预测同循环放电容量。跨循环组合需先说明每个输入在预测时已发生（Results Feature extraction / Fig. 3–4）。温度、起始 SOC、电流和切窗阈值影响可比性；若一段不存在，不能用未来完整曲线补齐。
- 划分/结果：Methods 明确 VALENCE #1–3 训练、#4 测试，标准化在划分后；主库最优 RMSE 0.012（原文表/图以其目标量报告，勿改称官方 pp）。跨域 #2/#3 先零样本，再用目标域标签微调；Table 3 某目标 #4 RMSE 0.034，换窗特征改善到 0.016 却使其他目标变差，提示窗选择容易按目标测试集优化。Supplementary Note 3 的具体微调标签数量本轮未核到，不能称一锚点迁移。
- 竞赛判断：证明在有重复完整 CC 曲线且同协议容量标签时局部 Ah 可承载容量信息；不能证明任意 20 Ah 浅充、未知初始 SOC、25/45°C 混合下窗口仍有相同映射。最小反证：按真实浅充事件而非深循环后裁剪，冻结窗口阈值与归一化，只用前缀，留出物理芯/温度，比固定宽窗、年龄/吞吐量基线；若有效窗缺失或性能随起点变动即降级。
- 核验等级：E2 出版 PDF Table 1/Fig. 3–4/Methods 和网页逐项对照；未获取底层数据、未运行代码。
