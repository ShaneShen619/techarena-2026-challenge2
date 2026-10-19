# Sources

Every file in `sources/` with its origin and SHA256. All were read with `git -C /Users/shane/Desktop/Arena_1013_model show <ref>:<path>` on 2026-10-19. Challenge data are read in place from this worktree (never copied).

| File | Origin | SHA256 |
|---|---|---|
| r11_FINAL_REPORT.md | git show exp/phase2-r11-eps-transfer-20261018 (tip ff45b48): research/phase2_r11_eps_transfer_20261018/FINAL_REPORT.md | e15f33b42a33ee197d62df6be4d13b6fed9f3710bb6bad5ef1067368eb19b052 |
| r11_wp4_pack_drivers.csv | git show exp/phase2-r11-eps-transfer-20261018 (tip ff45b48): research/phase2_r11_eps_transfer_20261018/wp4/pack_drivers.csv | 9ab950bac46f61cb88e33e71aed7af74402beb88af1209cce52c92935ca02cd1 |
| r11_wp4_pack.py | git show exp/phase2-r11-eps-transfer-20261018 (tip ff45b48): research/phase2_r11_eps_transfer_20261018/src/wp4_pack.py (round 11's CV fit) | caf0d1adbcfde763b8f1efcbc47b5e913ea4f313f79793c786831a285e4a4b6b |
| r11_drift.py | git show exp/phase2-r11-eps-transfer-20261018 (tip ff45b48): research/phase2_r11_eps_transfer_20261018/src/drift.py ("SUB + drift d", copied from round 7 WP3) | 0ad5a9d38152f0fb0c8fb8d762d8090a506ad4153c86caf4a0443f42df5588fe |
| r11_wp5_R12_HANDOFF.json | git show exp/phase2-r11-eps-transfer-20261018 (tip ff45b48): research/phase2_r11_eps_transfer_20261018/wp5/R12_HANDOFF.json | b15c18daa1d85174f5d6c7d17d2a8788afa5cb14aa3649c81cd661ad715653c3 |
| r8_DATA_DICTIONARY.md | git show exp/phase2-r8-error-table-20261017 (tip 126173a): research/phase2_r8_error_table_20261017/DATA_DICTIONARY.md | 80c38dbca4e5dddd315c6ec26bb9fe187ff1e635f200abb63eaac4dccdf8ef7b |
| r8_table_events.csv | git show exp/phase2-r8-error-table-20261017 (tip 126173a): research/phase2_r8_error_table_20261017/outputs/table_events.csv | fddf6c190b8a970d2bfa467018e0bafd663fff674ffa5fcdb66da941a4858570 |
| r8_table_anchors.csv | git show exp/phase2-r8-error-table-20261017 (tip 126173a): research/phase2_r8_error_table_20261017/outputs/table_anchors.csv | 061db0ffd340a8f152beabdfafedada463d9f49ed66d9bf6620df2992f45e152 |
| r5b_FINAL_REPORT.md | git show exp/phase2-r5b-electrode-model-20261014 (tip 63b16ac): research/phase2_r5b_electrode_model_20261014/FINAL_REPORT.md | 7a9d09372106cd97eb0d995016043fbc323d59406bf4600ea7abea1cf54d8401 |

Read in place (not copied):

- Challenge data: `TechArena_Challenge2_Team_Package/data/` of this worktree (identical to base `6525edf`).
  - sha256 `data/checkups/CK0_reference_discharge.csv.gz`: fe244391b1a492dce4909b087f3ee196bd6edf91bf3f8c05abd177c31b3a377a
- SUB: `TechArena_Challenge2_Team_Package/my_model/model_template.py` at `6525edf`, sha256 3bd26ed8bbb5890fec5efa53606a03c39b55f52b04a0cf1e5f92ae0e36a2fbd5; run through `run_model.py` into `cache/sub/` (git-ignored).
