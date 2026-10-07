# LFP SOH 第二阶段下一轮研究

本目录执行 2026-09-29 版 `START_PROMPT.md`，按 R0→R6 完成数据与环境检查、最佳微调 TCN 配对消融、浅充反事实、官方脉冲预测、四串状态可辨识、独立测量方案和官方候选硬测试。

阅读顺序：

1. `outputs/EXECUTIVE_SUMMARY.md`：一分钟结论。
2. `outputs/LFP_SOH_下一轮逐路线验证与决策报告.md`：完整技术报告。
3. `outputs/acceptance_results.json`：机器可读验收。
4. `outputs/method_comparison.csv` 与 `outputs/predictions_long.csv`：统一指标和逐点结果。
5. `outputs/measurement_plan.md`：获得真实四串结论所需的测量。
6. `REPRODUCE.md`：复现命令。

当前结论：D1 平均最优仍为 2.851 pp，高性能目标未达；温度对 D1 代理有增量，电压波形容量增量未成立；脉冲可以预测未来电压但没有容量证据；官方 CK1–CK7 容量准确度未验证。安全备选为 `candidates/ck0_hold`，探索候选为 `candidates/exploratory_fallback`。根目录 ActiveModel 仍为 ExampleModel。
