<a id="en"></a>

# Round 7: Literature-Driven Checks — Overhang State Effect, Temperature-Weighted √t for CK2, ε Drift on Yagci — Execution Prompt

> **Language:** English · [中文](#zh)

Written 2026-10-16. This document is self-contained. The English text is the execution text; the Chinese section is a translation for the reader, and if they differ the English governs.

The work is split into **work packages WP0–WP5**. Each has its own *Done* list and can be run as a separate `/goal`. WP0 must be done first. WP1, WP2 and WP3 are independent of each other. WP4 is optional. WP5 comes last.

## 0. Mode of work (all work packages)

- **Unattended.** Never stop to ask. When a decision is open, take the most conservative option that keeps every rule here, record it in `notes/DECISIONS.md`, and continue.
- **Restarts.** Keep `notes/STATUS.md` current after every step: WP, done, next, last commit. On restart, read `notes/STATUS.md` and `notes/DECISIONS.md` first and resume. Never redo a finished WP or step.
- **Honesty over targets.** A negative, inconclusive or "exit" result is a valid outcome. Never tune on the real proxies. This round produces **evidence and recommendations**; it never changes the submission.
- **Done for any WP** means the common criteria below, plus that WP's own list:
  1. its registered protocol (`wpN/protocol.json` + `wpN/protocol.sha256`) was committed **before** its evaluation outputs;
  2. its bilingual `wpN/REPORT.md` exists, conclusions first;
  3. `notes/STATUS.md` marks the WP done, capped, skipped or exited, with one line of result;
  4. every commit is pushed to `origin exp/phase2-r7-lit-checks-20261016`, and `git status` shows no uncommitted study files.
- **Global Done** (whole prompt): WP0–WP5 each done, capped, skipped or exited by a registered rule; `FINAL_REPORT.md` and `README.md` exist (bilingual, conclusions first); common criteria 3–4 hold.

## 1. Workspace, isolation, git

- **Worktree and branch (create in WP0 if missing; idempotent).**
  - Base: round 6's final commit on `exp/phase2-r6-robust-20261016`. At writing time this is `e144086`; use the branch tip and record its hash.
  - Create: `git -C /Users/shane/Desktop/Arena_1013_model worktree add /Users/shane/Desktop/Arena_1016_r7_lit -b exp/phase2-r7-lit-checks-20261016 <base>`. If the worktree or branch already exists, check that its history contains `<base>` and reuse it.
  - Work only in `/Users/shane/Desktop/Arena_1016_r7_lit`. The study directory is `research/phase2_r7_lit_checks_20261016/`.
- **Code to reuse (present in this worktree because it starts from round 6):**
  - round 6 study `research/phase2_r6_robust_20261016/`: `src/` (5C runner and harness copies, `common6.py`), `sources/` (archived `v3.py`, rebound diagnosis, submitted `my_model`), `wp1/` (18-hypothesis grid and score s_h), `wp3/` (3a start-state audit, 3b drift, 3c path offsets and their outputs), `wp4/` (Yagci table builder and table);
  - round 3 harness `research/phase2_round3_models_20261014/src/harness.py` (scenarios real, PG1, PG2, PC5, PC10);
  - V2 `research/phase2_v2_phase_matched_20261013/src/v2.py` and events `research/phase2_anchor_step_20261013/src/events.py`.
  - Copy what you change into this study; edit only the copies.
- **Read-only sources outside this worktree.** Never `cd` into them and never write to them:
  - the **submission branch** `exp/phase2-anchor-step-20261013`, commit `21a7a55`, in `/Users/shane/Desktop/Arena_1013_model`. Use only `git -C … show` / `git -C … archive`. `my_model/model_template.py` there is the **submitted model SUB = V2+√t**. Extract the package into `cache/submitted_package/` exactly as round 6 did.
  - the **literature refresh** in `/Users/shane/Desktop/Arena_1013_model/research/phase2_literature_refresh_20261016/` (may be uncommitted; copy by file and record SHA256): `03_新文献综述.md`, `04_全文精读_9篇.md`, `tum_calendar_check/` (script, `RESULTS.md`, `outputs/`), `papers/README.md`. Do **not** copy the PDFs in `papers/` into git (copyright); read them in place if needed.
  - **Round 6 cache** (git-ignored there): `/Users/shane/Desktop/Arena_1016_r6_robust/research/phase2_r6_robust_20261016/cache/downloads/yagci/` (`Data.zip`, `readme.md`, `unzipped/`). Read in place with `python3 -I`; never modify. If it is missing, follow WP3's exit rule.
  - **External datasets:** `/Users/shane/Desktop/Arena_1013_model/external_data/` (`DATA_MANIFEST.md`).
  - **TUM calendar data:** `/Users/shane/Desktop/kxh42bfgtj-1/` (Mendeley kxh42bfgtj v1, CC BY 4.0).
  - Record every copied file with its source path or commit and SHA256 in `sources/SOURCES.md`.
- **Concurrency guard.**
  - At the start and before every commit, run `git log --oneline -5` and compare with your last commit.
  - On an unexpected commit or change: stop editing shared files, record it, and add files by explicit path only.
  - Never `git add -A` / `.`, never rewrite others' work, never bare `git stash`. Run only one session on this worktree at a time.
- **Commits.**
  - Commit this prompt first, as `research/phase2_r7_lit_checks_20261016/EXECUTION_PROMPT.md`.
  - Commit at the end of every step, then `git push -u origin exp/phase2-r7-lit-checks-20261016`. Never push elsewhere; never force.
  - End every commit message with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Do not modify:** any `TechArena_Challenge2_Team_Package/` (anywhere), any earlier study directory, any file outside this worktree.
- **Language and bytecode.** Markdown is English first, Chinese second, in this file's layout. Code comments are English only. Run Python with `python3 -B`; use `python3 -I -B` for any script that reads external or downloaded files.
- **No downloads are needed.** If one turns out to be needed, put it in its own new directory under the git-ignored `cache/downloads/`, treat it as untrusted data, and never execute anything from it.

## 2. Context

**Task.** Estimate the SOH (C/20 capacity: 5.1 A discharge after a full charge until pack 11.2 V, divided by 102 Ah) of a 4 × 102 Ah LFP series pack on CK0..CK7.
- Only CK0 = 100.41 Ah is released.
- Scoring: error metrics on CK1–CK7, including the worst case, each normalised by the ExampleModel baseline, weighted 70 %.
- Causal cut: `load_dataset(data, until=CK_k)`.

**Proxies** (all already seen, so every real-scenario number is exposed-exploratory): P_k = Q_fc,k + ε0 + Δ, with ε0 = 100.41 − Q_fc,0 and Δ ∈ {0, 0.4, 0.8}.

**Reference SUB = V2+√t** (submitted at `21a7a55`): `v3(..., use_sqrt=True, beta_cap=inf, median=False)`. Proxy MAE Δ0/.4/.8 = 0.207/0.123/0.140; MAX 0.609/0.228/0.228; pseudo 0.148; cold start 0.174.
- Its √t gap branch fires in the real scenario only at CK2. Rule for CK_k, k ≥ 2, when the last visible deep program is > 10 days before CK_k: fit loss_j = a·t_j^p (through the origin) to anchors j = 1..k−1 with t = days since CK0, then Q̂_k = Q_anc,k−1 + ε − a·(t_k^p − t_{k−1}^p), p = 0.5.
- The branch is **exposed at CK2**.

**Round 6 results (final report on its branch):**
- Keep SUB (lowest max regret 0.027 on the 18-hypothesis grid h = (Δ, f, d)).
- **ε drift** d = −0.031 Ah/Ah is the best hedge (best worst case 0.194 vs 0.225; wins in 14/18 h) → first leaderboard probe **P_drift**.
- **3a start state:** the charge left at anchor start differs by up to 1.29 Ah from anchor 0 (upper bound from the CK0 C/20 tail), with low confidence.
- **3c path effect:** the first deep program after each anchor charge sits 0.41–0.56 Ah deeper (trend-adjusted median over 6 step variants; **0.83 Ah for month 0 at 45 °C**). Dropping those programs **contradicts the proxies** under every grid hypothesis.
- The WP2/WP4 stress-law candidates did not pass the gates.

**Literature refresh findings this round tests (see `04_全文精读_9篇.md`):**
1. **Overhang state effect** (Lewerenz 2017 JPS 345:254; Lewerenz 2018 JES 18:149; Gyenes 2015; Naumann 2018).
   - While the anode is held near empty, lithium flows from the passive anode overhang into the active area. This **raises cyclable lithium and capacity**, and lengthens the graphite-step → top distance.
   - At high SOC it flows back. Overhang share is 5.7–9 % of the anode; the exchange has Ea ≈ 64.5 kJ/mol; full compensation takes about 150 d at 50 °C (whole overhang), but near-edge parts are faster.
   - Here, after every checkup the pack rests near empty (2.89–3.00 V/cell) before the anchor charge. That would boost **both** the anchor Q_fc and the first deep program, which also explains why removing only the program contradicts the anchor-based proxies.
   - The LFP memory effect (Sasaki 2013) is largely ruled out: it is mostly in charge direction and erased by one full charge, and every deep program starts with a full charge. Homogenisation (Lewerenz 2017 DVA) predicts a sharper step, which was not seen.
   - **Open question:** the time constant. The offset is gone by the next program, about 5 days later.
2. **Temperature-weighted time for √t** (Naumann 2018 JES 17:153).
   - In the dynamic calendar study the order of conditions did not matter and the rate depends on the current state, so time should accumulate as Arrhenius-weighted "virtual time".
   - CK0→CK1 is about 20 d at 45 °C (segment 1). CK1→CK2 is 8 d at 25 °C (segment 2) plus the missing segment 3 (19 Feb–11 Mar), which by the public alternation schedule (short 25 °C / long 45 °C) is 45 °C.
   - Weighting 25 °C days by 1/AF (AF 1.7–2.6 for Ea 20.6–37.3 kJ/mol) shrinks SUB's CK1→CK2 increment by 6–9 %, i.e. CK2 SOH +0.08–0.12 pp.
   - Independently, the TUM Sony LFP data (`tum_calendar_check/RESULTS.md`) show that √t over-predicts the day-25 → day-56 loss by a median of 13 % on the 6 conditions with comparable early fade (median ratio 0.87, range 0.81–1.02).
3. **ε is not a Coulomb-efficiency effect** (Smith 2011 JES 158:A1136).
   - Parasitic charge during one ~5 h full charge is only about 0.007 Ah here, so ε and its drift come from protocol and endpoint state.
   - The external drift estimate rests on LIC 280 Ah (−0.035) and Gotion 53 Ah (−0.031) only. The Yagci 180 Ah cycling cells (in round 6's cache, with a per-cycle sheet) are a third, unused source.
   - TUM data cannot test ε: charge capacity is not published.

## 3. Common rules

1. **Register, then run.** Register in `wpN/protocol.json` (with SHA256) before computing any number that the WP's decision uses. For WP2, run and commit the causal scenarios before the real scenario.
2. **Selection never uses the real proxies.** Real-scenario results are reported for every registered design, including losers.
3. **Exposed changes.** WP2 designs act only through the √t branch. In the real scenario that branch fires only at CK2, whose error was known when they were conceived, so their real-scenario CK2 gain is labelled `exposed-CK2` and is not evidence. Causal evidence comes only from scenarios where the branch fires without exposure (WP2).
4. **Leaderboard-only outputs.** Label-hypothesis implications (WP1) and drift values (WP3) are never scored as proxy improvements. They are reported as SOH tables and on round 6's hypothesis grid, extended where this prompt says so.
5. **Small samples.** There are only 7–8 anchors. Every WP1 statistic is descriptive. Report effect size, sign counts and an exact permutation p-value, never a significance claim alone.
6. **Implementation.** Cache keys include every parameter; causality checks compare exact floats; deviations are registered before running.
7. **Wiring.** Never wire anything into a real `my_model/`. Any candidate class is checked on a copy in `cache/package_copy_*`.

## 4. Work packages

### WP0 — Setup and re-baselining (cap 0.5 h)

- Create the worktree (§1) if missing, plus `notes/STATUS.md`, `notes/DECISIONS.md`, `.gitignore` (`cache/`) and `sources/`.
- Copy the read-only sources (§1) and write `sources/SOURCES.md` with SHA256 values.
- **Reproduce with round 6's code:**
  - SUB at Δ = 0.4: MAE 0.123, MAX 0.228, pseudo 0.148, cold start 0.174;
  - round 6 WP1 max regret of SUB (0.027);
  - round 6 3c per-anchor path offsets (`wp3c_path_offsets.csv`);
  - 3a start-state table.
- **Inventory the √t branch.** For every scenario in real, PG1, PG2, PC5, PC10, CS and CSE, list each (scenario, k) where SUB takes the `sqrt_gap` branch. Save it to `wp0/outputs/sqrt_branch_cases.csv`. WP2 depends on it.
- **Done:** all reproductions within 0.001 pp (stop the whole run if SUB fails), the inventory, plus the common criteria. WP0 has no protocol; `wp0/REPORT.md` is short.

### WP1 — Is the post-anchor offset an overhang state effect? (cap 2.5 h; no model change)

**Per-anchor table** (anchors 0..7, from the full operation data; these are diagnostics, not predictions, so the causal cut does not apply). Columns:
- (a) **near-empty dwell proxy**: hours from the last operating sample before CK_k to the start of anchor k's charge; also the rest hours and pre-charge pack/cell rest voltages at anchor start;
- (b) round 6 3a residual charge r_j (upper bound and half bound);
- (c) round 6 3c **discharge-direction offset** of the first deep program after anchor k (trend-adjusted, all 6 step variants, plus the median);
- (d) the same offset for the **second** deep program after anchor k;
- (e) the **charge-direction step → top distance inside the anchor charge** (from `charge_step_split`, 2 Ah smoothing);
- (f) the same distance in the recharges of the first two deep programs after anchor k. These recharges start from about 56 Ah below full and cross the step in charge direction. Implement the location with the same method as `charge_step_split`, measured from the CV end, so the start depth cancels.
- (g) setpoint temperature from anchor start to the first deep program.

Write `wp1/outputs/anchor_state_table.csv`.

**Registered predictions** (overhang state effect vs a program-path effect). Use anchors 1..7 for P1–P4; report anchor 0 separately because of break-in, the delivery state and 45 °C.
- **P1 — the anchor shares the offset.** e_k = (e) − median of (f). Prediction: median_k e_k ≥ +0.20 Ah and e_k > 0 for ≥ 5 of 7 anchors. A program-path effect predicts e_k ≈ 0.
- **P2 — dwell dependence.** Spearman ρ between (c, median) and (a) ≥ +0.5, with an exact permutation p-value.
- **P3 — emptier start, larger boost.** Spearman ρ between (c, median) and r_j (upper bound) ≤ −0.5, with an exact permutation p-value.
- **P4 — fast decay.** (d) − trend ≤ 0.15 Ah for ≥ 5 of 7 anchors. This tests the time-constant objection; it is not a support criterion.

**Classification (registered):**
- **supported** if P1 holds and at least one of P2/P3 holds;
- **partly supported** if P1 holds alone;
- **not supported** if P1 fails.

Always report P4 and the month-0 values (0.83 Ah discharge-direction offset at 45 °C) with a short physical discussion. Use Lewerenz 2018's Ea of 64.5 kJ/mol to compare the expected exchange speed at 25 °C and 45 °C, and state whether month 0 is consistent.

**Implication analysis (leaderboard-only, registered):**
- Let b_k be the anchor boost estimate (e_k if P1 holds; otherwise 0). If the hidden C/20 is measured **before** the near-empty dwell (the most likely order: operation ends → checkup, full charge then C/20 discharge → dwell → anchor), the hidden capacity excludes the boost. Then Q_CK,k = Q_fc,k − b_k + c, and with ε0 defined at CK0, T_k^ov = Q_fc,k + ε0 + (b_0 − b_k).
- Add this as hypothesis family **H_ov**, crossed with d ∈ {0, −0.031}, to round 6's WP1 grid.
- Recompute s_h, worst case and max regret for SUB, SUB + drift (d = −0.031 and −0.020) and the round 6 WP1 candidate set.
- Also report the implied Δ_eff = b_0 − b_k per checkup, and compare it with the Δ ∈ {0, 0.4, 0.8} axis.
- If b_0 cannot be separated from the 45 °C effect at anchor 0, report H_ov with b_0 = median(b_1..b_7) as the main case and the measured b_0 as a sensitivity.
- Also give a diagnosis-informed prior over (Δ, f) updated by the WP1 classification, with the update rule written in the protocol before computing.

**Done:** the table, the P1–P4 results with plots (offsets vs dwell and vs r_j; anchor vs recharge step → top), the classification, the H_ov grid results, the updated prior, plus the common criteria.

### WP2 — Temperature-weighted √t for the CK2 gap branch (cap 2.5 h)

**Designs** (registered). Replace t in the √t branch with effective time t_eff(t) = ∫ AF(T(τ)) dτ from CK0, AF(T) = exp[(Ea/R)(1/318.15 − 1/(T + 273.15))], i.e. normalised to 45 °C. T(τ) is the chamber setpoint of visible segments; for unobserved intervals use a registered assumption.
- **T_main:** Ea = 20.6 kJ/mol (Schimpe 2018, Sony LFP calendar); checkup gaps at 25 °C; missing segment 3 at 45 °C (public alternation schedule — the only allowed non-data input, as in round 6).
- **T_ea37:** Ea = 37.3 kJ/mol (Yagci 2025), otherwise as T_main.
- **T_gap45:** checkup gaps at 45 °C, otherwise as T_main.
- **T_seg25:** segment 3 at 25 °C, otherwise as T_main (sensitivity only).
- **R_p044:** calendar time with p = 0.44 (fitted on all anchors, hence **non-causal**; reference only, never selectable).
- Everything else is identical to SUB (p = 0.5, 10-day gap rule, same anchors and ε).

**Causal evaluation first** (commit before the real run):
- Run every design on all (scenario, k) cases from `sqrt_branch_cases.csv` outside the real scenario, plus the full pseudo (PG1, PG2, PC5, PC10) and cold-start (CS, CSE) means at Δ = 0.4, exactly as round 6 computes them.
- **Exit rule:** if fewer than 4 non-real cases take the `sqrt_gap` branch, there is no causal test. Mark WP2 "exited: no causal analogue", still report the real-scenario numbers as exposed, and recommend keeping SUB.

**Real evaluation:** proxy MAE/MAX at Δ 0/0.4/0.8 and per-checkup errors (exposed-CK2). Also give the WP1-grid max regret, from round 6's grid plus H_ov if WP1 is done.

**Also report:**
- the TUM consistency check: on the 6 comparable TUM conditions, the median ratio of true to predicted increment for p = 0.5 is 0.87. State how much of that gap each design closes for this pack's CK2 (arithmetic only, no fitting);
- the CK2 SOH of every design.

**Gates against SUB (registered):**
- **G-gapcases:** mean absolute error over the non-real `sqrt_gap` cases ≤ SUB − 0.005 pp;
- **G-pseudo:** pseudo mean ≤ SUB + 0.005;
- **G-coldstart:** ≤ SUB + 0.005;
- **G-hyp:** grid max regret ≤ SUB + 0.005;
- **G-causal:** bit-identical output with all post-cut data replaced by noise, on all 8 checkups and the gap cases;
- **G-impl:** a numpy/pandas candidate class within 0.001 pp of the research implementation; `validate_submission.py` passing on a copy of the archived `21a7a55` package under the Python 3.11 venv (create `cache/venv311` as round 6 did); full run < 30 min.

**Decision (registered):**
- **recommend switching** only if T_main passes all gates;
- otherwise **keep SUB** and report the CK2 risk range (SUB vs T_main vs T_ea37), stating the evidence class of each.
- A design other than T_main may be named as an alternative only if it passes every gate **and** T_main fails G-gapcases by less than 0.005 pp; label it as such.
- Never wire anything.

**Done:** protocol, causal results committed before real, real results, gates table, CK2 table, a candidate class and checks only if a design passes every gate, plus the common criteria.

### WP3 — ε drift on the Yagci 180 Ah cycling cells (cap 2 h)

**Qualification audit** (before any drift number):
- From round 6's Yagci files (read in place, `python3 -I`) and the paper's protocol (`04_全文精读_9篇.md` and round 6 `wp4/REPORT.md`), document for the 4 cycling cells (35/50 °C, 0.28C CC-CV full cycles):
  - the checkup (RPT) protocol: 20 °C, 50 A CC-CV, second cycle;
  - whether the per-cycle sheet gives charge Ah from empty for the first operating cycles after each RPT;
  - the temperatures;
  - the 2 cells per condition.
- Storage cells have no operating charge and are excluded by design.
- **Exit rule:** if per-cycle charge Ah after each RPT is not available for ≥ 2 cells with ≥ 3 RPTs each, mark WP3 "exited: not qualifying" and keep d = −0.031 as round 6 did.

**Estimand:** for each cell and checkup j ≥ 1, ε_j = C_RPT,j (discharge capacity at the RPT, as used in round 6's table) − Q_ch,j, where Q_ch,j is the first full operating charge after RPT j (charge Ah to the CV end), both scaled to a 102 Ah cell by C_nom = 180 Ah. Main variant: the first operating charge. Sensitivity: the mean of the first three. Fade L_j = C_RPT,0 − C_RPT,j on the same scale.
- **Drift:** d_cell = OLS slope of ε_j on L_j (needs ≥ 3 points), with a leave-one-checkup-out range.
- **Temperature confound:** the RPT is at 20 °C and cycling at 35/50 °C. Report ε_0 per temperature; the slope d is the target, not the level.

**Pooling (registered):** combine d from LIC (−0.035), Gotion (−0.031) and the Yagci cells (one value per temperature group, mean of its 2 cells). Report the median, the range and a leave-one-dataset-out median.

**Recommendation rule for round 6's P_drift probe (registered):**
- If the Yagci group values are within [−0.05, −0.015], keep d = −0.031.
- If both are within (−0.015, +0.01), recommend d = −0.020 and state the disagreement.
- If any is > +0.01, flag "drift sign not robust" and recommend that P_drift be probed only after the other probes.
- Also produce SUB + drift SOH tables for the recommended d and its grid scores (round 6 grid, plus H_ov if WP1 is done).

**Also record:** TUM kxh42bfgtj (2018) and Mendeley 6hgyr25h8d (2020) were checked and carry no charge capacity, so they cannot test ε. Cite `04_全文精读_9篇.md`.

**Done:** audit, ε tables and plots, pooled d, the recommendation, SOH tables, plus the common criteria.

### WP4 — Reichert 2013 rest recovery (optional, cap 0.5 h)

- Look for a PDF of Reichert et al., *J. Power Sources* 239 (2013) 45–53, doi 10.1016/j.jpowsour.2013.03.053, in `/Users/shane/Desktop/` (top level) and in `/Users/shane/Desktop/Arena_1013_model/research/phase2_literature_refresh_20261016/papers/`. Never download it.
- If found: read it in place and record:
  - the cells (LFP and NMC), rest SOC, temperatures and durations;
  - the recovered capacity vs rest time (Epding 2019 reports up to 0.6 % after 5 days at 20 °C for LFP);
  - the fitted time constant.
  Compare with the WP1 offset (about 0.4 %, gone within about 5 days) and with the overhang interpretation.
- If not found: mark WP4 "skipped: no full text".
- **Done:** a short bilingual `wp4/REPORT.md` (no protocol needed), plus common criteria 3–4.

### WP5 — Synthesis (cap 1 h)

- **Decision table:**
  - CK2: keep SUB / switch to T_main, with the evidence class;
  - post-anchor offset interpretation: overhang supported / partly / not;
  - recommended d for P_drift;
  - whether round 6's probe order (P_drift → P_stress_early → P_start) should change, and why.
- **`report_material/risk_addendum.md`** (bilingual, ready to paste into the package REPORT by the user; **never edit the package**). It covers:
  - the overhang interpretation and its evidence;
  - why the memory effect is excluded;
  - ε as a protocol effect (Smith 2011 bound);
  - the CK2 time-law risk with numbers;
  - the drift estimate.
  Use 4–6 short paragraphs and cite with DOIs.
- **`FINAL_REPORT.md` and `README.md`** (bilingual): conclusions first; all WPs; risks; reproduction commands; environment.
- **Done:** the global Done (§0).

## 5. Caps and order

| WP | Content | Cap | Depends on |
|---|---|---|---|
| 0 | setup, re-baselining, √t inventory | 0.5 h | — |
| 1 | overhang state effect | 2.5 h | 0 |
| 2 | temperature-weighted √t | 2.5 h | 0 (uses 1's H_ov if done) |
| 3 | ε drift on Yagci | 2 h | 0 (uses 1's H_ov if done) |
| 4 | Reichert 2013 (optional) | 0.5 h | — |
| 5 | synthesis | 1 h | 1–4 |

Recommended order: 0 → 1 → 3 → 2 → 4 → 5. At a cap, write up what exists (including "inconclusive"), commit, push and mark the WP capped.

## 6. Prohibitions (summary)

- **Causality.** No data after CK_k for CK_k in any prediction. The public segment schedule is the only exception. WP1 diagnostics may use the full data because they predict nothing.
- **Selection.** Never use the real proxies to select. No change of a registered main after its results. Exposed and non-causal designs are labelled and never selected.
- **Proxies.** Never present proxies or H_ov as hidden truth; never reconstruct CK1–CK7 from external sources.
- **Files and git.** Do not edit any submission package, earlier study, the literature-refresh folder, round 6's worktree or any external checkout. Push only to this branch; never force-push. Do not commit PDFs.
- **No questions.** Never ask the user; record decisions and continue.

---

<a id="zh"></a>

# 第七轮：文献驱动的检验——overhang 状态效应、CK2 的温度加权 √t、Yagci 数据上的 ε 漂移——执行 Prompt

> **语言：** [English](#en) · 中文

编写日期：2026-10-16。本文自成一体。英文部分是执行文本，中文部分是给读者的翻译；两者不一致时以英文为准。

工作分成 **WP0–WP5 六个工作包**。每个都有自己的“完成标准”，可以作为单独的 `/goal` 运行。WP0 必须最先完成；WP1、WP2、WP3 互相独立；WP4 可选；WP5 放在最后。

## 0. 工作方式（所有工作包）

- **无人值守。** 不要停下来提问。遇到未定的决策，选择遵守本文全部规则前提下最保守的方案，记入 `notes/DECISIONS.md`，然后继续。
- **重启。** 每一步之后都更新 `notes/STATUS.md`：工作包、已完成、下一步、最近一次提交。重启后先读 `notes/STATUS.md` 和 `notes/DECISIONS.md` 再接着做，不要重做已完成的工作包或步骤。
- **诚实优先于目标。** 负面、无定论或“按规则退出”都是有效结果。绝不在真实代理上调参。本轮只产出**证据和建议**，绝不改动提交。
- **任何工作包的“完成”** 都要满足下面的通用标准，再加上该工作包自己的清单：
  1. 登记的协议（`wpN/protocol.json` + `wpN/protocol.sha256`）在其评估输出**之前**提交；
  2. 有双语、结论在前的 `wpN/REPORT.md`；
  3. `notes/STATUS.md` 把该工作包标为完成、到达上限、跳过或已退出，并附一行结果；
  4. 所有提交都已推送到 `origin exp/phase2-r7-lit-checks-20261016`，`git status` 没有未提交的研究文件。
- **整体完成**（整个 prompt）：WP0–WP5 都已完成、到达上限、跳过或按登记规则退出；`FINAL_REPORT.md` 和 `README.md` 已写好（双语，结论在前）；通用标准 3–4 成立。

## 1. 工作区、隔离与 git

- **worktree 与分支（若不存在，在 WP0 中创建；可重复执行）。**
  - 基点：第六轮在 `exp/phase2-r6-robust-20261016` 上的最终提交。编写时为 `e144086`；以分支最新提交为准，并记下其哈希。
  - 创建命令：`git -C /Users/shane/Desktop/Arena_1013_model worktree add /Users/shane/Desktop/Arena_1016_r7_lit -b exp/phase2-r7-lit-checks-20261016 <基点>`。若 worktree 或分支已存在，确认其历史包含 `<基点>` 后直接复用。
  - 只在 `/Users/shane/Desktop/Arena_1016_r7_lit` 中工作。研究目录为 `research/phase2_r7_lit_checks_20261016/`。
- **可复用的代码（本 worktree 从第六轮开始，因此都在）：**
  - 第六轮研究 `research/phase2_r6_robust_20261016/`：`src/`（5C 运行器与 harness 副本、`common6.py`）、`sources/`（归档的 `v3.py`、回弹诊断、提交的 `my_model`）、`wp1/`（18 个假设的网格与得分 s_h）、`wp3/`（3a 起点审计、3b 漂移、3c 路径偏移及输出）、`wp4/`（Yagci 表构建脚本与表）；
  - 第三轮 harness `research/phase2_round3_models_20261014/src/harness.py`（场景 real、PG1、PG2、PC5、PC10）；
  - V2 的 `research/phase2_v2_phase_matched_20261013/src/v2.py` 和事件提取 `research/phase2_anchor_step_20261013/src/events.py`。
  - 要改的代码复制到本研究中，只改副本。
- **本 worktree 之外的只读来源。** 绝不 `cd` 进去，也绝不写入：
  - **提交分支** `exp/phase2-anchor-step-20261013` 的提交 `21a7a55`，位于 `/Users/shane/Desktop/Arena_1013_model`。只能用 `git -C … show` / `git -C … archive`。其中的 `my_model/model_template.py` 是**提交的模型 SUB = V2+√t**。按第六轮的做法把提交包解压到 `cache/submitted_package/`。
  - **文献更新**目录 `/Users/shane/Desktop/Arena_1013_model/research/phase2_literature_refresh_20261016/`（可能尚未提交；逐个文件复制并记录 SHA256）：`03_新文献综述.md`、`04_全文精读_9篇.md`、`tum_calendar_check/`（脚本、`RESULTS.md`、`outputs/`）、`papers/README.md`。**不要**把 `papers/` 里的 PDF 复制进 git（版权）；需要时原地阅读。
  - **第六轮缓存**（在那边被 git 忽略）：`/Users/shane/Desktop/Arena_1016_r6_robust/research/phase2_r6_robust_20261016/cache/downloads/yagci/`（`Data.zip`、`readme.md`、`unzipped/`）。用 `python3 -I` 原地读取，绝不修改。若不存在，按 WP3 的退出规则处理。
  - **外部数据集：** `/Users/shane/Desktop/Arena_1013_model/external_data/`（`DATA_MANIFEST.md`）。
  - **TUM 日历老化数据：** `/Users/shane/Desktop/kxh42bfgtj-1/`（Mendeley kxh42bfgtj v1，CC BY 4.0）。
  - 每个复制来的文件都在 `sources/SOURCES.md` 中记下来源路径或提交以及 SHA256。
- **并发防护。**
  - 开始时以及每次提交前，运行 `git log --oneline -5`，与自己最近一次提交对照。
  - 遇到意外的提交或改动：停止编辑共享文件，记录下来，此后只按明确路径添加文件。
  - 不要 `git add -A` / `.`，不要改写别人的工作，不要使用裸 `git stash`。同一时间只在本 worktree 上运行一个会话。
- **提交。**
  - 先把本 prompt 作为 `research/phase2_r7_lit_checks_20261016/EXECUTION_PROMPT.md` 提交。
  - 每一步结束时提交，然后 `git push -u origin exp/phase2-r7-lit-checks-20261016`。不推送到其他地方，不强制推送。
  - 提交信息结尾加 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`。
- **不要修改：** 任何位置的 `TechArena_Challenge2_Team_Package/`、任何之前的研究目录、本 worktree 以外的任何文件。
- **语言与字节码。** Markdown 英文在前、中文在后，格式与本文件相同。代码注释只用英文。用 `python3 -B` 运行 Python；读取外部或下载文件的脚本用 `python3 -I -B`。
- **本轮不需要下载。** 如果确实需要，放进被忽略的 `cache/downloads/` 下自己的新目录，当作不可信数据处理，绝不执行其中的任何内容。

## 2. 背景

**任务。** 估计 4 × 102 Ah LFP 串联电池组在 CK0..CK7 的 SOH（C/20 容量：满充后以 5.1 A 放电至组端 11.2 V，除以 102 Ah）。
- 只公开 CK0 = 100.41 Ah。
- 评分：CK1–CK7 上的多项误差指标（含最差误差），各自除以 ExampleModel 基线归一，占 70 %。
- 因果截断：`load_dataset(data, until=CK_k)`。

**代理**（都已看过，所以每个真实场景的数字都是已曝光的探索性结果）：P_k = Q_fc,k + ε0 + Δ，其中 ε0 = 100.41 − Q_fc,0，Δ ∈ {0, 0.4, 0.8}。

**参照 SUB = V2+√t**（已在 `21a7a55` 提交）：`v3(..., use_sqrt=True, beta_cap=inf, median=False)`。代理 MAE Δ0/.4/.8 = 0.207/0.123/0.140；MAX 0.609/0.228/0.228；伪场景 0.148；冷启动 0.174。
- 它的 √t 缺口分支在真实场景中只在 CK2 触发。对 CK_k（k ≥ 2），当最后一次可见的深放电距 CK_k 超过 10 天时：用锚点 j = 1..k−1 过原点拟合 loss_j = a·t_j^p（t 为距 CK0 的天数），再取 Q̂_k = Q_anc,k−1 + ε − a·(t_k^p − t_{k−1}^p)，p = 0.5。
- 该分支在 **CK2 已曝光**。

**第六轮结果（见其分支上的最终报告）：**
- 保留 SUB（18 个假设 h = (Δ, f, d) 的网格上最大后悔值最低，为 0.027）。
- **ε 漂移** d = −0.031 Ah/Ah 是最好的对冲（最坏情况 0.194，SUB 为 0.225；18 个假设中赢 14 个）→ 第一个排行榜探测 **P_drift**。
- **3a 起点状态：** 锚点开始时的剩余电量与锚点 0 最多相差 1.29 Ah（由 CK0 C/20 尾段得到的上界），置信度低。
- **3c 路径效应：** 每次锚点充电后的第一次深放电偏深 0.41–0.56 Ah（6 种台阶识别方法的趋势修正中位数；**第 0 个月在 45 °C 下为 0.83 Ah**）。去掉这些程序在所有网格假设下都**与代理冲突**。
- WP2/WP4 的应力模型候选都没有通过门槛。

**本轮要检验的文献发现（见 `04_全文精读_9篇.md`）：**
1. **overhang 状态效应**（Lewerenz 2017 JPS 345:254；Lewerenz 2018 JES 18:149；Gyenes 2015；Naumann 2018）。
   - 负极处于近空状态时，锂会从无对电极的 overhang 流回活性区。这会**增加可循环锂和容量**，并拉长石墨台阶 → 满充端的距离。
   - 回到高 SOC 后，锂又流回 overhang。overhang 占负极 5.7–9 %；交换过程的 Ea ≈ 64.5 kJ/mol；整块 overhang 在 50 °C 下约 150 天完全补偿，但靠近边缘的部分更快。
   - 本题每次检查后，电池组都在近空（2.89–3.00 V/cell）下停放，然后才做锚点充电。这会**同时**抬高锚点 Q_fc 和第一次深放电，也能解释为什么只去掉那次程序会和以锚点为基础的代理冲突。
   - LFP 记忆效应（Sasaki 2013）基本排除：它主要出现在充电方向，一次满充即清除，而每个深放电程序都从满充开始。均匀化（Lewerenz 2017 DVA）会让台阶变尖，而观测中没有。
   - **未决问题：** 时间常数。偏移在下一次程序（约 5 天后）已经消失。
2. **√t 的温度加权时间**（Naumann 2018 JES 17:153）。
   - 动态日历老化实验表明条件的先后顺序无影响，速率取决于当前状态，所以时间应按 Arrhenius 加权的“虚拟时间”累加。
   - CK0→CK1 约 20 天在 45 °C（段 1）。CK1→CK2 是 8 天 25 °C（段 2），加上缺失的段 3（2 月 19 日–3 月 11 日）；按公开的交替规律（短段 25 °C / 长段 45 °C），段 3 为 45 °C。
   - 25 °C 的天数按 1/AF 折算（Ea 20.6–37.3 kJ/mol 时 AF 为 1.7–2.6），SUB 的 CK1→CK2 增量缩小 6–9 %，即 CK2 SOH 上调 0.08–0.12 pp。
   - 另一条独立证据：TUM Sony LFP 数据（`tum_calendar_check/RESULTS.md`）显示，在早期衰减可比的 6 个条件上，√t 把第 25 → 56 天的损失高估了中位 13 %（中位比值 0.87，范围 0.81–1.02）。
3. **ε 不是库仑效率效应**（Smith 2011 JES 158:A1136）。
   - 本题一次约 5 h 的满充中副反应只消耗约 0.007 Ah，所以 ε 及其漂移来自协议和端点状态。
   - 外部漂移估计只依据 LIC 280 Ah（−0.035）和 Gotion 53 Ah（−0.031）。第六轮缓存中的 Yagci 180 Ah 循环芯（带逐循环表）是尚未使用的第三个来源。
   - TUM 数据无法检验 ε：没有公开充电容量。

## 3. 通用规则

1. **先登记，再运行。** 在计算任何会用于该工作包决策的数字之前，先在 `wpN/protocol.json` 中登记（附 SHA256）。WP2 要先运行并提交因果场景的结果，再跑真实场景。
2. **选择绝不使用真实代理。** 每个登记设计（包括落选的）都要报告真实场景结果。
3. **已曝光的改动。** WP2 的设计只通过 √t 分支起作用。真实场景中该分支只在 CK2 触发，而 CK2 的误差在这些设计提出时已知，所以它们在真实场景 CK2 上的收益标为 `exposed-CK2`，不算证据。因果证据只来自分支在未曝光情况下触发的场景（WP2）。
4. **只用于排行榜判断的输出。** 标签假设的推论（WP1）和漂移数值（WP3）绝不作为代理上的改进来评分。它们以 SOH 表的形式报告，并放在第六轮的假设网格上（在本文要求处扩展网格）。
5. **小样本。** 锚点只有 7–8 个。WP1 的所有统计量都是描述性的：报告效应量、符号计数和精确置换 p 值，绝不只给“显著”结论。
6. **实现。** 缓存键包含所有参数；因果性检查比较精确浮点数；任何偏离都在运行前登记。
7. **接入。** 绝不把任何东西接入真实的 `my_model/`。候选类只在 `cache/package_copy_*` 的副本上检查。

## 4. 工作包

### WP0 — 准备与重新确定基线（上限 0.5 h）

- 若 worktree 不存在则创建（§1），并建立 `notes/STATUS.md`、`notes/DECISIONS.md`、`.gitignore`（`cache/`）和 `sources/`。
- 复制只读来源（§1），写好附 SHA256 的 `sources/SOURCES.md`。
- **用第六轮的代码复现：**
  - SUB 在 Δ = 0.4 时：MAE 0.123，MAX 0.228，伪场景 0.148，冷启动 0.174；
  - 第六轮 WP1 中 SUB 的最大后悔值（0.027）；
  - 第六轮 3c 的逐锚点路径偏移（`wp3c_path_offsets.csv`）；
  - 3a 起点状态表。
- **清点 √t 分支。** 对 real、PG1、PG2、PC5、PC10、CS、CSE 中的每个场景，列出 SUB 走 `sqrt_gap` 分支的每个（场景, k），存为 `wp0/outputs/sqrt_branch_cases.csv`。WP2 依赖这张表。
- **完成标准：** 全部复现误差在 0.001 pp 以内（SUB 复现失败则停止整个运行），完成清点，并满足通用标准。WP0 不需要协议；`wp0/REPORT.md` 简短即可。

### WP1 — 锚点后偏移是不是 overhang 状态效应？（上限 2.5 h；不改模型）

**逐锚点表**（锚点 0..7，使用全部运行数据；这些是诊断，不是预测，所以不受因果截断限制）。各列：
- (a) **近空停放的代理量**：从 CK_k 之前最后一个运行采样点到锚点 k 开始充电的小时数；另记静置小时数，以及锚点开始前的组端和各芯静置电压；
- (b) 第六轮 3a 的剩余电量 r_j（上界和一半上界两种）；
- (c) 第六轮 3c 的锚点 k 之后第一次深放电的**放电方向偏移**（趋势修正，6 种台阶方法及其中位数）；
- (d) 锚点 k 之后**第二次**深放电的同一偏移；
- (e) **锚点充电内部的充电方向台阶 → 满充端距离**（用 `charge_step_split`，2 Ah 平滑）；
- (f) 锚点 k 之后前两次深放电程序的回充中的同一距离。这些回充从满充以下约 56 Ah 开始，会在充电方向上越过台阶。用与 `charge_step_split` 相同的方法定位，从 CV 末端起量，这样起点深度不影响结果。
- (g) 从锚点开始到第一次深放电期间的设定温度。

写入 `wp1/outputs/anchor_state_table.csv`。

**登记的预测**（overhang 状态效应 vs 程序路径效应）。P1–P4 用锚点 1..7；锚点 0 因磨合、出厂状态和 45 °C 单独报告。
- **P1 — 锚点本身也带有偏移。** e_k = (e) − (f) 的中位数。预测：各锚点 e_k 的中位数 ≥ +0.20 Ah，且 7 个中至少 5 个 e_k > 0。程序路径效应预测 e_k ≈ 0。
- **P2 — 依赖停放时长。** (c) 中位数与 (a) 的 Spearman ρ ≥ +0.5，附精确置换 p 值。
- **P3 — 越空，抬高越多。** (c) 中位数与 r_j（上界）的 Spearman ρ ≤ −0.5，附精确置换 p 值。
- **P4 — 快速衰减。** 7 个锚点中至少 5 个满足 (d) − 趋势 ≤ 0.15 Ah。这一条检验时间常数方面的反对意见，不作为支持判据。

**分类（登记）：**
- P1 成立且 P2/P3 至少一条成立 → **支持**；
- 只有 P1 成立 → **部分支持**；
- P1 不成立 → **不支持**。

无论结果如何，都要报告 P4 和第 0 个月的数值（45 °C 下放电方向偏移 0.83 Ah），并做简短的物理讨论：用 Lewerenz 2018 的 Ea = 64.5 kJ/mol 比较 25 °C 与 45 °C 下的预期交换速度，说明第 0 个月是否一致。

**推论分析（只用于排行榜判断，登记）：**
- 设 b_k 为锚点抬高量的估计（P1 成立时取 e_k，否则取 0）。如果隐藏的 C/20 是在近空停放**之前**测的（最可能的顺序：运行结束 → 检查，先满充再 C/20 放电 → 停放 → 锚点），那么隐藏容量不含这部分抬高。于是 Q_CK,k = Q_fc,k − b_k + c；由于 ε0 在 CK0 定义，T_k^ov = Q_fc,k + ε0 + (b_0 − b_k)。
- 把它作为假设族 **H_ov**，与 d ∈ {0, −0.031} 交叉，加入第六轮的 WP1 网格。
- 对 SUB、SUB + 漂移（d = −0.031 和 −0.020）以及第六轮 WP1 的候选集，重新计算 s_h、最坏情况和最大后悔值。
- 同时报告每个检查点隐含的 Δ_eff = b_0 − b_k，并与 Δ ∈ {0, 0.4, 0.8} 这一轴比较。
- 如果锚点 0 的 b_0 无法与 45 °C 效应分开，以 b_0 = median(b_1..b_7) 作为 H_ov 主情形，实测 b_0 作为敏感性分析。
- 再给出按 WP1 分类结果更新后的 (Δ, f) 诊断先验；更新规则在计算前写入协议。

**完成标准：** 逐锚点表；P1–P4 结果及图（偏移对停放时长、偏移对 r_j、锚点与回充的台阶 → 满充端距离对比）；分类；H_ov 网格结果；更新后的先验；并满足通用标准。

### WP2 — CK2 缺口分支的温度加权 √t（上限 2.5 h）

**设计**（登记）。把 √t 分支中的 t 换成等效时间 t_eff(t) = ∫ AF(T(τ)) dτ（从 CK0 起积分），AF(T) = exp[(Ea/R)(1/318.15 − 1/(T + 273.15))]，即以 45 °C 归一。T(τ) 取可见运行段的设定温度；未观测的区间使用登记的假设。
- **T_main：** Ea = 20.6 kJ/mol（Schimpe 2018，Sony LFP 日历老化）；检查间隔按 25 °C；缺失的段 3 按 45 °C（公开的交替规律——与第六轮一样，这是唯一允许的非数据输入）。
- **T_ea37：** Ea = 37.3 kJ/mol（Yagci 2025），其余同 T_main。
- **T_gap45：** 检查间隔按 45 °C，其余同 T_main。
- **T_seg25：** 段 3 按 25 °C，其余同 T_main（只作敏感性分析）。
- **R_p044：** 日历时间、p = 0.44（用全部锚点拟合得到，因此**不符合因果性**；只作参照，永不入选）。
- 其他一切与 SUB 相同（p = 0.5、10 天缺口规则、相同的锚点和 ε）。

**先做因果评估**（在跑真实场景之前提交）：
- 在 `sqrt_branch_cases.csv` 中所有非真实场景的案例上运行每个设计；同时按第六轮的算法，给出 Δ = 0.4 时全部伪场景（PG1、PG2、PC5、PC10）和冷启动场景（CS、CSE）的平均值。
- **退出规则：** 若走 `sqrt_gap` 分支的非真实案例少于 4 个，就没有因果检验可做。把 WP2 标为“退出：无因果类比”，仍按已曝光报告真实场景的数字，并建议保留 SUB。

**真实场景评估：** Δ 0/0.4/0.8 下的代理 MAE/MAX 和逐检查点误差（exposed-CK2）。另给出网格最大后悔值：用第六轮的网格，若 WP1 已完成则加上 H_ov。

**还要报告：**
- TUM 一致性检查：在 TUM 的 6 个可比条件上，p = 0.5 时实测增量与预测增量之比的中位数为 0.87。说明每个设计对本题 CK2 弥补了这一差距的多少（只做算术，不做拟合）；
- 每个设计的 CK2 SOH。

**相对 SUB 的门槛（登记）：**
- **G-gapcases：** 非真实 `sqrt_gap` 案例上的平均绝对误差 ≤ SUB − 0.005 pp；
- **G-pseudo：** 伪场景平均 ≤ SUB + 0.005；
- **G-coldstart：** ≤ SUB + 0.005；
- **G-hyp：** 网格最大后悔值 ≤ SUB + 0.005；
- **G-causal：** 截断后的数据全部换成噪声时，在全部 8 个检查点和缺口案例上输出逐位不变；
- **G-impl：** numpy/pandas 实现的候选类与研究实现相差不超过 0.001 pp；在 Python 3.11 虚拟环境（按第六轮做法建在 `cache/venv311`）中，于归档 `21a7a55` 提交包的副本上通过 `validate_submission.py`；完整运行 < 30 分钟。

**决策（登记）：**
- 只有 T_main 通过全部门槛时才**建议切换**；
- 否则**保留 SUB**，并报告 CK2 的风险范围（SUB、T_main、T_ea37），注明各自的证据类别。
- T_main 以外的设计只有在通过全部门槛、**且** T_main 只以不到 0.005 pp 的差距未通过 G-gapcases 时，才可以作为备选列出，并如实标注。
- 绝不接入。

**完成标准：** 协议；在真实场景之前提交的因果结果；真实场景结果；门槛表；CK2 表；只有当某设计通过全部门槛时才做候选类及其检查；并满足通用标准。

### WP3 — 在 Yagci 180 Ah 循环芯上检验 ε 漂移（上限 2 h）

**资格审查**（在计算任何漂移数字之前）：
- 根据第六轮的 Yagci 文件（原地读取，`python3 -I`）和论文的协议（`04_全文精读_9篇.md` 及第六轮 `wp4/REPORT.md`），对 4 只循环芯（35/50 °C，0.28C CC-CV 满循环）记录：
  - 检查（RPT）协议：20 °C、50 A CC-CV、取第二个循环；
  - 逐循环表是否给出每次 RPT 之后最初几个运行循环从空态充入的 Ah；
  - 温度；
  - 每个条件 2 只芯。
- 存储芯没有运行充电，按设计排除。
- **退出规则：** 若不到 2 只芯、每只至少 3 次 RPT 有 RPT 后的逐循环充电 Ah，就把 WP3 标为“退出：不合格”，并像第六轮一样沿用 d = −0.031。

**估计量：** 对每只芯和每次检查 j ≥ 1，ε_j = C_RPT,j（RPT 的放电容量，与第六轮表中所用一致）− Q_ch,j，Q_ch,j 是 RPT j 之后第一次完整运行充电（充到 CV 末端的 Ah），两者都按 C_nom = 180 Ah 折算到 102 Ah 的电芯。主变体用第一次运行充电；敏感性分析用前三次的平均。衰减 L_j = C_RPT,0 − C_RPT,j，同样折算。
- **漂移：** d_cell = ε_j 对 L_j 的 OLS 斜率（至少 3 个点），并给出逐一剔除检查点的范围。
- **温度混杂：** RPT 在 20 °C，循环在 35/50 °C。按温度报告 ε_0；目标是斜率 d，不是水平。

**合并（登记）：** 合并 LIC（−0.035）、Gotion（−0.031）和 Yagci 循环芯（每个温度组一个值，取其 2 只芯的平均）的 d。报告中位数、范围和逐一剔除数据集的中位数。

**对第六轮 P_drift 探测的建议规则（登记）：**
- 若 Yagci 两个温度组的值都在 [−0.05, −0.015] 内，保持 d = −0.031；
- 若都在 (−0.015, +0.01) 内，建议 d = −0.020 并说明分歧；
- 若任一 > +0.01，标注“漂移符号不稳健”，并建议 P_drift 排在其他探测之后。
- 同时给出所建议 d 下 SUB + 漂移的 SOH 表及其网格得分（第六轮网格，若 WP1 已完成则加上 H_ov）。

**另外记录：** 已核对 TUM kxh42bfgtj（2018）和 Mendeley 6hgyr25h8d（2020）两份数据，都没有充电容量，无法检验 ε。引用 `04_全文精读_9篇.md`。

**完成标准：** 资格审查；ε 表和图；合并后的 d；建议；SOH 表；并满足通用标准。

### WP4 — Reichert 2013 静置恢复（可选，上限 0.5 h）

- 在 `/Users/shane/Desktop/`（顶层）和 `/Users/shane/Desktop/Arena_1013_model/research/phase2_literature_refresh_20261016/papers/` 中查找 Reichert et al., *J. Power Sources* 239 (2013) 45–53（doi 10.1016/j.jpowsour.2013.03.053）的 PDF。绝不下载。
- **找到时：** 原地阅读，记录：
  - 电芯（LFP 和 NMC）、静置 SOC、温度和时长；
  - 恢复容量随静置时间的变化（Epding 2019 报告 LFP 在 20 °C 下静置 5 天后最多回升 0.6 %）；
  - 拟合的时间常数。
  再与 WP1 的偏移（约 0.4 %，约 5 天内消失）以及 overhang 解释比较。
- **没找到时：** 标为“跳过：无全文”。
- **完成标准：** 一份简短的双语 `wp4/REPORT.md`（不需要协议），并满足通用标准 3–4。

### WP5 — 综合（上限 1 h）

- **决策表：**
  - CK2：保留 SUB / 切换到 T_main，并注明证据类别；
  - 锚点后偏移的解释：overhang 支持 / 部分支持 / 不支持；
  - P_drift 建议采用的 d；
  - 第六轮的探测顺序（P_drift → P_stress_early → P_start）是否需要调整，以及原因。
- **`report_material/risk_addendum.md`**（双语，供用户直接粘贴进提交包的 REPORT；**绝不编辑提交包**）。内容包括：
  - overhang 解释及其证据；
  - 为什么排除记忆效应；
  - ε 是协议效应（Smith 2011 的量级界）；
  - CK2 时间律的风险及数字；
  - 漂移估计。
  写成 4–6 段短文，引用附 DOI。
- **`FINAL_REPORT.md` 和 `README.md`**（双语）：结论在前；所有工作包；风险；复现命令；环境。
- **完成标准：** 整体完成（§0）。

## 5. 上限与顺序

| WP | 内容 | 上限 | 依赖 |
|---|---|---|---|
| 0 | 准备、重新确定基线、√t 清点 | 0.5 h | — |
| 1 | overhang 状态效应 | 2.5 h | 0 |
| 2 | 温度加权 √t | 2.5 h | 0（若 WP1 已完成则用其 H_ov） |
| 3 | Yagci 上的 ε 漂移 | 2 h | 0（若 WP1 已完成则用其 H_ov） |
| 4 | Reichert 2013（可选） | 0.5 h | — |
| 5 | 综合 | 1 h | 1–4 |

建议顺序：0 → 1 → 3 → 2 → 4 → 5。到达上限时，把已有结果（包括“无定论”）写成报告，提交、推送，并把该工作包标为到达上限。

## 6. 禁止事项（汇总）

- **因果性。** 任何预测在预测 CK_k 时都不得使用 CK_k 之后的数据。公开的段时间表是唯一例外。WP1 的诊断不做预测，可以使用全部数据。
- **选择。** 绝不用真实代理做选择。登记的主设计在看到结果后不得更换。已曝光和不符合因果性的设计要标注，且永不入选。
- **代理。** 绝不把代理或 H_ov 当作隐藏真值；绝不从外部来源重建 CK1–CK7。
- **文件与 git。** 不要编辑任何提交包、之前的研究、文献更新目录、第六轮的 worktree 或任何外部签出。只推送到本分支；绝不强制推送。不要提交 PDF。
- **不提问。** 绝不向用户提问；记录决策后继续。
