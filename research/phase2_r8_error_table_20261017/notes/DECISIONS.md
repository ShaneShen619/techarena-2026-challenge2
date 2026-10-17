<a id="en"></a>

# DECISIONS (round 8)

> **Language:** English · [中文](#zh)

- **D0.1 (WP0, cache location).** The round 3 harness writes its pickle cache next to its own study. To avoid writing into an earlier study directory, `harness.py` is copied into `src/` unchanged except for a docstring line, so the cache lives in this study's git-ignored `cache/`. Events and V2 are still imported from their original directories in this worktree.
- **D0.2 (WP0, scenario set).** "Every scenario" is the round 7 WP0 set: real, PG1, PG2, PC5 and PC10 (k = 3..7, as in the pseudo metric), CS, CSE, plus PC5_all and PC10_all (k = 2..7). That gives 47 cases per Δ, the "about 48 causal cases" of the prompt. Pseudo = mean MAE over PG1, PG2, PC5, PC10; cold start = mean over CS, CSE (Δ = 0.4), as in round 7.
- **D1.1 (WP1, first-program flag).** `uses_first_post_anchor_program` is true for fallback cases whose increment `after[-1] − after[0]` uses at least two programs. With a single program after the anchor the increment is identically 0 and does not depend on that program. The phase branch never uses the first program (E is the last 45 °C step of a month with n ≥ 3 in all real cases); its event use is recorded in the `ev_*` columns.
- **D1.2 (WP1, context definitions).** Throughput = integrated discharge Ah (negative `current_A`, Δt > 600 s ignored as in events.py) in the scenario cut after the anchor CV end. `share_45C_assigned` uses the registered T_main hourly temperature (visible segment → set point, segment-3 interval → 45 °C, other gaps → 25 °C, after the last sample → 45 °C). `share_45C_visible` counts only visible 45 °C samples. Both run from the anchor to CK_k.
- **D3.1 (WP3, common cut-off).** I_cut = the largest anchor end current = 5.10 A. Every anchor charge ends at the first 10 s sample whose current is at or below about 5.1 A, so the prompt's "until the current first falls below I_cut" is implemented as the first CV sample with current ≤ I_cut (inclusive). This gives Q_fc(cut) = Q_fc for all anchors. The 6.0 A column is the informative common cut-off and is used by H9. A strict "< I_cut" would never trigger for anchor 2 (end 5.100 A).
- **D2.1 (WP2, switch timing).** days_since_switch is measured from the start of the event's visible segment. 45 °C segments follow a 25 °C segment directly (gap 0.3–1.1 days, including segment 11 at 1.05 days) and are labelled direct_switch. 25 °C segments follow a checkup gap of more than 2 days whose chamber temperature is not observed (after_checkup_gap). Segment 1 is campaign_start. The CK date cannot be used to detect gaps, because several segments end after their checkup date (the date is midnight).
- **D2.2 (WP2, exposure).** During table QA (before WP5's registration), the pack-level R_anc and R_seg per event and the per-unit summary (mean/quantiles) of R_cell were printed. So the R_anc month trend (expected from b ≈ 0.75 < 1) and the per-cell sign pattern of R_cell (cell1 negative, cells 2–3 positive) were seen before registration. H4 (event part) and H6 (per-cell sign part) are labelled 'residual seen before registration'. Their verdicts are still computed by the registered rules. Nothing was grouped by any other slice variable.
- **D4.1 (WP4, cycle definition).** The profile has no daily cycle. A cycle is one SOC swing between consecutive SOC tops (local maxima of segment-integrated Ah with prominence ≥ 10 Ah), inside one segment. `slot` is the swing's order inside its program block (between consecutive deep-program CV ends). The prompt's R_cyc (leave-one-out median of the centred 7-cycle window, same set point) is kept as written. Because the profile repeats exactly per block, a phase-matched variant R_cyc_slot (same slot, ±3 blocks, same set point, leave-one-out median, ≥ 3 others) is added.
- **D4.2 (WP4 → WP5, H10).** Top-of-charge Ah relative to the last CV end is fixed by the current-controlled script (slot-matched spread about 0.001 Ah), and no top reaches CV except the program-opening charge. H10 is therefore registered on R_cyc_slot of top-of-charge Ah, expecting 'not systematic' by construction. A registered secondary H10b on R_cyc_slot of V_bottom_pack (the loaded voltage at the swing bottom) is added as the state-bearing quantity.

---

<a id="zh"></a>

# 决策记录（第 8 轮）

> **语言：** [English](#en) · 中文

- **D0.1（WP0，缓存位置）。** 第 3 轮 harness 把 pickle 缓存写在它自己的研究目录旁。为了不写入较早的研究目录，把 `harness.py` 原样复制到 `src/`（只改一行文档字符串），缓存因此位于本研究被 git 忽略的 `cache/`。events 和 V2 仍从本 worktree 中原目录导入。
- **D0.2（WP0，场景集合）。** "所有场景"取第 7 轮 WP0 的集合：real、PG1、PG2、PC5 和 PC10（k = 3..7，与伪场景指标一致）、CS、CSE，加上 PC5_all 和 PC10_all（k = 2..7）。每个 Δ 共 47 个案例，即 prompt 中的"约 48 个因果案例"。伪场景 = PG1、PG2、PC5、PC10 的 MAE 均值；冷启动 = CS、CSE 的均值（Δ = 0.4），与第 7 轮相同。
- **D1.1（WP1，首个程序标志）。** 当 fallback 的增量 `after[-1] − after[0]` 用到至少两个程序时，`uses_first_post_anchor_program` 为真。锚点后只有一个程序时增量恒为 0，与该程序无关。phase 分支从不使用首个程序（在所有真实案例中 E 都是 n ≥ 3 的月份里最后一个 45 °C 台阶）；它用到的事件记录在 `ev_*` 列中。
- **D1.2（WP1，上下文定义）。** 吞吐量 = 场景截断数据中锚点 CV 结束之后积分得到的放电 Ah（负的 `current_A`，与 events.py 一样忽略 Δt > 600 s）。`share_45C_assigned` 使用登记的 T_main 逐小时温度（可见段 → 设定点，第 3 段区间 → 45 °C，其他空档 → 25 °C，最后一个样本之后 → 45 °C）；`share_45C_visible` 只计可见的 45 °C 样本。两者都从锚点算到 CK_k。
- **D3.1（WP3，公共截止）。** I_cut = 锚点终止电流的最大值 = 5.10 A。每次锚点充电都在第一个电流约 ≤ 5.1 A 的 10 s 采样点结束，所以 prompt 中的"直到电流首次低于 I_cut"实现为第一个电流 ≤ I_cut（含等号）的 CV 采样点。这样所有锚点都有 Q_fc(截止) = Q_fc。6.0 A 列才是有信息量的公共截止，H9 使用该列。若用严格的"< I_cut"，锚点 2（终止 5.100 A）永远不会触发。
- **D2.1（WP2，切换时间）。** days_since_switch 从事件所在可见段的起点算起。45 °C 段紧接在 25 °C 段之后（间隔 0.3–1.1 天，包括间隔 1.05 天的第 11 段），标为 direct_switch。25 °C 段之前是超过 2 天、箱温未观测的检查空档（after_checkup_gap）。第 1 段为 campaign_start。检查日期不能用来识别空档，因为有几段结束于其检查日期之后（日期为午夜）。
- **D2.2（WP2，曝光）。** 表格质检时（WP5 登记之前）打印过每个事件的 pack 级 R_anc 和 R_seg，以及 R_cell 按单元的汇总（均值/分位数）。因此 R_anc 的逐月趋势（由 b ≈ 0.75 < 1 可预期）和 R_cell 的单体符号模式（cell1 为负，cell2–3 为正）在登记前已被看到。H4（事件部分）和 H6（单体符号部分）标为"残差在登记前已见"，结论仍按登记规则计算。没有按任何其他切片变量分组。
- **D4.1（WP4，循环定义）。** 工况没有日循环。一个循环是同一段内相邻两个 SOC 顶点（段内积分 Ah 的局部极大值，显著性 ≥ 10 Ah）之间的一次 SOC 摆动。`slot` 是该摆动在所属程序周期（相邻两次深放程序的 CV 结束之间）中的序号。prompt 的 R_cyc（同设定点、居中 7 个循环窗口的留一中位数）按原文保留。由于工况在每个周期中完全重复，另加相位匹配版本 R_cyc_slot（同槽位、前后各 3 个周期、同设定点、留一中位数、至少 3 个其他值）。
- **D4.2（WP4 → WP5，H10）。** 相对上一次 CV 结束的充电顶点 Ah 由电流控制脚本固定（同槽位离散约 0.001 Ah），且除开启程序的充电外没有顶点到达 CV。因此 H10 登记在充电顶点 Ah 的 R_cyc_slot 上，按构造预期为"非系统性"。另登记次要假设 H10b，作用于 V_bottom_pack（摆动底部的带载电压）的 R_cyc_slot，作为携带状态的量。
