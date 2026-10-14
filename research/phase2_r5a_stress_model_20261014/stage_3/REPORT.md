<a id="en"></a>

# Stage 3 — Pack stress model: registered evaluation

> **Language:** English · [中文](#zh)

- **Protocol:** [protocol.json](protocol.json) (SHA256 [protocol.sha256](protocol.sha256)), committed in `ee359ef` before any evaluation. Pseudo-scenario results (k ≥ 3) were committed in `13fd5f5` before the real data were run.
- **Code:** [../src/smodel.py](../src/smodel.py), [run_3.py](run_3.py).
- **Exposure.** All results are **exposed-exploratory**. Proxies are post-checkup charges plus an assumed ε, not hidden C/20 truth.

## Result: no model passes every gate

| Model | MAE Δ0 / .4 / .8 (pp) | MAX Δ0 / .4 / .8 | ε-free CK2–7 MAE | Pseudo MAE (k ≥ 3) | Gates failed |
|---|---|---|---|---|---|
| M4 | 0.347 / 0.291 / 0.285 | 0.669 / 0.669 / 0.669 | 0.304 | 0.247 | — |
| **V2** | 0.272 / **0.216** / 0.210 | 0.669 / 0.669 / 0.669 | 0.216 | 0.240 | reference |
| **S_main** | 0.270 / 0.326 / 0.382 | 0.742 / 1.134 / 1.526 | **0.192** | **0.131** | G-proxy, G-robust (0/8), G-regress (+0.92 at CK1) |
| ENS50 | **0.158** / 0.214 / 0.270 | 0.617 / 0.617 / 0.851 | 0.173 | 0.144 | G-proxy (Δ = 0.8 MAE and MAX) |
| V2_Sfb | 0.268 / 0.324 / 0.380 | 0.742 / 1.134 / 1.526 | 0.189 | 0.147 | G-proxy, G-robust (0/6), G-regress |

All variants are in [S3_summary_table.csv](outputs/S3_summary_table.csv) and the gates in [S3_gates.json](outputs/S3_gates.json). Selection: no model passes, so no candidate class is produced.

**Per-checkup errors at Δ = 0.4 (pp)** ([S3_per_checkup_d04.csv](outputs/S3_per_checkup_d04.csv)):

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| V2 | +0.217 | +0.669 | +0.080 | +0.228 | +0.150 | −0.163 | −0.004 |
| S_main | **−1.134** | +0.565 | −0.025 | −0.004 | −0.156 | −0.370 | +0.029 |
| ENS50 | −0.459 | +0.617 | +0.027 | +0.112 | −0.003 | −0.266 | +0.013 |
| S, z = 1 (G4) | +2.314 | −2.134 | −0.857 | −0.519 | −0.545 | −0.750 | −0.285 |
| S, z = 0.5 (report only) | +0.940 | −0.206 | −0.168 | −0.038 | −0.130 | −0.338 | +0.034 |
| S, prior only | −1.134 | +0.393 | +0.358 | +0.400 | +0.263 | +0.058 | +0.356 |

## What the numbers say

- **CK1 is S_main's whole problem.**
  - At CK1 no anchor pair is visible, so S is the prior alone. The prior (Yagci-derived scale at z = 0.2) predicts 3.9 Ah of loss over month 0, about 1.2 Ah more than the proxy implies.
  - From CK2 on, the anchors pull A_cal down to 1.6–1.8 Ah/d^0.2 ([S3_parameters_d04.csv](outputs/S3_parameters_d04.csv)), and errors at CK3–CK7 are small.
  - S_main's ε-free CK2–7 MAE (0.192) and pseudo MAE (0.131) are better than V2's. Its Δ = 0.4 MAE (0.326) is worse only because of CK1.
- **The proxy MAE of S grows with Δ while V2's falls.** S uses the CK0 label without Δ at CK1, as V2 and M4 do, but its errors elsewhere are mostly negative. ENS50 is therefore better than V2 at Δ = 0 and 0.4 and worse at Δ = 0.8, which fails G-proxy.
- **Every robustness group loses to V2 at Δ = 0.4**, all for the same reason: CK1 depends only on the prior. With z = 1 or cycle-only, the sign at CK1 flips (+2.3 to +2.6 pp).
- **Fitted parameters are stable after CK2.**
  - A_cal = 1.61–1.74 (posterior SD of log A ≈ 0.14–0.18).
  - A_cyc = 4.8–6.2 × 10⁻⁵ per Arrhenius-weighted Ah from CK3 on, about 6–8 times the Yagci-derived prior centre (SD of log A ≈ 0.22–0.42). At CK2 it stays at the prior.
  - o_45 = −0.08 to −0.14 Ah, within its prior.
  - With z free the data choose z ≈ 0.38–0.40, larger than the Challenge 1 prior mean of 0.20.
- **Calendar vs cycle split.**
  - The predicted calendar part of the month's loss falls from 0.68 Ah (CK2) to 0.18 Ah (CK7); the cycle part is about 0.6 Ah per month from CK3 on.
  - This split is **not physically identified**: the schedule repeats the same daily duty, so throughput and time are nearly collinear, and the split follows the prior's z.
- **Independence (H-B).** The correlation of S_main and V2 errors over CK1–CK7 is 0.44 ([S3_diagnostics.json](outputs/S3_diagnostics.json)): seven exposed points, diagnostic only. The ensemble lowers MAE at small Δ but does not pass the registered gate.
- **Pseudo scenarios including k = 2** (reporting only, [S3_pc_k2_reporting_metrics.csv](outputs/S3_pc_k2_reporting_metrics.csv)): at Δ = 0.4, S_main has PC5/PC10 MAE 0.191/0.189 against V2's 0.302/0.340.

---

<a id="zh"></a>

# 第 3 阶段——电池组应力模型：预登记评估

> **语言：** [English](#en) · 中文

- **协议：** [protocol.json](protocol.json)（SHA256 见 [protocol.sha256](protocol.sha256)），在任何评估之前于 `ee359ef` 提交。伪场景结果（k ≥ 3）在运行真实数据之前于 `13fd5f5` 提交。
- **代码：** [../src/smodel.py](../src/smodel.py)、[run_3.py](run_3.py)。
- **曝光。** 所有结果都是**已曝光的探索性结果**。代理是检查后充电量加假定的 ε，不是隐藏的 C/20 真值。

## 结果：没有模型通过全部门槛

| 模型 | MAE Δ0 / .4 / .8（pp） | MAX Δ0 / .4 / .8 | 与 ε 无关的 CK2–7 MAE | 伪场景 MAE（k ≥ 3） | 未通过的门槛 |
|---|---|---|---|---|---|
| M4 | 0.347 / 0.291 / 0.285 | 0.669 / 0.669 / 0.669 | 0.304 | 0.247 | — |
| **V2** | 0.272 / **0.216** / 0.210 | 0.669 / 0.669 / 0.669 | 0.216 | 0.240 | 参照 |
| **S_main** | 0.270 / 0.326 / 0.382 | 0.742 / 1.134 / 1.526 | **0.192** | **0.131** | G-proxy、G-robust（0/8）、G-regress（CK1 处 +0.92） |
| ENS50 | **0.158** / 0.214 / 0.270 | 0.617 / 0.617 / 0.851 | 0.173 | 0.144 | G-proxy（Δ = 0.8 时的 MAE 和 MAX） |
| V2_Sfb | 0.268 / 0.324 / 0.380 | 0.742 / 1.134 / 1.526 | 0.189 | 0.147 | G-proxy、G-robust（0/6）、G-regress |

所有变体见 [S3_summary_table.csv](outputs/S3_summary_table.csv)，门槛见 [S3_gates.json](outputs/S3_gates.json)。选择：没有模型通过，因此不产出候选类。

**Δ = 0.4 时各检查点误差（pp）**（[S3_per_checkup_d04.csv](outputs/S3_per_checkup_d04.csv)）：

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| V2 | +0.217 | +0.669 | +0.080 | +0.228 | +0.150 | −0.163 | −0.004 |
| S_main | **−1.134** | +0.565 | −0.025 | −0.004 | −0.156 | −0.370 | +0.029 |
| ENS50 | −0.459 | +0.617 | +0.027 | +0.112 | −0.003 | −0.266 | +0.013 |
| S，z = 1（G4） | +2.314 | −2.134 | −0.857 | −0.519 | −0.545 | −0.750 | −0.285 |
| S，z = 0.5（仅报告） | +0.940 | −0.206 | −0.168 | −0.038 | −0.130 | −0.338 | +0.034 |
| S，仅先验 | −1.134 | +0.393 | +0.358 | +0.400 | +0.263 | +0.058 | +0.356 |

## 这些数字说明什么

- **S_main 的问题全在 CK1。**
  - CK1 时还看不到任何锚点对，S 只有先验。先验（z = 0.2 下由 Yagci 推出的尺度）预测第 0 月损失 3.9 Ah，比代理所示多约 1.2 Ah。
  - 从 CK2 起，锚点把 A_cal 拉到 1.6–1.8 Ah/d^0.2（[S3_parameters_d04.csv](outputs/S3_parameters_d04.csv)），CK3–CK7 的误差都很小。
  - S_main 与 ε 无关的 CK2–7 MAE（0.192）和伪场景 MAE（0.131）都优于 V2。它在 Δ = 0.4 时的 MAE（0.326）较差，完全是因为 CK1。
- **S 的代理 MAE 随 Δ 增大，V2 的随 Δ 减小。** S 在 CK1 时和 V2、M4 一样直接用不含 Δ 的 CK0 标签，但其他检查点的误差大多为负。因此 ENS50 在 Δ = 0 和 0.4 时优于 V2，在 Δ = 0.8 时更差，未通过 G-proxy。
- **每个稳健性组在 Δ = 0.4 时都输给 V2**，原因相同：CK1 只取决于先验。z = 1 或只有循环项时，CK1 的符号反过来（+2.3 至 +2.6 pp）。
- **CK2 之后拟合参数很稳定。**
  - A_cal = 1.61–1.74（log A 的后验 SD ≈ 0.14–0.18）。
  - 从 CK3 起 A_cyc = 4.8–6.2 × 10⁻⁵ /（Arrhenius 加权 Ah），约为 Yagci 推出的先验中心的 6–8 倍（log A 的 SD ≈ 0.22–0.42）。CK2 时它停在先验值。
  - o_45 = −0.08 至 −0.14 Ah，在其先验范围内。
  - z 放开时，数据选出 z ≈ 0.38–0.40，大于 Challenge 1 的先验均值 0.20。
- **日历与循环的划分。**
  - 月损失中预测的日历部分从 0.68 Ah（CK2）降到 0.18 Ah（CK7）；从 CK3 起，循环部分每月约 0.6 Ah。
  - 这个划分**在物理上无法辨识**：日程每天重复相同的工况，吞吐和时间几乎共线，划分结果跟着先验的 z 走。
- **独立性（H-B）。** CK1–CK7 上 S_main 与 V2 误差的相关系数为 0.44（[S3_diagnostics.json](outputs/S3_diagnostics.json)）：只有 7 个已曝光的点，仅作诊断。集成在 Δ 较小时降低了 MAE，但没有通过登记的门槛。
- **含 k = 2 的伪场景**（仅报告，[S3_pc_k2_reporting_metrics.csv](outputs/S3_pc_k2_reporting_metrics.csv)）：Δ = 0.4 时，S_main 的 PC5/PC10 MAE 为 0.191/0.189，V2 为 0.302/0.340。
