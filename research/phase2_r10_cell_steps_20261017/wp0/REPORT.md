<a id="en"></a>

# WP0 — Setup and re-baselining

> **Language:** English · [中文](#zh)

**Result: every reproduction passes.** Script [run_wp0.py](run_wp0.py); [outputs/reproduce.json](outputs/reproduce.json). A rerun is byte-identical.

| Check | Result |
|---|---|
| SUB real MAE / MAX, pseudo 0.1439, cold 0.1703, per-checkup errors | match (≤ 0.001 pp) |
| Round 9 P2a (median): pseudo 0.1385, cold 0.1511, real 0.1135 | match |
| Round 9 per-variant table (SUB and P2a, 6 variants) | max diff 8e-17 pp |
| Branch-freeze framework with cell mean = SUB | 0.0 Ah on all scenarios, Δ and variants (D0.1) |
| Submitted `5cd305c` class vs research; vs `EXPECTED_SOH` | equal |

**Caches.** The per-cell locations of all 6 variants are in the harness tables (`H.tables`, one per scenario cut). Per-cell CV-end voltages for 28 cuts (41 programs in the full data) are in `cache/cvv_*.pkl`.

**Noise scale** ([outputs/noise_scale.json](outputs/noise_scale.json)): σ_det = 1.4826·MAD of per-cell R_seg (45 °C segments 1, 5, 7, 9, 11, 13; 100 cell rows). The main variant equals round 8's R_seg to 7e-15.

| variant | pooled σ_det (Ah) | τ = 3·√2·σ (Ah) |
|---|---|---|
| main | 0.0897 | 0.380 |
| band_narrow | 0.1048 | 0.445 |
| windows_minus3 | 0.0664 | 0.282 |
| windows_plus3 | 0.1012 | 0.429 |
| dvdq_peak | 0.3707 | 1.573 |
| ir_corrected | 0.1024 | 0.434 |

dvdq_peak is about 4 times noisier than the others: it sits on a 0.25 Ah grid. This is the likely reason the median failed on it in round 9.

---

<a id="zh"></a>

# WP0——环境搭建与重新基线

> **语言：** [English](#en) · 中文

**结论：所有复现全部通过。** 重跑结果逐字节相同。
- SUB 的真实 MAE/MAX、伪场景 0.1439、冷启动 0.1703 和逐检查点误差均一致。
- 第 9 轮中位数（P2a）的数字及逐变体表一致。
- 分支冻结框架取单体均值时等于 SUB（误差 0.0 Ah）。
- 提交类 = 研究实现 = EXPECTED_SOH。

检测噪声尺度 σ_det 见英文表格：主变体 0.090 Ah，阈值 τ = 0.380 Ah。dvdq_peak 的噪声约为其他变体的 4 倍（0.25 Ah 网格），这很可能就是第 9 轮中位数在它上面失败的原因。
