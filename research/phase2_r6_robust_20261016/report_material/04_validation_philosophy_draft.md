<a id="en"></a>

# Draft — Validation (REPORT.md section 3)

> **Language:** English · [中文](#zh)

Only CK0 is labelled, so the hidden CK1–CK7 cannot be scored locally. We therefore validated on three levels and kept them apart.

1. **Strict causality.** Every prediction for CK_k uses `load_dataset(data, until=CK_k)` only. Each model class is checked bit-for-bit: replacing all data after the cutoff with noise, and fitting on the CK1 prefix only, must give identical output.
2. **Proxy labels — exposed.** The post-checkup full charge plus an offset (P_k = Q_fc,k + ε0 + Δ, with Δ = 0 / 0.4 / 0.8 Ah) tracks capacity closely. Every model was developed with these proxies in view, so proxy errors are reported as **exposed-exploratory**, never as accuracy.
3. **Causal hold-out scenarios — not exposed.** These are the tests used for model selection:
   - **Pseudo-gap and pseudo-cut:** delete in-month data before later checkups.
   - **Cold start:** delete all earlier anchors, so a model must work as it would at CK1.
   - Every design round was registered (SHA-256 committed) before any result. Selections were made on these scenarios only, and real results were computed once per round.
4. **Label-hypothesis robustness.** Because the hidden truth may differ from the proxies, models were scored on an 18-hypothesis grid, normalised by the official ExampleModel (= 1):
   - the true anchor offset Δ;
   - the share f of the post-checkup step offset that the C/20 test does not see;
   - an ε drift d = −0.031 Ah per Ah of fade, seen in open data.

   The submitted model has the lowest maximum regret (0.027) on this grid.

**Robustness checks:**

- six graphite-step detection methods;
- 25 vs 45 °C (phase matching cancels a +0.18 Ah temperature offset);
- reduced data budget (pseudo-cuts of 5 and 10 days; pseudo-gaps after one or two programs);
- the missing segment 3 (CK2).

**Key numbers (pp, Δ = 0.4).**

- SUB: proxy MAE 0.123, maximum 0.228; pseudo 0.148; cold start 0.174.
- ExampleModel: proxy MAE about 4.3.
- On the official normalised scale, SUB therefore scores about 0.03–0.05.

---

<a id="zh"></a>

# 草稿——验证（REPORT.md 第 3 节）

> **语言：** [English](#en) · 中文

只有 CK0 有标签，所以隐藏的 CK1–CK7 无法在本地评分。因此我们在三个层面上做验证，并且把它们分开对待。

1. **严格因果。** 对 CK_k 的每个预测只使用 `load_dataset(data, until=CK_k)`。每个模型类都做逐位检查：把截断之后的所有数据换成噪声，以及只用 CK1 前缀拟合，输出都必须完全一致。
2. **代理标签——已曝光。** 检查后的满充量加一个偏差（P_k = Q_fc,k + ε0 + Δ，Δ = 0 / 0.4 / 0.8 Ah）能紧密跟踪容量。每个模型都是在看得到这些代理的情况下开发的，所以代理误差只作为**已曝光的探索性结果**报告，绝不作为精度。
3. **因果留出场景——未曝光。** 这些是用来选模型的检验：
   - **伪缺口和伪截断：** 在后面的检查点之前删掉月内数据。
   - **冷启动：** 删掉所有更早的锚点，让模型必须像在 CK1 时那样工作。
   - 每一轮设计都在出任何结果之前登记（提交 SHA-256）。选择只在这些场景上进行，真实结果每轮只计算一次。
4. **对标签假设的稳健性。** 由于隐藏真值可能与代理不同，我们在一个 18 种假设的网格上给模型打分，用官方 ExampleModel 归一（= 1）：
   - 真实的锚点偏差 Δ；
   - 检查后台阶偏移中 C/20 测试没有测到的比例 f；
   - 开放数据中观察到的 ε 漂移，d = 每衰减 1 Ah 漂移 −0.031 Ah。

   提交的模型在这个网格上最大后悔值最低（0.027）。

**稳健性检查：**

- 六种石墨台阶检测方法；
- 25 °C 与 45 °C（同相位比较抵消了 +0.18 Ah 的温度偏差）；
- 数据量减少（提前 5 天和 10 天的伪截断；在一次或两次程序之后的伪缺口）；
- 缺失的第 3 段（CK2）。

**关键数字（pp，Δ = 0.4）。**

- SUB：代理 MAE 0.123，最大 0.228；伪场景 0.148；冷启动 0.174。
- ExampleModel：代理 MAE 约 4.3。
- 因此在官方归一化尺度上，SUB 约为 0.03–0.05。
