<a id="en"></a>

# WP2 — Uncertainty-weighted fusion of the stress model and SUB

> **Language:** English · [中文](#zh)

- **Protocol:** [protocol.json](protocol.json), committed `3b270ab` before any evaluation. Variances, class weights and the selection were estimated on pseudo + cold-start scenarios only and committed (`c30e43b`) before the real run. Code: [run_wp2.py](run_wp2.py).
- **Exposure:** real numbers are exposed proxies.

## Conclusions first

1. **No fusion design passes every gate against SUB. No candidate class is produced; SUB stays.**
2. **The registered main F2_S_A (class weights) fails on the real proxies.**
   - On pseudo + cold start it was best (score 0.125 vs SUB 0.161). Its estimated weights were 1 for the cold, phase and √t-gap classes and 0.5 for fallback, so it reduces to the stress model almost everywhere.
   - On the real proxies that gives CK1 −0.561 and CK2 −0.638 pp, failing G-proxy, G-epsfree, G-robust, G-regress and G-hyp.
3. **Lesson: the causal scenarios do not represent CK1 and CK2.**
   - The "cold" class in pseudo/CS consists of later months with earlier anchors removed; the real cold case is the very first month (break-in).
   - The "gap" class in pseudo/CS is a cut of a few days; the real CK2 gap is a whole missing 45 °C segment.
   - Weights learned per class therefore transfer badly to exactly the two checkups where SUB and S disagree most.
4. **F1 (inverse variance) behaves best.**
   - F1_S_A (not exposed) has real MAE 0.141 / 0.128 / 0.174 and MAX 0.282 / 0.232 / 0.624. It loses to SUB at Δ = 0.4 (0.128 vs 0.123) and 0.8, but wins on the causal tests (pseudo 0.119 vs 0.148; cold start 0.141 vs 0.174).
   - The exposed-CK1 versions F1_S_B and F1_S_C have MAE 0.196 / 0.116 / 0.118 and MAX 0.545 / 0.192 / 0.239. They pass G-proxy and G-robust, but miss G-epsfree (0.137 vs a 0.119 requirement) and G-hyp (max regret 0.029 vs SUB 0.027). By rule 3 they cannot be selected anyway.

## Estimated parameters (pseudo + CS, Δ = 0.4, main step)

| Quantity | Value |
|---|---|
| σ_S0 (S_A = S_B = S_C on pseudo/CS) | see [wp2_estimated_params.json](outputs/wp2_estimated_params.json) |
| σ_SUB: phase / sqrt_gap / fallback / pooled (Ah) | 0.250 / 0.179 / 0.245 / 0.208 |
| F2 weights (cold, phase, sqrt_gap, fallback) | 1, 1, 1, 0.5 (for all S variants) |
| Cases per class (S_A) | cold 10, phase 4, sqrt_gap 12, fallback 2 |

S_B and S_C are identical to S_A on every pseudo/CS case. As expected, their rules change only month 0, i.e. only CK1.

## Results

Real proxies, main step, A4 2 Ah, in pp. G-hyp columns come from the WP1 grid with each design added ([hypothesis table](outputs/wp2_hypothesis_decision_table.csv)).

| Model | MAE Δ0 / .4 / .8 | MAX Δ0 / .4 / .8 | ε-free | Pseudo | Cold | Max regret | Worst s |
|---|---|---|---|---|---|---|---|
| **SUB** | 0.207 / 0.123 / 0.140 | 0.609 / 0.228 / 0.228 | 0.139 | 0.148 | 0.174 | **0.027** | 0.225 |
| **F2_S_A (main)** | 0.186 / 0.242 / 0.298 | 0.638 / 0.638 / 0.953 | 0.189 | **0.106** | 0.144 | 0.095 | 0.208 |
| F1_S_A | 0.141 / 0.128 / 0.173 | 0.282 / 0.232 / 0.624 | 0.137 | 0.119 | **0.141** | 0.042 | 0.214 |
| F3_S_A | 0.167 / 0.147 / 0.189 | 0.425 / 0.328 / 0.564 | 0.159 | 0.120 | 0.149 | 0.051 | 0.212 |
| F1_S_B / F1_S_C (exposed-CK1) | 0.196 / 0.116 / 0.118 | 0.545 / 0.192 / 0.239 | 0.137 | 0.119 | 0.141 | 0.029 | 0.219 |
| F2_S_B / F2_S_C (exposed-CK1) | 0.217 / 0.163 / 0.219 | 0.638 / 0.638 / 0.638 | 0.189 | 0.106 | 0.144 | 0.080 | 0.212 |
| F3_S_B / F3_S_C (exposed-CK1) | 0.207 / 0.137 / 0.149 | 0.496 / 0.328 / 0.288 | 0.159 | 0.120 | 0.149 | 0.045 | 0.215 |

**Per-checkup errors at Δ = 0.4 (pp):**

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| SUB | +0.217 | −0.018 | +0.080 | +0.228 | +0.150 | −0.163 | −0.004 |
| F2_S_A | −0.561 | −0.638 | −0.035 | +0.100 | −0.007 | −0.209 | +0.144 |
| F1_S_A | −0.232 | −0.118 | −0.065 | +0.145 | +0.049 | −0.192 | +0.092 |
| F1_S_B (exposed) | +0.153 | −0.118 | −0.065 | +0.145 | +0.049 | −0.192 | +0.092 |

**Gates** ([wp2_gates.json](outputs/wp2_gates.json)): every design fails at least one. F1_S_A fails G-proxy, G-epsfree, G-robust and G-hyp; F2 and F3 fail more.

## What this means

- From CK3 on, the fusion and the stress model match or beat SUB. The decisive checkpoints are CK1 and CK2, where neither the causal tests nor the physics settle which model is right. They are also the checkpoints where SUB (√t, CK2) and the stress models (CK1 rules) each rely on an exposed choice.
- A causal test that resembles CK1 and CK2 does not exist in this data. That is a structural limit, not a tuning problem.
- WP6 should therefore treat "SUB vs F1-type fusion" as a leaderboard question.

---

<a id="zh"></a>

# WP2——应力模型与 SUB 的不确定度加权融合

> **语言：** [English](#en) · 中文

- **协议：** [protocol.json](protocol.json)，在任何评估之前于 `3b270ab` 提交。方差、类别权重和选择都只在伪场景 + 冷启动场景上估计，并在真实运行之前提交（`c30e43b`）。代码：[run_wp2.py](run_wp2.py)。
- **曝光：** 真实数字都是已曝光的代理。

## 结论先读

1. **没有融合设计对 SUB 通过全部门槛。不产出候选类；保留 SUB。**
2. **登记的主模型 F2_S_A（按类别定权重）在真实代理上失败。**
   - 在伪场景 + 冷启动上它是最好的（分数 0.125，SUB 为 0.161）。估出的权重在冷启动、phase、√t 缺口三类都是 1，fallback 类是 0.5，所以几乎处处都退化成了应力模型。
   - 在真实代理上，这导致 CK1 −0.561、CK2 −0.638 pp，未通过 G-proxy、G-epsfree、G-robust、G-regress 和 G-hyp。
3. **教训：因果场景不能代表 CK1 和 CK2。**
   - 伪场景 / CS 中的"冷启动"类是删掉了更早锚点的后面月份；而真实的冷启动是第一个月（磨合期）。
   - 伪场景 / CS 中的"缺口"类只是截掉几天；真实的 CK2 缺口是整整一个缺失的 45 °C 段。
   - 所以按类别学到的权重，恰好在 SUB 和 S 分歧最大的两个检查点上迁移得很差。
4. **F1（逆方差加权）表现最好。**
   - F1_S_A（未曝光）的真实 MAE 为 0.141 / 0.128 / 0.174，MAX 为 0.282 / 0.232 / 0.624。在 Δ = 0.4（0.128 对 0.123）和 0.8 时输给 SUB，但在因果检验上胜出（伪场景 0.119 对 0.148；冷启动 0.141 对 0.174）。
   - 已曝光 CK1 的 F1_S_B 和 F1_S_C 的 MAE 为 0.196 / 0.116 / 0.118，MAX 为 0.545 / 0.192 / 0.239。它们通过了 G-proxy 和 G-robust，但没过 G-epsfree（0.137，要求 0.119）和 G-hyp（最大后悔值 0.029，SUB 为 0.027）。按规则 3，它们本来也不能被选中。

## 估计出的参数（伪场景 + CS，Δ = 0.4，主台阶方法）

| 量 | 值 |
|---|---|
| σ_S0（S_A = S_B = S_C 在伪场景 / CS 上） | 见 [wp2_estimated_params.json](outputs/wp2_estimated_params.json) |
| σ_SUB：phase / sqrt_gap / fallback / 合并（Ah） | 0.250 / 0.179 / 0.245 / 0.208 |
| F2 权重（冷启动、phase、sqrt_gap、fallback） | 1、1、1、0.5（所有 S 变体相同） |
| 各类别情形数（S_A） | 冷启动 10、phase 4、sqrt_gap 12、fallback 2 |

S_B 和 S_C 在每个伪场景 / CS 情形上都与 S_A 完全相同。这在预期之内：它们的规则只改变第 0 月，也就是只影响 CK1。

## 结果

真实代理，主台阶方法，A4 2 Ah，单位 pp。G-hyp 相关列来自加入各设计后的 WP1 网格（[假设表](outputs/wp2_hypothesis_decision_table.csv)）。

| 模型 | MAE Δ0 / .4 / .8 | MAX Δ0 / .4 / .8 | 与 ε 无关 | 伪场景 | 冷启动 | 最大后悔值 | 最坏 s |
|---|---|---|---|---|---|---|---|
| **SUB** | 0.207 / 0.123 / 0.140 | 0.609 / 0.228 / 0.228 | 0.139 | 0.148 | 0.174 | **0.027** | 0.225 |
| **F2_S_A（主模型）** | 0.186 / 0.242 / 0.298 | 0.638 / 0.638 / 0.953 | 0.189 | **0.106** | 0.144 | 0.095 | 0.208 |
| F1_S_A | 0.141 / 0.128 / 0.173 | 0.282 / 0.232 / 0.624 | 0.137 | 0.119 | **0.141** | 0.042 | 0.214 |
| F3_S_A | 0.167 / 0.147 / 0.189 | 0.425 / 0.328 / 0.564 | 0.159 | 0.120 | 0.149 | 0.051 | 0.212 |
| F1_S_B / F1_S_C（已曝光 CK1） | 0.196 / 0.116 / 0.118 | 0.545 / 0.192 / 0.239 | 0.137 | 0.119 | 0.141 | 0.029 | 0.219 |
| F2_S_B / F2_S_C（已曝光 CK1） | 0.217 / 0.163 / 0.219 | 0.638 / 0.638 / 0.638 | 0.189 | 0.106 | 0.144 | 0.080 | 0.212 |
| F3_S_B / F3_S_C（已曝光 CK1） | 0.207 / 0.137 / 0.149 | 0.496 / 0.328 / 0.288 | 0.159 | 0.120 | 0.149 | 0.045 | 0.215 |

**Δ = 0.4 时各检查点误差（pp）：**

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| SUB | +0.217 | −0.018 | +0.080 | +0.228 | +0.150 | −0.163 | −0.004 |
| F2_S_A | −0.561 | −0.638 | −0.035 | +0.100 | −0.007 | −0.209 | +0.144 |
| F1_S_A | −0.232 | −0.118 | −0.065 | +0.145 | +0.049 | −0.192 | +0.092 |
| F1_S_B（已曝光） | +0.153 | −0.118 | −0.065 | +0.145 | +0.049 | −0.192 | +0.092 |

**门槛**（[wp2_gates.json](outputs/wp2_gates.json)）：每个设计都至少有一个门槛没过。F1_S_A 没过 G-proxy、G-epsfree、G-robust 和 G-hyp；F2、F3 没过的更多。

## 这意味着什么

- 从 CK3 起，融合模型和应力模型都与 SUB 持平或更好。决定性的是 CK1 和 CK2：在这两个点上，因果检验和物理都无法判定哪个模型对。而且 SUB（√t，CK2）和应力模型（CK1 的规则）恰好各自依赖一个已曝光的选择。
- 这批数据中不存在与 CK1、CK2 相似的因果检验。这是结构性的限制，不是调参能解决的问题。
- 因此 WP6 应把"SUB 还是 F1 类融合"当作一个需要排行榜来回答的问题。
