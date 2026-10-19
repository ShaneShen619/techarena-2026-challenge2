# Decisions

Open points resolved without asking, each with the most conservative option that keeps every rule of `EXECUTION_PROMPT.md`.

| # | WP | Decision | Why |
|---|---|---|---|
| D1 | WP0 | Base = `6525edf`; it is the tip of `exp/phase2-anchor-step-20261013` at start. | Prompt §1. |
| D2 | WP0 | `cache/` (incl. `cache/variants/`) is git-ignored via the study's own `.gitignore`, as in round 11. | Prompt §1 asks for a git-ignored `cache/variants/`; the repo root `.gitignore` is shared, so it is not touched. |
| D3 | WP0 | Fact 1 (round 11's CV fit) is verified from round 11's own code and table (`sources/r11_wp4_pack.py`, `r11_wp4_pack_drivers.csv`) plus raw, non-model numbers from the CV window (end current, current 60 s before the end). It is not re-fitted. | WP0 forbids any tail-model fit before WP1's registration. |
| D4 | WP0 | Full charge = a charge step (starts when I rises above 15 A, ends at the first sample with I < 1 A) that has at least one sample with pack ≥ 13.95 V and I < 19.9 A. CV start = that first sample. CV end = the step's last sample (I ≈ 5.1 A). "+30 min" = the last rest sample before the 20 A pulse (lag 1800–1801 s for all 41). | Prompt WP0.3 gives only the CV-start rule; these are the closest data-defined boundaries. |
| D5 | WP0 | `cv_Ah` = trapezoid of I over the CV samples; the cycler-counter difference is kept as `cv_Ah_counter`. | Trapezoid matches the least-squares models' integral; counter as a cross-check. |
| D6 | WP0 | Anchor k = first full charge in segment 1, 2, 4, 6, 8, 10, 12, 14 (round 8/11 convention). The pulse resistance is round 8's `R_pulse_mOhm` per cell, matched on the CV-end timestamp; the pack value is the sum of the four cells. | Prompt WP0.3 asks for round 8's value; the pack sum keeps T3 in pack volts/Ah like s_top. |
