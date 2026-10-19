"""WP1: write wp1/protocol.json (registered protocol of round 12) and wp1/protocol.sha256.

The constants below are written by hand; src/test_registered.py checks that the registered modules use them.
The §2 definitions and the §4 gates and decision rules are copied verbatim from EXECUTION_PROMPT.md."""
import hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ST = os.path.dirname(HERE)
PROMPT = os.path.join(ST, "EXECUTION_PROMPT.md")
OUT = os.path.join(ST, "wp1")
REGISTERED_CODE = ["src/locators.py", "src/ahchain.py", "src/test_registered.py", "src/wp1_protocol.py"]


def english_part():
    s = open(PROMPT, encoding="utf-8").read()
    return s[:s.index('<a id="zh"></a>')]


def between(text, start, end):
    a = text.index(start)
    b = text.index(end, a)
    return text[a:b].rstrip()


def section4_bullets(text):
    block = between(text, "- **G_noise (WP3).**", "\n---")
    return block.splitlines()


CONSTANTS = {
    # locators: charge side
    "locators.GRID_DX_AH": 0.05,
    "locators.GRID_MARGIN_PTS": 3,
    "locators.CC_I_MIN_A": 20.0,
    "locators.CL_SMOOTH_AH": {"CL1": 2.0, "CL2": 1.0, "CL3": 3.0},
    "locators.CL_WINDOW_AH": [50.0, 80.0],
    "locators.MID_WINDOWS_AH": {"4": [5.0, 15.0], "5": [10.0, 20.0]},
    "locators.MIN_PLATEAU_SAMPLES": 5,
    "locators.MIN_VARIANTS": 4,
    "locators.MIN_CELLS": 3,
    # locators: discharge side and programs
    "locators.DL_SMOOTH_AH": {"DL1": 2.0, "DL2": 1.0, "DL3": 3.0},
    "locators.CK0_Q_AH": 100.41,
    "locators.DL_WINDOW_FROM_END_AH": [50.0, 80.0],
    "locators.PROG_BAND_A": [-12.5, -8.0],
    "locators.PROG_RECHARGE_AH": 2.0,
    "locators.PROG_MIN_DEPTH_AH": 50.0,
    "locators.PROG_MIN_BAND_SAMPLES": 50,
    "locators.PROG_DL1_WINDOW_AH": [22.0, 42.0],
    # WP2 sets, trend and gates
    "locators.RELAXED_ANCHORS": [1, 2, 4, 5, 6, 7],
    "locators.H_ANCHORS": [1, 2, 4, 5, 6, 7],
    "locators.MIN_H_ANCHORS": 3,
    "locators.G_SB_SIGMA_MAX_AH": 0.25,
    "locators.G_RESID_FLOOR_AH": 0.15,
    "locators.G_A3_MIN_SAME_SIGN": 4,
    "locators.G_B3_WIDTH_MAX_AH": 0.40,
    "locators.R8_GRID_AH": 0.25,
    "locators.R8_CHECK_TOL_AH": 0.25,
    # Ah chain
    "ahchain.MAX_DT_S": 600.0,
    "ahchain.GAP_DT_S": 60.0,
    "ahchain.COUNTER_FLAT_AH": 0.0005,
    "ahchain.MIN_POOLED_TT": 2,
    "ahchain.MAD_K": 1.4826,
    "ahchain.SE_WIDEN": 2.0,
    "ahchain.G_NOISE_MAX_AH": 0.30,
    "ahchain.G_T_HALF_WIDTH_AH": 0.25,
    "ahchain.G_E2_MAX_AH": 0.20,
    "ahchain.SWITCH_SETPOINTS": [25, 45],
    "ahchain.N_CELLS": 4,
    "ahchain.DUDT_ASSUMED_V_PER_K": 0.0003,
    "ahchain.S_WINDOWS_AH": [[0.5, 2.0], [0.25, 1.0], [1.0, 3.0]],
}


