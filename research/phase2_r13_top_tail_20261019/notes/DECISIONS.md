# Decisions

Open points resolved without asking, each with the most conservative option that keeps every rule of `EXECUTION_PROMPT.md`.

| # | WP | Decision | Why |
|---|---|---|---|
| D1 | WP0 | Base = `6525edf`; it is the tip of `exp/phase2-anchor-step-20261013` at start. | Prompt §1. |
| D2 | WP0 | `cache/` (incl. `cache/variants/`) is git-ignored via the study's own `.gitignore`, as in round 11. | Prompt §1 asks for a git-ignored `cache/variants/`; the repo root `.gitignore` is shared, so it is not touched. |
