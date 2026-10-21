<a id="en"></a>

# Round 17: Physics Improvements to the r5c Stress Model — Registered Designs, Causal Selection — Execution Prompt

> **Language:** English · [中文](#zh)

Written 2026-10-21. This document is self-contained. The English text is the execution text; the Chinese section is a translation for the reader, and if they differ the English governs.

The work is split into **work packages WP0–WP5**. Run them in order. Each has its own *Done* list and can be run as a separate `/goal`.

## Why this round exists (read first)

The 2026-10-21 analysis of r5c found that its CK2 result comes from two large errors cancelling. At Δ = 0.4 the stress model R3_T alone is at −0.638 pp, V2 alone is at +0.669 pp, and the ensemble REF = 0.75·R3_T + 0.25·V2 is at −0.311 pp. It traced most of R3_T's CK2 over-loss to the break-in term: amplitude ≈ 4.9 Ah, τ_b ≈ 134 d taken from the Challenge 1 prior, and τ_b is not identifiable. CK2 also has no step data, because segment 3 is missing. It then proposed literature-based fixes:
1. a reversible overhang term, or model averaging over τ_b;
2. an SOC-dependent calendar rate;
3. putting the Arrhenius factor on k instead of on time;
4. a reworked or removed cycle term;
5. regime-dependent ensemble weights.

A triage prompt for those ideas (R16, `research/phase2_r16_triage_20261021/R16_EXECUTION_PROMPT.md`) exists but was not run. **On 2026-10-21 the user chose to run this full improvement study instead.** Do not run R16 as well. This round reuses R16's verified facts and implements the proposed designs.

**Exploratory numbers from the 10-21 analysis.** All are exposed (they were computed with the real proxies in view) and were not reproduced. They are context only and **must not select anything**. MAE values are ensemble values in pp; CK2 is the ensemble error.

| Change (10-21, exploratory) | Real | Pseudo | Cold | CK2 |
|---|---|---|---|---|
| REF (r5c as is) | 0.131 | 0.123 | 0.134 | −0.31 |
| Arrhenius on the rate, time weight aT² | 0.127 | 0.161 | 0.127 | +0.15 |
| Schimpe 20.6 kJ/mol on the rate | 0.128 | 0.130 | 0.130 | −0.26 |
| "Checkup" rows get no calendar ageing | 0.143 | 0.119 | 0.122 | −0.34 |
| τ_b = 60 d | 0.117 | 0.182 | 0.152 | +0.08 |
| τ_b = 30 d | 0.152 | 0.147 | 0.166 | +0.48 |

Across τ_b = 30–134 d, R3_T alone moves CK2 from +0.42 to −0.64 pp.

**Premises corrected before this round (checked against the code; build on these, not on the 10-21 wording):**
- **"Checkup" rows are not only checkups.** In r5c `src/stress.py`, `stress_table` gives *every* boundary between consecutive segments a 25 °C `kind="checkup"` row. That includes the 7–25 h idle 25→45 °C chamber switches inside each month. So the 10-21 "no calendar ageing at checkups" test also switched off the chamber switches. Its result is not a test of checkup SOC.
- **Checkup SOC is mixed, not "empty".** The pack enters every checkup charged (13.1–13.3 V, round 7). It leaves empty: the first charge after each checkup starts at 11.5–12.0 V after about 2 h at I = 0. The time spent at each SOC inside a checkup is hidden.
- **The operating load is one 116.1 h block repeated almost identically** (block-to-block current correlation ≥ 0.99 at 25 and 45 °C). The steady SOC window is 11–72 Ah below full. So any SOC weighting of the *operation* time is a near-constant multiplier that A_cal absorbs. SOC weighting can change predictions only through intervals whose SOC differs from operation: chamber switches, checkups, the missing segment and the extrapolated tail. The same argument applies to the cycle term: throughput per operating day is nearly constant at each temperature, so A_cyc is nearly collinear with calendar time.
- **The Arrhenius convention matters less than the 10-21 text says.** The 25 °C clock weight relative to 45 °C is exp(Ea/R·(1/318.15 − 1/298.15)):

  | Convention | Weight |
  |---|---|
  | SUB, 20.6 kJ/mol on time | 0.593 |
  | r5c, 37.3 on time | 0.388 |
  | Schimpe's 20.6 on k (= 41.2 on time) | 0.352 |
  | Yagci's 37.3 read as on k (= 74.6 on time) | 0.151 |

  r5c's clock is already close to the Schimpe convention. The large 10-21 shift (aT²) corresponds to the last row.
- **SUB's clock is half strength.** SUB (`6525edf`) applies 20.6 kJ/mol to time and then takes t^0.5, which is 10.3 kJ/mol on k. In the real scenario its √t gap branch fires only at CK2. This round does not change SUB.
- **The cycle term is not zero.** The prior mean exp(−11.754) still adds a fixed loss.
- **Overhang status.** Round 7 WP1 found the overhang explanation of the *post-anchor step offset* not supported (ρ with dwell and start state had the wrong sign). That tested a different effect. Overhang as the source of the *early calendar nonlinearity* (Lewerenz 2018) has not been tested on this pack. The literature timescale is slow: Lewerenz 2018 reports full compensation after about 150 d at 50 °C, 250 d at 40 °C and 490 d at 30 °C (Ea 64.5 kJ/mol, 25 Ah NMC cells). At 25 °C, lithium flowing back from the overhang during a 1–3-day checkup is therefore expected to be small.
- **"Causal" scenarios are input-causal only.** Pseudo (PG1, PG2, PC5, PC10) and cold-start (CS, CSE) cases are scored against the same exposed proxies as the real scenario (`proxy = H.QFC[k] + H.EPS0 + d` in `runner5c.run`). Margins of 0.003–0.005 pp sit below per-case noise. Selection rules here are therefore paired, blocked by k, and noise-aware.
- **The level problem is bigger and out of scope.** The first leaderboard score (0.1868 for SUB, 2026-10-20) implies a real error of about 0.7–1.0 pp. That error is common-mode and invisible to proxy MAE. This round reports each design's level shift against SUB, but cannot fix the level.

**Rough expectations, written before running.** Report the results against these:
- C changes predictions little; the 41.2 vs 37.3 on-time weight is a 9 % change in the 25 °C clock.
- S moves predictions only through switch, checkup and gap rows. It may move enough to matter, but much less than the 10-21 "checkup" test.
- O2 (overhang) behaves like a break-in term with τ of the order of 50–75 d at 45 °C. Checkup recovery is small. Its CK2 effect is therefore likely between the 10-21 τ_b = 60 d and 134 d rows. The 60 d row had worse pseudo scores.
- D is likely inert (non-inferior).
- "No design beats REF causally" is a valid and likely outcome.

## 0. Mode of work (all work packages)

- **Unattended.** Never stop to ask. When a decision is open, take the most conservative option that keeps every rule here, record it in `notes/DECISIONS.md`, and continue.
- **Restarts.** Keep `notes/STATUS.md` current after every step (WP, done, next, last commit). On restart, read `notes/STATUS.md` and `notes/DECISIONS.md` first and resume. Never redo a finished step.
- **Honesty over targets.** Never tune on the real proxies. This round produces evidence, a recommendation and at most a candidate code copy: **no package change, no zip, no upload, no change to any submission file.**
- **Done for any WP** means:
  1. its registered protocol (`wpN/protocol.json` + `wpN/protocol.sha256`) was committed **before** its outputs (WP0 has none);
  2. its bilingual `wpN/REPORT.md` exists, conclusions first;
  3. `notes/STATUS.md` marks the WP done, capped or exited, with one result line;
  4. every commit is pushed to `origin exp/phase2-r17-r5c-improve-20261021`, and `git status` shows no uncommitted study files.
- **Global Done:** WP0–WP4 each done, capped or exited by a registered rule; WP5 done or skipped by its rule; `FINAL_REPORT.md` and `README.md` exist (bilingual, conclusions first); criteria 3–4 hold.

## 1. Workspace, isolation, git

- **Worktree and branch** (create in WP0 if missing; idempotent):
  - Base: r5c tip `348af0b` on the local branch `exp/phase2-r5c-stress-fix-20261015`. Check that `git -C /Users/shane/Desktop/Arena_1013_model rev-parse exp/phase2-r5c-stress-fix-20261015` starts with `348af0b`, and record it.
  - Create: `git -C /Users/shane/Desktop/Arena_1013_model worktree add /Users/shane/Desktop/Arena_1021_r17_r5c -b exp/phase2-r17-r5c-improve-20261021 348af0b`. If it exists, check that its history contains `348af0b` and reuse it.
  - Work only in `/Users/shane/Desktop/Arena_1021_r17_r5c`. The study directory is `research/phase2_r17_r5c_improve_20261021/`.
  - The old r5c worktree `/Users/shane/Desktop/Arena_1015_r5c_stressfix` does **not** exist on this Mac. Do not reference it.
- **Code to reuse** (present in the new worktree because it starts from r5c):
  - `research/phase2_r5c_stress_fix_20261015/src/`: `common5c.py`, `runner5c.py`, `preds5c.py`, `smodel5c.py`, `stress.py`, `smodel.py`, `checks5c.py`;
  - `research/phase2_r5c_stress_fix_20261015/stage_1/prior2.json`, `stage_2/run_3.py` (R3_T's definition);
  - `research/phase2_round3_models_20261014/src/harness.py`, `research/phase2_anchor_step_20261013/src/events.py` (`_cv_ends`, `full_charges`), `research/phase2_v2_phase_matched_20261013/src/v2.py` (V2 returns `branch` ∈ {`phase`, `fallback`}).
  - Copy `src/` into the study as `src/`, rename `common5c.py` → `common17.py`, and change its worktree assert to `Arena_1021_r17_r5c`. Edit only the copies.
- **R3_T** is `LawFit(dict(law="two", sigma_s=0.10, transient_ref="restart", steps=True, steps_mode="gap_endpoint", beta_mode="one"))`, as in `run_3.py`. **REF** = 0.75·R3_T + 0.25·V2 (`preds5c.ens`).
- **Two known code traps; fix them in the copies before any run:**
  1. `preds5c.s_pred` memoises on `(key, name, delta[, step, a4s])`, not on the config. Every predictor name must encode every non-default config value. Add an assert that a name never maps to two different config hashes.
  2. `smodel5c.load_prior2` hard-codes the r5c study path. Make it take the path as an argument and point it at the copy.
- **Read-only sources outside this worktree.** Never `cd` into them or write to them. For git sources use `git -C … show` / `archive` only.
  - **Submitted model SUB:** commit `6525edf` on `exp/phase2-anchor-step-20261013` in `/Users/shane/Desktop/Arena_1013_model`. Extract `TechArena_Challenge2_Team_Package/` into the git-ignored `cache/submitted_package/`.
  - **SUB per-case predictions:** `exp/phase2-r10-cell-steps-20261017:research/phase2_r10_cell_steps_20261017/wp1/outputs/wp1_predictions.csv`, rows with `model == "A3"` and `step == "main"`. Columns: scenario, checkup, k, delta, step, a4s, model, Q, proxy, err_pp, SOH, branch. Copy it to `sources/`.
  - **Literature PDFs** (local only, git-ignored): `/Users/shane/Desktop/Arena_1013_model/research/phase2_literature_refresh_20261016/papers/`. Use `Naumann2018_LFP_calendar_aging_JES17-153.pdf`, `Lewerenz2018_overhang_reversible_loss_JES18-149.pdf`, `Lewerenz2017_capacity_rise_overhang_JPS345-254.pdf` and `Naumann2020_LFP_cycle_aging_JPS451-227666.pdf`. The reading notes are in `04_全文精读_9篇.md` and `03_新文献综述.md` on `exp/phase2-anchor-step-20261013`; they are secondary, and the PDF governs.
  - **TUM Sony LFP calendar data** (Naumann 2018, Mendeley kxh42bfgtj, CC BY 4.0): `/Users/shane/Desktop/Arena项目书面文件/外部数据/kxh42bfgtj-1/DischargeCapacity.xlsx`. Its existing reader is `research/phase2_literature_refresh_20261016/tum_calendar_check/check_tum_calendar.py` on `exp/phase2-anchor-step-20261013`. Copy it; read the data with `python3 -I -B`.
  - Record every copied or read external file with its source and SHA256 in `sources/SOURCES.md`.
- **One permitted download:** Schimpe et al. 2018, *JES* 165:A181, DOI 10.1149/2.1181714jes, open access from the publisher. Save it to the git-ignored `cache/papers/`. If the download fails, record it and use Naumann 2018 (same Sony cell, same group) for every parameter. No other downloads.
- **Concurrency guard.** Run `git log --oneline -5` at start and before every commit. On an unexpected change, stop editing shared files, record it, and add files by explicit path only. Never `git add -A`/`.`, never bare `git stash`, never force-push.
- **Commits.**
  - Commit this prompt first, as `research/phase2_r17_r5c_improve_20261021/EXECUTION_PROMPT.md`.
  - Commit at the end of every step and push with `git push -u origin exp/phase2-r17-r5c-improve-20261021`.
  - End every commit message with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
  - If the push fails, record it in STATUS.md and continue committing locally.
- **Do not modify** any `TechArena_Challenge2_Team_Package/`, any earlier study directory, or any file outside this worktree.
- **Language and Python.** Markdown is English first, Chinese second. Code comments are in English. Use `python3 -B`, and `python3 -I -B` for scripts that read external files.

## 2. Reference numbers (reproduce in WP0)

Units are pp of SOH, at Δ = 0.4, main step variant, A4 smoothing 2 Ah. Pseudo = mean MAE over PG1, PG2, PC5, PC10. Cold = mean over CS, CSE. All proxies are exposed.

| Model | Real MAE | Pseudo | Cold | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|---|---|---|
| REF = R3_TD_w0.75 | 0.131 | 0.123 | 0.134 | +0.048 | −0.311 | −0.092 | +0.132 | +0.033 | −0.197 | +0.107 |
| R3_T | 0.179 | 0.119 | 0.144 | −0.008 | −0.638 | −0.150 | +0.100 | −0.007 | −0.209 | +0.144 |
| V2 | 0.216 | 0.240 | 0.252 | +0.217 | +0.669 | +0.080 | +0.228 | +0.150 | −0.163 | −0.004 |
| SUB (A3, 6525edf) | 0.120 | 0.1342 | 0.1599 | +0.210 | +0.039 | +0.140 | +0.237 | +0.084 | −0.068 | −0.060 |

- **SUB's expected SOH, CK1–CK7:** 95.984, 94.507, 93.600, 92.821, 92.015, 91.426, 90.765.
- **R3_T prior** (`stage_1/prior2.json`), as (mean, sd):

  | Parameter | Mean | sd | Note |
  |---|---|---|---|
  | logA_b | 1.857 | 1.099 | |
  | logtau_b | 4.901 | 5.35 | Fixed at the mean: `tau_b_free=False`, ≈ 134 d |
  | logA_cal | −1.441 | 1.099 | Yagci fallback |
  | logA_cyc | −11.754 | 1.099 | |

- **R3_T clock:** Ea 37.3 kJ/mol applied to time (`stress.cumulative`), shared by all three terms.

## 3. Common rules

1. **Register, then run.** Each protocol is committed before the outputs it governs. External parameters are frozen in WP1, before any design is run with them.
2. **Selection never uses the real proxies.** Designs are selected on causal cases only (pseudo + cold). The real scenario runs once, in WP4, after all selections are committed. Real numbers are reported and labelled exposed; they never select, rank or veto.
3. **Prediction screens never read proxies.** Screen scripts must not load `H.QFC`, `proxy` or `err` columns. Add an assert, and include a grep of the script in the report.
4. **Exposure labels.** Every number derived from a quantity seen on the real proxies carries its label: `exposed-τb` (the τ_b grid; 134/60/30 d were seen on real), `exposed-CK1`, `exposed-CK2`, `exposed-w`.
5. **Small samples.** Causal cases are grouped by checkup k (k = 3..7; PG1/PG2 only k = 4..7). Inference is by blocks of k, never by pooling cases as if they were independent. Report effect size, sign counts and leave-one-k-out (LOKO) results; never a bare p-value.
6. **Shared month structure.** k = 4 is positive and k = 6 negative in every model. Report it once in WP0, as per-k mean errors over models. Any error-correlation statistic must first remove the per-(scenario, k) mean across models.
7. **One design per idea.** Each design below has one registered main form. Sensitivity variants are reported, never selected.

## 4. Work packages

### WP0 — Setup, reproduction, facts (cap 1.5 h)

- Create the worktree, `notes/`, `.gitignore` (`cache/`), `sources/`, `src/` (with the two fixes in §1).
- **Reproduce the §2 rows** for REF, R3_T and V2 with the copied code, within 0.001 pp. If REF does not reproduce, stop the whole run.
- **Load SUB per-case predictions.** Check that the real-scenario SOH at Δ = 0.4 equals SUB's expected SOH within 0.001 pp, and that the (scenario, k) case set matches runner5c's. Use only matching cases, and list any that don't match.
- **Noise floor.** For every causal case, take the SD of REF's predicted SOH across the 6 step variants (`H.VARIANTS`). Then:
  - T_move = max(0.05 pp, 2 × median SD);
  - δ = max(0.005 pp, 0.5 × median SD).

  Write both to `wp0/outputs/noise.json`.
- **F1 — split the "checkup" rows.** For every real and causal cut, classify each `kind == "checkup"` row of `stress_table` as `true_ck` (its interval contains a CK date) or `switch` (otherwise). Report days per class per month, and each class's share of R3_T's Arrhenius-weighted τ at the CK7 cut.
- **F2 — pack SOC history.** Build a causal SOC series from the visible data: Ah below the latest CV end, resetting at every `events._cv_ends` event (about every 4.8 days). Do **not** use `events.full_charges`, which resets only once per segment. Then SOC = 1 − (Ah below)/Q_ref, where Q_ref is the latest visible anchor capacity.

  Report, per month and per setpoint: the time-weighted mean SOC, its 10/90 % range, and the month-to-month spread of the mean. Also report the SOC at the last visible row of every segment. Those are the switch-row SOCs and the checkup entry SOCs.
- **F3 — term sizes.** For R3_T at the prior mean and at the real-cut MAP: the break-in, calendar and cycle contributions to the predicted loss, per month and cumulative to CK7, in Ah and pp.
- **F4 — Ea provenance.** Trace where 37.3 kJ/mol in `smodel.MAIN` and `stage_1/prior2.json` comes from: commit, file and fit. State whether its source fitted Ea on time or on k. `smodel.yagci_logA_cal` applies it to time before t^z.
- **F5 — SUB clock.** Quote `_effective_days` and `_sqrt_extrapolation` from 6525edf. List the (scenario, k) cases where SUB's `branch` is the √t gap branch.
- **F6 — V2 regime.** For every causal and real case, record V2's `branch` (`phase` or `fallback`). Tabulate the counts by scenario and k. This is the regime indicator for E2.
- **Done:** the reproductions; `noise.json`; F1–F6 tables in `wp0/REPORT.md`; criteria 2–4.

### WP1 — External parameters, frozen before use (cap 1.5 h; no pack proxies)

Extract each parameter from the primary source. Record value, unit, page, equation or table number, the cell it was measured on, and whether it is on time or on k. Write everything to `wp1/external_params.json`, commit it with its SHA256, and do not change it afterwards.

- **P1 — calendar Ea on k.**
  - Primary: Schimpe 2018. Its 20.6 kJ/mol was reported as fitted at 100 % SOC; confirm that and the form k(T)·√t.
  - Cross-check: Naumann 2018's temperature function for the same Sony cell.
  - If the two differ by > 20 %, use Naumann 2018, which has more storage conditions, and record why.
- **P2 — calendar SOC function k_SOC(SOC).**
  - Primary: Naumann 2018's published k_SOC form and parameters for the Sony US26650FTC1 cell. Schimpe 2018's Tafel-type anode-potential form is the cross-check.
  - Data check: from the TUM file, fit a per-condition √t amplitude (pure √t through the origin, over 0–400 d) at 25 °C and 40 °C. Normalise by the 50 % SOC value at each temperature and compare the shape with the paper function on SOC 0–100 %.
  - **Registered rule:**
    - Use the paper function if it was extracted with an equation number and its ratio k_SOC(SOC)/k_SOC(0.5) agrees with the TUM table within ±30 % at every TUM SOC from 12.5 % to 100 %.
    - Otherwise use the TUM table: average the 25 °C and 40 °C normalised amplitudes, interpolated linearly in SOC.
    - Either way, store the losing form as `k_SOC_alt` for the sensitivity runs.
- **P3 — overhang parameters.**
  - From Lewerenz 2018: the overhang area fraction, the reversible-loss relation ΔC = (SOC_before_test − SOC_storage) × f_oh, the full-compensation times at 30/40/50 °C, and the compensation Ea.
  - From Naumann 2018: the Sony cell's overhang fraction (the notes say 6.2 %).
  - Fit an Arrhenius line through Lewerenz's three compensation times, and report t_full at 25 °C and 45 °C both from that fit and from the stated 64.5 kJ/mol.
  - **Registered conversion:** τ_oh(T) = t_full(T)/3, from the stated-Ea line (the "full" point is taken as 95 % complete). The fitted-line values are the sensitivity.
  - **Overhang amplitude prior:** f_oh = the Sony value (6.2 % if confirmed), sd ln 2.
- **P4 — cycle term.** From Naumann 2020: does any reversible shallow-cycle loss appear under realistic dynamic profiles? Report the calendar/cycle split for the PV profiles. Only record the finding; it is used to label D, not to parameterise it.
- **P5 — transfer caveats.** One line per parameter on cell format and chemistry (Sony 3 Ah 26650 LFP; Lewerenz 25 Ah NMC prismatic) versus the 102 Ah LFP pack.
- **Done:** `external_params.json` + SHA256 committed; the P2 comparison plot and table; criteria 2–4. WP1 has no protocol, because it reads no pack proxies; its freeze commit plays that role.

### WP2 — Single-factor designs: prediction screen, then paired causal check (cap 3 h)

**Registered designs.** Each design is a change to R3_T only; everything else stays as REF. Each is evaluated both alone (`X`) and in the ensemble `X_ens` = 0.75·X + 0.25·V2.

| Id | Design (main form) | Sensitivity (reported only) |
|---|---|---|
| **B0** | Switch fix. `switch` rows get `kind="switch"` and the temperature mean of the last row of the earlier segment and the first row of the later one; throughput 0. `true_ck` rows are unchanged. This is a correction, not physics. | none |
| **S** | B0 + an SOC-weighted calendar clock. The calendar term uses τ_cal = Σ days·aT·k_SOC(SOC)/κ, where κ normalises k_SOC to a time-weighted mean of 1 over the visible operation rows of that cut, so A_cal's prior keeps its meaning. Break-in and cycle clocks are unchanged. SOC per row type: **observed** = F2 series; **switch** = SOC at the last row of the earlier segment; **true_ck** = half the interval at the entry SOC, half at 0 %; **seg_gap / extrapolated** = mean operating SOC of the last visible 45 °C segment. | true_ck all at entry SOC; true_ck all at 0 %; `k_SOC_alt` |
| **C** | Calendar Ea on k. τ_cal uses Ea_time = 2·P1 (41.2 kJ/mol if P1 = 20.6). Break-in and cycle clocks stay at 37.3 on time. Priors are not refit. | Ea_time = 74.6 (Yagci read as on k), labelled `exposed-CK2`, because the 10-21 table shows it |
| **O1** | τ_b model averaging (`exposed-τb`). Fit R3_T at τ_b ∈ {33.5, 67, 134, 268} d (= 134·2^{−2..1}), τ_b fixed in each. Per case, weight the predictions by the Laplace evidence of the anchor-pair + step-pair fit: log Z ≈ −½‖r‖² − ½ log det(JᵀJ). Use the LM residual vector at the MAP, including prior rows, with a numerical J over the free parameters. No proxies are involved. | uniform weights |
| **O2** | B0 + a reversible overhang state replacing the break-in term. dx/dt = (x_eq − x)/τ_oh(T), with x(CK0) = 0 and x_eq = A_oh·(SOC − SOC_0)/(SOC̄_op − SOC_0). SOC uses the same per-row-type rules as S. τ_oh(T) comes from P3. SOC_0 = 0.30 (assumed shipping SOC). SOC̄_op is the time-weighted mean operating SOC of the visible cut. logA_oh is free with prior mean ln(f_oh·(SOC̄_op − SOC_0)·Q_nom) and sd ln 2. The irreversible √τ_cal and cycle terms stay. Integrate x on the hourly rows; use the exact exponential update per row. | SOC_0 ∈ {0.10, 0.50}; τ_oh from the fitted line; x(CK0) = x_eq |
| **D** | Cycle term removed (the logA_cyc term and its prior row dropped). This is a simplification. | none |

GP or hybrid residual layers are not run: there are 7 anchors, and a fit-then-residual design uses the same data twice. Record this.

**Step 1 — prediction screen (no proxies).** For each design and each case (all causal cases + real k = 1..7; Δ = 0.4, main variant, a4s 2), compute ΔSOH = SOH(X) − SOH(R3_T). Report:
- S_causal = the 90th percentile of |ΔSOH| over causal cases;
- S_real = the maximum over real k.

A design **moves** if S_causal ≥ T_move or S_real ≥ 2·T_move. Designs that do not move are labelled **inert**. They skip step 2, except D, which is then accepted as non-inferior by definition. Commit the screen before step 2.

**Step 2 — paired causal check.** For each moving design, per causal case, compute the paired difference p_i = |err_X| − |err_R3_T|. Compute the same for the ensemble, q_i = |err_X_ens| − |err_REF|. Report:
- the mean, the share < 0, the per-k block means, the LOKO means and the worst value, for p and q;
- the same at Δ = 0 and Δ = 0.8;
- the stress-alone CK-by-CK signed error next to V2's, to show whether any ensemble gain comes from cancellation;
- the demeaned error correlation between X and V2 (rule 6).

**Pass rule (registered).** A design **passes** if all of the following hold:
1. mean p ≤ −δ at Δ = 0.4;
2. at most one k block of p has a positive mean;
3. every LOKO mean of p is ≤ 0;
4. the worst p_i is ≤ +0.30 pp;
5. mean q ≤ 0 at Δ = 0.4;
6. mean p ≤ 0 at both Δ = 0 and Δ = 0.8.

For D, the rule is non-inferiority instead: mean p ≤ +δ and worst p_i ≤ +0.10 pp.

O1 additionally reports per-case weight tables. τ_b is **identified** if the top weight is ≥ 0.8 in at least half the causal cases. If it is unidentified, O1 is labelled "uncertainty band, not a model". It is still evaluated, but cannot become the main design.

**Done:** the screen table, the paired tables, pass/fail per design, O1's identifiability verdict, criteria 1–4.

### WP3 — Combination and ensemble weights (cap 2 h; causal only)

**Step 1 — one combination.** Combine every design that passed WP2 into one model, M_comb:
- If both O1 and O2 passed, keep the one with the lower mean p.
- S and O2 share the SOC machinery; combine them as written.
- An accepted D removes the cycle term.

Evaluate M_comb against R3_T and REF with the WP2 rule. If M_comb fails while a single design passed, the main stress model M is the passing single design with the lowest mean p. If nothing passed, M = R3_T.

**Step 2 — ensemble on M.**
- **E1, a curve, not a selection.** Report the causal mean MAE of w·M + (1−w)·V2 for w ∈ {0, 0.25, 0.5, 0.75, 1}, at Δ = 0/0.4/0.8. Also report w·M + (1−w)·SUB on the matching cases.
- **E2, a two-regime weight.** The weight is w_phase when V2's branch is `phase` and w_fb when it is `fallback` (F6), with (w_phase, w_fb) ∈ {0.5, 0.75, 1.0}².
  - Pick the pair with the lowest causal mean MAE at Δ = 0.4.
  - Run LOKO re-picking and report how often each pair wins.
  - E2 replaces the fixed w = 0.75 only if both hold:
    - it beats M's best fixed w by ≥ δ in mean MAE;
    - the same pair wins in ≥ 4 of the 5 LOKO folds.
  - Otherwise keep w = 0.75. This is the pre-registered weight; do not re-pick the fixed w.
  - If F6 shows that one regime has fewer than 6 causal cases, E2 is not run. Record that.
- The chosen ensemble is **FINAL**.

**Step 3 — FINAL against SUB, causal only.** On the matching cases, compute the paired differences r_i = |err_FINAL| − |err_SUB| and apply WP2 rules 1–4 to r. The result is the label "causally better than SUB" (yes/no).

**Done:** M_comb result; M; E1 curves; E2 table and LOKO; FINAL's definition; the SUB comparison; criteria 1–4.

### WP4 — Real run, level, synthesis (cap 1.5 h)

**Real run.** Run once, after WP3 is committed. Models: R3_T, REF, every WP2 design that moved (alone and in the ensemble), M, FINAL, V2 and SUB. Report:
- MAE and MAX at Δ = 0/0.4/0.8, and per-CK signed errors;
- MAE without CK1, without CK2, and without both;
- the r5c real gates (G-proxy, G-epsfree, G-robust, G-regress) as pass/fail information only.

A design whose real gain over REF comes mostly (≥ 50 %) from CK1 or CK2 is labelled `exposed-CK1`/`exposed-CK2`. Real numbers never change any WP2/WP3 outcome; they are printed beside them.

**Level column.** For FINAL and every moving design, report the mean SOH shift against SUB over CK1–7 and over CK2–7. Set these next to the two leaderboard readings: truth about 1 pp below SUB, or CK2–7 about +0.65 pp above SUB (see the 2026-10-20 leaderboard note). This is information for the user, not a decision.

**FINAL_REPORT.md and README.md**, bilingual, conclusions first:
1. **One table**, with one row per design (B0, S, C, O1, O2, D, M_comb, E2, FINAL). Columns: moves? (S_causal / S_real), causal pass, mean p / q, LOKO, the real (exposed) columns, and the level shift against SUB.
2. **Expectations against outcomes**, for each item in "Rough expectations".
3. **What the 10-21 analysis got right and wrong**, including what B0 and S show about the "checkup" test.
4. **Recommendation:** one of the three below. The submission is unchanged in every case.
   - "FINAL is causally better than SUB; candidate code in `candidate_model/`; adopting it is the user's decision";
   - "FINAL improves r5c but not SUB";
   - "no design improves r5c".
5. **Scope statement.** Nothing here addresses the 0.7–1.0 pp level suggested by the leaderboard. Proxy-based scores are blind to a common-mode offset.

**Done:** both files; STATUS.md final; all commits pushed (or the push failure recorded).

### WP5 — Candidate code copy (only if FINAL is "causally better than SUB"; cap 1 h)

- Write `candidate_model/` as r5c did: a self-contained class with numpy/pandas only, which reproduces FINAL's real predictions within 0.001 pp.
- Run it under Python 3.11 and 3.13, and record runtime.
- Run `validate_submission.py` on a **copy** of the package in `cache/`; never on the real package.
- No zip, no upload, no change to any submission file.
- If FINAL is not causally better than SUB, mark WP5 skipped by rule.

---

<a id="zh"></a>

# 第 17 轮：r5c 压力模型的物理改进——预先登记设计，因果情景选择——执行 Prompt

> **语言：** [English](#en) · 中文

写于 2026-10-21。本文档自成一体。英文为执行文本，中文为供读者参考的翻译，两者不一致时以英文为准。

工作分为 **WP0–WP5** 六个工作包，按顺序执行。每个工作包有自己的"完成"清单，可以作为单独的 `/goal` 运行。

## 为什么有这一轮（先读）

2026-10-21 对 r5c 的分析发现，它的 CK2 结果是两个大误差互相抵消的产物。Δ = 0.4 时，压力模型 R3_T 单独为 −0.638 pp，V2 单独为 +0.669 pp，集成 REF = 0.75·R3_T + 0.25·V2 为 −0.311 pp。分析把 R3_T 在 CK2 多算的损失主要归因于磨合项：幅度约 4.9 Ah，τ_b 约 134 天，取自 Challenge 1 先验，且 τ_b 识别不出来。另外段 3 缺失，CK2 前没有台阶数据。分析随后提出了一组有文献依据的改进：
1. 可逆的 overhang 项，或对 τ_b 做模型平均；
2. 依赖 SOC 的日历老化速率；
3. Arrhenius 因子加在速率系数 k 上，而不是加在时间上；
4. 重写或去掉循环项；
5. 按情形切换的集成权重。

针对这些想法已经写过一个分诊 prompt（R16，`research/phase2_r16_triage_20261021/R16_EXECUTION_PROMPT.md`），但没有运行。**2026-10-21 用户选择改为运行这份完整的改进研究。** 不要再运行 R16。本轮沿用 R16 已核实的事实，并实现上述设计。

**10-21 分析中的探索性数字。** 全部已曝光（是在看着真实代理的情况下算的），也没有复现过。它们只作背景，**不得用于任何选择**。MAE 为集成后的值，单位 pp；CK2 为集成误差。

| 改动（10-21，探索性） | 真实 | 伪情景 | 冷启动 | CK2 |
|---|---|---|---|---|
| REF（r5c 原样） | 0.131 | 0.123 | 0.134 | −0.31 |
| Arrhenius 加在速率上，时间权重 aT² | 0.127 | 0.161 | 0.127 | +0.15 |
| Schimpe 20.6 kJ/mol 加在速率上 | 0.128 | 0.130 | 0.130 | −0.26 |
| "检测期"行不计日历老化 | 0.143 | 0.119 | 0.122 | −0.34 |
| τ_b = 60 天 | 0.117 | 0.182 | 0.152 | +0.08 |
| τ_b = 30 天 | 0.152 | 0.147 | 0.166 | +0.48 |

τ_b 在 30–134 天之间变动时，R3_T 单独的 CK2 从 +0.42 摆到 −0.64 pp。

**本轮之前已经更正的前提（已对照代码核实；以此为准，不以 10-21 的原文为准）：**
- **"检测期"行不只是检测期。** r5c 的 `src/stress.py` 中，`stress_table` 给相邻两段之间的*每一个*边界都加一行 25 °C 的 `kind="checkup"`，其中也包括月内 25→45 °C 换温箱时 7–25 小时的空闲。所以 10-21 那次"检测期不计日历老化"的测试把换温箱也一起关掉了，它的结果不是对检测期 SOC 的检验。
- **检测期的 SOC 有高有低，并非"放空"。** 电池组进入每次检测时都是充好电的（13.1–13.3 V，第 7 轮）；离开时是空的：每次检测后的第一次充电，都是在 I = 0 静置约 2 小时后、从 11.5–12.0 V 开始。检测期内各 SOC 停留了多长时间，看不到。
- **运行负载是一个 116.1 小时的程序块，几乎原样重复**（块与块之间的电流相关 ≥ 0.99，25 °C 和 45 °C 都是）。稳态 SOC 窗口是满充以下 11–72 Ah。所以对*运行*时间做任何 SOC 加权，都近似于一个常数乘子，会被 A_cal 吸收。SOC 加权只能通过 SOC 与运行时不同的区间改变预测：换温箱、检测期、缺失段、外推尾段。循环项也是同样道理：每个温度下每个运行日的吞吐量几乎不变，所以 A_cyc 与日历时间几乎共线。
- **Arrhenius 写法的影响没有 10-21 说的那么大。** 25 °C 相对 45 °C 的时钟权重是 exp(Ea/R·(1/318.15 − 1/298.15))：

  | 写法 | 权重 |
  |---|---|
  | SUB，20.6 kJ/mol 加在时间上 | 0.593 |
  | r5c，37.3 加在时间上 | 0.388 |
  | Schimpe 的 20.6 加在 k 上（= 41.2 加在时间上） | 0.352 |
  | 把 Yagci 的 37.3 当作加在 k 上（= 74.6 加在时间上） | 0.151 |

  r5c 的时钟已经接近 Schimpe 写法。10-21 那个大幅变化（aT²）对应的是最后一行。
- **SUB 的时钟只有一半强度。** SUB（`6525edf`）把 20.6 kJ/mol 加在时间上再开平方，相当于在 k 上只有 10.3 kJ/mol。真实场景里它的 √t 缺口分支只在 CK2 触发。本轮不改 SUB。
- **循环项不为零。** 先验均值 exp(−11.754) 仍然带来一个固定的损失。
- **Overhang 的现状。** 第 7 轮 WP1 发现，用 overhang 解释*锚点后台阶偏移*不被支持（与停放时长、起始状态的相关系数 ρ 符号相反）。那检验的是另一个现象。用 overhang 解释*早期日历非线性*（Lewerenz 2018），还没有在本电池组上检验过。文献给的时间尺度很慢：Lewerenz 2018 报告完全补偿约需 50 °C 下 150 天、40 °C 下 250 天、30 °C 下 490 天（Ea 64.5 kJ/mol，25 Ah NMC 电芯）。因此在 25 °C 下，1–3 天的检测期里锂从 overhang 流回的量预计很小。
- **"因果"情景只保证输入因果。** 伪情景（PG1、PG2、PC5、PC10）和冷启动情景（CS、CSE）评分时对照的，和真实场景是同一批已曝光的代理（`runner5c.run` 里是 `proxy = H.QFC[k] + H.EPS0 + d`）。0.003–0.005 pp 的余量小于单个案例的噪声。所以本轮的选择规则是配对的、按 k 分块的，并且考虑噪声。
- **水平问题更大，不在本轮范围内。** 第一次排行榜分数（SUB 0.1868，2026-10-20）意味着真实误差约 0.7–1.0 pp。这个误差是共模的，代理 MAE 看不见。本轮会报告每个设计相对 SUB 的水平偏移，但修不了水平误差。

**运行前写下的粗略预期。** 结果要逐条对照：
- C 对预测影响很小：41.2 对 37.3 加在时间上，25 °C 时钟只差 9%。
- S 只通过换温箱、检测期和缺失段这几类行改变预测。它可能动到有意义的程度，但远小于 10-21 那次"检测期"测试。
- O2（overhang）的表现像一个 45 °C 下 τ 约 50–75 天的磨合项，检测期回流很小。所以它对 CK2 的影响很可能落在 10-21 表中 τ_b = 60 天和 134 天两行之间；而 60 天那一行的伪情景更差。
- D 很可能不起作用（非劣）。
- "没有任何设计在因果上优于 REF"是有效结论，而且很可能就是结论。

## 0. 工作方式（所有工作包）

- **无人值守。** 不要停下来提问。遇到未定的决定时，选最保守且不违反本文任何规则的选项，记录到 `notes/DECISIONS.md`，然后继续。
- **重启。** 每一步之后更新 `notes/STATUS.md`（当前 WP、已完成、下一步、最近一次提交）。重启时先读 `notes/STATUS.md` 和 `notes/DECISIONS.md` 再继续。已完成的步骤不重做。
- **诚实优先于目标。** 不在真实代理上调参。本轮只产出证据、一条建议，以及最多一份候选代码副本：**不改提交包、不打 zip、不上传、不改任何提交文件。**
- **任一 WP 的"完成"** 指：
  1. 其登记协议（`wpN/protocol.json` + `wpN/protocol.sha256`）在其输出**之前**提交（WP0 没有协议）；
  2. 双语的 `wpN/REPORT.md` 已存在，结论在前；
  3. `notes/STATUS.md` 把该 WP 标为完成、到时封顶或退出，并附一行结果；
  4. 每次提交都推送到 `origin exp/phase2-r17-r5c-improve-20261021`，`git status` 没有未提交的研究文件。
- **全局完成：** WP0–WP4 都已完成、到时封顶或按登记规则退出；WP5 已完成或按规则跳过；`FINAL_REPORT.md` 和 `README.md` 已存在（双语，结论在前）；第 3、4 条成立。

## 1. 工作区、隔离、git

- **工作树和分支**（在 WP0 中创建，若缺失；可重复执行）：
  - 基点：本地分支 `exp/phase2-r5c-stress-fix-20261015` 的 r5c 末端 `348af0b`。检查 `git -C /Users/shane/Desktop/Arena_1013_model rev-parse exp/phase2-r5c-stress-fix-20261015` 以 `348af0b` 开头，并记录。
  - 创建：`git -C /Users/shane/Desktop/Arena_1013_model worktree add /Users/shane/Desktop/Arena_1021_r17_r5c -b exp/phase2-r17-r5c-improve-20261021 348af0b`。若已存在，检查其历史包含 `348af0b` 后复用。
  - 只在 `/Users/shane/Desktop/Arena_1021_r17_r5c` 中工作。研究目录是 `research/phase2_r17_r5c_improve_20261021/`。
  - 旧的 r5c 工作树 `/Users/shane/Desktop/Arena_1015_r5c_stressfix` 在这台 Mac 上**不存在**，不要引用。
- **可复用的代码**（新工作树从 r5c 开始，所以都在）：
  - `research/phase2_r5c_stress_fix_20261015/src/`：`common5c.py`、`runner5c.py`、`preds5c.py`、`smodel5c.py`、`stress.py`、`smodel.py`、`checks5c.py`；
  - `research/phase2_r5c_stress_fix_20261015/stage_1/prior2.json`、`stage_2/run_3.py`（R3_T 的定义）；
  - `research/phase2_round3_models_20261014/src/harness.py`、`research/phase2_anchor_step_20261013/src/events.py`（`_cv_ends`、`full_charges`）、`research/phase2_v2_phase_matched_20261013/src/v2.py`（V2 返回的 `branch` ∈ {`phase`, `fallback`}）。
  - 把 `src/` 复制到研究目录下作为 `src/`，把 `common5c.py` 改名为 `common17.py`，并把其中的工作树断言改成 `Arena_1021_r17_r5c`。只改副本。
- **R3_T** 即 `LawFit(dict(law="two", sigma_s=0.10, transient_ref="restart", steps=True, steps_mode="gap_endpoint", beta_mode="one"))`，与 `run_3.py` 一致。**REF** = 0.75·R3_T + 0.25·V2（`preds5c.ens`）。
- **两个已知代码陷阱，任何运行之前先在副本里修好：**
  1. `preds5c.s_pred` 按 `(key, name, delta[, step, a4s])` 缓存，不包含配置。每个预测器名字必须编码所有非默认的配置值。加一个断言：同一个名字不得对应两个不同的配置哈希。
  2. `smodel5c.load_prior2` 把 r5c 研究路径写死了。改为通过参数传入路径，并指向副本。
- **工作树之外的只读来源。** 不要 `cd` 进去，也不要写入。git 来源只用 `git -C … show` / `archive`。
  - **提交模型 SUB：** `/Users/shane/Desktop/Arena_1013_model` 里 `exp/phase2-anchor-step-20261013` 分支上的提交 `6525edf`。把 `TechArena_Challenge2_Team_Package/` 解压到 git 忽略的 `cache/submitted_package/`。
  - **SUB 的逐案例预测：** `exp/phase2-r10-cell-steps-20261017:research/phase2_r10_cell_steps_20261017/wp1/outputs/wp1_predictions.csv` 中 `model == "A3"` 且 `step == "main"` 的行。列：scenario、checkup、k、delta、step、a4s、model、Q、proxy、err_pp、SOH、branch。复制到 `sources/`。
  - **文献 PDF**（只在本地，git 忽略）：`/Users/shane/Desktop/Arena_1013_model/research/phase2_literature_refresh_20261016/papers/`。使用 `Naumann2018_LFP_calendar_aging_JES17-153.pdf`、`Lewerenz2018_overhang_reversible_loss_JES18-149.pdf`、`Lewerenz2017_capacity_rise_overhang_JPS345-254.pdf` 和 `Naumann2020_LFP_cycle_aging_JPS451-227666.pdf`。精读笔记在 `exp/phase2-anchor-step-20261013` 上的 `04_全文精读_9篇.md` 和 `03_新文献综述.md`，只作二手参考，以 PDF 原文为准。
  - **TUM Sony LFP 日历老化数据**（Naumann 2018，Mendeley kxh42bfgtj，CC BY 4.0）：`/Users/shane/Desktop/Arena项目书面文件/外部数据/kxh42bfgtj-1/DischargeCapacity.xlsx`。现成的读取脚本是 `exp/phase2-anchor-step-20261013` 上的 `research/phase2_literature_refresh_20261016/tum_calendar_check/check_tum_calendar.py`。复制过来用，读数据时用 `python3 -I -B`。
  - 每个复制或读取的外部文件都在 `sources/SOURCES.md` 中记录来源和 SHA256。
- **唯一允许的下载：** Schimpe et al. 2018，*JES* 165:A181，DOI 10.1149/2.1181714jes，出版方开放获取。存到 git 忽略的 `cache/papers/`。下载失败时记录下来，所有参数改用 Naumann 2018（同一款 Sony 电芯，同一研究组）。不做其他下载。
- **并发保护。** 开始时和每次提交前运行 `git log --oneline -5`。遇到意外变更时，停止编辑共享文件，记录下来，只按显式路径添加文件。不用 `git add -A`/`.`，不用裸 `git stash`，不强推。
- **提交。**
  - 先把本 prompt 提交为 `research/phase2_r17_r5c_improve_20261021/EXECUTION_PROMPT.md`。
  - 每一步结束都提交，并用 `git push -u origin exp/phase2-r17-r5c-improve-20261021` 推送。
  - 每条提交信息末尾加 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`。
  - 推送失败时记入 STATUS.md，继续在本地提交。
- **不得修改：** 任何 `TechArena_Challenge2_Team_Package/`、任何更早的研究目录、本工作树之外的任何文件。
- **语言和 Python。** Markdown 英文在前、中文在后。代码注释用英文。用 `python3 -B`；读外部文件的脚本用 `python3 -I -B`。

## 2. 参考数字（在 WP0 中复现）

单位是 SOH 的 pp，Δ = 0.4，主台阶变体，A4 平滑 2 Ah。伪情景 = PG1、PG2、PC5、PC10 的 MAE 均值；冷启动 = CS、CSE 的均值。所有代理都已曝光。

| 模型 | 真实 MAE | 伪情景 | 冷启动 | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|---|---|---|
| REF = R3_TD_w0.75 | 0.131 | 0.123 | 0.134 | +0.048 | −0.311 | −0.092 | +0.132 | +0.033 | −0.197 | +0.107 |
| R3_T | 0.179 | 0.119 | 0.144 | −0.008 | −0.638 | −0.150 | +0.100 | −0.007 | −0.209 | +0.144 |
| V2 | 0.216 | 0.240 | 0.252 | +0.217 | +0.669 | +0.080 | +0.228 | +0.150 | −0.163 | −0.004 |
| SUB（A3，6525edf） | 0.120 | 0.1342 | 0.1599 | +0.210 | +0.039 | +0.140 | +0.237 | +0.084 | −0.068 | −0.060 |

- **SUB 的预期 SOH，CK1–CK7：** 95.984、94.507、93.600、92.821、92.015、91.426、90.765。
- **R3_T 先验**（`stage_1/prior2.json`），格式为（均值，sd）：

  | 参数 | 均值 | sd | 说明 |
  |---|---|---|---|
  | logA_b | 1.857 | 1.099 | |
  | logtau_b | 4.901 | 5.35 | 固定在均值：`tau_b_free=False`，约 134 天 |
  | logA_cal | −1.441 | 1.099 | Yagci 回退值 |
  | logA_cyc | −11.754 | 1.099 | |

- **R3_T 的时钟：** Ea 37.3 kJ/mol 加在时间上（`stress.cumulative`），三项共用。

## 3. 通用规则

1. **先登记，再运行。** 每个协议都在其管辖的输出之前提交。外部参数在 WP1 冻结，之后才能用于任何设计。
2. **选择从不使用真实代理。** 设计只在因果案例（伪情景 + 冷启动）上选择。真实场景只在 WP4 运行一次，且在所有选择都已提交之后。真实数字只报告并标为已曝光，从不用于选择、排序或否决。
3. **预测筛查从不读取代理。** 筛查脚本不得加载 `H.QFC`、`proxy` 或 `err` 列。加断言保证这一点，并在报告里附上对脚本的 grep 结果。
4. **曝光标签。** 凡是来自在真实代理上见过的量的数字，都要带上对应标签：`exposed-τb`（τ_b 网格；134/60/30 天在真实场景上看过）、`exposed-CK1`、`exposed-CK2`、`exposed-w`。
5. **小样本。** 因果案例按检测点 k 分组（k = 3..7；PG1/PG2 只有 k = 4..7）。推断按 k 分块，绝不把案例当作独立样本合并。报告效应量、符号计数和逐一留出 k（LOKO）的结果，不单独给 p 值。
6. **共享的月份结构。** 所有模型都是 k = 4 偏正、k = 6 偏负。在 WP0 报告一次，形式是各模型在每个 k 上的平均误差。任何误差相关统计量都必须先减去每个（情景, k）上各模型的平均值。
7. **一个想法一个设计。** 下面每个设计只登记一个主形式。敏感性变体只报告，不参与选择。

## 4. 工作包

### WP0 — 准备、复现、核实事实（上限 1.5 小时）

- 创建工作树、`notes/`、`.gitignore`（`cache/`）、`sources/`、`src/`（包含 §1 的两处修正）。
- **用复制的代码复现 §2 中 REF、R3_T、V2 三行**，误差在 0.001 pp 以内。REF 复现不了就终止整轮。
- **读入 SUB 的逐案例预测。** 检查真实场景 Δ = 0.4 的 SOH 与 SUB 预期 SOH 相差在 0.001 pp 以内，并检查（情景, k）案例集合与 runner5c 的一致。只使用一致的案例，列出不一致的。
- **噪声底。** 对每个因果案例，取 REF 预测 SOH 在 6 个台阶变体（`H.VARIANTS`）上的标准差。然后：
  - T_move = max(0.05 pp, 2 × 标准差的中位数)；
  - δ = max(0.005 pp, 0.5 × 标准差的中位数)。

  两者都写入 `wp0/outputs/noise.json`。
- **F1——拆分"检测期"行。** 对每个真实截断和因果截断，把 `stress_table` 中每一行 `kind == "checkup"` 分为 `true_ck`（区间包含某个 CK 日期）和 `switch`（其他情况）。报告每月每类的天数，以及在 CK7 截断时各类占 R3_T 的 Arrhenius 加权 τ 的比例。
- **F2——电池组的 SOC 历史。** 用可见数据构建一条因果的 SOC 序列：相对最近一次 CV 结束点的放出 Ah，在每次 `events._cv_ends` 事件处归零（约每 4.8 天一次）。**不要**用 `events.full_charges`，它每段只归零一次。然后 SOC = 1 − 放出 Ah / Q_ref，Q_ref 为最近一个可见锚点的容量。

  按月、按设定温度报告：时间加权的平均 SOC、10/90 % 区间，以及各月均值之间的离散程度。同时报告每段最后一个可见行的 SOC，即换温箱行的 SOC 和进入检测时的 SOC。
- **F3——各项大小。** 对 R3_T 在先验均值和真实截断 MAP 下：磨合项、日历项、循环项对预测损失的贡献，按月和到 CK7 累计，单位 Ah 和 pp。
- **F4——Ea 的来源。** 追溯 `smodel.MAIN` 和 `stage_1/prior2.json` 里 37.3 kJ/mol 的出处：哪个提交、哪个文件、哪次拟合。说明其来源是把 Ea 加在时间上还是加在 k 上拟合的。`smodel.yagci_logA_cal` 是先把它加在时间上，再取 t^z。
- **F5——SUB 的时钟。** 引用 6525edf 的 `_effective_days` 和 `_sqrt_extrapolation`。列出 SUB 的 `branch` 为 √t 缺口分支的（情景, k）案例。
- **F6——V2 的情形。** 对每个因果和真实案例，记录 V2 的 `branch`（`phase` 或 `fallback`），按情景和 k 列出计数。这是 E2 的情形指示变量。
- **完成：** 复现结果；`noise.json`；`wp0/REPORT.md` 中的 F1–F6 表格；外加第 2–4 条。

### WP1 — 外部参数，使用前冻结（上限 1.5 小时；不读电池组代理）

每个参数都从原始来源提取。记录数值、单位、页码、公式或表格编号、测量所用的电芯，以及它是加在时间上还是加在 k 上。全部写入 `wp1/external_params.json`，连同 SHA256 一起提交，之后不得修改。

- **P1——加在 k 上的日历 Ea。**
  - 主来源：Schimpe 2018。其 20.6 kJ/mol 据称是在 100% SOC 下拟合的；核实这一点，以及 k(T)·√t 的形式。
  - 交叉核对：Naumann 2018 对同一款 Sony 电芯给出的温度函数。
  - 两者相差 > 20% 时，用 Naumann 2018（存放条件更多），并记录原因。
- **P2——日历 SOC 函数 k_SOC(SOC)。**
  - 主来源：Naumann 2018 对 Sony US26650FTC1 电芯发表的 k_SOC 形式和参数。Schimpe 2018 基于负极电位的 Tafel 型形式作交叉核对。
  - 数据核对：从 TUM 文件中，对 25 °C 和 40 °C 下每个条件拟合 √t 幅度（过原点的纯 √t，用 0–400 天）。在每个温度下除以 50% SOC 的值做归一化，然后在 SOC 0–100% 上与论文函数比较形状。
  - **登记规则：**
    - 如果论文函数是带公式编号提取的，并且在 12.5% 到 100% 的每个 TUM SOC 点上，比值 k_SOC(SOC)/k_SOC(0.5) 与 TUM 表的差在 ±30% 以内，就用论文函数。
    - 否则用 TUM 表：取 25 °C 和 40 °C 归一化幅度的平均，在 SOC 上线性插值。
    - 无论哪种情况，落选的形式都存为 `k_SOC_alt`，供敏感性运行使用。
- **P3——overhang 参数。**
  - 从 Lewerenz 2018 提取：overhang 面积比例、可逆损失关系 ΔC = (检测前 SOC − 存放 SOC) × f_oh、30/40/50 °C 下的完全补偿时间，以及补偿过程的 Ea。
  - 从 Naumann 2018 提取 Sony 电芯的 overhang 比例（笔记里是 6.2%）。
  - 用 Lewerenz 的三个补偿时间拟合一条 Arrhenius 直线，分别用这条拟合线和文中给出的 64.5 kJ/mol 报告 25 °C 和 45 °C 下的 t_full。
  - **登记的换算：** τ_oh(T) = t_full(T)/3，用文中给出的 Ea 那条线（把"完全补偿"当作完成 95%）。拟合线的值作为敏感性。
  - **overhang 幅度先验：** f_oh = Sony 的值（若核实为 6.2% 即用之），sd 为 ln 2。
- **P4——循环项。** 从 Naumann 2020 核实：在真实动态剖面下，是否出现可逆的浅循环损失？报告 PV 剖面中日历与循环的占比。只记录结论，用于给 D 贴标签，不用于给 D 定参数。
- **P5——迁移的注意事项。** 每个参数写一行，说明其电芯规格和化学体系（Sony 3 Ah 26650 LFP；Lewerenz 25 Ah NMC 方形）与 102 Ah LFP 电池组的差别。
- **完成：** `external_params.json` 及其 SHA256 已提交；P2 的对比图和表；外加第 2–4 条。WP1 不读电池组代理，所以没有协议，冻结提交起协议的作用。

### WP2 — 单因素设计：先筛预测，再做配对因果检查（上限 3 小时）

**登记的设计。** 每个设计只改 R3_T，其余与 REF 相同。每个设计既单独评估（`X`），也在集成 `X_ens` = 0.75·X + 0.25·V2 中评估。

| 编号 | 设计（主形式） | 敏感性（只报告） |
|---|---|---|
| **B0** | 换温箱修正。`switch` 行改为 `kind="switch"`，温度取前一段最后一行与后一段第一行温度的均值，吞吐量为 0。`true_ck` 行不变。这是一处修正，不是物理改动。 | 无 |
| **S** | B0 + 按 SOC 加权的日历时钟。日历项用 τ_cal = Σ 天数·aT·k_SOC(SOC)/κ，其中 κ 把 k_SOC 归一化，使其在该截断可见运行行上的时间加权均值为 1，这样 A_cal 的先验含义不变。磨合项和循环项的时钟不变。各类行的 SOC：**observed** = F2 序列；**switch** = 前一段最后一行的 SOC；**true_ck** = 区间一半按进入时的 SOC、一半按 0%；**seg_gap / extrapolated** = 最后一个可见 45 °C 段的平均运行 SOC。 | true_ck 全按进入时的 SOC；true_ck 全按 0%；`k_SOC_alt` |
| **C** | 日历 Ea 加在 k 上。τ_cal 用 Ea_time = 2·P1（若 P1 = 20.6 即 41.2 kJ/mol）。磨合项和循环项的时钟保持 37.3 加在时间上。先验不重拟合。 | Ea_time = 74.6（把 Yagci 的值当作加在 k 上），标为 `exposed-CK2`，因为 10-21 的表里出现过 |
| **O1** | τ_b 模型平均（`exposed-τb`）。在 τ_b ∈ {33.5, 67, 134, 268} 天（= 134·2^{−2..1}）下分别拟合 R3_T，每次 τ_b 固定。逐案例用锚点对 + 台阶对拟合的 Laplace 证据对预测加权：log Z ≈ −½‖r‖² − ½ log det(JᵀJ)。用 MAP 处的 LM 残差向量（含先验行），J 对自由参数数值求导。全程不涉及代理。 | 等权 |
| **O2** | B0 + 可逆 overhang 状态，替换磨合项。dx/dt = (x_eq − x)/τ_oh(T)，x(CK0) = 0，x_eq = A_oh·(SOC − SOC_0)/(SOC̄_op − SOC_0)。SOC 用与 S 相同的分行规则，τ_oh(T) 来自 P3，SOC_0 = 0.30（假定的出厂 SOC），SOC̄_op 为可见截断内时间加权的平均运行 SOC。logA_oh 自由拟合，先验均值 ln(f_oh·(SOC̄_op − SOC_0)·Q_nom)，sd 为 ln 2。不可逆的 √τ_cal 项和循环项保留。x 在逐小时的行上积分，每行用精确的指数更新。 | SOC_0 ∈ {0.10, 0.50}；τ_oh 用拟合线；x(CK0) = x_eq |
| **D** | 去掉循环项（logA_cyc 项及其先验行一并去掉）。这是简化。 | 无 |

GP 或混合残差层不运行：只有 7 个锚点，而"先拟合再拟合残差"的设计把同一份数据用了两次。记录这一点。

**第 1 步——预测筛查（不读代理）。** 对每个设计和每个案例（全部因果案例 + 真实 k = 1..7；Δ = 0.4、主变体、a4s 2），计算 ΔSOH = SOH(X) − SOH(R3_T)。报告：
- S_causal = 因果案例上 |ΔSOH| 的第 90 百分位数；
- S_real = 真实 k 上的最大值。

若 S_causal ≥ T_move 或 S_real ≥ 2·T_move，判该设计*能动*。不能动的设计标为**惰性**，跳过第 2 步；D 例外，此时按定义判为非劣并接受。第 2 步之前先提交筛查结果。

**第 2 步——配对因果检查。** 对每个能动的设计，逐因果案例计算配对差 p_i = |err_X| − |err_R3_T|；对集成计算 q_i = |err_X_ens| − |err_REF|。报告：
- p 和 q 的均值、< 0 的比例、各 k 块均值、LOKO 均值和最差值；
- Δ = 0 和 Δ = 0.8 下的同样统计；
- 压力模型单独的逐 CK 带符号误差，与 V2 的并列，用来看集成的收益是否来自抵消；
- X 与 V2 去均值后的误差相关（规则 6）。

**通过规则（登记）。** 以下全部满足时，判该设计**通过**：
1. Δ = 0.4 时 p 的均值 ≤ −δ；
2. p 至多一个 k 块的均值为正；
3. p 的每个 LOKO 均值都 ≤ 0；
4. 最差的 p_i ≤ +0.30 pp；
5. Δ = 0.4 时 q 的均值 ≤ 0；
6. Δ = 0 和 Δ = 0.8 时 p 的均值都 ≤ 0。

D 改用非劣规则：p 的均值 ≤ +δ，且最差的 p_i ≤ +0.10 pp。

O1 另外报告逐案例的权重表。若至少一半因果案例的最大权重 ≥ 0.8，判 τ_b *可识别*。不可识别时，O1 标为"不确定度带，不是模型"：它仍参与评估，但不能成为主设计。

**完成：** 筛查表、配对表、各设计的通过与否、O1 的可识别性结论，外加第 1–4 条。

### WP3 — 组合与集成权重（上限 2 小时；只用因果情景）

**第 1 步——一个组合。** 把 WP2 中所有通过的设计合成一个模型 M_comb：
- O1 和 O2 都通过时，保留 p 均值较低的那个。
- S 和 O2 共用 SOC 机制，按原样组合。
- D 若被接受，就去掉循环项。

用 WP2 的规则把 M_comb 与 R3_T 和 REF 比较。如果 M_comb 不通过而有单个设计通过，主压力模型 M 取通过的单个设计中 p 均值最低的那个。如果没有任何设计通过，M = R3_T。

**第 2 步——在 M 上做集成。**
- **E1，一条曲线，不是一次选择。** 报告 w·M + (1−w)·V2 在 w ∈ {0, 0.25, 0.5, 0.75, 1} 时的因果 MAE 均值，Δ = 0/0.4/0.8。也在一致的案例上报告 w·M + (1−w)·SUB。
- **E2，两档权重。** V2 的 branch 为 `phase` 时用 w_phase，为 `fallback` 时用 w_fb（见 F6），(w_phase, w_fb) ∈ {0.5, 0.75, 1.0}²。
  - 取 Δ = 0.4 时因果 MAE 均值最低的组合。
  - 逐一留出 k 重新选，报告每个组合胜出的次数。
  - 只有同时满足以下两条，E2 才替换固定的 w = 0.75：
    - 它的 MAE 均值比 M 的最佳固定 w 低至少 δ；
    - 同一个组合在 5 个 LOKO 折中至少 4 个胜出。
  - 否则保留 w = 0.75。这是预先登记的权重，不要重新挑选固定 w。
  - 如果 F6 显示某一档的因果案例少于 6 个，E2 不运行，并记录下来。
- 选出的集成记为 **FINAL**。

**第 3 步——FINAL 与 SUB 比较，只用因果情景。** 在一致的案例上计算配对差 r_i = |err_FINAL| − |err_SUB|，对 r 套用 WP2 规则 1–4。结果是"因果上优于 SUB"（是/否）。

**完成：** M_comb 的结果；M；E1 曲线；E2 的表和 LOKO；FINAL 的定义；与 SUB 的比较；外加第 1–4 条。

### WP4 — 真实运行、水平、汇总（上限 1.5 小时）

**真实运行。** 在 WP3 提交之后运行一次。模型：R3_T、REF、WP2 中所有能动的设计（单独和集成）、M、FINAL、V2、SUB。报告：
- Δ = 0/0.4/0.8 下的 MAE 和 MAX，以及各 CK 的带符号误差；
- 去掉 CK1、去掉 CK2、两者都去掉后的 MAE；
- r5c 的真实门槛（G-proxy、G-epsfree、G-robust、G-regress），只作为通过/不通过的信息。

真实场景中相对 REF 的收益主要（≥ 50%）来自 CK1 或 CK2 的设计，标为 `exposed-CK1`/`exposed-CK2`。真实数字从不改变 WP2/WP3 的任何结论，只列在旁边。

**水平一列。** 对 FINAL 和每个能动的设计，报告相对 SUB 在 CK1–7 和 CK2–7 上的平均 SOH 偏移。把它和两种排行榜解读并列：真值比 SUB 低约 1 pp；或 CK2–7 比 SUB 高约 +0.65 pp（见 2026-10-20 的排行榜笔记）。这是给用户的信息，不是决定。

**FINAL_REPORT.md 和 README.md**，双语，结论在前：
1. **一张表**，每个设计一行（B0、S、C、O1、O2、D、M_comb、E2、FINAL）。列：能否动（S_causal / S_real）、因果是否通过、p / q 均值、LOKO、真实（已曝光）各列、相对 SUB 的水平偏移。
2. **预期与结果对照**，逐条对照"运行前写下的粗略预期"。
3. **10-21 分析说对了什么、说错了什么**，包括 B0 和 S 对那次"检测期"测试说明了什么。
4. **建议：** 以下三者之一。无论哪种，提交版本都不变。
   - "FINAL 在因果上优于 SUB；候选代码在 `candidate_model/`；是否采用由用户决定"；
   - "FINAL 改进了 r5c，但不优于 SUB"；
   - "没有设计能改进 r5c"。
5. **范围声明。** 本轮没有任何内容涉及排行榜暗示的 0.7–1.0 pp 水平误差。基于代理的分数看不见共模偏移。

**完成：** 两个文件都已存在，STATUS.md 为最终状态，所有提交都已推送（或已记录推送失败）。

### WP5 — 候选代码副本（仅当 FINAL "因果上优于 SUB"；上限 1 小时）

- 像 r5c 那样写 `candidate_model/`：一个只用 numpy/pandas 的独立类，复现 FINAL 的真实预测，误差在 0.001 pp 以内。
- 在 Python 3.11 和 3.13 下运行，并记录耗时。
- 在 `cache/` 里的提交包**副本**上运行 `validate_submission.py`，绝不在真实提交包上运行。
- 不打 zip、不上传、不改任何提交文件。
- 如果 FINAL 不是因果上优于 SUB，把 WP5 标为按规则跳过。
