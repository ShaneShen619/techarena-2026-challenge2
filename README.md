# TechArena 2026 Challenge 2 — 检查后完整充电锚点 + 石墨台阶模型

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
├── TechArena_Challenge2_Team_Package/     提交包（官方模板 + 已接入的 V1 模型）
│   ├── framework/  run_model.py  validate_submission.py   官方框架，不可修改
│   ├── my_model/                          正式模型入口（MyModel = V1 锚点 + 台阶）
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

- **V1 已接入正式提交**：`TechArena_Challenge2_Team_Package/my_model/model_template.py` 中的 `MyModel` 即 `AnchorStepModel`，开关已切到 `MyModel`。在全新 Python 3.11 venv 中 `validate_submission.py` 通过；全量数据输出与 `outputs/F_candidate_predictions.csv` 逐位一致（numpy 1.24/pandas 2.0 与 numpy 2.4/pandas 3.0 下相同）。提交包的 README 与 REPORT.md 已按提交要求更新（队名、成员待填）。尚未打包 zip、尚未提交。
- **V2 候选**（[research/phase2_v2_phase_matched_20261013/](research/phase2_v2_phase_matched_20261013/)）：同相位 45 °C 台阶差分 + 物理 β，代理 MAE 0.29 → 0.22 pp，预登记门 H1–H6 全部通过（已曝光的探索性验证）。尚未接入正式提交。
- 主要风险：检查协议与运行充电之间的偏置 ε、检查后回弹、CK1 对比例假设敏感、CK2 缺第 3 段。见两份报告的风险一节。

## 相关分支

| 分支 | 内容 |
|---|---|
| `main` | 官方提交模板 |
| `exp/phase2-anchor-step-20261013` | 本分支：main + 新模型（V1 已接入提交包，V2 为候选） |
| `research-archive-20261010` | 截至 2026-10-13 的全部其他研究（文献、历史实验、失败路线报告、诊断文档） |
