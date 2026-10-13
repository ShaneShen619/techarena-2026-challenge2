# Frozen execution protocol — 2026-10-10

Use the supplied execution plan and experiment.json. Raw datasets and legacy projects are read-only.
Six whole-cell outer folds and training-only inner folds; all source-derived model/cache keys include the training entity set.
Targets are the existing 180 fixed dates; labels live in panel_scoring.csv and are never exposed to target feature extraction.
Primary ranking: 20 Ah strict shallow A + legal prior charging history. 15/30 Ah are sensitivity strata.
Reuse v1.5 cropped observations only after provenance/hash verification and independent raw prefix replay. Full-history exposure is reconstructed from raw inputs.
Simple age/throughput baselines and B use identical history input. D1-restricted does not allow B's full-history coordinate and is separately marked not_applicable.
Source labels/temperature may be complete for training cells; no heldout target labels enter source fit, scaling, imputation, selection or residual generation.
No tuning on official CK trajectory. No reconstruction of hidden CK answers. No root ActiveModel switch.
E5 is conditional: if E3 B gate fails, numeric fusion is skipped and monitoring/E4 diagnostic can continue.
No independent 4S C/20 label exists locally: E7 must remain not_testable.