def protocol():
    en = english_part()
    return {
        "round": 12,
        "protocol_version": 1,
        "written": "2026-10-19",
        "branch": "exp/phase2-r12-eps-level-20261019",
        "base_commit": "6525edf",
        "status": "registered in WP1, committed before any WP2 or WP3 output; no value computed on challenge data",
        "registered_code": REGISTERED_CODE,
        "change_rule": ("WP2 and WP3 import src/locators.py and src/ahchain.py unchanged. Any later change is a new "
                        "registered version: reason in notes/DECISIONS.md, new protocol hash committed, results computed "
                        "before it labelled."),
        "proxy_rule": "No rule, gate or estimate in this protocol uses the Challenge 2 proxy labels P_k or any proxy error.",
        # ------------------------------------------------------------------------------------------------
        "definitions_section2_verbatim": between(en, "**How the submission SUB uses ε.**", "**Facts already established.**").splitlines(),
        "definitions": {
            "SOH": "C/20 capacity (5.1 A discharge to pack 11.2 V after a full charge) / 102 Ah",
            "Q_fc_k": "F^A_k - B_k: package-integrated charge of anchor k (charge start state B_k to the end of the 14.0 V CV at ~5.1 A, F^A_k)",
            "C20_k": "F^CK_k - S_k: checkup top state to the state at the end of its C/20 discharge",
            "eps_k": "C20_k - Q_fc,k = (F^CK_k - F^A_k) + (B_k - S_k)",
            "eps0": "100.41 - Q_fc,0 (45 degC anchor 0)",
            "EPS_EXTRA_true_k": "eps_k - eps_0 = [F^A_0 - F^A_k] (T_top, WP3) + [F^CK_k - F^CK_0] (drift d, out of scope) + [a_0 - a_k] (WP2)",
            "a_k": "S_k - B_k (> 0 if the anchor starts deeper than its C/20 ended)",
            "H_SB": "a_k = 0: the anchor starts from the state its checkup's C/20 discharge ended in, changed only by rest",
            "EPS_EXTRA_hat": "T_top + a_0 (under H_SB, equal ageing, relaxed 25 degC anchors)",
            "a_k_rel": "anchor-specific bottom anomaly: Q_bot,k minus the trend of the relaxed anchors at t_k",
            "coulombic_efficiency": "neglected (round 11: T_CE -0.0008 Ah/Ah in LIC)",
            "anchors": "k = 0 segment 1 (45 degC); k = 1..7 segments 2, 4, 6, 8, 10, 12, 14 (25 degC); type-A events of wp0/events.csv",
        },
        # ------------------------------------------------------------------------------------------------
        "data_conventions": {
            "integration": ("package _integrated_ah per segment: backward rectangle i_k * dt_k with dt_k = t_k - t_(k-1); "
                            "dt > 600 s or dt <= 0 contributes 0; the first sample of a segment has dt = 0"),
            "events": "wp0/events.csv (src/wp0_events.py, DECISIONS D7): CV end = last sample of a charge run (I > 0.5 A) "
                      "with max pack >= 13.95 V and 0 < I_end < 6 A; type A = package _first_full_charge conditions",
            "anchor_time_t_k": "days from the CK0 date 2025-01-14 00:00 to the anchor's charge start",
            "ck0_curve": "CK0_reference_discharge.csv.gz; Q axis = its discharged_Ah column; per-cell voltages",
        },
        # ------------------------------------------------------------------------------------------------
        "WP2": {
            "B1_start_audit": {
                "rest": "contiguous samples with |I| <= 0.5 A immediately before the anchor charge",
                "slope": "OLS slope of pack voltage over the last 30 min of rest (whole rest if shorter), mV/h",
                "relaxed_if": "slope <= 6 mV/h",
                "temperature_trend": "OLS slope of temp_mean_C over the rest, K/h; start value = last rest sample",
                "spread": "max - min cell voltage at the last rest sample",
                "window": "checkup window from wp0/checkup_windows.csv; k = 0: exact time since the C/20 end",
            },
            "B2_charge_side": {
                "samples": "anchor charge from its first sample to its CV end; CC samples I > 20 A; q = Ah from the charge "
                           "start with the package base ah[start - 1]; duplicate q removed (first occurrence after a stable sort)",
                "dvdq_variants": {
                    "CL1": "maximum of +dV/dQ, 0.05 Ah grid, centred moving average 2 Ah (41 points), central differences, "
                           "parabolic interpolation through the maximum and its two neighbours, open window (50, 80) Ah",
                    "CL2": "as CL1 with 1 Ah smoothing (21 points)",
                    "CL3": "as CL1 with 3 Ah smoothing (61 points)",
                    "grid": "grid points are multiples of 0.05 Ah from floor((lo - pad)/dx) dx to ceil((hi + pad)/dx) dx, "
                            "pad = (points // 2 + 3) * 0.05 Ah; the data must cover the grid, else NaN",
                    "nan_rules": "NaN if the maximum is on the first or last grid point inside the window, or the three "
                                 "points are not a strict maximum (second difference >= 0)",
                },
                "midpoint_variants": {
                    "CL4": "threshold = mean of the medians of the raw cell-voltage samples on [s - 15, s - 5] Ah and "
                           "[s + 5, s + 15] Ah (>= 5 samples each), s = CL1; location = first upward crossing among samples "
                           "with q in [s - 5, s + 5], linear interpolation between the crossing sample and its predecessor",
                    "CL5": "as CL4 with plateaus [s - 20, s - 10] and [s + 10, s + 20] Ah, crossing searched in [s - 10, s + 10]",
                },
                "combination": "cell value = median of its finite variants (>= 4 needed); anchor value = median of the finite "
                               "cell values (>= 3 needed); per-locator anchor value = median over the cells of that locator "
                               "(>= 3 finite cells)",
                "Q_bot_k": "combined anchor value (Ah from the charge start to the step); Q_top,k = Q_fc,k - Q_bot,k",
                "R8_check": "CL1 per cell rounded to the 0.25 Ah grid, mean over the 4 cells, compared with round 8 "
                            "table_anchors.bottom_to_step; passes within 0.25 Ah (diagnostic, not a gate)",
                "trend": "Theil-Sen line (median pairwise slope, intercept median(y - b x)) of Q_bot vs t_k over the relaxed "
                         "anchors {1, 2, 4, 5, 6, 7}",
                "sigma_LOO": "1.4826 * MAD of the leave-one-out residuals (each anchor vs the Theil-Sen line of the other five)",
                "a3_rel": "Q_bot,3 - trend(t_3) on the combined value; per locator: the locator's anchor value minus that "
                          "locator's own Theil-Sen trend over the relaxed anchors",
                "a0_rel": "Q_bot,0 - trend(t_0) (extrapolated, confounded by 45 degC; diagnostic only)",
                "descriptive": "in-sample residuals of the relaxed anchors vs start pack voltage (rest end) and bottom spread: "
                               "table and Spearman rho; no gate",
            },
            "B3_ck0_split": {
                "dvdq_variants": "DL1-DL3: as CL1-CL3 with -dV/dQ on the CK0 curve (q = discharged_Ah = D_top axis), "
                                 "window mirrored from the end of the discharge: open (100.41 - 80, 100.41 - 50) = (20.41, 50.41) Ah",
                "midpoint_variants": "DL4-DL5: as CL4-CL5 mirrored: plateau before the step [s - b, s - a], after it "
                                     "[s + a, s + b], first downward crossing in [s - a, s + a], s = DL1; (a, b) = (5, 15), (10, 20)",
                "combination": "as B2 (cell >= 4 variants, pack >= 3 cells)",
                "D_top_D_bot": "D_top,c from the DL family; D_bot,c = 100.41 - D_top,c",
                "C_bot_C_top": "C_bot,c = anchor 0's Q_bot per cell (CL family); C_top,c = Q_fc,0 - C_bot,c",
                "medians": "D_top, D_bot, C_top, C_bot = medians over the cells (the median commutes with x -> const - x, "
                           "so eps0 = (D_top - C_top) + (D_bot - C_bot) holds exactly)",
                "h": {
                    "anchors": [1, 2, 4, 5, 6, 7],
                    "h1_k": "D1_k - C_top,k; D1_k = step depth of the deep program that starts at anchor k's own CV end",
                    "h2_k": "D2_k - C_top,k - (F^T2 - F^A_k); D2_k = step depth of the program that starts at the next CV end "
                            "(T2) in the same segment; F^T2 - F^A_k = N - lambda_s thr of that AT pair from src/ahchain.py "
                            "(Term3_k); AT pairs that are not admissible (recording gap) give no h2_k",
                    "step_values": "A3 = package _robust_step via _step_depths (unchanged); DL1 = locators.program_dl1 "
                                   "(band samples -12.5 < I < -8 A, depth below the CV end, window (22, 42) Ah, 2 Ah smoothing, "
                                   "pack = median of >= 3 finite cells)",
                    "C_top_k": "Q_fc,k - Q_bot,k (combined B2 value)",
                    "medians": "median over the finite k (>= 3 needed, else NaN) of h1(A3), h1(DL1), h2(A3), h2(DL1)",
                    "interval": "[h_lo, h_hi] = min and max of the finite medians; point = median of the finite medians",
                },
                "a0": "-(D_bot - C_bot) - h_point; interval [-max(V) - h_hi, -min(V) - h_lo], V = {combined D_bot - C_bot} "
                      "united with the paired variants (DLi, CLi), i = 1..5 (the 5 x 5 range is reported descriptively)",
                "top_split": "F^CK_0 - F^A_0 = (D_top - C_top) - h_point; interval from the same paired variants and [h_lo, h_hi]",
                "caveats": "CK0 discharges at 5.1 A while the programs' step band is ~10 A; checkup temperature unknown; "
                           "anchor 0 charged at 45 degC",
            },
        },
        # ------------------------------------------------------------------------------------------------
        "WP3": {
            "E1_pairs": {
                "pairs": "consecutive CV ends i -> j (wp0/events.csv in time order) with no checkup date in (t_i, t_j]",
                "N": "sum of i_k dt_k / 3600 over the samples in (t_i, t_j] (package convention); across a chamber switch "
                     "the two segments' sums are added and the boundary contributes 0",
                "thr": "same sum restricted to i_k < 0, sign flipped (includes the 20 A pulse)",
                "types": {"AT": "anchor -> next top-up in the same segment", "TT": "top-up -> top-up in the same segment",
                          "X": "last 25 degC CV end -> first 45 degC CV end of the next segment (consecutive segment files, "
                               "set points 25 -> 45)"},
                "exclusion": "any sample spacing > 60 s inside (t_i, t_j] excludes the pair; the chamber-switch boundary is "
                             "exempt only if both counters change by < 0.0005 Ah across it; every exclusion is recorded",
            },
            "E1_loss_rule": {
                "lambda_s": "median of N/thr over the admissible TT pairs of segment s",
                "fallback": "no TT pair in s -> pooled median of the same set point, if that set point has >= 2 TT pairs "
                            "overall (counted on the full set); otherwise the other set point's pooled median (recorded)",
                "loo": "for a TT pair's own residual the pair is left out of every median above (the overall count is not)",
                "residual": "r = N - lambda thr",
                "sigma_TT": "sigma_TT,25 and sigma_TT,45 = 1.4826 MAD of the TT residuals per set point",
            },
            "E1_terms": {
                "Term1": "-(N(A_0 -> T) - lambda_seg1 thr) = F^A_0 - F^T_45 (one value)",
                "Term3_k": "N(A_k -> T) - lambda_s thr = F^T_25 - F^A_k for the admissible AT pairs of k in 1..7; main = all of "
                           "them; sensitivity = without k = 3",
                "Term2_j": "N_X - lambda_bar thr_X = F^T_45 - F^T_25 for the admissible X pairs; lambda_bar = mean of the 25 degC "
                           "segment's lambda and the 45 degC segment's lambda; sensitivities: each side's lambda alone",
                "T_top": "Term1 + median_j Term2_j + median_k Term3_k",
                "descriptive_only": "Term1 and Term3_k with the pooled same-set-point lambda (not part of the interval); "
                                    "Term2_j and Term3_k vs month; Term2_j vs idle hours",
            },
            "E1_interval": {
                "per_term": "[min, max] of the point over its lambda sensitivities (Term2: lambda_bar, lambda_25, lambda_45; "
                            "Term1 and Term3: the rule's lambda only), widened by +-2 SE",
                "SE": "1.4826 MAD / sqrt(n) of the term's event values (main lambda); Term1: SE = sigma_TT,45",
                "T_top_interval": "sum of the lower ends, sum of the upper ends",
                "order": "G_noise -> term intervals -> G_E2 widening of Term2 -> T_top interval -> G_T on the final interval",
            },
            "E2_step_jump": {
                "J_j": "depth(program of the first 45 degC CV end after switch j) - depth(program of the last 25 degC CV end "
                       "before it) - r_45 dt; NaN if either program is the first program after an anchor or is not a deep "
                       "program",
                "r_45": "Theil-Sen rate (Ah/day) of the step depths of all deep programs of that 45 degC segment vs CV-end time",
                "dt": "days between the two programs' CV ends",
                "values": "A3 (package _robust_step) and DL1 (locators.program_dl1); median_j J_dvdq uses DL1",
            },
            "E3_physics_diagnostic": {
                "dV_j": "pack voltage 30 min after the CV end (last sample before the pulse, wp0/events.csv pack_V_prepulse) "
                        "of the first 45 degC top-up minus that of the last 25 degC top-up",
                "dT_j": "temp_mean_C at the same two samples (difference)",
                "s": "OLS slope of CK0 pack voltage vs charge content (= -discharged_Ah) on discharged Ah [0.5, 2.0] "
                     "(V per Ah, > 0); sensitivities [0.25, 1.0] and [1.0, 3.0]",
                "dU_dT": "assumption: +-0.3 mV/K per cell (no cited LFP/graphite high-SOC value available offline; the "
                         "repository review quotes electrode-level magnitudes graphite ~0.2, LFP ~0.1 mV/K, Spingler et al. "
                         "2020, JES 167:040526)",
                "Term2_E3": "(dV - 4 dU/dT dT) / s; point at dU/dT = 0 and the main window; interval = min/max over "
                            "dU/dT in {-0.3, +0.3} mV/K and the three windows",
                "top_cell": "cell with the highest voltage at the CV end and 30 min later, per temperature",
                "gating": "none",
            },
        },
        # ------------------------------------------------------------------------------------------------
        "section4_gates_and_decision_rules_verbatim": section4_bullets(en),
        "operationalisation": {
            "G_SB_residuals": "leave-one-out residuals (the stricter reading)",
            "G_a3_per_locator": "per-locator a_3^rel against the locator's own trend; a NaN locator does not count as same sign",
            "G_B3_width": "a0_hi - a0_lo; NaN anywhere -> 'no finite interval' -> budget L3",
            "G_E2_not_evaluable": "if median_j J_dvdq is NaN, G_E2 is reported as not evaluable and nothing is widened",
            "budget_width": "EPS_EXTRA_hat interval width = hi - lo; T_top unmeasured or no finite a_0 interval -> L3",
            "decision_point_rounding": "SUB_L uses the point estimate rounded to the nearest 0.05 Ah",
            "decisions_reference": "notes/DECISIONS.md D10-D27",
        },
        "synthetic_tests": {
            "file": "src/test_registered.py",
            "step_tolerance_Ah": 0.02,
            "ah_offset_tolerance_Ah": 0.005,
            "curves": "clean symmetric tanh steps (w 1.0-2.5 Ah) on a linear slope; exact synthetic Ah chains",
            "resolution_diagnostic": "wp1/synthetic_resolution.json (1 mV quantisation, reported, not a pass criterion)",
        },
        "constants": CONSTANTS,
    }


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "protocol.json")
    json.dump(protocol(), open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    if "--hash" in sys.argv:
        lines = [f"{sha(p)}  wp1/protocol.json"] + [f"{sha(os.path.join(ST, f))}  {f}" for f in REGISTERED_CODE]
        open(os.path.join(OUT, "protocol.sha256"), "w").write("\n".join(lines) + "\n")
        print("\n".join(lines))
    print("wrote", p)
