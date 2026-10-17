"""Writes wp5/protocol.json and wp5/protocol.sha256 (registration before any residual slice is computed).
Tercile edges are computed here from non-residual columns only."""
import hashlib
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)

ev = pd.read_csv(os.path.join(STUDY, "outputs", "table_events.csv"),
                 usecols=["unit", "setpoint", "segment", "dT_at45", "sharp_height_mV_per_Ah"])
pk = ev[ev.unit == "pack_mean"]
seg_n = pk.groupby("segment").size()
rseg_segments = sorted(int(s) for s in seg_n[seg_n >= 4].index)   # R_seg needs >= 3 other events in the segment
dT_edges = {str(sp): [round(float(x), 4) for x in np.quantile(pk[pk.setpoint == sp]["dT_at45"], [1 / 3, 2 / 3])]
            for sp in (25, 45)}
sh_pack = [round(float(x), 4) for x in np.quantile(pk[pk.segment.isin(rseg_segments)]["sharp_height_mV_per_Ah"], [1 / 3, 2 / 3])]
cl = ev[(ev.unit != "pack_mean") & ev.segment.isin(rseg_segments)]
sh_cell = [round(float(x), 4) for x in np.quantile(cl["sharp_height_mV_per_Ah"], [1 / 3, 2 / 3])]

