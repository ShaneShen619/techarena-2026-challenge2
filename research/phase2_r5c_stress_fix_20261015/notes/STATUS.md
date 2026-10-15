<a id="en"></a>

# STATUS (round 5C)

> **Language:** English · [中文](#zh)

**All stages finished (0-4); three design rounds run; none capped.**

Start: 2026-10-15. Branch `exp/phase2-r5c-stress-fix-20261015`, worktree `/Users/shane/Desktop/Arena_1015_r5c_stressfix`.

| Stage | State | Notes |
|---|---|---|
| 0 setup, reproduction, CS | done | V2/M4/S_main/ENS50 reproduced; CS mean MAE: V2 0.252, S_main 0.287, ENS50 0.220 |
| 1 design round 1 | done | main D4_D2_w0.5: MAE .087/.143/.199, MAX .864 at d0.8 -> fails G-proxy; no registered design passes; round 2 opened |
| 2 rounds 2-3 | round 2 done (main R2_D_w0.75 fails G-proxy at d0.8; R2_B pseudo .119 / cold .144); round 3 done: R3_TD_w0.75 passes every gate (exposed-CK1) | |
| 3 candidate | done | R3_TD_w0.75: G-causal/G-impl pass (py3.13, py3.11, diff 0.0, ~29 s); validate_submission PASSED on package copy |
| 4 final report | done | FINAL_REPORT.md, README.md; targets T2/T4/T6 met, T1/T3/T5 missed |

---

<a id="zh"></a>

# 状态（第五轮 C）

> **语言：** [English](#en) · 中文

**全部阶段（0–4）已完成；共进行三轮设计；没有阶段到达上限。**

开始：2026-10-15。分支 `exp/phase2-r5c-stress-fix-20261015`，worktree `/Users/shane/Desktop/Arena_1015_r5c_stressfix`。

| 阶段 | 状态 | 说明 |
|---|---|---|
| 0 准备、复现、CS | 完成 | 复现 V2/M4/S_main/ENS50；CS 平均 MAE：V2 0.252、S_main 0.287、ENS50 0.220 |
| 1 第一轮设计 | 完成 | 主模型 D4_D2_w0.5：MAE .087/.143/.199，Δ0.8 时 MAX .864 -> 未过 G-proxy；无登记设计通过；开启第二轮 |
| 2 第二、三轮 | 第二轮完成（主模型 R2_D_w0.75 在 Δ0.8 未过 G-proxy；R2_B 伪场景 .119 / 冷启动 .144）；第三轮完成：R3_TD_w0.75 通过全部门槛（已曝光 CK1） | |
| 3 候选 | 完成 | R3_TD_w0.75：G-causal/G-impl 通过（py3.13、py3.11，差 0.0，约 29 s）；提交包副本上 validate_submission 通过 |
| 4 最终报告 | 完成 | FINAL_REPORT.md、README.md；达成 T2/T4/T6，未达成 T1/T3/T5 |
