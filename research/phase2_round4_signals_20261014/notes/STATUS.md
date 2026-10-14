# STATUS (round 4)

Start 2026-10-14 20:21 CEST, worktree /Users/shane/Desktop/Arena_1014_round4, branch exp/phase2-round4-signals-20261014.

| Stage | State | Notes |
|---|---|---|
| 0 setup | done | V2 0.215726/0.669052, M4 0.291265 reproduced (stage0/reproduce.json) |
| 1 month-end regression | done (fail) | S1 0.242 > 0.216; in-segment residual SD 0.012-0.036 Ah -> V2 error is systematic, not noise |
| 2 dynamic crossings | done (exit) | closure median 0.61 Ah > 0.2; extra crossings only at day 4 of each cycle |
| 3 rest pseudo-OCV | done (exit) | all 110 rests at 0-22 Ah below CV end; none near the step |
| 4 top-21-Ah feature | done (exit) | 'peak' = window-edge artefact; valley 16.4-16.8 Ah, no trend |
| 5 recovery physics | done | recovery 0.02->0.87 Ah, tau ~2.5 d; ranking V1>V2 if C/20 is pre/partly recovered |
| 6 eps temperature | next | |
| 7 round-3 leads | todo | |
| 8 final report | todo | |
