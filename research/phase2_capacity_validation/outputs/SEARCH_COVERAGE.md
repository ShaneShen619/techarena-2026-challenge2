# N1 数据检索范围与资格结论

检索日期 2026-09-30。先盘点项目 `data/`、`dataset original/`、`TU Darmstadt/` 以及 Downloads 中显然与已有包相同的 `dataset/`、`field_data/`，跳过虚拟环境和无关个人目录；后两者为已知包副本，不按新的独立实体计。查阅桌面 `项目/Current State_Challenge1/README.md`、前轮数据资格表和重调研登记表。未发现新独立 4S 实体的成对操作加真实 RPT；“未发现”仅限上述范围和下列公开来源，不是全网不存在。

公开原始来源按作者/机构数据页核验：

- [Ji 等二次利用 LFP 23 单芯 Zenodo](https://zenodo.org/records/18630889)：作者说明 23 个单芯、三次容量测试均值写入文件名，后续 25 °C 的 1C 恒流恒压充电曲线。下载 4,196,439 字节 ZIP，发布页 MD5 `ffacb176a7be606067b5d0c805fe8892` 与本地一致，SHA-256 见 `download_log.csv`。23 个工作簿均可解析；每个物理单芯一份，一次快照，无三次 RPT 原始放电曲线。来源页许可字段未明确；仅本地研究，不再分发。只能作异协议单芯容量迁移。
- [He 等 ESSL1 Zenodo](https://zenodo.org/records/20132842)：16S 包及单芯数据，非官方 4S；容量/协议配对待进一步核验，未为本轮大包下载付出空间。不能升级 D2。
- [Xu 等 Mendeley 数据](https://data.mendeley.com/datasets/4nww8p6vxf/1)：1P10S 模组及单芯、校准容量，拓扑不符；留条件迁移候选。
- [UConn REIL 108 单芯](https://digitalcommons.lib.uconn.edu/reil_datasets/3/)：1.2 Ah 单芯周期 RPT，容量真实性较有价值，但体积大且拓扑/额定容量不符；本轮只核对来源页，未下载原始大包。
- [DOE ROVI](https://www.energy.gov/oe/rapid-operational-validation-initiative-rovi)：仅作为采集/RPT 字段组织的参考线索，不是本赛 4S 标签。

本地 P1/D1 六单芯为反复开发代理；Che 单芯归一化充电标签不等于组端首次 11.2 V 的 4S C/20 容量；TU 8S 现场数据没有配对容量 RPT。官方仅一只现有 4S 组，CK0 公开 100.41 Ah，CK1–CK7 真值隐藏。对“同协议独立验证”的阻断点是缺新的物理四串组及其同组运行前缀与受确认满充/温度/截止协议的配对 RPT，不是软件环境、联网或表格解析能力。

来源页面为元数据证据，文件级 SHA 和标签暴露见 `source_registry.csv`、`label_provenance.csv`；未下载来源不得写作已解析。当前交叉协议试验使用 Ji 单芯真实作者容量标签，但源文件名曾暴露数值，研究者不是盲法；只有程序按电芯隔离开发/封存，因而确认等级为探索性。
