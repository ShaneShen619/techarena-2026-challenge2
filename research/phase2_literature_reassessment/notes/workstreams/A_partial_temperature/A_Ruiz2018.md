# A_Ruiz2018 — 充/放温度历史与参考容量

**书目/全文。** Ruiz Ruiz, Kriston, Adanouj, Destro, Fontana, Pfrang, *Journal of Visualized Experiments* 137:e57501 (2018), DOI [10.3791/57501](https://doi.org/10.3791/57501)。2026-09-29 实读 [Europe PMC 完整 JATS 正文](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC6126518/fullTextXML)，本地 `papers/A_partial_temperature/TempLFP2018.xml`；XML 声明 CC BY-NC-ND 3.0，仅作本地研究副本。它与作者 2017 *Electrochimica Acta* 论文 [10.1016/j.electacta.2017.03.126](https://doi.org/10.1016/j.electacta.2017.03.126) 有共享实验，**不计独立重复**。E1：Protocol §3、Results 图 1–4/表 1、Discussion 图 7；未复算 ANOVA。

**实体/协议/标签。** 约 20 枚试制 LFP/石墨 B5 pouch（十种充/放温度组合，各重复一次），-20 至 30°C、1C、100 深循环；每 25 次在 **25°C、0.3C** 做两次参考充放，充分热稳定。文中区分 `CR_long-term`（各老化工况同温/1C 实测）与 `CR_ref`（25°C 参考工况），分母均需对应首周期/首参考周期，不能混用。额外热电偶在芯表面，环境箱控温。未覆盖 45°C 或百 Ah 四串。Protocol §2–3、表 1。

**结果/公式。** 图 3、表 1 中 30°C 充/-5°C 放与 30/30°C 放，运行容量保持率约 90% vs 86%，但 25°C 参考保持率方向反转（约 82% vs 86%）；说明即时低温可用量与永久损失混合时甚至会反转排序。作者把参考退化率在充/放温度平面拟合多项式（图 7，R²=0.92），发现温度相互作用，不能简化为单个运行温度 Arrhenius 校正。低温工况存在复温后容量恢复；表面形貌为可能机制，不能凭此直接确定每枚芯 LLI/LAM。短时间 100 周期及试制芯限制外推。

**适配/反证。** Q3 必须分开事件测温、老化温度历史与参考标签温度。最小实验：同一物理芯在不同运行温度重复同样窗口，均回 25°C 做标准容量，另交叉充/放温度顺序；若运行指标变而参考容量不变，是可逆测量效应；若参考容量随热历史变，才是老化信号。时间顺序和参考复测必须固定。作者没有公开可直接运行的容量估计代码。
