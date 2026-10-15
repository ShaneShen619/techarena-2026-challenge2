<a id="en"></a>

# Round 5C — Fixing the stress model's cold start

> **Language:** English · [中文](#zh)

Branch `exp/phase2-r5c-stress-fix-20261015`. This round continues round 5A's stress-history model and fixes its CK1 cold start under strict, pre-registered rules. A new cold-start test scenario was added for this.

**Result.** In the causal tests (pseudo and cold-start), the two-term law with step information for the not-yet-anchored month clearly beats V2.

- Cold start: MAE 0.144 vs V2's 0.252.
- Pseudo: MAE 0.119 vs V2's 0.240.

The ensemble R3_TD_w0.75 (0.75 × stress model + 0.25 × V2) passes every gate on the real proxies: MAE 0.131 vs V2's 0.216 at Δ = 0.4, max error 0.44 vs 0.67. Its CK1 value, however, relies on an exposed correction. A candidate class is ready and validated on a copy of the package; the real package is unchanged. Read [FINAL_REPORT.md](FINAL_REPORT.md).

| Path | Content |
|---|---|
| [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md) | execution brief |
| [FINAL_REPORT.md](FINAL_REPORT.md) | final report |
| [notes/](notes/) | STATUS and DECISIONS |
| [src/](src/) | copied 5A modules, `smodel5c.py` (law fits), `runner5c.py` (cold-start scenarios), `preds5c.py`, `checks5c.py` |
| [stage_0/](stage_0/) | reproduction and cold-start protocol and baselines |
| [stage_1/](stage_1/) | round 1 protocol, Challenge 1 two-term prior, results |
| [stage_2/](stage_2/) | round 2–3 diagnoses, protocols, results |
| [stage_3/](stage_3/), [stage_3_check.py](stage_3_check.py) | candidate checks and packaging log |
| [candidate_model/](candidate_model/) | `r5c_stress_ensemble_model.MyModel` (numpy/pandas) |

---

<a id="zh"></a>

# 第五轮 C——修复应力模型的冷启动

> **语言：** [English](#en) · 中文

分支 `exp/phase2-r5c-stress-fix-20261015`。本轮延续第五轮 A 的应力历史模型，在严格的预登记规则下修复它在 CK1 的冷启动问题，并为此新增了冷启动检验场景。

**结果。** 在因果检验（伪场景和冷启动）中，两项定律加上"尚无锚点月份的台阶信息"明显优于 V2：

- 冷启动：MAE 0.144，V2 为 0.252；
- 伪场景：MAE 0.119，V2 为 0.240。

集成 R3_TD_w0.75（0.75 × 应力模型 + 0.25 × V2）在真实代理上通过了全部门槛：Δ = 0.4 时 MAE 0.131（V2 0.216），最大误差 0.44（V2 0.67）。但它在 CK1 上的数值依赖一个已曝光的修正。候选类已准备好，并在提交包副本上验证通过；真实提交包没有改动。请读 [FINAL_REPORT.md](FINAL_REPORT.md)。

| 路径 | 内容 |
|---|---|
| [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md) | 执行任务书 |
| [FINAL_REPORT.md](FINAL_REPORT.md) | 最终报告 |
| [notes/](notes/) | STATUS 与 DECISIONS |
| [src/](src/) | 复制的 5A 模块、`smodel5c.py`（定律拟合）、`runner5c.py`（冷启动场景）、`preds5c.py`、`checks5c.py` |
| [stage_0/](stage_0/) | 复现与冷启动协议及基线 |
| [stage_1/](stage_1/) | 第一轮协议、Challenge 1 两项定律先验、结果 |
| [stage_2/](stage_2/) | 第二、三轮诊断、协议、结果 |
| [stage_3/](stage_3/)、[stage_3_check.py](stage_3_check.py) | 候选检查与打包日志 |
| [candidate_model/](candidate_model/) | `r5c_stress_ensemble_model.MyModel`（numpy/pandas） |
