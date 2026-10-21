# DECISIONS

- **D0.1 (WP0)** The round-3 harness is copied into `src/harness.py` so its cache lands in this study's git-ignored `cache/`, not in the round-3 study directory (no earlier study directory is written). `common17.py` imports that copy.
- **D0.2 (WP0)** SUB per-case predictions: the round-10 CSV holds model `A3` (= SUB 6525edf) and a model literally named `SUB` (an older submission). `A3` is used, as the prompt says; its real Δ=0.4 SOH matches SUB's expected SOH within 0.001 pp.
- **D1.1 (WP1)** P1 rule "differ by > 20 %" is read relative to the primary (Schimpe): |20.592 − 17.126| / 20.592 = 16.8 % → Schimpe 20.592 kJ/mol on k. (Relative to Naumann it would be 20.2 %.) Naumann's value (34.25 on time) is reported as a C sensitivity, not selected.
- **D1.2 (WP1)** P2: Naumann's cubic deviates from the TUM √t table by up to 40 % (12.5 % SOC) → by the registered rule k_SOC = TUM table (25/40 °C mean where both exist, else 40 °C), linear interpolation in SOC; `k_SOC_alt` = Naumann cubic.
- **D1.3 (WP1)** Lewerenz 2018 full-compensation times are 100/250/490 d at 50/40/30 °C (PDF p. 157); the 2026-10-16 notes' "150 d at 50 °C" is wrong. τ_oh = t_full/3 → 48.6 d at 45 °C, 249.5 d at 25 °C (stated Ea 64.5 line through 50 °C/100 d).
- **D1.4 (WP1 → WP2, registered before any S run)** In S the clock weight is k_SOC(SOC)**2, not k_SOC: both sources write Q = k(T,SOC)·√t with the virtual-time rule (Naumann Eq. 17), so Q = √(Σ k² dt). This is the same doubling the prompt applies to Ea in C. The prompt's linear form is kept as a sensitivity.
