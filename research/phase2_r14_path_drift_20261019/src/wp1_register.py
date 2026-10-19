"""WP1: write wp1/protocol.json (with SHA256 of the registered code) and wp1/protocol.sha256. Reads no challenge data."""
import hashlib, json, os
import data14 as D

ST = D.ST
CODE = ["src/data14.py", "src/ahchain.py", "src/signals.py", "src/stats14.py", "src/decide.py", "src/test_synthetic.py",
        "sources/r11/drift.py", "../../TechArena_Challenge2_Team_Package/my_model/model_template.py"]

VERBATIM_RULES = [
    "Let E = d_path × 8.2 Ah, the effect at CK7.",
    "Noise gate: σ_TT,25 ≤ 0.30 Ah. Otherwise the outcome is \"not identifiable\": report and exit after WP3's write-up.",
    "Identifiability: the LOO range of E is ≤ 0.30 Ah wide. Otherwise the outcome is O3 \"not identifiable\".",
    "O1 \"path drift small\": the LOO range of E lies within [−0.10, +0.10] Ah, and P1b's median E lies within ±0.15 Ah.",
    "O2 \"path drift material\": the LOO range of E excludes 0, |median E| > 0.10 Ah, BIC prefers (b) by ≥ 2, and P1b has "
    "the same sign. Candidate \"SUB + d_path\" is leaderboard-only.",
    "O3 \"inconclusive\": any other case.",
    "Combination with round 13 (only if R13_RESULT.json is available): d_top = d_tail + d_path, with medians added and "
    "ranges added endpoint-wise. Report it; it decides nothing in this round. It is passed to round 15.",
    "No rule uses P_k or proxy errors.",
]


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    proto = {
        "round": 14,
        "title": "Path drift on our own pack: does the from-empty vs top-up top difference change with age?",
        "registered": "2026-10-19, WP1, before any WP2 output",
        "base_commit": "6525edfcc1d60a5ca911e430401c8c79b4c58d61",
        "branch": "exp/phase2-r14-path-drift-20261019",
        "data": {"operation": "TechArena_Challenge2_Team_Package/data/operation, full (uncut) via framework.data.load_dataset",
                 "ck0_reference": "TechArena_Challenge2_Team_Package/data/checkups/CK0_reference_discharge.csv.gz",
                 "never_used": "Challenge 2 proxy labels P_k and any error against them"},
        "optional_sources_at_registration": {
            "checked": "2026-10-19 22:26 after git fetch origin",
            "r12_src_ahchain_py": "not available on origin (tip bd7ab9d); the rule is implemented in src/ahchain.py",
            "r12_wp3_pairs_csv": "not available; re-checked at WP2 for the N cross-check (|dN| <= 0.001 Ah on shared pairs)",
            "r13_wp3_R13_RESULT_json": "not available (tip 94f7e45); re-checked at WP3 for the d_top combination"},
        "events": {
            "cv_end": "package rule in _step_depths: last sample of each run with pack >= 13.95 V and 0 < I < 6 A",
            "anchor": "package _first_full_charge of the segment (from-empty CCCV); must be the first CV end of its segment; "
                      "anchors k = 0..7 in time order (k = 0: segment 1, 45 C)",
            "T1_T2": "the next one / two CV ends in the same segment",
            "Q_fc": "package q of the anchor (_integrated_ah)",
            "indexing": "row index within the segment (timestamps are not unique)"},
        "ah_chain": {
            "code": "src/ahchain.py (own implementation of the round 12 rule)",
            "N": "integral of current_A over (t_i, t_j] between two CV ends of the same segment, package convention "
                 "_integrated_ah (dt > 600 s or dt <= 0 get zero weight)",
            "thr": "discharged Ah over (t_i, t_j]: integral of max(-current_A, 0), same weights",
            "pairs": "AT1 = anchor -> T1, AT2 = anchor -> T2, TT = consecutive top-ups; same segment only",
            "gap_rule": "a pair with any dt > 60 s in (t_i, t_j] is excluded (main estimates)",
            "lambda_s": "median of N/thr over the gap-free TT pairs of segment s; none -> pooled median of the segment's set "
                        "point; that set point with < 2 gap-free TT pairs -> the other set point's pooled median (recorded "
                        "as lambda_source)",
            "sigma_TT": "1.4826 * MAD of r = N - lambda(-p) * thr over the gap-free TT pairs of a set point, lambda(-p) = the "
                        "lambda rule for p's segment applied without p",
            "sigma_TT_readings": {
                "reduced": "the '< 2 TT pairs' test counts the pairs left after removing p (literal)",
                "full": "the test counts the full TT set; p is removed only from the median",
                "gate_value": "sigma_TT,25 for the noise gate = max(reduced, full), the conservative choice "
                              "(both readings keep the rule; they differ at 25 C, which has only 2 TT pairs)"},
            "synthetic_test": "src/test_synthetic.py; a planted A->T1 Ah offset must be recovered within 0.005 Ah"},
        "signals": {
            "P1": "primary: Term3_k = N(A_k -> T1) - lambda_s * thr(A_k -> T1), k = 1..7 (25 C), gap-free AT1 pairs only",
            "P1b": "robustness: Term3'_k = N(A_k -> T2) - lambda_s * thr(A_k -> T2), gap-free AT2 pairs only",
            "P1_45C_anchor0": "Term3_0 with lambda of segment 1; reported separately, not in any trend",
            "S_gap": "descriptive only, decides nothing: Term3_k for every AT1 pair including those with recording gaps, with "
                     "the package integration (gap intervals > 600 s carry zero weight; the counters show no flow across "
                     "the three gaps, WP0 F9). Same statistics as P1",
            "P2": "consistency: dV_k = V30(T1) - V30(A_k) in mV, pack and per cell; P2_Ah = -dV / s_top (sign of Term3); "
                  "s_top = OLS dV/dQ of the CK0 C/20 curve over discharged Ah in [0.5, 2.0] (pack: voltage_V; cell: that "
                  "cell's curve). V30 = last rest sample at or before t_e + 1800 s, within 30 s of it, no gap. Statistics "
                  "on pack P2_Ah; cells and cell mean reported",
            "P3": "descriptive path memory, decides nothing: o_k = D1_k - D2_k with the package A3 robust step value and its "
                  "dV/dQ variant (median over cells; 0.25 Ah grid); absolute shift o_k + Term3_k; anchor minus T1 CV Ah, CV "
                  "duration and end current"},
        "statistics": {
            "code": "src/stats14.py",
            "x": "fade_k = Q_fc,1 - Q_fc,k (package Q_fc)",
            "d": "Theil-Sen slope of the signal against fade_k over the available k in 1..7; at least 5 points, otherwise "
                 "'not estimable'. 'median E' = d * 8.2 Ah",
            "loo": "leave-one-anchor-out: the n Theil-Sen slopes on n - 1 points; LOO range = [min, max] of these slopes; "
                   "E range = 8.2 * that",
            "days": "Theil-Sen slope against days since CK0 (anchor CV end - 2025-01-14), with its LOO range",
            "bic": "(a) constant, (b) linear in fade; OLS; BIC = n ln(RSS/n) + k ln(n), k = 2 for (a), 3 for (b); "
                   "dBIC = BIC_a - BIC_b; 'BIC prefers (b) by >= 2' means dBIC >= 2",
            "outliers": "flag |r - median(r)| > 3 * MAD(r), raw MAD, r = Theil-Sen residuals (no flag if MAD = 0); flagged "
                        "points stay in the main estimate; sensitivity without them",
            "anchor_3": "stays in the main estimate where its pair is usable; sensitivity without it. For P1 its A->T1 pair "
                        "contains recording gaps (WP0), so the gap rule removes it from P1 and the sensitivity equals the "
                        "main estimate; for P2 (voltages, no Ah chain) it is in",
            "sensitivity_min_points": 3,
            "applied_to": ["P1", "P1b", "P2 (pack Ah)", "S_gap (descriptive)"]},
        "decision_rules_verbatim": VERBATIM_RULES,
        "decision_rules_operational": {
            "code": "src/decide.py",
            "order": "noise gate -> identifiability -> O1 -> O2 -> O3",
            "p1_not_estimable": "O3 'not identifiable' (identifiability cannot be established)",
            "p1b_not_estimable": "a condition that needs P1b (O1: |P1b median E| <= 0.15 Ah; O2: same sign) is not met",
            "loo_excludes_0": "all LOO E strictly > 0 or all strictly < 0",
            "same_sign": "sign(P1b median E) = sign(median E), median E != 0"},
        "known_from_wp0_structure": {
            "p1_set": "gap-free AT1 pairs exist for anchors 1, 2, 4, 5, 6 (anchors 3, 7 have recording gaps between A and "
                      "T1): exactly 5 points; each LOO fit has 4",
            "p1b_set": "a second top-up in the same segment exists only for anchors 5 and 6: 2 points < 5, so P1b is not "
                       "estimable and neither O1 nor O2 can be reached. Attainable outcomes: 'not identifiable', "
                       "'O3 not identifiable', 'O3 inconclusive'",
            "p1b_identity": "segments 10 and 12 each have a single TT pair (T1 -> T2), so lambda_s * thr(T1 -> T2) = N(T1 -> T2) "
                            "and Term3'_k = Term3_k exactly for k = 5, 6: P1b carries no independent information here",
            "tt_25C": "2 gap-free TT pairs at 25 C (segments 10, 12); anchor segments 2, 4, 6, 8, 14 use the pooled 25 C lambda"},
        "agreement_reported": {
            "P2_vs_P1": "sign of the median E, overlap of the LOO E ranges, difference of the median E",
            "P1b_vs_P1": "estimability; per-anchor Term3' - Term3 for anchors with T2"},
        "wp2_crosscheck_r12": "if round 12 wp3/pairs.csv is on origin at WP2: shared pairs matched by segment and CV-end times; "
                              "N must agree within 0.001 Ah; mismatches recorded, never resolved by editing either side",
        "combination_r13": "if R13_RESULT.json is on origin at WP3: read d_tail median and range; d_top = d_tail + d_path "
                           "(medians added, ranges endpoint-wise; d_path range = its LOO range). Reported; decides nothing",
        "soh_variants": "wp3/SOH_variants.csv, leaderboard-only, never scored against proxies: SUB (wp0/SUB_SOH.csv) and "
                        "SUB + d with d = d_path median, LOO low, LOO high (and d_top if available), built with the copied "
                        "sources/r11/drift.py add_drift(soh, d): Q' = Q + d * max(0, 100.41 - Q). If d_path is not estimable "
                        "the rows are not built and this is recorded",
        "deviation_policy": "WP2/WP3 driver scripts only call the registered functions and write files/figures. Any change "
                            "to a registered file after this commit is a deviation, recorded in notes/DECISIONS.md with the "
                            "reason and the diff, and reported in the WP report",
    }
    proto["registered_code_sha256"] = {c: sha(os.path.normpath(os.path.join(ST, c))) for c in CODE}
    path = os.path.join(ST, "wp1", "protocol.json")
    with open(path, "w") as f:
        json.dump(proto, f, indent=1, ensure_ascii=False)
        f.write("\n")
    h = sha(path)
    open(os.path.join(ST, "wp1", "protocol.sha256"), "w").write(f"{h}  protocol.json\n")
    print(h)


if __name__ == "__main__":
    main()
