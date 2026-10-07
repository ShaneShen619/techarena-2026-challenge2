# V0 数据资格复核（2026-09-29）

结论：在本次**本地相关项目目录**复查中，未发现可作为 D2-compatible 确认集的、带独立容量真值的新四串物理组。现有唯一同协议组是官方一组：CK0=100.41 Ah（约 98.44%/102 Ah）公开，CK1–CK7 仅有日期而无真值。不能据此报告组级容量误差。没有把旧研究的预测 CSV、合成组、候选包中的 `sample_data` 复制件或同一物理组的多次脉冲当新组。

资格标准来自本轮 `START_PROMPT.md` §3–4 与官方 `data/DATA_DESCRIPTION.md`：D2-compatible 需要**未参与选择的新物理组**，四串 LFP、相符的满充后 5.1 A 放电至**组端首次 11.2 V**的容量标签和可审查时点。独立但异拓扑、化学、温度/倍率或容量定义者至多为限定 D2-transfer，且需原始标签口径、实体及划分审计；单有 `SOH` 列不够。D0/D1 开发结果不能作独立确认。

本次查了根目录 `data/`、`dataset original/`、`Che-Dataset3.mat`、`TU Darmstadt/`，以及相关 `research/phase2_*` 的数据、输出与文献缓存和 `/Users/shane/Desktop/项目/Current State_Challenge1/`。`data/operation/` 有 13 段，`TU Darmstadt/` 有 28 个系统 CSV。代表原始列、官方 README、既有 `outputs/dataset_registry.csv` 与 `notes/workstreams/C_DATA_QUALIFICATION.md` 已复查。没有下载或执行外部 pickle。该搜索是本地清单审计，不能证明互联网上不存在新的合格数据。

| 数据 | 资格与理由 |
|---|---|
| P1/D0 与 D1 v1.5 | 同六枚 102 Ah 单芯，D1 是从 P1 深充记录按首次实测 3.50 V 越线严格裁剪的浅充**代理**；180 目标和不同历史设定不增加物理实体。P1 0.5/1C 单芯放电容量与官方 C/20 四串组端截止不同。已经反复开发，只有代理开发/反证资格。 |
| Che Dataset 3 v9 | 11 枚独立 LFP 单芯，有派生 `Capacity`、`Workingprofile`、`Partial_Q` 等；发布口径是全充入量归一化的 SOH，不等于官方放出 Ah/102。且前轮做过形状审计。可作异协议形状开发，不能作封存 D2。 |
| TU/BattGP | 28 套 8S LFP 系统，各有运行电压、电流、SOC、温度和八芯电压；无可核的配对周期参考容量。SOC 与阻抗目标不能冒充容量标签。只适合机制、组内差异与质量门控。 |
| 官方 CK0/CK1–7 | 一套 4S 组，CK0 曲线和容量是真锚点；CK1–7 仅时点/运行前缀公开。四芯同组不能当四个独立组；隐藏真值不能本地评价容量。 |
| He ESSL1 | 本地 ZIP 内六芯 pickle 和**一套 16S pack** pickle；既有安全 opcode 审计见到 `SOH`/`rate_capacity (Ah)` 字段，但未核容量测量条件或许可。即使核实真值，拓扑不符且仅一个组；当前为条件候选，不列已合格 D2-transfer。 |
| Xu 1P10S、Yagci 180 Ah | 目前分别为发布记录/README 级。Xu 一套 10S 53 Ah 模组，文献所述 1C 校准；Yagci 12 枚单芯、35/50°C，原始大包未取代表 RPT。均不能升 D2；取得原始数据并核真值后可考虑限定迁移。 |
| Deng 车辆、Bilfinger 车辆 | 前轮已有记录：NCM 车端全充 Ah 或车端充电能量目标，与本题放电 Ah 不同；只有机制/方法压力测试资格，不能计作新四串标签。 |

下一步应在任何外层容量误差查看前冻结新数据来源、去重实体、组级分割和标签温度/倍率/截止；若无新组，R02/R05 仍可做 D1 代理、CK0/官方前缀、合成机制及程序验证，组容量确认状态保持 `not_testable`。`outputs/data_eligibility.csv` 记录逐源资格和代表文件 SHA256；哈希的是本次实际读到的文件字节，目录/远端元数据没有被伪装成已验证原始包。大源仅取代表文件哈希，完整输入清单须另由 V0 主线建立。
