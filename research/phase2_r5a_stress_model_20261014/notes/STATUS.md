<a id="en"></a>

# STATUS (round 5A)

> **Language:** English · [中文](#zh)

Start: 2026-10-14. Branch `exp/phase2-r5a-stress-model-20261014`, worktree `/Users/shane/Desktop/Arena_1014_r5a_stress`.

| Stage | State | Notes |
|---|---|---|
| 0 setup | done | V2 0.215726/0.669052, M4 0.291265 reproduced (stage0/reproduce.json) |
| 1 stress extraction | done | extrapolation error <= 1.7 eff-days except CK6 month (4.2) |
| 2 prior | done | z at bound 0.2; Ea and A from Yagci fallback (prior.json) |
| 3 pack model | done | no model passes; S_main eps-free 0.192 / pseudo 0.131 but CK1 -1.13 (prior only) |
| 4 CK2 analysis | done | seg-3 extrapolation accurate (+3 % Ah, -0.013 pp); CK2 error is law shape; H-A weak/inconclusive |
| 5 final report | next | |

---

<a id="zh"></a>

# 状态（第五轮 A）

> **语言：** [English](#en) · 中文

开始：2026-10-14。分支 `exp/phase2-r5a-stress-model-20261014`，worktree `/Users/shane/Desktop/Arena_1014_r5a_stress`。

| 阶段 | 状态 | 说明 |
|---|---|---|
| 0 准备 | 完成 | 复现 V2 0.215726/0.669052、M4 0.291265（stage0/reproduce.json） |
| 1 应力提取 | 完成 | 外推误差 <= 1.7 个有效天，CK6 那个月除外（4.2） |
| 2 先验 | 完成 | z 撞界 0.2；Ea 与 A 回退到 Yagci（prior.json） |
| 3 电池组模型 | 完成 | 无模型通过；S_main 与 ε 无关 0.192 / 伪场景 0.131，但 CK1 −1.13（仅先验） |
| 4 CK2 分析 | 完成 | 第 3 段外推准确（Ah +3 %，−0.013 pp）；CK2 误差来自定律形状；H-A 弱 / 无定论 |
| 5 最终报告 | 下一步 | |
