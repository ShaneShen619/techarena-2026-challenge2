# Status

| WP | State | Result |
|---|---|---|
| WP0 | done | SUB reproduces (CK7 90.765); no leaderboard observations (log missing → template); 3 existing zips = 6525edf / 5cd305c / 21a7a55, all with the template pptx; R12 L3 (G_a3 pass), R13 O3, R14 O3 |
| WP1 | done | registered (protocol sha256 f4cf3da6…); grid = round 6's 18 (R12 L3, R13/R14 O3 not identifiable) + G_r11 gate; eligible: P_A3fix only (P_level L3, P_drift no O2, P_stress_early dropped); tests 7/7 |
| WP2 | next | — |
| WP3 | open | — |
| WP4 | open | — |

- Current WP: WP2
- Done: WP0.1 worktree, prompt commit `f0480d8` (pushed), notes, 25 sources; WP0.2 `wp0/RULES.md`; WP0.3 input templates; WP0.4 `wp0/existing_packages.csv`, `wp0/SUB_SOH.csv`; WP0.5 `wp0/candidates.md`; `wp0/REPORT.md`
- Done: WP1 `wp1/protocol.json` + `protocol.sha256` (protocol + registered code `src/grid15.py`, `src/variants.py`, `src/test_wp1.py`), `wp1/test_wp1.json` 7/7, `wp1/REPORT.md`
- Next: WP2 (rebuild P_A3fix + EX via CLI, Δs tables, ranking, PROBE_PLAN, ORGANIZER_QUESTION)
- Push policy: local commits only after `f0480d8` (D4)
- Last commit: see `git log -1`
