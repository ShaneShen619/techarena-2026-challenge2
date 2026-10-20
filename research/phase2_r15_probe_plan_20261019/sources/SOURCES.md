# Sources

Copied 2026-10-20 08:28 by `src/wp0_sources.py` after `git -C /Users/shane/Desktop/Arena_1013_model fetch origin`. Read-only copies; the originals are not modified. *required* = listed by the prompt; *support* = needed to build round 6's T_k(h) exactly or to check a rebuild.

| copy (under `sources/`) | ref | commit | path at ref | role | required | SHA256 |
|---|---|---|---|---|---|---|
| `r6/wp1_protocol.json` | `origin/exp/phase2-r6-robust-20261016` | `e144086` | `research/phase2_r6_robust_20261016/wp1/protocol.json` | 18-hypothesis grid h = (Delta, f, d), score s | yes | `cbbb0dc419da26b202bd6ae206273f6ddc0341c810c89262a8592861914e7bdf` |
| `r6/wp1_run_wp1.py` | `origin/exp/phase2-r6-robust-20261016` | `e144086` | `research/phase2_r6_robust_20261016/wp1/run_wp1.py` | T_k(h), s, prior weights | yes | `1be612a9a7ce67d78a9ae79e1550ffccf22c92d99cfdc36dc2de0c69d821ee1c` |
| `r6/wp6_run_wp6.py` | `origin/exp/phase2-r6-robust-20261016` | `e144086` | `research/phase2_r6_robust_20261016/wp6/run_wp6.py` | probe delta-s machinery | yes | `442bf5f5c4f5e49510d51ab0ba15272c5613498104563e86a8ab051f96fdbb49` |
| `r6/wp6_REPORT.md` | `origin/exp/phase2-r6-robust-20261016` | `e144086` | `research/phase2_r6_robust_20261016/wp6/REPORT.md` | old probe plan | yes | `190d157cfba19b272618a333801b2accf7f7af15999187454e70db80e8c5814b` |
| `r6/wp6_probe_plan.json` | `origin/exp/phase2-r6-robust-20261016` | `e144086` | `research/phase2_r6_robust_20261016/wp6/outputs/wp6_probe_plan.json` | old probe vectors (older SUB 21a7a55) | yes | `8665591db6faf758cf2470000a4a9523bd7c7a7b21703255684752ab91cedb33` |
| `r6/wp1_predictions.csv` | `origin/exp/phase2-r6-robust-20261016` | `e144086` | `research/phase2_r6_robust_20261016/wp1/outputs/wp1_predictions.csv` | proxy column = Q_fc,k + eps0 + Delta (harness) | support | `3562b3125e2b0aa38580b6e6c577f60366dc01cf470fd3082801c3f5506fd72f` |
| `r6/wp1_scores_long.csv` | `origin/exp/phase2-r6-robust-20261016` | `e144086` | `research/phase2_r6_robust_20261016/wp1/outputs/wp1_scores_long.csv` | reproduction check of s | support | `ab3c3cf11798f41068ed07c1e8ed50849b633cb80f27be9e00ca137fb5deb9a1` |
| `r6/wp6_delta_s_vs_SUB_by_h.csv` | `origin/exp/phase2-r6-robust-20261016` | `e144086` | `research/phase2_r6_robust_20261016/wp6/outputs/wp6_delta_s_vs_SUB_by_h.csv` | reproduction check of delta-s | support | `42b12e8ffa035fbacd73a52882a80baf307ccef026ca940ef363de15379c5846` |
| `r6/wp3_run_wp3.py` | `origin/exp/phase2-r6-robust-20261016` | `e144086` | `research/phase2_r6_robust_20261016/wp3/run_wp3.py` | 3b eps-drift transform (P_drift) | support | `9ad4fc2c0a219f895cf3f91261ee0112a383a564f444b48b5c6a05826d7fe419` |
| `r6/wp2_run_wp2.py` | `origin/exp/phase2-r6-robust-20261016` | `e144086` | `research/phase2_r6_robust_20261016/wp2/run_wp2.py` | F1_S_B fusion (P_stress_early rebuild check) | support | `b00f681d2dcf66c02413f6683c09b14236539bf3ba70ba27bc92705cd2982d42` |
| `r6/wp2_selection.json` | `origin/exp/phase2-r6-robust-20261016` | `e144086` | `research/phase2_r6_robust_20261016/wp2/outputs/wp2_selection.json` | F1 fusion parameters sigma_SUB, sigma_S0 | support | `11bda2ce838f744940f2d843023a6df974ca5ef63c18006557d6d3f6d26b2e07` |
| `r6/round3_harness.py` | `origin/exp/phase2-r6-robust-20261016` | `e144086` | `research/phase2_round3_models_20261014/src/harness.py` | QFC, EPS0 definition (round 3 harness, as imported by round 6) | support | `e401c384732ff29da04d3869ac5d3f74c201b6eb84c7a8f6fda1e4f09d3c5f42` |
| `r6/round4_jumps.csv` | `origin/exp/phase2-r6-robust-20261016` | `e144086` | `research/phase2_round4_signals_20261014/stage_5/outputs/jumps.csv` | R_k = recovery_Ah_with_aging | support | `38237af5b62a4e8a774b1c3b5c50c9bcd60e2767c8e2e26cbfeddad8dc05c21d` |
| `r11/drift.py` | `origin/exp/phase2-r11-eps-transfer-20261018` | `ff45b48` | `research/phase2_r11_eps_transfer_20261018/src/drift.py` | round 11 drift model | yes | `0ad5a9d38152f0fb0c8fb8d762d8090a506ad4153c86caf4a0443f42df5588fe` |
| `r11/wp5_decision.json` | `origin/exp/phase2-r11-eps-transfer-20261018` | `ff45b48` | `research/phase2_r11_eps_transfer_20261018/wp5/decision.json` | round 11 d interval [-0.036, +0.052] | yes | `8edb3d3c5f44d6f04723de6a8487e497c7e85524f66ef3d4610dab4471a100d0` |
| `r12/wp4_budget_decision.json` | `origin/exp/phase2-r12-eps-level-20261019` | `a6994c7` | `research/phase2_r12_eps_level_20261019/wp4/budget_decision.json` | round 12 decision (L1/L2/L3, G_a3) | yes | `d9642566f657be2a850cd0e43fac45e0704b129dc56074193b4014d8308b2897` |
| `r12/wp4_SOH_variants.csv` | `origin/exp/phase2-r12-eps-level-20261019` | `a6994c7` | `research/phase2_r12_eps_level_20261019/wp4/SOH_variants.csv` | round 12 SOH variants | yes | `2de32cfb20c3d9fec008a7646bdc45c3a71b6bbb2620685d923d930ebeff5a9b` |
| `r12/wp4_R13_HANDOFF.json` | `origin/exp/phase2-r12-eps-level-20261019` | `a6994c7` | `research/phase2_r12_eps_level_20261019/wp4/R13_HANDOFF.json` | round 12 hand-off | yes | `9a5340522e5e5fdf8614161b29fdad7ec3c2d001d97f42895371f00c42a6aed4` |
| `r12/wp4_REPORT.md` | `origin/exp/phase2-r12-eps-level-20261019` | `a6994c7` | `research/phase2_r12_eps_level_20261019/wp4/REPORT.md` | round 12 WP4 report | yes | `dad30723bb7c406baa64ce1200744fec2d9128dd9f93c7716e7d706ff67a8926` |
| `r12/wp4_run.py` | `origin/exp/phase2-r12-eps-level-20261019` | `a6994c7` | `research/phase2_r12_eps_level_20261019/src/wp4_run.py` | registered SUB_A3fix hook (a3fix_variant) | support | `46793dadb0e61d0d7bfd95212850c97b8cc6adc8d2765953580cbe9f332ae8ec` |
| `r13/wp3_R13_RESULT.json` | `origin/exp/phase2-r13-top-tail-20261019` | `fb50d07` | `research/phase2_r13_top_tail_20261019/wp3/R13_RESULT.json` | round 13 outcome | yes | `58b97b6c2883b13533bfd20b569a4ebcbb6ddea61a1f0d4a6eb7040875a995a8` |
| `r13/wp3_SOH_variants.csv` | `origin/exp/phase2-r13-top-tail-20261019` | `fb50d07` | `research/phase2_r13_top_tail_20261019/wp3/SOH_variants.csv` | round 13 SOH variants | yes | `eb76bce5b84fbd19f3945ac7777311733068fa2cd5c6a89d848dd3a160ff1a2f` |
| `r14/wp3_R14_RESULT.json` | `origin/exp/phase2-r14-path-drift-20261019` | `643d202` | `research/phase2_r14_path_drift_20261019/wp3/R14_RESULT.json` | round 14 outcome | yes | `5e17f4b86d8ca2637064a762bb01d0f9d490332a4af0c82668b50ec3f473d58a` |
| `r14/wp3_SOH_variants.csv` | `origin/exp/phase2-r14-path-drift-20261019` | `643d202` | `research/phase2_r14_path_drift_20261019/wp3/SOH_variants.csv` | round 14 SOH variants | yes | `2fa1f362ffe091de882800741cef7deb2963fca324671e34d451e00420f7efff` |
| `base/package_submission.py` | `worktree (base 6525edf)` | `f0480d8` | `research/phase2_v3_20261015/package_submission.py` | packaging script | yes | `b855deca00aa523db5edd6a3665c4cad5c4d0f97391e989d5354e678326be216` |

## Rounds 12–14 presence

| round | ref | commit | status |
|---|---|---|---|
| 12 | `origin/exp/phase2-r12-eps-level-20261019` | `a6994c7` | present |
| 13 | `origin/exp/phase2-r13-top-tail-20261019` | `fb50d07` | present |
| 14 | `origin/exp/phase2-r14-path-drift-20261019` | `643d202` | present |

## User files (listed and hashed only)

See `wp0/existing_packages.csv`. Zips are extracted only into the git-ignored `cache/existing/`.
