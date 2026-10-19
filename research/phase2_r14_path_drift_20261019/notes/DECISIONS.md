# Decisions

- D1 (WP0): base = `6525edf`. The tip of `exp/phase2-anchor-step-20261013` at the start of the round (after `git fetch origin`) is `6525edf` itself, so no newer tip was used.
- D2 (WP0): the tool shell of this session starts in `/Users/shane/Desktop/Arena_1013_model` (harness default, reset after every command). Every command therefore `cd`s into this worktree or uses absolute paths / `git -C`; nothing is written outside `/Users/shane/Desktop/Arena_1019_r14_path_drift`.
- D3 (WP0): `cache/` (model variants, CLI outputs) and `__pycache__/` are git-ignored by the study's own `.gitignore`, as in rounds 11 and 12. The repository `.gitignore` is not touched.
