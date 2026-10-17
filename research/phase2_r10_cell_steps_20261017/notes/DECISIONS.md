<a id="en"></a>

# DECISIONS (round 10)

> **Language:** English · [中文](#zh)

- **D0.1 (WP0, branch-freeze implementation).** Candidates replay SUB's selection with `internals.decompose(ctx, "SUB")`, which takes the branch, E_cur/E_prev, the rate-fit set, after[0]/after[-1], d and β from SUB on the ctx's own detection variant. With main-variant cells and the cell mean, the framework reproduces SUB on all scenarios, Δ and variants to 0.0 Ah. With the cell median it reproduces round 9's P2a and its per-variant table to 1e-16 pp. No selected program had a NaN cell value.
- **D2.1 (WP2, G_event for change candidates).** B-type candidates combine per-cell changes and have no per-program position series. Their G_event uses a chained series: within each segment, start at the 4-cell mean of the first program and add the combined per-cell change between consecutive programs. This tests whether combining changes yields a smoother step series than SUB's cell mean.
- **D2.2 (WP2, B3 robustness).** B3 is built on the A3 ensemble, so its G_robust uses the six leave-one-variant-out A3 ensembles, as in WP1. τ is held at the full-ensemble value for every rebuild.
- **D3.1 (WP3, C1/C2 degeneracy, noted after the exit).** As written in the prompt, C1 (loc_c − k·u_c) and C2 (loc_c − w_c) subtract deviations from the cell mean, which sum to zero over the four cells. Followed by the 4-cell mean, they reproduce SUB exactly and could never pass G_changed. Only C3 (correction followed by rejection) or a median would have been informative. WP3 exited at WP3a, so no candidate was registered or evaluated.

---

<a id="zh"></a>

# 决策记录（第 10 轮）

> **语言：** [English](#en) · 中文

- **D0.1（WP0，分支冻结的实现）。** 候选通过 `internals.decompose(ctx, "SUB")` 重放 SUB 的选择：分支、E_cur/E_prev、速率拟合集、after[0]/after[-1]、d 和 β 都取自 ctx 自身检测变体上的 SUB。用主变体单体加单体均值时，该框架在所有场景、Δ 和变体上复现 SUB，误差 0.0 Ah；用单体中位数时复现第 9 轮的 P2a 及其逐变体表，误差 1e-16 pp。所有被选中的程序都没有出现 NaN 单体值。
- **D2.1（WP2，变化量候选的 G_event）。** B 类候选合并的是单体变化量，没有逐程序的位置序列。它们的 G_event 使用链式序列：每段从首个程序的四单体均值出发，依次加上相邻程序之间合并后的单体变化。这检验合并变化量是否比 SUB 的单体均值得到更平滑的台阶序列。
- **D2.2（WP2，B3 的稳健性）。** B3 建立在 A3 集成之上，所以它的 G_robust 与 WP1 一样，使用 6 个留一变体的 A3 集成；每次重建都把 τ 固定为完整集成的值。
- **D3.1（WP3，C1/C2 退化，退出后记录）。** 按 prompt 的写法，C1（loc_c − k·u_c）和 C2（loc_c − w_c）减去的是相对单体均值的偏差，四个单体加起来为零。再取四单体均值后会完全等于 SUB，永远无法通过 G_changed。只有 C3（修正后再剔除）或中位数才有信息量。WP3 在 WP3a 处退出，因此没有登记或评估任何候选。
