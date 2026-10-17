<a id="en"></a>

# STATUS (round 8)

> **Language:** English · [中文](#zh)

| WP | State | Result |
|---|---|---|
| WP0 | done | SUB = T_main reproduced (MAE 0.197/0.126/0.146, pseudo 0.144, cold 0.170); submitted class = research = EXPECTED_SOH |
| WP1 | done | table_cases 423 rows; offset assertion passes; SUB real inc_resid CK1 +0.62 Ah, others within ±0.24 |
| WP2 | done | table_events 205 rows; 41 events and 6 variants match events_merged (≤3.6e-15 Ah); free-slope b = 0.745 [0.674, 0.765] |
| WP3 | done | table_anchors 8 rows; common 5.1 A cut = Q_fc (D3.1); 6 A cut removes 0.10–0.13 Ah; CV Ah 1.35→1.57; pulse R flat (quantised 0.049 mΩ) |
| WP4 | done | table_cycles 430 swings; profile repeats exactly per 116 h block, so cycle Ah carries no state (slot-matched spread ~0.001 Ah); only loaded voltages vary |
| WP5 | open | — |
| WP6 | open | — |

Next: WP5: register protocol (no slicing before commit). Last commit: see git log.

---

<a id="zh"></a>

# 状态（第 8 轮）

> **语言：** [English](#en) · 中文

| WP | 状态 | 结果 |
|---|---|---|
| WP0 | 完成 | SUB = T_main 复现（MAE 0.197/0.126/0.146，伪场景 0.144，冷启动 0.170）；提交类 = 研究实现 = EXPECTED_SOH |
| WP1 | 完成 | table_cases 共 423 行；offset 断言通过；SUB 真实 inc_resid CK1 +0.62 Ah，其余在 ±0.24 以内 |
| WP2 | 完成 | table_events 共 205 行；41 个事件和 6 个变体与 events_merged 一致（≤3.6e-15 Ah）；自由斜率 b = 0.745 [0.674, 0.765] |
| WP3 | 完成 | table_anchors 共 8 行；公共 5.1 A 截止 = Q_fc（D3.1）；6 A 截止去掉 0.10–0.13 Ah；CV 充电量 1.35→1.57 Ah；脉冲内阻平稳（量化步长 0.049 mΩ） |
| WP4 | 完成 | table_cycles 共 430 次摆动；工况每 116 h 周期完全重复，循环 Ah 不携带状态（同槽位离散约 0.001 Ah）；只有带载电压在变 |
| WP5 | 未开始 | — |
| WP6 | 未开始 | — |

下一步：WP5：登记协议（提交前不做切片）。最近一次提交见 git log。
