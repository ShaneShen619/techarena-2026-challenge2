<a id="en"></a>

# WP2 — Temperature-weighted √t for the CK2 gap branch

> **Language:** English · [中文](#zh)

- **Protocol:** [protocol.json](protocol.json), committed in `712da9f` before any WP2 prediction.
- **Causal results:** committed in `d76fd20` before the real run.
- **Code:** research [src/tsqrt.py](../src/tsqrt.py) and [run_wp2.py](run_wp2.py); candidate class [candidate_model/model_template.py](candidate_model/model_template.py) (not wired); checks [check_candidate.py](check_candidate.py) and [check_package.sh](check_package.sh).

## Conclusions first

1. **T_main passes every registered gate, so the registered decision is "recommend switching" from SUB to T_main.**
   - T_main is SUB with the √t time axis replaced by Arrhenius-weighted 45 °C-equivalent days (Ea 20.6 kJ/mol; checkup gaps 25 °C; missing segment 3 at 45 °C).
   - **Nothing was wired.** The change affects only CK2: **94.451 → 94.507 % SOH (+0.057 pp)**.
2. **The causal evidence is modest but consistent.**
   - On the 5 distinct one-month √t extrapolations outside CK2 (k = 3..7), gap-case MAE falls from 0.113 to 0.105 pp; CSE: 0.118 → 0.110.
   - Pseudo mean 0.148 → 0.144; cold start 0.174 → 0.170.
   - T_ea37 (Ea 37.3) is a little better on all three, but by rule only T_main is the main design.
   - The non-causal reference R_p044 (calendar time, p = 0.44) is **worse** on every causal metric (gap cases 0.142). Simply lowering the exponent is not supported; weighting time by temperature is.
3. **Real CK2 is exposed and only moves slightly.** CK2 error at Δ 0.4 goes from −0.018 (SUB) to +0.039 pp (T_main), +0.073 (T_ea37) and +0.093 (T_gap45). Real MAE at Δ 0/0.4/0.8 moves from 0.207/0.123/0.140 to 0.197/0.126/0.146; MAX is unchanged (0.609/0.228/0.228).
4. **TUM consistency.** T_main's CK1→CK2 loss increment is 0.957× SUB's. The TUM data suggest about 0.87×, so T_main closes about a third of that gap (T_ea37: 0.932×).
5. **Main assumption to state in the report: the temperature of the missing segment 3.** With segment 3 at 25 °C (T_seg25, sensitivity only), CK2 would rise by +0.39 pp and every causal metric worsens. The public schedule (short 25 °C / long 45 °C, segment 3 is 20 days long) supports 45 °C.

## Gates against SUB

| Gate | T_main | T_ea37 | T_gap45 | T_seg25 | R_p044 |
|---|---|---|---|---|---|
| G_gapcases (≤ SUB − 0.005) | **pass** (0.105 vs 0.113) | pass (0.101) | fail (0.108) | fail | fail |
| G_pseudo (≤ SUB + 0.005) | pass (0.144) | pass (0.142) | pass | fail | fail |
| G_coldstart (≤ SUB + 0.005) | pass (0.170) | pass (0.168) | pass | fail | fail |
| G_hyp (grid max regret ≤ SUB + 0.005) | pass (0.0354 vs 0.0344) | pass (0.0360) | pass | fail | (non-causal) |
| G_causal (noise after cut, 8 checkups) | **pass**, bit-identical | — | — | — | — |
| G_impl (class vs research ≤ 0.001 pp; Python 3.11 venv; validator; < 30 min) | **pass**: 0.0004 pp; Python 3.11.14, numpy 2.4.6, pandas 3.0.6; `validate_submission.py` PASSED; full train + test 12 s | — | — | — | — |

## Real scenario (exposed-CK2)

| Model | MAE Δ0 / 0.4 / 0.8 | MAX Δ0 / 0.4 / 0.8 | CK2 err Δ0.4 | CK2 SOH |
|---|---|---|---|---|
| SUB | 0.207 / 0.123 / 0.140 | 0.609 / 0.228 / 0.228 | −0.018 | 94.451 |
| T_main | 0.197 / 0.126 / 0.146 | 0.609 / 0.228 / 0.228 | +0.039 | 94.507 |
| T_ea37 | 0.192 / 0.131 / 0.151 | 0.609 / 0.228 / 0.254 | +0.073 | 94.541 |
| T_gap45 | 0.188 / 0.133 / 0.153 | 0.609 / 0.228 / 0.271 | +0.093 | 94.561 |
| T_seg25 | 0.210 / 0.173 / 0.187 | 0.609 / 0.371 / 0.509 | +0.371 | 94.840 |
| R_p044 | 0.177 / 0.145 / 0.162 | 0.609 / 0.228 / 0.338 | +0.171 | 94.639 |

(Full numbers in [wp2_real_summary.json](outputs/wp2_real_summary.json). Only CK2 differs between designs.)

## How to adopt (if the user decides to)

Replace the package's `my_model/model_template.py` with [candidate_model/model_template.py](candidate_model/model_template.py). The diff against the submitted file is the docstring, 7 constants, `_effective_days` and the two-line change in `_sqrt_extrapolation` and its call. Then rebuild the zip with `research/phase2_v3_20261015/package_submission.py` on the submission branch. This round does not do it.

---

<a id="zh"></a>

# WP2 — CK2 缺口分支的温度加权 √t

> **语言：** [English](#en) · 中文

- **协议：** [protocol.json](protocol.json)，在任何 WP2 预测之前于 `712da9f` 提交。
- **因果结果：** 在跑真实场景之前于 `d76fd20` 提交。
- **代码：** 研究实现 [src/tsqrt.py](../src/tsqrt.py) 和 [run_wp2.py](run_wp2.py)；候选类 [candidate_model/model_template.py](candidate_model/model_template.py)（未接入）；检查脚本 [check_candidate.py](check_candidate.py) 和 [check_package.sh](check_package.sh)。

## 结论先读

1. **T_main 通过了全部登记门槛，按登记规则的决策是“建议从 SUB 切换到 T_main”。**
   - T_main 就是 SUB，只是把 √t 的时间轴换成按 Arrhenius 加权的 45 °C 等效天数（Ea 20.6 kJ/mol；检查间隔按 25 °C；缺失的段 3 按 45 °C）。
   - **没有接入任何东西。** 这个改动只影响 CK2：**94.451 → 94.507 % SOH（+0.057 pp）**。
2. **因果证据不大，但方向一致。**
   - 在 CK2 以外 5 个不同的一个月 √t 外推（k = 3..7）上，缺口案例 MAE 从 0.113 降到 0.105 pp；CSE 从 0.118 降到 0.110。
   - 伪场景平均 0.148 → 0.144；冷启动 0.174 → 0.170。
   - T_ea37（Ea 37.3）在三项上都略好，但按规则主设计只能是 T_main。
   - 不符合因果性的参照 R_p044（日历时间、p = 0.44）在所有因果指标上都**更差**（缺口案例 0.142）。也就是说，单纯降低指数没有依据，按温度加权时间才有。
3. **真实 CK2 已曝光，变化很小。** Δ 0.4 时 CK2 误差从 −0.018（SUB）变为 +0.039 pp（T_main）、+0.073（T_ea37）和 +0.093（T_gap45）。真实场景 Δ 0/0.4/0.8 的 MAE 从 0.207/0.123/0.140 变为 0.197/0.126/0.146；MAX 不变（0.609/0.228/0.228）。
4. **与 TUM 数据的一致性。** T_main 的 CK1→CK2 损失增量是 SUB 的 0.957 倍。TUM 数据提示约 0.87 倍，所以 T_main 弥补了这一差距的约三分之一（T_ea37 为 0.932 倍）。
5. **报告中需要写明的主要假设：缺失的段 3 的温度。** 若段 3 为 25 °C（T_seg25，只作敏感性分析），CK2 会上调 0.39 pp，而且所有因果指标都变差。公开的时间表（短段 25 °C / 长段 45 °C，段 3 长 20 天）支持 45 °C。

## 门槛

T_main 通过：G_gapcases（0.105 对 0.113）、G_pseudo、G_coldstart、G_hyp（0.0354 对 0.0344 + 0.005）、G_causal（截断后数据换成噪声，8 个检查点逐位一致）和 G_impl（与研究实现相差 0.0004 pp；Python 3.11.14、numpy 2.4.6、pandas 3.0.6 下 `validate_submission.py` 通过；完整训练和测试用时 12 秒）。

## 如果决定采用

用 [candidate_model/model_template.py](candidate_model/model_template.py) 替换提交包的 `my_model/model_template.py`。与已提交文件相比，改动只有文档字符串、7 个常量、`_effective_days` 函数，以及 `_sqrt_extrapolation` 及其调用处的两行。然后在提交分支上用 `research/phase2_v3_20261015/package_submission.py` 重新打包。本轮不做这一步。
