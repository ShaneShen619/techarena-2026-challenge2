<a id="en"></a>

# Round 12: The ε Level on Our Own Pack — 45/25 °C Anchor-Top Offset and Shared-Bottom Test — Execution Prompt

> **Language:** English · [中文](#zh)

Written 2026-10-19. This document is self-contained. The English text is the execution text. The Chinese section is a translation for the reader; where the two differ, the English governs.

The work is split into **work packages WP0–WP4**. Each has its own *Done* list and can be run as a separate `/goal`.
- WP0 comes first and WP1 second.
- WP2 and WP3 depend only on WP1 and are independent of each other. Run them one after the other (one session per worktree).
- WP4 needs WP2 and WP3. `FINAL_REPORT.md` comes last.

## 0. Mode of work (all work packages)

- **Unattended.** Never stop to ask. When a decision is open, take the most conservative option that keeps every rule here, record it in `notes/DECISIONS.md`, and continue.
- **Restarts.** Keep `notes/STATUS.md` current after every step: WP, done, next, last commit. On a restart, read `notes/STATUS.md` and `notes/DECISIONS.md` first and resume from there. Never redo a finished WP or step.
- **Honesty over targets.** "Not identifiable" and "inconclusive" are valid outcomes. This round produces **measurements, intervals and a recommendation**. It never changes the submission, and it never computes an error against the Challenge 2 proxy labels P_k.
- **Done for any WP** means the common criteria below, plus that WP's own list:
  1. its registered protocol (`wp1/protocol.json` + `wp1/protocol.sha256`, and the registered code of §3 WP1) was committed **before** any of its evaluation outputs;
  2. its bilingual `wpN/REPORT.md` exists, conclusions first;
  3. `notes/STATUS.md` marks the WP done, skipped or exited, with a one-line result;
  4. every commit is pushed to `origin exp/phase2-r12-eps-level-20261019`, and `git status` shows no uncommitted study files.
- **Global Done** (whole prompt):
  - WP0–WP4 are each done or exited by a registered rule;
  - `FINAL_REPORT.md`, `README.md` and `wp4/R13_HANDOFF.json` exist (Markdown bilingual, conclusions first);
  - common criteria 3–4 hold.

## 1. Workspace, isolation, git

- **Worktree and branch.** Create them in WP0 if missing; the step is idempotent.
  - Base: `6525edf` on `exp/phase2-anchor-step-20261013` ("Wire the robust multi-variant cell-median step (A3) into the submission"). If the branch tip is newer, use the tip and record its hash.
  - Create: `git -C /Users/shane/Desktop/Arena_1013_model worktree add /Users/shane/Desktop/Arena_1019_r12_eps_level -b exp/phase2-r12-eps-level-20261019 <base>`. If the worktree or branch already exists, check that its history contains `<base>` and reuse it.
  - Work only in `/Users/shane/Desktop/Arena_1019_r12_eps_level`. The study directory is `research/phase2_r12_eps_level_20261019/`.
- **This prompt** currently lives, uncommitted, at `/Users/shane/Desktop/Arena_1013_model/research/phase2_r12_eps_level_20261019/R12_EXECUTION_PROMPT.md`. Copy it to `research/phase2_r12_eps_level_20261019/EXECUTION_PROMPT.md` in your worktree and commit it first. Do not commit, move or delete the original.
- **Read-only sources outside this worktree.** Never `cd` into them and never write to them. Record every copied file with its source ref or path and its SHA256 in `sources/SOURCES.md`. Read earlier rounds with `git -C /Users/shane/Desktop/Arena_1013_model show <ref>:<path>`:
  - round 11 `exp/phase2-r11-eps-transfer-20261018` (final `ff45b48`), under `research/phase2_r11_eps_transfer_20261018/`: `FINAL_REPORT.md`, `wp4/pack_drivers.csv`, `src/wp4_pack.py`, `wp5/R12_HANDOFF.json`;
  - round 8 `exp/phase2-r8-error-table-20261017`, under `research/phase2_r8_error_table_20261017/`: `DATA_DICTIONARY.md`, `outputs/table_anchors.csv`, `outputs/table_events.csv`, `outputs/table_cycles.csv`, `src/eventcurves.py`, `src/common8.py`;
  - round 5B `exp/phase2-r5b-electrode-model-20261014`: `research/phase2_r5b_electrode_model_20261014/FINAL_REPORT.md` (negative result, see §2);
  - on the base branch (already in your worktree): `research/phase2_rebound_diagnosis_20261015/` (first-program offset), `research/phase2_v2_phase_matched_20261013/` (25 → 45 °C step jump), `research/phase2_anchor_step_20261013/FINAL_REPORT.md`.
- **Challenge data:** `TechArena_Challenge2_Team_Package/data/` in your own worktree (`operation/`, `checkups/CK0_reference_discharge.csv.gz`, `checkups/evaluation_points.csv`, `DATA_DESCRIPTION.md`) and `CHALLENGE2_DESCRIPTION.pdf`.
- **Concurrency guard.**
  - At the start and before every commit, run `git log --oneline -5` and compare it with your last commit.
  - On an unexpected commit or change: stop editing shared files, record it, and add files by explicit path only.
  - Never use `git add -A` or `git add .`, never rewrite others' work, never use a bare `git stash`. Run only one session on this worktree at a time.
- **Commits.**
  - Commit at the end of every step, then run `git push -u origin exp/phase2-r12-eps-level-20261019`. Never push elsewhere and never force.
  - End every commit message with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Do not modify:** any `TechArena_Challenge2_Team_Package/` directory (anywhere), any earlier study directory, or any file outside this worktree. Model variants are built as copies under the git-ignored `cache/variants/`.
- **Language and bytecode.** Markdown is English first, Chinese second, in this file's layout. Code comments are English only. Run Python with `python3 -B`.
- **No downloads** in this round.

## 2. Context

**Task.** Estimate the SOH of a 4 × 102 Ah LFP series pack on CK0..CK7. SOH is the C/20 capacity divided by 102 Ah. Per the challenge PDF, the C/20 capacity is a 5.1 A discharge to pack 11.2 V "after a full charge"; the full-charge protocol is not stated.
- Only CK0 = 100.41 Ah is released. The causal cut is `load_dataset(data, until=CK_k)`. The PDF states that a public leaderboard is updated weekly.

**How the submission SUB uses ε.** SUB is `my_model/model_template.py` at the base commit.
- Every prediction built on a 25 °C anchor uses `q_anchor = Q_fc,k + ε0 + EPS_EXTRA_AH`.
  - ε0 = 100.41 − Q_fc,0 = 0.288 Ah comes from the 45 °C anchor 0.
  - `EPS_EXTRA_AH = 0.4` is an **assumption** (registered range {0, 0.4, 0.8} since the first anchor study).
- This moves CK2–CK7 together: 1 Ah of EPS_EXTRA = 0.98 pp. CK1 is built on CK0 = 100.41 directly and does not use it.
- The proxies are P_k = Q_fc,k + ε0 + Δ. Changing EPS_EXTRA moves the prediction and the proxy together, so **proxy scoring is blind to this question by construction**. That is why this round measures the offset from the pack's own data.

**Decomposition registered for this round.** Quantities are charge contents in Ah. Coulombic efficiency is neglected (round 11: T_CE flat, −0.0008 Ah/Ah in LIC).
- C20_k = F^CK_k − S_k: from the checkup's top state to the state at the end of its C/20 discharge.
- Q_fc,k = F^A_k − B_k: from the anchor's start state to the anchor's top (14.0 V CV ended at ≈ 5.1 A).

```
ε_k = C20_k − Q_fc,k = (F^CK_k − F^A_k) + (B_k − S_k)

EPS_EXTRA_true(k) = ε_k − ε_0
   = [F^A_0 − F^A_k]                T_top: top of the 45 °C from-empty anchor 0 minus top of a 25 °C from-empty anchor   (WP3)
   + [F^CK_k − F^CK_0]              change of the checkup top with ageing = the drift d (out of scope)
   + [a_0 − a_k],  a_k := S_k − B_k  bottom mismatch: > 0 if the anchor starts deeper than its C/20 ended               (WP2)
```

- **Hypothesis H_SB ("shared bottom").** The anchor starts from the state its checkup's C/20 discharge ended in, changed only by rest: a_k = 0. Under H_SB and at equal ageing, **EPS_EXTRA_true = T_top + a_0** for the relaxed 25 °C anchors. This round measures T_top and a_0 and tests H_SB as far as the data allow. For k ≥ 1 only a necessary condition can be tested, because S_k is not visible.
- **Prediction note (registered).** An anchor-specific bottom anomaly a_k^rel (deviation from the trend of the relaxed anchors) biases every prediction that uses anchor k as its base for a later checkup. This holds whether or not its own C/20 shared the anomaly, because the next checkup ends at a normal depth. For ε0 only the non-shared part a_0 = S_0 − B_0 matters.

**Facts already established.** Cite these, and re-verify them in WP0.
- **CK0 C/20 curve.** 2025-01-15 14:03:42 → 2025-01-16 09:44:56 at 5.10 A. It starts at 13.590 V under load, delivers 100.41 Ah, and ends with all four cells at 2.800–2.802 V.
- **Anchor 0** (segment 1, 45 °C).
  - The data start at 2025-01-19 19:10:56, 3.4 days after the C/20 ended, with only 0.5 h of rest.
  - The start voltage is 11.53–11.57 V and rising at +84–86 mV/h.
  - The CV phase lasts only ≈ 36 s (0.09–0.15 Ah).
  - 30 min after the CV end the pack reads 13.644 V, with cell3 at 3.53 V (top spread 264 mV).
  - Q_fc,0 = 100.122 Ah with the package integration.
- **25 °C anchors 1–7** (segments 2, 4, 6, 8, 10, 12, 14).
  - CV 1.17–1.44 Ah, I_end 5.09–5.10 A, pack 30 min after CV end 13.435–13.439 V, top spread 88 → 52 mV.
  - Start 11.80–11.95 V rising ≤ 6 mV/h, bottom spread 22 → 35 mV. The exception is anchor 3 (segment 6): 11.47 → 11.62 V, rising +52 mV/h.
  - Q_fc,1..7 = 97.00, 95.66, 94.64, 93.75, 93.08, 92.64, 91.95 Ah.
- **Exposed, exploratory** (2026-10-17, not in the repo). Anchor 3 needs ≈ 0.3–0.4 Ah more than its neighbours to reach pack 13.0/13.2 V and the charge-side step.
- **Exposed** (rebound study, 2026-10-15).
  - The first deep program after every from-empty anchor sits +0.39–0.46 Ah deeper, on all 6 detection variants, and the offset is gone by the next program.
  - After the anchor, the rest voltage at the top is 7–8 mV lower, and the next top-up needs ≈ +0.1 Ah.
- **Exposed** (V2 study, 2026-10-13). The discharge-side step depth jumps by ≈ +0.18 Ah at each 25 → 45 °C switch.
- **Month structure.** CK → 25 °C segment (2–3 blocks) → idle chamber switch (unrecorded, counters flat) → 45 °C segment (4 blocks) → CK.
  - Each block starts with a 20.4 A CC charge to 14.0 V and a CV phase to ≈ 5.1 A.
  - Then come 30 min of rest, a 30 min 20 A pulse, and the ≈ 55.9 Ah deep program (step current band −12.5…−8 A).
- **Visible 25 → 45 °C switches** (counters identical across the gap). There are five:
  - seg4 → seg5, ≈ 21.2 h idle;
  - seg6 → seg7, ≈ 6.9 h;
  - seg8 → seg9, ≈ 9.7 h;
  - seg10 → seg11, ≈ 25.3 h;
  - seg12 → seg13, ≈ 12.1 h.
  
  Month 1 has no 25 °C part, and segment 3 (month 2's 45 °C part) is missing.
- **Checkup windows** (last operating sample → start of the next anchor segment): CK1 ≈ 3.2 d, CK3 ≈ 3.1 d, CK4 ≈ 3.7 d, CK5 ≈ 5.4 d, CK6 ≈ 6.0 d, CK7 ≈ 4.3 d. CK2 is unknown (segment 3 is missing).
- **Integration.**
  - The cumulative counters book the 20 A pulse as charge. Integrate `current_A` with the package convention (`_integrated_ah`: samples with dt > 600 s contribute 0).
  - The per-block Ah balance between consecutive CV ends does not close (−0.3 to −1.1 Ah per block, the wrong sign for side reactions), so a measurement bias exists.
- **Resolution.**
  - The package's charge-side step locator (`_charge_step_to_top`) takes an argmax on a 0.25 Ah grid. It, and round 8's `bottom_to_step`/`step_to_top`, are therefore quantised at 0.25 Ah, which is too coarse for this round.
  - The package's discharge-side `dvdq` variant is on the same 0.25 Ah grid.
- **Round 5B.** Reconstructing absolute Q_C20 with literature OCPs is unidentifiable (8–10 Ah spans). Do not retry it.
- **Scope change.** The round 11 handoff named a top-of-charge drift model as round 12. The user chose to measure the ε **level** first; the drift model moves to round 13. Record this in `notes/DECISIONS.md`.

## 3. Work packages

### WP0 — Setup and fact sheet

1. Create or reuse the worktree, write `notes/STATUS.md`, `notes/DECISIONS.md` and `sources/SOURCES.md`, and commit this prompt.
2. Copy the sources listed in §1 into `sources/`, with their SHA256.
3. Run SUB on the full data with the package's own CLI, and save `wp0/SUB_SOH.csv`.
   - Build a research copy of `model_template.py` under `cache/variants/` whose only change is `EPS_EXTRA_AH`.
   - Save the SOH for EPS_EXTRA ∈ {0, 0.2, 0.4, 0.6, 0.8} to `wp0/eps_extra_sensitivity.csv`.
   - Check three things and explain any deviation: 0.4 reproduces SUB exactly; CK2–CK7 move by 0.98 pp per Ah; CK1 does not move.
4. Write the event catalogue `wp0/events.csv`. It lists every CCCV charge that reaches CV (pack ≥ 13.95 V, ending with 0 < I < 6 A), with:
   - segment, set point, and type (A = from-empty anchor, T = top-up);
   - start and end times, CV end current, CV Ah, rest before the charge;
   - pack and cell voltages at the CV end and 30 min later (just before the pulse);
   - whether there is any recording gap (dt > 60 s) before the next CV end;
   - the cumulative counters at both ends.
5. Write `wp0/FACTS.md`.
   - Verify each bullet under "Facts already established" in §2 with a number from the data. Mark it "confirmed" or give the corrected value.
   - Add the switch table: idle hours, counter change across the gap, and temperature before and after.
   - Add the checkup-window table.
   - Integration check: for each anchor, compare the package integration with the counter-based Q, and confirm how the counters book the pulse.

Do not compute any Ah balance, step location or ε-related estimate in WP0.

**Done:** worktree, notes, sources, `wp0/SUB_SOH.csv`, `wp0/eps_extra_sensitivity.csv`, `wp0/events.csv` and `wp0/FACTS.md` are committed and pushed.

### WP1 — Registration (no estimator values computed)

1. Write `wp1/protocol.json` containing:
   - the definitions of §2;
   - the locators of WP2 and the Ah chain of WP3, exactly as specified below, with every numeric constant fixed;
   - the gates and decision rules of §4, verbatim.
2. Implement the registered methods as `src/locators.py` (charge-side and discharge-side step locators, all variants) and `src/ahchain.py` (pairing, integration and the loss rule).
   - Test them only on **synthetic** curves (`src/test_registered.py`): a known step location must be recovered to within 0.02 Ah, and a known Ah offset to within 0.005 Ah.
   - Do not run them on the challenge data in WP1.
   - WP2 and WP3 import these modules unchanged. Any later change is a new registered version: record the reason in `notes/DECISIONS.md`, commit the new protocol hash, and label results computed before it.
3. Commit `protocol.json`, `protocol.sha256`, the two modules and the test **before** any WP2 or WP3 output.
4. In `wp1/REPORT.md`, add a table "what each outcome would mean": L1, L2, L3, the anchor-3 rule, and H_SB failed vs not failed.

**Done:** protocol, hash, registered code with passing synthetic tests, and `wp1/REPORT.md` are committed and pushed. No value computed on challenge data appears in any WP1 file.

### WP2 — Bottom: shared-bottom test and start anomalies

**B1. Start state and timing (descriptive).** Save `wp2/start_audit.csv`, one row per anchor, with:
- the checkup window (for k = 0, the exact time since the C/20 end) and the recorded rest;
- the start pack and cell voltages, and the slope over the last 30 min of rest (over the whole rest if shorter);
- the temperature at the start and its trend over the rest (is the pack still warming? This matters for segment 1);
- the cell spread at the start.

For each anchor, state whether its start is consistent with "C/20 end state plus rest only" (relaxed anchors: slope ≤ 6 mV/h). For each unrelaxed anchor, state what the timing implies:
- anchor 0 is unrelaxed 3.4 days after its C/20, which points to an unrecorded event or a thermal transient after the C/20;
- anchor 3: is its window short, or does it show something else?

**B2. Bottom section.** Locate the charge-side graphite step in each anchor's CC phase (I > 20 A), per cell, with the registered locators:
- **CL1:** dV/dQ maximum (charge direction) on a 0.05 Ah grid, moving-average smoothing 2 Ah, parabolic interpolation of the peak, search window 50–80 Ah from the charge start (the package's window).
- **CL2:** as CL1 with 1 Ah smoothing.
- **CL3:** as CL1 with 3 Ah smoothing.
- **CL4:** midpoint crossing, interpolated linearly between samples. The threshold is the mean of the median cell voltage on the lower plateau [s − 15, s − 5] Ah and on the upper plateau [s + 5, s + 15] Ah, where s is CL1's location.
- **CL5:** as CL4 with plateau windows [s − 20, s − 10] and [s + 10, s + 20] Ah.

Combine them as follows:
- A cell's value is the median over its finite variants (at least 4 needed). The anchor's value is the median over the cells.
- Define Q_bot,k = Ah from the charge start to the step, and Q_top,k = Q_fc,k − Q_bot,k.
- Report every locator's values. Check that rounding CL1 to the 0.25 Ah grid reproduces round 8's `bottom_to_step` to within 0.25 Ah.
- **Trend.** Fit a Theil–Sen line of Q_bot against days since CK0 over the relaxed 25 °C anchors {1, 2, 4, 5, 6, 7}. σ_LOO = 1.4826·MAD of the leave-one-out residuals.
- **Anomalies.**
  - a_3^rel = Q_bot,3 − trend(t_3), for anchor 3.
  - a_0^rel = Q_bot,0 − trend(t_0), for anchor 0. This is extrapolated and confounded by 45 °C, so it is diagnostic only.
- **Descriptive.** Among the relaxed anchors, relate the Q_bot residuals to the start voltage and the bottom spread. Under H_SB, the rising start voltage has no ε effect, because the checkup shares it.

**B3. CK0 split** (CK0 is the only checkup with a visible C/20 curve).
- On the CK0 curve, locate the discharge-side step per cell with the mirrored locator family:
  - DL1–DL3: maximum of −dV/dQ;
  - DL4–DL5: midpoint crossing with the plateau windows mirrored.

  This gives D_top,c (Ah from the C/20 start to the step) and D_bot,c = 100.41 − D_top,c. The cells reach the cutoff within 2 mV of each other.
- From anchor 0, take C_bot,c = Q_bot per cell and C_top,c = Q_fc,0 − C_bot,c. Then, with medians over the cells:

```
ε0 = (D_top − C_top) + (D_bot − C_bot)
D_bot − C_bot = −a_0 − h          h = step_ch − step_dis  (charge-side minus discharge-side step position)
D_top − C_top = (F^CK_0 − F^A_0) + h
```

- **Estimate h from the operation data at a common top**, over the 25 °C anchors k ∈ {1, 2, 4, 5, 6, 7}:
  - **h1_k = D1_k − C_top,k.** D1_k is the step depth of the first deep program after anchor k, which discharges from the anchor's own top. This value carries the first-program offset.
  - **h2_k = D2_k − C_top,k − (F^T2 − F^A_k).** D2_k is the step depth of the second program. F^T2 − F^A_k = N − λ·thr, computed with `src/ahchain.py` between the anchor's CV end and the second program's CV end.
  - Compute both with the package's A3 step value and with the sub-grid dv/dQ variant (DL1 applied to the programs).
  - The h interval [h_lo, h_hi] is the minimum and maximum of the four medians over k: {h1, h2} × {A3, DL1}.
- **Results.**
  - a_0 = −(D_bot − C_bot) − h. Its interval combines the h interval with the min/max of (D_bot − C_bot) over the locator variants.
  - Also report the top split F^CK_0 − F^A_0 = (D_top − C_top) − h.
- **Caveats to state.** CK0 discharges at 5.1 A, while the programs' step band is ≈ 10 A. The checkup temperature is unknown. Anchor 0 charged at 45 °C.

Apply the WP2 gates of §4.

**Done:** `wp2/start_audit.csv`, `wp2/bottom_locators.csv`, `wp2/ck0_split.json` (with a_0 and its interval), `wp2/gates.json`, a figure (Q_bot trend with anomalies; the CK0 vs anchor-0 step positions) and `wp2/REPORT.md` are committed and pushed.

### WP3 — Top: the 45/25 °C anchor-top offset T_top

**E1. Ah chain.**
- **Pairs.** For consecutive CV ends i → j with no checkup between them:
  - N_ij = ∫ current_A dt over (t_i, t_j], with the package convention;
  - thr_ij = the discharged Ah between them.
  
  Exclude any pair with a recording gap (dt > 60 s), except the chamber-switch idle, where the counters must be flat (as checked in WP0). Record each exclusion.
- **Pair types:**
  - AT: anchor → next top-up;
  - TT: top-up → top-up within a segment;
  - X: last 25 °C CV end → first 45 °C CV end across a switch.
- **Loss rule.**
  - λ_s = median of N/thr over the TT pairs of segment s.
  - If segment s has no TT pair, use the pooled median of the same set point. If that set point has fewer than 2 TT pairs overall, use the other set point's pooled median, and record it.
  - Residual r = N − λ·thr, with λ computed without that pair. σ_TT,25 and σ_TT,45 are 1.4826·MAD of the TT residuals per set point.
- **Terms.**
  - **Term1** = −(N(A_0 → T) − λ_seg1·thr) = F^A_0 − F^T_45. One value.
  - **Term3_k** = N(A_k → T) − λ_s·thr = F^T_25 − F^A_k, for k ∈ {1..7}, where a following top-up exists in the same segment. The main estimate uses all of them; a sensitivity run excludes k = 3.
  - **Term2_j** = N_X − λ̄·thr_X = F^T_45 − F^T_25, for the j = 5 switches. λ̄ is the mean of the two adjacent segments' λ. Sensitivity runs use each side's λ alone.
  - **T_top** = Term1 + median_j Term2_j + median_k Term3_k.
- **Interval.**
  - Per term: take the minimum and maximum of the point value over the λ sensitivities, then widen by ±2·SE. SE = 1.4826·MAD/√n of the event values; for Term1, SE = σ_TT,45.
  - The T_top interval is the sum of the lower ends and the sum of the upper ends.
- **Descriptive.** Show Term2_j and Term3_k against month, and Term2_j against idle hours (self-discharge during the idle).

**E2. Step jump** (cross-check of Term2).
- J_j = depth(first 45 °C program after switch j) − depth(last 25 °C program before it). Neither may be the first program after an anchor.
- Subtract r_45·Δt, where r_45 is the Theil–Sen rate of that 45 °C segment's depths and Δt the days between the two programs.
- Compute two values: the A3 value (package `_robust_step`) and the sub-grid dV/dQ value (DL1, insensitive to polarisation).
- E2 measures Term2 plus any shift of the step itself with temperature.

**E3. Physics diagnostic** (not gating).
- ΔV_j = pack voltage 30 min after the CV end of the first 45 °C top-up, minus the same for the last 25 °C top-up.
- s = dV/dQ of the CK0 pack curve over discharged Ah ∈ [0.5, 2.0], with sensitivity windows [0.25, 1.0] and [1.0, 3.0].
- The entropy term is 4·(dU/dT)·ΔT. Take dU/dT for LFP/graphite at high SOC from a cited source. If none is found, use ±0.3 mV/K per cell and label it an assumption.
- Term2_E3 = (ΔV − entropy term)/s, reported as an interval.
- Also report which cell sets the top at each temperature (anchor 0: cell3).

Apply the WP3 gates of §4.

**Done:** `wp3/pairs.csv`, `wp3/terms.csv`, `wp3/T_top.json` (point, interval, gate results), `wp3/e2_e3.csv`, a figure (the chain terms by event; Term2 vs J vs Term2_E3) and `wp3/REPORT.md` are committed and pushed.

### WP4 — ε-level budget and decision

1. **Budget.** EPS_EXTRA_hat = T_top + a_0, with the interval endpoints added. Non-identified components are handled as in §4.
2. **Decision.** Apply the rules of §4: L1, L2 or L3, plus the anchor-3 rule.
3. **SOH variants.** Save `wp4/SOH_variants.csv`. These are **leaderboard-only** numbers and are never scored against proxies. Build each as a research copy under `cache/variants/` and run it through the package CLI:
   - SUB;
   - SUB with EPS_EXTRA = point, lo and hi;
   - if L2, also the rounded point (SUB_L);
   - SUB_A3fix, if the anchor-3 rule passes;
   - the combination of SUB_L and SUB_A3fix, if both apply.
4. **Probe.**
   - Say whether a single-submission P_level probe (CK2–CK7 shifted by the measured EPS_EXTRA change) is worth it, and where it goes in round 7's order P_stress_early → P_start → P_drift.
   - Quote what `CHALLENGE2_DESCRIPTION.pdf` says about the leaderboard and submissions. The user decides; nothing is submitted in this round.
5. **Handoff.** Write `wp4/R13_HANDOFF.json` with:
   - T_top with its terms, a_0, a_3^rel, and the H_SB status;
   - the open terms: the drift d (top-of-charge model, round 11's plan), self-discharge during checkup rests, and the checkup protocol and temperature.
6. **README draft.** Write two sentences, not applied to the package, that the package README could use to justify EPS_EXTRA with the measured interval.

**Done:** budget, decision, `wp4/SOH_variants.csv`, `wp4/R13_HANDOFF.json` and `wp4/REPORT.md` are committed and pushed. Then `FINAL_REPORT.md` and `README.md` are written (conclusions first; per-checkup SOH of SUB vs any candidate) and committed and pushed.

## 4. Registered gates and decision rules (copy into `wp1/protocol.json` verbatim)

- **G_noise (WP3).** σ_TT,25 ≤ 0.30 Ah and σ_TT,45 ≤ 0.30 Ah. Otherwise E1 exits "not identifiable" and T_top is unmeasured.
- **G_T (WP3).** T_top is "identified" if the half-width of its interval is ≤ 0.25 Ah.
- **G_E2 (WP3).** Term2 and E2 are "consistent" if |median_j J_dvdq − median_j Term2_j| ≤ 0.20 Ah. Otherwise they are "inconsistent": widen Term2's interval, and with it T_top's, to include median_j J_dvdq.
- **G_SB (WP2, a necessary condition for H_SB).** σ_LOO ≤ 0.25 Ah, and no relaxed anchor has |residual| > max(2·σ_LOO, 0.15 Ah). On failure, H_SB is "rejected for anchor(s) …", and those anchors join the anomaly list.
- **G_a3 (WP2).** a_3^rel is "identified" if |a_3^rel| > max(2·σ_LOO, 0.15 Ah) on the combined locator value, with the same sign on at least 4 of the 5 locators CL1–CL5.
- **G_B3 (WP2).** a_0 is "identified" if the width of its interval is ≤ 0.40 Ah. Otherwise it is "not identified" and enters the budget with its full interval. If no finite interval exists, the budget is L3.
- **Budget.** EPS_EXTRA_hat = T_top + a_0. The interval endpoints add.
- **Decision.**
  - **L1 "assumption supported":** 0.4 lies in the interval, and the interval width is ≤ 0.50 Ah. Keep SUB; the README may cite the interval.
  - **L2 "assumption off":** 0.4 lies outside the interval, the width is ≤ 0.50 Ah, G_noise passed, and G_SB did not fail. Candidate SUB_L = SUB with EPS_EXTRA_AH set to the point estimate rounded to 0.05 Ah. It is not wired and is leaderboard-only; the user decides.
  - **L3 "inconclusive":** any other case. Keep SUB.
  - **Anchor-3 rule:** if G_a3 passes, candidate SUB_A3fix subtracts a_3^rel from anchor 3's Q_fc in a research copy, so the change reaches every use of that anchor. It is not wired and is leaderboard-only.
- **No rule above uses P_k or any proxy error.**

---

<a id="zh"></a>

# 第 12 轮：在本电池组上测 ε 的水平——45/25 °C 锚点顶部偏移与"共用底部"检验——执行 Prompt

> [English](#en) · 中文

写于 2026-10-19。本文档自成一体。英文部分是执行文本，中文部分是供读者阅读的译文；两者不一致时以英文为准。

工作分为**工作包 WP0–WP4**。每个工作包都有自己的"完成"清单，可以作为单独的 `/goal` 运行。
- 先做 WP0，再做 WP1。
- WP2 和 WP3 只依赖 WP1，彼此独立。请依次运行（一个工作树同时只开一个会话）。
- WP4 需要 WP2 和 WP3。`FINAL_REPORT.md` 最后写。

## 0. 工作方式（所有工作包）

- **无人值守。** 永远不要停下来提问。遇到未决问题时，选择符合本文全部规则的最保守做法，记入 `notes/DECISIONS.md`，然后继续。
- **重启。** 每完成一步就更新 `notes/STATUS.md`：当前工作包、已完成、下一步、最后一次提交。重启时先读 `notes/STATUS.md` 和 `notes/DECISIONS.md`，从断点继续。已完成的工作包或步骤不要重做。
- **诚实优先于目标。** "无法识别"和"无定论"都是有效结果。本轮产出的是**测量值、区间和建议**。本轮不改动提交，也不针对 Challenge 2 代理标签 P_k 计算任何误差。
- **任一工作包的"完成"**指满足下列通用条件，以及该工作包自己的清单：
  1. 登记协议（`wp1/protocol.json` + `wp1/protocol.sha256`，以及第 3 节 WP1 中登记的代码）在任何评估输出**之前**已提交；
  2. 有中英双语的 `wpN/REPORT.md`，结论在前；
  3. `notes/STATUS.md` 把该工作包标为完成、跳过或退出，并附一行结果；
  4. 每次提交都已推送到 `origin exp/phase2-r12-eps-level-20261019`，且 `git status` 中没有未提交的研究文件。
- **全局完成**（整份 prompt）：
  - WP0–WP4 各自完成，或按登记规则退出；
  - `FINAL_REPORT.md`、`README.md` 和 `wp4/R13_HANDOFF.json` 均存在（Markdown 双语，结论在前）；
  - 通用条件 3–4 成立。

## 1. 工作区、隔离与 git

- **工作树和分支。** 在 WP0 中按需创建，此步骤可重复执行。
  - 基点：`exp/phase2-anchor-step-20261013` 上的 `6525edf`（"Wire the robust multi-variant cell-median step (A3) into the submission"）。如果分支末端更新，就用末端，并记录其哈希。
  - 创建：`git -C /Users/shane/Desktop/Arena_1013_model worktree add /Users/shane/Desktop/Arena_1019_r12_eps_level -b exp/phase2-r12-eps-level-20261019 <base>`。如果工作树或分支已存在，确认其历史包含 `<base>` 后复用。
  - 只在 `/Users/shane/Desktop/Arena_1019_r12_eps_level` 中工作。研究目录为 `research/phase2_r12_eps_level_20261019/`。
- **本 prompt** 目前未提交，位于 `/Users/shane/Desktop/Arena_1013_model/research/phase2_r12_eps_level_20261019/R12_EXECUTION_PROMPT.md`。把它复制到你工作树中的 `research/phase2_r12_eps_level_20261019/EXECUTION_PROMPT.md`，并作为第一次提交。不要提交、移动或删除原文件。
- **本工作树之外的只读来源。** 永远不要 `cd` 进去，也不要写入。每个复制的文件都要在 `sources/SOURCES.md` 中记录来源引用或路径以及 SHA256。用 `git -C /Users/shane/Desktop/Arena_1013_model show <ref>:<path>` 读取之前各轮的文件：
  - 第 11 轮 `exp/phase2-r11-eps-transfer-20261018`（最终提交 `ff45b48`），位于 `research/phase2_r11_eps_transfer_20261018/` 下：`FINAL_REPORT.md`、`wp4/pack_drivers.csv`、`src/wp4_pack.py`、`wp5/R12_HANDOFF.json`；
  - 第 8 轮 `exp/phase2-r8-error-table-20261017`，位于 `research/phase2_r8_error_table_20261017/` 下：`DATA_DICTIONARY.md`、`outputs/table_anchors.csv`、`outputs/table_events.csv`、`outputs/table_cycles.csv`、`src/eventcurves.py`、`src/common8.py`；
  - 第 5B 轮 `exp/phase2-r5b-electrode-model-20261014`：`research/phase2_r5b_electrode_model_20261014/FINAL_REPORT.md`（负面结果，见第 2 节）；
  - 基点分支上（你的工作树里已有）：`research/phase2_rebound_diagnosis_20261015/`（首个程序偏移）、`research/phase2_v2_phase_matched_20261013/`（25 → 45 °C 台阶跳变）、`research/phase2_anchor_step_20261013/FINAL_REPORT.md`。
- **赛题数据：** 你自己工作树中的 `TechArena_Challenge2_Team_Package/data/`（`operation/`、`checkups/CK0_reference_discharge.csv.gz`、`checkups/evaluation_points.csv`、`DATA_DESCRIPTION.md`），以及 `CHALLENGE2_DESCRIPTION.pdf`。
- **并发保护。**
  - 开始时以及每次提交前，运行 `git log --oneline -5`，与你上一次提交对比。
  - 遇到意外的提交或改动：停止编辑共享文件，记录下来，之后只按明确路径添加文件。
  - 不要用 `git add -A` 或 `git add .`，不要改写他人的工作，不要用不带参数的 `git stash`。同一时间只在本工作树上运行一个会话。
- **提交。**
  - 每一步结束时提交，然后运行 `git push -u origin exp/phase2-r12-eps-level-20261019`。不要推送到其他地方，也不要强制推送。
  - 每条提交信息的末尾加上 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`。
- **不得修改：** 任何位置的 `TechArena_Challenge2_Team_Package/` 目录、之前各轮的研究目录、本工作树之外的任何文件。模型变体以副本形式建在 git 忽略的 `cache/variants/` 下。
- **语言与字节码。** Markdown 先英文后中文，版式同本文件。代码注释只用英文。运行 Python 时用 `python3 -B`。
- 本轮**不下载**任何东西。

## 2. 背景

**任务。** 估计一个 4 × 102 Ah LFP 串联电池组在 CK0..CK7 的 SOH。SOH 是 C/20 容量除以 102 Ah。按赛题 PDF，C/20 容量是"满充后"以 5.1 A 放电到电池组 11.2 V 的容量；满充协议没有说明。
- 只公布了 CK0 = 100.41 Ah。因果截断为 `load_dataset(data, until=CK_k)`。PDF 说明公开排行榜每周更新。

**提交模型 SUB 如何使用 ε。** SUB 是基点提交上的 `my_model/model_template.py`。
- 凡是以 25 °C 锚点为基础的预测，都用 `q_anchor = Q_fc,k + ε0 + EPS_EXTRA_AH`。
  - ε0 = 100.41 − Q_fc,0 = 0.288 Ah，来自 45 °C 的锚点 0。
  - `EPS_EXTRA_AH = 0.4` 是一个**假设**（自第一次锚点研究起，登记范围为 {0, 0.4, 0.8}）。
- 它让 CK2–CK7 一起平移：EPS_EXTRA 每 1 Ah 对应 0.98 pp。CK1 直接以 CK0 = 100.41 为基础，不使用它。
- 代理标签为 P_k = Q_fc,k + ε0 + Δ。改动 EPS_EXTRA 会让预测和代理一起移动，所以**代理评分在结构上就看不到这个问题**。这正是本轮改用电池组自身数据来测这个偏移的原因。

**本轮登记的分解。** 各量都是以 Ah 计的电荷量。忽略库伦效率（第 11 轮：LIC 中 T_CE 平坦，−0.0008 Ah/Ah）。
- C20_k = F^CK_k − S_k：从检查的顶部状态到其 C/20 放电结束时的状态。
- Q_fc,k = F^A_k − B_k：从锚点的起点状态到锚点的顶部（14.0 V CV 在约 5.1 A 处结束）。

```
ε_k = C20_k − Q_fc,k = (F^CK_k − F^A_k) + (B_k − S_k)

EPS_EXTRA_true(k) = ε_k − ε_0
   = [F^A_0 − F^A_k]                T_top：45 °C 从空充满的锚点 0 的顶部减 25 °C 从空充满的锚点的顶部   （WP3）
   + [F^CK_k − F^CK_0]              检查顶部随老化的变化 = 漂移 d（不在本轮范围内）
   + [a_0 − a_k]，a_k := S_k − B_k  底部错位：锚点起点比其 C/20 结束点更深时 > 0                        （WP2）
```

- **假设 H_SB（"共用底部"）。** 锚点从其检查的 C/20 放电结束时的状态开始，中间只有静置：a_k = 0。在 H_SB 成立且老化程度相同时，对已充分静置的 25 °C 锚点有 **EPS_EXTRA_true = T_top + a_0**。本轮测量 T_top 和 a_0，并在数据允许的范围内检验 H_SB。对 k ≥ 1 只能检验一个必要条件，因为 S_k 不可见。
- **关于预测（登记）。** 某个锚点特有的底部异常 a_k^rel（相对于已静置锚点趋势的偏差），会使所有以锚点 k 为基础预测之后检查点的结果产生偏差。不论它自己那次 C/20 是否共有这个异常都是如此，因为下一次检查会在正常深度结束。对 ε0 而言，只有不共用的部分 a_0 = S_0 − B_0 起作用。

**已确立的事实。** 引用这些事实，并在 WP0 中重新核实。
- **CK0 的 C/20 曲线。** 2025-01-15 14:03:42 → 2025-01-16 09:44:56，电流 5.10 A。带载起始电压 13.590 V，放出 100.41 Ah，结束时四个电芯都在 2.800–2.802 V。
- **锚点 0**（第 1 段，45 °C）。
  - 数据从 2025-01-19 19:10:56 开始，距 C/20 结束 3.4 天，只静置了 0.5 h。
  - 起始电压 11.53–11.57 V，以 +84–86 mV/h 上升。
  - CV 段只有约 36 s（0.09–0.15 Ah）。
  - CV 结束 30 min 后，电池组为 13.644 V，其中 cell3 为 3.53 V（顶部压差 264 mV）。
  - 按包内积分，Q_fc,0 = 100.122 Ah。
- **25 °C 锚点 1–7**（第 2、4、6、8、10、12、14 段）。
  - CV 1.17–1.44 Ah，I_end 5.09–5.10 A，CV 结束 30 min 后电池组 13.435–13.439 V，顶部压差 88 → 52 mV。
  - 起始 11.80–11.95 V，上升 ≤ 6 mV/h，底部压差 22 → 35 mV。例外是锚点 3（第 6 段）：11.47 → 11.62 V，以 +52 mV/h 上升。
  - Q_fc,1..7 = 97.00、95.66、94.64、93.75、93.08、92.64、91.95 Ah。
- **已曝光，探索性**（2026-10-17，不在仓库中）。锚点 3 要比相邻锚点多充约 0.3–0.4 Ah，才能到达电池组 13.0/13.2 V 和充电侧台阶。
- **已曝光**（2026-10-15 回弹诊断）。
  - 每次从空充满后，第一次深放电程序的台阶都深 +0.39–0.46 Ah，6 种检测变体都如此，到下一个程序就消失了。
  - 锚点之后顶部的静置电压低 7–8 mV，下一次补电需要多充约 +0.1 Ah。
- **已曝光**（2026-10-13 V2 研究）。每次 25 → 45 °C 切换时，放电侧台阶深度跳变约 +0.18 Ah。
- **月度结构。** CK → 25 °C 段（2–3 块）→ 换温箱停机（未记录，计数器不变）→ 45 °C 段（4 块）→ CK。
  - 每块以 20.4 A 恒流充电到 14.0 V 开始，再恒压到约 5.1 A。
  - 之后是 30 min 静置、30 min 的 20 A 脉冲，以及约 55.9 Ah 的深放电程序（台阶电流带 −12.5…−8 A）。
- **可见的 25 → 45 °C 切换**（间隙前后计数器相同），共五次：
  - 第 4 → 5 段，停机约 21.2 h；
  - 第 6 → 7 段，约 6.9 h；
  - 第 8 → 9 段，约 9.7 h；
  - 第 10 → 11 段，约 25.3 h；
  - 第 12 → 13 段，约 12.1 h。
  
  第 1 个月没有 25 °C 部分，第 3 段（第 2 个月的 45 °C 部分）缺失。
- **检查窗口**（最后一个运行样本 → 下一个锚点段开始）：CK1 约 3.2 天，CK3 约 3.1 天，CK4 约 3.7 天，CK5 约 5.4 天，CK6 约 6.0 天，CK7 约 4.3 天。CK2 未知（第 3 段缺失）。
- **积分。**
  - 累计计数器把 20 A 脉冲记作充电。要对 `current_A` 积分，并沿用包内约定（`_integrated_ah`：dt > 600 s 的样本贡献为 0）。
  - 相邻两次 CV 结束之间的逐块电量对账不闭合（每块 −0.3 到 −1.1 Ah，符号与副反应相反），说明存在测量偏差。
- **分辨率。**
  - 包内的充电侧台阶定位器（`_charge_step_to_top`）在 0.25 Ah 网格上取 argmax。因此它以及第 8 轮的 `bottom_to_step`/`step_to_top` 都量化在 0.25 Ah，对本轮来说太粗。
  - 包内放电侧的 `dvdq` 变体也在同样的 0.25 Ah 网格上。
- **第 5B 轮。** 用文献 OCP 重建绝对 Q_C20 无法识别（范围宽达 8–10 Ah）。不要重试。
- **范围调整。** 第 11 轮的交接文件把"充电顶部漂移模型"列为第 12 轮。用户决定先测 ε 的**水平**；漂移模型挪到第 13 轮。在 `notes/DECISIONS.md` 中记录这一点。

## 3. 工作包

### WP0 — 准备与事实清单

1. 创建或复用工作树，写 `notes/STATUS.md`、`notes/DECISIONS.md` 和 `sources/SOURCES.md`，并提交本 prompt。
2. 把第 1 节列出的来源复制到 `sources/`，附 SHA256。
3. 用包自带的 CLI 在完整数据上运行 SUB，保存 `wp0/SUB_SOH.csv`。
   - 在 `cache/variants/` 下建一个 `model_template.py` 的研究副本，唯一的改动是 `EPS_EXTRA_AH`。
   - 把 EPS_EXTRA ∈ {0, 0.2, 0.4, 0.6, 0.8} 时的 SOH 存为 `wp0/eps_extra_sensitivity.csv`。
   - 检查三件事，有偏差要解释：0.4 时与 SUB 完全一致；CK2–CK7 每 Ah 移动 0.98 pp；CK1 不动。
4. 写事件目录 `wp0/events.csv`。它列出每一次到达 CV 的恒流恒压充电（电池组 ≥ 13.95 V，结束时 0 < I < 6 A），包括：
   - 所在段、设定温度、类型（A = 从空充满的锚点，T = 补电）；
   - 开始和结束时间、CV 结束电流、CV 电量、充电前的静置时长；
   - CV 结束时和 30 min 后（脉冲之前）的电池组电压和各电芯电压；
   - 到下一次 CV 结束之前有没有记录间隙（dt > 60 s）；
   - 两端的累计计数器读数。
5. 写 `wp0/FACTS.md`。
   - 对第 2 节"已确立的事实"的每一条，用数据中的数字核实。标为"已确认"，或给出更正后的值。
   - 加上切换表：停机时长、间隙前后计数器的变化、前后的温度。
   - 加上检查窗口表。
   - 积分核对：每个锚点比较包内积分与基于计数器的 Q，并确认计数器如何记录脉冲。

WP0 中不计算任何电量对账、台阶位置或与 ε 相关的估计。

**完成：** 工作树、记录文件、sources、`wp0/SUB_SOH.csv`、`wp0/eps_extra_sensitivity.csv`、`wp0/events.csv` 和 `wp0/FACTS.md` 均已提交并推送。

### WP1 — 登记（不计算任何估计值）

1. 写 `wp1/protocol.json`，包含：
   - 第 2 节的定义；
   - 下文 WP2 的定位器和 WP3 的电量链，与规定完全一致，所有数值常数都固定下来；
   - 第 4 节的门槛和决策规则，原样照抄。
2. 把登记的方法实现为 `src/locators.py`（充电侧和放电侧台阶定位器及全部变体）和 `src/ahchain.py`（配对、积分和损耗规则）。
   - 只在**合成**曲线上测试（`src/test_registered.py`）：已知的台阶位置要在 0.02 Ah 以内找回，已知的电量偏移要在 0.005 Ah 以内找回。
   - WP1 中不要在赛题数据上运行它们。
   - WP2 和 WP3 原样导入这两个模块。之后的任何改动都算新的登记版本：在 `notes/DECISIONS.md` 中记录原因，提交新的协议哈希，并给改动前算出的结果加标注。
3. 在 WP2 或 WP3 产生任何输出**之前**，提交 `protocol.json`、`protocol.sha256`、两个模块和测试。
4. 在 `wp1/REPORT.md` 中加一张"各结果意味着什么"的表：L1、L2、L3、锚点 3 规则，以及 H_SB 不成立与未被否定两种情况。

**完成：** 协议、哈希、通过合成测试的登记代码和 `wp1/REPORT.md` 均已提交并推送。WP1 的任何文件中都不出现在赛题数据上算出的值。

### WP2 — 底部："共用底部"检验与起点异常

**B1. 起点状态与时间线（描述性）。** 保存 `wp2/start_audit.csv`，每个锚点一行，包括：
- 检查窗口（k = 0 时为距 C/20 结束的确切时长）和记录到的静置时长；
- 起始时电池组和各电芯的电压，以及静置最后 30 min 的电压斜率（静置不足 30 min 时取整个静置段）；
- 起始温度及其在静置期间的趋势（电池组是否还在升温？这对第 1 段很重要）；
- 起始时的电芯压差。

对每个锚点，说明其起点是否与"C/20 结束状态加上单纯静置"相符（已静置锚点：斜率 ≤ 6 mV/h）。对每个未静置好的锚点，说明时间线意味着什么：
- 锚点 0 在其 C/20 结束 3.4 天后仍未静置好，这指向 C/20 之后有一次未记录的事件或温度瞬变；
- 锚点 3：是它的窗口短，还是有别的迹象？

**B2. 底部区段。** 在每个锚点的恒流段（I > 20 A）中，用登记的定位器逐个电芯定位充电侧石墨台阶：
- **CL1：** 充电方向 dV/dQ 最大值，0.05 Ah 网格，2 Ah 滑动平均平滑，对峰值做抛物线插值，搜索窗口为从充电开始算起 50–80 Ah（与包内窗口一致）。
- **CL2：** 同 CL1，平滑 1 Ah。
- **CL3：** 同 CL1，平滑 3 Ah。
- **CL4：** 中点穿越，在样本之间线性插值。阈值是下平台 [s − 15, s − 5] Ah 与上平台 [s + 5, s + 15] Ah 上电芯电压中位数的平均值，其中 s 为 CL1 的位置。
- **CL5：** 同 CL4，平台窗口改为 [s − 20, s − 10] 和 [s + 10, s + 20] Ah。

按以下方式合并：
- 电芯的值取其有限变体的中位数（至少需要 4 个）。锚点的值取各电芯的中位数。
- 定义 Q_bot,k = 从充电开始到台阶的 Ah，Q_top,k = Q_fc,k − Q_bot,k。
- 报告每个定位器的值。检查把 CL1 取整到 0.25 Ah 网格后，与第 8 轮的 `bottom_to_step` 相差在 0.25 Ah 以内。
- **趋势。** 在已静置的 25 °C 锚点 {1, 2, 4, 5, 6, 7} 上，对 Q_bot 与距 CK0 天数做 Theil–Sen 直线拟合。σ_LOO = 留一残差的 1.4826·MAD。
- **异常。**
  - a_3^rel = Q_bot,3 − trend(t_3)，针对锚点 3。
  - a_0^rel = Q_bot,0 − trend(t_0)，针对锚点 0。这是外推值，且受 45 °C 干扰，只作诊断。
- **描述性。** 在已静置锚点中，把 Q_bot 残差与起始电压和底部压差对照。在 H_SB 下，起始电压的上升不影响 ε，因为检查同样包含它。

**B3. CK0 拆分**（CK0 是唯一能看到 C/20 曲线的检查）。
- 在 CK0 曲线上，用镜像的定位器族逐个电芯定位放电侧台阶：
  - DL1–DL3：−dV/dQ 的最大值；
  - DL4–DL5：中点穿越，平台窗口镜像。

  由此得到 D_top,c（从 C/20 开始到台阶的 Ah）和 D_bot,c = 100.41 − D_top,c。各电芯到达截止电压时彼此相差在 2 mV 以内。
- 从锚点 0 取 C_bot,c = 各电芯的 Q_bot，C_top,c = Q_fc,0 − C_bot,c。然后取各电芯的中位数：

```
ε0 = (D_top − C_top) + (D_bot − C_bot)
D_bot − C_bot = −a_0 − h          h = step_ch − step_dis（充电侧台阶位置减放电侧台阶位置）
D_top − C_top = (F^CK_0 − F^A_0) + h
```

- **在运行数据中以同一个顶部为基准估计 h**，使用 25 °C 锚点 k ∈ {1, 2, 4, 5, 6, 7}：
  - **h1_k = D1_k − C_top,k。** D1_k 是锚点 k 之后第一个深放电程序的台阶深度，它从锚点自己的顶部开始放电。这个值带有首个程序偏移。
  - **h2_k = D2_k − C_top,k − (F^T2 − F^A_k)。** D2_k 是第二个程序的台阶深度。F^T2 − F^A_k = N − λ·thr，用 `src/ahchain.py` 在锚点 CV 结束与第二个程序 CV 结束之间计算。
  - 两者都分别用包内 A3 台阶值和亚网格 dV/dQ 变体（把 DL1 用于这些程序）计算。
  - h 区间 [h_lo, h_hi] 取四个按 k 求的中位数 {h1, h2} × {A3, DL1} 中的最小值和最大值。
- **结果。**
  - a_0 = −(D_bot − C_bot) − h。其区间由 h 区间与 (D_bot − C_bot) 在各定位器变体上的最小/最大值合成。
  - 同时报告顶部拆分 F^CK_0 − F^A_0 = (D_top − C_top) − h。
- **需要说明的局限。** CK0 以 5.1 A 放电，而程序的台阶电流带约为 10 A。检查温度未知。锚点 0 是在 45 °C 下充电的。

按第 4 节应用 WP2 的门槛。

**完成：** `wp2/start_audit.csv`、`wp2/bottom_locators.csv`、`wp2/ck0_split.json`（含 a_0 及其区间）、`wp2/gates.json`、一张图（带异常标注的 Q_bot 趋势；CK0 与锚点 0 的台阶位置）和 `wp2/REPORT.md` 均已提交并推送。

### WP3 — 顶部：45/25 °C 锚点顶部偏移 T_top

**E1. 电量链。**
- **配对。** 对相邻两次 CV 结束 i → j（中间没有检查）：
  - N_ij = 在 (t_i, t_j] 上对 current_A 的积分，沿用包内约定；
  - thr_ij = 两者之间的放电 Ah。
  
  排除任何带记录间隙（dt > 60 s）的配对，换温箱停机除外，但停机期间计数器必须不变（已在 WP0 核实）。每次排除都要记录。
- **配对类型：**
  - AT：锚点 → 下一次补电；
  - TT：同一段内补电 → 补电；
  - X：跨切换，最后一次 25 °C CV 结束 → 第一次 45 °C CV 结束。
- **损耗规则。**
  - λ_s = 第 s 段所有 TT 配对的 N/thr 的中位数。
  - 如果第 s 段没有 TT 配对，用同一设定温度的合并中位数。如果该设定温度总共不足 2 个 TT 配对，就用另一个设定温度的合并中位数，并记录下来。
  - 残差 r = N − λ·thr，计算 λ 时排除该配对本身。σ_TT,25 和 σ_TT,45 为各设定温度 TT 残差的 1.4826·MAD。
- **各项。**
  - **Term1** = −(N(A_0 → T) − λ_seg1·thr) = F^A_0 − F^T_45。只有一个值。
  - **Term3_k** = N(A_k → T) − λ_s·thr = F^T_25 − F^A_k，对 k ∈ {1..7} 中同一段内有后续补电的锚点计算。主估计用全部锚点；敏感性分析排除 k = 3。
  - **Term2_j** = N_X − λ̄·thr_X = F^T_45 − F^T_25，对 j = 5 次切换计算。λ̄ 是相邻两段 λ 的平均。敏感性分析分别只用一侧的 λ。
  - **T_top** = Term1 + median_j Term2_j + median_k Term3_k。
- **区间。**
  - 对每一项：取点估计在各 λ 敏感性下的最小值和最大值，再向两侧各放宽 2·SE。SE = 事件值的 1.4826·MAD/√n；Term1 的 SE = σ_TT,45。
  - T_top 的区间取各项下端之和与上端之和。
- **描述性。** 画出 Term2_j 和 Term3_k 随月份的变化，以及 Term2_j 随停机时长的变化（停机期间的自放电）。

**E2. 台阶跳变**（交叉检验 Term2）。
- J_j = 切换 j 之后第一个 45 °C 程序的深度 − 切换之前最后一个 25 °C 程序的深度。两者都不能是锚点之后的第一个程序。
- 减去 r_45·Δt，其中 r_45 是该 45 °C 段台阶深度的 Theil–Sen 速率，Δt 是两个程序之间的天数。
- 计算两个值：A3 值（包内 `_robust_step`）和亚网格 dV/dQ 值（DL1，不受极化影响）。
- E2 测到的是 Term2 加上台阶本身随温度的移动。

**E3. 物理诊断**（不作为门槛）。
- ΔV_j = 第一次 45 °C 补电 CV 结束 30 min 后的电池组电压，减去最后一次 25 °C 补电的同一电压。
- s = CK0 电池组曲线在放电 Ah ∈ [0.5, 2.0] 区间的 dV/dQ，敏感性窗口为 [0.25, 1.0] 和 [1.0, 3.0]。
- 熵项为 4·(dU/dT)·ΔT。dU/dT 取有出处的 LFP/石墨高 SOC 数值；找不到时用每个电芯 ±0.3 mV/K，并标为假设。
- Term2_E3 = (ΔV − 熵项)/s，以区间形式报告。
- 同时报告每个温度下由哪个电芯决定顶部（锚点 0：cell3）。

按第 4 节应用 WP3 的门槛。

**完成：** `wp3/pairs.csv`、`wp3/terms.csv`、`wp3/T_top.json`（点估计、区间、门槛结果）、`wp3/e2_e3.csv`、一张图（各事件的电量链分项；Term2、J、Term2_E3 对比）和 `wp3/REPORT.md` 均已提交并推送。

### WP4 — ε 水平预算与决策

1. **预算。** EPS_EXTRA_hat = T_top + a_0，区间端点相加。未识别的分项按第 4 节处理。
2. **决策。** 应用第 4 节的规则：L1、L2 或 L3，外加锚点 3 规则。
3. **SOH 变体。** 保存 `wp4/SOH_variants.csv`。这些数字**只用于排行榜**，绝不与代理标签对比打分。每个变体都在 `cache/variants/` 下建研究副本，并用包的 CLI 运行：
   - SUB；
   - EPS_EXTRA 取点估计、下端和上端的 SUB；
   - 若为 L2，再加取整后的点估计（SUB_L）；
   - 若锚点 3 规则通过，加 SUB_A3fix；
   - 两者都适用时，加 SUB_L 与 SUB_A3fix 的组合。
4. **探针。**
   - 说明单次提交的 P_level 探针（把 CK2–CK7 按测得的 EPS_EXTRA 变化平移）是否值得做，以及它在第 7 轮探针顺序 P_stress_early → P_start → P_drift 中的位置。
   - 引用 `CHALLENGE2_DESCRIPTION.pdf` 中关于排行榜和提交的原文。由用户决定；本轮不提交任何东西。
5. **交接。** 写 `wp4/R13_HANDOFF.json`，包括：
   - T_top 及其各项、a_0、a_3^rel、H_SB 的状态；
   - 仍未解决的项：漂移 d（第 11 轮计划的充电顶部模型）、检查后静置期间的自放电、检查协议与温度。
6. **README 草稿。** 写两句话（不改动包），供包的 README 用测得的区间说明 EPS_EXTRA 的依据。

**完成：** 预算、决策、`wp4/SOH_variants.csv`、`wp4/R13_HANDOFF.json` 和 `wp4/REPORT.md` 均已提交并推送。然后写 `FINAL_REPORT.md` 和 `README.md`（结论在前；列出 SUB 与各候选在每个检查点的 SOH），提交并推送。

## 4. 登记的门槛与决策规则（原样复制进 `wp1/protocol.json`）

- **G_noise（WP3）。** σ_TT,25 ≤ 0.30 Ah 且 σ_TT,45 ≤ 0.30 Ah。否则 E1 以"无法识别"退出，T_top 视为未测得。
- **G_T（WP3）。** T_top 区间的半宽 ≤ 0.25 Ah 时，T_top 为"已识别"。
- **G_E2（WP3）。** |median_j J_dvdq − median_j Term2_j| ≤ 0.20 Ah 时，Term2 与 E2 为"一致"。否则为"不一致"：放宽 Term2 的区间（T_top 的区间随之放宽），使其包含 median_j J_dvdq。
- **G_SB（WP2，H_SB 的必要条件）。** σ_LOO ≤ 0.25 Ah，且没有任何已静置锚点的 |残差| > max(2·σ_LOO, 0.15 Ah)。不满足时，H_SB 记为"对锚点 … 不成立"，这些锚点加入异常列表。
- **G_a3（WP2）。** 合并定位器值上 |a_3^rel| > max(2·σ_LOO, 0.15 Ah)，且在 CL1–CL5 中至少 4 个定位器上同号时，a_3^rel 为"已识别"。
- **G_B3（WP2）。** a_0 区间宽度 ≤ 0.40 Ah 时，a_0 为"已识别"。否则为"未识别"，以完整区间进入预算。如果不存在有限区间，预算结果为 L3。
- **预算。** EPS_EXTRA_hat = T_top + a_0，区间端点相加。
- **决策。**
  - **L1"假设得到支持"：** 0.4 在区间内，且区间宽度 ≤ 0.50 Ah。保留 SUB；README 可以引用该区间。
  - **L2"假设偏离"：** 0.4 不在区间内，区间宽度 ≤ 0.50 Ah，G_noise 通过，且 G_SB 未失败。候选 SUB_L = 把 EPS_EXTRA_AH 设为点估计（取整到 0.05 Ah）的 SUB。不接入提交，只用于排行榜；由用户决定。
  - **L3"无定论"：** 其他所有情况。保留 SUB。
  - **锚点 3 规则：** 若 G_a3 通过，候选 SUB_A3fix 在研究副本中从锚点 3 的 Q_fc 减去 a_3^rel，使改动传到该锚点的每一处使用。不接入提交，只用于排行榜。
- **以上规则都不使用 P_k 或任何代理误差。**
