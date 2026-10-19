<a id="en"></a>

# Round 14 WP1 — Registration: report

> **Language:** English · [中文](#zh)

Registered 2026-10-19, before any WP2 output. Nothing in this WP was computed on challenge data. The protocol is `wp1/protocol.json`, with SHA256 in `wp1/protocol.sha256`; the code hashes are inside the protocol.

## Conclusions

- **Registered:** the Ah chain, the signals P1 / P1b / P2 / P3 (plus a descriptive gap-bridged P1), the statistics and the decision rules (copied verbatim).
  - Round 12's `ahchain.py` was not on origin at 22:26 (tip `bd7ab9d`), so the same rule is implemented in `src/ahchain.py`.
- **Synthetic test: 19/19 pass** (`synthetic_test.log`, `synthetic_test.json`).
  - Planted A → T1 offsets (0.10–0.15 Ah) are recovered with a maximum error of 4·10⁻¹³ Ah, against a tolerance of 0.005 Ah. This includes the 45 °C anchor and a segment with a paused-recording gap.
  - The λ fallback chain works, and the gap rule removes the gap pair.
  - The statistics, the 3-MAD flag and all 9 decision scenarios behave as intended.
- **What the outcome can be, known from the WP0 structure alone (no Ah values used):**
  1. **P1 has exactly 5 points** (anchors 1, 2, 4, 5, 6). Anchors 3 and 7 have recording gaps between A and T1, and the registered gap rule excludes them. Each LOO fit uses 4 points.
  2. **P1b is not estimable.** A second top-up exists only for anchors 5 and 6 (2 points < 5). It would not add information anyway: in segments 10 and 12, λ comes from the T1 → T2 pair itself, so Term3' = Term3 exactly.
  3. Both O1 and O2 require P1b, so **neither can be reached.** The attainable outcomes are "not identifiable" (noise gate), "O3 not identifiable" (LOO wider than 0.30 Ah) and "O3 inconclusive".
  - The round still delivers its estimate: d_path with its LOO range, the days slope, the BIC, P2 and the descriptive gap-bridged 7-anchor series, all passed to round 15.

## Registered choices where the prompt left room

All are also logged in `notes/DECISIONS.md` (D10–D16).

| Topic | Registered choice | Why |
|---|---|---|
| σ_TT,25 with λ "without that pair" | Computed under two readings of the "< 2 TT pairs" fallback. *Reduced*: count after removing the pair, so a 25 °C pair falls back to λ_45. *Full*: count the full set, so the other 25 °C pair's λ is used. **Gate = the larger value** | Both keep the rule. 25 °C has only 2 TT pairs, so the two readings differ |
| P1b with < 5 points | Not estimable, so the O1/O2 conditions that need it are **not met** | Same statistics as P1 (≥ 5 points); claiming O1/O2 without the robustness check would not be conservative |
| LOO | n Theil–Sen fits on n − 1 points; range = [min, max] | The 5-point minimum is stated for d_path; LOO is by definition n − 1 |
| Anchor 3 in P1 | Excluded by the gap rule; the "without anchor 3" sensitivity therefore equals the main estimate. Anchor 3 stays in P2 | The prompt keeps anchor 3 despite its unrelaxed start; the gap rule is a separate registered rule |
| "3 MAD" | Raw MAD of the Theil–Sen residuals (≈ 2σ for Gaussian noise) | Literal; the prompt writes "1.4826·MAD" where it means the scaled value. Flags only drive a sensitivity |
| Gap pairs | Main estimates exclude them. A **descriptive** S_gap series keeps them, using the package integration (gaps > 600 s carry zero weight; WP0 F9 shows the counters flat across them) | Gives round 15 the 7-anchor picture without touching the rule |
| BIC | OLS fits; BIC = n ln(RSS/n) + k ln n, k = 2 / 3; ΔBIC = BIC_const − BIC_linear ≥ 2 | Standard Gaussian BIC |

## What each outcome would mean

| Outcome | Condition (registered) | Meaning for the pack | Consequence |
|---|---|---|---|
| **not identifiable** (noise gate) | σ_TT,25 > 0.30 Ah | The 25 °C Ah chain is too noisy to see a top difference of a few tenths of an Ah | d_path unmeasured; SUB unchanged; round 15 needs another handle (probe or a different chain) |
| **O3 not identifiable** | P1 < 5 points, or LOO range of E wider than 0.30 Ah | The path-drift trend cannot be pinned to within ±0.15 Ah at CK7 on this pack | SUB unchanged; the LOO envelope is passed to round 15 as a bound, not as an estimate |
| **O1 path drift small** | LOO E ⊂ [−0.10, +0.10] Ah and \|P1b E\| ≤ 0.15 Ah | From-empty and top-up tops move together with age: the path part of the ε drift is closed on this pack | SUB unchanged; together with round 13 (tail), the top-of-charge motivation for P_drift weakens. *Not reachable here (P1b not estimable)* |
| **O2 path drift material** | LOO E excludes 0, \|E\| > 0.10 Ah, ΔBIC ≥ 2, P1b same sign | The top-up top drifts against the from-empty top by > 0.1 Ah at CK7 | Candidate "SUB + d_path", leaderboard-only; round 15 plans a probe. *Not reachable here (P1b not estimable)* |
| **O3 inconclusive** | any other case | A width-limited estimate exists but does not meet O1 or O2 | SUB unchanged; d_path (median, LOO range) passed to round 15, and to d_top if round 13 is available |

## Files

| File | Content |
|---|---|
| `protocol.json` | the full registration (events, Ah chain, signals, statistics, verbatim and operational rules, structure known from WP0, code SHA256) |
| `protocol.sha256` | SHA256 of `protocol.json` |
| `synthetic_test.log`, `synthetic_test.json` | the 19 synthetic tests and their results |
| `../src/ahchain.py`, `signals.py`, `stats14.py`, `decide.py`, `data14.py`, `test_synthetic.py` | registered code |

---

<a id="zh"></a>

# 第 14 轮 WP1 — 登记：报告

> [English](#en) · 中文

于 2026-10-19 在任何 WP2 输出之前登记。本工作包没有在赛题数据上计算任何东西。协议为 `wp1/protocol.json`，其 SHA256 在 `wp1/protocol.sha256` 中；代码的哈希写在协议里。

## 结论

- **已登记：** 电量链、信号 P1 / P1b / P2 / P3（另加一个描述性的、跨记录间隙的 P1）、统计方法和决策规则（原样照抄）。
  - 22:26 时第 12 轮的 `ahchain.py` 不在 origin 上（末端 `bd7ab9d`），因此在 `src/ahchain.py` 中按同一规则自行实现。
- **合成测试：19/19 通过**（`synthetic_test.log`、`synthetic_test.json`）。
  - 植入的 A → T1 偏移（0.10–0.15 Ah）找回的最大误差为 4·10⁻¹³ Ah，容差为 0.005 Ah。其中包括 45 °C 锚点，以及一段带记录暂停间隙的数据。
  - λ 的后备链正常工作，间隙规则会去掉带间隙的配对。
  - 统计方法、3-MAD 标记和全部 9 个决策情景都符合预期。
- **仅凭 WP0 的结构（未使用任何电量值）就能知道结果的可能范围：**
  1. **P1 正好 5 个点**（锚点 1、2、4、5、6）。锚点 3 和 7 在 A 与 T1 之间有记录间隙，登记的间隙规则将其排除。每个留一拟合用 4 个点。
  2. **P1b 无法估计。** 只有锚点 5、6 有第二次补电（2 个点 < 5）。即便能估计也不会带来新信息：在第 10、12 段，λ 就来自 T1 → T2 这个配对本身，所以 Term3' 与 Term3 完全相等。
  3. O1 和 O2 都要求 P1b，因此**两者都不可能达到。** 可能的结果只有"无法识别"（噪声门）、"O3 无法识别"（LOO 宽于 0.30 Ah）和"O3 无定论"。
  - 本轮仍会给出它的估计：d_path 及其 LOO 范围、对天数的斜率、BIC、P2，以及描述性的跨间隙 7 锚点序列，全部交给第 15 轮。

## prompt 留有余地之处的登记选择

全部同时记在 `notes/DECISIONS.md`（D10–D16）。

| 主题 | 登记的选择 | 理由 |
|---|---|---|
| "排除该配对本身"时的 σ_TT,25 | 对"不足 2 个 TT 配对"的后备条件按两种读法计算。*缩减读法*：去掉该配对后再计数，所以 25 °C 配对退回用 λ_45。*全集读法*：按全集计数，所以用另一个 25 °C 配对的 λ。**噪声门取较大值** | 两种读法都符合规则。25 °C 只有 2 个 TT 配对，所以两者会不同 |
| P1b 不足 5 个点 | 无法估计，因此 O1/O2 中需要它的条件**不满足** | 与 P1 用同样的统计（≥ 5 个点）；不做稳健性检查就宣称 O1/O2 不够保守 |
| 留一 | n 个各用 n − 1 个点的 Theil–Sen 拟合；范围 = [最小, 最大] | 5 个点的下限是对 d_path 规定的；留一按定义就是 n − 1 |
| P1 中的锚点 3 | 被间隙规则排除；因此"去掉锚点 3"的敏感性分析与主估计相同。锚点 3 保留在 P2 中 | prompt 保留锚点 3 是针对其起点未静置；间隙规则是另一条登记规则 |
| "3 MAD" | Theil–Sen 残差的原始 MAD（高斯噪声下约 2σ） | 按字面理解；prompt 在指缩放值时写的是"1.4826·MAD"。标记只用于敏感性分析 |
| 带间隙的配对 | 主估计排除。另设一个**描述性**的 S_gap 序列保留它们，使用包内积分（> 600 s 的间隙权重为零；WP0 F9 显示计数器在间隙上不变） | 不碰规则，同时给第 15 轮提供 7 个锚点的全貌 |
| BIC | 最小二乘拟合；BIC = n ln(RSS/n) + k ln n，k = 2 / 3；ΔBIC = BIC_常数 − BIC_线性 ≥ 2 | 标准高斯 BIC |

## 各结果意味着什么

| 结果 | 条件（已登记） | 对电池组意味着什么 | 后果 |
|---|---|---|---|
| **无法识别**（噪声门） | σ_TT,25 > 0.30 Ah | 25 °C 的电量链噪声太大，看不到零点几 Ah 的顶部差 | d_path 未测得；SUB 不变；第 15 轮需要别的抓手（探测或另一条电量链） |
| **O3 无法识别** | P1 不足 5 个点，或 E 的 LOO 范围宽于 0.30 Ah | 在本电池组上，路径漂移趋势无法在 CK7 处定到 ±0.15 Ah 以内 | SUB 不变；LOO 包络作为界限（而不是估计）交给第 15 轮 |
| **O1 路径漂移小** | LOO E ⊂ [−0.10, +0.10] Ah 且 \|P1b E\| ≤ 0.15 Ah | 从空充满和补电的顶部随老化同步移动：本电池组上 ε 漂移的路径部分可以关闭 | SUB 不变；与第 13 轮（尾巴）合起来，P_drift 的充电顶部动机减弱。*本轮不可达（P1b 无法估计）* |
| **O2 路径漂移显著** | LOO E 不含 0，\|E\| > 0.10 Ah，ΔBIC ≥ 2，P1b 同号 | 到 CK7 时补电顶部相对从空充满的顶部漂移超过 0.1 Ah | 候选"SUB + d_path"，只用于排行榜；第 15 轮规划探测。*本轮不可达（P1b 无法估计）* |
| **O3 无定论** | 其他所有情况 | 有一个宽度受限的估计，但不满足 O1 或 O2 | SUB 不变；d_path（中位数、LOO 范围）交给第 15 轮，若第 13 轮可用也并入 d_top |

## 文件

| 文件 | 内容 |
|---|---|
| `protocol.json` | 完整登记（事件、电量链、信号、统计、原文与可执行的规则、WP0 已知的结构、代码 SHA256） |
| `protocol.sha256` | `protocol.json` 的 SHA256 |
| `synthetic_test.log`、`synthetic_test.json` | 19 个合成测试及其结果 |
| `../src/ahchain.py`、`signals.py`、`stats14.py`、`decide.py`、`data14.py`、`test_synthetic.py` | 登记的代码 |
