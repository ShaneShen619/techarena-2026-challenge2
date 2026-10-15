<a id="en"></a>

# Draft — Open data used (REPORT.md section 2)

> **Language:** English · [中文](#zh)

| Dataset | Source / URL | Licence | How it was used | In the submitted model? |
|---|---|---|---|---|
| Challenge 1 LFP 102 Ah cells (6 cells, 25–55 °C, 0.5/1C) | TechArena 2026 Challenge 1 release | competition data | prior for the stress law's time exponent and break-in shape (5A/5C) | no |
| Yagci et al. 2025, 180 Ah LFP storage + cycling | doi 10.1016/j.est.2025.116774; data doi 10.5281/zenodo.22939281 (cite also 10.5281/zenodo.22010995 as the readme requires) | CC BY 4.0 | published calendar/cyclic losses and Ea = 37.3 kJ/mol as the prior centre (5A/5C); raw data for the WP4 calendar prior (in progress) | no |
| TEMPEST 280 Ah LFP (0.1C RPT every 50 cycles) | doi 10.5281/zenodo.20813753 | CC BY 4.0 | ε drift ≈ −0.035 Ah per Ah of fade; cycle-term prior (WP4) | no (risk statement; WP3 drift variant) |
| Gotion 53 Ah LFP cell + 10S module | doi 10.17632/4nww8p6vxf.1 | CC BY 4.0 | ε drift ≈ −0.031 Ah per Ah; cycle-term prior (WP4) | no (risk statement; WP3 drift variant) |
| ESSL1 / ESSL2 LFP 102/105 Ah cells and 16S/15S packs | doi 10.5281/zenodo.20132842 | CC BY 4.0 | graphite-step β in packs (1.1–1.2) and cells (0.9–1.1) | no (β cap tested, rejected) |
| PyBaMM half-cell OCPs (Afshar 2017 LFP; Chen 2020 / Ecker 2015 graphite) | PyBaMM 26.10.1.0 | BSD-3-Clause | electrode-level model (5B; not identifiable on this pack) | no |

**Data efficiency.** The submitted model uses only the released operating data and the single CK0 label. No external data or pre-training enters it; the open data bound its assumptions (ε drift, β) and support the explored alternatives.

---

<a id="zh"></a>

# 草稿——使用的开放数据（REPORT.md 第 2 节）

> **语言：** [English](#en) · 中文

| 数据集 | 来源 / 网址 | 许可证 | 用途 | 是否进入提交模型 |
|---|---|---|---|---|
| Challenge 1 的 LFP 102 Ah 电芯（6 枚，25–55 °C，0.5/1C） | TechArena 2026 Challenge 1 发布 | 竞赛数据 | 应力定律时间指数和磨合形状的先验（5A/5C） | 否 |
| Yagci 等 2025，180 Ah LFP 存储 + 循环 | doi 10.1016/j.est.2025.116774；数据 doi 10.5281/zenodo.22939281（按 readme 要求，同时引用 10.5281/zenodo.22010995） | CC BY 4.0 | 公布的日历 / 循环损失和 Ea = 37.3 kJ/mol 作为先验中心（5A/5C）；原始数据用于 WP4 的日历先验（进行中） | 否 |
| TEMPEST 280 Ah LFP（每 50 循环一次 0.1C RPT） | doi 10.5281/zenodo.20813753 | CC BY 4.0 | ε 漂移约为每衰减 1 Ah 漂移 −0.035 Ah；循环项先验（WP4） | 否（风险说明；WP3 漂移变体） |
| Gotion 53 Ah LFP 单芯 + 10 串模组 | doi 10.17632/4nww8p6vxf.1 | CC BY 4.0 | ε 漂移约为每 Ah −0.031 Ah；循环项先验（WP4） | 否（风险说明；WP3 漂移变体） |
| ESSL1 / ESSL2 LFP 102/105 Ah 电芯与 16 串 / 15 串电池组 | doi 10.5281/zenodo.20132842 | CC BY 4.0 | 电池组（1.1–1.2）和单芯（0.9–1.1）的石墨台阶 β | 否（测试过 β 上限，未采用） |
| PyBaMM 半电池 OCP（Afshar 2017 LFP；Chen 2020 / Ecker 2015 石墨） | PyBaMM 26.10.1.0 | BSD-3-Clause | 电极级模型（5B；在本电池组上不可辨识） | 否 |

**数据效率。** 提交的模型只使用发布的运行数据和唯一的 CK0 标签，不引入任何外部数据，也没有预训练；开放数据用于约束其假设（ε 漂移、β），并支撑探索过的替代方案。
