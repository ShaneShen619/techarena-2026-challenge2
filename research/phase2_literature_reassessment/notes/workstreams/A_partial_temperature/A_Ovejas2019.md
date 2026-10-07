# A_Ovejas2019 — LFP 老化、滞后与极化

**书目/全文。** Ovejas & Cuadras, *Scientific Reports* 9:14875 (2019), DOI [10.1038/s41598-019-51474-5](https://doi.org/10.1038/s41598-019-51474-5)。2026-09-29 实读 [Europe PMC 完整 JATS XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC6795866/fullTextXML)（PMC 页面临时验证码），本地 `papers/A_partial_temperature/Hysteresis2019.xml`；XML 声明 CC BY 4.0。E1：Results “Overvoltage and OCV hysteresis in LFP cells”、Methods “OCV and hysteresis”、图 5、7、式(1)–(7)；未运行数据。

**研究设计。** 商用 LFP/石墨 14430、标称 0.4 Ah 与 NMC/石墨 18650、2.8 Ah；LFP 在 25°C 以 C/5 充、2C 放，约 1000 次循环。LFP GITT 测双方向 OCV：C/50 脉冲 150 min + 16 h 静置；不是普通 BMS 休止点。文中报告 LFP 在 C/25 与 2C 不同检测倍率下容量衰退可为 23% 与 15%，说明“容量损失”依测试协议而变。实体数/独立重复未在所读正文清楚报告，不按曲线数累计。作者没有做在线组容量预测。

**方程/证据。** `H(z)=OCV_charge(z)-OCV_discharge(z)`；充电极化 `η_ch=V_ch-OCV_ch`，放电极化 `η_dis=OCV_dis-V_dis`。图 5 LFP 老化后充电极化增大，但在首末两点比较中放电极化可能下降；作者解释中间约 300 周期后又上升，截取首末会误判轨迹。图 5、7 中老化所致额外充放极化差与滞后增量相随，石墨相变对峰形有影响。作者的机理归因是实验解释，并未证明此关系可单独识别全容量。

**本题边界/最小实验。** 同一固定电压窗的 Ah 会受充放方向、最近极化/静置和老化滞后改变，CK0 放电准 OCV 不足以直接标定运行充电。用同一枚容量已知 LFP 先从共同 SOC 锚点执行充→放与放→充两路径、相同温度/电流/窗口且不同静置长，估窗口 Ah 和峰位；容量不变时若指标显著漂移，先分路径或拒绝更新。本论文温度固定 25°C，不支持温度补偿系数。
