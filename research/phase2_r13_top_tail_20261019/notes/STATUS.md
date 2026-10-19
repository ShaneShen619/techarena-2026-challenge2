# Status

Worktree `/Users/shane/Desktop/Arena_1019_r13_top_tail`, branch `exp/phase2-r13-top-tail-20261019`, base `6525edf` (= tip of `exp/phase2-anchor-step-20261013` on 2026-10-19).

| WP | State | Result |
|---|---|---|
| WP0 | done | SUB reproduced (CK7 90.765); 41 full charges catalogued (8 A + 33 T); 4/6 facts hold, CV durations corrected (anchors 438–530 s, top-ups 1.9–4.4 min); cell3 tops all 41 charges |
| WP1 | done | protocol + tail.py + test_tail.py registered before any fit; synthetic tests 0 failures (params ≤ 1.3e-4 rel, Q_tail ≤ 5e-4 Ah) |
| WP2 | pending | |
| WP3 | pending | |
| FINAL | pending | |

Next: WP2 — run registered fits (src/run_wp2.py calling src/tail.py), tables, two figures, report.
Last commit: 5dcb907 (WP0); WP1 registration commit follows.