P = {
    "registered": "2026-10-17, before any residual of table_cases/table_events/table_cycles is grouped, plotted or ranked by a slice variable",
    "exposure": "D2.2: pack-level R_anc/R_seg per event and the per-unit summary of R_cell were printed during WP2 QA; WP1 printed the per-branch summary of inc_resid (required by WP1). H4-event and H6(a) are labelled 'residual seen before registration'.",
    "seed": 20261017, "n_boot": 2000, "n_perm": 5000, "exact_perm_max_n": 9, "ci_level": 0.90,
    "units": "residual = predicted - reference; Ah, and pp = 100*Ah/102",
    "residuals": {
        "inc_resid": "table_cases.inc_resid_Ah (increment_pred - (Q_fc,k - Q_fc,anchor used)); case set = model SUB, delta 0.4 (inc_resid is delta-free), all 9 scenarios (47 cases); real-only reported separately",
        "R_seg": "table_events.R_seg (WP2 definition: depth_main minus leave-one-out Theil-Sen line in time of the other events of the same segment and unit; NaN if < 3 others)",
        "R_anc": "table_events.R_anc (WP2: depth_main - [a_sp,unit + 1*Q_interp], a = mean of depth - Q_interp over other months, same set point and unit)",
        "R_anc_b": "registered secondary: depth_main - [a_sp,unit + b_unit*Q_interp], (a_25, a_45, b) by OLS on events of the same unit from the other months (leave-month-out), so the sub-unity step sensitivity (b = 0.745 in WP2) is not left in the residual",
        "R_cell": "table_events.R_cell (unit depth_main minus the median of the four cell depths of the same event)",
        "R_cyc_slot": "table_cycles.R_cyc_slot_<col> (D4.1); H10 col = top_Ah_rel_last_cv_end, H10b col = V_bottom_pack",
    },
    "item_sets": {
        "cases": "table_cases, model SUB, delta 0.4, all scenarios; block = k (checkup index); stratum = branch",
        "events_pack": "table_events unit == pack_mean; block = month (anchor index the event follows); stratum = set point",
        "events_cell": "table_events unit in cell1_V..cell4_V; block = month; stratum = set point",
        "anchors": "table_anchors; n = 8 (anchor 0 is 45 C); exact permutations",
        "cycles": "table_cycles; block = month; stratum = set point",
    },
    "bins": {
        "fade_pct": {"edges": [3.0, 6.0], "labels": ["0-3", "3-6", ">6"],
                     "def": "cases: 100*cum_fade_at_anchor_Ah/102; events: 100*(100.41 - Q_interp - eps0)/102"},
        "days_since_switch": {"edges": [2.0, 5.0], "labels": ["0-2", "2-5", ">5"]},
        "dT_at45": {"edges_by_setpoint": dT_edges, "labels": ["low", "mid", "high"],
                    "def": "terciles of T_at45 - set point over the 41 pack events, per set point (no residuals)"},
        "sharpness_pack": {"edges": sh_pack, "labels": ["low", "mid", "high"],
                           "def": "terciles of sharp_height_mV_per_Ah over pack events of segments with defined R_seg " + str(rseg_segments)},
        "sharpness_cell": {"edges": sh_cell, "labels": ["low", "mid", "high"], "def": "same over the cell rows"},
        "gap_days": {"edges": [5.0, 10.0], "labels": ["0-5", "5-10", ">10"]},
        "days_anchor_to_ck": {"edges": [25.0, 30.0], "labels": ["0-25", "25-30", ">30"]},
        "month_group": {"edges": [3, 6], "labels": ["m0-2", "m3-5", "m6-7"]},
        "hours_since_segment_start": {"edges": [48.0], "labels": ["0-48h", ">48h"]},
        "bin_rule": "bin i holds edges[i-1] <= x < edges[i]",
    },
    "statistics": {
        "effect_binary": "mean(residual | group) - mean(residual | rest)",
        "effect_binned": "mean(residual | highest bin) - mean(residual | lowest bin), unless the hypothesis names other bins",
        "slope": "OLS slope of residual on the continuous slice variable (descriptive; H4 compares it with -0.031 Ah/Ah)",
        "ci": "block bootstrap: resample blocks with replacement (n_boot, seed), recompute the effect, 5th-95th percentile; resamples where the effect is undefined are dropped and counted",
        "sign_share": "if the slice variable varies within blocks: share of blocks (with both groups / extreme bins present, else the within-block OLS slope) whose within-block effect has the expected sign. If it is constant within blocks: a block agrees when sign(block mean residual - overall mean) == expected sign * sign(block x - median block x); blocks at the median are skipped",
        "permutation": "two-sided on |effect|: the slice variable is permuted across items within strata (set point for events/cycles, branch for cases; anchors: no strata), i.e. across month blocks; exact enumeration when n <= 9, else n_perm random permutations (seed)",
        "verdict": "systematic: |effect| >= threshold AND the 90% CI excludes 0 AND sign_share >= 0.70 (expected sign); 'systematic (opposite sign)' if all three hold with the opposite sign; not systematic: |effect| < threshold AND CI contains 0; inconclusive: otherwise. Threshold 0.10 Ah unless stated. The permutation p is reported, not used in the verdict.",
    },
    "hypotheses": {
        "H1": {"what": "cases with uses_first_post_anchor_program vs the other cases: inc_resid shift",
               "items": "cases", "expected_sign": -1, "expected_size_Ah": [-0.8, -0.4],
               "note": "competing known effect: the fallback uses beta = 1 while depth moves ~0.75 Ah per Ah of Q_fc (WP2 b), which biases fallback inc_resid positive",
               "diagnostic_only": ["(a) increment with after[0] replaced by after[1] (second program after the anchor)",
                                   "(b) after[0] minus the round 6/7 3c adj_offset of its anchor (main variant)",
                                   "(c) the original increment divided by b = 0.745 (WP2 free-slope fit)"],
               "diag_rule": "report inc_resid of each counterfactual per case; never scored as proxy MAE"},
        "H2": {"what": "R_seg and R_anc (also R_anc_b) vs days_since_switch, per set point",
               "items": "events_pack", "effect": "mean(0-2 d) - mean(>5 d)", "expected_sign": 1,
               "primary": "45 C events of direct_switch segments; 25 C reported but confounded with the first-program offset (all 25 C events at 0-2 d are first programs) and R_seg is undefined at 25 C"},
        "H3": {"what": "R_anc (also R_anc_b) vs dT_at45 = T_at45 - set point", "items": "events_pack",
               "effect": "mean(high tercile) - mean(low tercile), terciles per set point, pooled", "expected_sign": 1},
        "H4": {"what": "signed inc_resid (cases) and R_anc (events) vs cumulative fade", "items": ["cases", "events_pack"],
               "effect": "mean(>6 %) - mean(0-3 %); slope in Ah per Ah of fade with block-bootstrap CI",
               "expected_sign": -1, "eps_drift_slope": -0.031,
               "label_rule": "if the slope CI contains -0.031: 'indistinguishable from eps drift, invisible to proxies'",
               "note": "event part: R_anc with b = 1 is expected to trend at about +(1 - b) = +0.255 Ah/Ah from WP2 (seen); also reported on R_anc_b"},
        "H5": {"what": "|R_seg| larger in the lowest sharpness tercile; worst-20 % events enriched in it",
               "items": ["events_pack", "events_cell"], "effect": "mean|R_seg| (low) - mean|R_seg| (mid+high)",
               "expected_sign": 1, "enrichment": "Fisher exact (greater) of lowest-tercile share in the worst 20 % by |R_seg| vs the rest"},
        "H6": {"what": "(a) persistent per-cell sign of R_cell; (b) spread of the four cell depths grows with time; (c) weakest cell by voltage at maximum depth changes or not",
               "items": "events_cell", "a": "per cell: effect = mean R_cell, expected sign = sign of the cell's mean, criteria as verdict (sign_share = share of months whose block mean has that sign)",
               "b": "spread = max - min of the 4 cell depth_main per event; effect = mean(m6-7) - mean(m0-2); expected +1",
               "c": "weakest_cell_maxdepth per month: descriptive table; 'changes' if the modal weakest cell differs between m0-2 and m6-7"},
        "H7": {"what": "pulse resistance trends upward; anchor CV Ah and Q_fc - Q_fc(6 A cut) grow with it", "items": "anchors",
               "tests": ["Spearman(R_mean_mOhm, anchor) over 25 C anchors 1..7, exact; expected +",
                         "Spearman(cv_Ah, R_mean_mOhm) and Spearman(-dQ_cut6A, R_mean_mOhm) over anchors 1..7, exact; expected +",
                         "events: Theil-Sen slope of R_mean_mOhm on time per set point, block-bootstrap CI (descriptive)"],
               "verdict": "systematic if all three Spearman rho have the expected sign with exact p <= 0.05 and the cv_Ah change across the R range >= 0.10 Ah; not systematic if the R trend rho has p > 0.2; inconclusive otherwise"},
        "H8": {"what": "|inc_resid| grows with gap_days and with days_anchor_to_ck, by branch", "items": "cases",
               "effect": "mean|inc_resid| (highest bin) - (lowest bin), pooled and within each branch where both bins exist",
               "expected_sign": 1},
        "H9": {"what": "month-to-month dQ_fc before vs after the 6 A cut and its dependence on r_upper", "items": "anchors",
               "def": "scatter = residuals of dQ_fc,j (25 C pairs j = 1..6, i.e. 1->2 .. 6->7) about an OLS line in j; 0->1 reported separately",
               "corrections": {"cut": "use Q_fc_cut6A (fixed)", "start_state": "Q_fc + r_half (fixed coefficient 1: residual charge before the anchor charge)",
                               "start_state_fitted": "Q_fc + g*r_upper with g fitted by OLS on the pair residuals (descriptive, in-sample) and leave-one-out"},
               "metric": "variance ratio var(after)/var(before); Spearman(dQ residual, d r_upper) exact (n = 6)",
               "verdict": "systematic if a fixed correction gives ratio <= 0.5; inconclusive if a fixed one gives 0.5-0.8 or only the fitted one <= 0.5; not systematic otherwise"},
        "H10": {"what": "R_cyc_slot of top-of-charge Ah shows a post-anchor and post-switch pattern", "items": "cycles",
                "effects": ["mean(first program block after the anchor) - mean(other blocks)",
                            "45 C segments: mean(0-48 h since segment start) - mean(>48 h)"],
                "expected_sign": 1, "threshold_Ah": 0.10, "prior": "not systematic by construction (D4.2)"},
        "H10b": {"what": "same on R_cyc_slot of V_bottom_pack", "items": "cycles", "expected_sign": -1,
                 "threshold_V": 0.005, "note": "registered secondary (D4.2); expected sign: a deeper step after anchor/switch means lower loaded voltage"},
    },
    "worst_set": {"rule": "top 20 % by |residual| (ceil(0.2*n)), ties at the cut included",
                  "cases": "|inc_resid|, SUB, delta 0.4, all scenarios", "events": ["|R_anc| pack_mean", "|R_seg| pack_mean"],
                  "enrichment_categories": {"cases": ["scenario", "branch", "anchor_setpoint", "uses_first_post_anchor_program", "fade_bin", "gap_bin"],
                                            "events": ["setpoint", "is_first_after_anchor", "switch_bin", "sharpness_bin", "month_group", "switch_kind"]},
                  "test": "Fisher exact (two-sided) per category level, worst vs rest"},
    "outputs": ["wp5/outputs/slice_summary.csv", "wp5/figures/*", "wp5/dossier/*", "wp5/dossier/enrichment.csv"],
}

if __name__ == "__main__":
    s = json.dumps(P, indent=1, ensure_ascii=False)
    open(os.path.join(HERE, "protocol.json"), "w", encoding="utf-8").write(s + "\n")
    h = hashlib.sha256(open(os.path.join(HERE, "protocol.json"), "rb").read()).hexdigest()
    open(os.path.join(HERE, "protocol.sha256"), "w").write(f"{h}  protocol.json\n")
    print(h)
