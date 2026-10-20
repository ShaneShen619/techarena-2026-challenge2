<a id="en"></a>

# WP1 — Registration

> **Language:** English · [中文](#zh)

## Conclusions

- **Only one probe is eligible: P_A3fix.** It is round 12's anchor-3 bottom correction (one scalar, a_3^rel = 0.3047 Ah). WP2 decides whether it is readable and worth a submission.
  - **P_level:** not eligible (round 12 = L3).
  - **P_drift:** not eligible (rounds 13 and 14 are both O3; neither reached O2).
  - **P_stress_early:** dropped. It cannot be rebuilt on the current SUB without refitting its fusion weight against proxies, and it is not a one-scalar change.
- **The hypothesis grid is round 6's, unchanged:** Δ {0, 0.4, 0.8} × f {0, 0.5, 1} × d {0, −0.031}, 18 hypotheses. Round 12's L3 keeps the Δ axis. Rounds 13 and 14 are present but not identifiable, so the d axis is not replaced. As a conservative gate, a probe must also be readable on round 11's d range {−0.036, 0, +0.052} (D10).
- **No leaderboard observations yet**, so the surviving set is the full grid.
- **The machinery reproduces round 6 exactly:** 216 score cells to 4e-14, the P_drift Δs to 1e-15, and p_k independently to 1.4e-14 Ah. All 7 tests pass ([test_wp1.json](test_wp1.json)).
- Protocol: [protocol.json](protocol.json); hashes of the protocol and the registered code: [protocol.sha256](protocol.sha256). Both were committed before any WP2 output.

## What is registered

| Item | Registered choice |
|---|---|
| Truth vectors | T_k(h) = Q_fc,k + ε0 + Δ − f·R_k + d·L_k, exactly as round 6 (p_k and R_k listed in the protocol) |
| Grids | G_main (18, decides); G_r11 (27, readability gate); G_env (54, descriptive) |
| Metric family | s (round 6), nMAE, nRMSE, nMAX, each relative to ExampleModel under the same h; all scores from the package CLI output |
| Eligible probes | P_A3fix only, rebuilt from round 12's registered hook; it must reproduce round 12's SOH vector exactly |
| Free information first | a hypothesis survives if some metric matches every shown value within one display unit; if none survives, keep the full grid and flag the inconsistency |
| Readable | the same sign of Δs under all four metrics for ≥ 80 % of surviving hypotheses, on G_main **and** G_r11 |
| Chosen | readable, and the expected Δs is negative under every metric; rank by the worst metric's expectation, then the worst case; at most two |
| Reading | tol = display precision (0.005 if unknown); Δ < −tol adopt; Δ > +tol revert and drop the branch; otherwise no information and revert; with several metrics, a probe wins only if one improves and none worsens beyond tol |
| End state | the last submission is the best observed option (SUB by default); re-upload SUB right after a probe's evaluation unless it won; assume ≤ 2 evaluation cycles remain |
| Compliance | ≤ 2 probes, one scalar each, disclosed; no per-checkup edits; nothing is uploaded or sent by this round |

## What each outcome would mean

| WP2 outcome | Meaning | Action |
|---|---|---|
| No eligible probe is readable, or none is expected to win under every metric | the leaderboard cannot answer a one-scalar question safely under the unknown metric | **no probe; keep SUB**; WP3 builds nothing to upload; the hand-over says to keep `Current State_Challenge2.zip` as the last submission |
| P_A3fix is chosen | under every metric and almost every hypothesis, the board's sign would tell whether anchor 3's bottom offset should be removed | WP3 builds its zip; upload once, read with the rules below |

| P_A3fix board reading (vs SUB) | Meaning | Action |
|---|---|---|
| better by > tol on a shown metric, worse on none | the hidden CK4 capacity sits closer to the anchor-3-corrected estimate: anchor 3's charge did start from a deeper, unrelaxed state | adopt a_3^rel; final package built in WP4 (wiring is the user's call) |
| worse by > tol on a shown metric | the correction overshoots at CK4: either anchor 3 is not biased, or the truth at CK4 is higher (large Δ, no drift) | revert to SUB; drop the hypotheses that predicted a clear win |
| within tol | the board's precision or metric does not see the CK4 change | revert to SUB; no information |

## Compliance note on P_A3fix

The change is a single data-derived constant applied to one anchor (segment 6). Its effect is concentrated on CK4 (−0.36 pp; CK5–CK7 −0.02 pp). A board reading is therefore mostly one bit of information about CK4. That is not a reconstruction of the value, and the constant was measured from operating data in round 12, not tuned to the board. It must still be disclosed if submitted.

---

<a id="zh"></a>

# WP1 — 登记

