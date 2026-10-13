# phase2_v2_phase_matched_20261013

V2 容量估计：在 V1（检查后完整充电锚点 + 石墨台阶位移）的基础上，月内更新只比较同温度、同相位（月末 45 °C）的台阶，β 由充电方向的 LLI 份额给出。结论见 [FINAL_REPORT.md](FINAL_REPORT.md)，协议见 [protocol.json](protocol.json)（哈希在 `protocol.sha256`）。

| 路径 | 内容 |
|---|---|
| `src/v2.py` | 研究实现：月份划分、月末 45 °C 值、速率、β（A4 / 直接标定）、V2 预测器 |
| `stage_v2_eval.py` | 因果预测 + 代理评估 + 门 H2–H5 |
| `stage_v2_candidate.py` | 候选类按 run_model.py 方式运行，检查 H1、H6，sample_data 冒烟 |
| `candidate_model/anchor_step_v2_model.py` | 可接入框架的候选类 `MyModel`（只依赖 numpy / pandas，尚未接入正式提交） |
| `outputs/` | 全部结果 |

依赖：复用 `../phase2_anchor_step_20261013/src/events.py` 与其 requirements；数据与框架来自 `TechArena_Challenge2_Team_Package/`。

```bash
cd research/phase2_v2_phase_matched_20261013
python3 stage_v2_eval.py && python3 stage_v2_candidate.py
```
