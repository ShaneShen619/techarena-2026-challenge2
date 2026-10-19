<a id="en"></a>

# Round 13 — Top-of-charge drift bound: how much can the anchor's CV tail move ε? — Final report

> English · [中文](#zh)

Branch `exp/phase2-r13-top-tail-20261019`, base `6525edf`. Protocol registered at `7960a99`, before any fit on challenge data. Written 2026-10-19. No rule or output of this round uses P_k or any proxy error, and the submission is not changed.

## Conclusions

1. **Registered outcome: O3 "not identifiable", with an envelope of 0.412 Ah against the 0.30 Ah gate.** SUB is unchanged and there is no candidate.
2. **Bound.** Every member of the admitted set is ≥ 0. The top-tail part of the ε drift lies in **[0, +0.41] Ah at CK7** (0 to +0.39 pp of SOH).
   - The tail models alone give **+0.04 to +0.12 Ah** (+0.10 pp at the median, d_tail = 0.0131 Ah/Ah).
   - It is exactly 0 if the checkup stops its CV at 5.1 A like the anchor.
3. **Decision.** The top-tail motivation for P_drift is **not** removed; that needed O1. The open variable is the checkup's CV termination. It is not in the data, and any answer on it collapses the envelope to a single scenario.
4. **Recommendation.**
   - Keep SUB.
   - Do not add a tail term.
   - Carry [0, +0.41] Ah (tail models: +0.04…+0.12 Ah) into rounds 14/15 as the size of this term.
   - Ask the organisers, or probe, about the checkup CV termination. Under the admitted tail model, that answer is worth at most about 0.1 pp at CK7.

## What was found, by work package

**WP0 — set-up and facts** ([wp0/REPORT.md](wp0/REPORT.md), [wp0/FACTS.md](wp0/FACTS.md)).
- SUB is reproduced (CK7 90.765 %).
- 41 full charges are catalogued: 8 anchors and 33 top-ups.
- Four of the six §2 facts hold. Two are corrected:
  - the anchors' CV phase is 438–530 s (45–54 samples) and lengthens with ageing;
  - the top-ups' CV phase is 1.9–4.4 min, not 2–9 min.
- Cell3 is the highest cell at the top of all 41 charges.

**WP1 — registration** ([wp1/REPORT.md](wp1/REPORT.md)). Four tail models (M1–M4), seven checkup-termination scenarios (C1–C7), two top-state estimators (T2, T3) and the decision rules were registered verbatim. The registered code passed every synthetic test.

**WP2 — measurements** ([wp2/REPORT.md](wp2/REPORT.md)).
- **Only M4 (two exponentials) fits the anchors' CV current.** It is admitted on all of anchors 1–7. M1, M2 and M3 fail on all seven.
  - M2 reproduces round 11's τ = 179 s and I∞ = 4.23 A but misses the RMSE gate (0.16–0.28 A).
  - M3, the diffusion tail, fits worst.
- **The exposed back-of-envelope.** Under M1's own fit, I_end·τ is 0.465 → 0.588 Ah (anchors 1 → 7), but M1 is not admitted. The 0.25 → 0.31 Ah in the prompt used M2's τ. Under M4 the tail grows by +0.11…+0.13 Ah at anchor 7, more than the guessed ≈ 0.05 Ah, but with the same order of magnitude.
- **M4's tail drift is positive under every scenario: +0.041 Ah (2.55 A cutoff) to +0.124 Ah (2 h hold) at CK7.** The shape is a step from anchor 1 to anchor 2, then a slow rise.
- **T2 (relaxed top voltage) gives +0.41 Ah, but it rests on 7 mV of V30 at 1 mV resolution.** Its slope s_top (0.022 V/Ah) is taken on the CK0 window where the steep top meets the plateau. On the [0.25, 1.0] Ah window it gives +0.06 Ah.
- **T3 (resistance) gives +0.10 Ah**, with the same sign.
- **The 25 °C top-ups' tails do not grow** (+0.003 Ah). The growth is specific to the from-empty anchor charge.

**WP3 — decision** ([wp3/REPORT.md](wp3/REPORT.md), [wp3/R13_RESULT.json](wp3/R13_RESULT.json)).
- Envelope 0.412 Ah > 0.30 → O3 "not identifiable".
- Unregistered diagnostic: without T2, or with T2 on [0.25, 1.0] Ah, it would have been a borderline O2 (median 0.107 Ah against 0.10). The registered outcome hinges on T2's s_top window.

## SOH per checkup: SUB vs SUB + d_tail (leaderboard-only, no candidate under O3)

| Variant | d (Ah/Ah) | CK0 | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|---|---|
| **SUB (unchanged)** | 0 | 98.441 | 95.984 | 94.507 | 93.600 | 92.821 | 92.015 | 91.426 | 90.765 |
| SUB + d_tail (median over A without C1) | 0.0131 | 98.441 | 96.016 | 94.559 | 93.664 | 92.895 | 92.099 | 91.518 | 90.866 |
| SUB + d_max (T2) | 0.0502 | 98.441 | 96.107 | 94.704 | 93.843 | 93.103 | 92.338 | 91.778 | 91.150 |

d_min over A is 0 (C1), which gives SUB. All four rows are in [wp3/SOH_variants.csv](wp3/SOH_variants.csv).

## Hand-off

- **Round 14.** The anchor tail grows with ageing while the top-up tails do not. This is a from-empty path candidate: τ2 goes from 412 s to 503 s, with a step from anchor 1 to anchor 2.
- **Round 15.** The checkup's CV termination is the single variable that decides this term. T2 cannot replace it, because the unrelaxed CK0 top (cell3 leading by 137 mV) does not define a usable s_top.
- **Round 11's transfer bound** was d ∈ [−0.036, +0.052]. This round's admitted set, [0, +0.050], lies inside it and removes the negative side for the tail term.

---

<a id="zh"></a>

# 第 13 轮——充电顶部漂移的上界：锚点的 CV 尾巴能让 ε 移动多少？——最终报告

> [English](#en) · 中文

分支 `exp/phase2-r13-top-tail-20261019`，基点 `6525edf`。协议在 `7960a99` 登记，早于在赛题数据上的任何拟合。写于 2026-10-19。本轮的任何规则或输出都没有使用 P_k 或代理误差，提交也没有改动。

## 结论

1. **登记结果：O3"无法识别"，包络 0.412 Ah，门槛为 0.30 Ah。** SUB 不变，没有候选。
2. **界。** 准入集的每个成员都 ≥ 0。ε 漂移的顶部尾巴部分落在 **CK7 处 [0, +0.41] Ah**（SOH 0 到 +0.39 pp）。
   - 仅尾巴模型给出 **+0.04 到 +0.12 Ah**（中位数 +0.10 pp，d_tail = 0.0131 Ah/Ah）。
   - 如果检查像锚点一样在 5.1 A 停止 CV，则恰为 0。
3. **决策。** P_drift 来自顶部尾巴的动机**没有**被排除；排除它需要 O1。未知量是检查的 CV 终止方式。数据中没有这一信息，而只要知道它，包络就会收缩到单一情景。
4. **建议。**
   - 保持 SUB。
   - 不加入尾巴项。
   - 把 [0, +0.41] Ah（尾巴模型：+0.04…+0.12 Ah）作为这一项的大小带入第 14/15 轮。
   - 向主办方询问或用探针弄清检查的 CV 终止方式。在准入的尾巴模型下，这个答案在 CK7 处最多值约 0.1 pp。

## 各工作包的发现

**WP0——准备与事实**（[wp0/REPORT.md](wp0/REPORT.md)，[wp0/FACTS.md](wp0/FACTS.md)）。
- SUB 已复现（CK7 90.765 %）。
- 编目了 41 次满充：8 个锚点和 33 次补电。
- 第 2 节六条事实中四条成立。两条被修正：
  - 锚点 CV 段为 438–530 s（45–54 个样本），并随老化变长；
  - 补电 CV 段为 1.9–4.4 min，不是 2–9 min。
- 在全部 41 次充电的顶部，cell3 都是最高的电芯。

**WP1——登记**（[wp1/REPORT.md](wp1/REPORT.md)）。原样登记了四个尾巴模型（M1–M4）、七个检查终止情景（C1–C7）、两个顶部状态估计（T2、T3）和决策规则。登记的代码通过了全部合成测试。

**WP2——测量**（[wp2/REPORT.md](wp2/REPORT.md)）。
- **只有 M4（双指数）能拟合锚点的 CV 电流。** 它在锚点 1–7 上全部准入。M1、M2、M3 在这 7 个锚点上全部失败。
  - M2 复现了第 11 轮的 τ = 179 s、I∞ = 4.23 A，但没有通过 RMSE 门槛（0.16–0.28 A）。
  - M3（扩散型尾巴）拟合最差。
- **已曝光的粗算。** 用 M1 自己的拟合，I_end·τ 为 0.465 → 0.588 Ah（锚点 1 → 7），但 M1 没有准入。prompt 中的 0.25 → 0.31 Ah 用的是 M2 的 τ。在 M4 下，锚点 7 的尾巴增长 +0.11…+0.13 Ah，比猜测的约 0.05 Ah 大，但数量级相同。
- **M4 的尾巴漂移在每个情景下都为正：CK7 处从 +0.041 Ah（2.55 A 截止）到 +0.124 Ah（保持 2 h）。** 形状是从锚点 1 到锚点 2 的一个台阶，之后缓慢上升。
- **T2（静置顶部电压）给出 +0.41 Ah，但它只依赖 V30 上 1 mV 分辨率下的 7 mV 变化。** 它的斜率 s_top（0.022 V/Ah）取自 CK0 曲线上陡峭顶部与平台相接的窗口。用 [0.25, 1.0] Ah 窗口则为 +0.06 Ah。
- **T3（内阻）给出 +0.10 Ah**，符号相同。
- **25 °C 补电的尾巴不增长**（+0.003 Ah）。这种增长是从空开始的锚点充电所特有的。

**WP3——决策**（[wp3/REPORT.md](wp3/REPORT.md)，[wp3/R13_RESULT.json](wp3/R13_RESULT.json)）。
- 包络 0.412 Ah > 0.30 → O3"无法识别"。
- 未登记的诊断：去掉 T2，或 T2 改用 [0.25, 1.0] Ah 窗口，结果会是一个勉强的 O2（中位数 0.107 Ah，门槛 0.10）。登记的结果取决于 T2 的 s_top 窗口。

## 各检查点 SOH：SUB 与 SUB + d_tail（只用于排行榜；O3 下没有候选）

| 变体 | d (Ah/Ah) | CK0 | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|---|---|
| **SUB（不变）** | 0 | 98.441 | 95.984 | 94.507 | 93.600 | 92.821 | 92.015 | 91.426 | 90.765 |
| SUB + d_tail（不含 C1 的 A 的中位数） | 0.0131 | 98.441 | 96.016 | 94.559 | 93.664 | 92.895 | 92.099 | 91.518 | 90.866 |
| SUB + d_max（T2） | 0.0502 | 98.441 | 96.107 | 94.704 | 93.843 | 93.103 | 92.338 | 91.778 | 91.150 |

A 中的 d 最小值为 0（C1），即 SUB 本身。四行全部见 [wp3/SOH_variants.csv](wp3/SOH_variants.csv)。

## 交接

- **第 14 轮。** 锚点尾巴随老化增长，而补电尾巴不增长。这是一个从空充电路径的候选：τ2 从 412 s 增至 503 s，锚点 1 到锚点 2 之间有一个台阶。
- **第 15 轮。** 检查的 CV 终止方式是决定这一项的唯一变量。T2 无法替代它，因为未静置的 CK0 顶部（cell3 领先 137 mV）无法给出可用的 s_top。
- **第 11 轮的迁移界**为 d ∈ [−0.036, +0.052]。本轮的准入集 [0, +0.050] 落在其中，并且排除了尾巴项的负值一侧。