> [English](#en) · 中文

## 结论

- **只有一个探针合格：P_A3fix。** 它是第 12 轮的锚点 3 底部修正（一个标量，a_3^rel = 0.3047 Ah）。是否可解读、是否值得提交，由 WP2 决定。
  - **P_level：** 不合格（第 12 轮 = L3）。
  - **P_drift：** 不合格（第 13、14 轮都是 O3，没有一轮达到 O2）。
  - **P_stress_early：** 放弃。不对代理标签重新拟合其融合权重，就无法在当前 SUB 上重建它；而且它不是单标量改动。
- **假设网格就是第 6 轮的，没有改动：** Δ {0, 0.4, 0.8} × f {0, 0.5, 1} × d {0, −0.031}，共 18 个假设。第 12 轮是 L3，所以 Δ 轴保留。第 13、14 轮存在但不可识别，所以 d 轴不替换。作为保守的门槛，探针还必须在第 11 轮的 d 范围 {−0.036, 0, +0.052} 上可解读（D10）。
- **目前没有排行榜观测**，所以存活集就是整个网格。
- **这套方法完全复现了第 6 轮：** 216 个得分单元误差 4e-14，P_drift 的 Δs 误差 1e-15，p_k 独立复算误差 1.4e-14 Ah。7 项测试全部通过（[test_wp1.json](test_wp1.json)）。
- 协议：[protocol.json](protocol.json)；协议和登记代码的哈希：[protocol.sha256](protocol.sha256)。两者都在任何 WP2 输出之前提交。

## 登记内容

| 项目 | 登记的选择 |
|---|---|
| 真值向量 | T_k(h) = Q_fc,k + ε0 + Δ − f·R_k + d·L_k，与第 6 轮完全相同（p_k 和 R_k 列在协议里） |
| 网格 | G_main（18，决定）；G_r11（27，可解读性门槛）；G_env（54，只作描述） |
| 指标族 | s（第 6 轮）、nMAE、nRMSE、nMAX，各自相对同一 h 下的 ExampleModel；所有得分都用包 CLI 的输出 |
| 合格探针 | 只有 P_A3fix，按第 12 轮登记的钩子重建；必须完全复现第 12 轮的 SOH 向量 |
| 先用免费信息 | 若对每个显示值都有某个指标在一个显示单位内相符，则该假设存活；若没有存活者，保留整个网格并标注不一致 |
| 可解读 | 在 ≥ 80 % 的存活假设上，四个指标的 Δs 符号相同，G_main **和** G_r11 都要满足 |
| 选中 | 可解读，且在每个指标下期望 Δs 都为负；按最差指标的期望排序，再按最坏情况排序；最多两个 |
| 解读 | tol = 显示精度（未知时 0.005）；Δ < −tol 采纳；Δ > +tol 退回并排除该分支；否则无信息并退回；有多个指标时，只有某个指标改善且没有指标变差超过 tol，探针才算胜出 |
| 最终状态 | 最后一次提交是观测到的最佳选项（默认 SUB）；探针的评估结果出来后，除非它胜出，立即重新上传 SUB；假设最多还剩 2 个评估周期 |
| 合规 | 最多 2 个探针，每个只改一个标量，全部披露；不做逐个检查点的修改；本轮不上传、不发送任何东西 |

## 各结果意味着什么

| WP2 结果 | 含义 | 行动 |
|---|---|---|
| 没有合格探针可解读，或没有一个在每个指标下都预期胜出 | 在指标未知的情况下，排行榜无法安全地回答一个单标量问题 | **不做探针，保留 SUB**；WP3 不构建要上传的包；交接说明写明保持 `Current State_Challenge2.zip` 为最后一次提交 |
| 选中 P_A3fix | 在每个指标、几乎每个假设下，榜单的符号都能说明是否应去掉锚点 3 的底部偏差 | WP3 构建它的 zip；上传一次，按下表解读 |

| P_A3fix 榜单读数（相对 SUB） | 含义 | 行动 |
|---|---|---|
| 某个显示指标好于 SUB 超过 tol，且没有指标变差 | CK4 的隐藏容量更接近锚点 3 修正后的估计：锚点 3 的充电确实从更深、未松弛的状态开始 | 采纳 a_3^rel；最终包在 WP4 中构建（是否接入由用户决定） |
| 某个显示指标差于 SUB 超过 tol | 修正在 CK4 处过头了：要么锚点 3 没有偏差，要么 CK4 的真值更高（Δ 大、无漂移） | 退回 SUB；排除那些预测明显胜出的假设 |
| 在 tol 以内 | 榜单的精度或指标看不出 CK4 的变化 | 退回 SUB；无信息 |

## 关于 P_A3fix 的合规说明

这个改动是一个由数据得出的常数，只作用于一个锚点（第 6 段）。它的影响集中在 CK4（−0.36 pp；CK5–CK7 −0.02 pp），所以榜单读数主要是关于 CK4 的一比特信息。这不是对该值的重建，而且这个常数是第 12 轮从运行数据中测得的，不是对着榜单调出来的。如果提交，仍必须披露。
