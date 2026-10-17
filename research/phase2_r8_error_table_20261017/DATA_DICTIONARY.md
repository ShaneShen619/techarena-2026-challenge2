<a id="en"></a>

# Data dictionary (round 8)

> **Language:** English · [中文](#zh)

Every column of every table. Sign convention: residual = predicted − reference; pp = 100·Ah/102. Kind: **causal** = computed from the scenario's cut data exactly as the framework hands it to the model; **diagnostic** = built from the full operation data; **reference** = uses the full-data proxy Q_fc,k.

## Case table (WP1) — `outputs/table_cases.csv`

| column | unit | definition | source | kind |
|---|---|---|---|---|
| `scenario` | — | scenario: real, PG1, PG2, PC5, PC10 (k 3..7), CS, CSE, PC5_all, PC10_all (k 2..7) | runner5c.SCEN | causal (scenario cut) |
| `k` | — | index of the checkup predicted (1..7) | runner5c.SCEN | causal (scenario cut) |
| `checkup` | — | checkup name CK_k | harness.CK_NAMES | causal (scenario cut) |
| `ck_date` | date | checkup date (framework cut date) | evaluation_points.csv | causal (scenario cut) |
| `delta` | Ah | Δ added to ε0 in the anchor term and in the proxy (0, 0.4, 0.8) | harness.DELTAS | causal (scenario cut) |
| `model` | — | SUB = T_main (submitted), V2_sqrt = V2 + calendar √t, V2 | internals.MODELS | causal (scenario cut) |
| `branch` | — | branch taken: phase, fallback or sqrt_gap | internals.decompose | causal (scenario cut) |
| `Q_pred` | Ah | predicted capacity (asserted equal to the model's own output, < 1e-9 Ah) | internals.decompose / model_q | causal (scenario cut) |
| `SOH_pred` | % | 100·Q_pred/102 | run_wp1.py | causal (scenario cut) |
| `proxy` | Ah | P_k = Q_fc,k (full data) + ε0 + Δ | harness.QFC, EPS0 | reference (full data) |
| `err_Ah` | Ah | Q_pred − proxy | run_wp1.py | reference (full data) |
| `err_pp` | pp | 100·err_Ah/102 | run_wp1.py | reference (full data) |
| `anchor_used` | — | index j of the anchor (post-CK_j empty→full charge) the prediction is built on | internals.decompose | causal (scenario cut) |
| `anchor_t_end` | timestamp | CV end of the anchor used | events.full_charges | causal (scenario cut) |
| `Q_fc_anchor_used` | Ah | integrated charge of the anchor used | events.full_charges | causal (scenario cut) |
| `q_anchor_term` | Ah | anchor term of the prediction: Q_fc + ε0 + Δ (ε0 + EPS_EXTRA_AH in the package), or Q_CK0 = 100.41 for fallback from the 45 °C anchor 0 | internals.decompose | causal (scenario cut) |
| `increment_pred` | Ah | predicted change since the anchor: β·x (phase), after[-1] − after[0] (fallback), −a·(t_k^½ − t_k−1^½) (sqrt_gap) | internals.decompose | causal (scenario cut) |
| `Q_fc_k` | Ah | anchor charge after CK_k from the full data (the proxy's base) | harness.QFC | reference (full data) |
| `increment_obs` | Ah | Q_fc,k − Q_fc_anchor_used | run_wp1.py | reference (full data) |
| `inc_resid_Ah` | Ah | increment_pred − increment_obs; free of ε0 and Δ; the primary case residual | run_wp1.py | reference (full data) |
| `inc_resid_pp` | pp | 100·inc_resid_Ah/102 | run_wp1.py | reference (full data) |
| `offset_part_Ah` | Ah | err_Ah − inc_resid_Ah = q_anchor_term − Q_fc_anchor_used − ε0 − Δ (0, or −Δ for fallback from anchor 0) | run_wp1.py | reference (full data) |
| `offset_part_pp` | pp | 100·offset_part_Ah/102 | run_wp1.py | reference (full data) |
| `uses_first_post_anchor_program` | bool | fallback whose increment uses after[0] with ≥ 2 programs after the anchor (D1.1) | run_wp1.py | causal (scenario cut) |
| `anchor_setpoint` | °C | chamber set point of the anchor charge | events.full_charges | causal (scenario cut) |
| `anchor_is_ck0_45C` | bool | anchor used is anchor 0 at 45 °C | run_wp1.py | causal (scenario cut) |
| `beta_used` | — | β applied to the increment (phase: beta_a4; fallback: 1; sqrt_gap: NaN) | internals.decompose | causal (scenario cut) |
| `beta_a4` | — | β from visible 25 °C anchors (step-to-top change vs Q_fc change), shrunk to 1 with τ = 1 | v2.beta_a4 | causal (scenario cut) |
| `beta_raw` | — | unshrunk LS slope behind beta_a4 (NaN if < 2 usable anchors) | internals.beta_internals | causal (scenario cut) |
| `beta_S` | Ah² | S = Σx² of the step-to-top changes used for β | internals.beta_internals | causal (scenario cut) |
| `beta_shrink_w` | — | weight of the data in β: S/(τ+S) | internals.beta_internals | causal (scenario cut) |
| `beta_n_pairs` | — | number of anchor pairs in β | internals.beta_internals | causal (scenario cut) |
| `x` | Ah | phase-matched month-end 45 °C step change E_cur − E_prev + r·(d_cur − d_prev) | v2.phase_diff | causal (scenario cut) |
| `E_cur` | Ah | last 45 °C step depth of month k−1 | v2.end45 | causal (scenario cut) |
| `E_prev` | Ah | last 45 °C step depth of month k−2 | v2.end45 | causal (scenario cut) |
| `d_cur` | days | days from E_cur's program to CK_k | v2.end45 | causal (scenario cut) |
| `d_prev` | days | days from E_prev's program to CK_k−1 | v2.end45 | causal (scenario cut) |
| `r_cur` | Ah/day | Theil–Sen rate of the 45 °C steps of month k−1 (0 if < 3) | v2.end45 | causal (scenario cut) |
| `r_used` | Ah/day | rate used in x (r_cur if n_cur ≥ 3, else 0); NaN outside phase | internals.decompose | causal (scenario cut) |
| `n_cur` | — | number of 45 °C steps in month k−1 | v2.end45 | causal (scenario cut) |
| `n_prev` | — | number of 45 °C steps in month k−2 | v2.end45 | causal (scenario cut) |
| `gap_days` | days | days from the end of the last visible deep program to CK_k | v3.coverage_gap_days | causal (scenario cut) |
| `sqrt_a` | Ah/day^½ | √t loss coefficient fitted to visible anchors 1..k−1 | internals.decompose | causal (scenario cut) |
| `sqrt_t_km1_days` | days | time axis at CK_k−1 (T_main: 45 °C-equivalent days; V2_sqrt: calendar days since CK0) | tsqrt.t_eff_days | causal (scenario cut) |
| `sqrt_t_k_days` | days | time axis at CK_k (same convention) | tsqrt.t_eff_days | causal (scenario cut) |
| `sqrt_anchors` | — | anchors used in the √t fit, '|'-separated | internals.decompose | causal (scenario cut) |
| `n_after` | — | fallback: number of programs after the anchor | internals.decompose | causal (scenario cut) |
| `ev_E_cur` | timestamp | CV end of the program used as E_cur | internals.decompose | causal (scenario cut) |
| `ev_E_prev` | timestamp | CV end of the program used as E_prev | internals.decompose | causal (scenario cut) |
| `ev_rate_fit` | timestamps | programs in the rate fit, '|'-separated (empty if no rate) | internals.decompose | causal (scenario cut) |
| `ev_after_first` | timestamp | fallback: program after[0] | internals.decompose | causal (scenario cut) |
| `ev_after_last` | timestamp | fallback: program after[-1] | internals.decompose | causal (scenario cut) |
| `days_anchor_to_ck` | days | anchor CV end to CK_k | internals.context | causal (scenario cut) |
| `eff45_days_anchor_to_ck` | days | T_main 45 °C-equivalent days from the anchor to CK_k | internals.context | causal (scenario cut) |
| `cum_fade_at_anchor_Ah` | Ah | 100.41 − Q_fc_anchor_used − ε0 | internals.context | causal (scenario cut) |
| `throughput_dis_Ah_since_anchor` | Ah | integrated discharge (negative current_A) in the cut after the anchor | internals.discharge_since | causal (scenario cut) |
| `share_45C_assigned` | — | share of hours anchor→CK_k at 45 °C in the T_main temperature assignment (D1.2) | internals.context | causal (scenario cut) |
| `share_45C_visible` | — | visible 45 °C sample time / (anchor→CK_k hours) | internals.context | causal (scenario cut) |

## Case table, SUB at Δ = 0.4 (same columns as table_cases) — `outputs/table_cases_wide.csv`

| column | unit | definition | source | kind |
|---|---|---|---|---|
| `scenario` | — | scenario: real, PG1, PG2, PC5, PC10 (k 3..7), CS, CSE, PC5_all, PC10_all (k 2..7) | runner5c.SCEN | causal (scenario cut) |
| `k` | — | index of the checkup predicted (1..7) | runner5c.SCEN | causal (scenario cut) |
| `checkup` | — | checkup name CK_k | harness.CK_NAMES | causal (scenario cut) |
| `ck_date` | date | checkup date (framework cut date) | evaluation_points.csv | causal (scenario cut) |
| `delta` | Ah | Δ added to ε0 in the anchor term and in the proxy (0, 0.4, 0.8) | harness.DELTAS | causal (scenario cut) |
| `model` | — | SUB = T_main (submitted), V2_sqrt = V2 + calendar √t, V2 | internals.MODELS | causal (scenario cut) |
| `branch` | — | branch taken: phase, fallback or sqrt_gap | internals.decompose | causal (scenario cut) |
| `Q_pred` | Ah | predicted capacity (asserted equal to the model's own output, < 1e-9 Ah) | internals.decompose / model_q | causal (scenario cut) |
| `SOH_pred` | % | 100·Q_pred/102 | run_wp1.py | causal (scenario cut) |
| `proxy` | Ah | P_k = Q_fc,k (full data) + ε0 + Δ | harness.QFC, EPS0 | reference (full data) |
| `err_Ah` | Ah | Q_pred − proxy | run_wp1.py | reference (full data) |
| `err_pp` | pp | 100·err_Ah/102 | run_wp1.py | reference (full data) |
| `anchor_used` | — | index j of the anchor (post-CK_j empty→full charge) the prediction is built on | internals.decompose | causal (scenario cut) |
| `anchor_t_end` | timestamp | CV end of the anchor used | events.full_charges | causal (scenario cut) |
| `Q_fc_anchor_used` | Ah | integrated charge of the anchor used | events.full_charges | causal (scenario cut) |
| `q_anchor_term` | Ah | anchor term of the prediction: Q_fc + ε0 + Δ (ε0 + EPS_EXTRA_AH in the package), or Q_CK0 = 100.41 for fallback from the 45 °C anchor 0 | internals.decompose | causal (scenario cut) |
| `increment_pred` | Ah | predicted change since the anchor: β·x (phase), after[-1] − after[0] (fallback), −a·(t_k^½ − t_k−1^½) (sqrt_gap) | internals.decompose | causal (scenario cut) |
| `Q_fc_k` | Ah | anchor charge after CK_k from the full data (the proxy's base) | harness.QFC | reference (full data) |
| `increment_obs` | Ah | Q_fc,k − Q_fc_anchor_used | run_wp1.py | reference (full data) |
| `inc_resid_Ah` | Ah | increment_pred − increment_obs; free of ε0 and Δ; the primary case residual | run_wp1.py | reference (full data) |
| `inc_resid_pp` | pp | 100·inc_resid_Ah/102 | run_wp1.py | reference (full data) |
| `offset_part_Ah` | Ah | err_Ah − inc_resid_Ah = q_anchor_term − Q_fc_anchor_used − ε0 − Δ (0, or −Δ for fallback from anchor 0) | run_wp1.py | reference (full data) |
| `offset_part_pp` | pp | 100·offset_part_Ah/102 | run_wp1.py | reference (full data) |
| `uses_first_post_anchor_program` | bool | fallback whose increment uses after[0] with ≥ 2 programs after the anchor (D1.1) | run_wp1.py | causal (scenario cut) |
| `anchor_setpoint` | °C | chamber set point of the anchor charge | events.full_charges | causal (scenario cut) |
| `anchor_is_ck0_45C` | bool | anchor used is anchor 0 at 45 °C | run_wp1.py | causal (scenario cut) |
| `beta_used` | — | β applied to the increment (phase: beta_a4; fallback: 1; sqrt_gap: NaN) | internals.decompose | causal (scenario cut) |
| `beta_a4` | — | β from visible 25 °C anchors (step-to-top change vs Q_fc change), shrunk to 1 with τ = 1 | v2.beta_a4 | causal (scenario cut) |
| `beta_raw` | — | unshrunk LS slope behind beta_a4 (NaN if < 2 usable anchors) | internals.beta_internals | causal (scenario cut) |
| `beta_S` | Ah² | S = Σx² of the step-to-top changes used for β | internals.beta_internals | causal (scenario cut) |
| `beta_shrink_w` | — | weight of the data in β: S/(τ+S) | internals.beta_internals | causal (scenario cut) |
| `beta_n_pairs` | — | number of anchor pairs in β | internals.beta_internals | causal (scenario cut) |
| `x` | Ah | phase-matched month-end 45 °C step change E_cur − E_prev + r·(d_cur − d_prev) | v2.phase_diff | causal (scenario cut) |
| `E_cur` | Ah | last 45 °C step depth of month k−1 | v2.end45 | causal (scenario cut) |
| `E_prev` | Ah | last 45 °C step depth of month k−2 | v2.end45 | causal (scenario cut) |
| `d_cur` | days | days from E_cur's program to CK_k | v2.end45 | causal (scenario cut) |
| `d_prev` | days | days from E_prev's program to CK_k−1 | v2.end45 | causal (scenario cut) |
| `r_cur` | Ah/day | Theil–Sen rate of the 45 °C steps of month k−1 (0 if < 3) | v2.end45 | causal (scenario cut) |
| `r_used` | Ah/day | rate used in x (r_cur if n_cur ≥ 3, else 0); NaN outside phase | internals.decompose | causal (scenario cut) |
| `n_cur` | — | number of 45 °C steps in month k−1 | v2.end45 | causal (scenario cut) |
| `n_prev` | — | number of 45 °C steps in month k−2 | v2.end45 | causal (scenario cut) |
| `gap_days` | days | days from the end of the last visible deep program to CK_k | v3.coverage_gap_days | causal (scenario cut) |
| `sqrt_a` | Ah/day^½ | √t loss coefficient fitted to visible anchors 1..k−1 | internals.decompose | causal (scenario cut) |
| `sqrt_t_km1_days` | days | time axis at CK_k−1 (T_main: 45 °C-equivalent days; V2_sqrt: calendar days since CK0) | tsqrt.t_eff_days | causal (scenario cut) |
| `sqrt_t_k_days` | days | time axis at CK_k (same convention) | tsqrt.t_eff_days | causal (scenario cut) |
| `sqrt_anchors` | — | anchors used in the √t fit, '|'-separated | internals.decompose | causal (scenario cut) |
| `n_after` | — | fallback: number of programs after the anchor | internals.decompose | causal (scenario cut) |
| `ev_E_cur` | timestamp | CV end of the program used as E_cur | internals.decompose | causal (scenario cut) |
| `ev_E_prev` | timestamp | CV end of the program used as E_prev | internals.decompose | causal (scenario cut) |
| `ev_rate_fit` | timestamps | programs in the rate fit, '|'-separated (empty if no rate) | internals.decompose | causal (scenario cut) |
| `ev_after_first` | timestamp | fallback: program after[0] | internals.decompose | causal (scenario cut) |
| `ev_after_last` | timestamp | fallback: program after[-1] | internals.decompose | causal (scenario cut) |
| `days_anchor_to_ck` | days | anchor CV end to CK_k | internals.context | causal (scenario cut) |
| `eff45_days_anchor_to_ck` | days | T_main 45 °C-equivalent days from the anchor to CK_k | internals.context | causal (scenario cut) |
| `cum_fade_at_anchor_Ah` | Ah | 100.41 − Q_fc_anchor_used − ε0 | internals.context | causal (scenario cut) |
| `throughput_dis_Ah_since_anchor` | Ah | integrated discharge (negative current_A) in the cut after the anchor | internals.discharge_since | causal (scenario cut) |
| `share_45C_assigned` | — | share of hours anchor→CK_k at 45 °C in the T_main temperature assignment (D1.2) | internals.context | causal (scenario cut) |
| `share_45C_visible` | — | visible 45 °C sample time / (anchor→CK_k hours) | internals.context | causal (scenario cut) |

## Event table (WP2) — `outputs/table_events.csv`

| column | unit | definition | source | kind |
|---|---|---|---|---|
| `event_id` | — | E00..E40 in time order | run_wp2.py | diagnostic (full data) |
| `unit` | — | cell1_V..cell4_V or pack_mean | run_wp2.py | diagnostic (full data) |
| `t_cv_end` | timestamp | CV end that opens the deep program | events.step_programs | diagnostic (full data) |
| `segment` | — | data segment number | operation data | diagnostic (full data) |
| `setpoint` | °C | chamber set point | operation data | diagnostic (full data) |
| `month` | — | index m of the anchor the event follows | run_wp2.py | diagnostic (full data) |
| `program_index` | — | order of the program after its anchor (1, 2, …) | run_wp2.py | diagnostic (full data) |
| `is_first_after_anchor` | bool | program_index == 1 | run_wp2.py | diagnostic (full data) |
| `ck_index` | — | index of the last checkup date before the event | run_wp2.py | diagnostic (full data) |
| `days_since_anchor` | days | event CV end − anchor CV end | run_wp2.py | diagnostic (full data) |
| `days_since_checkup` | days | event CV end − last checkup date | run_wp2.py | diagnostic (full data) |
| `T_cv_end` | °C | measured temp_mean_C at the CV end | events_merged.csv | diagnostic (full data) |
| `T_at15` | °C | measured temp_mean_C at 15 Ah depth | events_merged.csv | diagnostic (full data) |
| `T_at25` | °C | measured temp_mean_C at 25 Ah depth | events_merged.csv | diagnostic (full data) |
| `T_at35` | °C | measured temp_mean_C at 35 Ah depth | events_merged.csv | diagnostic (full data) |
| `T_at45` | °C | measured temp_mean_C at 45 Ah depth | events_merged.csv | diagnostic (full data) |
| `dT_cv_end` | K | T_cv_end − set point | run_wp2.py | diagnostic (full data) |
| `dT_at45` | K | T_at45 − set point | run_wp2.py | diagnostic (full data) |
| `segment_start` | timestamp | first sample of the event's segment | run_wp2.py | diagnostic (full data) |
| `switch_kind` | — | how the segment began: campaign_start, direct_switch (25→45 °C, gap ≤ 2 d), after_checkup_gap (D2.1) | run_wp2.segment_table | diagnostic (full data) |
| `prev_segment_gap_days` | days | gap between the previous segment's last sample and this segment's first | run_wp2.segment_table | diagnostic (full data) |
| `days_since_switch` | days | event CV end − segment start | run_wp2.py | diagnostic (full data) |
| `rest_before_chg_h` | h | rest before the program-opening charge | events_merged.csv | diagnostic (full data) |
| `chg_Ah` | Ah | Ah of the program-opening CCCV charge | events_merged.csv | diagnostic (full data) |
| `chg_start_pack_V` | V | pack voltage just before that charge | events_merged.csv | diagnostic (full data) |
| `cv_Ah` | Ah | Ah in the CV phase of that charge | events_merged.csv | diagnostic (full data) |
| `cv_h` | h | CV duration | events_merged.csv | diagnostic (full data) |
| `I_cv_end` | A | current at the CV end | events_merged.csv | diagnostic (full data) |
| `throughput_dis_Ah_since_anchor` | Ah | integrated discharge since the anchor CV end | run_wp2.discharge_cum | diagnostic (full data) |
| `throughput_dis_Ah_since_start` | Ah | integrated discharge since the campaign start | run_wp2.discharge_cum | diagnostic (full data) |
| `has_recording_gap` | bool | any Δt > 600 s from charge start to discharge stop | run_wp2.py | diagnostic (full data) |
| `max_depth_Ah` | Ah | maximum depth below the CV end | eventcurves.programs | diagnostic (full data) |
| `V_at15` | V | loaded cell-mean voltage at 15 Ah depth | events_merged.csv | diagnostic (full data) |
| `V_at25` | V | loaded cell-mean voltage at 25 Ah depth | events_merged.csv | diagnostic (full data) |
| `V_at35` | V | loaded cell-mean voltage at 35 Ah depth | events_merged.csv | diagnostic (full data) |
| `V_at45` | V | loaded cell-mean voltage at 45 Ah depth | events_merged.csv | diagnostic (full data) |
| `I_at15` | A | current at 15 Ah depth | events_merged.csv | diagnostic (full data) |
| `I_at25` | A | current at 25 Ah depth | events_merged.csv | diagnostic (full data) |
| `I_at35` | A | current at 35 Ah depth | events_merged.csv | diagnostic (full data) |
| `I_at45` | A | current at 45 Ah depth | events_merged.csv | diagnostic (full data) |
| `R_mean_mOhm` | mΩ | mean per-cell apparent pulse resistance at the 20 A pulse after the CV end (quantised ≈ 0.049 mΩ) | events_merged.csv | diagnostic (full data) |
| `cell_spread_cv_end_V` | V | max − min cell voltage at the CV end | run_wp2.py | diagnostic (full data) |
| `cell_spread_maxdepth_V` | V | max − min cell voltage at maximum depth | run_wp2.py | diagnostic (full data) |
| `weakest_cell_maxdepth` | — | cell with the lowest voltage at maximum depth | run_wp2.py | diagnostic (full data) |
| `Q_interp_Ah` | Ah | Q_fc interpolated linearly in time between the bracketing anchors (NaN after anchor 7) | run_wp2.py | diagnostic (full data) |
| `use_end45_E_cur` | checkups | real-scenario SUB checkups (Δ 0.4) that used this event as E_cur | table_cases ev_* | diagnostic (full data) |
| `use_end45_E_prev` | checkups | same, as E_prev | table_cases ev_* | diagnostic (full data) |
| `use_rate_fit` | checkups | same, in the 45 °C rate fit | table_cases ev_* | diagnostic (full data) |
| `use_after_first` | checkups | same, as fallback after[0] | table_cases ev_* | diagnostic (full data) |
| `use_after_last` | checkups | same, as fallback after[-1] | table_cases ev_* | diagnostic (full data) |
| `used_by_SUB_real` | bool | any of the use flags | run_wp2.py | diagnostic (full data) |
| `depth_main` | Ah | graphite-step depth below the CV end, variant main: the unit's cell locate (cell rows) or the 4-cell mean step_mean (pack_mean) | events.step_programs | diagnostic (full data) |
| `depth_band_narrow` | Ah | graphite-step depth below the CV end, variant band_narrow: the unit's cell locate (cell rows) or the 4-cell mean step_mean (pack_mean) | events.step_programs | diagnostic (full data) |
| `depth_windows_minus3` | Ah | graphite-step depth below the CV end, variant windows_minus3: the unit's cell locate (cell rows) or the 4-cell mean step_mean (pack_mean) | events.step_programs | diagnostic (full data) |
| `depth_windows_plus3` | Ah | graphite-step depth below the CV end, variant windows_plus3: the unit's cell locate (cell rows) or the 4-cell mean step_mean (pack_mean) | events.step_programs | diagnostic (full data) |
| `depth_dvdq_peak` | Ah | graphite-step depth below the CV end, variant dvdq_peak: the unit's cell locate (cell rows) or the 4-cell mean step_mean (pack_mean) | events.step_programs | diagnostic (full data) |
| `depth_ir_corrected` | Ah | graphite-step depth below the CV end, variant ir_corrected: the unit's cell locate (cell rows) or the 4-cell mean step_mean (pack_mean) | events.step_programs | diagnostic (full data) |
| `R_pulse_mOhm` | mΩ | pulse resistance of the unit (pack_mean: cell mean) | events_merged.csv | diagnostic (full data) |
| `start_rest_V` | V | rest voltage before the program-opening charge (pack_mean: sum of cells) | eventcurves.programs | diagnostic (full data) |
| `V_rank_maxdepth` | — | rank of the cell's voltage at maximum depth (1 = lowest); NaN for pack_mean | run_wp2.py | diagnostic (full data) |
| `sharp_height_mV_per_Ah` | mV/Ah | peak of −dV/dQ in 22–42 Ah (0.25 Ah grid, 2 Ah moving average, band samples) | eventcurves.sharpness | diagnostic (full data) |
| `sharp_fwhm_Ah` | Ah | full width at half maximum of that peak | eventcurves.sharpness | diagnostic (full data) |
| `dvdq_peak_Ah` | Ah | depth of that peak | eventcurves.sharpness | diagnostic (full data) |
| `plateau_upper_V` | V | median loaded voltage at 15–25 Ah depth | eventcurves.plateau | diagnostic (full data) |
| `plateau_lower_V` | V | median loaded voltage at 42–50 Ah depth | eventcurves.plateau | diagnostic (full data) |
| `t_days` | days | days since the first event's CV end | run_wp2.add_residuals | diagnostic (full data) |
| `R_seg` | Ah | depth_main − leave-one-out Theil–Sen line (time) of the other events of the same segment and unit; NaN if < 3 others | run_wp2.add_residuals | diagnostic (full data) |
| `R_anc` | Ah | depth_main − (a_sp,unit + 1·Q_interp), a = mean over other months | run_wp2.add_residuals | diagnostic (full data) |
| `a_anc_loo` | Ah | leave-month-out intercept a_sp,unit used in R_anc | run_wp2.add_residuals | diagnostic (full data) |
| `pack_median_depth` | Ah | median of the four cell depth_main of the event | run_wp2.add_residuals | diagnostic (full data) |
| `R_cell` | Ah | depth_main − pack_median_depth | run_wp2.add_residuals | diagnostic (full data) |

## Anchor table (WP3) — `outputs/table_anchors.csv`

| column | unit | definition | source | kind |
|---|---|---|---|---|
| `anchor` | — | anchor index j (first empty→full charge after CK_j) | v2.anchors_by_checkup | diagnostic (full data) |
| `checkup` | — | CK_j | round 7 anchor_state_table | diagnostic (full data) |
| `ck_date` | date | CK_j date | round 7 | diagnostic (full data) |
| `anchor_start` | timestamp | start of the anchor charge | round 7 | diagnostic (full data) |
| `setpoint` | °C | set point during the anchor charge | round 7 | diagnostic (full data) |
| `Q_fc` | Ah | integrated anchor charge | events.full_charges | diagnostic (full data) |
| `dwell_h` | h | last operating sample before the CK_j date → start of the anchor charge | round 7 wp1 | diagnostic (full data) |
| `end_pack_V` | V | pack voltage of the last sample before the CK_j date | round 7 wp1 | diagnostic (full data) |
| `end_I_A` | A | current of that sample | round 7 wp1 | diagnostic (full data) |
| `end_setpoint` | °C | set point of that sample | round 7 wp1 | diagnostic (full data) |
| `end_time` | timestamp | time of that sample ('campaign start' for anchor 0) | round 7 wp1 | diagnostic (full data) |
| `rest_before_h` | h | rest before the anchor charge | round 6 3a | diagnostic (full data) |
| `pack_rest_V` | V | pack rest voltage before the anchor charge | round 6 3a | diagnostic (full data) |
| `r_upper` | Ah | upper bound of the charge left at that rest voltage, from the CK0 C/20 tail | round 6 3a | diagnostic (full data) |
| `r_half` | Ah | r_upper/2 | round 6 3a | diagnostic (full data) |
| `off_median` | Ah | median over variants of the trend-adjusted first-program offset after this anchor | round 7 wp1 | diagnostic (full data) |
| `off_main` | Ah | trend-adjusted first-program offset (raw first − second minus the per-program trend), variant main | round 6 3c | diagnostic (full data) |
| `off_band_narrow` | Ah | trend-adjusted first-program offset (raw first − second minus the per-program trend), variant band_narrow | round 6 3c | diagnostic (full data) |
| `off_windows_minus3` | Ah | trend-adjusted first-program offset (raw first − second minus the per-program trend), variant windows_minus3 | round 6 3c | diagnostic (full data) |
| `off_windows_plus3` | Ah | trend-adjusted first-program offset (raw first − second minus the per-program trend), variant windows_plus3 | round 6 3c | diagnostic (full data) |
| `off_dvdq_peak` | Ah | trend-adjusted first-program offset (raw first − second minus the per-program trend), variant dvdq_peak | round 6 3c | diagnostic (full data) |
| `off_ir_corrected` | Ah | trend-adjusted first-program offset (raw first − second minus the per-program trend), variant ir_corrected | round 6 3c | diagnostic (full data) |
| `n_programs_after` | — | programs after the anchor in its segment | round 6 3c | diagnostic (full data) |
| `first_program_setpoint` | °C | set point of the first program after the anchor | round 6 3c | diagnostic (full data) |
| `second_offset` | Ah | second − third program step difference, trend-adjusted (where ≥ 3 programs) | round 7 wp1 | diagnostic (full data) |
| `bottom_to_step` | Ah | charge-direction Ah from the bottom to the step (4-cell mean) | events.charge_step_split | diagnostic (full data) |
| `step_to_top` | Ah | charge-direction Ah from the step to the top (4-cell mean) | events.charge_step_split | diagnostic (full data) |
| `I_end_A_check` | A | end current of the anchor charge | events.full_charges | diagnostic (full data) |
| `I_cut_common_A` | A | common cut-off = largest end current among the 8 anchors (5.10 A) | run_wp3.py | diagnostic (full data) |
| `Q_fc_cut_common` | Ah | charge up to the first CV sample with current ≤ I_cut_common (D3.1) | run_wp3.q_at_cut | diagnostic (full data) |
| `dQ_cut_common` | Ah | Q_fc_cut_common − Q_fc (0 for all anchors) | run_wp3.py | diagnostic (full data) |
| `Q_fc_cut6A` | Ah | charge up to the first CV sample with current ≤ 6.0 A | run_wp3.q_at_cut | diagnostic (full data) |
| `dQ_cut6A` | Ah | Q_fc_cut6A − Q_fc | run_wp3.py | diagnostic (full data) |
| `cv_Ah` | Ah | charge from the first sample at pack ≥ 13.95 V to the end | run_wp3.py | diagnostic (full data) |
| `cv_h` | h | CV duration | run_wp3.py | diagnostic (full data) |
| `cc_Ah` | Ah | charge before the CV phase | run_wp3.py | diagnostic (full data) |
| `T_charge_mean_C` | °C | mean temp_mean_C during the charge | events.full_charges | diagnostic (full data) |
| `T_charge_max_C` | °C | max temp_mean_C during the charge | run_wp3.py | diagnostic (full data) |
| `start_rest_cell1_V` | V | cell1 rest voltage before the anchor charge | round 6 3a | diagnostic (full data) |
| `start_rest_cell2_V` | V | cell2 rest voltage before the anchor charge | round 6 3a | diagnostic (full data) |
| `start_rest_cell3_V` | V | cell3 rest voltage before the anchor charge | round 6 3a | diagnostic (full data) |
| `start_rest_cell4_V` | V | cell4 rest voltage before the anchor charge | round 6 3a | diagnostic (full data) |
| `start_rest_spread_V` | V | max − min of the four start rest voltages | run_wp3.py | diagnostic (full data) |
| `step_to_top_cell1_V` | Ah | charge-direction step → top distance of cell1 (0.25 Ah grid) | events.charge_step_split | diagnostic (full data) |
| `step_to_top_cell2_V` | Ah | charge-direction step → top distance of cell2 (0.25 Ah grid) | events.charge_step_split | diagnostic (full data) |
| `step_to_top_cell3_V` | Ah | charge-direction step → top distance of cell3 (0.25 Ah grid) | events.charge_step_split | diagnostic (full data) |
| `step_to_top_cell4_V` | Ah | charge-direction step → top distance of cell4 (0.25 Ah grid) | events.charge_step_split | diagnostic (full data) |
| `step_to_top_spread_Ah` | Ah | max − min over cells of step → top | run_wp3.py | diagnostic (full data) |
| `pulse_event_t_cv_end` | timestamp | deep program supplying the pulse resistance (starts at the anchor CV end) | events_merged.csv | diagnostic (full data) |
| `pulse_event_lag_h` | h | its CV end − anchor CV end (0 for all) | run_wp3.py | diagnostic (full data) |
| `R_mean_mOhm` | mΩ | cell-mean pulse resistance at that program | events_merged.csv | diagnostic (full data) |
| `R_cell1_mOhm` | mΩ | cell1 pulse resistance | events_merged.csv | diagnostic (full data) |
| `R_cell2_mOhm` | mΩ | cell2 pulse resistance | events_merged.csv | diagnostic (full data) |
| `R_cell3_mOhm` | mΩ | cell3 pulse resistance | events_merged.csv | diagnostic (full data) |
| `R_cell4_mOhm` | mΩ | cell4 pulse resistance | events_merged.csv | diagnostic (full data) |
| `end_cell1_V` | V | cell1 voltage at the anchor CV end | events.full_charges | diagnostic (full data) |
| `end_cell2_V` | V | cell2 voltage at the anchor CV end | events.full_charges | diagnostic (full data) |
| `end_cell3_V` | V | cell3 voltage at the anchor CV end | events.full_charges | diagnostic (full data) |
| `end_cell4_V` | V | cell4 voltage at the anchor CV end | events.full_charges | diagnostic (full data) |
| `cv_end_spread_V` | V | max − min cell voltage at the CV end | run_wp3.py | diagnostic (full data) |
| `dR_mean_from_anchor0_mOhm` | mΩ | R_mean_mOhm − anchor 0 value | run_wp3.py | diagnostic (full data) |
| `dR_cell1_mOhm_from_anchor0` | mΩ | R_cell1_mOhm − anchor 0 value | run_wp3.py | diagnostic (full data) |
| `dR_cell2_mOhm_from_anchor0` | mΩ | R_cell2_mOhm − anchor 0 value | run_wp3.py | diagnostic (full data) |
| `dR_cell3_mOhm_from_anchor0` | mΩ | R_cell3_mOhm − anchor 0 value | run_wp3.py | diagnostic (full data) |
| `dR_cell4_mOhm_from_anchor0` | mΩ | R_cell4_mOhm − anchor 0 value | run_wp3.py | diagnostic (full data) |
| `dQ_fc_next` | Ah | Q_fc of the next anchor − Q_fc | run_wp3.py | diagnostic (full data) |
| `dQ_fc_cut_common_next` | Ah | same with the common cut-off | run_wp3.py | diagnostic (full data) |
| `dQ_fc_cut6A_next` | Ah | same with the 6 A cut-off | run_wp3.py | diagnostic (full data) |
| `cum_fade_Ah` | Ah | 100.41 − Q_fc − ε0 | run_wp3.py | diagnostic (full data) |

## Cycle (SOC swing) table (WP4) — `outputs/table_cycles.csv`

| column | unit | definition | source | kind |
|---|---|---|---|---|
| `cycle_id` | — | C0000.. in time order | run_wp4.py | diagnostic (full data) |
| `t_top` | timestamp | SOC top starting the swing | run_wp4.py | diagnostic (full data) |
| `segment` | — | segment | operation data | diagnostic (full data) |
| `setpoint` | °C | set point | operation data | diagnostic (full data) |
| `month` | — | index of the anchor before t_top | run_wp4.py | diagnostic (full data) |
| `program_block` | — | number of deep-program CV ends at or before t_top (block between consecutive programs) | run_wp4.py | diagnostic (full data) |
| `slot` | — | order of the swing inside its program block | run_wp4.py | diagnostic (full data) |
| `t_bottom` | timestamp | lowest SOC point of the swing | run_wp4.py | diagnostic (full data) |
| `t_next_top` | timestamp | next SOC top (end of the swing) | run_wp4.py | diagnostic (full data) |
| `ck_index` | — | last checkup before t_top | run_wp4.py | diagnostic (full data) |
| `hours_since_program` | h | t_top − last deep-program CV end | run_wp4.py | diagnostic (full data) |
| `hours_since_segment_start` | h | t_top − segment start | run_wp4.py | diagnostic (full data) |
| `V_top_pack` | V | pack voltage at t_top (loaded or not) | run_wp4.py | diagnostic (full data) |
| `I_top` | A | current at t_top | run_wp4.py | diagnostic (full data) |
| `V_bottom_pack` | V | pack voltage at t_bottom | run_wp4.py | diagnostic (full data) |
| `I_bottom` | A | current at t_bottom | run_wp4.py | diagnostic (full data) |
| `V_next_top_pack` | V | pack voltage at t_next_top | run_wp4.py | diagnostic (full data) |
| `V_rest_1h_after_top` | V | voltage 1 h after the top if the pack rested the whole hour (never: all NaN) | run_wp4.py | diagnostic (full data) |
| `Ah_discharged` | Ah | integrated discharge top → bottom | run_wp4.py | diagnostic (full data) |
| `Ah_charged` | Ah | integrated charge bottom → next top | run_wp4.py | diagnostic (full data) |
| `swing_down_Ah` | Ah | net Ah top → bottom | run_wp4.py | diagnostic (full data) |
| `swing_up_Ah` | Ah | net Ah bottom → next top | run_wp4.py | diagnostic (full data) |
| `cv_reached` | bool | pack ≥ 13.95 V while charging between bottom and next top | run_wp4.py | diagnostic (full data) |
| `top_Ah_rel_last_cv_end` | Ah | segment-integrated Ah at the next top minus at the last CV end (same segment) | run_wp4.py | diagnostic (full data) |
| `cell_spread_top_V` | V | max − min cell voltage at the next top | run_wp4.py | diagnostic (full data) |
| `cell_spread_bottom_V` | V | max − min cell voltage at the bottom | run_wp4.py | diagnostic (full data) |
| `T_mean_C` | °C | mean measured temperature over the swing | run_wp4.py | diagnostic (full data) |
| `dT_mean` | K | T_mean_C − set point | run_wp4.py | diagnostic (full data) |
| `duration_h` | h | t_next_top − t_top | run_wp4.py | diagnostic (full data) |
| `R_cyc_top_Ah_rel_last_cv_end` | Ah | top_Ah_rel_last_cv_end minus the leave-one-out median of the centred 7-cycle window, same set point (prompt definition; mixes profile phases) | run_wp4.r_cyc | diagnostic (full data) |
| `R_cyc_slot_top_Ah_rel_last_cv_end` | Ah | top_Ah_rel_last_cv_end minus the leave-one-out median of the same slot in ±3 blocks, same set point (D4.1) | run_wp4.r_cyc_slot | diagnostic (full data) |
| `R_cyc_V_bottom_pack` | V | V_bottom_pack minus the leave-one-out median of the centred 7-cycle window, same set point (prompt definition; mixes profile phases) | run_wp4.r_cyc | diagnostic (full data) |
| `R_cyc_slot_V_bottom_pack` | V | V_bottom_pack minus the leave-one-out median of the same slot in ±3 blocks, same set point (D4.1) | run_wp4.r_cyc_slot | diagnostic (full data) |
| `R_cyc_swing_down_Ah` | Ah | swing_down_Ah minus the leave-one-out median of the centred 7-cycle window, same set point (prompt definition; mixes profile phases) | run_wp4.r_cyc | diagnostic (full data) |
| `R_cyc_slot_swing_down_Ah` | Ah | swing_down_Ah minus the leave-one-out median of the same slot in ±3 blocks, same set point (D4.1) | run_wp4.r_cyc_slot | diagnostic (full data) |

## WP5 event columns — `wp5/outputs/events_wp5_columns.csv`

| column | unit | definition | source | kind |
|---|---|---|---|---|
| `event_id` | — | E00..E40 in time order | run_wp2.py | diagnostic (full data) |
| `unit` | — | cell1_V..cell4_V or pack_mean | run_wp2.py | diagnostic (full data) |
| `R_anc_b` | Ah | depth_main − (a_25/a_45 + b·Q_interp), leave-month-out OLS per unit (registered secondary) | run_wp5.r_anc_b | diagnostic (full data) |
| `cum_fade_Ah` | Ah | 100.41 − Q_interp − ε0 | run_wp5.load | diagnostic (full data) |
| `fade_pct` | % | 100·cum_fade/102 | run_wp5.load | diagnostic (full data) |
| `fade_bin` | — | registered fade bin 0-3 / 3-6 / >6 % | protocol.json | diagnostic (full data) |
| `switch_bin` | — | registered days-since-switch bin 0-2 / 2-5 / >5 | protocol.json | diagnostic (full data) |
| `dT_bin` | — | dT_at45 tercile per set point (low/mid/high) | protocol.json | diagnostic (full data) |
| `sharp_bin` | — | sharpness tercile (pack or cell edges) | protocol.json | diagnostic (full data) |
| `month_group` | — | m0-2 / m3-5 / m6-7 | protocol.json | diagnostic (full data) |

## Error budget, SUB real Δ = 0.4 (WP6) — `wp6/outputs/error_budget_real_d04.csv`

| column | unit | definition | source | kind |
|---|---|---|---|---|
| `checkup` | — | checkup name CK_k | harness.CK_NAMES | causal (scenario cut) |
| `branch` | — | branch taken: phase, fallback or sqrt_gap | internals.decompose | causal (scenario cut) |
| `err_Ah` | Ah | Q_pred − proxy | run_wp1.py | reference (full data) |
| `err_pp` | pp | 100·err_Ah/102 | run_wp1.py | reference (full data) |
| `offset_part_Ah` | Ah | err_Ah − inc_resid_Ah = q_anchor_term − Q_fc_anchor_used − ε0 − Δ (0, or −Δ for fallback from anchor 0) | run_wp1.py | reference (full data) |
| `inc_resid_Ah` | Ah | increment_pred − increment_obs; free of ε0 and Δ; the primary case residual | run_wp1.py | reference (full data) |
| `inc_resid_pp` | pp | 100·inc_resid_Ah/102 | run_wp1.py | reference (full data) |
| `contrib_beta_vs_step_scaling_Ah` | Ah | increment_pred − raw increment/b (b = 0.745): β used vs the step's sub-unity sensitivity | wp6/run_wp6.py | reference (full data) |
| `contrib_first_program_offset_Ah` | Ah | fallback: −off_main of the anchor (the deeper first program); phase: 0 | wp6/run_wp6.py | reference (full data) |
| `contrib_cell_mean_vs_median_Ah` | Ah | increment from cell means minus increment from cell medians | wp6/run_wp6.py | reference (full data) |
| `H4_trend_fitted_Ah` | Ah | fitted value of the H4 line inc_resid ~ cum_fade_at_anchor (all SUB cases) | wp6/run_wp6.py | reference (full data) |
| `rest_Ah` | Ah | inc_resid − sum of the three contributions (descriptive; contributions interact) | wp6/run_wp6.py | reference (full data) |

---

<a id="zh"></a>

# 数据字典（第 8 轮）

> **语言：** [English](#en) · 中文

覆盖每张表的每一列。符号约定：残差 = 预测 − 参考；pp = 100·Ah/102。类型：因果 = 由场景截断数据计算；诊断 = 由全量数据构建；参考 = 使用全量数据的代理 Q_fc,k。

## 案例表（WP1） — `outputs/table_cases.csv`

| 列 | 单位 | 定义 |
|---|---|---|
| `scenario` | — | 场景名 |
| `k` | — | 被预测检查点序号 |
| `checkup` | — | 检查点名称 |
| `ck_date` | date | 检查日期（框架截断日期） |
| `delta` | Ah | 加在 ε0 上的 Δ（锚点项与代理中） |
| `model` | — | 模型：SUB = T_main（提交版）、V2_sqrt、V2 |
| `branch` | — | 所走分支 |
| `Q_pred` | Ah | 预测容量（断言等于模型输出） |
| `SOH_pred` | % | 预测 SOH |
| `proxy` | Ah | 代理真值 P_k |
| `err_Ah` | Ah | 预测误差 |
| `err_pp` | pp | 预测误差（pp） |
| `anchor_used` | — | 所用锚点序号 j |
| `anchor_t_end` | timestamp | 所用锚点的 CV 结束时刻 |
| `Q_fc_anchor_used` | Ah | 所用锚点充电量 |
| `q_anchor_term` | Ah | 预测中的锚点项 |
| `increment_pred` | Ah | 预测的锚点后变化量 |
| `Q_fc_k` | Ah | CK_k 后锚点充电量（全量数据） |
| `increment_obs` | Ah | 观测增量 |
| `inc_resid_Ah` | Ah | 增量残差（主残差） |
| `inc_resid_pp` | pp | 增量残差（pp） |
| `offset_part_Ah` | Ah | 偏移部分 |
| `offset_part_pp` | pp | 偏移部分（pp） |
| `uses_first_post_anchor_program` | bool | fallback 增量是否用到锚点后首个程序 |
| `anchor_setpoint` | °C | 锚点充电时的设定温度 |
| `anchor_is_ck0_45C` | bool | 所用锚点是否为 45 °C 的锚点 0 |
| `beta_used` | — | 实际使用的 β |
| `beta_a4` | — | 由 25 °C 锚点估计并收缩的 β |
| `beta_raw` | — | 未收缩的最小二乘斜率 |
| `beta_S` | Ah² | β 所用 Σx² |
| `beta_shrink_w` | — | β 中数据的权重 |
| `beta_n_pairs` | — | β 所用锚点对数 |
| `x` | Ah | 相位匹配的月末 45 °C 台阶变化 |
| `E_cur` | Ah | 第 k−1 月最后一个 45 °C 台阶深度 |
| `E_prev` | Ah | 第 k−2 月最后一个 45 °C 台阶深度 |
| `d_cur` | days | E_cur 程序到 CK_k 的天数 |
| `d_prev` | days | E_prev 程序到 CK_k−1 的天数 |
| `r_cur` | Ah/day | 第 k−1 月 45 °C 台阶速率 |
| `r_used` | Ah/day | x 中使用的速率 |
| `n_cur` | — | 第 k−1 月 45 °C 台阶数 |
| `n_prev` | — | 第 k−2 月 45 °C 台阶数 |
| `gap_days` | days | 最后一个可见深放程序结束到 CK_k 的天数 |
| `sqrt_a` | Ah/day^½ | √t 损失系数 |
| `sqrt_t_km1_days` | days | CK_k−1 处的时间轴值 |
| `sqrt_t_k_days` | days | CK_k 处的时间轴值 |
| `sqrt_anchors` | — | √t 拟合所用锚点 |
| `n_after` | — | fallback：锚点后程序数 |
| `ev_E_cur` | timestamp | 作为 E_cur 的程序 |
| `ev_E_prev` | timestamp | 作为 E_prev 的程序 |
| `ev_rate_fit` | timestamps | 速率拟合所用程序 |
| `ev_after_first` | timestamp | fallback：after[0] 程序 |
| `ev_after_last` | timestamp | fallback：after[-1] 程序 |
| `days_anchor_to_ck` | days | 锚点到 CK_k 的天数 |
| `eff45_days_anchor_to_ck` | days | 锚点到 CK_k 的 45 °C 等效天数 |
| `cum_fade_at_anchor_Ah` | Ah | 锚点处累计衰减 |
| `throughput_dis_Ah_since_anchor` | Ah | 锚点以来积分放电量 |
| `share_45C_assigned` | — | T_main 温度分配中 45 °C 的小时占比 |
| `share_45C_visible` | — | 可见 45 °C 样本时间占比 |

## 案例宽表（SUB，Δ = 0.4，列同上） — `outputs/table_cases_wide.csv`

| 列 | 单位 | 定义 |
|---|---|---|
| `scenario` | — | 场景名 |
| `k` | — | 被预测检查点序号 |
| `checkup` | — | 检查点名称 |
| `ck_date` | date | 检查日期（框架截断日期） |
| `delta` | Ah | 加在 ε0 上的 Δ（锚点项与代理中） |
| `model` | — | 模型：SUB = T_main（提交版）、V2_sqrt、V2 |
| `branch` | — | 所走分支 |
| `Q_pred` | Ah | 预测容量（断言等于模型输出） |
| `SOH_pred` | % | 预测 SOH |
| `proxy` | Ah | 代理真值 P_k |
| `err_Ah` | Ah | 预测误差 |
| `err_pp` | pp | 预测误差（pp） |
| `anchor_used` | — | 所用锚点序号 j |
| `anchor_t_end` | timestamp | 所用锚点的 CV 结束时刻 |
| `Q_fc_anchor_used` | Ah | 所用锚点充电量 |
| `q_anchor_term` | Ah | 预测中的锚点项 |
| `increment_pred` | Ah | 预测的锚点后变化量 |
| `Q_fc_k` | Ah | CK_k 后锚点充电量（全量数据） |
| `increment_obs` | Ah | 观测增量 |
| `inc_resid_Ah` | Ah | 增量残差（主残差） |
| `inc_resid_pp` | pp | 增量残差（pp） |
| `offset_part_Ah` | Ah | 偏移部分 |
| `offset_part_pp` | pp | 偏移部分（pp） |
| `uses_first_post_anchor_program` | bool | fallback 增量是否用到锚点后首个程序 |
| `anchor_setpoint` | °C | 锚点充电时的设定温度 |
| `anchor_is_ck0_45C` | bool | 所用锚点是否为 45 °C 的锚点 0 |
| `beta_used` | — | 实际使用的 β |
| `beta_a4` | — | 由 25 °C 锚点估计并收缩的 β |
| `beta_raw` | — | 未收缩的最小二乘斜率 |
| `beta_S` | Ah² | β 所用 Σx² |
| `beta_shrink_w` | — | β 中数据的权重 |
| `beta_n_pairs` | — | β 所用锚点对数 |
| `x` | Ah | 相位匹配的月末 45 °C 台阶变化 |
| `E_cur` | Ah | 第 k−1 月最后一个 45 °C 台阶深度 |
| `E_prev` | Ah | 第 k−2 月最后一个 45 °C 台阶深度 |
| `d_cur` | days | E_cur 程序到 CK_k 的天数 |
| `d_prev` | days | E_prev 程序到 CK_k−1 的天数 |
| `r_cur` | Ah/day | 第 k−1 月 45 °C 台阶速率 |
| `r_used` | Ah/day | x 中使用的速率 |
| `n_cur` | — | 第 k−1 月 45 °C 台阶数 |
| `n_prev` | — | 第 k−2 月 45 °C 台阶数 |
| `gap_days` | days | 最后一个可见深放程序结束到 CK_k 的天数 |
| `sqrt_a` | Ah/day^½ | √t 损失系数 |
| `sqrt_t_km1_days` | days | CK_k−1 处的时间轴值 |
| `sqrt_t_k_days` | days | CK_k 处的时间轴值 |
| `sqrt_anchors` | — | √t 拟合所用锚点 |
| `n_after` | — | fallback：锚点后程序数 |
| `ev_E_cur` | timestamp | 作为 E_cur 的程序 |
| `ev_E_prev` | timestamp | 作为 E_prev 的程序 |
| `ev_rate_fit` | timestamps | 速率拟合所用程序 |
| `ev_after_first` | timestamp | fallback：after[0] 程序 |
| `ev_after_last` | timestamp | fallback：after[-1] 程序 |
| `days_anchor_to_ck` | days | 锚点到 CK_k 的天数 |
| `eff45_days_anchor_to_ck` | days | 锚点到 CK_k 的 45 °C 等效天数 |
| `cum_fade_at_anchor_Ah` | Ah | 锚点处累计衰减 |
| `throughput_dis_Ah_since_anchor` | Ah | 锚点以来积分放电量 |
| `share_45C_assigned` | — | T_main 温度分配中 45 °C 的小时占比 |
| `share_45C_visible` | — | 可见 45 °C 样本时间占比 |

## 事件表（WP2） — `outputs/table_events.csv`

| 列 | 单位 | 定义 |
|---|---|---|
| `event_id` | — | 事件编号 |
| `unit` | — | 单元：单体或 pack 均值 |
| `t_cv_end` | timestamp | 深放程序开始的 CV 结束时刻 |
| `segment` | — | 数据段号 |
| `setpoint` | °C | 箱体设定温度 |
| `month` | — | 事件所跟随的锚点序号 |
| `program_index` | — | 锚点后的程序序号 |
| `is_first_after_anchor` | bool | 是否为锚点后首个程序 |
| `ck_index` | — | 事件前最后一个检查点序号 |
| `days_since_anchor` | days | 距锚点天数 |
| `days_since_checkup` | days | 距检查日期天数 |
| `T_cv_end` | °C | CV 结束时实测温度 |
| `T_at15` | °C | 15 Ah 深度处实测温度 |
| `T_at25` | °C | 25 Ah 深度处实测温度 |
| `T_at35` | °C | 35 Ah 深度处实测温度 |
| `T_at45` | °C | 45 Ah 深度处实测温度 |
| `dT_cv_end` | K | CV 结束时实测温度与设定点之差 |
| `dT_at45` | K | 45 Ah 处实测温度与设定点之差 |
| `segment_start` | timestamp | 所在段起点 |
| `switch_kind` | — | 段起点类型 |
| `prev_segment_gap_days` | days | 与上一段的间隔 |
| `days_since_switch` | days | 距段起点（切换）天数 |
| `rest_before_chg_h` | h | 开程序充电前静置时间 |
| `chg_Ah` | Ah | 开程序 CCCV 充电量 |
| `chg_start_pack_V` | V | 该充电前的 pack 电压 |
| `cv_Ah` | Ah | 该充电 CV 阶段电量 |
| `cv_h` | h | CV 时长 |
| `I_cv_end` | A | CV 结束电流 |
| `throughput_dis_Ah_since_anchor` | Ah | 锚点以来积分放电量 |
| `throughput_dis_Ah_since_start` | Ah | 试验开始以来积分放电量 |
| `has_recording_gap` | bool | 程序内是否有 > 600 s 记录空档 |
| `max_depth_Ah` | Ah | 最大放电深度 |
| `V_at15` | V | 15 Ah 处带载单体均值电压 |
| `V_at25` | V | 25 Ah 处带载单体均值电压 |
| `V_at35` | V | 35 Ah 处带载单体均值电压 |
| `V_at45` | V | 45 Ah 处带载单体均值电压 |
| `I_at15` | A | 15 Ah 处电流 |
| `I_at25` | A | 25 Ah 处电流 |
| `I_at35` | A | 35 Ah 处电流 |
| `I_at45` | A | 45 Ah 处电流 |
| `R_mean_mOhm` | mΩ | 四单体平均脉冲内阻 |
| `cell_spread_cv_end_V` | V | CV 结束时单体电压差 |
| `cell_spread_maxdepth_V` | V | 最大深度处单体电压差 |
| `weakest_cell_maxdepth` | — | 最大深度处最弱单体 |
| `Q_interp_Ah` | Ah | 按时间插值的锚点 Q_fc |
| `use_end45_E_cur` | checkups | 以该事件为 E_cur 的真实检查点 |
| `use_end45_E_prev` | checkups | 以该事件为 E_prev 的检查点 |
| `use_rate_fit` | checkups | 在速率拟合中使用该事件的检查点 |
| `use_after_first` | checkups | 作为 after[0] 的检查点 |
| `use_after_last` | checkups | 作为 after[-1] 的检查点 |
| `used_by_SUB_real` | bool | 是否被真实场景 SUB 使用 |
| `depth_main` | Ah | 变体 main 的台阶深度 |
| `depth_band_narrow` | Ah | 变体 band_narrow 的台阶深度 |
| `depth_windows_minus3` | Ah | 变体 windows_minus3 的台阶深度 |
| `depth_windows_plus3` | Ah | 变体 windows_plus3 的台阶深度 |
| `depth_dvdq_peak` | Ah | 变体 dvdq_peak 的台阶深度 |
| `depth_ir_corrected` | Ah | 变体 ir_corrected 的台阶深度 |
| `R_pulse_mOhm` | mΩ | 该单元脉冲内阻 |
| `start_rest_V` | V | 开程序充电前静置电压 |
| `V_rank_maxdepth` | — | 最大深度处电压排名 |
| `sharp_height_mV_per_Ah` | mV/Ah | 台阶 −dV/dQ 峰高 |
| `sharp_fwhm_Ah` | Ah | 峰的半高宽 |
| `dvdq_peak_Ah` | Ah | 峰位深度 |
| `plateau_upper_V` | V | 上平台电压中位数 |
| `plateau_lower_V` | V | 下平台电压中位数 |
| `t_days` | days | 距首个事件的天数 |
| `R_seg` | Ah | 段内残差 |
| `R_anc` | Ah | 锚点跟踪残差（b = 1） |
| `a_anc_loo` | Ah | R_anc 的留月截距 |
| `pack_median_depth` | Ah | 四单体深度中位数 |
| `R_cell` | Ah | 单体离散残差 |

## 锚点表（WP3） — `outputs/table_anchors.csv`

| 列 | 单位 | 定义 |
|---|---|---|
| `anchor` | — | 锚点序号 |
| `checkup` | — | 检查点 |
| `ck_date` | date | 检查日期 |
| `anchor_start` | timestamp | 锚点充电开始 |
| `setpoint` | °C | 锚点充电设定温度 |
| `Q_fc` | Ah | 锚点充电量 |
| `dwell_h` | h | 检查前最后样本到锚点充电的小时数 |
| `end_pack_V` | V | 检查前最后样本 pack 电压 |
| `end_I_A` | A | 该样本电流 |
| `end_setpoint` | °C | 该样本设定温度 |
| `end_time` | timestamp | 该样本时刻 |
| `rest_before_h` | h | 锚点充电前静置 |
| `pack_rest_V` | V | 锚点充电前 pack 静置电压 |
| `r_upper` | Ah | 起始剩余电量上界 |
| `r_half` | Ah | r_upper 的一半 |
| `off_median` | Ah | 首个程序偏移（各变体中位数） |
| `off_main` | Ah | 变体 main 的首个程序偏移 |
| `off_band_narrow` | Ah | 变体 band_narrow 的首个程序偏移 |
| `off_windows_minus3` | Ah | 变体 windows_minus3 的首个程序偏移 |
| `off_windows_plus3` | Ah | 变体 windows_plus3 的首个程序偏移 |
| `off_dvdq_peak` | Ah | 变体 dvdq_peak 的首个程序偏移 |
| `off_ir_corrected` | Ah | 变体 ir_corrected 的首个程序偏移 |
| `n_programs_after` | — | 锚点所在段内其后的程序数 |
| `first_program_setpoint` | °C | 首个程序设定温度 |
| `second_offset` | Ah | 第二与第三个程序的差 |
| `bottom_to_step` | Ah | 充电方向底部到台阶 |
| `step_to_top` | Ah | 充电方向台阶到顶部 |
| `I_end_A_check` | A | 锚点充电终止电流 |
| `I_cut_common_A` | A | 公共截止电流 |
| `Q_fc_cut_common` | Ah | 公共截止下的充电量 |
| `dQ_cut_common` | Ah | 与 Q_fc 之差 |
| `Q_fc_cut6A` | Ah | 6 A 截止下的充电量 |
| `dQ_cut6A` | Ah | 与 Q_fc 之差 |
| `cv_Ah` | Ah | CV 阶段电量 |
| `cv_h` | h | CV 时长 |
| `cc_Ah` | Ah | CV 之前的电量 |
| `T_charge_mean_C` | °C | 充电期间平均温度 |
| `T_charge_max_C` | °C | 充电期间最高温度 |
| `start_rest_cell1_V` | V | cell1 充电前静置电压 |
| `start_rest_cell2_V` | V | cell2 充电前静置电压 |
| `start_rest_cell3_V` | V | cell3 充电前静置电压 |
| `start_rest_cell4_V` | V | cell4 充电前静置电压 |
| `start_rest_spread_V` | V | 静置电压单体差 |
| `step_to_top_cell1_V` | Ah | cell1 台阶到顶部距离 |
| `step_to_top_cell2_V` | Ah | cell2 台阶到顶部距离 |
| `step_to_top_cell3_V` | Ah | cell3 台阶到顶部距离 |
| `step_to_top_cell4_V` | Ah | cell4 台阶到顶部距离 |
| `step_to_top_spread_Ah` | Ah | 台阶到顶部的单体差 |
| `pulse_event_t_cv_end` | timestamp | 提供脉冲内阻的程序 |
| `pulse_event_lag_h` | h | 与锚点的时间差 |
| `R_mean_mOhm` | mΩ | 单体平均脉冲内阻 |
| `R_cell1_mOhm` | mΩ | cell1 脉冲内阻 |
| `R_cell2_mOhm` | mΩ | cell2 脉冲内阻 |
| `R_cell3_mOhm` | mΩ | cell3 脉冲内阻 |
| `R_cell4_mOhm` | mΩ | cell4 脉冲内阻 |
| `end_cell1_V` | V | cell1 CV 结束电压 |
| `end_cell2_V` | V | cell2 CV 结束电压 |
| `end_cell3_V` | V | cell3 CV 结束电压 |
| `end_cell4_V` | V | cell4 CV 结束电压 |
| `cv_end_spread_V` | V | CV 结束时单体电压差 |
| `dR_mean_from_anchor0_mOhm` | mΩ | 相对锚点 0 的平均内阻变化 |
| `dR_cell1_mOhm_from_anchor0` | mΩ | cell1 内阻相对锚点 0 的变化 |
| `dR_cell2_mOhm_from_anchor0` | mΩ | cell2 内阻相对锚点 0 的变化 |
| `dR_cell3_mOhm_from_anchor0` | mΩ | cell3 内阻相对锚点 0 的变化 |
| `dR_cell4_mOhm_from_anchor0` | mΩ | cell4 内阻相对锚点 0 的变化 |
| `dQ_fc_next` | Ah | 到下一锚点的 ΔQ_fc |
| `dQ_fc_cut_common_next` | Ah | 公共截止下的 ΔQ_fc |
| `dQ_fc_cut6A_next` | Ah | 6 A 截止下的 ΔQ_fc |
| `cum_fade_Ah` | Ah | 累计衰减 |

## 循环（SOC 摆动）表（WP4） — `outputs/table_cycles.csv`

| 列 | 单位 | 定义 |
|---|---|---|
| `cycle_id` | — | 循环编号 |
| `t_top` | timestamp | 摆动起始 SOC 顶点 |
| `segment` | — | 段号 |
| `setpoint` | °C | 设定温度 |
| `month` | — | 所跟随的锚点序号 |
| `program_block` | — | 程序周期编号 |
| `slot` | — | 周期内槽位 |
| `t_bottom` | timestamp | 摆动最低点 |
| `t_next_top` | timestamp | 下一个顶点 |
| `ck_index` | — | 此前最后检查点 |
| `hours_since_program` | h | 距上一深放程序的小时数 |
| `hours_since_segment_start` | h | 距段起点小时数 |
| `V_top_pack` | V | 顶点 pack 电压 |
| `I_top` | A | 顶点电流 |
| `V_bottom_pack` | V | 最低点 pack 电压 |
| `I_bottom` | A | 最低点电流 |
| `V_next_top_pack` | V | 下一顶点 pack 电压 |
| `V_rest_1h_after_top` | V | 顶点后 1 h 静置电压（全为 NaN） |
| `Ah_discharged` | Ah | 顶点到最低点放电量 |
| `Ah_charged` | Ah | 最低点到下一顶点充电量 |
| `swing_down_Ah` | Ah | 下摆净 Ah |
| `swing_up_Ah` | Ah | 上摆净 Ah |
| `cv_reached` | bool | 是否到达 CV |
| `top_Ah_rel_last_cv_end` | Ah | 顶点相对上次 CV 结束的 Ah |
| `cell_spread_top_V` | V | 顶点单体电压差 |
| `cell_spread_bottom_V` | V | 最低点单体电压差 |
| `T_mean_C` | °C | 摆动期间平均温度 |
| `dT_mean` | K | 与设定点之差 |
| `duration_h` | h | 摆动时长 |
| `R_cyc_top_Ah_rel_last_cv_end` | Ah | top_Ah_rel_last_cv_end 的 7 循环留一中位数残差 |
| `R_cyc_slot_top_Ah_rel_last_cv_end` | Ah | top_Ah_rel_last_cv_end 的同槽位残差 |
| `R_cyc_V_bottom_pack` | V | V_bottom_pack 的 7 循环留一中位数残差 |
| `R_cyc_slot_V_bottom_pack` | V | V_bottom_pack 的同槽位残差 |
| `R_cyc_swing_down_Ah` | Ah | swing_down_Ah 的 7 循环留一中位数残差 |
| `R_cyc_slot_swing_down_Ah` | Ah | swing_down_Ah 的同槽位残差 |

## WP5 事件附加列 — `wp5/outputs/events_wp5_columns.csv`

| 列 | 单位 | 定义 |
|---|---|---|
| `event_id` | — | 事件编号 |
| `unit` | — | 单元：单体或 pack 均值 |
| `R_anc_b` | Ah | 自由斜率锚点残差 |
| `cum_fade_Ah` | Ah | 事件处累计衰减 |
| `fade_pct` | % | 累计衰减百分比 |
| `fade_bin` | — | 衰减分箱 |
| `switch_bin` | — | 切换天数分箱 |
| `dT_bin` | — | 温差三分位 |
| `sharp_bin` | — | 尖锐度三分位 |
| `month_group` | — | 月份组 |

## 误差预算（WP6） — `wp6/outputs/error_budget_real_d04.csv`

| 列 | 单位 | 定义 |
|---|---|---|
| `checkup` | — | 检查点名称 |
| `branch` | — | 所走分支 |
| `err_Ah` | Ah | 预测误差 |
| `err_pp` | pp | 预测误差（pp） |
| `offset_part_Ah` | Ah | 偏移部分 |
| `inc_resid_Ah` | Ah | 增量残差（主残差） |
| `inc_resid_pp` | pp | 增量残差（pp） |
| `contrib_beta_vs_step_scaling_Ah` | Ah | β 与台阶比例的差贡献 |
| `contrib_first_program_offset_Ah` | Ah | 首个程序偏移贡献 |
| `contrib_cell_mean_vs_median_Ah` | Ah | 单体均值与中位数之差贡献 |
| `H4_trend_fitted_Ah` | Ah | H4 趋势拟合值 |
| `rest_Ah` | Ah | 剩余部分 |
