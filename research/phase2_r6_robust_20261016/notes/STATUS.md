<a id="en"></a>

# STATUS (round 6)

> **Language:** English · [中文](#zh)

Branch `exp/phase2-r6-robust-20261016`, worktree `/Users/shane/Desktop/Arena_1016_r6_robust`.

| WP | State | Result |
|---|---|---|
| 0 setup, re-baselining | done | V2/SUB/R3_TD_w0.75/R2_B reproduced; archived submitted class = SUB within 0.0004 pp; ExampleModel computed (proxy MAE ~4.3 pp) |
| 1 robust selection | done | real grid: SUB (max regret 0.027); R3_TD_w0.75 best worst case / uniform E; causal grid favours stress ensembles (tie window wide) |
| 2 fusion | done | no design passes all gates; main F2_S_A fails (CK1 -0.56, CK2 -0.64); F1_S_A best fusion (causal better, real slightly worse); no candidate |
| 3 truth-oriented corrections | done | 3b drift: best worst-case and expectations (hedge, first probe); 3a start state up to 1.29 Ah, low confidence; 3c path effect verified 6/6 but contradicts proxies |
| 4 open-data prior | done (registered Yagci-unavailable fallback; past the 3 h cap) | prior3 = prior2; prior2 over-predicts LIC (+50 %) and Gotion (+24 %) loss; no candidate |
| 5 report material | done | 7 bilingual drafts in report_material/ (method, interpretability figure, open data, validation, negative results, slides, code audit) |
| 6 synthesis | next | |

---

<a id="zh"></a>

# 状态（第六轮）

> **语言：** [English](#en) · 中文

分支 `exp/phase2-r6-robust-20261016`，worktree `/Users/shane/Desktop/Arena_1016_r6_robust`。

| WP | 状态 | 结果 |
|---|---|---|
| 0 准备、重新确定基线 | 完成 | 复现 V2/SUB/R3_TD_w0.75/R2_B；归档的提交类与 SUB 相差不超过 0.0004 pp；已算出 ExampleModel（代理 MAE 约 4.3 pp） |
| 1 稳健选择 | 完成 | 真实网格：SUB（最大后悔值 0.027）；R3_TD_w0.75 最坏情况和均匀期望最好；因果网格偏向应力集成（并列阈值偏宽） |
| 2 融合 | 完成 | 无设计通过全部门槛；主模型 F2_S_A 失败（CK1 -0.56，CK2 -0.64）；F1_S_A 是最好的融合（因果检验更好，真实略差）；无候选 |
| 3 真值导向修正 | 完成 | 3b 漂移：最坏情况与期望最好（对冲，首个探测）；3a 起点最多 1.29 Ah，置信度低；3c 路径效应 6/6 证实但与代理冲突 |
| 4 开放数据先验 | 完成（按登记的 Yagci 不可用回退；已过 3 小时上限） | prior3 = prior2；prior2 高估 LIC（+50 %）和 Gotion（+24 %）的损失；无候选 |
| 5 报告材料 | 完成 | report_material/ 中 7 份双语草稿（方法、可解释性图、开放数据、验证、负面结果、演示、代码审计） |
| 6 综合 | 下一步 | |
