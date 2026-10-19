<a id="en"></a>

# WP0 fact sheet

> **Language:** English · [中文](#zh)

Written 2026-10-19. Every bullet under "Facts already established" in §2 of `EXECUTION_PROMPT.md` was re-checked against the challenge data of this worktree. Numbers come from `src/wp0_events.py` (`events.csv`) and `src/wp0_facts.py` (`facts.json`, `switches.csv`, `checkup_windows.csv`, `integration_check.csv`, `pulses_programs.csv`, `counter_booking_by_segment.csv`, `in_segment_gaps.csv`).

**WP0 rule.** WP0 computes no Ah balance, step location or ε-related estimate. Bullets that need one are marked **deferred** and point to the registered WP2/WP3 measurement. Step-related bullets that earlier rounds already exposed are **cited** from their source and not recomputed.

## Summary

- **Confirmed:** 23 bullets (#34 by citation); #35, the scope change, is recorded.
- **Corrected:** 6 bullets, all small: the 264 mV and 88 → 52 mV spreads are CV-end values, Q_fc,2 = 95.67 Ah, CV Ah depends on how the CV start is defined, the 30-min pack range is 13.432–13.439 V, and the bottom spread is 22 → 36 mV.
- **Cited, not recomputed:** 2 bullets (the first-program offset and the 25 → 45 °C step jump).
- **Deferred:** 3 bullets (anchor 3's extra Ah, the next top-up's +0.1 Ah, the block Ah balance).
- **New facts that matter later:**
  - Segment 6 has two recording gaps (3.65 h and 16.64 h) between anchor 3's CV end (E14) and the next top-up (E15). Segment 14 has one 29-min gap between E40 (anchor 7) and E41.
  - The counters stay flat across all three gaps (+0.051 Ah at most), so the profile paused. The blocks are 20.3 h longer there.
  - WP3's pair rule excludes these pairs.
  - In anchor 0's 0.5 h rest the pack is **cooling** (47.01 → 46.54 °C), not warming.

## 1. Re-verification of §2

| # | Fact (prompt) | Data | Status |
|---|---|---|---|
| 1 | CK0 C/20 curve 2025-01-15 14:03:42 → 2025-01-16 09:44:56 at 5.10 A | 14:03:42 → 09:44:56, median −5.100 A (mean −5.1003), 19.69 h | confirmed |
| 2 | starts at 13.590 V under load | 13.590 V (cells 3.374/3.351/3.511/3.359) | confirmed |
| 3 | delivers 100.41 Ah | 100.410 Ah at 11.201 V; 100.412 Ah at the last sample (11.200 V) | confirmed |
| 4 | ends with all four cells at 2.800–2.802 V | 2.800/2.800/2.802/2.801 V | confirmed |
| 5 | anchor 0 data start 2025-01-19 19:10:56, 3.4 d after the C/20 end, 0.5 h rest | 19:10:56; 3.393 d; rest 0.501 h, from the segment start, I = 0 | confirmed |
| 6 | start voltage 11.53–11.57 V, rising at +84–86 mV/h | 11.527 → 11.569 V; +85.0 mV/h (last 30 min), +85.2 mV/h (whole rest) | confirmed |
| 7 | CV phase ≈ 36 s (0.09–0.15 Ah) | 47 s / 0.106 Ah from pack ≥ 13.95 V; 37 s / 0.069 Ah from I < 20 A (package integration) | **corrected:** 37–47 s, 0.07–0.11 Ah depending on the CV start. Earlier rounds' 0.15–0.16 Ah used other integration conventions |
| 8 | 30 min after CV end pack 13.644 V, cell3 3.53 V (top spread 264 mV) | pack 13.644 V, cell3 3.530 V, spread **172 mV**; at the CV end the spread is 264 mV (cell3 3.680 V) | **corrected:** 264 mV is the CV-end spread |
| 9 | Q_fc,0 = 100.122 Ah (package integration) | 100.122386 Ah (`_first_full_charge`) | confirmed |
| 10 | 25 °C anchors 1–7 in segments 2, 4, 6, 8, 10, 12, 14 | type-A events E06, E08, E14, E20, E26, E33, E40 | confirmed |
| 11 | CV 1.17–1.44 Ah | 1.293–1.516 Ah (pack ≥ 13.95 V); 1.126–1.351 Ah (I < 20 A). It rises with age, from anchor 1 to anchor 7 | **corrected:** 1.29–1.52 / 1.13–1.35 Ah depending on the CV start |
| 12 | I_end 5.09–5.10 A | 5.094–5.100 A | confirmed |
| 13 | pack 30 min after CV end 13.435–13.439 V | 13.432–13.439 V (anchor 5: 13.432) | **corrected (minor):** 13.432–13.439 V |
| 14 | top spread 88 → 52 mV | at the CV end: 88, 75, 68, 64, 61, 55, 52 mV. 30 min later: 20 → 12 mV | confirmed at the CV end |
| 15 | start 11.80–11.95 V rising ≤ 6 mV/h | rest end 11.804–11.953 V; last-30-min slopes −0.2…+5.5 mV/h (the whole-rest slope of anchor 2 is +7.0) | confirmed (last 30 min) |
| 16 | bottom spread 22 → 35 mV | 22, 23, 25 (anchor 3), 24, 29, 31, 36 mV at the rest end | **corrected (minor):** 22 → 36 mV |
| 17 | anchor 3 (segment 6): 11.47 → 11.62 V, rising +52 mV/h | 11.474 → 11.624 V; +53.2 mV/h (last 30 min), +74.1 mV/h (whole 2 h rest); spread 36 → 25 mV | confirmed (+53 vs +52 depends on the fit) |
| 18 | Q_fc,1..7 = 97.00, 95.66, 94.64, 93.75, 93.08, 92.64, 91.95 Ah | 97.003, **95.670**, 94.642, 93.747, 93.082, 92.636, 91.954 Ah | **corrected:** Q_fc,2 = 95.67 Ah |
| 19 | (exposed, exploratory) anchor 3 needs ≈ 0.3–0.4 Ah more to reach pack 13.0/13.2 V and the charge-side step | — | **deferred to WP2 B2.** It needs a step location and a bottom offset, which WP0 forbids. The registered locators CL1–CL5 measure it as a_3^rel |
| 20 | (rebound) the first deep program after every anchor sits +0.39–0.46 Ah deeper on all 6 variants; gone by the next program | commit `8429b53` message: "0.39–0.46 Ah deeper on all six step-detection methods … gone by the next discharge". Package README: "0.4–0.46 Ah" | **cited.** The reference of that offset is not stored in the copied outputs, so it is not recomputed. WP2 carries it in h1 vs h2 |
| 21 | (rebound) rest voltage at the top 7–8 mV lower after the anchor | anchor minus the next top-up in the same 25 °C segment, 30 min after the CV end: −7.0 … −8.25 mV per cell (−28 … −33 mV pack), all 7 anchors | confirmed |
| 22 | (rebound) the next top-up needs ≈ +0.1 Ah | — | **deferred to WP3 E1.** It is an Ah balance; it equals Term3_k up to the loss rule |
| 23 | (V2) discharge-side step depth jumps ≈ +0.18 Ah at each 25 → 45 °C switch | V2 FINAL_REPORT §1: "+0.14 to +0.22 Ah", CK1 → CK2 month +0.60 | **cited** (consistent with ≈ +0.18). WP3 E2 measures it as J_j |
| 24 | month structure: CK → 25 °C (2–3 blocks) → idle switch → 45 °C (4 blocks) → CK | CV events per segment: 25 °C 2, 2, 2, 2, 3, 3, 2; 45 °C 4, 4, 4, 4, 4 (segment 1: 5 incl. anchor 0) | confirmed |
| 25 | block: 20.4 A CC to 14.0 V, CV to ≈ 5.1 A, 30 min rest, 30 min 20 A pulse, ≈ 55.9 Ah deep program (band −12.5…−8 A) | CC 20.400 A; CV-end pack 14.009–14.010 V, I_end 5.088–5.100 A; rest 30.0–30.02 min; pulse 30.0 min at −20.40 A (−10.20 Ah); maximum depth below the CV end 55.92 Ah (median; incl. the pulse, 45.72 Ah after it; minimum 53.42 Ah for E35, which is cut by the segment end); band samples cover a depth of 11.8–55.6 Ah. Blocks without a gap last 116.03–116.09 h | confirmed |
| 26 | five visible 25 → 45 °C switches, idle 21.2, 6.9, 9.7, 25.3, 12.1 h, counters identical | 21.23, 6.87, 9.71, 25.30, 12.08 h; Δ counters 0.000 / 0.000 for all five (table §2) | confirmed |
| 27 | month 1 has no 25 °C part; segment 3 missing | segment 1 (45 °C) is followed by CK1, then segment 2 (25 °C); no segment-3 file; the counters jump +1581.8 / +1491.8 Ah from segment 2 to segment 4 | confirmed |
| 28 | checkup windows CK1 3.2, CK3 3.1, CK4 3.7, CK5 5.4, CK6 6.0, CK7 4.3 d, CK2 unknown | 3.23, 3.11, 3.71, 5.35, 5.98, 4.28 d; CK2 unknown (≤ 3.68 d from the CK2 date to the segment 4 start) | confirmed |
| 29 | the counters book the 20 A pulse as charge | all 41 pulses: integrated −10.200…−10.205 Ah; Δ charge counter +10.143…+10.257 Ah; Δ discharge counter 0.000 | confirmed |
| 30 | integrate `current_A` with the package convention (dt > 600 s → 0) | `_integrated_ah` in `model_template.py` (MAX_DT_S = 600); used unchanged in `src/data12.py` | confirmed (code) |
| 31 | the per-block Ah balance between consecutive CV ends does not close (−0.3 to −1.1 Ah) | — | **deferred to WP3 E1** (it is an Ah balance) |
| 32 | `_charge_step_to_top` argmax on a 0.25 Ah grid; round 8 `bottom_to_step`/`step_to_top` quantised at 0.25 Ah | code: `grid = np.arange(0.0, qq.max(), 0.25)`, `argmax`. Round 8 per-cell Q_fc − step_to_top values are exact multiples of 0.25 Ah; anchor means are multiples of 0.0625 | confirmed |
| 33 | the discharge-side `dvdq` variant is on the same 0.25 Ah grid | `DVDQ_GRID_AH = (18.0, 46.0, 0.25)` | confirmed (code) |
| 34 | round 5B: absolute Q_C20 from literature OCPs is unidentifiable (8–10 Ah spans) | r5b FINAL_REPORT: "admitted parameter combinations already differ by 8.101–10.516 Ah" | confirmed (cited) |
| 35 | scope change: drift model → round 13 | `notes/DECISIONS.md` D1 | recorded |

## 2. Switch table (25 → 45 °C)

| Switch | Last 25 °C sample | First 45 °C sample | Idle h | Δ charge counter Ah | Δ discharge counter Ah | temp_mean before → after °C | I last / first A | pack V last → first |
|---|---|---|---|---|---|---|---|---|
| seg4 → seg5 | 2025-03-22 17:36:35 | 2025-03-23 14:50:25 | 21.23 | 0.000 | 0.000 | 25.73 → 45.73 | −5.10 / −5.80 | 13.260 → 13.333 |
| seg6 → seg7 | 2025-04-25 14:58:45 | 2025-04-25 21:51:05 | 6.87 | 0.000 | 0.000 | 25.68 → 45.29 | −5.39 / −4.78 | 13.261 → 13.335 |
| seg8 → seg9 | 2025-05-26 10:12:54 | 2025-05-26 19:55:29 | 9.71 | 0.000 | 0.000 | 25.71 → 45.50 | 1.68 / 1.45 | 12.940 → 12.959 |
| seg10 → seg11 | 2025-07-02 13:35:33 | 2025-07-03 14:53:28 | 25.30 | 0.000 | 0.000 | 25.53 → 45.57 | 8.45 / 8.81 | 13.317 → 13.229 |
| seg12 → seg13 | 2025-08-07 21:12:09 | 2025-08-08 09:17:02 | 12.08 | 0.000 | 0.000 | 25.10 → 45.45 | −7.39 / −6.95 | 13.045 → 13.174 |

- `elapsed_s` advances by exactly the idle time, so the clock runs on.
- The current is non-zero on both sides of every switch, at about the same value, and the counters do not move. The profile is paused in mid-step and resumes after the chamber has reached 45 °C.
- The pack voltage moves by −88 … +129 mV across the idle (descriptive only).

## 3. Checkup windows

| Checkup | Date | Last sample before | First sample of next segment | Window d | Δ charge / discharge counter Ah | temp_mean at start °C | pack V at start |
|---|---|---|---|---|---|---|---|
| CK0 | 2025-01-14 | 2025-01-16 09:44:56 (CK0 C/20 curve) | 2025-01-19 19:10:56 (seg1) | 3.39 | — | 47.01 | 11.527 |
| CK1 | 2025-02-08 | 2025-02-08 15:35:55 (seg1) | 2025-02-11 21:08:25 (seg2) | 3.23 | 0.000 / 0.000 | 25.50 | 11.799 |
| CK2 | 2025-03-11 | 2025-02-19 09:50:00 (seg2) | 2025-03-14 16:15:51 (seg4) | unknown (≤ 3.68) | 1581.840 / 1491.830 | 25.38 | 11.795 |
| CK3 | 2025-04-14 | 2025-04-13 15:21:55 (seg5) | 2025-04-16 18:07:22 (seg6) | 3.11 | 0.000 / 0.000 | 25.63 | 11.474 |
| CK4 | 2025-05-16 | 2025-05-15 21:30:54 (seg7) | 2025-05-19 14:28:34 (seg8) | 3.71 | 0.000 / 0.000 | 25.38 | 11.871 |
| CK5 | 2025-06-16 | 2025-06-16 12:23:32 (seg9) | 2025-06-21 20:52:28 (seg10) | 5.35 | 0.000 / 0.000 | 25.56 | 11.950 |
| CK6 | 2025-07-25 | 2025-07-22 16:32:49 (seg11) | 2025-07-28 16:07:28 (seg12) | 5.98 | 0.000 / 0.000 | 25.23 | 11.886 |
| CK7 | 2025-08-28 | 2025-08-28 13:46:50 (seg13) | 2025-09-01 20:34:43 (seg14) | 4.28 | 0.000 / 0.000 | 25.32 | 11.919 |

- The checkup throughput is not counted (counters flat), as `DATA_DESCRIPTION.md` states.
- CK2's window is unknown. Segment 3 is missing, and the counter jump includes its throughput.
- Segments 9 and 13 end later on the checkup date itself (12:23 and 13:46). The causal cut `until = CK date` (00:00) removes those last hours.

## 4. Integration check (anchors)

| k | Seg | Set °C | Q package (`_first_full_charge`) Ah | Q counter Ah | counter − package Ah | Δ discharge counter during charge Ah |
|---|---|---|---|---|---|---|
| 0 | 1 | 45 | 100.122 | 100.128 | +0.006 | 0.000 |
| 1 | 2 | 25 | 97.003 | 97.020 | +0.017 | 0.000 |
| 2 | 4 | 25 | 95.670 | 95.680 | +0.010 | 0.000 |
| 3 | 6 | 25 | 94.642 | 94.660 | +0.018 | 0.000 |
| 4 | 8 | 25 | 93.747 | 93.760 | +0.013 | 0.000 |
| 5 | 10 | 25 | 93.082 | 93.100 | +0.018 | 0.000 |
| 6 | 12 | 25 | 92.636 | 92.600 | −0.036 | 0.000 |
| 7 | 14 | 25 | 91.954 | 92.000 | +0.046 | 0.000 |

- **Counter vs package.** Q counter = Δ `charge_Ah_cum` over the charge. It agrees with the package integration within −0.036…+0.046 Ah, which is the counter's resolution: one 10-s step at 20.4 A is 0.057 Ah.
- **Pulse booking.** The pulse is booked in `charge_Ah_cum`: +10.14…+10.26 Ah for an integrated −10.20 Ah, with `discharge_Ah_cum` unchanged.
- **Booking by sign, per segment.** This is the same current in two accountings, not an Ah balance.
  - Δ charge counter = ∫(I > 0) + |∫pulse|, within −0.18…+0.17 Ah.
  - Δ discharge counter = |∫(I < 0, non-pulse)|, within −0.10…+0.002 Ah.
  - Segment throughput is 560–1660 Ah.
- Consequence: counter-based net charge (charge − discharge) is wrong by 2 × 10.2 Ah per pulse. WP3 therefore integrates `current_A`.

## 5. Recording gaps inside segments (dt > 60 s)

| Segment | Last sample before | First sample after | dt h | I before / after A | Δ charge / discharge counter Ah | Between events |
|---|---|---|---|---|---|---|
| 6 | 2025-04-18 18:27:58 | 2025-04-18 22:06:45 | 3.65 | 3.715 / 3.422 | 0.008 / 0.000 | E14 (anchor 3) → E15 |
| 6 | 2025-04-19 02:12:15 | 2025-04-19 18:50:44 | 16.64 | −0.007 / 18.361 | 0.051 / 0.000 | E14 (anchor 3) → E15 |
| 14 | 2025-09-04 22:21:44 | 2025-09-04 22:50:57 | 0.49 | 6.373 / 6.879 | 0.006 / 0.000 | E40 (anchor 7) → E41 |

- The counters do not bridge these gaps: they book ≤ 0.051 Ah over up to 16.6 h, even where the current on both sides is 3.4–3.7 A.
- The E14 → E15 block lasts 136.37 h instead of 116.06 h; the extra 20.3 h equals the two gaps. The profile therefore paused.
- WP3's pair rule excludes AT pairs with dt > 60 s, so anchors 3 and 7 have no admissible AT pair. WP3 applies that rule as registered.
- **Sampling.** Outside these gaps, dt ≤ 60 s everywhere. Duplicate timestamps (dt = 0) occur at every current change. The package convention gives them zero weight.

## 6. SUB and EPS_EXTRA (WP0.3)

| | CK1 | CK2 | CK3 | CK4 | CK5 | CK6 | CK7 |
|---|---|---|---|---|---|---|---|
| SUB SOH % | 95.984 | 94.507 | 93.600 | 92.821 | 92.015 | 91.426 | 90.765 |
| pp per Ah of EPS_EXTRA (unrounded) | 0 | 1.4465 | 0.9804 | 0.9804 | 0.9804 | 0.9804 | 0.9804 |

- EPS_EXTRA = 0.4 reproduces SUB exactly.
- CK1 does not move: it is built on CK0 = 100.41 Ah directly.
- CK3–CK7 move by 100/102 = 0.9804 pp/Ah. CK3's 0.9815 in the rounded CLI output is the 0.001 pp rounding.
- **Deviation: CK2 moves by 1.4465 pp/Ah.** CK2 uses the √t gap branch. Its loss slope a is fitted to loss_1 = 100.41 − (Q_fc,1 + ε), so EPS_EXTRA enters twice. dQ/dε = √(t_CK2/t_CK1) = √(49.252/22.626) = 1.4754 (45 °C-equivalent days), and 0.9804 × 1.4754 = 1.4465. This matches exactly.

---

<a id="zh"></a>

# WP0 事实清单

> [English](#en) · 中文

写于 2026-10-19。`EXECUTION_PROMPT.md` 第 2 节"已确立的事实"下的每一条，都已用本工作树的赛题数据重新核对。数字来自 `src/wp0_events.py`（`events.csv`）和 `src/wp0_facts.py`（`facts.json`、`switches.csv`、`checkup_windows.csv`、`integration_check.csv`、`pulses_programs.csv`、`counter_booking_by_segment.csv`、`in_segment_gaps.csv`）。

**WP0 规则。** WP0 不计算任何电量对账、台阶位置或与 ε 相关的估计。需要这些的条目标为**推迟**，并指向 WP2/WP3 中登记的测量。之前各轮已曝光的台阶相关条目只**引用**其出处，不重新计算。

## 摘要

- **已确认：** 23 条（#34 为引用确认）；#35（范围调整）已记录。
- **已更正：** 6 条，都是小的更正：264 mV 和 88 → 52 mV 是 CV 结束时的压差；Q_fc,2 = 95.67 Ah；CV 电量取决于 CV 起点的定义；30 min 后的电池组电压范围为 13.432–13.439 V；底部压差为 22 → 36 mV。
- **引用、未重算：** 2 条（首个程序偏移、25 → 45 °C 台阶跳变）。
- **推迟：** 3 条（锚点 3 多充的电量、下一次补电多充的 +0.1 Ah、逐块电量对账）。
- **对后续有影响的新事实：**
  - 第 6 段在锚点 3 的 CV 结束（E14）与下一次补电（E15）之间有两处记录间隙（3.65 h 和 16.64 h）。第 14 段在 E40（锚点 7）与 E41 之间有一处 29 min 的间隙。
  - 三处间隙前后计数器都几乎不变（最多 +0.051 Ah），说明工况程序暂停了；这几块因此比正常长 20.3 h。
  - WP3 的配对规则会排除这些配对。
  - 锚点 0 在 0.5 h 静置期间是在**降温**（47.01 → 46.54 °C），而不是升温。

## 1. 第 2 节逐条核对

| # | 事实（prompt） | 数据 | 结论 |
|---|---|---|---|
| 1 | CK0 C/20 曲线 2025-01-15 14:03:42 → 2025-01-16 09:44:56，5.10 A | 14:03:42 → 09:44:56，电流中位数 −5.100 A（均值 −5.1003），19.69 h | 已确认 |
| 2 | 带载起始 13.590 V | 13.590 V（电芯 3.374/3.351/3.511/3.359） | 已确认 |
| 3 | 放出 100.41 Ah | 11.201 V 时 100.410 Ah；最后一个样本（11.200 V）100.412 Ah | 已确认 |
| 4 | 结束时四个电芯 2.800–2.802 V | 2.800/2.800/2.802/2.801 V | 已确认 |
| 5 | 锚点 0 数据始于 2025-01-19 19:10:56，距 C/20 结束 3.4 天，静置 0.5 h | 19:10:56；3.393 天；静置 0.501 h，从段起点开始，I = 0 | 已确认 |
| 6 | 起始电压 11.53–11.57 V，以 +84–86 mV/h 上升 | 11.527 → 11.569 V；+85.0 mV/h（最后 30 min），+85.2 mV/h（整个静置） | 已确认 |
| 7 | CV 段约 36 s（0.09–0.15 Ah） | 以电池组 ≥ 13.95 V 为起点：47 s / 0.106 Ah；以 I < 20 A 为起点：37 s / 0.069 Ah（包内积分） | **更正：** 视 CV 起点定义为 37–47 s、0.07–0.11 Ah。之前各轮的 0.15–0.16 Ah 用的是其他积分约定 |
| 8 | CV 结束 30 min 后电池组 13.644 V，cell3 3.53 V（顶部压差 264 mV） | 电池组 13.644 V，cell3 3.530 V，压差 **172 mV**；CV 结束时压差为 264 mV（cell3 3.680 V） | **更正：** 264 mV 是 CV 结束时的压差 |
| 9 | Q_fc,0 = 100.122 Ah（包内积分） | 100.122386 Ah（`_first_full_charge`） | 已确认 |
| 10 | 25 °C 锚点 1–7 位于第 2、4、6、8、10、12、14 段 | A 类事件 E06、E08、E14、E20、E26、E33、E40 | 已确认 |
| 11 | CV 1.17–1.44 Ah | 1.293–1.516 Ah（电池组 ≥ 13.95 V）；1.126–1.351 Ah（I < 20 A）。从锚点 1 到锚点 7 随老化增大 | **更正：** 视 CV 起点为 1.29–1.52 / 1.13–1.35 Ah |
| 12 | I_end 5.09–5.10 A | 5.094–5.100 A | 已确认 |
| 13 | CV 结束 30 min 后电池组 13.435–13.439 V | 13.432–13.439 V（锚点 5：13.432） | **更正（小）：** 13.432–13.439 V |
| 14 | 顶部压差 88 → 52 mV | CV 结束时：88、75、68、64、61、55、52 mV；30 min 后：20 → 12 mV | 已确认（CV 结束时） |
| 15 | 起始 11.80–11.95 V，上升 ≤ 6 mV/h | 静置末 11.804–11.953 V；最后 30 min 斜率 −0.2…+5.5 mV/h（锚点 2 整个静置的斜率为 +7.0） | 已确认（最后 30 min） |
| 16 | 底部压差 22 → 35 mV | 静置末 22、23、25（锚点 3）、24、29、31、36 mV | **更正（小）：** 22 → 36 mV |
| 17 | 锚点 3（第 6 段）：11.47 → 11.62 V，以 +52 mV/h 上升 | 11.474 → 11.624 V；+53.2 mV/h（最后 30 min），+74.1 mV/h（整个 2 h 静置）；压差 36 → 25 mV | 已确认（+53 与 +52 的差别来自拟合方式） |
| 18 | Q_fc,1..7 = 97.00、95.66、94.64、93.75、93.08、92.64、91.95 Ah | 97.003、**95.670**、94.642、93.747、93.082、92.636、91.954 Ah | **更正：** Q_fc,2 = 95.67 Ah |
| 19 | （已曝光，探索性）锚点 3 要多充约 0.3–0.4 Ah 才到电池组 13.0/13.2 V 和充电侧台阶 | — | **推迟到 WP2 B2。** 这需要台阶位置和底部偏移，WP0 禁止计算；登记的定位器 CL1–CL5 会把它测为 a_3^rel |
| 20 | （回弹）每个锚点后的第一个深放电程序深 +0.39–0.46 Ah，6 种变体都如此，到下一个程序消失 | 提交 `8429b53` 的说明："六种台阶检测方法都深 0.39–0.46 Ah……到下一次放电消失"；包 README："0.4–0.46 Ah" | **引用。** 该偏移的参照没有存在复制的输出里，因此不重算；WP2 通过 h1 与 h2 的对比带入它 |
| 21 | （回弹）锚点之后顶部静置电压低 7–8 mV | 锚点减同一 25 °C 段内下一次补电，CV 结束 30 min 后：每个电芯 −7.0 … −8.25 mV（电池组 −28 … −33 mV），7 个锚点都如此 | 已确认 |
| 22 | （回弹）下一次补电要多充约 +0.1 Ah | — | **推迟到 WP3 E1。** 这是电量对账；在损耗规则之外它就等于 Term3_k |
| 23 | （V2）每次 25 → 45 °C 切换，放电侧台阶深度跳变约 +0.18 Ah | V2 FINAL_REPORT 第 1 节："+0.14 到 +0.22 Ah"，CK1 → CK2 那个月 +0.60 | **引用**（与约 +0.18 一致）。WP3 E2 会把它测为 J_j |
| 24 | 月度结构：CK → 25 °C（2–3 块）→ 换温箱停机 → 45 °C（4 块）→ CK | 每段 CV 事件数：25 °C 为 2、2、2、2、3、3、2；45 °C 为 4、4、4、4、4（第 1 段为 5，含锚点 0） | 已确认 |
| 25 | 每块：20.4 A 恒流到 14.0 V，恒压到约 5.1 A，30 min 静置，30 min 20 A 脉冲，约 55.9 Ah 深放电程序（电流带 −12.5…−8 A） | 恒流 20.400 A；CV 结束时电池组 14.009–14.010 V，I_end 5.088–5.100 A；静置 30.0–30.02 min；脉冲 30.0 min，−20.40 A（−10.20 Ah）；CV 结束以下最大深度中位数 55.92 Ah（含脉冲；脉冲之后 45.72 Ah；最小值 53.42 Ah 是被段末截断的 E35）；电流带样本覆盖深度 11.8–55.6 Ah。无间隙的块长 116.03–116.09 h | 已确认 |
| 26 | 五次可见的 25 → 45 °C 切换，停机 21.2、6.9、9.7、25.3、12.1 h，计数器不变 | 21.23、6.87、9.71、25.30、12.08 h；五次的计数器变化都是 0.000 / 0.000（见第 2 节表） | 已确认 |
| 27 | 第 1 个月没有 25 °C 部分；第 3 段缺失 | 第 1 段（45 °C）之后是 CK1，再是第 2 段（25 °C）；没有第 3 段文件；计数器从第 2 段到第 4 段跳变 +1581.8 / +1491.8 Ah | 已确认 |
| 28 | 检查窗口 CK1 3.2、CK3 3.1、CK4 3.7、CK5 5.4、CK6 6.0、CK7 4.3 天，CK2 未知 | 3.23、3.11、3.71、5.35、5.98、4.28 天；CK2 未知（从 CK2 日期到第 4 段开始 ≤ 3.68 天） | 已确认 |
| 29 | 计数器把 20 A 脉冲记作充电 | 全部 41 次脉冲：积分 −10.200…−10.205 Ah；充电计数器 +10.143…+10.257 Ah；放电计数器 0.000 | 已确认 |
| 30 | 按包内约定对 `current_A` 积分（dt > 600 s → 0） | `model_template.py` 的 `_integrated_ah`（MAX_DT_S = 600），在 `src/data12.py` 中原样使用 | 已确认（代码） |
| 31 | 相邻 CV 结束之间的逐块电量对账不闭合（−0.3 到 −1.1 Ah） | — | **推迟到 WP3 E1**（这是电量对账） |
| 32 | `_charge_step_to_top` 在 0.25 Ah 网格上取 argmax；第 8 轮 `bottom_to_step`/`step_to_top` 量化在 0.25 Ah | 代码：`grid = np.arange(0.0, qq.max(), 0.25)`，`argmax`。第 8 轮各电芯的 Q_fc − step_to_top 恰为 0.25 Ah 的整数倍；锚点均值是 0.0625 的整数倍 | 已确认 |
| 33 | 放电侧 `dvdq` 变体也在 0.25 Ah 网格上 | `DVDQ_GRID_AH = (18.0, 46.0, 0.25)` | 已确认（代码） |
| 34 | 第 5B 轮：用文献 OCP 重建绝对 Q_C20 无法识别（范围 8–10 Ah） | r5b FINAL_REPORT："被接受的参数组合之间已相差 8.101–10.516 Ah" | 已确认（引用） |
| 35 | 范围调整：漂移模型 → 第 13 轮 | `notes/DECISIONS.md` D1 | 已记录 |

## 2. 切换表（25 → 45 °C）

表格同英文部分第 2 节。

- `elapsed_s` 恰好前进停机时长，即时钟继续走。
- 每次切换两侧电流都不为零且大致相同，计数器不动。工况程序是在某一步中间暂停的，等温箱到 45 °C 后再继续。
- 停机前后电池组电压变化 −88 … +129 mV（仅作描述）。

## 3. 检查窗口

表格同英文部分第 3 节。

- 检查期间的电量不计入计数器（计数器不变），与 `DATA_DESCRIPTION.md` 一致。
- CK2 的窗口未知：第 3 段缺失，计数器的跳变包含了第 3 段的电量。
- 第 9 段和第 13 段在检查日期当天较晚时才结束（12:23 和 13:46）；因果截断 `until = CK 日期`（00:00）会去掉这最后几个小时。

## 4. 积分核对（锚点）

表格同英文部分第 4 节。

- **计数器与包内积分。** 基于计数器的 Q（充电期间 `charge_Ah_cum` 的变化）与包内积分相差 −0.036…+0.046 Ah，即计数器的分辨率：20.4 A 下一个 10 s 步长为 0.057 Ah。
- **脉冲的记账。** 脉冲记入 `charge_Ah_cum`：积分为 −10.20 Ah，计数器记 +10.14…+10.26 Ah，`discharge_Ah_cum` 不变。
- **按符号逐段记账。** 这是同一电流的两种记账方式，不是电量对账。
  - 充电计数器变化 = ∫(I > 0) + |∫脉冲|，误差在 −0.18…+0.17 Ah 以内。
  - 放电计数器变化 = |∫(I < 0，非脉冲)|，误差在 −0.10…+0.002 Ah 以内。
  - 各段电量为 560–1660 Ah。
- 后果：用计数器算的净电量（充电 − 放电）每次脉冲会错 2 × 10.2 Ah，所以 WP3 对 `current_A` 积分。

## 5. 段内记录间隙（dt > 60 s）

表格同英文部分第 5 节。

- 计数器没有跨过这些间隙：即使两侧电流为 3.4–3.7 A，在最长 16.6 h 的间隙里也只记了 ≤ 0.051 Ah。
- E14 → E15 这一块长 136.37 h，而正常为 116.06 h；多出的 20.3 h 正好等于两个间隙之和。可见工况程序暂停了。
- WP3 的配对规则排除带 dt > 60 s 的 AT 配对，因此锚点 3 和 7 没有可用的 AT 配对。WP3 按登记的规则执行。
- **采样。** 除这些间隙外，dt 处处 ≤ 60 s。每次电流变化时都有重复时间戳（dt = 0），按包内约定其权重为零。

## 6. SUB 与 EPS_EXTRA（WP0.3）

表格同英文部分第 6 节。

- EPS_EXTRA = 0.4 时与 SUB 完全一致。
- CK1 不动：它直接以 CK0 = 100.41 Ah 为基础。
- CK3–CK7 每 Ah 移动 100/102 = 0.9804 pp。CLI 取整后的输出里 CK3 为 0.9815，这是 0.001 pp 取整造成的。
- **偏差：CK2 每 Ah 移动 1.4465 pp。** CK2 走 √t 间隙分支，其损失斜率 a 是用 loss_1 = 100.41 − (Q_fc,1 + ε) 拟合的，所以 EPS_EXTRA 进入了两次。dQ/dε = √(t_CK2/t_CK1) = √(49.252/22.626) = 1.4754（45 °C 等效天数），0.9804 × 1.4754 = 1.4465，完全吻合。
