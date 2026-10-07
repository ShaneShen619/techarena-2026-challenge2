# 下一步执行顺序（2026-09-29）

1. **冻结评价契约和测量规格。**确认官方 `fit`/`estimate_soh` 信息边界；取得电流/电压/温度精度、同步与 CK0 容量重复性。读取 `OFFICIAL_CONSTRAINTS.md`、`runs/L0_measurement_20260929/result.json`。若拿不到规格，以假设范围做敏感性，不将其称实测。
2. **完成 R02 最小原型与识别性门控。**用 CK0 5.1 A 带载模板、组端 11.2 V 首次根、已结束事件、容量一维和有界 nuisance 参数，输出 `Q` 剖面、事件一致性和拒绝原因。先检验公式/单位/模拟区分能力及固定模型删未来反事实，再使用任何 D1 容量代理。代码设计见 `route_cards/R02.md`，不承诺官方准确率。
3. **尽早采集新 D2。**以新物理四串组的同协议容量 RPT 为主；在试点估组间方差和重复测量噪声后确定样本量与封存组。每组需要多个寿命点与末期覆盖。若短期没有 D2，R02 只可报告可辨识性/电压机制，R01 作为容量输出回退。
4. **并行做 R05 的温度机制分离。**同组短时跨温并复位状态测试可逆电压/可用量；不同老化热暴露组统一参考温度 RPT 测不可逆容量。比较时间、Ah、箱温、实际芯温及热历史同预算基线，重视末期最差组。不能把两温 Arrhenius 直接外推。
5. **次序进入其他方向。**R03 先证明真实浅充与后验裁窗的差异；R04 用 D2 检验脉冲容量增量；R06/R09 先做诊断与复测触发；R07 仅在 R02 的一维容量可辨且有额外约束后增加独立 `Q_i`；R08 只有简单路线显示可用信息且组级监督充足才投入。所有路线的否定/回退条件在 `EXPERIMENT_ROADMAP.md`。

本轮旧文献调查资料若被替换，旧 `notes/` 仍是历史记录；本轮证据、原文定位、路线卡和审查在 `research/phase2_literature_reassessment/`。任何来自 TU、Che、P1、He、Xu、Yagci 的结果均须照 `dataset_registry.csv` 标明目标量和迁移限制。

新队友的最短文件导航（以下相对本轮目录）：`OFFICIAL_CONSTRAINTS.md` 核官方标签及严格前缀；`PROJECT_EVIDENCE_AUDIT.md` 核旧实验的输入/输出/未验证边界；`route_cards/R02.md` 查看公式和 `fit`/`estimate_soh` 伪代码；`outputs/EXPERIMENT_ROADMAP.md` 的 E1 冻结表及 D2 一页记录模板用于实施；`outputs/dataset_registry.csv` 查外部数据资格；`runs/L0_measurement_20260929/result.json` 与 `runs/L6_window_table_20260929/result.json` 复查本轮轻量重算；`outputs/REPRODUCE.md` 给重建命令。未取得仪表规格、R02 数值阈值和 D2 真标签前，可做原型及反证，不可把盲验或容量目标写成已完成。
