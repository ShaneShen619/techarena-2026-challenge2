<a id="en"></a>

# V3: V2 + √t gap branch + β cap + median-of-cells steps — validation report

> English · [中文](#zh)

> [!IMPORTANT]
> **V3 as registered is NOT the recommended or submitted version.**
>
> The submitted model is **V2 + change 1 (√t gap branch) only**. It was wired into `TechArena_Challenge2_Team_Package/my_model/model_template.py` on 2026-10-15. Its proxy MAE is 0.123 pp and its maximum error 0.228 pp (Δ=0.4).
>
> V3 is not used because:
> - change 3 (median of cells) is not robust: dvdq_peak MAE 0.333 → 0.448;
> - change 2 (β cap) raises CK5–CK7 SOH, in the same direction as the known ε-drift risk.
>
> V3's lower proxy MAE (0.114) does not make it the better choice. The wired model matches the research V2+1 to within 0.0004 pp and passes the noise-causality check on all 8 checkups ([outputs/submission_check.json](outputs/submission_check.json)).

- **Run date:** 2026-10-15.
- **Protocol:** [protocol.json](protocol.json), SHA256 `e87a1683…`. It was frozen before any V3 code was written.
- **Base:** V2_main ([../phase2_v2_phase_matched_20261013/](../phase2_v2_phase_matched_20261013/)). The harness reproduces V2 to 1.4×10⁻¹⁴ Ah.

## Conclusions first

**V3 passes all five pre-registered gates. Proxy MAE at Δ=0.4 falls from 0.216 to 0.114 pp, and the maximum error from 0.669 to 0.255 pp.** Almost all of that gain comes from change 1 (CK2 √t), and change 1 was exposed before registration. A supplement run after the main evaluation shows that change 3 is not robust. The recommended next candidate is therefore **V2 + change 1, optionally with change 2**, not V3 as registered. Nothing has been wired into `my_model`.

## Results (main step method, A4 2 Ah)

| Model | MAE Δ0 / 0.4 / 0.8 | MAX Δ0 / 0.4 / 0.8 | CK3–7 MAE (ε-independent) |
|---|---|---|---|
| V2 | 0.272 / 0.216 / 0.210 | 0.669 / 0.669 / 0.669 | 0.125 |
| V2+1 (√t) | 0.207 / 0.123 / 0.140 | 0.609 / 0.228 / 0.228 | 0.125 |
| V2+2 (β cap 1.2) | 0.280 / 0.224 / 0.218 | 0.669 | 0.136 |
| V2+3 (median) | 0.258 / 0.202 / 0.206 | 0.674 | 0.112 |
| V2+1+2 | 0.215 / 0.131 / 0.148 | 0.609 / 0.228 / 0.228 | 0.136 |
| V2+1+3 | 0.192 / 0.108 / 0.135 | 0.572 / 0.255 / 0.255 | 0.112 |
| **V3 (1+2+3)** | **0.198 / 0.114 / 0.141** | **0.572 / 0.255 / 0.255** | **0.120** |

Per-checkup errors at Δ=0.4 (pp):

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| V2 | +0.22 | +0.67 | +0.08 | +0.23 | +0.15 | −0.16 | −0.00 |
| V3 | +0.18 | −0.02 | +0.13 | +0.26 | +0.08 | +0.05 | +0.09 |

V3 branches: CK1 and CK3 use the fallback, CK2 uses √t_gap, and CK4–CK7 use the phase-matched branch. β is capped at 1.2 for CK3 and CK5–CK7.

## Gates

| Gate | Result |
|---|---|
| K1 causality | **Pass.** With every operation value after each cut replaced by noise, the predictions are bit-identical (7/7). |
| K2 proxy | **Pass.** MAE is lower at all three Δ, and the maximum error is not higher. |
| K3 ε scope | **Pass.** CK3–7 MAE is 0.120 vs 0.125. CK2 is ε-dependent: −0.21 / −0.02 / +0.18 pp. |
| K4 robustness | **Pass.** V3 wins on 6/6 step-detection variants, and all 8 sensitivity settings stay below V2. |
| K5 no large regression | **Pass.** The largest single-checkup increase in absolute error is +0.08 pp (CK7). CK3 rises by +0.05 and CK4 by +0.03. |

## Contribution of each change (supplement, run after the main evaluation)

MAE at Δ=0.4, by step-detection variant:

| Model | main | band_narrow | windows−3 | windows+3 | dvdq_peak | ir_corrected |
|---|---|---|---|---|---|---|
| V2 | 0.216 | 0.217 | 0.274 | 0.304 | 0.333 | 0.238 |
| V2+1 | 0.123 | 0.121 | 0.178 | 0.211 | **0.254** | 0.150 |
| V2+2 | 0.224 | 0.226 | 0.275 | 0.308 | 0.301 | 0.239 |
| V2+3 | 0.202 | 0.197 | 0.278 | 0.304 | **0.448** | 0.226 |
| V3 | 0.114 | 0.113 | 0.185 | 0.213 | 0.324 | 0.146 |

- **Change 1 (√t for the uncovered period).**
  - It improves every variant by 0.08–0.10 pp, and only CK2 triggers it.
  - It is exposed, and it depends on ε and on its own assumptions. Across p = 0.4–0.6 and a ±5-day time origin, the CK2 error ranges from −0.35 to +0.29 pp at Δ=0.4. Every setting is still better than V2's +0.67.
- **Change 2 (β cap 1.2).**
  - On the proxy it costs 0.008 pp on the main method and helps only on dvdq_peak.
  - It is a hedge against β running high, justified by the external data, not a proxy improvement. The cap binds at CK3 and CK5–CK7 and moves CK6 from −0.16 to +0.05 pp.
- **Change 3 (median of cells).**
  - It is not robust. It helps on 3 of 6 detection variants and badly worsens dvdq_peak: MAE 0.333 → 0.448, and CK3–7 MAE 0.223 → 0.396.
  - The ESSL1 motivation (16 cells, single-cell mis-detections) does not transfer to 4 cells, where the median is the mean of only two cells.

## Recommendation and limits

- **Use V2 + change 1 as the next candidate, optionally with change 2. Drop change 3.**
  - V2+1: MAE 0.123, maximum 0.228 pp.
  - V2+1+2: MAE 0.131, maximum 0.228 pp.
  - This is a post-hoc choice informed by the supplement. It must be stated as such.
- **CK2 is the only checkup the √t branch changes.** On the proxy it moves CK2 from the worst point to one of the best, but the hidden truth for CK2 is still unknown. The rule extrapolates the CK0→CK1 loss, so a first-month break-in, the CK0 temperature confound (ε0) and the exponent assumption all propagate into it.
- **Remaining limits.** All errors are proxy errors. The ε drift risk (up to about 0.3 pp by CK7, see [external_data/DATA_MANIFEST.md](../../external_data/DATA_MANIFEST.md)) is not modelled.

## Reproduction

```bash
cd research/phase2_v3_20261015
python3 -B stage_v3_eval.py                 # main evaluation, ablations, sensitivity, gates, causality
python3 -B stage_v3_ablation_variants.py    # supplement: each change on all six step variants
```

Outputs are in `outputs/`: V3_predictions_long, V3_metrics, V3_errors_per_checkup_eps0.4, V3_CK2_by_delta, V3_branch_beta, V3_gates.json, V3_ablation_by_variant. The study runs on Python 3.13 with numpy 2.4 and pandas 3.0.

---

<a id="zh"></a>

# V3：V2 + √t 缺口分支 + β 上限 + 电芯中位数：验证报告

> [English](#en) · 中文

> [!IMPORTANT]
> **按登记版本的 V3 不是推荐版本，也不是提交版本。**
>
> 提交的是 **V2 + 第 1 项（√t 缺口分支）**，已于 2026-10-15 接入 `TechArena_Challenge2_Team_Package/my_model/model_template.py`。代理 MAE 0.123 pp，最大误差 0.228 pp（Δ=0.4）。
>
> 不用 V3 的原因：
> - 第 3 项（中位数汇总）不稳健：dvdq_peak 方法的 MAE 从 0.333 升到 0.448；
> - 第 2 项（β 上限）会抬高 CK5–CK7 的 SOH 预测，与已知的 ε 漂移风险方向相同。
>
> V3 的代理 MAE 更低（0.114），但不能因此认为它更好。接入后的模型与研究实现 V2+1 的差异不超过 0.0004 pp，8 个检查点的噪声因果性检验全部通过（[outputs/submission_check.json](outputs/submission_check.json)）。

- **运行日期：** 2026-10-15。
- **协议：** [protocol.json](protocol.json)（SHA256 `e87a1683…`），在写任何 V3 代码之前冻结。
- **基线：** V2_main。评估流程复现 V2 的结果，误差 1.4×10⁻¹⁴ Ah。

## 结论先行

**V3 通过全部 5 道预登记验收门。Δ=0.4 时代理 MAE 从 0.216 降到 0.114 pp，最大误差从 0.669 降到 0.255 pp。** 但几乎全部收益来自第 1 项（CK2 的 √t），而这一项在登记之前就已曝光。主评估之后补跑的结果显示第 3 项不稳健。因此建议的下一个候选是 **V2 + 第 1 项（第 2 项可选）**，而不是按登记版本的 V3。没有接入 `my_model`。

## 结果（主台阶方法，A4 平滑 2 Ah）

| 模型 | MAE Δ0 / 0.4 / 0.8 | 最大误差 | CK3–7 MAE（与 ε 无关） |
|---|---|---|---|
| V2 | 0.272 / 0.216 / 0.210 | 0.669 | 0.125 |
| V2+1（√t） | 0.207 / 0.123 / 0.140 | 0.609 / 0.228 / 0.228 | 0.125 |
| V2+2（β 上限 1.2） | 0.280 / 0.224 / 0.218 | 0.669 | 0.136 |
| V2+3（中位数） | 0.258 / 0.202 / 0.206 | 0.674 | 0.112 |
| V2+1+2 | 0.215 / 0.131 / 0.148 | 0.609 / 0.228 / 0.228 | 0.136 |
| V2+1+3 | 0.192 / 0.108 / 0.135 | 0.572 / 0.255 / 0.255 | 0.112 |
| **V3（1+2+3）** | **0.198 / 0.114 / 0.141** | **0.572 / 0.255 / 0.255** | **0.120** |

Δ=0.4 时逐检查点误差（pp）：

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| V2 | +0.22 | +0.67 | +0.08 | +0.23 | +0.15 | −0.16 | −0.00 |
| V3 | +0.18 | −0.02 | +0.13 | +0.26 | +0.08 | +0.05 | +0.09 |

## 各项改动的贡献（主评估之后补跑）

Δ=0.4 时各台阶检测方法的 MAE：

| 模型 | main | band_narrow | windows−3 | windows+3 | dvdq_peak | ir_corrected |
|---|---|---|---|---|---|---|
| V2 | 0.216 | 0.217 | 0.274 | 0.304 | 0.333 | 0.238 |
| V2+1 | 0.123 | 0.121 | 0.178 | 0.211 | **0.254** | 0.150 |
| V2+2 | 0.224 | 0.226 | 0.275 | 0.308 | 0.301 | 0.239 |
| V2+3 | 0.202 | 0.197 | 0.278 | 0.304 | **0.448** | 0.226 |
| V3 | 0.114 | 0.113 | 0.185 | 0.213 | 0.324 | 0.146 |

- **第 1 项（√t）。**
  - 6 种方法都改善 0.08–0.10 pp，只在 CK2 触发。
  - 这一项已曝光，并且依赖 ε 和自身假设。指数 p 取 0.4–0.6、时间起点前后移 5 天时，CK2 误差在 −0.35 到 +0.29 pp 之间（Δ=0.4），所有设定仍然都好于 V2 的 +0.67。
- **第 2 项（β 上限）。**
  - 代理上略有代价：主方法差 0.008 pp，只在 dvdq_peak 上有帮助。
  - 它是防止 β 偏高的保险，依据是外部数据，不是用来提高代理分数的。
- **第 3 项（中位数）。**
  - 不稳健。6 种方法里只有 3 种变好，dvdq_peak 明显变差：MAE 0.333 → 0.448，CK3–7 MAE 0.223 → 0.396。
  - 16 串电池组上的结论不能直接搬到 4 串：4 只电芯取中位数，只相当于中间两只的平均。

## 建议与局限

- **下一个候选用 V2 + 第 1 项，第 2 项作为可选保险，放弃第 3 项。**
  - V2+1：MAE 0.123，最大误差 0.228 pp。
  - V2+1+2：MAE 0.131，最大误差 0.228 pp。
  - 这是看过补充结果之后做的选择，必须如实标注。
- **√t 分支只改变 CK2。** 在代理上，CK2 从误差最大的一个点变成最好的之一，但 CK2 的真值仍然未知。这条规则外推的是 CK0→CK1 的损失，所以首月磨合、CK0 的温度混淆（ε0）和指数假设都会传进去。
- **其他局限。** 所有误差都是代理误差。ε 漂移的风险（到 CK7 最多约 0.3 pp）没有建模。
