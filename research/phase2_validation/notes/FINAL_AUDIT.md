# 最终交付与科学审计

2026-09-28。工程与研究流程验收结果：**PASS，附明确科学边界**。自动检查细节及当前报告/Word SHA256 见 `final_audit.json`；`scripts/final_audit.py` 实际重算 29 项检查，全部通过。独立读者按七个问题审阅报告，均能找到结论；其建议的标签公式、A 参数和单芯适配、B 逐门漏斗、CK0 采样率、模拟统计范围已补入最终版。读者测试并不替代四串组容量真值。

## 逐项验收

| 交付条件 | 状态与证据 |
| --- | --- |
| M0 原始材料与协议 | PASS。官方入口/数据原始 31 文件 SHA256 重算一致；第一阶段、Che、TU 的 94 个原始文件大小和修改时间与验收清单一致；协议在误差结果前冻结于 `PROTOCOL.md`。 |
| 双候选实现 | PASS。`candidates/route_a/`、`route_b/` 有独立模型/依赖/说明；各自 11 个官方入口、框架及 sample_data 文件与原始字节一致，根目录 ActiveModel 未切换。 |
| E0 科学与因果正确性 | PASS。干净 venv `pip check` 和 12 项 pytest 通过；覆盖积分、跨阈值插值、缺口/重复、NaN、空前缀、计数器重置、未来扰动、`fit(full)` 对 `fit(prefix)`、调用顺序和 pickle 跨进程，以及 B 高/低信息正反例。 |
| 官方接口 E1 | PASS。A/B 各在全量官方 data 上 train 和八检查点 test 成功；两套 ZIP 在新 venv 解包后，各自官方 sample validator 通过。`outputs/predictions_official.csv` 有 B0/B1/B2/A/B 各八行，CK1–CK7 真值字段全空。 |
| 官方 B 漏斗 | PASS。CK7 前缀 1,016 个事件 = 527 个不足 5 Ah + 142 个温度不匹配 + 347 个进入拟合；进入拟合者 168 个异常容量跃迁、99 个边界解、80 个信息不足，零接受。5 次长缺口为可重叠诊断，不重复计入。逐 CK 见 `outputs/route_b_rejection_funnel.csv`。 |
| 第一阶段 E3-P1 | PASS。六物理芯 × 早中晚 3 检查点，54 行 B0/A/B 预测；输入结束均早于目标放电开始。18 个真实目标 A/B/B0 MAE 分别 10.57/15.27/14.86 SOH pp；六芯 cluster bootstrap 的 A-B 配对区间跨零。标签是单芯高倍率放电，不是四串 C/20。 |
| 独立模拟 E2 | PASS。20 种子 × 四机制 × 三后续阶段 × 三方法 = 720 行；真值由独立 5.1 A 至 11.2 V 放电求得，生成器双 RC/滞后与 B 单 RC 不同。压力测试为 20 种子 × 14 场景 × 两方法 = 560 行，覆盖 10/20/30/60 s、丢样、传感器/电流偏置、曲线漂移等。 |
| 消融与外部补充 | PASS。E2 260 行消融、第一阶段 108 行 A 消融；Che 33 点同次充电诊断，TU 三系统九窗口共 90 万行信号诊断。Che/TU 未被冒充为官方容量评分。 |
| 文档与复现 | PASS。同名 Markdown/Word、`NEXT_STEPS.md`、`REPRODUCE.md`、全部 CSV/图与本审计齐全。Word 用 documents renderer 生成 `runs/report_render_v6/` 的九页 PNG/PDF；逐页检查字形、图表、分页、链接与截断，最后一页非空。 |

## 保留的失败与限制

- A 首轮把约 100 Ah 深充与约 21 Ah 浅补电配同一参考，CK1 假降至约 60%；原首轮输出仍在 `runs/A_official/`。修复依赖官方无标签事件的物理解释，**未凭隐藏标签调参**。
- B 首轮准 OCV 量化斜率与边界更新使第一阶段 18 点 MAE 约 25.47 pp；原首轮预测在 `runs/phase1_sixfold_v1/`。修复后 15.27 pp 仍不优于常数 14.86 pp。官方运行的零更新是能力不足的证据，不能包装成成功追踪。
- 六个第一阶段电芯曾参与旧项目开发；修复后同芯再测只算留芯开发验证。第一阶段 0.5C/1C 单芯 2.5 V 标签与官方 C/20 四串 11.2 V 标签不可混同；A 的优势还需未见过的组级验证。
- Che MAT 没有可核实的原始 t/I/V 与显式电压网格，只有同次充电形状补充；TU 没实测容量标签，不计算容量 MAE。Che 101 点与论文 3.3–3.5 V/2 mV 的对应仅为文献推断。
- 官方 CK1–CK7 真值按赛题隐藏，无法从原始包补下载。本轮没有外部提交或反馈反演。故**方法实现与既定验证工作完成，官方隐藏精度未获证实**。最有信息价值的下一步是冻结方法后拿独立四串组的检查前前缀和实际 C/20 容量作留组测试。

## 本机执行证据

干净环境路径 `preflight/final_clean_venv/`，软件版本见 `requirements.lock.txt`；离线 wheels 为 macOS ARM64，本机结果不声称 Linux 等价。两套本地 ZIP、解包目录与 validator 日志在 `runs/package_check/`。A 全量八点 test 约 12 s，B 约 23 s；正式评分机硬件和耗时未知。最终 Word 是 `outputs/LFP_SOH_双方案设计验证与比较报告.docx`；可编辑 Markdown 和逐点 CSV 同在 `outputs/`。所有脚本入口及执行顺序见 `REPRODUCE.md` 和 `EXPERIMENT_INDEX.csv`。
