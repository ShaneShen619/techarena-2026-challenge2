<a id="en"></a>

# WP0 — Rounds 12–14 and candidate SOH vectors

> **Language:** English · [中文](#zh)

## Conclusions

- **All three rounds are present on origin and complete.** None of them changed the submission.
- **Round 12: L3** (keep SUB). The ε-level interval is far too wide (4.48 [2.35, 6.34] Ah). G_a3 passed (a_3^rel = +0.305 Ah, 4 of 5 locators agree), so the leaderboard-only candidate **SUB_A3fix** exists.
- **Round 13: O3, "not identifiable"** (envelope 0.41 Ah > 0.30 Ah). d_tail median +0.0131, range [0, +0.0502] Ah/Ah.
- **Round 14: O3, "not identifiable"** (LOO width of E 0.59 Ah > 0.30 Ah). d_path median −0.118, LOO [−0.167, −0.095]; reported d_top −0.105 [−0.167, −0.045].
- **Round 11** (for reference): O3, d ∈ [−0.036, +0.052].
- Consequence for WP1 (applied there by the registered rules): the Δ axis stays {0, 0.4, 0.8}; P_level is not eligible (needs L2); P_A3fix is eligible (G_a3 passed); P_drift needs an O2 that neither round reached.

## Presence

| Round | Ref | Commit | Outcome | Files copied |
|---|---|---|---|---|
| 12 | `origin/exp/phase2-r12-eps-level-20261019` | `a6994c7` | **L3** (keep SUB); G_SB failed; G_a3 identified | `wp4/budget_decision.json`, `SOH_variants.csv`, `R13_HANDOFF.json`, `REPORT.md`; `src/wp4_run.py` |
| 13 | `origin/exp/phase2-r13-top-tail-20261019` | `fb50d07` | **O3** not identifiable | `wp3/R13_RESULT.json`, `SOH_variants.csv` |
| 14 | `origin/exp/phase2-r14-path-drift-20261019` | `643d202` | **O3** not identifiable | `wp3/R14_RESULT.json`, `SOH_variants.csv` |
| 11 | `origin/exp/phase2-r11-eps-transfer-20261018` | `ff45b48` | O3, d ∈ [−0.036, +0.052] | `src/drift.py`, `wp5/decision.json` |

## Candidate SOH vectors (%, CK1..CK7)

All are leaderboard-only research copies built by their own rounds on SUB `6525edf`; none has been scored against proxies.

| Source | Variant | Changed scalar | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|---|---|
| base | **SUB** (A3, re-verified through the CLI) | — | 95.984 | 94.507 | 93.600 | 92.821 | 92.015 | 91.426 | 90.765 |
| R12 | SUB_A3fix | anchor-3 Q_fc − 0.3047 Ah | 95.984 | 94.507 | 93.600 | 92.461 | 91.987 | 91.410 | 90.750 |
| R12 | SUB_eps_point | EPS_EXTRA_AH = 4.483 | 95.984 | 100.413 | 97.603 | 96.824 | 96.018 | 95.429 | 94.768 |
| R12 | SUB_eps_lo | EPS_EXTRA_AH = 2.347 | 95.984 | 97.324 | 95.509 | 94.730 | 93.924 | 93.335 | 92.674 |
| R12 | SUB_eps_hi | EPS_EXTRA_AH = 6.338 | 95.984 | 103.096 | 99.422 | 98.642 | 97.837 | 97.248 | 96.587 |
| R13 | SUB + d_tail median | d = +0.0131 | 96.016 | 94.559 | 93.664 | 92.895 | 92.099 | 91.518 | 90.866 |
| R13 | SUB + d_tail max | d = +0.0502 | 96.107 | 94.704 | 93.843 | 93.103 | 92.338 | 91.778 | 91.150 |
| R14 | SUB + d_path median | d = −0.1179 | 95.694 | 94.043 | 93.029 | 92.158 | 91.257 | 90.599 | 89.860 |
| R14 | SUB + d_top median | d = −0.1048 | 95.727 | 94.095 | 93.093 | 92.232 | 91.342 | 90.691 | 89.961 |
| R14 | SUB + d_top high | d = −0.0451 | 95.873 | 94.330 | 93.382 | 92.568 | 91.725 | 91.110 | 90.419 |
| R14 | SUB + d_top low | d = −0.1670 | 95.574 | 93.850 | 92.792 | 91.883 | 90.942 | 90.255 | 89.483 |

Round 6's probe vectors (P_drift, P_stress_early, P_start) were built on the older SUB `21a7a55` and are not candidates until rebuilt (WP1/WP2). The R12 ε variants put CK2 above CK0 (an artefact, per round 12). R13's `SUB + d_min` is identical to SUB (its C1 member has zero tail drift) and is not listed. Rounds 12–14 label all their variants "not recommended".

---

<a id="zh"></a>

# WP0 — 第 12–14 轮与候选 SOH 向量

> [English](#en) · 中文

## 结论

- **三轮都已在 origin 上且已完成。** 没有一轮改动过提交。
- **第 12 轮：L3**（保留 SUB）。ε 水平区间太宽（4.48 [2.35, 6.34] Ah）。G_a3 通过（a_3^rel = +0.305 Ah，5 个定位器中 4 个一致），所以存在只用于排行榜的候选 **SUB_A3fix**。
- **第 13 轮：O3，"不可识别"**（包络 0.41 Ah > 0.30 Ah）。d_tail 中位数 +0.0131，范围 [0, +0.0502] Ah/Ah。
- **第 14 轮：O3，"不可识别"**（E 的留一宽度 0.59 Ah > 0.30 Ah）。d_path 中位数 −0.118，留一 [−0.167, −0.095]；报告的 d_top −0.105 [−0.167, −0.045]。
- **第 11 轮**（参考）：O3，d ∈ [−0.036, +0.052]。
- 对 WP1 的影响（在 WP1 中按登记规则应用）：Δ 轴保持 {0, 0.4, 0.8}；P_level 不合格（需要 L2）；P_A3fix 合格（G_a3 通过）；P_drift 需要 O2，两轮都没有达到。

## 是否存在

| 轮次 | 引用 | 提交 | 结果 | 复制的文件 |
|---|---|---|---|---|
| 12 | `origin/exp/phase2-r12-eps-level-20261019` | `a6994c7` | **L3**（保留 SUB）；G_SB 未通过；G_a3 可识别 | `wp4/budget_decision.json`、`SOH_variants.csv`、`R13_HANDOFF.json`、`REPORT.md`；`src/wp4_run.py` |
| 13 | `origin/exp/phase2-r13-top-tail-20261019` | `fb50d07` | **O3** 不可识别 | `wp3/R13_RESULT.json`、`SOH_variants.csv` |
| 14 | `origin/exp/phase2-r14-path-drift-20261019` | `643d202` | **O3** 不可识别 | `wp3/R14_RESULT.json`、`SOH_variants.csv` |
| 11 | `origin/exp/phase2-r11-eps-transfer-20261018` | `ff45b48` | O3，d ∈ [−0.036, +0.052] | `src/drift.py`、`wp5/decision.json` |

## 候选 SOH 向量（%，CK1..CK7）

数值见英文部分的表。全部是各轮在 SUB `6525edf` 上构造的、只用于排行榜的研究副本；没有一个对代理标签打过分。第 6 轮的探针向量（P_drift、P_stress_early、P_start）基于旧 SUB `21a7a55`，在重建之前不算候选（WP1/WP2）。第 12 轮的 ε 变体把 CK2 放到 CK0 之上（第 12 轮认定为伪影）。第 13 轮的 `SUB + d_min` 与 SUB 完全相同（其 C1 成员的尾部漂移为零），表中未列出。第 12–14 轮把它们的所有变体都标为"不推荐"。
