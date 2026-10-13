# DECISIONS (round 3)

- D0.1 Harness caches cut operation data and event tables under cache/ (git-ignored).
- D0.2 Pseudo-gap PG1/PG2 keep operation rows of month k-1's 45 C segment up to `t_measured` (last sample of the deep-discharge excursion) of the first / second step; later rows of that segment are dropped. Pseudo-cut PC5/PC10 cut all rows `days` before CK_k. Proxies stay P_k of CK_k.
- D0.3 G-impl: candidate output is rounded to 3 decimals (as run_model output); pass if |candidate - research| <= 0.001 pp.
- D0.4 Causality check corrupts current, voltages, chamber setpoint and mean temperature after the cutoff.
