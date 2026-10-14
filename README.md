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
├── TechArena_Challenge2_Team_Package/     submission package (official template + wired-in V2 model)
│   ├── framework/  run_model.py  validate_submission.py   official framework, do not modify
│   ├── my_model/                          active model entry (MyModel = V2 anchor + phase-matched step)
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
    └── phase2_v2_phase_matched_20261013/  V2 study (phase-matched step differencing + physics β)
        ├── FINAL_REPORT.md  protocol.json validation report and frozen protocol
        ├── candidate_model/               candidate class MyModel (V2)
        └── src/  stage_v2_*.py  outputs/  research code, scripts and results
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

- **V2 is wired into the submission (2026-10-14).**
  - `MyModel` in `TechArena_Challenge2_Team_Package/my_model/model_template.py` is the V2 candidate class from [research/phase2_v2_phase_matched_20261013/](research/phase2_v2_phase_matched_20261013/): phase-matched 45 °C step differencing plus a physics β. The switch points at `MyModel`.
  - `validate_submission.py` passes in a fresh Python 3.11 venv.
  - The full-data output is identical to `outputs/V2_candidate_predictions.csv`, both with numpy 1.24 / pandas 2.0 and with numpy 2.4 / pandas 3.0.
  - Proxy MAE is 0.22 pp (V1: 0.29 pp). This is exposed-exploratory validation.
  - The submission README and REPORT.md describe V2. Team name and members are still to be filled in.
  - The zip has not been built and nothing has been submitted.
- **V1** ([research/phase2_anchor_step_20261013/](research/phase2_anchor_step_20261013/)) was the active model until 2026-10-14 and remains in git history (commit `60a602d`).
- **Further alternatives** were tested on branches `exp/phase2-round3-models-20261014` and `exp/phase2-round4-signals-20261014`; none beat V2.
- **Main risks.** These are covered in the risk section of both reports:
  - the offset ε between the checkup protocol and the operating charge
  - the post-checkup recovery
  - CK1's sensitivity to the ratio assumption
  - the missing segment 3 before CK2

## Related branches

| Branch | Contents |
|---|---|
| `main` | official submission template |
| `exp/phase2-anchor-step-20261013` | this branch: main + new model (V2 wired into the package; V1 in history) |
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
├── TechArena_Challenge2_Team_Package/     提交包（官方模板 + 已接入的 V2 模型）
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

- **V2 已接入正式提交（2026-10-14）**：`TechArena_Challenge2_Team_Package/my_model/model_template.py` 中的 `MyModel` 即 [research/phase2_v2_phase_matched_20261013/](research/phase2_v2_phase_matched_20261013/) 的 V2 候选类（同相位 45 °C 台阶差分 + 物理 β），开关指向 `MyModel`。在全新 Python 3.11 venv 中 `validate_submission.py` 通过；全量数据输出与 `outputs/V2_candidate_predictions.csv` 逐位一致（numpy 1.24/pandas 2.0 与 numpy 2.4/pandas 3.0 下相同）。代理 MAE 0.22 pp（V1 为 0.29 pp），属已曝光的探索性验证。提交包的 README 与 REPORT.md 已改为描述 V2（队名、成员待填）。尚未打包 zip、尚未提交。
- **V1**（[research/phase2_anchor_step_20261013/](research/phase2_anchor_step_20261013/)）在 2026-10-14 之前是正式模型，保留在 git 历史中（提交 `60a602d`）。
- **更多备选方案**在分支 `exp/phase2-round3-models-20261014` 和 `exp/phase2-round4-signals-20261014` 上测试过，没有一个胜过 V2。
- 主要风险：检查协议与运行充电之间的偏置 ε、检查后回弹、CK1 对比例假设敏感、CK2 缺第 3 段。见两份报告的风险一节。

## 相关分支

| 分支 | 内容 |
|---|---|
| `main` | 官方提交模板 |
| `exp/phase2-anchor-step-20261013` | 本分支：main + 新模型（V2 已接入提交包；V1 保留在历史中） |
| `research-archive-20261010` | 截至 2026-10-13 的全部其他研究（文献、历史实验、失败路线报告、诊断文档） |
