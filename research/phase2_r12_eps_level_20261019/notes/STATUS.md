# Status

| WP | State | Result |
|---|---|---|
| WP0 | done | SUB reproduced (CK7 90.765); EPS_EXTRA: CK3–7 0.9804 pp/Ah, CK2 1.4465 (√t branch), CK1 flat; 41 CV events (8 A); 35 facts: 23 confirmed, 6 corrected, 2 cited, 3 deferred, 1 recorded; AT pairs of anchors 3 and 7 contain recording gaps |
| WP1 | done | protocol v1 registered in b3f3e7a (sha256 88194bec… in `wp1/protocol.sha256`); `src/locators.py` + `src/ahchain.py`; synthetic tests 15/15 (step ≤ 0.002 Ah clean, Ah offsets at float precision); 1 mV quantisation limits dV/dQ variants (synthetic, reported) |
| WP2 | done | G_SB failed (anchors 5 −0.52, 7 +0.40 > 0.264; σ_LOO 0.13) → H_SB rejected for 5, 7; G_a3 identified (a3_rel +0.305 Ah, 4/5); a0 +3.37 [1.74, 4.72] not identified (h does not transfer 25→45 °C; exploratory h1_0 gives a0 ≈ −0.3…−0.5) |
| WP3 | done | T_top +1.11 [0.60, 1.62] Ah, G_T not identified (half-width 0.51); G_noise pass (σ 0.125/0.026); G_E2 consistent (J_DL1 0.705 vs Term2 0.616); λ drifts −0.97→−2.82·10⁻³ (exploratory time-matched λ: T_top ≈ 0.68); E3 non-informative |
| WP4 | done | L3 (keep SUB): EPS_EXTRA_hat 4.48 [2.35, 6.34] Ah (point puts CK2 above CK0 → artefact); anchor-3 rule passes → SUB_A3fix leaderboard-only (CK4 −0.36 pp); no P_level probe; order P_stress_early → P_start → P_drift unchanged |
| FINAL | done | FINAL_REPORT.md + README.md; 5/5 hashes and 15/15 synthetic tests pass; pushed 2026-10-20 after the user authorised it (D45) |

- Done: WP0.1–WP0.5 (worktree, notes, sources, SUB + sensitivity, events, FACTS, REPORT)
- Done: WP1.1–WP1.4 (protocol.json + sha256, registered modules, synthetic tests, REPORT with outcome table)
- Done: WP2 B1 `wp2/start_audit.csv`: anchors 1, 2, 4–7 relaxed (≤ 5.5 mV/h); anchor 0 (+84 mV/h, cooling −0.89 K/h) and anchor 3 (+53 mV/h) not
- Done: WP2 B2 (`bottom_locators.csv`, `b2_results.json`), B3 (`ck0_split.json`, `h_table.csv`), `gates.json`, `wp2_bottom.png`, `REPORT.md`
- Done: WP3 E1 (`pairs.csv`, `terms.csv`, `e1_chain.json`), E2/E3 (`e2_e3.csv`, `e2_e3_summary.json`), `T_top.json`, `wp3_top.png`, `REPORT.md`
- Current WP: none (local closeout complete)
- Done: WP4.1–3 `wp4/budget_decision.json` (EPS_EXTRA_hat 4.48 [2.35, 6.34] → L3; anchor-3 rule passes), `wp4/SOH_variants.csv`
- Done: WP4.4–6 probe assessment, `wp4/R13_HANDOFF.json`, README draft, `wp4/REPORT.md`
- Next: none. Round 12 is complete (Global Done); round 13 starts from `wp4/R13_HANDOFF.json`.
- Update 2026-10-20: the user authorised the push (D45), lifting D42; all commits are on `origin exp/phase2-r12-eps-level-20261019`.
- Last result commit: af263cb. Final documentation commit: `git log -1 --format=%h -- research/phase2_r12_eps_level_20261019/FINAL_REPORT.md` (self-reference).

- Final verification (2026-10-19): registered file hashes match 5/5; synthetic tests rerun 15/15 pass; budget arithmetic and handoff SOH agree; final-report SOH table checked against CSV; submission unchanged from base 6525edf.
- Completion scope: WP0–WP4 retain their existing completion records. Final documentation is locally complete. The original remote-push criterion is intentionally not fulfilled for the closeout commit because the user forbids uploads (D42).

## 中文收尾状态

WP0–WP4 保持原有完成记录；最终报告与研究目录 README 已在本地补齐。登记哈希 5/5 一致、合成测试 15/15 通过，预算与 SOH 已核对，提交包未改变。当前无剩余本地收尾工作；按用户“不得上传”的要求不执行 Git push，原 prompt 的远端同步条件不宣称满足。最后提交见上方命令。
