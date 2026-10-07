# Bilfinger2026｜整车 SOH/DVA 测量稳健性（全文受限）

Philip Bilfinger, Philipp Rosner, Markus Schreiber, Tobias Brehler, Cristina Grosu, Jan Schöberl, Kareem Abo Gamra, Markus Lienkamp，*Battery pack diagnostics for electric vehicles: Robustness of the state of health measurement and differential voltage analysis at the vehicle level*，*eTransportation* **28**, 100589 (May 2026)，[DOI 10.1016/j.etran.2026.100589](https://doi.org/10.1016/j.etran.2026.100589)。书目由出版方 DOI/Crossref、[TUM 机构记录](https://portal.fis.tum.de/en/publications/battery-pack-diagnostics-for-electric-vehicles-robustness-of-the-/) 核对。Elsevier API 元数据标开放获取、CC BY 4.0，但本轮无法取得完整正文：ScienceDirect HTTP 403/浏览器验证码；SSRN 2025 作者预印本 PDF 亦 403。未绕过限制。访问日期 2026-09-29；本地保存 TUM 记录、Elsevier/Crossref 元数据、作者 [代码库 README](https://github.com/TUMFTM/EV_DVA_robustness) 和 [mediaTUM 数据入口](https://mediatum.ub.tum.de/1840112)，见 `papers/E_forward_pack/`。**访问等级：metadata/abstract only；不计全文评价，也不支撑正文中无法复核的分割、数值或性能主张。**

机构记录/摘要明确研究对象是 **VW ID.3、Cupra Born、Tesla Model 3** 的车端低功率充电测量，评价充电功率、环境温度、充/放方向、静置 SOC 对**车端 SOH 测定和 DVA** 的影响，并比较同型号多车的重复性。这里的“转移/比较”是车辆测量条件和同款车辆间对照；它没有在已读摘要中声称四串 LFP、单容量锚点训练、隐藏月度 C/20 放电容量预测或 ICA 回归误差。作者摘要称在受控边界条件下可重复，不能代替阈值、效应量、分割和容量真值协议的全文核验。

作者公开代码仓库 README 指向 mediaTUM 数据，描述车端 SOH、DVA、滤波和图表生成；代码入口存在不等于已经审查或运行。其余细节：车辆具体数量/各车化学与容量、参考标签倍率/温度/电压窗、重复性数值、误差分布及最差车、是否与独立放电真值比较——**未从可读全文确认，保持未知**。此外，该 2026 论文的标题/摘要重点为 **DVA** 和测量稳健性，不能把它表述成 LFP ICA 直接容量预测验证。

对官方问题的保守用途：提醒实施时需预先固定充电功率、温度、方向、静置 SOC、可用电压界，并验证重复性；不据此改写容量路线的性能证据等级。若后续获得合法完整正文，从其方法、表/图、数据及代码核实上述未知后再升级证据卡。唯一无须新全文即可独立开展的反证实验是：同一 4S LFP 组在可控 SOC/温度/功率下重复标准化诊断事件，并与独立参考容量比较，而不是只比较波形外观。
