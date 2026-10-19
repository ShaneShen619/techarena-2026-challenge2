<a id="en"></a>

# WP1 — Registration

> English · [中文](#zh)

**Conclusions first.**

- **The protocol is registered before any fit on challenge data.** The files are [protocol.json](protocol.json), the registered code `src/tail.py` and the synthetic tests `src/test_tail.py`. Their SHA256 are in [protocol.sha256](protocol.sha256). Up to this commit, no tail model and no top-state estimator has touched the challenge data.
- **The synthetic tests all pass (0 failures, [test_tail_output.txt](test_tail_output.txt)).**
  - Each of M1–M4 recovers its own generating parameters to within 1.3·10⁻⁴ relative error, on 10 s traces quantised to 1 mA.
  - Every defined Q_tail (C2–C7) is recovered to within 5·10⁻⁴ Ah, against a gate of 0.01 Ah.
  - An M2 trace with I∞ = 4.2 A is correctly reported "undefined" for the 2.55 / 1.02 / 0.51 A cutoffs.
  - The closed-form integrals match numerical quadrature to 10⁻¹⁵ Ah, and Theil–Sen with LOO recovers a known slope exactly.
  - The decision function returns O1, O2, O3 "inconclusive" and O3 "not identifiable" on hand-made inputs.
- **The decision rules are copied verbatim** into `protocol.json` → `decision_rules_verbatim`. `decision_implementation` fixes how each phrase is computed, and `notes/DECISIONS.md` D7–D14 record the readings of ambiguous points.
- **The synthetic tests already show how far apart the models' extrapolations can be.** Each generator was chosen to resemble an anchor's CV window, and their tails differ sharply:
  - an exponential to zero (M1, M4) adds 0.25–0.37 Ah, whatever the termination;
  - a diffusion tail (M3) adds 3–23 Ah under the current cutoffs, and 2–5 Ah under the 30–120 min holds;
  - M2 with I∞ > 0 grows linearly with hold time.

  So if M3 or M2 is admitted on the anchors, the envelope will probably be decided by them. The envelope gate is designed to catch exactly this.

## What is registered

| Item | Registered choice |
|---|---|
| CV phase | first sample with pack ≥ 13.95 V and I < 19.9 A, to the last sample of the charge step; t from the CV start |
| Models | M1 A·e^(−t/τ); M2 I∞ + A·e^(−t/τ), I∞ ∈ [0, I_end]; M3 A·(t+t0)^(−1/2), t0 ≥ 0; M4 A1·e^(−t/τ1) + A2·e^(−t/τ2), τ2 = 3τ1 + δ, δ ≥ 0; all amplitudes ≥ 0 |
| Solver | `least_squares` (trf), multi-start grids in the protocol; the lowest cost wins |
| Admission | RMSE ≤ 0.15 A and \|mean residual over t ≥ ⅔·t_end\| ≤ 0.10 A |
| Scenarios | C1 ≡ 0; C2/C3/C4 cutoffs 2.55/1.02/0.51 A; C5/C6/C7 holds of 30/60/120 min beyond the observed CV end; "undefined" when M2's I∞ ≥ I_cut |
| Tail drift | Δ_tail(k) = Q_tail(k) − Q_tail(1); Theil–Sen against fade_k over usable anchors 1..7 (anchor 1 at the origin); LOO range; a pair needs anchor 1 usable plus ≥ 5 of anchors 2..7 |
| fade | Q_fc,1 − Q_fc,k from round 11's `pack_drivers.csv`; effect at CK7 = d·8.2 Ah |
| T2 | (V30_k − V30_1)/s_top, Δε = −ΔF; s_top = −dV/dQ_dis of the CK0 C/20 curve on [0.5, 2.0] Ah (also [0.25, 1.0], [1.0, 3.0]); pack (member of A) and per cell |
| T3 | ΔF_R = −5.1·(R_k − R_1)/s_top with the pack pulse resistance (sum of round 8's cells), Δε = −ΔF_R; consistency check only |
| Top-ups | the same fits; monthly medians of the 25 °C top-ups; descriptive, not in the decision |
| CK0 comparison | the top cell at the CK0 start, at the anchor CV end, at +30 min and in the 20 A pulse; descriptive |
| WP3 variants | `add_drift` from round 11's `drift.py`, with d ∈ {min over A, median over A without C1, max over A} |

## What each outcome would mean

| Outcome | Condition (registered) | What it would mean | What follows |
|---|---|---|---|
| **O1 "tail drift small"** | envelope ≤ 0.30 Ah, every member \|d·8.2\| ≤ 0.10 Ah, every LOO range within ±0.15 Ah | However the checkup terminates its CV (same 5.1 A, a lower cutoff, or a hold of up to 2 h), and whichever admitted tail shape is right, the change in the anchor's CV tail across ageing moves ε by at most 0.1 Ah at CK7 (≈ 0.1 pp SOH). | The top-tail part of the ε drift is closed. SUB is unchanged. The top-tail motivation for a P_drift probe is removed; round 15's probe plan can drop it. |
| **O2 "tail drift material"** | identifiable, all members except C1 share a sign, and their median \|d·8.2\| > 0.10 Ah | The tail's change with ageing moves ε by more than 0.1 Ah at CK7 in a consistent direction under every admitted scenario other than "same termination". | Candidate "SUB + d_tail" goes to the leaderboard only, never scored against proxies. Rounds 14/15 must weigh it against the possibility that the checkup terminates at 5.1 A (C1), where the tail drift is zero. |
| **O3 "not identifiable"** | envelope > 0.30 Ah | The admitted tail shapes and scenarios disagree by more than 0.3 Ah at CK7. The pack's ~8-minute CV window cannot tell how a longer CV would continue, so the bound depends on an unobserved termination and an unobservable tail shape. | Exit after writing the result. SUB is unchanged. The bound is reported as an envelope; the only way to narrow it is to learn the checkup's CV termination (a probe or the organisers). |
| **O3 "inconclusive"** | identifiable, but neither O1 nor O2 | The members agree within 0.3 Ah, but they differ in sign, or some exceed 0.1 Ah while the median does not. | SUB is unchanged. The interval is reported for rounds 14/15 with no candidate. |

---

<a id="zh"></a>

# WP1 — 登记

> [English](#en) · 中文

**结论先读。**

- **协议在赛题数据上做任何拟合之前登记。** 登记文件为 [protocol.json](protocol.json)、登记代码 `src/tail.py` 和合成测试 `src/test_tail.py`，三者的 SHA256 见 [protocol.sha256](protocol.sha256)。到本次提交为止，还没有任何尾巴模型或顶部状态估计碰过赛题数据。
- **合成测试全部通过（0 个失败，[test_tail_output.txt](test_tail_output.txt)）。**
  - 在 10 s 采样、量化到 1 mA 的曲线上，M1–M4 都能找回自己的生成参数，相对误差不超过 1.3·10⁻⁴。
  - 所有有定义的 Q_tail（C2–C7）误差不超过 5·10⁻⁴ Ah，门槛为 0.01 Ah。
  - I∞ = 4.2 A 的 M2 曲线在 2.55 / 1.02 / 0.51 A 截止下正确地报告为"未定义"。
  - 闭式积分与数值积分一致到 10⁻¹⁵ Ah；Theil–Sen 加 LOO 能精确找回已知斜率。
  - 在人工构造的输入上，决策函数分别返回 O1、O2、O3"无定论"和 O3"无法识别"。
- **决策规则原样照抄**在 `protocol.json` → `decision_rules_verbatim` 中。`decision_implementation` 规定了每句话的计算方式；有歧义之处的解读记在 `notes/DECISIONS.md` 的 D7–D14。
- **合成测试已经显示各模型外推的差距有多大。** 每个生成曲线都按锚点的 CV 窗口来选，但它们的尾巴相差很大：
  - 衰减到零的指数（M1、M4）无论怎样终止，都只多充 0.25–0.37 Ah；
  - 扩散型尾巴（M3）在电流截止下多充 3–23 Ah，在 30–120 min 恒压保持下多充 2–5 Ah；
  - I∞ > 0 的 M2 随保持时间线性增长。

  因此，如果 M3 或 M2 在锚点上被准入，包络很可能由它们决定。包络门槛正是为这种情况设计的。

## 登记内容

| 项目 | 登记的选择 |
|---|---|
| CV 段 | 从第一个电池组 ≥ 13.95 V 且 I < 19.9 A 的样本，到充电步的最后一个样本；t 从 CV 开始计 |
| 模型 | M1 A·e^(−t/τ)；M2 I∞ + A·e^(−t/τ)，I∞ ∈ [0, I_end]；M3 A·(t+t0)^(−1/2)，t0 ≥ 0；M4 A1·e^(−t/τ1) + A2·e^(−t/τ2)，τ2 = 3τ1 + δ，δ ≥ 0；所有幅值 ≥ 0 |
| 求解器 | `least_squares`（trf），多起点网格见协议；取代价最小者 |
| 准入 | RMSE ≤ 0.15 A，且 t ≥ ⅔·t_end 的样本上平均残差的绝对值 ≤ 0.10 A |
| 情景 | C1 ≡ 0；C2/C3/C4 截止于 2.55/1.02/0.51 A；C5/C6/C7 在观测到的 CV 结束之后再保持 30/60/120 min；M2 的 I∞ ≥ I_cut 时为"未定义" |
| 尾巴漂移 | Δ_tail(k) = Q_tail(k) − Q_tail(1)；在锚点 1..7 中可用的锚点上对 fade_k 做 Theil–Sen（锚点 1 在原点）；LOO 范围；一个组合需要锚点 1 可用，且锚点 2..7 中至少 5 个可用 |
| fade | Q_fc,1 − Q_fc,k，取自第 11 轮的 `pack_drivers.csv`；CK7 处的影响 = d·8.2 Ah |
| T2 | (V30_k − V30_1)/s_top，Δε = −ΔF；s_top = CK0 C/20 曲线在 [0.5, 2.0] Ah 上的 −dV/dQ_放电（另有 [0.25, 1.0]、[1.0, 3.0]）；电池组版本（属于 A）和各电芯版本 |
| T3 | ΔF_R = −5.1·(R_k − R_1)/s_top，R 为电池组脉冲内阻（第 8 轮各电芯之和），Δε = −ΔF_R；只作一致性检查 |
| 补电 | 同样的拟合；25 °C 补电的月中位数；描述性，不进入决策 |
| CK0 对比 | CK0 起点、锚点 CV 结束、+30 min 和 20 A 脉冲时各自的顶部电芯；描述性 |
| WP3 变体 | 用第 11 轮 `drift.py` 中的 `add_drift`，d ∈ {A 中的最小值、不含 C1 的 A 的中位数、A 中的最大值} |

## 各结果意味着什么

| 结果 | 条件（已登记） | 含义 | 后续 |
|---|---|---|---|
| **O1"尾巴漂移小"** | 包络 ≤ 0.30 Ah，每个成员 \|d·8.2\| ≤ 0.10 Ah，每个 LOO 范围都在 ±0.15 Ah 以内 | 无论检查怎样终止 CV（同为 5.1 A、更低的截止电流，或最长 2 h 的保持），也无论哪种准入的尾巴形状是对的，锚点 CV 尾巴随老化的变化在 CK7 处让 ε 移动不超过 0.1 Ah（约 0.1 pp SOH）。 | ε 漂移中顶部尾巴这一部分结案。SUB 不变。为 P_drift 探针提供的顶部尾巴动机被排除；第 15 轮的探针计划可以去掉这一项。 |
| **O2"尾巴漂移显著"** | 可识别，除 C1 外所有成员同号，且其 \|d·8.2\| 的中位数 > 0.10 Ah | 在除"相同终止"以外的所有准入情景下，尾巴随老化的变化都让 ε 在 CK7 处朝同一方向移动超过 0.1 Ah。 | 候选"SUB + d_tail"只用于排行榜，绝不与代理对比打分。第 14/15 轮必须同时考虑检查也在 5.1 A 终止（C1）的可能，那时尾巴漂移为零。 |
| **O3"无法识别"** | 包络 > 0.30 Ah | 各准入的尾巴形状和情景在 CK7 处相差超过 0.3 Ah。电池组约 8 分钟的 CV 窗口无法说明更长的 CV 会怎样延续，因此这个界取决于一个未观测到的终止方式和一个无法观测的尾巴形状。 | 写完结果后退出。SUB 不变。界以包络形式报告；要收窄它，唯一的办法是弄清检查的 CV 终止方式（通过探针或向主办方了解）。 |
| **O3"无定论"** | 可识别，但既不是 O1 也不是 O2 | 各成员的差异在 0.3 Ah 以内，但符号不一致，或者有些成员超过 0.1 Ah 而中位数没有超过。 | SUB 不变。把区间报告给第 14/15 轮，不提出候选。 |
