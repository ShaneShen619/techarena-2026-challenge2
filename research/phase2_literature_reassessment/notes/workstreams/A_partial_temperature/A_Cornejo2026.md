# A_Cornejo2026 — 现场单芯/模块估计与末端限制

**书目/状态。** Cornejo, Meyer-Schwickerath, Sandalinas, Jossen, [arXiv:2609.04487](https://arxiv.org/html/2609.04487), 2026-09 预印本；2026-09-29 实读作者 HTML，尚无核实的期刊 DOI。E1：Results “Battery system and dataset”, “Validation against reference measurements”, 图 5–6、Methods OCV alignment；作者 Julia 仓库仅见论文说明，未核 commit/执行。

**实体/真值。** 27 模块、324 个可观测逻辑芯，每逻辑芯 2P LEV50N LMO/石墨 50 Ah 物理芯，12 逻辑芯串联/模块；**非 LFP 且 MMC 动态切换模块**，与本题恒定四串不同。12.5 h 两次现场循环，电芯电压 10 s、模块电流 1 s、模块温度 15 s，有时间缺口。模型在累计 Ah `q=∫I dt` 上拟合每芯 ECM/GP-OCV，再跨芯曲线对齐求初始 SOC、容量；需要群体共享 OCV 形状、端点锚与足够 SOC 覆盖。§Results 首节、Methods OCV alignment。

**结果需按真值层分开。** 图 5 中 lumped 模块估计比按其单芯估计的“可用 SOH”高 4–16%（25/27 模块），最坏两模块高 24%、31%；这是两种模型输出的比较，**31% 不是与独立 C/20 组容量真值的误差**。独立参照只覆盖 8 模块/96 逻辑芯，C/25 左右一次放/充，静置约 60 s 所构“pseudo-OCV”与拟合共用 CMU 传感器且容量同用曲线配准端点；单芯容量 RMSE 1.25 Ah，去模块共同偏差后 0.55 Ah。Results 图 5–6、Discussion 明述共享电流偏置与参考限制。缺官方低倍率至总压目标的直接验证。

**适配/反证。** 它支持“平均行为可能掩蔽限制芯”且揭示四芯同一电流测量误差相关；不能把其最小芯映射或 31% 转成四串预测误差。对本题取同一四芯的 `V_i`、组 `I` 以及 CK0 放电端点，分别模拟/核实总压与单芯截止协议下组可用 Ah，并做电流偏置共同扰动；若纯最小芯模型不能重现 11.2 V 组容量，需协议约束映射。末期监控限制芯身份切换与 SOC 不平衡，不能只看均值。
