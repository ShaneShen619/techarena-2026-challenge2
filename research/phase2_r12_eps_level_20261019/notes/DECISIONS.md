# Decisions

- D1 (scope): the round 11 handoff (`wp5/R12_HANDOFF.json`) named a top-of-charge drift model as round 12. The user chose to measure the ε **level** on our own pack first (this round); the drift model moves to round 13.
- D2 (WP0): base = `6525edf`. The tip of `exp/phase2-anchor-step-20261013` at the start of the round is `6525edf` itself, so no newer tip was used.
- D3 (WP0): the tool shell of this session starts in `/Users/shane/Desktop/Arena_1013_model` (harness default, reset after every command). Every command therefore `cd`s into this worktree or uses absolute paths / `git -C`; nothing is written outside `/Users/shane/Desktop/Arena_1019_r12_eps_level`.
- D4 (WP0): `cache/` (model variants, CLI outputs) and `__pycache__/` are git-ignored by the study's own `.gitignore`, as in round 11.
- D5 (WP0): WP0 produces no evaluation output (only descriptive facts and the SUB reproduction); the registered protocol is WP1's. Common criterion 1 is therefore vacuous for WP0. It binds every WP2/WP3 output, and WP1 commits the protocol before any of them.
- D6 (WP0): §3 WP0 asks to verify every §2 fact *and* forbids any Ah balance, step location or ε-related estimate in WP0. Conservative resolution: facts that need one (anchor 3's extra Ah, the next top-up's +0.1 Ah, the per-block balance) are **deferred** to the registered WP2/WP3 measurement. Step facts already exposed by earlier rounds (first-program offset, 25 → 45 °C step jump) are **cited** from their source, not recomputed. During WP0 a naive "first minus second program" difference was computed from the copied rebound-study output. It was discarded before any commit, because it is not the cited quantity (the cited offset's reference is not stored in the outputs).
- D7 (WP0): event catalogue definitions (`src/wp0_events.py`).
  - A charge is a maximal run of samples with I > 0.5 A (package `CHARGE_I_MIN_A`). It enters the catalogue if its maximum pack voltage is ≥ 13.95 V and its last sample has 0 < I < 6 A.
  - Type A uses the package's `_first_full_charge` conditions: start pack < 12.3 V, charge ≥ 50 Ah, first such charge of the segment. Everything else is type T.
  - CV start: first sample with pack ≥ 13.95 V (main). The sensitivity uses the first sample after that with I < 20 A.
  - Rest means |I| ≤ 0.5 A.
  - "30 min later (just before the pulse)" is the last sample before the first non-rest sample after the CV end. For all 41 events it lies 30.00–30.02 min after the CV end.
  - Counters "at both ends": at the sample before the charge's first sample, and at the CV end.
- D8 (WP0): CK2's checkup window is reported as an upper bound (CK2 date 00:00 → segment 4 start), because the end of segment 3 is not visible.
- D9 (WP0): segment 6 has two in-segment recording gaps (3.65 h, 16.64 h) and segment 14 has one (0.49 h). All three lie inside the AT pairs of anchors 3 and 7, and the counters stay flat across them (the profile paused). WP1 registers WP3's pair rule unchanged (dt > 60 s → excluded, the only exception being the chamber-switch idle with flat counters), with no new exception. Consequences: Term3 has no admissible pair for k = 3 or k = 7, and the main Term3 estimate coincides with the "exclude k = 3" sensitivity.
