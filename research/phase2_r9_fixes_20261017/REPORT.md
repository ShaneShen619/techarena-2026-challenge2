<a id="en"></a>

# Round 9 (quick) — fixes for round 8 patterns #1 and #2

> **Language:** English · [中文](#zh)

**Result: nothing is wired; SUB stays.** Protocol [protocol.json](protocol.json) was committed in `6a06de6` before any evaluation. Script [run_r9.py](run_r9.py); outputs in [outputs/](outputs/).

| Candidate | Pseudo | Cold | Changed non-real cases (SUB → cand) | Worst case | Real MAE Δ0.4 | Gates |
|---|---|---|---|---|---|---|
| SUB | 0.144 | 0.170 | — | — | 0.126 | — |
| P1a fallback × β | 0.156 | 0.170 | 0.184 → 0.167 (3 cases) | +0.357 (PG2 CK7) | 0.139 | fail |
| P1b fallback × β, skip first program | 0.186 | 0.262 | 0.213 → 0.484 | +0.538 | 0.376 | fail |
| P1c β from phase-matched pairs | 0.145 | 0.170 | 0.221 → 0.227 | +0.071 | 0.145 | fail |
| P1ref prior 1/b (non-causal reference) | 0.159 | 0.253 | 0.217 → 0.271 | +0.368 | 0.222 | reference |
| P2a median of cells | 0.139 | 0.151 | 0.217 → 0.195 (16 cases) | +0.057 | 0.114 | **pass** |
| P2b min of cells | 0.154 | 0.183 | 0.217 → 0.254 | +0.225 | 0.169 | fail |

- **Pattern #1 (step scale).** No causal fix passes. Scaling the fallback increment by β also scales the first-program offset and the 25→45 °C jump that sit in the same difference, so the causal cases get worse (PG2 CK7 −0.04 → −0.39 pp). β from phase-matched pairs (P1c) has too few pairs early.
- **Pattern #2 (cells).** The median passes the four registered gates. A **post-registration robustness check** ([robust_r9.py](robust_r9.py), [outputs/r9_robust_variants.csv](outputs/r9_robust_variants.csv)), added after recalling the V3 result, shows it wins on only 3 of 6 step-detection variants: dvdq_peak real MAE 0.257 → 0.361, pseudo 0.151 → 0.172, cold 0.217 → 0.249. This is the same failure V3 found, so the median is **not adopted**.

---

<a id="zh"></a>

# 第 9 轮（快速）——针对第 8 轮模式 #1、#2 的修正

> **语言：** [English](#en) · 中文

**结论：没有接入任何改动，SUB 保持不变。** 协议 [protocol.json](protocol.json) 在评估之前已提交（`6a06de6`）。
- **模式 #1（台阶比例）：** 没有任何因果修正能通过检验。给 fallback 增量乘 β，会把同一差值里的首个程序偏移和 25→45 °C 跳变一起放大，因果案例因此变差（PG2 CK7 从 −0.04 变为 −0.39 pp）。
- **模式 #2（电芯）：** 中位数通过了 4 项登记检验，但登记后补做的稳健性检查显示，它只在 6 种台阶检测方法中的 3 种上更好，dvdq_peak 明显变差。这与 V3 的结论相同，因此**不采用**。
