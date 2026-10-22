# Materials index

Copy only the selected materials into this folder. One row per file.
Evidence: p primary · a academic · m media or company claim · i inference · v to verify · n internal.

| File | Origin (full path) | Kind | Used on slides | Evidence | Note |
|---|---|---|---|---|---|
| REPORT.md | TechArena_Challenge2_Team_Package/REPORT.md | report | 2, 5–13 | n | Main source: submitted model (V2 + temperature-weighted √t gap + robust step A3), proxy errors at ε0+0.4 |
| V1_FINAL_REPORT.md | research/phase2_anchor_step_20261013/FINAL_REPORT.md | report | 6, 7, 9, 10 | n | Anchor table Q_fc, step detection 41/41, M0–M5 comparison, gates G1–G5 |
| V2_FINAL_REPORT.md | research/phase2_v2_phase_matched_20261013/FINAL_REPORT.md | report | 8, 9, 10 | n | Phase matching, β per checkup, six detection variants, gates H1–H6 |
| V3_FINAL_REPORT.md | research/phase2_v3_20261015/FINAL_REPORT.md | report | 8, 9, 12 | n | √t gap branch, CK2 sensitivity −0.35…+0.29 pp; V3 as registered not used |
| DATA_MANIFEST.md | external_data/DATA_MANIFEST.md | report | 11, 12 | n / p | Three open LFP datasets (CC BY 4.0), ε drift −0.03 Ah per Ah of fade |
| submission_instructions_2026.md | TechArena_Challenge2_Team_Package/submission_instructions_2026.md | rules | 5 | p | Task, data, scoring (baseline = 1.0), final presentation rules (≤ 15 min, C1 + C2, .pptx) |
| evaluation_points.csv | TechArena_Challenge2_Team_Package/data/checkups/evaluation_points.csv | data | 5, 6, 8 | p | Checkup dates CK0–CK7 |
| segments.csv | made from TechArena_Challenge2_Team_Package/data/operation/*.csv.gz (first and last timestamp) | data | 5 | p | Segment periods and set-points; segment 3 period from the rules |
| A1_full_charges.csv | research/phase2_anchor_step_20261013/outputs/A1_full_charges.csv | data | 6 | n | Post-checkup full charges Q_fc |
| A2_step_programs_all_variants.csv | research/phase2_anchor_step_20261013/outputs/A2_step_programs_all_variants.csv | data | 7, 8 | n | 41 step events × 6 detection variants × 4 cells |
| overview.png | research/phase2_anchor_step_20261013/figures/overview.png | figure | — | n | Reference for the slide 7 chart (redrawn as SVG) |

Conflicts and own numbers:
- Monthly fade 0.45–1.33 Ah (slide 13) is computed from consecutive Q_fc values CK1→CK7; not stated in the reports. Tag i.
- Decision "calibrate ε with leaderboard feedback" (slide 13) follows the direction of rounds r12/r15; confirmed by the user at gate 2. Tag i.
- Slide 7 plots the main detection method (cell mean), as in REPORT.md and overview.png; slide 8 plots the robust value (median of 6 variants, then of 4 cells) that the submitted model uses.
