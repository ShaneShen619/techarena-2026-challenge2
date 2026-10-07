# BatteryGPT2025｜早期完整寿命退化预测

## 书目、来源

Jincheng Hu, Pengyu Fu, Zhongbao Wei, Yanjun Huang, Juliana Early, Ashley Fly, Yuanjian Zhang，*Early prediction of lithium-ion battery degradation with a generative pre-trained transformer*，[DOI 10.1038/s41467-025-66819-0](https://doi.org/10.1038/s41467-025-66819-0)，2025-12-05 在线出版，正式引文 *Nature Communications* **17**, 126 (2026)。不能只从 DOI 年份称其为“2025 卷”。2026-09-29 下载出版方 [HTML](https://www.nature.com/articles/s41467-025-66819-0)、PDF 和补充 Note 1/3/4/6，本地 `papers/D_old_refs/BatteryGPT2025*`。出版页开放获取，**CC BY-NC-ND 4.0**。**E1 原文/补充核对**，未运行模型。

## 研究目标、数据和标签

目标是给定早期生命周期充电数据，生成未来**整个寿命轨迹**并预测随周期变化的 SOH、退化拐点与达到 80% SOH 的 EOL。主数据是 MIT/Severson 快充实验的 **46 枚 1.1 Ah LFP/石墨单芯**，30°C 强制对流箱；充电第一/第二阶段约 3.7–5.9C、至 80% SOC，随后 1C CC-CV 至 3.6 V，CC 放电至 2.0 V（正文“Data overview”，补充 Note 1）。文章称处理后 **21,280,768 samples**，它们是大量时间点/窗口，独立实体仍为 46 枚。SOH 定义当前容量/初始容量；CNN-LSTM SOH 估计器以**每周期真 SOH 监督训练**，GPT 另用整个训练芯充电轨迹进行下一 token 自监督。故信息条件是多芯全寿命轨迹与大量容量标签，不是仅一个 CK0 锚。

## 模型、切分、比较

离散化每时刻 `V,I,T`，GPT-small（论文称约 42M 参数、256 token context）自回归生成未来充电特征；CNN-LSTM 从生成的单周期特征估 SOH，再由预测 SOH 曲线取拐点/EOL（图 1、方法式 1/4/8–11）。正文与补充均称**前 42 芯训练，其余 4 芯验证**；正文“Data overview”又把这 4 芯称 test，并写 k-fold，具体独立调参/最终测试分工未充分清楚。没有理由把 21M 时间点当独立测试。作者提供的 EPSO 定义是可见寿命比例，但补充 Note 6 又把 BatteryGPT(5)/(30) 称作 **5/30 个观察周期**，并另讨论 5%/30% 起点；这两个信息预算不能视为等价，应区分主文 MIT 表 1 与 KIT 补充表 1。

MIT 表 1：BatteryGPT(5) 预测 SOH RMSE **2.56%**、MAPE **1.90%**、拐点误差 −177 周期；BatteryGPT(30) 为 **0.21%**、**0.14%**、拐点 +13 周期、EOL +10 周期。主文 EPSO(30) 是按**真实最终寿命的 30%**选择预测起点；若前瞻部署必须改成预先固定的日历、周期或 Ah 规则，不能事先知道总寿命。表 1 没明确四枚留出芯的指标汇总口径，不能擅称四芯组平均。回归 CNN/LSTM/CNN-LSTM 是**最近三周期预测下一周期**，任务时距不同；自回归 LSTM/Transformer 才同为长程生成且共用 SOH 估计器（正文 p.6–7、表 1）。本论文指标对应作者的寿命轨迹任务，不能外推为官方当前月度组容量 MAE。最差芯、最差月、置信区间未报告。

补充 Note 6 另称 KIT 长寿命跨温数据上 BatteryGPT(30) SOH RMSE **2.28%**、MAPE **2.01%**、拐点 −34、EOL −3 周期；仅说 chronological split，未列该数据的芯数、化学体系、具体训练/验证/测试实体及目标 SOH 测定细节，因此是**受限外部证据**，不是独立 4S LFP 容量确认。其 BatteryGPT(30) 标为 30 *cycles*；不可与 MIT 主文的 30% 起点混并。

## 可获得性、审查风险与竞赛适配

作者指向 [MIT 原始数据](https://data.matr.io/1)、[GitHub](https://github.com/ReparkHjc/BatteryGPT)（仓库可达、标 MIT license）和 Zenodo。正文“Code availability” 给出的 `10.5281/zenodo.1742067447` 实测 404；参考文献中的 [Zenodo 17420675](https://doi.org/10.5281/zenodo.17420675) 可达。记录这一书目/链接差异，未静态审代码、未复现。补充和正文没有澄清四芯是调参与最终测试是否分开；只标**不清楚**，不宣称发生泄漏。

本竞赛只有 CK0 一次 100.41 Ah 容量真值，目标为四串 102 Ah LFP 的月度 5.1 A 至组压 11.2 V 容量/102 Ah，CK1–7 隐藏。可借用轨迹预训练或将温度/电流/电压联合建模的想法，但模型需外部带全寿命标签的 LFP 单芯、适配到串联组与目标截止，并核查未来窗口/测试域统计。**拐点与 RUL 成功不能代替容量估计成功**。

最小证伪：冻结只在外部训练实体上学习的词表、归一化、GPT、SOH 头；在从未参与这些步骤的多组 LFP 前缀上，以组为单位、与年龄/累计 Ah/温度先验及低维容量基线比较相同月份的 C/20 组容量误差、最差组和后期高估。若增量只来自已知生命周期/训练标签或不能在单锚点适配后保持，则仅将该文用于寿命预测的背景论据。
