# Status

| WP | State | Result |
|---|---|---|
| WP0 | done | SUB reproduced (CK7 90.765); EPS_EXTRA: CK3–7 0.9804 pp/Ah, CK2 1.4465 (√t branch), CK1 flat; 41 CV events (8 A); 35 facts: 23 confirmed, 6 corrected, 2 cited, 3 deferred, 1 recorded; AT pairs of anchors 3 and 7 contain recording gaps |
| WP1 | done | protocol v1 registered in b3f3e7a (sha256 88194bec… in `wp1/protocol.sha256`); `src/locators.py` + `src/ahchain.py`; synthetic tests 15/15 (step ≤ 0.002 Ah clean, Ah offsets at float precision); 1 mV quantisation limits dV/dQ variants (synthetic, reported) |
| WP2 | not started | |
| WP3 | not started | |
| WP4 | not started | |
| FINAL | not started | |

- Current WP: WP2 (next session; WP2 and WP3 depend only on WP1)
- Done: WP0.1–WP0.5 (worktree, notes, sources, SUB + sensitivity, events, FACTS, REPORT)
- Done: WP1.1–WP1.4 (protocol.json + sha256, registered modules, synthetic tests, REPORT with outcome table)
- Next: WP2 B1 start audit (import src/locators.py and src/ahchain.py unchanged; check `shasum -a 256 -c wp1/protocol.sha256` first)
- Last commit: b3f3e7a
