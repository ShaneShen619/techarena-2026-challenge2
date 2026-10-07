# Jiang et al. 2023：10 分钟静置电压法，当前只作摘要级筛选

Bo Jiang et al., “An adaptive capacity estimation approach for lithium-ion battery using 10-min relaxation voltage within high state of charge range,” *Energy* **263** (2023), 125802, [DOI 10.1016/j.energy.2022.125802](https://doi.org/10.1016/j.energy.2022.125802)。日期按 Crossref 卷期为 2023，DOI 带 2022 不等于正式卷期年。

2026-09-29 检索出版方[论文页面](https://www.sciencedirect.com/science/article/pii/S0360544222026883)、Crossref 原始 DOI 元数据与 OpenAlex 可得性。出版方检索页/摘要明确：取**充电停止后的 10 分钟静置电压序列**；双层 GPR 一层估 OCV、一层利用序列和估计 OCV 估容量；在 **SOC 大于 90%** 时摘要报全寿命 MAE **2.493%**。可读网页曾显示引言片段，但获取完整正文的网页请求和 CLI 请求返回 403；OpenAlex 记录 `is_oa=false`, `any_repository_has_fulltext=false`，作者公开完整稿未检得。未取得 Methods、数据量、化学体系、真值测量、物理电芯数与测试划分；因此**不建深入证据卡，不把 2.493% 当可与本竞赛直接比较的精度**。

对本项目的最低条件是运行流中有可证明的“充电终止后连续静置 10 分钟、此前 SOC>90%”事件，并有带同定义容量标签的 LFP 四串训练/留出组。仅 CK0 单个组端 C/20 放电锚点不足以训练双 GPR。若后续拿到全文，再补清 chemistry、n、参考容量协议与跨组拆分；在此之前优先把它作为“静置事件资格检查”的探索线索，不能转为主路线证据。
