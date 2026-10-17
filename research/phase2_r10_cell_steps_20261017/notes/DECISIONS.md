<a id="en"></a>

# DECISIONS (round 10)

> **Language:** English · [中文](#zh)

- **D0.1 (WP0, branch-freeze implementation).** Candidates replay SUB's selection with `internals.decompose(ctx, "SUB")`, which takes the branch, E_cur/E_prev, the rate-fit set, after[0]/after[-1], d and β from SUB on the ctx's own detection variant. With main-variant cells and the cell mean, the framework reproduces SUB on all scenarios, Δ and variants to 0.0 Ah. With the cell median it reproduces round 9's P2a and its per-variant table to 1e-16 pp. No selected program had a NaN cell value.

---

<a id="zh"></a>

# 决策记录（第 10 轮）

> **语言：** [English](#en) · 中文

- **D0.1（WP0，分支冻结的实现）。** 候选通过 `internals.decompose(ctx, "SUB")` 重放 SUB 的选择：分支、E_cur/E_prev、速率拟合集、after[0]/after[-1]、d 和 β 都取自 ctx 自身检测变体上的 SUB。用主变体单体加单体均值时，该框架在所有场景、Δ 和变体上复现 SUB，误差 0.0 Ah；用单体中位数时复现第 9 轮的 P2a 及其逐变体表，误差 1e-16 pp。所有被选中的程序都没有出现 NaN 单体值。
