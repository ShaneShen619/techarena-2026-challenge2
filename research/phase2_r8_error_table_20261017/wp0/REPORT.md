<a id="en"></a>

# WP0 — Setup and re-baselining

> **Language:** English · [中文](#zh)

**Result: SUB = T_main reproduces exactly; the submitted class equals the research implementation and `EXPECTED_SOH`.** Script [run_wp0.py](run_wp0.py); outputs [outputs/reproduce.json](outputs/reproduce.json). A rerun is byte-identical.

| Check | Value | Target (±0.001 pp) | Pass |
|---|---|---|---|
| Proxy MAE Δ0 / 0.4 / 0.8 | 0.1972 / 0.1257 / 0.1464 | 0.197 / 0.126 / 0.146 | yes |
| Proxy MAX Δ0 / 0.4 / 0.8 | 0.6090 / 0.2277 / 0.2277 | 0.609 / 0.228 / 0.228 | yes |
| Pseudo / cold start | 0.1439 / 0.1703 | 0.144 / 0.170 | yes |
| One-month causal gap cases (PC10, k 3–7) | 0.1048 | 0.105 | yes |
| Submitted class (`5cd305c`) vs research, per checkup | max 1.4e-14 pp | ≤ 0.0005 pp | yes |
| Submitted class, rounded, vs `EXPECTED_SOH` | equal at CK0–CK7 | equal | yes |

**Branch inventory** ([wp0_branch_by_case.csv](outputs/wp0_branch_by_case.csv), [counts](outputs/wp0_branch_counts.csv)), 47 cases per Δ (D0.2):

| Scenario | fallback | phase | sqrt_gap |
|---|---|---|---|
| real | 2 (CK1, CK3) | 4 (CK4–7) | 1 (CK2) |
| PG1 / PG2 | 0 / 1 | 0 / 0 | 4 / 3 |
| PC5 / PC10 | 1 / 0 | 4 / 0 | 0 / 5 |
| CS / CSE | 5 / 0 | 0 / 0 | 0 / 5 |
| PC5_all / PC10_all | 1 / 0 | 4 / 0 | 1 / 6 |

Setup: worktree `/Users/shane/Desktop/Arena_1017_r8_err`, branch `exp/phase2-r8-error-table-20261017` from `c9658ad`; copied code in [../sources/SOURCES.md](../sources/SOURCES.md); decisions D0.1 (cache location) and D0.2 (scenario set).

---

<a id="zh"></a>

# WP0——环境搭建与重新基线

> **语言：** [English](#en) · 中文

**结论：SUB = T_main 完全复现；提交类与研究实现及 `EXPECTED_SOH` 一致。** 脚本 [run_wp0.py](run_wp0.py)，输出 [outputs/reproduce.json](outputs/reproduce.json)；重跑结果逐字节相同。

| 检查 | 数值 | 目标（±0.001 pp） | 通过 |
|---|---|---|---|
| 代理 MAE Δ0 / 0.4 / 0.8 | 0.1972 / 0.1257 / 0.1464 | 0.197 / 0.126 / 0.146 | 是 |
| 代理 MAX Δ0 / 0.4 / 0.8 | 0.6090 / 0.2277 / 0.2277 | 0.609 / 0.228 / 0.228 | 是 |
| 伪场景 / 冷启动 | 0.1439 / 0.1703 | 0.144 / 0.170 | 是 |
| 一个月因果缺口案例（PC10，k 3–7） | 0.1048 | 0.105 | 是 |
| 提交类（`5cd305c`）与研究实现逐检查点比较 | 最大 1.4e-14 pp | ≤ 0.0005 pp | 是 |
| 提交类四舍五入后与 `EXPECTED_SOH` | CK0–CK7 全部相同 | 相同 | 是 |

**分支清单**：每个 Δ 47 个案例（D0.2）。real：fallback 2（CK1、CK3）、phase 4（CK4–7）、sqrt_gap 1（CK2）；其余场景见英文表格。

环境：worktree `/Users/shane/Desktop/Arena_1017_r8_err`，分支 `exp/phase2-r8-error-table-20261017`，基于 `c9658ad`；复制的代码见 [../sources/SOURCES.md](../sources/SOURCES.md)；决策 D0.1（缓存位置）和 D0.2（场景集合）。
