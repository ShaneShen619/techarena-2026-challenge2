# C_Ispizua2026_PINN — 任意放电片段的物理损失

- 书目：Ispizua et al., “Real-Time State-of-Health Estimation and Online Degradation Prognosis from Partial Battery Discharge Using Physics-Informed Neural Networks,” [arXiv:2608.14764](https://arxiv.org/abs/2608.14764)。2026-09-29 读 22 页预印本 `papers/C_fulltexts/C_Ispizua2026_PINN.pdf`；正式发表/代码状态未核。
- 数据/目标：Section 2.1 明确复用 Severson et al. (2019) 快充集，122 枚标称 1.1 Ah、3.3 V 单芯，统一 4C 放电至 2 V，不同快充策略；该原始集为 A123 石墨/LFP。10 枚专用于验证/测试（Section 3/Conclusions 表述有别）。每条完整放电曲线用 Kneedle 寻找拐点，取对应容量当**SOH 指示量**（Results p.12），这个由算法生成的目标不等于官方至 11.2 V 放电积分 Ah。它与其他 MIT/Severson 论文共享原始数据，不可算独立重复。
- 方法：先按电压把完整放电曲线后验切成 8 类，每片固定 5% 额定容量跨度；分类器选类，类内特征选择，然后每类单独训练 FNN 加 Verhulst 型物理残差，参数 `r,K,C` 在训练中自由学习（Section 2 / Results p.12–14）。物理约束是经验退化轨迹形状，未给定从四串浅充波形到组端容量的守恒识别。
- 结果/划分：10 个验证芯与其余训练芯分开；Table 4 各电压片 FNN/PINN 对比，摘要 MAPE <4%。片段从同一完整放电构造，所以“任意片段”主要是**已覆盖完整曲线的后验裁剪**，不是自然到达的未知起点浅循环。99% 电压片分类精度来自相对均质的实验芯（Results p.12），与容量误差是两种指标。
- 适配/反证：借片段质量门控/分窗模型和经验损失做候选；但官方多为充电、四串、温变、真实缺窗。最小反证：仅真实浅充事件、禁止未来完整曲线选窗，在同输入外层留出组上，按组比较纯 FNN 与物理残差及简单双变量基线；若只在后验裁剪获益，路线不可部署。
- 核验等级：E1 原文 Section 2/3、Table 4、Conclusions；未数值复现。SOH 的作者指标来自放电拐点，虽然论文式 (2) 形式为 `Q_act/Q_nom`，不能误称全放电至截止的实际容量。
