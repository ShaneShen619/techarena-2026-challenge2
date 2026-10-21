<a id="en"></a>

# WP4 — Real run (once), level, gates

> **Language:** English · [中文](#zh)

Protocol: `protocol.json`, committed in db6412f, after every WP2/WP3 selection was committed. **All numbers here are exposed**: proxies = post-checkup full charge + ε0 + Δ. They change no outcome.

## Conclusions first

1. **On the real proxies, O1 and O2 look like big wins, and the whole gain is CK2.** O1_ens and O2_ens reach MAE 0.108 / 0.103 pp at Δ = 0.4, against REF 0.131 and SUB 0.120. CK2 moves from −0.311 to −0.130 / −0.096. Without CK2 they are no better than REF (0.105 / 0.105 vs 0.102). Both are labelled **exposed-CK2**. The causal check found them neutral to slightly worse (WP2). This is the selection-on-CK2 trap the study was registered to avoid.
2. **The inert designs change real errors by ≤ 0.03 pp**, as the screen predicted. C_ens and D_ens improve the real MAE by 0.002–0.003 pp, again through CK2 (exposed-CK2).
3. **Level.** At Δ = 0.4, every r5c-family model sits **below** SUB:

   | Model | Mean SOH shift vs SUB, CK1–7 (pp) | CK2–7 (pp) |
   |---|---|---|
   | REF | −0.124 | −0.117 |
   | O1_ens | −0.080 | −0.063 |
   | O2_ens | −0.104 | −0.079 |
   | R3_T | −0.193 | −0.189 |

   None comes near either leaderboard reading: truth about 1 pp below SUB, or CK2–7 about +0.65 pp above it. Switching to any of them would not test the level question.
4. **r5c's real gates (information only).** REF and every ensemble pass G-proxy, G-epsfree, G-robust (6/6) and G-regress (max increase ≤ 0.12 pp). The stress models alone fail G-proxy, and the inert ones also fail G-epsfree.

## Real table (Δ = 0.4 unless stated, main variant; pp)

| Model | MAE Δ0 / 0.4 / 0.8 | MAX Δ0.4 | w/o CK1 | w/o CK2 | w/o both | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 | Label |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SUB | 0.191 / 0.120 / 0.142 | 0.237 | 0.105 | 0.133 | 0.118 | +0.210 | +0.039 | +0.140 | +0.237 | +0.084 | −0.068 | −0.060 | |
| V2 | 0.272 / 0.216 / 0.210 | 0.669 | 0.216 | 0.140 | 0.125 | +0.217 | +0.669 | +0.080 | +0.228 | +0.150 | −0.163 | −0.004 | |
| R3_T | 0.233 / 0.179 / 0.235 | 0.638 | 0.208 | 0.103 | 0.122 | −0.008 | −0.638 | −0.150 | +0.100 | −0.007 | −0.209 | +0.144 | |
| **REF = FINAL** | 0.188 / 0.131 / 0.174 | 0.311 | 0.145 | 0.102 | 0.112 | +0.048 | −0.311 | −0.092 | +0.132 | +0.032 | −0.197 | +0.107 | |
| B0_ens | 0.189 / 0.133 / 0.175 | 0.311 | 0.147 | 0.103 | 0.114 | +0.048 | −0.311 | −0.099 | +0.132 | +0.032 | −0.200 | +0.107 | |
| S_ens | 0.189 / 0.133 / 0.177 | 0.297 | 0.148 | 0.106 | 0.118 | +0.043 | −0.297 | −0.100 | +0.139 | +0.049 | −0.191 | +0.112 | |
| C_ens | 0.185 / 0.129 / 0.173 | 0.302 | 0.144 | 0.101 | 0.112 | +0.044 | −0.302 | −0.088 | +0.134 | +0.034 | −0.195 | +0.108 | exposed-CK2 |
| O1_ens | 0.164 / 0.108 / 0.157 | 0.232 | 0.122 | 0.105 | 0.120 | +0.027 | −0.130 | −0.028 | +0.232 | +0.040 | −0.209 | +0.091 | exposed-CK2 |
| O2_ens | 0.147 / 0.103 / 0.159 | 0.204 | 0.113 | 0.105 | 0.117 | −0.044 | −0.096 | −0.089 | +0.136 | +0.051 | −0.204 | +0.102 | exposed-CK2 |
| D_ens | 0.185 / 0.129 / 0.173 | 0.285 | 0.143 | 0.102 | 0.115 | +0.042 | −0.285 | −0.076 | +0.147 | +0.049 | −0.179 | +0.123 | exposed-CK2 |

The stress models alone (B0, S, C, O1, O2, D) and the gate details are in `outputs/real.json`. The per-case rows, including all step variants, are in `outputs/real_predictions.csv`.

---

<a id="zh"></a>

# WP4 — 真实运行（一次）、水平、门槛

> **语言：** [English](#en) · 中文

协议：`protocol.json`，在 db6412f 中提交，此时 WP2/WP3 的所有选择都已提交。**这里所有数字都已曝光**：代理 = 检测后满充 + ε0 + Δ。它们不改变任何结论。

## 结论在前

1. **在真实代理上，O1 和 O2 看起来是大胜，但全部收益都来自 CK2。** Δ = 0.4 时 O1_ens 和 O2_ens 的 MAE 为 0.108 / 0.103 pp，REF 为 0.131，SUB 为 0.120。CK2 从 −0.311 变为 −0.130 / −0.096。去掉 CK2 后它们并不比 REF 好（0.105 / 0.105 对 0.102）。两者都标为 **exposed-CK2**。因果检查认为它们持平或略差（WP2）。这正是本研究预先登记规则要避开的"按 CK2 选模型"陷阱。
2. **惰性设计对真实误差的改变 ≤ 0.03 pp**，与筛查的预测一致。C_ens 和 D_ens 让真实 MAE 改善 0.002–0.003 pp，也是通过 CK2（exposed-CK2）。
3. **水平。** Δ = 0.4 时，r5c 系列的每个模型都**低于** SUB：

   | 模型 | 相对 SUB 的平均 SOH 偏移，CK1–7 (pp) | CK2–7 (pp) |
   |---|---|---|
   | REF | −0.124 | −0.117 |
   | O1_ens | −0.080 | −0.063 |
   | O2_ens | −0.104 | −0.079 |
   | R3_T | −0.193 | −0.189 |

   都远离两种排行榜解读：真值比 SUB 低约 1 pp，或 CK2–7 比 SUB 高约 +0.65 pp。换成其中任何一个，都检验不了水平问题。
4. **r5c 的真实门槛（仅供参考）。** REF 和所有集成都通过 G-proxy、G-epsfree、G-robust（6/6）和 G-regress（最大增幅 ≤ 0.12 pp）。单独的压力模型都不通过 G-proxy，其中惰性的还不通过 G-epsfree。

## 真实场景表（除特别说明外 Δ = 0.4，主变体；单位 pp）

| 模型 | MAE Δ0 / 0.4 / 0.8 | MAX Δ0.4 | 去 CK1 | 去 CK2 | 两者都去 | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 | 标签 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SUB | 0.191 / 0.120 / 0.142 | 0.237 | 0.105 | 0.133 | 0.118 | +0.210 | +0.039 | +0.140 | +0.237 | +0.084 | −0.068 | −0.060 | |
| V2 | 0.272 / 0.216 / 0.210 | 0.669 | 0.216 | 0.140 | 0.125 | +0.217 | +0.669 | +0.080 | +0.228 | +0.150 | −0.163 | −0.004 | |
| R3_T | 0.233 / 0.179 / 0.235 | 0.638 | 0.208 | 0.103 | 0.122 | −0.008 | −0.638 | −0.150 | +0.100 | −0.007 | −0.209 | +0.144 | |
| **REF = FINAL** | 0.188 / 0.131 / 0.174 | 0.311 | 0.145 | 0.102 | 0.112 | +0.048 | −0.311 | −0.092 | +0.132 | +0.032 | −0.197 | +0.107 | |
| B0_ens | 0.189 / 0.133 / 0.175 | 0.311 | 0.147 | 0.103 | 0.114 | +0.048 | −0.311 | −0.099 | +0.132 | +0.032 | −0.200 | +0.107 | |
| S_ens | 0.189 / 0.133 / 0.177 | 0.297 | 0.148 | 0.106 | 0.118 | +0.043 | −0.297 | −0.100 | +0.139 | +0.049 | −0.191 | +0.112 | |
| C_ens | 0.185 / 0.129 / 0.173 | 0.302 | 0.144 | 0.101 | 0.112 | +0.044 | −0.302 | −0.088 | +0.134 | +0.034 | −0.195 | +0.108 | exposed-CK2 |
| O1_ens | 0.164 / 0.108 / 0.157 | 0.232 | 0.122 | 0.105 | 0.120 | +0.027 | −0.130 | −0.028 | +0.232 | +0.040 | −0.209 | +0.091 | exposed-CK2 |
| O2_ens | 0.147 / 0.103 / 0.159 | 0.204 | 0.113 | 0.105 | 0.117 | −0.044 | −0.096 | −0.089 | +0.136 | +0.051 | −0.204 | +0.102 | exposed-CK2 |
| D_ens | 0.185 / 0.129 / 0.173 | 0.285 | 0.143 | 0.102 | 0.115 | +0.042 | −0.285 | −0.076 | +0.147 | +0.049 | −0.179 | +0.123 | exposed-CK2 |

单独的压力模型（B0、S、C、O1、O2、D）和门槛细节见 `outputs/real.json`；逐案例的行（含全部台阶变体）见 `outputs/real_predictions.csv`。
