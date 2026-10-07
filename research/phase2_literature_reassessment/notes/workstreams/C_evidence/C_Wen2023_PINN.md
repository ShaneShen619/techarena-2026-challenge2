# C_Wen2023_PINN — 经验退化方程约束的 SOH 网络

- 书目：Wen et al., “Physics-Informed Neural Networks for Prognostics and Health Management of Lithium-Ion Batteries”, [arXiv:2301.00776](https://arxiv.org/abs/2301.00776)。2026-09-29 读 14 页完整作者 PDF，本地 `papers/C_fulltexts/C_Wen2023_PINN.pdf`；论文脚注给 [作者代码](https://github.com/WenPengfei0823/PINN-Battery-Prognostics)。此卡使用作者稿版本，期刊正式状态待单独核。
- 研究：把 Verhulst 型容量损失动力学和 DeepHPM 数据推导残差加入网络损失，使用不确定性权重平衡多项损失；不是直接由无标签运行波形得到容量真值。目标 `PCL_k=1−Q_k/Q_nom`（原文式 1，分数），故 `SOH_fraction=1−PCL`；若报百分数则 `PCL_pct=100·PCL`、`SOH_pct=100−PCL_pct`；与官方 `Q/102 Ah` 只有分母概念相似。原文 Section III、式 (1)/(11)/(14)。
- 数据/特征：MIT/Stanford A123 LFP/石墨快充寿命数据，单芯约 1.1 Ah，完整周期容量及充放曲线。Case A 用 #91/#100 训练验证、#124 测试；Case B #101/#108/#120 训练验证、#116 测试；Case C batch 2 的 20% 数据随机抽作测试，故 C 的物理实体隔离需另核。特征包括 2.7–3.3 V 放电 Q–V 二次式系数、IC 统计、均温、内阻和充电时间（Section V-B/VI）；**官方浅充没有完整放电 Q–V 和同周期容量标签。**
- 划分/结果：训练标签由完整参考容量算出；A/B 按芯留出，训练集内另分验证；Table III 的 PCL 估计 RMSPE 改善到约 0.42% 等要结合 case/列解读，不能与官方 SOH pp MAE 等价。正文也说明简单等权物理损失有时不优于纯网络，权重法是性能关键（Table III、Fig. 6–8）。
- 适配：可借“偏导/变化率不为正”的弱损失或分段单调损伤先验；Verhulst 函数是经验形状，不是由官方可见量唯一辨识的电化学参数。CK0 单锚点下拟合多参数动力学会靠外部标签先验。最小反证：同容量标签、同输入、同训练预算，在留出实体/温度上比经验损失、单调损失、纯回归、年龄基线，并检查尾部高估；如只有训练内平滑改善，则不能入主路线。
- 核验等级：E1 原文式和 Table III/Case 划分；作者代码链接核到但本轮未运行/未作静态逐函数比对。
