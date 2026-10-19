# Status

| WP | State | Result |
|---|---|---|
| WP0 | done | SUB reproduced (CK7 90.765); EPS_EXTRA: CK3–7 0.9804 pp/Ah, CK2 1.4465 (√t branch), CK1 flat; 41 CV events (8 A); 35 facts: 23 confirmed, 6 corrected, 2 cited, 3 deferred, 1 recorded; AT pairs of anchors 3 and 7 contain recording gaps |
| WP1 | done | protocol v1 registered in b3f3e7a (sha256 88194bec… in `wp1/protocol.sha256`); `src/locators.py` + `src/ahchain.py`; synthetic tests 15/15 (step ≤ 0.002 Ah clean, Ah offsets at float precision); 1 mV quantisation limits dV/dQ variants (synthetic, reported) |
| WP2 | in progress | B1 done |
| WP3 | not started | |
| WP4 | not started | |
| FINAL | not started | |

- Current WP: WP2
- Done: WP0.1–WP0.5 (worktree, notes, sources, SUB + sensitivity, events, FACTS, REPORT)
- Done: WP1.1–WP1.4 (protocol.json + sha256, registered modules, synthetic tests, REPORT with outcome table)
- Done: WP2 B1 `wp2/start_audit.csv`: anchors 1, 2, 4–7 relaxed (≤ 5.5 mV/h); anchor 0 (+84 mV/h, cooling −0.89 K/h) and anchor 3 (+53 mV/h) not
- Next: WP2 B2 charge-side locators, trend, G_SB, G_a3
- Last commit: 3d3b6f6
