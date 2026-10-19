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
| D7 | WP1 | d_tail(M, C) = Theil–Sen slope over the usable anchors in k = 1..7 with anchor 1 at (fade 0, Δ 0); this equals the slope of Q_tail on fade. A pair needs anchor 1 usable (it is the reference of Δ_tail) **and** ≥ 5 of anchors 2..7 usable. LOO drops each usable anchor, anchor 1 included. A sensitivity slope without the anchor-1 requirement is reported, not used. | Literal reading of Δ_tail(k) = Q_tail(k) − Q_tail(1); anchor 1's point is real data (fade 0, Δ 0). |
| D8 | WP1 | s_top = −(least-squares slope of V on discharged Ah) over the window, so it is positive in V per Ah of charge content; T2's ΔF = ΔV30/s_top. | Sign convention: a higher relaxed top voltage = more charge in at the top. |
| D9 | WP1 | T3's contribution mirrors T2: Δε_T3 = −ΔF^A_R = +5.1·ΔR/s_top (main window), R = pack sum of round 8's per-cell pulse resistances. | The prompt defines ΔF^A_R but not its Δε sign; mirroring T2 is the only consistent choice. T3 is a check only. |
| D10 | WP1 | The T2 member of A is the pack version, main window [0.5, 2.0] Ah. Per-cell and sensitivity windows are reported only. | Prompt: "plus T2 (main window)"; per-cell versions are listed as "use … report". |
| D11 | WP1 | C1 enters A once (d = 0, LOO [0, 0]), not once per model. | C1 ≡ 0 for every model; counting it four times would only weight the median toward 0. |
| D12 | WP1 | WP3 variants: d_min / d_max = min / max over A (C1 and T2 included); d_median = median over A without C1 (= the O2 definition of d_tail). | The WP3 list says "median"; O2 defines d_tail as the median without C1. |
| D13 | WP1 | "Per-cell voltages under the 20 A pulse after rest" = the first 10 s pulse sample (the step-start row that repeats the rest timestamp is skipped). | That row is an instantaneous step-change record, not a measurement under steady 20 A. |
| D14 | WP1 | Under O3 "not identifiable", WP3 still writes `SOH_variants.csv`, `R13_RESULT.json` and the reports ("exit WP3 after writing the result"), then stops: no further analysis. | WP3's Done list requires those files under every outcome. |
| D15 | WP1 | Admission's "last third of the CV phase" is by time: samples with t ≥ ⅔·t_end. | Sampling is uniform (10 s) except the CV-end row; time and count thirds coincide to one sample. |
