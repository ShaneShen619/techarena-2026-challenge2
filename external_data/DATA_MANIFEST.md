<a id="en"></a>

# External datasets — inventory and screening (2026-10-14)

> English · [中文](#zh)

Raw files are git-ignored. This file and [data_manifest.json](data_manifest.json) (per-file bytes and SHA-256) are the tracked inventory. The folders also carry macOS Finder tags with the same labels.

## Inventory

| ID | Folder | Source / licence | Content | Capacity label | Tags |
|---|---|---|---|---|---|
| EXT-ESSL1 | `ESSL1/` | [zenodo 20132842](https://zenodo.org/records/20132842), CC BY 4.0 | LFP 102 Ah: 6 cells + 1 lab 16S pack, per-cycle CCCV charge segments (30 s), pack V1–V16 | same-cycle charge Ah ÷ 102 (**not independent**) | external, LFP, 16S-pack, label:charge-Ah, not-truth, use:beta |
| EXT-ESSL2 | `ESSL2/` | same record | LFP 105 Ah: 16 cells + 1 lab 15S pack | same-cycle charge Ah (**not independent**; a few corrupt values) | external, LFP, 15S-pack, label:charge-Ah, not-truth, use:beta |
| EXT-GOTION53 | `Battery_expansion_force_data/` | [mendeley 4nww8p6vxf](https://data.mendeley.com/datasets/4nww8p6vxf/1), CC BY 4.0 | Gotion 53 Ah LFP: 1 cell + 1 1P10S module, 1000 cycles, 1 s raw data, expansion force | **independent** calibration every 50 cycles (0.1 Ah resolution, protocol not stated) | external, LFP, 10S-module, label:independent-calibration, use:epsilon |
| EXT-LIC280 | `LIC_aging/` | [zenodo 20813753](https://zenodo.org/records/20813753), CC BY 4.0 | 280 Ah prismatic LFP, 700 1C cycles in 50-cycle blocks, 1 s raw data | **independent** 0.1C RPT every 50 cycles | external, LFP, 280Ah, label:independent-RPT, use:epsilon |

ESSL files are pandas 1.x pickles. They were scanned statically (pandas/numpy constructors only) and converted with an allow-list unpickler to `_converted/*.parquet`. Do not load the `.pkl` files with a plain `pandas.read_pickle`.

## Screening results

**None of these is the hidden CK1–CK7 truth, and none can be used to score the submission.** They test two assumptions of the model.

1. **Offset ε (charge Ah vs independent capacity) drifts slightly with ageing.**
   - EXT-LIC280: ε = 0.1C RPT capacity − first 1C CCCV charge from empty after the RPT. It moves from +0.22 to −0.25 Ah over 20.2 Ah of fade; slope −0.035 Ah per Ah lost. RPT k=5 is excluded because it hit the 10 h limit.
   - EXT-GOTION53 cell: charge Ah − calibration stays between −0.10 and −0.39 Ah over 4.4 Ah of fade; slope of ε −0.031 Ah per Ah lost.
   - EXT-GOTION53 module: +0.41 → −0.52 Ah (index alignment) or → −0.12 Ah (stretched alignment). Raw data hold 900 complete cycles against 1000 calibrated ones, so this case is inconclusive.
   - Transferred to the Challenge 2 pack (about 8 Ah of fade from CK0 to CK7), the two clean cases imply a common bias of roughly 0.25–0.3 pp by CK7. That bias is the same order as V2's proxy MAE (0.22 pp), and proxy scoring cannot see it.
2. **Graphite-step β (re-analysed 2026-10-14, restricted to 0–8 % fade).** An earlier whole-life fit (1.69 for the ESSL1 pack, 1.65–2.41 for the 56 °C cells) was contaminated: past about 12 % fade the step left the fixed 50–80 %-of-nominal search window. Within 0–8 % fade:
   - **Single cells (charge direction):** β ≈ 0.9–1.1.
   - **Packs:** β ≈ 1.1–1.2 (regression slope 1.12–1.17).
   - **LIC (0.1C RPT):** charge direction 0.68–0.83, discharge direction 1.19–1.44. The two directions differ.
   - **Simulated in-month updates** (`beta_sim.py`): fixed β = 1.3 is worse than β = 1 on 13 of 14 well-resolved series. Calibrating β on charge-direction steps and applying it to discharge-direction steps doubles the LIC error (0.23 → 0.56 pp).
   - **Cell aggregation** (`pack_agg.py`): in the ESSL1 pack, the median of per-cell step distances tracks pack Q better than the mean (R² 0.99 vs 0.89; single-cycle noise 0.29 vs 0.48 Ah) because 3 of 16 cells have step-detection jumps.
   - **Early-life shape:** the external sets fade with p = 0.56–1.09 (cycle-driven). Our pack follows p ≈ 0.44 per day (calendar-like), so their curve shapes do not transfer.
3. **Start state.** In EXT-LIC280, every 1C charge after the first in a block is about 1.5 Ah smaller than the first charge after an RPT (which starts from a 0.1C-empty state). This matches the model's start-state risk.
4. **Post-RPT rebound.** EXT-LIC280 shows no positive rebound in 1C discharge capacity after an RPT; the first 1–2 cycles are 0.2–0.4 Ah lower than the in-block trend. Resolution is limited by 0.78 Ah quantisation.

Protocol differences remain: 3.65 V vs 3.5 V per cell top, 0.1C vs C/20 references, cycling vs mostly 45 °C storage, and single cells vs a 4S pack. Treat these numbers as priors and risk bounds, not corrections to apply.

## Reproduce

Scripts are in `_screening/scripts/`, small outputs in `_screening/outputs/`. Run them with Python 3.11, pandas 1.5.3, numpy < 2, pyarrow < 15 and openpyxl: `convert.py` (ESSL → parquet), `essl_beta.py` (run inside `_converted/`), `gotion_steps.py` + `gotion_cycles.py`, `lic_segments.py` + `lic_eps.py`; re-analysis: `lic_curves.py` → `beta_series.py` → `beta_sim.py`, and `pack_agg.py`.

---

<a id="zh"></a>

# 外部数据集：清单与筛查（2026-10-14）

> [English](#en) · 中文

原始文件不进 git。本文件和 [data_manifest.json](data_manifest.json)（逐文件字节数与 SHA-256）是纳入版本管理的清单。各数据文件夹同时打了内容相同的 macOS Finder 标签。

## 清单

| ID | 文件夹 | 来源 / 许可 | 内容 | 容量标签 | 标签 |
|---|---|---|---|---|---|
| EXT-ESSL1 | `ESSL1/` | [zenodo 20132842](https://zenodo.org/records/20132842)，CC BY 4.0 | LFP 102 Ah：6 只单芯 + 1 个实验室 16 串电池组，每循环一段 CCCV 充电（30 s 采样），电池组含 V1–V16 | 同循环充电 Ah ÷ 102（**非独立测量**） | 外部数据、LFP 102Ah、16串电池组、标签=充电量(非真值)、用途:β校准 |
| EXT-ESSL2 | `ESSL2/` | 同上 | LFP 105 Ah：16 只单芯 + 1 个实验室 15 串电池组 | 同循环充电 Ah（**非独立测量**，个别坏值） | 外部数据、LFP 105Ah、15串电池组、标签=充电量(非真值)、用途:β校准 |
| EXT-GOTION53 | `Battery_expansion_force_data/` | [mendeley 4nww8p6vxf](https://data.mendeley.com/datasets/4nww8p6vxf/1)，CC BY 4.0 | 国轩 53 Ah LFP：1 只单芯 + 1 个 1P10S 模组，1000 次循环，1 s 原始数据，膨胀力 | **独立**容量标定，每 50 次循环一次（0.1 Ah 精度，协议未说明） | 外部数据、LFP 53Ah、10串模组、独立容量标定、用途:ε漂移检验 |
| EXT-LIC280 | `LIC_aging/` | [zenodo 20813753](https://zenodo.org/records/20813753)，CC BY 4.0 | 280 Ah 方壳 LFP，700 次 1C 循环，每 50 次一块，1 s 原始数据 | **独立** 0.1C RPT，每 50 次循环一次 | 外部数据、LFP 280Ah、单芯、独立RPT 0.1C、用途:ε漂移检验 |

ESSL 是 pandas 1.x 的 pickle 文件。已静态扫描（只引用 pandas/numpy 构造类），并用白名单加载器转换为 `_converted/*.parquet`。不要直接用 `pandas.read_pickle` 读取 `.pkl` 文件。

## 筛查结论

**这些数据都不是 CK1–CK7 的隐藏真值，也不能用来给提交模型打分。** 它们能检验模型依赖的两个假设。

1. **偏置 ε（充电 Ah 与独立容量之差）随老化有小幅漂移。**
   - EXT-LIC280：ε = 0.1C RPT 容量 − RPT 后第一次从空态开始的 1C CCCV 充电量。容量衰减 20.2 Ah 的过程中，ε 从 +0.22 Ah 变到 −0.25 Ah，斜率为每衰减 1 Ah 变化 −0.035 Ah。第 5 次 RPT 触发了 10 h 时间上限，已排除。
   - EXT-GOTION53 单芯：充电 Ah − 标定容量在衰减 4.4 Ah 的过程中保持在 −0.10 到 −0.39 Ah，ε 斜率 −0.031。
   - EXT-GOTION53 模组：按循环序号对齐时为 +0.41 → −0.52 Ah，按比例拉伸对齐时为 → −0.12 Ah。原始数据只有 900 个完整循环，标定表记到 1000 次，因此这一项无定论。
   - 换算到本题电池组（CK0 到 CK7 约衰减 8 Ah），两个可靠案例意味着到 CK7 时约有 0.25–0.3 pp 的共同偏差。这和 V2 的代理 MAE（0.22 pp）同一量级，而代理评分看不到它。
2. **石墨台阶 β（2026-10-14 重新分析，只看 0–8% 衰减）。** 之前按全寿命拟合的结果（ESSL1 电池组 1.69、56 °C 单芯 1.65–2.41）被污染了：衰减超过约 12% 后，台阶落到了固定的"额定容量 50–80%"搜索窗口之外。在 0–8% 衰减范围内：
   - **单芯（充电方向）：** β ≈ 0.9–1.1。
   - **电池组：** β ≈ 1.1–1.2（回归斜率 1.12–1.17）。
   - **LIC（0.1C RPT）：** 充电方向 0.68–0.83，放电方向 1.19–1.44，两个方向不一致。
   - **月内更新模拟**（`beta_sim.py`）：在 14 条台阶识别稳定的曲线中，有 13 条固定 β = 1.3 比 β = 1 差。用充电方向标定 β 再套到放电方向的台阶变化上，LIC 的误差从 0.23 pp 增大到 0.56 pp。
   - **电芯汇总方式**（`pack_agg.py`）：ESSL1 电池组里有 3/16 只电芯的台阶识别会跳。用各电芯台阶距离的中位数汇总，比均值更能跟住电池组容量（R² 0.99 对 0.89，单次噪声 0.29 对 0.48 Ah）。
   - **早期衰减形状：** 外部数据是循环老化，p = 0.56–1.09；我们电池组按天计 p ≈ 0.44，接近日历老化，所以外部数据的曲线形状不能借用。
3. **起点状态。** EXT-LIC280 中，每块内第一次之后的 1C 满充都比 RPT 后第一次满充（从 0.1C 放空状态开始）少约 1.5 Ah，与模型的起点风险一致。
4. **RPT 后回弹。** EXT-LIC280 中 RPT 之后 1C 放电容量没有正向回弹；头 1–2 个循环反而比块内趋势低 0.2–0.4 Ah。分辨率受 0.78 Ah 量化台阶限制。

协议差异仍然存在：单芯充电上限 3.65 V 对比 3.5 V，参考测试 0.1C 对比 C/20，循环老化对比以 45 °C 存储为主，单芯对比 4 串电池组。以上数字只能作为先验和风险范围，不能直接拿来修正模型。

## 复现

脚本在 `_screening/scripts/`，小型结果在 `_screening/outputs/`。环境：Python 3.11、pandas 1.5.3、numpy < 2、pyarrow < 15、openpyxl。依次为：`convert.py`（ESSL 转 parquet）、`essl_beta.py`（在 `_converted/` 下运行）、`gotion_steps.py` + `gotion_cycles.py`、`lic_segments.py` + `lic_eps.py`；重新分析：`lic_curves.py` → `beta_series.py` → `beta_sim.py`，以及 `pack_agg.py`。
