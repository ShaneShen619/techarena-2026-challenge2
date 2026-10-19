# Status

| WP | State | Result |
|---|---|---|
| WP0 | done | SUB reproduces (CK7 90.765); facts hold (7–8 mV is per cell; o_k raw +0.40…+0.70); A→T1 gaps for anchors 3, 7; T2 only for anchors 5, 6 |
| WP1 | done | registered (protocol sha256 144bbac3…); synthetic 19/19 pass; P1 = anchors 1,2,4,5,6; P1b not estimable → O1/O2 unreachable |
| WP2 | done | P1 d_path −0.118 (E −0.97 Ah), LOO width 0.59 > 0.30; σ_TT,25 gate 0.125; P1b n=2; P2 E −0.28 (cell 3 only); trend explained by month-specific λ (exploratory) |
| WP3 | not started | |
| FINAL | not started | |

- Current WP: WP3
- Done: WP0.1 worktree `/Users/shane/Desktop/Arena_1019_r14_path_drift`, branch `exp/phase2-r14-path-drift-20261019` from base `6525edf`; prompt copied to `EXECUTION_PROMPT.md` (SHA256 `62bffd5b…0e2a`, identical to the original)
- Done: WP0.1 sources copied (12 files; optional R12 `ahchain.py`, R12 `wp3/pairs.csv`, R13 `R13_RESULT.json` not available at 2026-10-19 22:09)
- Done: WP0.2 SUB via package CLI → `wp0/SUB_SOH.csv` (CK7 90.765, = rounds 11/12)
- Done: WP0.3 `wp0/anchor_blocks.csv`; WP0.4 `wp0/FACTS.md`, `wp0/facts.json`, `wp0/REPORT.md`
- Done: WP1 `wp1/protocol.json` + `protocol.sha256`, registered code (`src/ahchain.py`, `signals.py`, `stats14.py`, `decide.py`, `data14.py`), synthetic test 19/19, `wp1/REPORT.md`
- Done: WP2 tables (`pairs`, `lambda`, `term3`, `p2_voltage`, `p3_memory`, `events`), `stats.json`, R12 ahchain cross-check (27/27 identical), exploratory λ analysis, figures 1–3, `wp2/REPORT.md`
- Next: WP3 decision (re-check R13 `R13_RESULT.json` on origin first), SOH variants, R14_RESULT.json, reports
- Last commit: 46f3c26 (WP1 registration); WP2 commit follows
