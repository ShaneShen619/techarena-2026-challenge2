# 温度改进 Goal 状态

当前模块：M7 最终冻结、验收和交付。六芯 P1 代理的全部数值硬门槛、七组科学/接口测试、两项独立审计高严重度修复、中文报告及候选包已完成。最终 Goal 状态以本轮 `outputs/acceptance.json` 及 Goal 工具返回值为准。

固定六物理电芯 × 30 点主面板 SHA256：`7188b662900f84312292a7062d6023e5eeb4f2e32798b6d61a3547ed40cdc59c`。最终宏 MAE 1.038663 pp、宏 RMSE 1.219001 pp、P95 2.680110 pp、最大误差 3.889631 pp、最差芯 MAE 1.737271 pp；旧 A 同面板宏 MAE 11.316887 pp，降幅 90.82%。固定最强基线 1.384132 pp。新增事件覆盖 172/180=95.56%，最弱芯 86.67%。+1°C/-1°C 新状态重放宏 MAE 1.035875/1.043924 pp，覆盖均 95.56%。

M1 温度面留芯运行均温 RMSE 1.001358°C，名义温度 7.230343°C。M2 参考修复宏 MAE 9.754979 pp，未达其中间 30% 改善，但定位剩余容量映射问题；后续 M4 多窗监督映射满足最终门槛。温度在同架构去温度 1.136754 pp 基础上的边际改善仅约 0.098 pp，属于已反复使用开发集上的观察。

官方四串 CK1–CK7 真值隐藏；全部落入域外降级分支，精度不可验证。原始 P1 深充和官方浅充之间有显著域差。TU 无容量标签，仅作信号压力诊断。新增四类充电曲线形状压力测试暴露降级方法脆弱性，未用于拟合或调参。关键审查记录在 `notes/FINAL_AUDIT.md`，独立重算在 `outputs/M7_independent_recompute.json`。

交付：`outputs/方案A_温度修复与提升报告.md`、`.docx`、`outputs/multi_temp_candidate.zip`、`REPRODUCE.md`、`runs/M7_frozen_manifest.json`。Word 已通过系统预览的四页目视检查和结构检查；本机缺打包渲染依赖、原生 Word PDF 导出超时，精确 Word 分页未认证，详见 `outputs/report_render/qa.json`。不得把 P1 开发误差写成官方成绩。

恢复命令：

```bash
bash research/phase2_validation/run_python.sh research/phase2_temperature_improvement/scripts/check_acceptance.py --require-pass
```
