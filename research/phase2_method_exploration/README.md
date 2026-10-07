# 第二阶段多路线研究目录

从 [醒来摘要](outputs/EXECUTIVE_SUMMARY.md)进入；完整结论和证据边界见 [中文报告](outputs/LFP_SOH_多路线设计验证与比较报告.md)。本目录执行了 `START_PROMPT.md` 的 M0–M10 多路线研究；数据与模型仍未得到官方 CK1–CK7 容量真值确认。

- `notes/PROTOCOL.md`、`configs/acceptance.json`：冻结目标与输入预算；v1.4 的完整事件入选错误及 v1.5 纠正见 `notes/DECISIONS.md`、`notes/M9_FINDINGS.md`。
- `data_manifests/d1_v15_target_visibility.csv`、`d1_v15_cropped_events.csv`：严格模拟浅充前缀可见性与模型输入；独立前缀扫描在 `runs/M9_prefix_stop_replay_v2/`。
- `runs/M9_D1_v15_endpoint_3p45_v1/`、`runs/M9_D1_v15_endpoint_3p55_v1/`：另两个终点按首次越线严格重扫的输入与审计；对应五种基线的逐点文件见 `REPRODUCE.md`。
- `notes/M1_FINDINGS.md` 至 `M9_FINDINGS.md`：按模块的假设、运行、负结果和适用范围。旧 M2/M3/M7/M8 文首已注明 v1.4 D1 数值退役。
- `outputs/method_comparison.csv`、`outputs/predictions_long.csv`：按证据层、输入预算、标签口径分开的逐方法和逐点比较。D1 v1.5 是当前主开发基准，D1 v1.4 仅历史回顾；D3 隐藏容量没有虚构误差。
- `outputs/official_predictions.csv`、`outputs/official_diagnostics.csv`：官方 CK0–CK7 合法前缀预测及分支。CK1–CK7 真值隐藏。
- `outputs/event_catalog.csv`：41 条认证的官方标准放电脉冲目录，含起止、前序充电/静置、温度、质量、模态和拒绝原因；原始审计在 `runs/M1_certification_v2/event_certification.csv`。
- `outputs/acceptance_results.json`：硬正确性、D1 高目标、D2、官方真实验证和研究闭环分开计的验收字段。
- `outputs/MEASUREMENT_PLAN.md`：为解决真实浅循环四串容量缺口而建议的可实施新测量。
- `candidates/ck0_hold/`、`candidates/exploratory_fallback/` 与 `outputs/*research_candidate.zip`：两个通过干净提取接口验证的研究包，不代表官方容量精度已验证。
- `notes/EXPERIMENT_INDEX.csv`、`notes/FAILURES.md`：108 条已登记运行及保留的失败/修正；`REPRODUCE.md` 给出核验命令。
