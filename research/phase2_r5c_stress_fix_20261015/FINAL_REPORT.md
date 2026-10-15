<a id="en"></a>

# Round 5C: Fixing the Stress Model's Cold Start — Final Report

> **Language:** English · [中文](#zh)

- **Run:** 2026-10-15, unattended, following [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md).
- **Where:** worktree `/Users/shane/Desktop/Arena_1015_r5c_stressfix`, branch `exp/phase2-r5c-stress-fix-20261015` (from 5A's `f27cca7`).
- **Exposure:** every proxy value was seen before this round. All real-scenario numbers are **exposed-exploratory**: proxies are post-checkup charges plus an assumed ε, not hidden C/20 truth.
- **Untouched:** the real submission package and every earlier study.

## Conclusions first

1. **The cold-start problem is fixed in the causal tests.** Selection used only these tests; the real proxies never chose a design.
   - **What fixed it:** a two-term law (break-in + √t calendar + linear cycle), plus one endpoint pair of in-month 45 °C graphite steps for the month no anchor yet covers, with β = 1 (R2_B).
   - **Cold-start scenarios** (later months with all earlier anchors removed): R2_B has MAE 0.144 pp, against V2 0.252 and 5A's S_main 0.287.
   - **Pseudo scenarios:** R2_B has MAE 0.119 pp, against V2 0.240.
   - **Ensemble with V2** (w = 0.75 chosen on these tests): 0.123 (pseudo) and 0.134 (cold start).
2. **One model passes every gate: R3_TD_w0.75 = 0.75 × R3_T + 0.25 × V2. It is labelled exposed-CK1.**
   - Real proxies at Δ = 0 / 0.4 / 0.8: MAE 0.188 / 0.131 / 0.174 pp and MAX 0.440 / 0.311 / 0.344 pp. V2: MAE 0.272 / 0.216 / 0.210, MAX 0.669.
   - ε-free CK2–7 MAE 0.145 (V2 0.216). CK2 error −0.311 (V2 +0.669).
   - Every gate passes: G-proxy, G-epsfree, G-robust 6/6, G-pseudo, G-coldstart, G-regress (+0.10 pp max) and G-causal / G-impl (Python 3.13 and 3.11, difference 0.0 pp, 29 s). `validate_submission.py` passes on a **copy** of the package.
   - **Caveat:** it equals round 2's R2_D_w0.75 everywhere except CK1. Its pass depends on R3_T's physics correction (the step transient counted from the operation restart, round 4's τ ≈ 2.5 d), which only changes month 0. That correction was proposed after 5A's CK1 error was known, so its CK1 gain (−0.366 → +0.048 pp) is **not evidence** (rule 7, D3.1).
3. **Earlier registered mains each missed one gate.**
   - Round 1's main D4_D2_w0.5 and round 2's main R2_D_w0.75 both fail G-proxy at Δ = 0.8, through CK1 alone.
   - Some non-chosen ensemble weights pass every gate on the real run (w = 0.25 in rounds 1–3, w = 0.5 in rounds 2–3). They are **not candidates**, because choosing w after the real run would select on real proxies (D1.1).
4. **Targets** (candidate R3_TD_w0.75): **T2, T4, T6 met; T1, T3, T5 missed.** Details are below. No model meets all six.
5. **Recommendation.** Do not replace V2 silently.
   - The causal evidence that the stress + V2 ensemble beats V2 on CK3–CK7-type situations is strong: pseudo 0.123 vs 0.240 and cold start 0.134 vs 0.252.
   - The CK1 behaviour rests on an exposed correction.
   - If you want a leaderboard probe, the candidate is ready (see "Candidate"). V2 remains the fallback. **No submission file was changed.**

## Round-by-round

| Round | Diagnosis (pseudo / cold-start and physics only) | Designs registered | Main by registered rule | Real outcome |
|---|---|---|---|---|
| 1 | 5A: CK1 depends on the prior alone; one t^z term mixes break-in with storage; in-month steps unused | D1 S+steps, D2 two-term law, D3 both, D4 ensembles, D5 exposed-CK1 hybrid | D4_D2_w0.5 (score 0.159) | fails G-proxy (MAX 0.864 at Δ = 0.8, CK1 −0.47) |
| 2 | step terms over-weighted (σ_s 0.05) and β ≈ 1.3 inflates 45 °C step declines; steps help only at cold start ([diagnosis](stage_2/DIAGNOSIS_round2.md)) | R2_A–C gap-only step endpoints, β = 1; R2_D ensemble | R2_D_w0.75 (score 0.129) | fails G-proxy only (MAE 0.233 at Δ = 0.8, CK1 −0.37) |
| 3 | round 2 near its floor on pseudo/CS; physics: the transient counts from the restart, which affects only month 0 ([diagnosis](stage_2/DIAGNOSIS_round3.md)) | R3_T, R3_TD (both exposed-CK1) | none eligible (rule 7: identical to round 2 on pseudo/CS) | R3_TD_w0.75 passes every gate |

## Results (registered designs and baselines)

Units are pp. MAE and MAX are for Δ = 0 / 0.4 / 0.8. CK1 and CK2 are at Δ = 0.4. Pseudo is the mean MAE over PG1, PG2, PC5 and PC10 (k ≥ 3); cold is the mean over CS and CSE (Δ = 0.4). Full tables: [S1](stage_1/outputs/S1_summary_table.csv), [S2 R2](stage_2/outputs/S2_R2_summary_table.csv), [S2 R3](stage_2/outputs/S2_R3_summary_table.csv).

| Model | MAE | MAX | ε-free | CK1 | CK2 | Pseudo | Cold | Gates |
|---|---|---|---|---|---|---|---|---|
| V2 | 0.272 / 0.216 / 0.210 | 0.669 / 0.669 / 0.669 | 0.216 | +0.217 | +0.669 | 0.240 | 0.252 | reference |
| M4 | 0.347 / 0.291 / 0.285 | 0.669 / 0.669 / 0.669 | 0.304 | +0.217 | +0.669 | 0.247 | 0.252 | — |
| 5A S_main | 0.270 / 0.326 / 0.382 | 0.742 / 1.134 / 1.526 | 0.192 | −1.134 | +0.565 | 0.131 | 0.287 | fail |
| 5A ENS50 | 0.158 / 0.214 / 0.270 | 0.617 / 0.617 / 0.851 | 0.173 | −0.459 | +0.617 | 0.144 | 0.220 | fail |
| D1 | 0.314 / 0.370 / 0.426 | 0.511 / 0.700 / 1.092 | 0.315 | −0.700 | −0.495 | 0.290 | 0.187 | fail |
| D2 | 0.289 / 0.345 / 0.401 | 0.768 / 1.160 / 1.552 | 0.209 | −1.160 | −0.638 | 0.118 | 0.350 | fail |
| D3 | 0.376 / 0.432 / 0.488 | 0.651 / 0.651 / 0.987 | 0.405 | −0.595 | −0.406 | 0.386 | 0.150 | fail |
| D4_D1_w0.5 | 0.141 / 0.154 / 0.210 | 0.337 / 0.337 / 0.634 | 0.139 | −0.241 | +0.087 | 0.148 | 0.194 | fail |
| **D4_D2_w0.5 (R1 main)** | 0.087 / 0.143 / 0.199 | 0.181 / 0.472 / 0.864 | 0.088 | −0.472 | +0.015 | 0.152 | 0.165 | fail (G-proxy) |
| D4_D3_w0.5 | 0.182 / 0.180 / 0.236 | 0.407 / 0.407 / 0.581 | 0.178 | −0.189 | +0.132 | 0.184 | 0.175 | fail |
| D5 exposed-CK1 | 0.434 / 0.378 / 0.372 | 0.651 / 0.651 / 0.651 | 0.405 | +0.217 | −0.406 | 0.386 | 0.150 | fail |
| R2_A | 0.227 / 0.283 / 0.339 | 0.565 / 0.787 / 1.179 | 0.199 | −0.787 | +0.565 | 0.136 | 0.174 | fail |
| R2_B | 0.202 / 0.258 / 0.314 | 0.638 / 0.638 / 0.953 | 0.208 | −0.561 | −0.638 | 0.119 | 0.144 | fail |
| R2_C | 0.204 / 0.260 / 0.316 | 0.638 / 0.638 / 0.957 | 0.209 | −0.565 | −0.638 | 0.118 | 0.171 | fail |
| **R2_D_w0.75 (R2 main)** | 0.128 / 0.177 / 0.233 | 0.311 / 0.366 / 0.759 | 0.145 | −0.366 | −0.311 | 0.123 | 0.134 | fail (G-proxy) |
| R3_T (exposed-CK1) | 0.233 / 0.179 / 0.235 | 0.638 / 0.638 / 0.638 | 0.208 | −0.008 | −0.638 | 0.119 | 0.144 | fail |
| **R3_TD_w0.75 (candidate, exposed-CK1)** | **0.188 / 0.131 / 0.174** | **0.440 / 0.311 / 0.344** | **0.145** | +0.048 | −0.311 | 0.123 | 0.134 | **pass** |

Variants (σ_s, β free, 25 °C steps, τ_b free) all fail. Non-chosen ensemble weights are in the CSV files; those that pass the gates on the real run (D4_*_w0.25; R2_D_w0.25/0.5; R3_TD_w0.25/0.5) are exposed observations, not candidates.

**Per-checkup errors at Δ = 0.4 (pp):**

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| V2 | +0.217 | +0.669 | +0.080 | +0.228 | +0.150 | −0.163 | −0.004 |
| R2_D_w0.75 | −0.366 | −0.311 | −0.092 | +0.132 | +0.033 | −0.197 | +0.107 |
| R3_TD_w0.75 | +0.048 | −0.311 | −0.092 | +0.132 | +0.033 | −0.197 | +0.107 |

## Targets (candidate R3_TD_w0.75)

| Target | Value | Result |
|---|---|---|
| T1 MAE ≤ 0.15 at every Δ | 0.188 / 0.131 / 0.174 | **missed** (met only at Δ = 0.4) |
| T2 MAX ≤ 0.45 at every Δ | 0.440 / 0.311 / 0.344 | **met** |
| T3 \|CK1\|, \|CK2\| ≤ 0.30 | +0.048 (exposed) / −0.311 | **missed** (CK2 by 0.011) |
| T4 ε-free CK2–7 MAE ≤ 0.15 | 0.145 | **met** |
| T5 pseudo MAE ≤ 0.12 | 0.123 | **missed** (by 0.003; R2_B reaches 0.119 but fails gates) |
| T6 cold-start MAE ≤ 0.20 | 0.134 | **met** (V2: 0.252) |

Round mains: round 1's D4_D2_w0.5 meets T4 (0.088) and T6; round 2's R2_D_w0.75 meets T4 and T6.

## Candidate ([candidate_model/](candidate_model/))

- `r5c_stress_ensemble_model.MyModel` (numpy/pandas only) = 0.75 × R3_T + 0.25 × V2.
  - R3_T is the two-term law, MAP-fitted on anchor pairs plus one restart-referenced 45 °C step endpoint pair for the month not yet anchored.
  - V2 is the unchanged V2 class. The Challenge 1/Yagci prior is embedded as constants.
- **G-causal and G-impl:** future-noise and fit-on-CK1-prefix outputs are bit-identical, and the difference from research is 0.0 pp.
  - Python 3.13 / numpy 2.4.2 / pandas 3.0.0: [log](stage_3/outputs/S3_candidate_checks_py313.json).
  - Python 3.11.14 / numpy 2.4.6 / pandas 3.0.6: [log](stage_3/outputs/S3_candidate_checks_py311.json).
  - A full run takes about 29 s.
- **Packaging check:** the candidate files were wired into `cache/package_copy/my_model/` (a git-ignored copy), and `validate_submission.py` passed under Python 3.11 ([log](stage_3/outputs/S3_validate_submission_copy_py311.log)). **The real package was not modified.**

**Leaderboard-only SOH (%):**

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| R3_TD_w0.75 | 95.823 | 94.157 | 93.368 | 92.715 | 91.963 | 91.296 | 90.932 |
| V2 | 95.992 | 95.137 | 93.541 | 92.811 | 92.081 | 91.331 | 90.821 |

To try the candidate, copy the seven `r5c_*.py` files into `my_model/` and set `from .r5c_stress_ensemble_model import MyModel as ActiveModel` in `my_model/__init__.py`. That is your decision; nothing was wired.

## Risks and limits

- **Exposure.** Every proxy was seen. The cold-start scenario is a new causal test, but it reuses the same months and pack.
- **The CK1 fix is exposed** (D3.1). The candidate's CK1 value relies on a physics correction proposed after the CK1 error was known.
- **Shared assumptions with V2.** ε, and whether the hidden C/20 sees the post-checkup recovery (round 4: up to about 0.9 Ah late in the campaign). Both are anchor-based and share this risk. The external-dataset note that ε drifts with fade is not modelled.
- **Prior transfer.** The two-term prior comes from Challenge 1 cells under continuous cycling. Only A_b was identifiable there; τ_b, A_cal and A_cyc fell back by rule.
- **Single pack.** Seven checkups; correlations are diagnostics.
- **Deviation D3.2.** The harness causality check was copied with a float cast for pandas 3.

## Reproduction

```bash
cd /Users/shane/Desktop/Arena_1015_r5c_stressfix/research/phase2_r5c_stress_fix_20261015
python3 -B stage_0/run_0.py
python3 -B stage_1/c1_two_term.py
python3 -B stage_1/run_1.py select && python3 -B stage_1/run_1.py real
python3 -B stage_2/run_2.py select && python3 -B stage_2/run_2.py real
python3 -B stage_2/run_3.py select && python3 -B stage_2/run_3.py real
python3 -B stage_3_check.py
cache/venv311/bin/python -B stage_3_check.py      # venv: /opt/homebrew/bin/python3.11 -m venv cache/venv311; pip install numpy pandas
```

Research environment: Python 3.13.0, numpy 2.4.2, pandas 3.0.0, scipy 1.18.0 (scipy is used only for the Challenge 1 refit). Caches are in git-ignored `cache/`.

---

<a id="zh"></a>

# 第五轮 C：修复应力模型的冷启动——最终报告

> **语言：** [English](#en) · 中文

- **运行：** 2026-10-15，无人值守，按 [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md) 执行。
- **位置：** worktree `/Users/shane/Desktop/Arena_1015_r5c_stressfix`，分支 `exp/phase2-r5c-stress-fix-20261015`（从 5A 的 `f27cca7` 创建）。
- **曝光：** 所有代理值在本轮之前都已看过。所有真实场景的数字都是**已曝光的探索性结果**：代理是检查后充电量加假定的 ε，不是隐藏的 C/20 真值。
- **未改动：** 真实提交包和之前所有研究。

## 结论先读

1. **在因果检验上，冷启动问题已经修复。** 选择只用这些检验，真实代理从未参与挑选设计。
   - **靠什么修好的：** 两项定律（磨合 + √t 日历 + 线性循环），加上对还没有锚点覆盖的那个月，用一对月内 45 °C 石墨台阶的首尾观测，β = 1（R2_B）。
   - **冷启动场景**（后面的月份里删掉所有更早的锚点）：R2_B 的 MAE 为 0.144 pp，V2 为 0.252，5A 的 S_main 为 0.287。
   - **伪场景：** R2_B 的 MAE 为 0.119 pp，V2 为 0.240。
   - **与 V2 集成**（w = 0.75，在这些检验上选出）：伪场景 0.123，冷启动 0.134。
2. **有一个模型通过了全部门槛：R3_TD_w0.75 = 0.75 × R3_T + 0.25 × V2，标注为已曝光 CK1。**
   - 真实代理，Δ = 0 / 0.4 / 0.8：MAE 0.188 / 0.131 / 0.174 pp，MAX 0.440 / 0.311 / 0.344 pp。V2：MAE 0.272 / 0.216 / 0.210，MAX 0.669。
   - 与 ε 无关的 CK2–7 MAE 0.145（V2 0.216）。CK2 误差 −0.311（V2 +0.669）。
   - 所有门槛都通过：G-proxy、G-epsfree、G-robust 6/6、G-pseudo、G-coldstart、G-regress（最大 +0.10 pp），以及 G-causal / G-impl（Python 3.13 和 3.11，差 0.0 pp，29 s）。在提交包**副本**上 `validate_submission.py` 通过。
   - **注意：** 它除 CK1 外与第二轮的 R2_D_w0.75 完全相同。它能通过门槛，靠的是 R3_T 的物理修正（台阶暂态从恢复运行起算，依据第四轮的 τ ≈ 2.5 天），而这个修正只改变第 0 月。该修正是在 5A 的 CK1 误差已知之后提出的，所以它在 CK1 上的改进（−0.366 → +0.048 pp）**不是证据**（规则 7，D3.1）。
3. **之前登记的主模型各差一个门槛。**
   - 第一轮主模型 D4_D2_w0.5 和第二轮主模型 R2_D_w0.75 都在 Δ = 0.8 时未通过 G-proxy，原因都只在 CK1。
   - 一些未被选中的集成权重在真实结果上通过了全部门槛（第一至三轮的 w = 0.25，第二、三轮的 w = 0.5）。它们**不是候选**，因为在真实结果出来后再选 w，就是在真实代理上做选择（D1.1）。
4. **目标**（候选 R3_TD_w0.75）：**达成 T2、T4、T6；未达成 T1、T3、T5。** 细节见下文。没有模型达成全部六项。
5. **建议。** 不要悄悄替换 V2。
   - "应力模型 + V2 集成"在类似 CK3–CK7 的情形下优于 V2，这一点有很强的因果证据：伪场景 0.123 对 0.240，冷启动 0.134 对 0.252。
   - CK1 上的表现依赖一个已曝光的修正。
   - 如果你想用排行榜试一下，候选已经准备好（见"候选"一节），V2 仍作后备。**没有改动任何提交文件。**

## 各轮概况

| 轮次 | 诊断（只依据伪场景 / 冷启动和物理） | 登记的设计 | 按登记规则的主模型 | 真实结果 |
|---|---|---|---|---|
| 1 | 5A：CK1 只靠先验；单一 t^z 项混淆磨合和存储；月内台阶没用上 | D1 S+台阶、D2 两项定律、D3 两者兼有、D4 集成、D5 已曝光 CK1 混合 | D4_D2_w0.5（分数 0.159） | 未过 G-proxy（Δ = 0.8 时 MAX 0.864，CK1 −0.47） |
| 2 | 台阶项权重过大（σ_s 0.05），β ≈ 1.3 放大了 45 °C 台阶下降；台阶只在冷启动时有帮助（[诊断](stage_2/DIAGNOSIS_round2.md)） | R2_A–C 只在空缺月用首尾台阶，β = 1；R2_D 集成 | R2_D_w0.75（分数 0.129） | 只未过 G-proxy（Δ = 0.8 时 MAE 0.233，CK1 −0.37） |
| 3 | 第二轮在伪场景 / CS 上已接近极限；物理：暂态从恢复运行起算，只影响第 0 月（[诊断](stage_2/DIAGNOSIS_round3.md)） | R3_T、R3_TD（都是已曝光 CK1） | 无合格者（规则 7：在伪场景 / CS 上与第二轮相同） | R3_TD_w0.75 通过全部门槛 |

## 结果（登记的设计和基线）

单位 pp。MAE 和 MAX 依次为 Δ = 0 / 0.4 / 0.8；CK1、CK2 为 Δ = 0.4。"伪场景"是 PG1、PG2、PC5、PC10（k ≥ 3）的平均 MAE；"冷启动"是 CS 和 CSE 的平均（Δ = 0.4）。完整表格：[S1](stage_1/outputs/S1_summary_table.csv)、[S2 R2](stage_2/outputs/S2_R2_summary_table.csv)、[S2 R3](stage_2/outputs/S2_R3_summary_table.csv)。

| 模型 | MAE | MAX | 与 ε 无关 | CK1 | CK2 | 伪场景 | 冷启动 | 门槛 |
|---|---|---|---|---|---|---|---|---|
| V2 | 0.272 / 0.216 / 0.210 | 0.669 / 0.669 / 0.669 | 0.216 | +0.217 | +0.669 | 0.240 | 0.252 | 参照 |
| M4 | 0.347 / 0.291 / 0.285 | 0.669 / 0.669 / 0.669 | 0.304 | +0.217 | +0.669 | 0.247 | 0.252 | — |
| 5A S_main | 0.270 / 0.326 / 0.382 | 0.742 / 1.134 / 1.526 | 0.192 | −1.134 | +0.565 | 0.131 | 0.287 | 未通过 |
| 5A ENS50 | 0.158 / 0.214 / 0.270 | 0.617 / 0.617 / 0.851 | 0.173 | −0.459 | +0.617 | 0.144 | 0.220 | 未通过 |
| D1 | 0.314 / 0.370 / 0.426 | 0.511 / 0.700 / 1.092 | 0.315 | −0.700 | −0.495 | 0.290 | 0.187 | 未通过 |
| D2 | 0.289 / 0.345 / 0.401 | 0.768 / 1.160 / 1.552 | 0.209 | −1.160 | −0.638 | 0.118 | 0.350 | 未通过 |
| D3 | 0.376 / 0.432 / 0.488 | 0.651 / 0.651 / 0.987 | 0.405 | −0.595 | −0.406 | 0.386 | 0.150 | 未通过 |
| D4_D1_w0.5 | 0.141 / 0.154 / 0.210 | 0.337 / 0.337 / 0.634 | 0.139 | −0.241 | +0.087 | 0.148 | 0.194 | 未通过 |
| **D4_D2_w0.5（第一轮主模型）** | 0.087 / 0.143 / 0.199 | 0.181 / 0.472 / 0.864 | 0.088 | −0.472 | +0.015 | 0.152 | 0.165 | 未通过（G-proxy） |
| D4_D3_w0.5 | 0.182 / 0.180 / 0.236 | 0.407 / 0.407 / 0.581 | 0.178 | −0.189 | +0.132 | 0.184 | 0.175 | 未通过 |
| D5 已曝光 CK1 | 0.434 / 0.378 / 0.372 | 0.651 / 0.651 / 0.651 | 0.405 | +0.217 | −0.406 | 0.386 | 0.150 | 未通过 |
| R2_A | 0.227 / 0.283 / 0.339 | 0.565 / 0.787 / 1.179 | 0.199 | −0.787 | +0.565 | 0.136 | 0.174 | 未通过 |
| R2_B | 0.202 / 0.258 / 0.314 | 0.638 / 0.638 / 0.953 | 0.208 | −0.561 | −0.638 | 0.119 | 0.144 | 未通过 |
| R2_C | 0.204 / 0.260 / 0.316 | 0.638 / 0.638 / 0.957 | 0.209 | −0.565 | −0.638 | 0.118 | 0.171 | 未通过 |
| **R2_D_w0.75（第二轮主模型）** | 0.128 / 0.177 / 0.233 | 0.311 / 0.366 / 0.759 | 0.145 | −0.366 | −0.311 | 0.123 | 0.134 | 未通过（G-proxy） |
| R3_T（已曝光 CK1） | 0.233 / 0.179 / 0.235 | 0.638 / 0.638 / 0.638 | 0.208 | −0.008 | −0.638 | 0.119 | 0.144 | 未通过 |
| **R3_TD_w0.75（候选，已曝光 CK1）** | **0.188 / 0.131 / 0.174** | **0.440 / 0.311 / 0.344** | **0.145** | +0.048 | −0.311 | 0.123 | 0.134 | **通过** |

各变体（σ_s、β 自由、25 °C 台阶、τ_b 自由）都未通过。未被选中的集成权重见 CSV 文件；其中在真实结果上通过门槛的（D4_*_w0.25；R2_D_w0.25/0.5；R3_TD_w0.25/0.5）只是已曝光的观察，不是候选。

**Δ = 0.4 时各检查点误差（pp）：**

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| V2 | +0.217 | +0.669 | +0.080 | +0.228 | +0.150 | −0.163 | −0.004 |
| R2_D_w0.75 | −0.366 | −0.311 | −0.092 | +0.132 | +0.033 | −0.197 | +0.107 |
| R3_TD_w0.75 | +0.048 | −0.311 | −0.092 | +0.132 | +0.033 | −0.197 | +0.107 |

## 目标（候选 R3_TD_w0.75）

| 目标 | 数值 | 结果 |
|---|---|---|
| T1 每个 Δ 下 MAE ≤ 0.15 | 0.188 / 0.131 / 0.174 | **未达成**（只在 Δ = 0.4 时达到） |
| T2 每个 Δ 下 MAX ≤ 0.45 | 0.440 / 0.311 / 0.344 | **达成** |
| T3 \|CK1\|、\|CK2\| ≤ 0.30 | +0.048（已曝光）/ −0.311 | **未达成**（CK2 差 0.011） |
| T4 与 ε 无关的 CK2–7 MAE ≤ 0.15 | 0.145 | **达成** |
| T5 伪场景 MAE ≤ 0.12 | 0.123 | **未达成**（差 0.003；R2_B 达到 0.119，但未过门槛） |
| T6 冷启动 MAE ≤ 0.20 | 0.134 | **达成**（V2：0.252） |

各轮主模型：第一轮 D4_D2_w0.5 达成 T4（0.088）和 T6；第二轮 R2_D_w0.75 达成 T4 和 T6。

## 候选（[candidate_model/](candidate_model/)）

- `r5c_stress_ensemble_model.MyModel`（只用 numpy/pandas）= 0.75 × R3_T + 0.25 × V2。
  - R3_T 是两项定律，在锚点对加上一对以恢复运行为参照的 45 °C 台阶首尾观测（用于还没有锚点的那个月）上做 MAP 拟合。
  - V2 是未改动的 V2 类。Challenge 1 / Yagci 先验以常量嵌入。
- **G-causal 与 G-impl：** 未来数据加噪、仅用 CK1 前缀拟合时，输出都逐位一致；与研究实现的差为 0.0 pp。
  - Python 3.13 / numpy 2.4.2 / pandas 3.0.0：[日志](stage_3/outputs/S3_candidate_checks_py313.json)。
  - Python 3.11.14 / numpy 2.4.6 / pandas 3.0.6：[日志](stage_3/outputs/S3_candidate_checks_py311.json)。
  - 完整运行约 29 秒。
- **打包检查：** 把候选文件接入 `cache/package_copy/my_model/`（被 git 忽略的副本），在 Python 3.11 下 `validate_submission.py` 通过（[日志](stage_3/outputs/S3_validate_submission_copy_py311.log)）。**真实提交包没有改动。**

**只用于排行榜的 SOH（%）：**

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| R3_TD_w0.75 | 95.823 | 94.157 | 93.368 | 92.715 | 91.963 | 91.296 | 90.932 |
| V2 | 95.992 | 95.137 | 93.541 | 92.811 | 92.081 | 91.331 | 90.821 |

如果要试用这个候选，把七个 `r5c_*.py` 文件复制到 `my_model/`，并在 `my_model/__init__.py` 中设置 `from .r5c_stress_ensemble_model import MyModel as ActiveModel`。这由你决定，本轮没有接入任何东西。

## 风险与限制

- **曝光。** 所有代理都已看过。冷启动场景是新的因果检验，但它复用的是同样的月份和电池组。
- **CK1 的修复是已曝光的**（D3.1）。候选在 CK1 上的数值依赖一个在 CK1 误差已知之后提出的物理修正。
- **与 V2 共有的假设。** ε，以及隐藏的 C/20 是否包含检查后恢复（第四轮：试验后期最多约 0.9 Ah）。两者都基于锚点，共担这一风险。外部数据集记录中"ε 随容量衰减漂移"一点没有建模。
- **先验迁移。** 两项定律的先验来自连续循环的 Challenge 1 电芯，其中只有 A_b 可辨识；τ_b、A_cal、A_cyc 都按规则回退。
- **单个电池组。** 只有 7 个检查点，相关性只是诊断。
- **偏离 D3.2。** harness 的因果检查被复制了一份，加了适配 pandas 3 的浮点转换。

## 复现

```bash
cd /Users/shane/Desktop/Arena_1015_r5c_stressfix/research/phase2_r5c_stress_fix_20261015
python3 -B stage_0/run_0.py
python3 -B stage_1/c1_two_term.py
python3 -B stage_1/run_1.py select && python3 -B stage_1/run_1.py real
python3 -B stage_2/run_2.py select && python3 -B stage_2/run_2.py real
python3 -B stage_2/run_3.py select && python3 -B stage_2/run_3.py real
python3 -B stage_3_check.py
cache/venv311/bin/python -B stage_3_check.py      # venv：/opt/homebrew/bin/python3.11 -m venv cache/venv311；pip install numpy pandas
```

研究环境：Python 3.13.0、numpy 2.4.2、pandas 3.0.0、scipy 1.18.0（scipy 只用于 Challenge 1 重拟合）。缓存在被 git 忽略的 `cache/` 中。
