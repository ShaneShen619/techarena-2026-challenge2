# Status

| WP | State | Result |
|---|---|---|
| WP0 | done | SUB reproduced (CK7 90.765); EPS_EXTRA: CK3–7 0.9804 pp/Ah, CK2 1.4465 (√t branch), CK1 flat; 41 CV events (8 A); 35 facts: 23 confirmed, 6 corrected, 2 cited, 3 deferred, 1 recorded; AT pairs of anchors 3 and 7 contain recording gaps |
| WP1 | done | protocol v1 registered in b3f3e7a (sha256 88194bec… in `wp1/protocol.sha256`); `src/locators.py` + `src/ahchain.py`; synthetic tests 15/15 (step ≤ 0.002 Ah clean, Ah offsets at float precision); 1 mV quantisation limits dV/dQ variants (synthetic, reported) |
| WP2 | done | G_SB failed (anchors 5 −0.52, 7 +0.40 > 0.264; σ_LOO 0.13) → H_SB rejected for 5, 7; G_a3 identified (a3_rel +0.305 Ah, 4/5); a0 +3.37 [1.74, 4.72] not identified (h does not transfer 25→45 °C; exploratory h1_0 gives a0 ≈ −0.3…−0.5) |
| WP3 | not started | |
| WP4 | not started | |
| FINAL | not started | |

- Done: WP0.1–WP0.5 (worktree, notes, sources, SUB + sensitivity, events, FACTS, REPORT)
- Done: WP1.1–WP1.4 (protocol.json + sha256, registered modules, synthetic tests, REPORT with outcome table)
- Done: WP2 B1 `wp2/start_audit.csv`: anchors 1, 2, 4–7 relaxed (≤ 5.5 mV/h); anchor 0 (+84 mV/h, cooling −0.89 K/h) and anchor 3 (+53 mV/h) not
- Done: WP2 B2 (`bottom_locators.csv`, `b2_results.json`), B3 (`ck0_split.json`, `h_table.csv`), `gates.json`, `wp2_bottom.png`, `REPORT.md`
- Current WP: WP3 (next session)
- Next: WP3 E1 Ah chain (import src/ahchain.py unchanged; check `shasum -a 256 -c wp1/protocol.sha256` first)
- Last commit: 11c8546
