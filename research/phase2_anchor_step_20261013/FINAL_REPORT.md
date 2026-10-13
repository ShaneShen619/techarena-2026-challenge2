<a id="en"></a>

# Post-Checkup Full-Charge Anchor + Graphite-Step Displacement: Validation Report

> **Language:** English · [中文](#zh)

- **Run date:** 2026-10-13.
- **Branch:** `exp/phase2-anchor-step-20261013` (`main` plus this study directory).
- **Brief and protocol:** the work follows [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md). The protocol was frozen in [protocol.json](protocol.json) before evaluation (SHA256 `2c0e1365…`).
- **Untouched:** this round did not modify `framework/`, `run_model.py` or the active `my_model/`.
- **Other research referenced:** the three failed-route reports, the endpoint audit, the first-principles diagnosis and others are on branch `research-archive-20261010`.

## Conclusions first

**The data contain two signals that were never used as capacity observations before. M4 is a strictly causal model built on them. On the proxy labels its error is about 7 % (MAE) and 12–14 % (maximum error) of ExampleModel's. The pre-registered gates G1–G5 all pass, G1 with one caveat.**

- **Proxy SOH error:**
  - M4: MAE 0.29–0.35 pp, maximum error 0.67 pp.
  - ExampleModel: 3.9–4.7 / 4.9–5.7 pp.
  - Existing B baseline: 3.0–3.8 / 4.1–4.9 pp.
- **ε-independent error on CK2–CK7:** M4 0.30 pp.
- **Candidate package:** implemented and passes the causality checks, but is **not wired into the active submission**.

**Important limits.**

- The proxy label is "post-checkup full charge + offset ε", not the hidden truth.
- Some of the numbers in this task were seen during exploration before the protocol was registered. This is therefore an exposed, exploratory validation.
- All errors are proxy errors. The true accuracy on CK1–CK7 cannot be verified.

![Overview](figures/overview.png)

## 1. The signals

**Post-checkup full charge (A1).** After each checkup, the first operating segment opens with a 20.4 A charge from near empty to the end of the CCCV 14.0 V phase:

| | after CK0 (45 °C) | after CK1 | after CK2 | after CK3 | after CK4 | after CK5 | after CK6 | after CK7 |
|---|---|---|---|---|---|---|---|---|
| Q_fc (Ah) | 100.122 | 97.003 | 95.670 | 94.642 | 93.747 | 93.082 | 92.636 | 91.954 |

- The current integral and the counters differ by at most 0.022 Ah.
- The 25 °C charges follow a very consistent protocol: the rest before the start is always 2.0 h, the end current is always 5.10 A, and the temperature is about 26.4 °C.
- The rest voltage at the start is 2.89–3.00 V/cell.
  - Converted with the loaded tail of the CK0 curve, the remaining charge is at most 2.06 Ah.
  - This is a loose upper bound, because at the same SOC the rest voltage is higher than the loaded voltage.
- If the checkup ends with a 5.1 A discharge to 11.2 V and nothing after it, the starting state cancels between Q_CK and Q_fc. This depends on the checkup protocol and is **unverified**, which is why G1 passes with a caveat.

**The graphite step in the fixed program (A2).** About every 5 days, the sequence "CCCV full charge → 20 A pulse of 10.2 Ah → dynamic discharge of about 45.7 Ah" reaches 55.9 Ah of depth.

- **Location method:** in the ~10 A part of the discharge, each cell's step depth is taken as the first crossing of the midpoint between the upper and lower plateau.
- **Detection:** the step was found in 41 of 41 events. The median four-cell range is 0.63 Ah and the 90th percentile 0.74 Ah.
- **Trend:** step depth fell from 32.81 Ah (20 January) to 25.87 Ah (6 September). The four cells fell by 6.7–7.3 Ah each, and no single cell ran away.
- **Current dependence is small.** On the CK0 reference curve (5.1 A) the step is at 32.5–32.9 Ah, consistent with the first operating measurement (about 10 A).
- **Detection variants:** the six variants differ mainly by a constant offset (median 0.74 Ah), which cancels in differences.
- **A reversible recovery after each checkup.**
  - The jump from the last measurement before a checkup to the first one after it grows from +0.05 to +0.54 Ah, with a mean of 0.20 Ah.
  - At the same time, the step falls faster within 25 °C segments than within 45 °C segments.
  - Together these point to a reversible post-checkup recovery, or to a temperature effect. It is confounded with the checkup itself and cannot be separated in this round.

**Where the ageing happens (A4).** The charge-direction step is located inside each full charge. From February to September, Q_fc fell by 5.05 Ah, split as follows:

| Smoothing window | step → top of charge | empty end → step |
|---|---|---|
| 1 Ah | −3.99 | −1.06 |
| 2 Ah | −3.74 | −1.31 |
| 3 Ah | −3.42 | −1.63 |

- 68–79 % of the loss lies in the "step → top of charge" section, which is dominated by LLI.
- Part of the loss also appears in the bottom section, possibly from LAM_NE or a rate effect.

## 2. Causal prediction and proxy evaluation (B–D)

**Causal cut.**

- A prediction for CK_k uses only the output of `load_dataset(until=CK_k)`.
- The framework cuts at 00:00, so the step measurement at 08:52 on 8 February is not visible to CK1.

**Proxy.**

- The proxy is P_k = Q_fc,k + ε.
- ε0 = 100.41 − 100.122 = 0.288 Ah.
- The registered set is {ε0, ε0+0.4, ε0+0.8}.

| Model | MAE (pp) | Max error (pp) | MAE / M0 | Max error / M0 | CK1 error | CK2–7 MAE (ε-independent) |
|---|---|---|---|---|---|---|
| M0 ExampleModel | 3.90–4.69 | 4.88–5.67 | 1 | 1 | +2.2 to +3.0 | — |
| M1 B baseline | 3.05–3.83 | 4.12–4.91 | 0.78–0.82 | 0.84–0.87 | +1.3 to +2.0 | — |
| M2 anchor persistence | 1.03–1.14 | 2.27–3.06 | 0.24–0.26 | 0.47–0.54 | +2.3 to +3.1 | 0.83 |
| M3 anchor + √t | 0.58–0.69 | 2.27–3.06 | 0.15 | 0.47–0.54 | +2.3 to +3.1 | 0.30 |
| **M4 anchor + step (main)** | **0.29–0.35** | **0.67** | **0.07** | **0.12–0.14** | **−0.18 to +0.61** | **0.30** |
| M5 causally fitted β | 0.45–0.51 | 0.82 | 0.11 | 0.15–0.17 | −0.18 to +0.61 | 0.49 |

Per-checkup errors at ε0+0.4, in pp:

- M4: CK1 +0.22, CK2 +0.67, CK3 +0.08, CK4 +0.28, CK5 −0.11, CK6 −0.40, CK7 −0.28.
- ExampleModel: CK1 +2.64, CK2 +4.41, CK3 +4.15, CK4 +5.05, CK5 +5.28, CK6 +4.22, CK7 +4.32.

Notes on the results:

- **CK2 is M4's largest error.** Segment 3 (19 February to 11 March) is missing, so the last visible step stays at 17 February.
- **M4 fixes M3's CK1 problem.** M3 relies only on monthly anchors and cannot handle CK1; M4 solves this with the first month's step displacement.
- **M5's fitted β made things worse.** It drifts from 1.0 to 1.5, and the error ends up larger than with a fixed β = 1. This is consistent with the recovery effect above.

## 3. Robustness and falsification (E)

- **Step-detection variants (6).** The CK7 output changes by at most 0.18 Ah. Per checkup, the maximum differences are 0.45, 0.12, 0.27, 0.46, 0.59, 0.72 and 0.18 Ah.
- **β sensitivity (0.7–1.5).**
  - CK7 moves by 0.78 Ah, below the 1 pp flag threshold.
  - CK1 moves by 2.0 Ah, so **CK1 is driven by the ratio assumption**.
- **Choice of s_last.** Using the mean of the last two measurements raises the MAE to 0.37 pp. The main setting is better, but both are far better than the baseline.
- **Leave-one-anchor-out.** With the latest full charge removed, M4's errors are 0.52, 0.35, 0.32, 0.50, −0.09 and −0.24 pp, so the model degrades smoothly.
- **ε-drift checks.**
  - The CV share rises from 1.2 % to 1.5 %.
  - End current, rest time and temperature stay constant.
  - The residual of Q_fc against a √t fit correlates with the start voltage at −0.49 (n = 7, not significant).
  - No clear drift was found, but a change in the checkup protocol itself cannot be ruled out.
- **Synthetic half-cell falsification.** This is a schematic model roughly matched to the CK0 curve, not a real calibration.
  - **Pure LLI:** M4's error is at most 0.16 Ah.
  - **Pure LAM_NE:** M4 misreads the lengthening of the "step → top" section as a capacity increase, with an error about equal to the loss.
  - **Pure LAM_PE:** once the positive electrode limits the bottom end, the step stays put while capacity falls, and M4 does not see this loss.
  - **LLI and LAM_NE mixed in the measured proportion:** M4 underestimates the loss by about 25 %. The real model re-anchors on a full charge every month, so this error accumulates for only one month, about 0.2 Ah.

## 4. Acceptance gates

| Gate | Result |
|---|---|
| G1 data | **Pass (with caveat):** 8/8, counter difference 0.022 Ah; the start tail gives only an upper bound, and the start-state cancellation depends on the checkup protocol |
| G2 step channel | **Pass:** 100 % located, median four-cell range 0.63 Ah, CK7 variant difference 0.18 Ah |
| G3 causality | **Pass:** fitting on pre-CK1 data only and replacing future rows with noise both give bit-identical output |
| G4 proxy performance | **Pass:** MAE and maximum error below ExampleModel for every ε; CK2–7 error 0.30 pp |
| G5 mechanism | **Pass:** error ≤ 0.16 Ah under LLI; LAM cases reported as found, and A4 shows the real data are LLI-dominated |

Conclusion: **a formal candidate that passes at proxy level**. The hidden truth is unverified.

## 5. Candidate package (F)

- **Implementation:** [candidate_model/anchor_step_model.py](candidate_model/anchor_step_model.py) contains `AnchorStepModel`. It depends only on numpy/pandas and is an independent rewrite of the research M4. The two differ by at most 0.0005 pp (three-decimal rounding).
- **Predicted SOH (%):** CK0 98.441, CK1 95.992, CK2 95.137, CK3 93.541, CK4 92.862, CK5 91.819, CK6 91.091, CK7 90.544.
- **ε:** fixed at ε0+0.4, the midpoint of the registered range. This is an assumption.
- **Smoke test:** passes on sample_data. With no events, the model falls back to CK0.

## 6. Still unverifiable / risks

1. **Size and stability of ε.**
   - ε depends on the checkup protocol: full-charge termination, temperature, and whether anything else follows the discharge.
   - An overall shift in ε moves every CK by about ±0.4 pp.
2. **Post-checkup recovery.**
   - This round cannot tell whether the capacity measured at a checkup is closer to the state before or after the recovery.
   - It is one of the main sources of the ±0.4 pp-level errors from CK2 on.
3. **CK1.** It depends on β and spans 2 pp over β = 0.7–1.5. At β = 1 it falls inside the proxy range.
4. **A single pack, and proxies rather than truth.** No official accuracy can be claimed. Under the submission rules, proxy values must not be presented as "true CK" values.

## 7. Suggested next steps

1. The user decides whether to wire `AnchorStepModel` into `my_model/` and run `validate_submission.py`. If it is wired in, the README must state the ε assumption and the physical basis.
2. Find the official checkup protocol, or ask the organizers for it, to narrow ε.
3. Optional small improvements. Each needs a new registration and an independent evaluation:
   - a rate term for extrapolating the step when segment 3 is missing;
   - modelling the recovery as a term that decays with days since the checkup.
4. Stop inferring capacity from mid-plateau voltage windows (the capacity part of routes one, two and three).

See [README.md](README.md) for reproduction.

---

<a id="zh"></a>

# 检查后完整充电锚点 + 石墨台阶位移：验证报告

> **语言：** [English](#en) · 中文

执行日期：2026-10-13。分支 `exp/phase2-anchor-step-20261013`（`main` + 本研究目录）。执行依据：[EXECUTION_PROMPT.md](EXECUTION_PROMPT.md)；协议在评估前冻结于 [protocol.json](protocol.json)（SHA256 `2c0e1365…`）。本轮未修改 `framework/`、`run_model.py`、正式 `my_model/`。报告引用的其他研究目录（三份失败报告、端点审计、第一性原理诊断等）在分支 `research-archive-20261010` 上。

## 结论先读

**数据里存在两类此前从未被当作容量观测使用的信号，以它们为基础的严格因果模型 M4，在代理标签上的误差约为 ExampleModel 的 7%（MAE）和 12–14%（最大误差）。预登记的 G1–G5 门全部通过，其中 G1 带一个说明。**

- 代理 SOH 误差：M4 的 MAE 为 0.29–0.35 pp，最大误差 0.67 pp。ExampleModel 为 3.9–4.7 / 4.9–5.7 pp，既有 B 基线为 3.0–3.8 / 4.1–4.9 pp。
- CK2–CK7 上与 ε 无关的误差：M4 0.30 pp。
- 候选模型包已实现并通过因果检查，但**没有接入正式提交**。

**重要边界**：代理标签是"检查后完整充电量 + 偏置 ε"，不是隐藏真值。本任务部分数字在登记协议前已在探查中看到，属于已曝光的探索性验证。所有误差都是代理误差，CK1–CK7 的真实精度仍不可验证。

![总览](figures/overview.png)

## 1. 信号是什么

**检查后完整充电（A1）。** 每个检查之后的首个运行段，都以一次从近空到 CCCV 14.0 V 末端的 20.4 A 充电开头：

| | CK0 后（45°C） | CK1 后 | CK2 后 | CK3 后 | CK4 后 | CK5 后 | CK6 后 | CK7 后 |
|---|---|---|---|---|---|---|---|---|
| Q_fc (Ah) | 100.122 | 97.003 | 95.670 | 94.642 | 93.747 | 93.082 | 92.636 | 91.954 |

- 电流积分与计数器的最大差为 0.022 Ah。
- 25°C 的几次充电起点前静置都是 2.0 h，末电流都是 5.10 A，温度约 26.4°C，协议高度一致。
- 起点静置电压为 2.89–3.00 V/芯。用 CK0 带载尾段换算，剩余电量上界不超过 2.06 Ah；这是一个宽松上界，因为同一 SOC 下静置电压高于带载电压。
- 如果检查以 5.1 A 放电至 11.2 V 结束、之后没有其他步骤，起点状态在 Q_CK 与 Q_fc 之间相互抵消。这一点依赖检查协议，**未证实**，所以 G1 带说明通过。

**固定程序的石墨台阶（A2）。** 约每 5 天的"CCCV 满充 → 20 A 脉冲 10.2 Ah → 约 45.7 Ah 动态放电"会到达 55.9 Ah 深度。在约 10 A 段，按"上下平台中点首次穿越"定位每颗电芯的台阶深度：

- 41/41 次全部定位成功。四芯中位极差 0.63 Ah，90 分位 0.74 Ah。
- 台阶深度从 32.81 Ah（1 月 20 日）降到 25.87 Ah（9 月 6 日）。四颗电芯分别下降 6.7–7.3 Ah，没有哪颗失控。
- CK0 参考曲线（5.1 A）上的台阶在 32.5–32.9 Ah，与首次运行测量（约 10 A）一致，电流依赖很小。
- 6 种检测变体之间主要相差一个常数偏移（中位 0.74 Ah），这个偏移在差分中抵消。
- 检查前末测量到检查后首测量的跳变从 +0.05 Ah 逐渐增大到 +0.54 Ah，平均 0.20 Ah；同时 25°C 段内台阶下降比 45°C 段更快。这说明检查后存在可逆回弹（或温度效应），它与检查本身混在一起，本轮无法分开。

**老化发生在哪一段（A4）。** 在完整充电内定位充电方向的台阶。2 月到 9 月，Q_fc 下降 5.05 Ah，其中：

| 平滑窗 | 台阶→满充端 | 放空端→台阶 |
|---|---|---|
| 1 Ah | −3.99 | −1.06 |
| 2 Ah | −3.74 | −1.31 |
| 3 Ah | −3.42 | −1.63 |

损失的 68–79% 在"台阶→满充端"段，以 LLI 为主，另有一部分出现在底部段（可能是 LAM_NE 或倍率效应）。

## 2. 因果预测与代理评估（B–D）

预测 CK_k 只用 `load_dataset(until=CK_k)` 的结果；框架按 00:00 截断，所以 2 月 8 日 08:52 那次台阶测量对 CK1 不可见。代理为 P_k=Q_fc,k+ε，其中 ε0=100.41−100.122=0.288 Ah，登记集合为 {ε0, ε0+0.4, ε0+0.8}。

| 模型 | MAE (pp) | 最大误差 (pp) | MAE / M0 | 最大误差 / M0 | CK1 误差 | CK2–7 MAE（与 ε 无关） |
|---|---|---|---|---|---|---|
| M0 ExampleModel | 3.90–4.69 | 4.88–5.67 | 1 | 1 | +2.2 ~ +3.0 | — |
| M1 B 基线 | 3.05–3.83 | 4.12–4.91 | 0.78–0.82 | 0.84–0.87 | +1.3 ~ +2.0 | — |
| M2 锚点持续 | 1.03–1.14 | 2.27–3.06 | 0.24–0.26 | 0.47–0.54 | +2.3 ~ +3.1 | 0.83 |
| M3 锚点 + √t | 0.58–0.69 | 2.27–3.06 | 0.15 | 0.47–0.54 | +2.3 ~ +3.1 | 0.30 |
| **M4 锚点 + 台阶（主）** | **0.29–0.35** | **0.67** | **0.07** | **0.12–0.14** | **−0.18 ~ +0.61** | **0.30** |
| M5 因果拟合 β | 0.45–0.51 | 0.82 | 0.11 | 0.15–0.17 | −0.18 ~ +0.61 | 0.49 |

逐检查点误差（ε0+0.4 时，单位 pp）：

- M4：CK1 +0.22、CK2 +0.67、CK3 +0.08、CK4 +0.28、CK5 −0.11、CK6 −0.40、CK7 −0.28。
- ExampleModel：CK1 +2.64、CK2 +4.41、CK3 +4.15、CK4 +5.05、CK5 +5.28、CK6 +4.22、CK7 +4.32。

M4 误差最大的是 CK2，因为缺失的第 3 段（2 月 19 日至 3 月 11 日）让最后一次可见台阶停在 2 月 17 日。

M3 只靠月度锚点，无法处理 CK1；M4 用第一个月的台阶位移解决了这个问题。M5 拟合出的 β 从 1.0 漂到 1.5，误差反而大于固定 β=1，与上面的回弹现象一致。

## 3. 稳健性与反证（E）

- **台阶检测变体（6 种）**：CK7 输出最大差 0.18 Ah。各检查点最大差依次为 0.45、0.12、0.27、0.46、0.59、0.72、0.18 Ah。
- **β 敏感性（0.7–1.5）**：CK7 变化 0.78 Ah，低于 1 pp 的标记阈值；CK1 变化 2.0 Ah，**CK1 由比例假设驱动**。
- **s_last 取法**：取最后两次的均值时 MAE 升到 0.37 pp，主设置更好，但两种取法都远好于基准。
- **留一锚点**：去掉最近一次完整充电后，M4 误差为 0.52、0.35、0.32、0.50、−0.09、−0.24 pp，能平稳退化。
- **ε 漂移检查**：CV 段占比从 1.2% 升到 1.5%，末电流、静置时长、温度都恒定。Q_fc 对 √t 拟合的残差与起点电压的相关系数为 −0.49（n=7，不显著）。没有发现明显漂移，但也无法排除检查协议本身的变化。
- **半电池合成反证**：这是一个由 CK0 曲线粗配的示意模型，不是真实标定。
  - 纯 LLI：M4 误差不超过 0.16 Ah。
  - 纯 LAM_NE：M4 把"台阶→顶部"段的变长误读成容量上升，误差约等于损失量。
  - 纯 LAM_PE：在正极限制底端之后，台阶不动而容量下降，M4 看不到这部分损失。
  - 按实测比例混合 LLI 和 LAM_NE：M4 少估约 25% 的损失。真实模型每月用完整充电重新锚定，这部分误差只在一个月内累积，约 0.2 Ah。

## 4. 接纳门

| 门 | 结果 |
|---|---|
| G1 数据 | **通过（带说明）**：8/8，计数器差 0.022 Ah；起点尾段只给出上界，起点抵消依赖检查协议 |
| G2 台阶通道 | **通过**：100% 定位，四芯中位极差 0.63 Ah，CK7 变体差 0.18 Ah |
| G3 因果 | **通过**：只用 CK1 前数据做 fit、把未来行替换为噪声，输出都逐位一致 |
| G4 代理表现 | **通过**：全部 ε 下 MAE 与最大误差都低于 ExampleModel；CK2–7 误差 0.30 pp |
| G5 机制 | **通过**：LLI 下误差 ≤0.16 Ah；LAM 情形如实报告，A4 显示真实数据以 LLI 为主 |

结论：**代理层面通过的正式候选**，隐藏真值未验证。

## 5. 候选模型包（F）

- [candidate_model/anchor_step_model.py](candidate_model/anchor_step_model.py)：`AnchorStepModel`，只依赖 numpy/pandas，是对研究用 M4 的独立重写。两者相差不超过 0.0005 pp（三位小数舍入）。
- 预测 SOH（%）：CK0 98.441、CK1 95.992、CK2 95.137、CK3 93.541、CK4 92.862、CK5 91.819、CK6 91.091、CK7 90.544。
- 固定取 ε=ε0+0.4，即登记范围的中点；这是一个假设。
- sample_data 冒烟测试通过，无事件时回退到 CK0。

## 6. 仍不可验证 / 风险

1. **ε 的大小与稳定性**：取决于检查协议（满充终止条件、温度、放电后是否还有其他步骤）。ε 的整体偏移会使所有 CK 平移约 ±0.4 pp。
2. **检查后回弹**：检查时测得的容量更接近回弹前还是回弹后，本轮无法判断；它是 CK2 以后 ±0.4 pp 级误差的主要来源之一。
3. **CK1**：依赖 β，在 β 0.7–1.5 范围内跨 2 pp；在 β=1 时落在代理范围内。
4. **单一电池组、代理非真值**：不能宣称官方精度。按提交规则，不得把代理值作为"真实 CK"对外表述。

## 7. 建议下一步

1. 由用户决定是否把 `AnchorStepModel` 接入 `my_model/`，并跑 `validate_submission.py`。接入时 README 要写明 ε 假设和物理依据。
2. 查找或询问官方检查协议，以收窄 ε。
3. 可选的小改进（需新登记、独立评估）：为第 3 段缺失时的台阶外推加一个速率项；把回弹建模为随检查后天数衰减的项。
4. 停止从平台中段电压窗口反推容量的工作（路线一、二、三的容量部分）。

复现方法见 [README.md](README.md)。
