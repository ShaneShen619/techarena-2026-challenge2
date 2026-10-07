# C_YaoKowal2026_SSL — 周期顺序自监督的反证边界

- 书目：Yao & Kowal, “Degradation-aligned self-supervised learning for state of health estimation of lithium-ion batteries under label sparsity,” *Energy and AI* 26 (2026) 100884, DOI [10.1016/j.egyai.2026.100884](https://doi.org/10.1016/j.egyai.2026.100884)。2026-09-29 读正式开放 PDF 19 页，`papers/C_fulltexts/C_DegradationAligned2026_SSL.pdf`；PDF 页 2 标 CC BY。
- 数据/真值：CALCE CX2-34/36/37/38 四枚 **LCO 1.35 Ah** 单芯，0.5C CC-CV 充至 4.2 V、1C 放至 2.7 V；SOH 为实测完整放电容量/额定容量（Section 3.1、Table 2）。输入每周期 CC 充电电压曲线，重采样 300 点，长度本身也反映老化。四芯仅四个独立实体，不因数千周期增加跨芯自由度。
- 方法：同一芯两周期按周期号构造排序监督 `y_ij=sign(n_i−n_j)`，损失 `log(1+exp[−y_ij(s_i−s_j)])`（式 9–13）；预训练编码器后冻结，用稀疏容量标签训练新回归头（Fig. 4）。这是**寿命顺序监督**，无需 Q 标签但需事件排序与长期历史；能学到与老化相关的时间代理，并不保证机制上与容量一一对应。
- 划分/结果：主设 CX2-37/38 训练、36 验证、34 测试，主测试退化深度被训练芯包围；Section 4.4 再四轮留一芯，外推最深 CX2-38 的 1% 标签情形 MAE 3.195%（正文），而主情形摘要给 1% 标签 MAE 1.718%、RMSE 2.329%，不可混成同一难度。Table 4 的 early-only 1% 行 MAE 11.266%、MAX 27.212% 展示标签覆盖比标签比例更关键；这条是该表情形，需与对应列/划分读。作者在 Discussion 承认单型号受控数据不足以证明跨条件推广。
- 适配/反证：可试时间顺序预训练作为退化轨迹先验，但必须与仅周期序号/日期/累计 Ah 基线以及顺序打乱消融相比；预训练不得看到目标组未来序列。官方只有一个容量锚，1% 标签假设远强于此。若序号基线同样好或末期显著失效，排序编码器不提供可辩护的新增容量信息。
- 核验等级：E2 全文式 9–13、Table 2/4、Fig. 4 与 PDF 原页核查；未运行代码。
