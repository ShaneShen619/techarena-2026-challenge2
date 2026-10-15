<a id="en"></a>

# Draft — Method section

> **Language:** English · [中文](#zh)

*Draft for REPORT.md section 1. The package's current REPORT.md already describes SUB in detail; this draft condenses it and adds the context of what else was tried.*

**Submitted model (SUB = V2 + √t gap branch).** SOH is read from two measurements the pack makes on its own; no voltage threshold on the flat LFP plateau is used.

1. **Anchor.** The first CCCV charge after each checkup runs from near empty to the end of the 14.0 V CV phase (20.4 A, ending at 5.1 A). Its charged Ah, from the integrated current, is close to the usable capacity. The offset to the C/20 checkup protocol comes from the released CK0 (ε0 = 0.288 Ah), plus an assumed 0.4 Ah for 25 °C anchors.
2. **In-month update.** About every 5 days a fixed program discharges about 56 Ah below full and crosses the graphite staging step. Month-end 45 °C step depths are compared between consecutive months (phase matching). This cancels a temperature offset (+0.18 Ah at 45 °C) and a post-anchor charge-path offset (+0.4–0.56 Ah on the first program after an anchor). The difference is scaled by β, the measured share of the loss that lies above the step (1.06–1.51).
3. **Coverage gap.** When the last visible program is more than 10 days old (only CK2, because segment 3 is missing), the loss since the previous anchor is extrapolated with √t since CK0.

**Model families evaluated and not submitted** (all strictly causal, pre-registered):

- a stress-history ageing law: break-in + √t calendar + linear cycle, Arrhenius-weighted, calibrated on the pack's own anchors with an external prior (rounds 5A/5C);
- an electrode-level degradation-mode model from literature half-cell OCPs (round 5B);
- uncertainty-weighted fusions of the stress law with SUB (round 6 WP2);
- truth-oriented corrections: ε drift, anchor start state, path effect (round 6 WP3).

None beat SUB under the registered gates. The stress law beats SUB on causal hold-out tests (pseudo 0.119 vs 0.148 pp; cold start 0.144 vs 0.174 pp) but not at CK1 and CK2, where neither the data nor physics can decide.

**Candidate status:** no replacement for SUB is recommended. WP4 (open-data prior) is in progress at the time of writing.

---

<a id="zh"></a>

# 草稿——方法部分

> **语言：** [English](#en) · 中文

*供 REPORT.md 第 1 节使用的草稿。提交包当前的 REPORT.md 已经详细描述了 SUB；这份草稿做了压缩，并补充了"还试过什么"的背景。*

**提交的模型（SUB = V2 + √t 缺口分支）。** SOH 由电池组自己产生的两类测量读出，不在平坦的 LFP 平台上用电压阈值。

1. **锚点。** 每次检查后的第一次 CCCV 充电从近空一直充到 14.0 V 恒压段末尾（20.4 A，在 5.1 A 截止）。由电流积分得到的充入 Ah 接近可用容量。它与 C/20 检查协议之间的偏差由公开的 CK0 确定（ε0 = 0.288 Ah），25 °C 锚点再假定加 0.4 Ah。
2. **月内更新。** 大约每 5 天，一个固定程序会放电到满充以下约 56 Ah，越过石墨分阶台阶。比较相邻两个月月末的 45 °C 台阶深度（同相位）。这样可以抵消两种偏差：温度偏差（45 °C 下深 0.18 Ah），以及锚点后的充电路径偏差（锚点后第一次程序深 0.4–0.56 Ah）。差值再乘以 β，即测得的损失中位于台阶上方的那部分比例（1.06–1.51）。
3. **覆盖缺口。** 当最后一次可见程序已超过 10 天（只有 CK2，因为缺第 3 段）时，自上一个锚点以来的损失用自 CK0 起的 √t 外推。

**评估过但未提交的模型族**（全部严格因果、预登记）：

- 应力历史老化定律：磨合 + √t 日历 + 线性循环，Arrhenius 加权，用电池组自身锚点和外部先验标定（第 5A / 5C 轮）；
- 基于文献半电池 OCP 的电极级退化模式模型（第 5B 轮）；
- 应力定律与 SUB 的不确定度加权融合（第六轮 WP2）；
- 真值导向修正：ε 漂移、锚点起点状态、路径效应（第六轮 WP3）。

在登记的门槛下，没有一个超过 SUB。应力定律在因果留出检验上优于 SUB（伪场景 0.119 对 0.148 pp；冷启动 0.144 对 0.174 pp），但在 CK1 和 CK2 上不行；而在这两个点上，数据和物理都无法判定谁对。

**候选状态：** 不建议替换 SUB。撰写本稿时，WP4（开放数据先验）仍在进行中。
