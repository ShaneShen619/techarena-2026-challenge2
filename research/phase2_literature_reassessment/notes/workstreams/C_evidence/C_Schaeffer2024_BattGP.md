# C_Schaeffer2024_BattGP — BattGP 现场电阻 GP

- 书目：Schaeffer et al., *Cell Reports Physical Science* 5 (2024), 102258, DOI [10.1016/j.xcrp.2024.102258](https://doi.org/10.1016/j.xcrp.2024.102258)。2026-09-29 读作者稿 [arXiv:2406.19015](https://arxiv.org/abs/2406.19015) 19 页 PDF，并核正式出版页、[Zenodo 1.0.0](https://zenodo.org/records/13715694)、[BattGP 作者代码](https://github.com/JoachimSchaeffer/BattGP)。本地 `papers/C_fulltexts/C_Schaeffer2024_BattGP.pdf` 为作者稿。**版本差异：作者稿 29 系统/232 芯/131M 行；正式论文表 1 为 28 系统/224 芯/133M 行；Zenodo 1.0.0 README 则写 28 系统/232 芯/133M 行，且称每组 8 串，内在不一致。**样本数采用正式论文表 1 的 28/224，并保留 Zenodo 冲突。
- 问题与新增：用递归时空 GP 从不规则现场电流、电压、温度估计随运行点与时间变化的电阻，进而作单芯异常概率；新增开放 8S LFP 现场数据和 BattGP。数据是约 160 Ah 棱柱电芯，28 个返修 8S 系统，共 224 芯；四个温度探头各由相邻两芯共享，存在主动均衡。28 个组是实体单位，224 芯高度相关，133M 行更不是独立样本量。Zenodo 描述与作者稿 Field Data Set、表 1。
- 观测/目标：电流、组/芯电压、温度、平衡等现场信号；从电压电流瞬态推阻抗健康指标。**无与官方 5.1 A 至 11.2 V 相容的周期容量真值；SOH 一词在背景中泛用，结果主目标是电阻/故障概率。**无容量 SOH 分母可移植。作者稿 Methods 中脉冲条件筛选、式 (8) 附近的电阻模型和故障概率，正式版 Summary/Methods 可核。
- 方法：可写作 `ΔV_i≈R_i(SOC,T,t)ΔI+偏置/动态误差`，GP 对 `R_i` 的运行点与时间变化给后验。参数来自现场可筛脉冲和 GP 核先验，不从独立容量标签识别。代码 README 明说“8s1p LFP field data”，本轮只静态核 README，未运行 BattGP。
- 划分与结果：论文分析返修组历史，不是以封存四串组容量标签为测试目标；无需把 28 组电阻分析转成容量 MAE。数据集存在返修选择偏差，Zenodo 描述明示不能代表全部售出组。作者稿/正式版样本数冲突表明引用版本必须固定。
- 竞赛适配：可迁移脉冲质量筛选、SOC/温度条件化 GP 电阻、组内异常概率；要把阻抗变成容量需新增同一四串组随时间的参考容量映射，且温度、SOC、均衡和串联阈值要另建模型。最小反证：在有参考容量的独立组上，固定电阻模型与温度/SOC 匹配，检验其增量能否优于仅时间/温度/吞吐量；若不能，电阻只能保留为故障门控。
- 作者代码静态核查：[`BattGP`](https://github.com/JoachimSchaeffer/BattGP) 提交 `6d5e1db3337f0de5f3a533acbc09eddccc178e9d`。`src/batt_data/data_columns.py` 将包电压、电流、BMS SOC、四个两芯共用温度和八芯电压/均衡变换器电流接入模型；未列周期容量真值。`src/batt_models/fault_probabilities.py` 用各芯 `r0` 后验均值/方差计算越带或越阈概率；`Weakest_link_stat` 汇合八芯故障概率。对应的是阻抗异常门控，不能把 GP 区间当作容量区间。
- 核验等级：E2（作者稿全文、正式版及数据 README/代码静态交叉核），未运行代码、未作容量验证。许可：Zenodo README `CC BY-NC 4.0`；网页 Rights 字段未显示值，重用以下载 README 为准并再核。

**样本资格补充（独立审查）**：正式论文全数据描述为 28 个返修系统/224 芯；电阻模型分析另筛出运行超过 100 天且至少 2,000 个有效点的 **21 个系统**（正式 PDF 第 8 页）。28 是数据覆盖，不可当作每个模型结果的独立样本数。
