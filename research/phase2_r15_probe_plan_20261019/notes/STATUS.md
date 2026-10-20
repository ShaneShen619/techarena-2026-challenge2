# Status

| WP | State | Result |
|---|---|---|
| WP0 | done | SUB reproduces (CK7 90.765); no leaderboard observations (log missing → template); 3 existing zips = 6525edf / 5cd305c / 21a7a55, all with the template pptx; R12 L3 (G_a3 pass), R13 O3, R14 O3 |
| WP1 | done | registered (protocol sha256 f4cf3da6…); grid = round 6's 18 (R12 L3, R13/R14 O3 not identifiable) + G_r11 gate; eligible: P_A3fix only (P_level L3, P_drift no O2, P_stress_early dropped); tests 7/7 |
| WP2 | done | plan = one probe P_A3fix (rebuild = R12 exactly; readable G_main 17/18, G_r11 24/27; E[Δs] −0.009 all metrics; worst +0.017); upload only if SUB's board value known and next evaluation ≥ 3 d before a known deadline |
| WP3 | done | P_A3fix zip built + validated (validator PASSED, output = expected), SHA256 3d792662…72e6, template pptx (warning); HANDOVER, FINAL_REPORT, README |
| WP4 | waiting | 2026-10-20: waiting for leaderboard (log has header only; the goal's "recorded results" were not found) |

- Current WP: none (WP0–WP3 done; WP4 waiting for leaderboard) — Global Done
- Done: WP0.1 worktree, prompt commit `f0480d8` (pushed), notes, 25 sources; WP0.2 `wp0/RULES.md`; WP0.3 input templates; WP0.4 `wp0/existing_packages.csv`, `wp0/SUB_SOH.csv`; WP0.5 `wp0/candidates.md`; `wp0/REPORT.md`
- Done: WP1 `wp1/protocol.json` + `protocol.sha256` (protocol + registered code `src/grid15.py`, `src/variants.py`, `src/test_wp1.py`), `wp1/test_wp1.json` 7/7, `wp1/REPORT.md`
- Done: WP2 `probe_soh.csv`, `delta_s_long.csv`, `ranking.csv`, `selection.json`, `predicted_scores.csv`, `PROBE_PLAN.md`, `ORGANIZER_QUESTION.md`, `REPORT.md`
- Done: WP3 `src/wp3_stage.py`, `src/package_submission.py` (3 changes), `src/wp3_packages.py`; `wp3/staging.json`, `packages.csv`, `build_log_P_A3fix.txt`, `HANDOVER.md`, `REPORT.md`; `FINAL_REPORT.md`, `README.md`
- Done: WP4 run 2026-10-20 (`src/wp4_run.py`, `wp4/run_2026-10-20.json`, `wp4/processed_rows.json`, `wp4/REPORT.md`): waiting for leaderboard
- Next: user logs a board evaluation in `inputs/leaderboard_log.csv`, then rerun WP4
- Push policy: all study commits pushed to origin (D26, supersedes D4); zips git-ignored, never uploaded
- Last commit: see `git log -1`
