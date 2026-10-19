# Status

Worktree `/Users/shane/Desktop/Arena_1019_r13_top_tail`, branch `exp/phase2-r13-top-tail-20261019`, base `6525edf` (= tip of `exp/phase2-anchor-step-20261013` on 2026-10-19).

| WP | State | Result |
|---|---|---|
| WP0 | done | SUB reproduced (CK7 90.765); 41 full charges catalogued (8 A + 33 T); 4/6 facts hold, CV durations corrected (anchors 438–530 s, top-ups 1.9–4.4 min); cell3 tops all 41 charges |
| WP1 | done | protocol + tail.py + test_tail.py registered before any fit; synthetic tests 0 failures (params ≤ 1.3e-4 rel, Q_tail ≤ 5e-4 Ah) |
| WP2 | done | only M4 admitted on anchors 1–7 (M1/M2/M3 0/7); M4 d·8.2 +0.041…+0.124 Ah; T2 pack main +0.412 Ah (window-fragile: [0.25,1] +0.062); T3 +0.103; M1 I_end·τ 0.465→0.588 Ah, not admitted; top-ups flat |
| WP3 | done (exited by registered rule) | O3 'not identifiable': envelope 0.412 Ah > 0.30 (T2 +0.412 vs C1 0; M4 +0.041…+0.124); SUB unchanged; bound [0, +0.41] Ah at CK7; R13_RESULT.json written |
| FINAL | done | FINAL_REPORT.md + README.md; all WPs done or exited by registered rule |

Next: none — round complete (Global Done).
Last commit: 94f7e45 (WP2); WP3 + final commit follows (see git log).
