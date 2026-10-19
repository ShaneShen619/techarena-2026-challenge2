# Decisions

- D1 (scope): the round 11 handoff (`wp5/R12_HANDOFF.json`) named a top-of-charge drift model as round 12. The user chose to measure the ε **level** on our own pack first (this round); the drift model moves to round 13.
- D2 (WP0): base = `6525edf`. The tip of `exp/phase2-anchor-step-20261013` at the start of the round is `6525edf` itself, so no newer tip was used.
- D3 (WP0): the tool shell of this session starts in `/Users/shane/Desktop/Arena_1013_model` (harness default, reset after every command). Every command therefore `cd`s into this worktree or uses absolute paths / `git -C`; nothing is written outside `/Users/shane/Desktop/Arena_1019_r12_eps_level`.
- D4 (WP0): `cache/` (model variants, CLI outputs) and `__pycache__/` are git-ignored by the study's own `.gitignore`, as in round 11.
