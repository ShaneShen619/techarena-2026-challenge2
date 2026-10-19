# Decisions

- D1 (WP0): base = `6525edf`. The tip of `exp/phase2-anchor-step-20261013` at the start of the round (after `git fetch origin`) is `6525edf` itself, so no newer tip was used.
- D2 (WP0): the tool shell of this session starts in `/Users/shane/Desktop/Arena_1013_model` (harness default, reset after every command). Every command therefore `cd`s into this worktree or uses absolute paths / `git -C`; nothing is written outside `/Users/shane/Desktop/Arena_1019_r14_path_drift`.
- D3 (WP0): `cache/` (model variants, CLI outputs) and `__pycache__/` are git-ignored by the study's own `.gitignore`, as in rounds 11 and 12. The repository `.gitignore` is not touched.
- D4 (WP0): optional sources (round 12 `src/ahchain.py` and `wp3/pairs.csv`, round 13 `wp3/R13_RESULT.json`) were not on origin at the WP0 copy (2026-10-19 22:09; R12 tip `50a7373`, R13 tip `0dc5e8f`). They are re-checked (after `git fetch origin`) at the step that would use them: `ahchain.py` at WP1 registration, `pairs.csv` at WP2, `R13_RESULT.json` at WP3. Once WP1 registers an Ah chain, a later round-12 `ahchain.py` does not replace it; it is only used for the WP2 cross-check of `pairs.csv`.
