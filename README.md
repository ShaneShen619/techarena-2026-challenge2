<a id="en"></a>

# TechArena 2026 Challenge 2 — Post-Checkup Full-Charge Anchor + Graphite-Step Model

> **Language:** English · [中文](#zh)

Branch `exp/phase2-anchor-step-20261013`. This branch builds on `main`, which holds the official submission template. It adds only the new capacity estimator from 2026-10-13 and its validation.

## What the model does

It estimates the SOH of a 4 × 102 Ah LFP series pack on each checkup date. SOH is the checkup-protocol capacity divided by 102 Ah.

- **Anchor.** After every monthly checkup, the pack is charged from near empty to the end of the 14.0 V CV phase. The charged Ah is almost exactly the usable capacity at that time. To predict a checkup, the model uses the latest such charge before it as the anchor.
- **In-month update.** Roughly every 5 days, a fixed program discharges about 56 Ah below full and crosses the graphite staging step. The Ah distance from the step to the top of charge shrinks with loss of lithium inventory, so it tracks the capacity change after the anchor.

The proxy label is the post-checkup full charge plus an offset. On it, the strictly causal prediction error is about 7 % (MAE) of the official ExampleModel's. The proxy is not the hidden truth, and the official accuracy is still unverified. See the [validation report](research/phase2_anchor_step_20261013/FINAL_REPORT.md).

## Layout

```
.
├── README.md                              this file
├── .gitignore
├── TechArena_Challenge2_Team_Package/     submission package (official template + wired-in V2 + temperature-weighted √t gap model)
│   ├── framework/  run_model.py  validate_submission.py   official framework, do not modify
│   ├── my_model/                          active model entry (MyModel = V2 + temperature-weighted √t gap branch)
│   ├── README.md  REPORT.md               submission write-up and report
│   ├── data/                              official operating data and CK0 checkup data
│   ├── sample_data/                       small sample used by the validator
│   └── requirements.txt                   submission dependencies (numpy, pandas)
└── research/
    ├── phase2_anchor_step_20261013/       V1 study
    │   ├── README.md                      reproduction steps, environment, file guide
    │   ├── FINAL_REPORT.md                validation report
    │   ├── EXECUTION_PROMPT.md            execution brief
    │   ├── candidate_model/               candidate model AnchorStepModel
    │   ├── src/  stage_*.py               research code and stage scripts
    │   └── outputs/  figures/             results
    ├── phase2_v2_phase_matched_20261013/  V2 study (phase-matched step differencing + physics β)
    │   ├── FINAL_REPORT.md  protocol.json validation report and frozen protocol
    │   ├── candidate_model/               candidate class MyModel (V2)
    │   └── src/  stage_v2_*.py  outputs/  research code, scripts and results
    ├── phase2_rebound_diagnosis_20261015/ diagnosis of the post-checkup step offset
    └── phase2_v3_20261015/                V3 study (√t gap + β cap + median), submission checks,
                                           packaging script, comparison with r5c
external_data/                             open datasets (raw files git-ignored): DATA_MANIFEST.md,
                                           data_manifest.json, _screening/ scripts and outputs
```

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r research/phase2_anchor_step_20261013/requirements.txt
cd research/phase2_anchor_step_20261013
python3 stage_a_events.py && python3 stage_bcd_causal_eval.py && python3 stage_e_robustness.py \
  && python3 stage_f_candidate.py && python3 stage_g_figures.py
```

To see only the candidate's per-checkup output, run `stage_bcd_causal_eval.py` and then `stage_f_candidate.py`. The result is in `outputs/F_candidate_predictions.csv`.

## Current status

- **Temperature-weighted √t (T_main) replaces the calendar-time √t branch (2026-10-17).**
  - The √t gap branch now uses Arrhenius-weighted 45 °C-equivalent time (Ea 20.6 kJ/mol; checkup gaps at 25 °C; missing segment 3 at 45 °C). Only CK2 changes: 94.451 → 94.507.
  - Evidence: round 7 WP2 (branch `exp/phase2-r7-lit-checks-20261016`). It passes every registered gate. On the causal one-month gap cases the error falls 0.113 → 0.105 pp (pseudo 0.148 → 0.144, cold start 0.174 → 0.170). Real proxy MAE Δ0/0.4/0.8 = 0.197 / 0.126 / 0.146, MAX 0.609 / 0.228 / 0.228.
  - **Zip rebuilt:** `~/Desktop/Current State_Challenge2.zip`, validated from a clean extraction under Python 3.11.14 + numpy 2.4.6 / pandas 3.0.6. The previous zip is kept as `Current State_Challenge2_backup_V2sqrt_20261015.zip`.
- **V2 + √t gap branch was wired into the submission (2026-10-15; superseded by T_main above).**
  - `MyModel` is V2 plus one change: when the last visible deep discharge is more than 10 days before the checkup (only CK2, because segment 3 is missing), the loss since the previous anchor is extrapolated with √t since CK0. Only CK2 changes (95.137 → 94.451).
  - Proxy MAE at Δ = 0 / 0.4 / 0.8 is 0.207 / 0.123 / 0.140 pp; V2 alone gave 0.272 / 0.216 / 0.210. The √t branch was chosen after seeing CK2, so this is exposed-exploratory. See [research/phase2_v3_20261015/FINAL_REPORT.md](research/phase2_v3_20261015/FINAL_REPORT.md). V3 as registered (adding a β cap and a 4-cell median) is **not** the recommended version.
  - Checks: the output matches the research implementation to within 0.0004 pp; noise causality holds on all 8 checkups; 320 reduced-budget calls give no error.
  - **Zip:** `~/Desktop/Current State_Challenge2.zip` was built with `research/phase2_v3_20261015/package_submission.py` (team Current State; Mona Zhu, Zhikuan Shen). From a clean extraction it passed `validate_submission.py` with Python 3.11 + numpy 2.4.6 / pandas 3.0.6 and + numpy 1.24.4 / pandas 2.0.3. The full-data outputs were identical in both. Python 3.12 is untested.
  - **Still open:** the presentation in the zip is the official template (placeholder). Nothing has been submitted yet.
  - **Comparison:** the r5c candidate (branch `exp/phase2-r5c-stress-fix-20261015`) is roughly tied on the real proxies. It is better on the cut and cold-start scenarios: pseudo 0.123 vs 0.148, cold start 0.134 vs 0.175 ([compare_with_r5c.py](research/phase2_v3_20261015/compare_with_r5c.py)).
- **V1** ([research/phase2_anchor_step_20261013/](research/phase2_anchor_step_20261013/)) was the active model until 2026-10-14 and remains in git history (commit `60a602d`).
- **Further alternatives** were tested on branches `exp/phase2-round3-models-20261014`, `exp/phase2-round4-signals-20261014`, `exp/phase2-r5a-stress-model-20261014`, `exp/phase2-r5b-electrode-model-20261014` and `exp/phase2-r5c-stress-fix-20261015`.
- **Main risks.** These are covered in the risk section of both reports:
  - **The offset ε.** This is the offset between the checkup protocol and the operating charge. Open data suggest it drifts by about −0.03 Ah per Ah of fade, so late estimates may read up to about 0.3 pp high.
  - **The post-anchor step offset.** It is +0.4–0.46 Ah and constant across months; most likely it is a measurement effect.
  - **The √t assumption at CK2.**
  - **CK1's sensitivity to the ratio assumption.**

## Related branches

| Branch | Contents |
|---|---|
| `main` | official submission template |
| `exp/phase2-anchor-step-20261013` | this branch: main + new model (V2 + √t wired into the package; V1 and V2 in history) |
| `exp/phase2-r5c-stress-fix-20261015` | stress-model + V2 ensemble candidate R3_TD_w0.75 (not wired) |
| `research-archive-20261010` | all other research up to 2026-10-13 (literature, earlier experiments, failed-route reports, diagnostics) |

---

<a id="zh"></a>

# TechArena 2026 Challenge 2 — 检查后完整充电锚点 + 石墨台阶模型

> **语言：** [English](#en) · 中文

分支 `exp/phase2-anchor-step-20261013`。本分支在 `main`（官方提交模板）之上，只加入 2026-10-13 的新容量估计模型及其验证。

## 这个模型做什么

估计 4×102 Ah LFP 串联电池组在每个检查点日期的 SOH（检查协议容量 ÷ 102 Ah）。

- **锚点**：每次月度检查之后，电池组都会从近空完整充到 14.0 V CV 末端，充入量几乎就是当时的可用容量。预测某个检查点时，用它之前最近一次这样的充电作为锚点。
- **月内更新**：约每 5 天的固定程序会放电到满充以下约 56 Ah，越过石墨分阶台阶。台阶相对满充端的 Ah 距离随活性锂损失而缩短，用它跟踪锚点之后的容量变化。

在代理标签（检查后完整充电量 + 偏置）上，严格因果的预测误差约为官方 ExampleModel 的 7%（MAE）。代理不是隐藏真值，官方精度仍未验证。详见 [验证报告](research/phase2_anchor_step_20261013/FINAL_REPORT.md)。

## 目录结构

```
.
├── README.md                              本文件
├── .gitignore
├── TechArena_Challenge2_Team_Package/     提交包（官方模板 + 已接入的 V2 + 温度加权 √t 缺口模型）
│   ├── framework/  run_model.py  validate_submission.py   官方框架，不可修改
│   ├── my_model/                          正式模型入口（MyModel = V2 锚点 + 同相位台阶）
│   ├── README.md  REPORT.md               提交用方法说明与报告
│   ├── data/                              官方运行数据与 CK0 检查数据
│   ├── sample_data/                       validator 用的小样本
│   └── requirements.txt                   提交环境依赖（numpy、pandas）
└── research/
    ├── phase2_anchor_step_20261013/       V1 研究
    │   ├── README.md                      复现步骤、环境、文件说明
    │   ├── FINAL_REPORT.md                验证报告
    │   ├── EXECUTION_PROMPT.md            执行任务书
    │   ├── candidate_model/               候选模型 AnchorStepModel
    │   ├── src/  stage_*.py               研究代码与各阶段脚本
    │   └── outputs/  figures/             结果
    └── phase2_v2_phase_matched_20261013/  V2 研究（同相位台阶差分 + 物理 β）
        ├── FINAL_REPORT.md  protocol.json 验证报告与冻结协议
        ├── candidate_model/               候选类 MyModel（V2）
        └── src/  stage_v2_*.py  outputs/  研究代码、脚本与结果
```

## 快速开始

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r research/phase2_anchor_step_20261013/requirements.txt
cd research/phase2_anchor_step_20261013
python3 stage_a_events.py && python3 stage_bcd_causal_eval.py && python3 stage_e_robustness.py \
  && python3 stage_f_candidate.py && python3 stage_g_figures.py
```

只想看候选模型的逐检查点输出：运行 `stage_bcd_causal_eval.py` 后再运行 `stage_f_candidate.py`，结果在 `outputs/F_candidate_predictions.csv`。

## 当前状态

- **温度加权 √t（T_main）取代了日历时间 √t 分支（2026-10-17）。**
  - √t 缺口分支现在使用按 Arrhenius 加权的 45 °C 等效时间（Ea 20.6 kJ/mol；检查间隔按 25 °C；缺失的段 3 按 45 °C）。只有 CK2 变化：94.451 → 94.507。
  - 依据：第七轮 WP2（分支 `exp/phase2-r7-lit-checks-20261016`），通过全部登记门槛。因果一个月缺口案例上误差 0.113 → 0.105 pp（伪场景 0.148 → 0.144，冷启动 0.174 → 0.170）。真实代理 MAE Δ0/0.4/0.8 = 0.197 / 0.126 / 0.146，MAX 0.609 / 0.228 / 0.228。
  - **压缩包已重建：** `~/Desktop/Current State_Challenge2.zip`，从干净解压目录在 Python 3.11.14 + numpy 2.4.6 / pandas 3.0.6 下验证通过。旧包保留为 `Current State_Challenge2_backup_V2sqrt_20261015.zip`。
- **V2 + √t 缺口分支曾于 2026-10-15 接入正式提交（已被上面的 T_main 取代）。**
  - 改动：在 V2 基础上，最后一次可见的深放电距检查日超过 10 天时（只有缺第 3 段的 CK2），用 CK0 以来的 √t 外推上一锚点之后的损失。只有 CK2 变化（95.137 → 94.451）。
  - 代理 MAE（Δ = 0 / 0.4 / 0.8）：0.207 / 0.123 / 0.140 pp；V2 为 0.272 / 0.216 / 0.210。√t 分支是看过 CK2 之后才定的，属已曝光的探索性结果。详见 [research/phase2_v3_20261015/FINAL_REPORT.md](research/phase2_v3_20261015/FINAL_REPORT.md)。按登记版本的 V3（另加 β 上限和 4 芯中位数）**不是**推荐版本。
  - 检查：与研究实现的差异 ≤ 0.0004 pp；8 个检查点的噪声因果性检验全部通过；320 次数据缩减调用没有报错。
  - **压缩包**：`~/Desktop/Current State_Challenge2.zip`，由 `research/phase2_v3_20261015/package_submission.py` 生成（队名 Current State；成员 Mona Zhu、Zhikuan Shen）。从干净解压目录运行 `validate_submission.py`，在 Python 3.11 + numpy 2.4.6 / pandas 3.0.6 和 numpy 1.24.4 / pandas 2.0.3 下都通过，完整数据输出逐位一致。未在 Python 3.12 上测试。
  - **待办**：包里的演示文稿还是官方模板占位。尚未提交给组委会。
  - **对比**：r5c 候选（分支 `exp/phase2-r5c-stress-fix-20261015`）在真实代理上大致持平，在截断和冷启动情景上更好：伪情景 0.123 对 0.148，冷启动 0.134 对 0.175。
- **V1**（[research/phase2_anchor_step_20261013/](research/phase2_anchor_step_20261013/)）在 2026-10-14 之前是正式模型，保留在 git 历史中（提交 `60a602d`）。
- **更多备选方案**在分支 `exp/phase2-round3-models-20261014`、`exp/phase2-round4-signals-20261014`、`exp/phase2-r5a-stress-model-20261014`、`exp/phase2-r5b-electrode-model-20261014` 和 `exp/phase2-r5c-stress-fix-20261015` 上测试过。
- **主要风险**（见两份报告的风险一节）：
  - **偏置 ε**：检查协议与运行充电之间的偏置。外部数据显示它每衰减 1 Ah 约漂移 −0.03 Ah，后期估计可能偏高最多约 0.3 pp。
  - **锚点后台阶偏移**：+0.4–0.46 Ah，各月相同，最可能是测量效应。
  - **CK2 的 √t 假设。**
  - **CK1 对比例假设敏感。**

## 相关分支

| 分支 | 内容 |
|---|---|
| `main` | 官方提交模板 |
| `exp/phase2-anchor-step-20261013` | 本分支：main + 新模型（V2 + √t 已接入提交包；V1、V2 保留在历史中） |
| `exp/phase2-r5c-stress-fix-20261015` | 压力模型 + V2 集成候选 R3_TD_w0.75（未接入） |
| `research-archive-20261010` | 截至 2026-10-13 的全部其他研究（文献、历史实验、失败路线报告、诊断文档） |
