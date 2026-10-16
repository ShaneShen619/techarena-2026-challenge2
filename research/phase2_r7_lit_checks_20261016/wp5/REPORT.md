<a id="en"></a>

# WP5 — Synthesis

> **Language:** English · [中文](#zh)

Rules: [protocol.json](protocol.json) (committed in `671792e` before the table was assembled). Script [run_wp5.py](run_wp5.py); outputs [wp5_decision.json](outputs/wp5_decision.json), [wp5_SOH_table.csv](outputs/wp5_SOH_table.csv).

## Decision table

| Question | Result | Evidence class |
|---|---|---|
| CK2: keep SUB or switch to T_main? | **Recommend switching to T_main (not wired).** CK2 94.451 → 94.507 % | causal hold-out (5 one-month cases, pseudo, cold start) + all gates; real CK2 exposed |
| Post-anchor offset: overhang? | **Not supported** (P1–P3 all opposite in sign) | descriptive, n = 7; inputs seen before registration (D1.1) |
| Hidden C/20 order | Checkups start charged (7/7 at 13.1–13.3 V) → C/20 most likely without a preceding near-empty rest | data |
| d for P_drift | **−0.031 unchanged**; flag "drift sign not robust" (Yagci 50 °C −0.057, 35 °C +0.178) | external data, registered rule |
| Probe order | round 6: P_drift → P_stress_early → P_start. **Round 7: P_stress_early → P_start → P_drift.** Base: T_main if adopted, else SUB | registered rule (WP3) |

## SOH table (Δ = 0.4 configuration)

| Model | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| SUB (submitted) | 95.992 | 94.451 | 93.541 | 92.811 | 92.081 | 91.331 | 90.821 |
| T_main (recommended) | 95.992 | 94.507 | 93.541 | 92.811 | 92.081 | 91.331 | 90.821 |
| SUB + drift −0.031 | 95.916 | 94.327 | 93.389 | 92.637 | 91.884 | 91.111 | 90.585 |
| T_main + drift −0.031 | 95.916 | 94.385 | 93.389 | 92.637 | 91.884 | 91.111 | 90.585 |

The risk text for the submission report is in [../report_material/risk_addendum.md](../report_material/risk_addendum.md).

---

<a id="zh"></a>

# WP5 — 综合

> **语言：** [English](#en) · 中文

规则见 [protocol.json](protocol.json)（在汇总决策表之前于 `671792e` 提交）。

## 决策表

| 问题 | 结果 | 证据类别 |
|---|---|---|
| CK2：保留 SUB 还是切换到 T_main？ | **建议切换到 T_main（未接入）**，CK2 94.451 → 94.507 % | 因果留出（5 个一个月外推、伪场景、冷启动）+ 全部门槛；真实 CK2 已曝光 |
| 锚点后偏移是 overhang 吗？ | **不支持**（P1–P3 方向全部相反） | 描述性，n = 7；输入在登记前已见（D1.1） |
| 隐藏 C/20 的测量顺序 | 检查开始时电池组是充电状态（7/7 在 13.1–13.3 V）→ C/20 之前很可能没有近空停放 | 数据 |
| P_drift 采用的 d | **保持 −0.031**；标注“漂移符号不稳健”（Yagci 50 °C −0.057，35 °C +0.178） | 外部数据，登记规则 |
| 探测顺序 | 第六轮：P_drift → P_stress_early → P_start。**第七轮：P_stress_early → P_start → P_drift**。基础模型：若采用 T_main 则用 T_main，否则用 SUB | 登记规则（WP3） |

SOH 表见英文部分；提交报告的风险补充见 [../report_material/risk_addendum.md](../report_material/risk_addendum.md)。
