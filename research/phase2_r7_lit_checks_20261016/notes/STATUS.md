<a id="en"></a>

# STATUS (round 7)

> **Language:** English · [中文](#zh)

Branch `exp/phase2-r7-lit-checks-20261016`, worktree `/Users/shane/Desktop/Arena_1016_r7_lit`, base `e144086`.

| WP | State | Result |
|---|---|---|
| 0 setup, re-baselining | done | SUB reproduced (MAE Δ0.4 0.1227, MAX 0.2277, pseudo 0.1476, cold 0.1743), identical to round-6 predictions; round-6 grid max regret of SUB 0.0271 reproduced; 3a/3c reproduced; sqrt_gap fires in 24 non-real cases (5 distinct k = 3..7 outside CK2) |
| 1 overhang state effect | done | not supported: P1 ρ −0.29, P2 −0.18, P3 +0.61 (all opposite); checkups start charged (7/7 > 13 V) → H_ov_before main; SUB keeps lowest max regret (0.034); updated prior favours SUB+drift(−0.031) |
| 2 temperature-weighted sqrt | done | T_main passes all gates (gap cases 0.105 vs 0.113, pseudo 0.144, cold 0.170, G_hyp, G_causal, G_impl) → recommend switching; CK2 94.451 → 94.507; not wired |
| 3 eps drift on Yagci | done | drift sign not robust: Yagci 50 C −0.057, 35 C +0.178 (initial-checkup effect); pooled median −0.033; d stays −0.031; probe P_drift after the others |
| 4 Reichert 2013 | skipped | no full text on Desktop or in papers/ |
| 5 synthesis | pending | |

Next: WP5.

---

<a id="zh"></a>

# 状态（第七轮）

> **语言：** [English](#en) · 中文

见上表。WP0–WP3 已完成，WP4 跳过；下一步 WP5。
