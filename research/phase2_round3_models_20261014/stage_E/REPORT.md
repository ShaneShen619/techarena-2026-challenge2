<a id="en"></a>

# Stage E — Four-cell pack-cutoff / ε-drift scenarios

> **Language:** English · [中文](#zh)

**Result: under the registered scenarios, ε drift ranges from zero (S0) to as much as 0.5 pp (S1). The scenario that gives large drift (S1) conflicts with the data, but cannot be ruled out. Following the registered decision rule, a leaderboard-only variant `V2_S1` was produced. It is not recommended and not scored.**

Protocol: `protocol.json`. Nothing in this stage is scored on the proxies, because the proxies are the anchors themselves.

## Scenarios (`run_e.py`, `outputs/E_*`)

| Scenario | Assumption | Max \|ε drift\| |
|---|---|---|
| S0 cancellation | The checkup discharge ends at the pack 11.2 V root, and the anchor charge starts from there. The start state cancels. | 0 by construction |
| S1 no cancellation | ε = Ah still dischargeable at 5.1 A from the anchor start state to the pack 11.2 V root. The per-cell start rest voltage, minus a relaxation offset ΔV, is converted on the CK0 loaded tail. | 0.51 / 0.41 / 0.26 pp for ΔV = 0 / 0.05 / 0.10 V |
| S2 cell-limited top | The checkup's full charge stops at the first cell's limit, not at pack CV. Drift follows the per-cell top-state spread. | 0.03 pp |

**Evidence for and against S1.**

- **For, a sanity check.** With ΔV = 0.05 V, S1 reproduces the CK0-defined ε0 (0.285 vs 0.288 Ah) and the assumed 25 °C offset (0.71 vs ε0 + 0.4 = 0.69 Ah).
- **Against, a direct test.** Under S1, a deeper start (the post-CK3 anchor, 0.4–0.5 Ah less residual) should raise Q_fc by the same amount. Stage A shows that Q_fc residuals are uncorrelated with the start state (r = 0.04). The rest-voltage differences therefore do not behave like SOC differences, so S1's drift values are better read as an upper bound on the risk than as an estimate.
- **The top-of-charge spread (S2) is small.** The per-cell step offsets drift (cell 1 −0.20 → −0.42 Ah, cell 4 −0.21 → −0.01 Ah), but the leading cell's offset barely changes. A cell-limited checkup charge would therefore move ε by ≤ 0.03 pp.

## Leaderboard-only variant (`outputs/E_leaderboard_only_V2_S1.csv`)

`V2_S1` uses ε_(k−1) = x*_(k−1) (S1, ΔV = 0.05 V) for the anchor in place of ε0 + 0.4. The resulting SOH (%) is:

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| V2 | 95.992 | 95.137 | 93.541 | 92.811 | 92.081 | 91.331 | 90.821 |
| V2_S1 | 95.992 | 95.159 | 93.563 | 92.421 | 92.270 | 91.667 | 90.970 |
| difference (pp) | 0.000 | +0.022 | +0.022 | −0.390 | +0.189 | +0.336 | +0.149 |

These differences are as large as V2's whole proxy error. This is why the checkup protocol (what happens between the C/20 discharge and the next operating charge) remains the main unverified risk. **Recommendation:** do not submit `V2_S1` without information on the checkup protocol. If a spare submission slot is ever used as a probe, the leaderboard difference between V2 and `V2_S1` would show which scenario is closer.

---

<a id="zh"></a>

# 阶段 E——四芯组端截止 / ε 漂移情景

> **语言：** [English](#en) · 中文

**结果：在登记的几种情景下，ε 漂移从零（S0）到最多 0.5 pp（S1）不等。给出大漂移的情景（S1）与数据相矛盾，但无法排除。按登记的决策规则，生成了一个只供排行榜检验的变体 `V2_S1`；不推荐使用，也不评分。**

协议：`protocol.json`。代理标签本身就是锚点，所以本阶段的任何结果都不在代理上评分。

## 情景（`run_e.py`、`outputs/E_*`）

| 情景 | 假设 | 最大 \|ε 漂移\| |
|---|---|---|
| S0 抵消 | 检查放电止于组端 11.2 V 的根，锚点充电从该状态开始，起点状态抵消 | 按构造为 0 |
| S1 不抵消 | ε = 从锚点充电起点以 5.1 A 还能放到组端 11.2 V 的 Ah。各芯起点静置电压减去弛豫偏置 ΔV 后，在 CK0 带载尾段上换算 | ΔV = 0 / 0.05 / 0.10 V 时分别为 0.51 / 0.41 / 0.26 pp |
| S2 单芯限顶 | 检查的满充在第一颗电芯到限时就结束，而不是组端 CV。漂移随各芯顶部状态的离散而变 | 0.03 pp |

**支持与反对 S1 的证据。**

- **支持（合理性检验）。** 取 ΔV = 0.05 V 时，S1 复现了由 CK0 定义的 ε0（0.285 对 0.288 Ah），也复现了假定的 25 °C 偏置（0.71 对 ε0 + 0.4 = 0.69 Ah）。
- **反对（直接检验）。** 按 S1，起点更深（CK3 之后的锚点，剩余电量少 0.4–0.5 Ah）应当让 Q_fc 增加同样的量。但阶段 A 显示 Q_fc 残差与起点状态不相关（r = 0.04）。可见静置电压的差异不像 SOC 差异，所以 S1 给出的漂移更适合看作风险上限，而不是估计值。
- **顶部离散（S2）很小。** 各芯台阶偏移在漂移（电芯 1 −0.20 → −0.42 Ah，电芯 4 −0.21 → −0.01 Ah），但领先那颗电芯的偏移几乎不变，所以即使检查满充是单芯限顶，ε 也只会移动 ≤ 0.03 pp。

## 只供排行榜检验的变体（`outputs/E_leaderboard_only_V2_S1.csv`）

`V2_S1` 把锚点的 ε 由 ε0 + 0.4 换成 ε_(k−1) = x*_(k−1)（S1，ΔV = 0.05 V），得到的 SOH（%）如下：

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| V2 | 95.992 | 95.137 | 93.541 | 92.811 | 92.081 | 91.331 | 90.821 |
| V2_S1 | 95.992 | 95.159 | 93.563 | 92.421 | 92.270 | 91.667 | 90.970 |
| 差值（pp） | 0.000 | +0.022 | +0.022 | −0.390 | +0.189 | +0.336 | +0.149 |

这些差值与 V2 全部的代理误差同量级，这正是检查协议（C/20 放电与下一次运行充电之间发生了什么）仍是最大未验证风险的原因。**建议：** 在拿到检查协议信息之前，不要提交 `V2_S1`。如果将来用一次多余的提交机会做探测，V2 与 `V2_S1` 在排行榜上的差异可以显示哪种情景更接近事实。
