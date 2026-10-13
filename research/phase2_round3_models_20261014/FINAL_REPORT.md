<a id="en"></a>

# Round 3 alternative capacity models — final report

> English · [中文](#zh)

**Keep V2 as the leading research candidate. No new model passed its stage gates.** All six stages have completed with positive or negative findings; no stage needed its time cap. The active M4 submission was not changed. This is **exposed-exploratory** research: proxies were already seen, are post-checkup charge observations plus an assumed ε, and are not hidden C/20 truth.

V2 reproduces MAE **0.215726 pp**, MAX **0.669052 pp** at Δ=0.4, versus M4 MAE 0.291265 pp. The V2 reference candidate passes exact future-noise and fit-on-CK1-prefix comparisons, pickling, sample_data smoke and Python 3.11.14; its maximum difference from research is 1.42×10⁻¹⁴ pp. No newly passing candidate class or ensemble was warranted.

## All candidates and variants

All numbers are SOH percentage points. Main step method and A4 2 Ah; pseudo-scenario MAE uses Δ=0.4. The three numbers in each metric column use Δ=0, 0.4, 0.8. **n=6 for D3** because CK2 is undefined; that average cannot be compared with seven-checkup models. For D2 and SS variants, CK2–7 is a subset metric and is **not ε-free**.

| Model | n | MAE Δ0 / .4 / .8 | MAX Δ0 / .4 / .8 | RMSE Δ0 / .4 / .8 | CK2–7 MAE Δ.4 | ε independent | PG1 | PG2 | PC5 | PC10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M4 | 7 | 0.347 / 0.291 / 0.285 | 0.669 / 0.669 / 0.669 | 0.406 / 0.345 / 0.341 | 0.304 | yes | 0.251 | 0.207 | 0.325 | 0.340 |
| V2 | 7 | 0.272 / 0.216 / 0.210 | 0.669 / 0.669 / 0.669 | 0.364 / 0.293 / 0.289 | 0.216 | yes | 0.251 | 0.207 | 0.302 | 0.340 |
| D0 | 7 | 0.272 / 0.216 / 0.210 | 0.669 / 0.669 / 0.669 | 0.364 / 0.293 / 0.289 | 0.216 | yes | 0.251 | 0.207 | 0.302 | 0.340 |
| D1 | 7 | 0.380 / 0.324 / 0.318 | 1.427 / 1.427 / 1.427 | 0.599 / 0.559 / 0.557 | 0.342 | yes | 0.386 | 0.337 | 0.428 | 0.687 |
| D2 | 7 | 0.370 / 0.270 / 0.244 | 1.358 / 1.049 / 0.911 | 0.576 / 0.423 / 0.372 | 0.279 | no | 0.412 | 0.350 | 0.365 | 0.473 |
| D3 | 6 | 0.206 / 0.140 / 0.133 | 0.609 / 0.228 / 0.228 | 0.282 / 0.160 / 0.152 | 0.125 | yes | 0.205 | 0.230 | 0.229 | 0.176 |
| V2_reg | 7 | 0.298 / 0.242 / 0.236 | 0.669 / 0.669 / 0.669 | 0.380 / 0.313 / 0.310 | 0.246 | yes | 0.251 | 0.207 | 0.312 | 0.340 |
| V2_reg_dvdq | 7 | 0.330 / 0.274 / 0.268 | 0.669 / 0.669 / 0.669 | 0.403 / 0.340 / 0.337 | 0.284 | yes | 0.251 | 0.207 | 0.319 | 0.340 |
| V2_reg_bottom | 7 | 0.296 / 0.240 / 0.234 | 0.669 / 0.669 / 0.669 | 0.378 / 0.311 / 0.308 | 0.244 | yes | 0.251 | 0.207 | 0.310 | 0.340 |
| SS | 7 | 0.479 / 0.355 / 0.242 | 0.935 / 0.696 / 0.616 | 0.604 / 0.421 / 0.307 | 0.334 | no | 0.136 | 0.225 | 0.336 | 0.353 |
| SS_tau3 | 7 | 0.584 / 0.444 / 0.305 | 1.613 / 0.976 / 0.573 | 0.777 / 0.524 / 0.339 | 0.443 | no | 0.148 | 0.208 | 0.445 | 0.435 |
| SS_tau8 | 7 | 0.352 / 0.243 / 0.228 | 0.749 / 0.696 / 0.643 | 0.444 / 0.340 / 0.310 | 0.235 | no | 0.107 | 0.225 | 0.231 | 0.263 |
| SS_beta1 | 7 | 0.911 / 0.740 / 0.569 | 1.066 / 0.995 / 0.924 | 0.915 / 0.762 / 0.657 | 0.783 | no | 0.393 | 0.665 | 0.743 | 0.539 |
| SS_rw01 | 7 | 0.486 / 0.359 / 0.232 | 0.935 / 0.521 / 0.483 | 0.588 / 0.405 / 0.286 | 0.339 | no | 0.098 | 0.141 | 0.355 | 0.399 |
| SS_rw04 | 7 | 0.553 / 0.410 / 0.266 | 0.935 / 0.810 / 0.714 | 0.650 / 0.470 / 0.357 | 0.398 | no | 0.238 | 0.348 | 0.404 | 0.344 |

Full precision, sample counts, every step/A4 setting and scenario are in [independent_all_predictions.csv](stage_F/outputs/independent_all_predictions.csv) and [independent_main_metrics.csv](stage_F/outputs/independent_main_metrics.csv). δ in the original reports sometimes denotes the proxy offset; here Δ denotes that offset, while δ in SS is the fitted temperature shift.

## Per-checkup errors at Δ=0.4

| Model | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M4 | 0.217 | 0.669 | 0.080 | 0.279 | -0.111 | -0.402 | -0.281 |
| V2 | 0.217 | 0.669 | 0.080 | 0.228 | 0.150 | -0.163 | -0.004 |
| D0 | 0.217 | 0.669 | 0.080 | 0.228 | 0.150 | -0.163 | -0.004 |
| D1 | 0.217 | -1.427 | 0.080 | 0.228 | 0.150 | -0.163 | -0.004 |
| D2 | 0.217 | -1.049 | 0.080 | 0.228 | 0.150 | -0.163 | -0.004 |
| D3 | 0.217 | unavailable | 0.080 | 0.228 | 0.150 | -0.163 | -0.004 |
| V2_reg | 0.217 | 0.669 | 0.080 | 0.353 | 0.219 | -0.103 | 0.051 |
| V2_reg_dvdq | 0.217 | 0.669 | 0.080 | 0.431 | 0.314 | 0.066 | 0.145 |
| V2_reg_bottom | 0.217 | 0.669 | 0.080 | 0.343 | 0.212 | -0.111 | 0.047 |
| SS | 0.481 | 0.501 | -0.044 | 0.696 | 0.463 | -0.070 | -0.232 |
| SS_tau3 | 0.450 | 0.976 | -0.143 | 0.670 | 0.431 | -0.138 | -0.301 |
| SS_tau8 | 0.290 | 0.041 | 0.052 | 0.696 | 0.459 | -0.004 | -0.158 |
| SS_beta1 | 0.481 | 0.501 | 0.675 | 0.831 | 0.995 | 0.785 | 0.911 |
| SS_rw01 | 0.481 | 0.501 | -0.516 | 0.521 | 0.337 | -0.064 | -0.095 |
| SS_rw04 | 0.481 | 0.501 | 0.125 | 0.810 | 0.528 | -0.107 | -0.315 |

## Acceptance decisions

| Stage/main | Decision | G-proxy | G-epsfree | G-robust | G-regress |
| --- | --- | --- | --- | --- | --- |
| B | diagnostic-only exit | not applicable | not applicable | not applicable | not applicable |
| D0 selected | no CK2 or PG improvement | fail | fail | 0/6 | pass |
| V2_reg | rejected | fail | fail | 0/6 | pass |
| SS | rejected | fail | not ε-free; threshold fails | 0/6 | fail |
| E | unscored sensitivity; inconclusive | not scored | not scored | not applicable | not applicable |
| F | only V2 eligible; no ensemble | not applicable | not applicable | not applicable | not applicable |

G-causal and G-impl are independently **passed for the V2 reference class**. New research models already failed their required performance gates, so they were rejected without producing submission classes; their class-level causal/implementation gates are **not run**, not claimed passed or failed. Late diagnostic variants never replace a registered main result.

## Stage findings

**B — diagnostic-only exit.** Of 41 CV-ending charges, only eight post-checkup anchors span ≥45 Ah. Periodic CCCV charges span about 21 Ah and miss the graphite step; zero of seven months have two usable 45-C charge-side events. No additional charge channel enters C. [Report](stage_B/REPORT.md).

**D — keep D0.** PG1+PG2 MAE is D0 0.229, D1 0.361 and D2 0.381 pp. D3 is 0.217 but undefined for CK2 and ineligible. Selection was committed as 816a21d before the real-data evaluation, and no CK2 tuning was observed. However PC5/PC10 CK2 are identical to the real CK2 prefix and were evaluated before that commit: the strict CK2 result-order requirement was violated. D1/D2 worsen CK2 to −1.427/−1.049 pp, compared with V2 +0.669. This rejects the tested rules; it does **not** establish an irreducible error floor. Leave-one-anchor-observation-out MAE is D0 0.336, D1 0.514, D2 0.466 and D3 0.301 (D3 excludes CK2). [Report](stage_D/REPORT.md).

**A — registration beta rejected.** Main MAE is 0.242 pp and six step variants give zero wins. Original profiles identify bottom/top scales in 60%/85% of anchor-cell fits, but the original voltage nuisance was unconstrained and not profiled. The unscored bounded-nuisance audit identifies bottom/top/voltage in only 40%/80%/20%; it cannot rehabilitate the main beta. Dual CK0/first25C templates, 1/2/3-Ah derivative features and all three parameter profiles are now supplied in separately registered supplements. The strong start-voltage/bottom-change correlation (r=−0.975) suggests confounding; it does not uniquely prove LAM or its absence. The Q_fc residual correlation r≈0.04 in this small sample neither rules out start-state effects nor validates the proxy. [Main report](stage_A/REPORT.md), [templates](stage_A/TEMPLATE_REPORT.md), [profiles](stage_A/BOUNDED_PROFILE_REPORT.md).

**C — fusion rejected.** Main MAE is 0.355 pp, CK2–7 MAE is 0.334 at Δ=0.4, and regression exceeds 0.30 pp. τ=8 reaches 0.243 pp but is a variant and still loses to V2. The fitted temperature/transient terms are consistent with prior observations under this model, not an independent mechanism validation. All monthly rates/amplitudes and pseudo-scenario calibration are supplied. The 7-point real-data fraction within 2 SD is 5/7; calibration is descriptive because points are exposed and scenarios reuse observations. D2 error spans 0.447 pp and SS spans 0.868 pp across the ε assumptions at CK2–7, so neither subset score is genuinely ε-free. Metadata additions match 648 original predictions exactly (0 Ah difference). [Report](stage_C/REPORT.md), [states](stage_C/outputs/C_independent_monthly_states.csv), [calibration](stage_C/outputs/C_independent_calibration.csv).

**E — ε remains unverified.** Prescribed causal per-cell charge maps/A4 fallback maps are applied to the CK0 loaded discharge, summed and solved for the first 11.2 V root. Only anchors visible before each CK cutoff are used. 90/105 roots exist within the registered 0.1-Ah tail extension; among finite roots, max |ε−ε0| is 0.022651 pp. Fifteen unavailable roots mean the overall range is **inconclusive**, not established negligible. The raw four-cell reference sum ends at 11.203 V; its extended root is 100.416854 Ah. No absolute IR/polarization was added, and charge-specific voltage offsets were not transplanted into discharge. The original S0/S1/S2 mechanism stress scenarios remain separate: legacy S1 gives 0.26–0.51 pp but uses an arbitrary −1 V endpoint jump in interpolation, so those values are not validated continuous pack roots or rigorous upper bounds. The registered leaderboard-only V2_S1 option remains an unqualified diagnostic; it is neither recommended nor claimed to improve proxy scores. [Causal mapping report](stage_E/REQUIRED_MAPPING_REPORT.md), [legacy scenarios](stage_E/REPORT.md).

**F — no ensemble.** Only V2 is eligible. Pairwise correlation has no definition for a single member, so the fixed-weight ensemble reporting condition is not met. [Report](stage_F/REPORT.md).

## Protocol deviations and limits

- Concurrent work was found after initial setup. Original harness interfaces and completed commits were preserved; supplementary outputs are now integrated and committed.
- D2 estimates missing throughput from visible 45-C history because the post-gap counter jump is unavailable causally at CK2; it also uses beta=1 step observations rather than the specified beta conversion. Its failure is evidence about this implementation, not an exact test of the prescribed D2 formula.
- A dual-reference features, bounded voltage profiles and the required E maps were missing from the first main runs. Supplements froze separate protocols before their own computation. They came after main evaluation and cannot be presented as original pre-registration or used to select a replacement.
- Main configurations and stage-D selection were retained. Required 1/3-Ah A4 sensitivity variants are reported separately; A cache keys now include reference feature coordinates to avoid cross-window cache reuse.
- Proxies are already exposed. Pseudo cuts/gaps increase test cases, not independent packs or hidden labels. Small correlations do not validate physical causality or the capacity label.
- ε, full-charge start state, post-checkup recovery, 25/45-C transfer, endpoint extrapolation and the single-pack design remain material limits. Independent same-protocol capacity measurements would resolve these assumptions; this run cannot infer hidden CK1–CK7 truth.

## Exact reproduction

Run from the specified worktree. `-B` prevents bytecode writes into reused directories. Reproduction reruns frozen analyses and reports; it does not recreate the historical pre-registration/selection timing. Environment versions are recorded in stage_0/outputs/*environment.json. Extraction caches are git-ignored.

```bash
cd /Users/shane/Desktop/Arena_1013_model/research/phase2_round3_models_20261014
python3 -B stage0_reproduce.py
python3 -B stage_B/audit_coverage.py
python3 -B stage_D/run_select.py
python3 -B stage_D/run_eval.py
python3 -B stage_D/run_independent_robustness.py
python3 -B stage_A/run_a.py
python3 -B stage_A/explore_start_state.py
python3 -B stage_A/run_independent_smoothing.py
python3 -B stage_A/run_templates.py
python3 -B stage_A/run_bounded_profiles.py
python3 -B stage_C/run_c.py
python3 -B stage_C/run_independent_diagnostics.py
python3 -B stage_E/run_e.py
python3 -B stage_E/run_required_mapping.py
python3 -B stage_F/run_independent_summary.py
python3 -B stage_F/write_final_report.py
python3 -B stage_0/audit_integrity.py
```

```bash
/opt/homebrew/bin/python3.11 -m venv /tmp/arena-round3-py311
/tmp/arena-round3-py311/bin/pip install numpy==2.4.6 pandas==3.0.6
/tmp/arena-round3-py311/bin/python -B stage_0/validate_candidate.py \
  candidate_model/v2_reference_model.py stage_0/outputs/predictions.csv V2 \
  --output stage_0/outputs/v2_independent_candidate_check.json
```

Protected tracked directories are unchanged relative to 24728fa. Protocol hashes, bilingual document markers and candidate imports are checked by stage_0/audit_integrity.py. Branch: `exp/phase2-round3-models-20261014`; no wiring into my_model, other-branch push or force push was performed.

---

<a id="zh"></a>

# Round 3 alternative capacity models — final report

> [English](#en) · 中文

**继续以 V2 为领先研究候选。没有新增模型通过本阶段接纳门。** 六个阶段均完成，包含退出和负面结果，无阶段需要用满时间上限；当前 M4 提交模型未修改。这是**已曝光探索性研究**：代理值此前已看过，是检查后充入量加假设 ε，不是隐藏 C/20 真值。

Δ=0.4 下复现 V2：MAE **0.215726 pp**，MAX **0.669052 pp**；M4 MAE 为 0.291265 pp。V2 参考候选类在 Python 3.11.14 下通过未来噪声、仅 CK1 前缀 fit 的精确一致性、序列化和 sample_data 冒烟检查，与研究实现最大差异 1.42×10⁻¹⁴ pp。没有新增通过验收的类，也不构建集成。

## 全部候选与变体

数值均为 SOH 百分点。使用主台阶方法及 A4 2 Ah；伪情景 MAE 对应 Δ=0.4。三个指标值依次对应 Δ=0、0.4、0.8。**D3 只有六个有效点**，CK2 无定义，不能与七点模型直接比较。D2 和 SS 变体的 CK2–7 只是子集指标，**不与 ε 无关**。

| Model | n | MAE Δ0 / .4 / .8 | MAX Δ0 / .4 / .8 | RMSE Δ0 / .4 / .8 | CK2–7 MAE Δ.4 | ε independent | PG1 | PG2 | PC5 | PC10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M4 | 7 | 0.347 / 0.291 / 0.285 | 0.669 / 0.669 / 0.669 | 0.406 / 0.345 / 0.341 | 0.304 | yes | 0.251 | 0.207 | 0.325 | 0.340 |
| V2 | 7 | 0.272 / 0.216 / 0.210 | 0.669 / 0.669 / 0.669 | 0.364 / 0.293 / 0.289 | 0.216 | yes | 0.251 | 0.207 | 0.302 | 0.340 |
| D0 | 7 | 0.272 / 0.216 / 0.210 | 0.669 / 0.669 / 0.669 | 0.364 / 0.293 / 0.289 | 0.216 | yes | 0.251 | 0.207 | 0.302 | 0.340 |
| D1 | 7 | 0.380 / 0.324 / 0.318 | 1.427 / 1.427 / 1.427 | 0.599 / 0.559 / 0.557 | 0.342 | yes | 0.386 | 0.337 | 0.428 | 0.687 |
| D2 | 7 | 0.370 / 0.270 / 0.244 | 1.358 / 1.049 / 0.911 | 0.576 / 0.423 / 0.372 | 0.279 | no | 0.412 | 0.350 | 0.365 | 0.473 |
| D3 | 6 | 0.206 / 0.140 / 0.133 | 0.609 / 0.228 / 0.228 | 0.282 / 0.160 / 0.152 | 0.125 | yes | 0.205 | 0.230 | 0.229 | 0.176 |
| V2_reg | 7 | 0.298 / 0.242 / 0.236 | 0.669 / 0.669 / 0.669 | 0.380 / 0.313 / 0.310 | 0.246 | yes | 0.251 | 0.207 | 0.312 | 0.340 |
| V2_reg_dvdq | 7 | 0.330 / 0.274 / 0.268 | 0.669 / 0.669 / 0.669 | 0.403 / 0.340 / 0.337 | 0.284 | yes | 0.251 | 0.207 | 0.319 | 0.340 |
| V2_reg_bottom | 7 | 0.296 / 0.240 / 0.234 | 0.669 / 0.669 / 0.669 | 0.378 / 0.311 / 0.308 | 0.244 | yes | 0.251 | 0.207 | 0.310 | 0.340 |
| SS | 7 | 0.479 / 0.355 / 0.242 | 0.935 / 0.696 / 0.616 | 0.604 / 0.421 / 0.307 | 0.334 | no | 0.136 | 0.225 | 0.336 | 0.353 |
| SS_tau3 | 7 | 0.584 / 0.444 / 0.305 | 1.613 / 0.976 / 0.573 | 0.777 / 0.524 / 0.339 | 0.443 | no | 0.148 | 0.208 | 0.445 | 0.435 |
| SS_tau8 | 7 | 0.352 / 0.243 / 0.228 | 0.749 / 0.696 / 0.643 | 0.444 / 0.340 / 0.310 | 0.235 | no | 0.107 | 0.225 | 0.231 | 0.263 |
| SS_beta1 | 7 | 0.911 / 0.740 / 0.569 | 1.066 / 0.995 / 0.924 | 0.915 / 0.762 / 0.657 | 0.783 | no | 0.393 | 0.665 | 0.743 | 0.539 |
| SS_rw01 | 7 | 0.486 / 0.359 / 0.232 | 0.935 / 0.521 / 0.483 | 0.588 / 0.405 / 0.286 | 0.339 | no | 0.098 | 0.141 | 0.355 | 0.399 |
| SS_rw04 | 7 | 0.553 / 0.410 / 0.266 | 0.935 / 0.810 / 0.714 | 0.650 / 0.470 / 0.357 | 0.398 | no | 0.238 | 0.348 | 0.404 | 0.344 |

完整精度、有效样本数、全部台阶/A4 设置和情景见 [总预测表](stage_F/outputs/independent_all_predictions.csv) 与 [总指标表](stage_F/outputs/independent_main_metrics.csv)。这里 Δ 表示代理偏置；SS 中 δ 表示拟合温度偏移。

## Δ=0.4 的逐检查点误差

| Model | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M4 | 0.217 | 0.669 | 0.080 | 0.279 | -0.111 | -0.402 | -0.281 |
| V2 | 0.217 | 0.669 | 0.080 | 0.228 | 0.150 | -0.163 | -0.004 |
| D0 | 0.217 | 0.669 | 0.080 | 0.228 | 0.150 | -0.163 | -0.004 |
| D1 | 0.217 | -1.427 | 0.080 | 0.228 | 0.150 | -0.163 | -0.004 |
| D2 | 0.217 | -1.049 | 0.080 | 0.228 | 0.150 | -0.163 | -0.004 |
| D3 | 0.217 | unavailable | 0.080 | 0.228 | 0.150 | -0.163 | -0.004 |
| V2_reg | 0.217 | 0.669 | 0.080 | 0.353 | 0.219 | -0.103 | 0.051 |
| V2_reg_dvdq | 0.217 | 0.669 | 0.080 | 0.431 | 0.314 | 0.066 | 0.145 |
| V2_reg_bottom | 0.217 | 0.669 | 0.080 | 0.343 | 0.212 | -0.111 | 0.047 |
| SS | 0.481 | 0.501 | -0.044 | 0.696 | 0.463 | -0.070 | -0.232 |
| SS_tau3 | 0.450 | 0.976 | -0.143 | 0.670 | 0.431 | -0.138 | -0.301 |
| SS_tau8 | 0.290 | 0.041 | 0.052 | 0.696 | 0.459 | -0.004 | -0.158 |
| SS_beta1 | 0.481 | 0.501 | 0.675 | 0.831 | 0.995 | 0.785 | 0.911 |
| SS_rw01 | 0.481 | 0.501 | -0.516 | 0.521 | 0.337 | -0.064 | -0.095 |
| SS_rw04 | 0.481 | 0.501 | 0.125 | 0.810 | 0.528 | -0.107 | -0.315 |

## 接纳决定

| Stage/main | Decision | G-proxy | G-epsfree | G-robust | G-regress |
| --- | --- | --- | --- | --- | --- |
| B | diagnostic-only exit | not applicable | not applicable | not applicable | not applicable |
| D0 selected | no CK2 or PG improvement | fail | fail | 0/6 | pass |
| V2_reg | rejected | fail | fail | 0/6 | pass |
| SS | rejected | fail | not ε-free; threshold fails | 0/6 | fail |
| E | unscored sensitivity; inconclusive | not scored | not scored | not applicable | not applicable |
| F | only V2 eligible; no ensemble | not applicable | not applicable | not applicable | not applicable |

**V2 参考类独立通过 G-causal/G-impl**。新增研究模型先已不满足必要性能门，因此拒绝，不生成提交类；其类级因果/实现门是**未运行**，不虚报为通过或失败。后补诊断变体不替代预登记主结果。

## 各阶段结果

**B——仅诊断退出。** 41 次 CV 结束充电中，只有八次检查后锚点跨越 ≥45 Ah；周期性 CCCV 只覆盖约 21 Ah，未穿过石墨台阶。七个月中没有一个月具备两次可用 45℃ 充电侧事件，C 不增加该通道。[报告](stage_B/REPORT.md)。

**D——保留 D0。** PG1+PG2 MAE：D0 0.229，D1 0.361，D2 0.381 pp；D3 为 0.217，但 CK2 无定义，不可选。选择在 816a21d 提交，随后才运行实际数据评估，未观察到对 CK2 调参。不过 PC5/PC10 的 CK2 前缀与实际 CK2 完全相同，已在该提交前评估，因此违反了严格的 CK2 结果顺序要求。D1/D2 让 CK2 误差变为 −1.427/−1.049 pp，V2 是 +0.669。本轮否定这些已测试规则，**不证明误差存在无法降低的下限**。留一锚点观测 MAE：D0 0.336，D1 0.514，D2 0.466，D3 0.301（D3 不含 CK2）。[报告](stage_D/REPORT.md)。

**A——配准 β 不通过。** 主 MAE 0.242 pp，六种台阶变体零胜。原缩放剖面给出底部/顶部可辨识比例 60%/85%，但电压干扰未限定范围且未做剖面。补充的有界干扰审计给出底部/顶部/电压比例 40%/80%/20%，不能恢复主 β 的资格。现已补齐 CK0/首个25℃双参考、1/2/3 Ah 导数特征及三个参数的剖面，各补充在自己的计算前单独登记。起点电压和底部变化的 r=−0.975 提示混淆，不唯一证明 LAM 或其不存在。Q_fc 残差的小样本 r≈0.04 既不能排除起点效应，也不能验证代理容量。[主报告](stage_A/REPORT.md)、[模板](stage_A/TEMPLATE_REPORT.md)、[剖面](stage_A/BOUNDED_PROFILE_REPORT.md)。

**C——融合不通过。** 主 MAE 0.355 pp，Δ=0.4 的 CK2–7 MAE 0.334，且有误差回归超过 0.30 pp。τ=8 的 0.243 pp 仍差于 V2，且只是变体。拟合温度/瞬态与已有观察相符，不是独立机制验证。已补齐所有月份的速率、瞬态幅度和伪情景区间描述；实际七点只有 5/7 落在 2 SD 内，曝光且相关的样本不能建立区间校准。CK2–7 在三个 ε 假设下的误差跨度：D2 0.447 pp、SS 0.868 pp，因此两者不是 ε 无关指标。元数据补充与 648 条原预测完全一致，差异 0 Ah。[报告](stage_C/REPORT.md)、[状态](stage_C/outputs/C_independent_monthly_states.csv)、[区间描述](stage_C/outputs/C_independent_calibration.csv)。

**E——ε 仍未验证。** 已按要求把因果可见的逐芯充电映射/A4 回退映射应用于 CK0 带载曲线，四芯求和并求首次 11.2 V 根。只使用检查点前的可见锚点。在登记的 0.1 Ah 尾段外延范围内，105 个首根中可找到 90 个；有限首根的最大 |ε−ε0| 为 0.022651 pp。十五个不可用首根意味着整体**无定论**，不能判定可忽略。原始四芯和末端 11.203 V，外延后的基准首根为 100.416854 Ah。未重复加入绝对 IR/极化，也未把充电特有电压偏置移植到放电。原 S0/S1/S2 是独立机制压力情景：旧 S1 给出 0.26–0.51 pp，但插值末端任意跳变 −1 V，不能当作已验证连续组端首根或严格风险上界。登记的排行榜限定 V2_S1 仍是未经资格验证的诊断选项，不推荐，也不声称改善代理分数。[因果映射报告](stage_E/REQUIRED_MAPPING_REPORT.md)、[旧情景](stage_E/REPORT.md)。

**F——不构建集成。** 只有 V2 符合成员条件，单成员没有可定义的成员间相关系数，不满足固定权重集成报告条件。[报告](stage_F/REPORT.md)。

## 流程偏差与局限

- 准备后发现并发执行；已保留原 harness 接口及完成提交，补充输出现已整合提交。
- D2 在 CK2 前看不到缺段后的计数器跳变，使用可见 45℃ 历史估吞吐量；其台阶观测另使用 β=1，而非要求的 β 换算。负面结论针对该实现，不等于精确检验原 D2 公式。
- 首轮主评估缺少 A 双参考、有界电压剖面及 E 规定的映射；后补项目各在计算前冻结单独协议。它们晚于主评估，不能称作原预登记，也不能用来挑选替代主模型。
- 主配置及阶段 D 选择保持原样。1/3 Ah A4 敏感性作为独立诊断变体报告；A 缓存键包含参考特征坐标，避免跨平滑窗口误用拟合。
- 代理已曝光；伪截断/缺口增加情景数，不增加独立电池组或隐藏标签。相关性不能证明物理因果或容量标签正确。
- ε、满充起点、检查后回弹、25/45℃ 迁移、端点外延和单电池组仍是实际局限；独立同协议容量测量可以核验，本轮不能推断隐藏 CK1–CK7 真值。

## 精确复现

在指定 worktree 运行。`-B` 避免向复用目录写入字节码。复现是重跑冻结分析和报告，不能重建历史预登记/选择的时间顺序。环境版本记录在 stage_0/outputs/*environment.json；cache 被 git 忽略。

```bash
cd /Users/shane/Desktop/Arena_1013_model/research/phase2_round3_models_20261014
python3 -B stage0_reproduce.py
python3 -B stage_B/audit_coverage.py
python3 -B stage_D/run_select.py
python3 -B stage_D/run_eval.py
python3 -B stage_D/run_independent_robustness.py
python3 -B stage_A/run_a.py
python3 -B stage_A/explore_start_state.py
python3 -B stage_A/run_independent_smoothing.py
python3 -B stage_A/run_templates.py
python3 -B stage_A/run_bounded_profiles.py
python3 -B stage_C/run_c.py
python3 -B stage_C/run_independent_diagnostics.py
python3 -B stage_E/run_e.py
python3 -B stage_E/run_required_mapping.py
python3 -B stage_F/run_independent_summary.py
python3 -B stage_F/write_final_report.py
python3 -B stage_0/audit_integrity.py
```

```bash
/opt/homebrew/bin/python3.11 -m venv /tmp/arena-round3-py311
/tmp/arena-round3-py311/bin/pip install numpy==2.4.6 pandas==3.0.6
/tmp/arena-round3-py311/bin/python -B stage_0/validate_candidate.py \
  candidate_model/v2_reference_model.py stage_0/outputs/predictions.csv V2 \
  --output stage_0/outputs/v2_independent_candidate_check.json
```

相对 24728fa，受保护的已跟踪目录未变。stage_0/audit_integrity.py 检查协议哈希、双语锚点及候选依赖。分支为 `exp/phase2-round3-models-20261014`，未接入 my_model、推送其他分支或强制推送。
