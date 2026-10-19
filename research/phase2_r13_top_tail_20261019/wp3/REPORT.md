<a id="en"></a>

# WP3 — Envelope, decision and hand-off

> English · [中文](#zh)

The registered rules (`wp1/protocol.json`, commit `7960a99`) were applied by `tail.decide` in `src/run_wp3.py` to the WP2 measurements. No P_k or proxy error was used.

**Conclusions first.**

- **Outcome: O3 "not identifiable".** The envelope over the admitted set A is **0.412 Ah**, above the 0.30 Ah gate. As registered, this round reports the envelope, writes the result and exits. **SUB is unchanged.**
- **The envelope is set by T2 (+0.412 Ah) against C1 (0).** The six tail-model members (M4 × C2–C7) lie within +0.041…+0.124 Ah.
- **Every member of A has the same sign: each is either positive or exactly 0 (C1).** If the checkup charges further into the CV than the anchor's 5.1 A end, the tail drift raises ε with fade. Within the admitted set, the top-tail part of the ε drift is bounded to **[0, +0.41] Ah at CK7**. That is at most **+0.39 pp** of SOH at CK7, and +0.10 pp at the median (d_tail = 0.0131 Ah/Ah).
- **The top-tail motivation for P_drift is not removed.** That removal needed O1. Under the C1 scenario (checkup also stops at 5.1 A) the tail drift is exactly 0. Nothing in the data says which termination the checkup uses.
- **Unregistered diagnostics (not used for the outcome).**
  - Without T2, or with T2 on the [0.25, 1.0] Ah window, the set would be identifiable: envelope 0.124 Ah, all members positive, median |d·8.2| = 0.107 Ah. That is a borderline O2, only 0.007 Ah over the 0.10 threshold.
  - So the registered O3 hinges on T2's main window, where the CK0 curve's steep top meets its plateau and each 1 mV of V30 becomes 0.045 Ah.
  - This sensitivity is reported for rounds 14/15. It does not change the registered outcome.

## Admitted set A and the rules

| Member | d (Ah/Ah) | d·8.2 (Ah) | LOO d·8.2 (Ah) |
|---|---|---|---|
| C1 (≡ 0) | 0 | 0.000 | [0.000, 0.000] |
| T2 pack, main window | 0.0502 | **+0.412** | [+0.292, +0.566] |
| M4 / C2 | 0.0050 | +0.041 | [+0.029, +0.088] |
| M4 / C3 | 0.0111 | +0.091 | [+0.062, +0.147] |
| M4 / C4 | 0.0131 | +0.108 | [+0.072, +0.167] |
| M4 / C5 | 0.0130 | +0.107 | [+0.072, +0.169] |
| M4 / C6 | 0.0151 | +0.124 | [+0.083, +0.186] |
| M4 / C7 | 0.0152 | +0.124 | [+0.083, +0.186] |

There are no M1, M2 or M3 members, because none is admitted on any of anchors 1–7.

| Rule | Value | Result |
|---|---|---|
| Envelope = max − min of d·8.2 over A | 0.412 − 0.000 = **0.412 Ah** | > 0.30 → **O3 "not identifiable"** |
| (O1 test, not reached) | T2 at 0.412 and M4 C4–C7 at 0.107–0.124 exceed 0.10 | would fail |
| (O2 test, not reached) | all non-C1 members positive; median \|d·8.2\| = 0.108 Ah | would pass, but identifiability failed first |

The order of the tests is registered: identifiability first.

## SOH variants (leaderboard-only, never scored against proxies)

`add_drift` comes from round 11's `drift.py`: Q' = Q + d·max(0, 100.41 − Q). Under O3 there is no candidate; the variants are written only because WP3's list requires them (D14). SOH in %:

| Variant | d | CK0 | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|---|---|
| SUB | 0 | 98.441 | 95.984 | 94.507 | 93.600 | 92.821 | 92.015 | 91.426 | 90.765 |
| SUB + d_min (= C1) | 0 | 98.441 | 95.984 | 94.507 | 93.600 | 92.821 | 92.015 | 91.426 | 90.765 |
| SUB + d_tail (median over A without C1) | 0.0131 | 98.441 | 96.016 | 94.559 | 93.664 | 92.895 | 92.099 | 91.518 | 90.866 |
| SUB + d_max (= T2) | 0.0502 | 98.441 | 96.107 | 94.704 | 93.843 | 93.103 | 92.338 | 91.778 | 91.150 |

## Hand-off ([R13_RESULT.json](R13_RESULT.json))

- **Round 14 (path drift).** The anchor's CV tail grows with ageing: a step from anchor 1 to anchor 2, then a slow rise, with τ2 going from 412 s to 503 s. The 25 °C top-ups' tails stay flat. This makes the growing tail a candidate from-empty path effect.
- **Round 15 (probe plan).** The open variable is the checkup's CV termination: does it stop at 5.1 A (C1), at a lower current, or after a hold? Any answer on it, from a probe or from the organisers, collapses the envelope to a single scenario. Under the admitted tail model that is between 0 and +0.12 Ah at CK7. The relaxed-voltage estimator (T2) cannot narrow it: its scale depends on an s_top that the unrelaxed CK0 top does not define.
- **Compared with round 11's transfer bound,** d ∈ [−0.036, +0.052]: this round's admitted set [0, 0.050] lies inside it and removes the negative side for the tail term.

---

<a id="zh"></a>

# WP3 — 包络、决策与交接

> [English](#en) · 中文

登记的规则（`wp1/protocol.json`，提交 `7960a99`）由 `src/run_wp3.py` 中的 `tail.decide` 应用到 WP2 的测量结果上。没有使用任何 P_k 或代理误差。

**结论先读。**

- **结果：O3"无法识别"。** 准入集 A 上的包络为 **0.412 Ah**，超过 0.30 Ah 的门槛。按登记规则，本轮报告包络、写出结果后退出。**SUB 不变。**
- **包络由 T2（+0.412 Ah）对 C1（0）决定。** 六个尾巴模型成员（M4 × C2–C7）落在 +0.041…+0.124 Ah。
- **A 的每个成员符号相同：要么为正，要么恰为 0（C1）。** 如果检查在 CV 中充得比锚点的 5.1 A 终点更深，尾巴漂移就会让 ε 随衰减上升。在准入集内，ε 漂移的顶部尾巴部分被限定在 **CK7 处 [0, +0.41] Ah**，即 CK7 的 SOH 最多 **+0.39 pp**，中位数为 +0.10 pp（d_tail = 0.0131 Ah/Ah）。
- **P_drift 来自顶部尾巴的动机没有被排除。** 排除它需要 O1。在 C1 情景下（检查同样在 5.1 A 停止），尾巴漂移恰为 0。数据中没有任何信息说明检查用的是哪种终止方式。
- **未登记的诊断（不用于决定结果）。**
  - 去掉 T2，或者 T2 改用 [0.25, 1.0] Ah 窗口，该集合就是可识别的：包络 0.124 Ah，所有成员为正，|d·8.2| 中位数 = 0.107 Ah。这是一个勉强的 O2，只比 0.10 的门槛高 0.007 Ah。
  - 因此，登记的 O3 取决于 T2 的主窗口：在这个窗口里，CK0 曲线的陡峭顶部与平台相接，V30 每 1 mV 对应 0.045 Ah。
  - 这一敏感性报告给第 14/15 轮，不改变登记的结果。

## 准入集 A 与规则

（成员表同英文部分。）没有 M1、M2、M3 成员，因为它们在锚点 1–7 中的任何一个上都没有准入。

| 规则 | 数值 | 结果 |
|---|---|---|
| 包络 = A 上 d·8.2 的最大值减最小值 | 0.412 − 0.000 = **0.412 Ah** | > 0.30 → **O3"无法识别"** |
| （O1 检验，未执行到） | T2 为 0.412，M4 C4–C7 为 0.107–0.124，都超过 0.10 | 会失败 |
| （O2 检验，未执行到） | 除 C1 外所有成员为正；\|d·8.2\| 中位数 = 0.108 Ah | 会通过，但可识别性先失败了 |

检验的顺序是登记好的：先检验可识别性。

## SOH 变体（只用于排行榜，绝不与代理对比打分）

`add_drift` 取自第 11 轮的 `drift.py`：Q' = Q + d·max(0, 100.41 − Q)。在 O3 下没有候选；写出这些变体只是因为 WP3 的清单要求（D14）。各检查点的 SOH 见英文部分的表。

## 交接（[R13_RESULT.json](R13_RESULT.json)）

- **第 14 轮（路径漂移）。** 锚点的 CV 尾巴随老化增长：从锚点 1 到锚点 2 有一个台阶，之后缓慢上升，τ2 从 412 s 增至 503 s。25 °C 补电的尾巴保持平坦。这使增长的尾巴成为一个从空充电路径效应的候选。
- **第 15 轮（探针计划）。** 未知量是检查的 CV 终止方式：它是在 5.1 A 停止（C1）、在更低的电流停止，还是保持一段时间后停止？无论是通过探针还是向主办方了解，只要知道这一点，包络就会收缩到单一情景。在准入的尾巴模型下，该情景的影响在 CK7 处介于 0 到 +0.12 Ah 之间。静置电压估计（T2）无法收窄它：它的尺度取决于 s_top，而未静置的 CK0 顶部无法确定 s_top。
- **与第 11 轮的迁移界相比**（d ∈ [−0.036, +0.052]）：本轮的准入集 [0, 0.050] 落在其中，并且排除了尾巴项的负值一侧。
