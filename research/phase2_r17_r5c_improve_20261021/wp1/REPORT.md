<a id="en"></a>

# WP1 — External parameters, frozen before use

> **Language:** English · [中文](#zh)

`outputs/external_params.json` was frozen and committed in e787faa, before any design run. SHA256: `cb29e4e799d880f3b06115431ac0ec22771c26d281b710190974a9b73388c6c6`. No pack data or proxy was read.

## Conclusions first

| Id | Parameter | Value used | Source | Note |
|---|---|---|---|---|
| P1 | Calendar Ea on k | **20.592 kJ/mol** (Schimpe); clock Ea_time = **41.18 kJ/mol** in C | Schimpe 2018 *JES* 165:A181, p. A184 Eq. (4), fitted at SOC = 100 %; Q = k·√t (Eq. 2) | Naumann 2018 Table 7 gives 17.126 kJ/mol; 16.8 % apart (< 20 % of the primary), so Schimpe is used (D1.1) |
| P2 | k_SOC(SOC) | **TUM data table**, squared in the clock (D1.4); `k_SOC_alt` = Naumann cubic | TUM Mendeley kxh42bfgtj (Naumann 2018 data), pure √t fits over 0–400 d at 25/40 °C | Naumann Eq. (12), c = 2.8575, d = 0.60225, deviates from the data by up to 40 % (12.5 % SOC), so it fails the ±30 % rule |
| P3 | Overhang | f_oh = 0.062 (Sony); τ_oh = t_full/3 = **48.6 d at 45 °C, 249.5 d at 25 °C**; Ea 64.5 kJ/mol | Lewerenz 2018 *J. Energy Storage* 18:149, p. 151 Eq. (3), p. 155 Eqs. (3)/(4), Table 4, p. 157 Eq. (5); Naumann 2018 p. 156 | t_full = 100/250/490 d at 50/40/30 °C. The earlier notes' "150 d at 50 °C" is wrong (D1.3). Fitting a line through the three points gives Ea = 64.6, i.e. τ 51 d / 263 d (sensitivity) |
| P4 | Cycle term | Label only | Naumann 2020 *JPS* 451:227666 §3.2.1, §3.3.2 | Reversible shallow-cycle loss appears only in static DOC < 80 % tests and is not modelled by the authors. In dynamic profiles, pure cycle ageing is 28.35 % (PV-HESS) and 2.61 % (PV-PCR) of the total |

**k_SOC shape** (normalised to 50 % SOC):

| SOC | 0 | 12.5 | 25 | 37.5 | 50 | 62.5 | 75 | 87.5 | 100 |
|---|---|---|---|---|---|---|---|---|---|
| TUM table (used) | 0.296 | 0.534 | 0.804 | 1.025 | 1 | 1.108 | 1.362 | 1.736 | 2.160 |
| Naumann Eq. 12 (alt) | 0.407 | 0.750 | 0.926 | 0.991 | 1 | 1.009 | 1.074 | 1.250 | 1.593 |
| Schimpe Eq. 8 (cross-check) | 0.125 | 0.356 | 0.602 | 0.878 | 1 | 1.085 | 1.351 | 1.585 | 1.644 |

The data table and Schimpe's anode-potential form agree well from 62.5 % to 100 %. Naumann's cubic is flatter than its own data. Plot: `outputs/k_soc_comparison.png`.

**Why k_SOC and Ea are squared in the clock (D1.4).** Both sources write Q = k(T, SOC)·√t and accumulate changing conditions by "virtual time" (Naumann 2018 Eq. 17). Then dQ/dt = k²/(2Q), so Q = √(Σ k² dt). A factor on k therefore enters the clock squared. That is why C uses 2 × 20.592 on time, and why S weights time by k_SOC². Linear k_SOC is kept as a sensitivity.

**P5 transfer caveats.**
- P1 and P2 come from Sony US26650FTC1 3 Ah LFP/C cells. The pack is 102 Ah prismatic LFP of unknown make; only the shape of k_SOC is expected to transfer.
- P3 comes from 25 Ah NMC/graphite prismatic cells. The anode-side mechanism transfers; the overhang geometry does not.
- P4 comes from 40 °C tests. The pack runs at 25/45 °C and discharges 56 Ah deep in every block.

**Downloads.** One, as permitted: Schimpe 2018 (IOP open access, SHA `8c4aa800…`, in the git-ignored `cache/papers/`).

---

<a id="zh"></a>

# WP1 — 外部参数，使用前冻结

> **语言：** [English](#en) · 中文

`outputs/external_params.json` 在 e787faa 中冻结并提交，早于任何设计运行。SHA256：`cb29e4e799d880f3b06115431ac0ec22771c26d281b710190974a9b73388c6c6`。没有读取电池组数据或代理。

## 结论在前

| 编号 | 参数 | 采用值 | 来源 | 说明 |
|---|---|---|---|---|
| P1 | 加在 k 上的日历 Ea | **20.592 kJ/mol**（Schimpe）；C 中的时钟 Ea_time = **41.18 kJ/mol** | Schimpe 2018 *JES* 165:A181，p. A184 式 (4)，在 SOC = 100% 下拟合；Q = k·√t（式 2） | Naumann 2018 表 7 给出 17.126 kJ/mol；两者相差 16.8%（< 主来源的 20%），所以用 Schimpe（D1.1） |
| P2 | k_SOC(SOC) | **TUM 数据表**，在时钟里取平方（D1.4）；`k_SOC_alt` = Naumann 三次式 | TUM Mendeley kxh42bfgtj（Naumann 2018 的数据），25/40 °C 下 0–400 天纯 √t 拟合 | Naumann 式 (12)（c = 2.8575，d = 0.60225）与数据最多相差 40%（12.5% SOC），不满足 ±30% 规则 |
| P3 | Overhang | f_oh = 0.062（Sony）；τ_oh = t_full/3 = **45 °C 下 48.6 天、25 °C 下 249.5 天**；Ea 64.5 kJ/mol | Lewerenz 2018 *J. Energy Storage* 18:149，p. 151 式 (3)，p. 155 式 (3)/(4)、表 4，p. 157 式 (5)；Naumann 2018 p. 156 | 50/40/30 °C 下 t_full = 100/250/490 天。之前笔记写的"50 °C 下 150 天"有误（D1.3）。用三个点拟合直线得 Ea = 64.6，即 τ 为 51 天 / 263 天（敏感性） |
| P4 | 循环项 | 只作标签 | Naumann 2020 *JPS* 451:227666 §3.2.1、§3.3.2 | 浅循环的可逆损失只出现在静态 DOC < 80% 的试验中，作者没有建模。动态剖面中纯循环老化占总老化的 28.35%（PV-HESS）和 2.61%（PV-PCR） |

**k_SOC 的形状**（以 50% SOC 归一）：

| SOC | 0 | 12.5 | 25 | 37.5 | 50 | 62.5 | 75 | 87.5 | 100 |
|---|---|---|---|---|---|---|---|---|---|
| TUM 表（采用） | 0.296 | 0.534 | 0.804 | 1.025 | 1 | 1.108 | 1.362 | 1.736 | 2.160 |
| Naumann 式 12（alt） | 0.407 | 0.750 | 0.926 | 0.991 | 1 | 1.009 | 1.074 | 1.250 | 1.593 |
| Schimpe 式 8（交叉核对） | 0.125 | 0.356 | 0.602 | 0.878 | 1 | 1.085 | 1.351 | 1.585 | 1.644 |

数据表与 Schimpe 基于负极电位的形式在 62.5% 到 100% 之间吻合得很好；Naumann 的三次式比它自己的数据平缓。图：`outputs/k_soc_comparison.png`。

**为什么 k_SOC 和 Ea 在时钟里要平方（D1.4）。** 两个来源都写成 Q = k(T, SOC)·√t，条件变化时按"虚拟时间"累加（Naumann 2018 式 17）。于是 dQ/dt = k²/(2Q)，即 Q = √(Σ k² dt)。所以加在 k 上的因子进入时钟时要平方。这就是 C 在时间上用 2 × 20.592、S 用 k_SOC² 给时间加权的原因。线性 k_SOC 保留为敏感性。

**P5 迁移注意事项。**
- P1 和 P2 来自 Sony US26650FTC1 3 Ah LFP/C 电芯。电池组是 102 Ah 方形 LFP，品牌未知；预计只有 k_SOC 的形状可以迁移。
- P3 来自 25 Ah NMC/石墨方形电芯。负极侧的机理可以迁移，overhang 的几何不能。
- P4 来自 40 °C 试验。电池组在 25/45 °C 下运行，每个程序块都有 56 Ah 的深放电。

**下载。** 只有一次，在允许范围内：Schimpe 2018（IOP 开放获取，SHA `8c4aa800…`，存于 git 忽略的 `cache/papers/`）。
