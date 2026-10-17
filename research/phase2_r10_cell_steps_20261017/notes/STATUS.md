<a id="en"></a>

# STATUS (round 10)

> **Language:** English · [中文](#zh)

| WP | State | Result |
|---|---|---|
| WP0 | done | SUB, round 9 P2a and the variant table reproduced; submitted class = research = EXPECTED_SOH; σ_det main 0.090 Ah |
| WP1 | done | A3 (median over variants, then median over cells) passes all gates: causal 0.157→0.147, LOVO 6/6, real MAE 0.126→0.120; A1/A2 fail |
| WP2 | done | B3 (rejection on A3 locations) passes but never rejects: equals A3 locations with mean of changes, weaker than A3 (causal 0.1515 vs 0.1470); B1/B2 fail; no single-cell monthly jumps |
| WP3 | exited | WP3a: neither CV-end voltage (R² 0.00002) nor anchor step→top (R² 0.065) explains per-cell drift; divergence is cell1 ageing faster (−0.18→−0.51 Ah) |
| WP4 | done | final = A3 (combination = B3 by construction, causal 0.1515 > A3 0.1470); class = research to 1.4e-14 pp, causal checks and Python 3.11 package check pass; not wired |
| WP5 | done | FINAL_REPORT, README; recommendation: A3 optional low-risk upgrade (wiring is the user's decision) |

Next: all WPs done. Last commit: see git log.

---

<a id="zh"></a>

# 状态（第 10 轮）

> **语言：** [English](#en) · 中文

| WP | 状态 | 结果 |
|---|---|---|
| WP0 | 完成 | SUB、第 9 轮 P2a 和变体表均已复现；提交类 = 研究实现 = EXPECTED_SOH；主变体 σ_det 0.090 Ah |
| WP1 | 完成 | A3（变体中位数再取单体中位数）通过全部检验：因果 0.157→0.147，留一变体 6/6，真实 MAE 0.126→0.120；A1/A2 未通过 |
| WP2 | 完成 | B3（在 A3 位置上做剔除）通过但从未剔除：等于 A3 位置加变化量平均，弱于 A3（因果 0.1515 对 0.1470）；B1/B2 未通过；不存在单月单体跳变 |
| WP3 | 退出 | WP3a：CV 结束电压（R² 0.00002）和锚点台阶→顶部距离（R² 0.065）都解释不了单体漂移；拉开来自单体 1 老化更快（−0.18→−0.51 Ah） |
| WP4 | 完成 | 最终候选 = A3（组合在构造上等于 B3，因果 0.1515 > A3 0.1470）；模型类与研究实现相差 1.4e-14 pp，因果检查和 Python 3.11 提交包检查通过；未接入 |
| WP5 | 完成 | FINAL_REPORT、README；建议：A3 为可选的低风险升级（是否接入由用户决定） |

下一步：所有 WP 已完成。最近一次提交见 git log。
