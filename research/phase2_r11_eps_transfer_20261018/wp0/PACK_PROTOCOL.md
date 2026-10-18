<a id="en"></a>

# WP0 — Protocol fact sheet of the Challenge 2 pack

> English · [中文](#zh)

| Variable | Value | Source |
|---|---|---|
| Object | 4 × 102 Ah LFP prismatic cells in series (pack, not single cell) | CHALLENGE2_DESCRIPTION.pdf §2.2 |
| Reference (truth) test | C/20 = 5.1 A discharge to pack 11.2 V "after a full charge"; full-charge protocol (CV voltage, cutoff) not stated | PDF §2.2 protocol line; DATA_DESCRIPTION.md |
| Reference temperature | not stated; assumed 25 °C | assumption (round 5B used the same) |
| CK0 curve | starts at 13.590 V under −5.1 A load, ends at 11.200 V with cells 2.800–2.802 V; 100.41 Ah | data/checkups/CK0_reference_discharge.csv.gz |
| Operating ("anchor") charge | first charge after each checkup: 20.4 A (0.2C) CC to 14.0 V, CV until 5.1 A (0.05C) | prompt §2; measured again in WP4 |
| Anchor temperature | chamber 25 °C for anchors 1–7 (cell 26.9–27.2 °C at charge end); anchor 0 (seg1) at 45 °C | prompt §2; WP4 |
| Start state | relaxed 11.80–11.95 V after ~2 h rest, except seg1 (0.5 h rest, 45 °C, rising +86 mV/h) and seg6 (11.47 → 11.62 V, unrelaxed) | prompt §2; round 6 wp3a (sources/r6_wp3_wp3a_start_state.csv) |
| State between checkup end and anchor | unknown (checkup sequence after the C/20 discharge is not published) | PDF |
| Pack entering checkup | charged, 13.1–13.3 V | round 7 WP1 (prompt §2) |
| Operating CE | not measurable (per-block balance −0.3 to −1.1 Ah) | prompt §2 |
| Fade CK0→CK7 (proxy) | ≈ 8.2 Ah | Q_fc series, prompt §2 |

**Differences from the open datasets that matter for transfer:** charge rate 0.2C (LIC 1C); reference rate C/20 (LIC 0.1C); CV cutoff 0.05C (LIC 0.05C, same); pack-voltage limits on both ends (single-cell limits in LIC/Yagci/Gotion cell); reference temperature unknown.

---

<a id="zh"></a>

# WP0 — 本题电池组的协议变量

> [English](#en) · 中文

| 变量 | 值 | 来源 |
|---|---|---|
| 对象 | 4 只 102 Ah LFP 方壳电芯串联（电池组，不是单芯） | 赛题 PDF §2.2 |
| 参考（真值）测试 | "满充后"以 C/20 = 5.1 A 放电到电池组 11.2 V；满充协议（CV 电压、截止电流）未说明 | PDF §2.2；DATA_DESCRIPTION.md |
| 参考温度 | 未说明；假设 25 °C | 假设（第 5B 轮同样假设） |
| CK0 曲线 | 在 −5.1 A 负载下从 13.590 V 开始，结束于 11.200 V，各电芯 2.800–2.802 V；100.41 Ah | CK0_reference_discharge.csv.gz |
| 运行（锚点）充电 | 每次检查后的第一次充电：20.4 A（0.2C）恒流到 14.0 V，恒压到 5.1 A（0.05C） | prompt §2；WP4 复测 |
| 锚点温度 | 锚点 1–7 在 25 °C 箱温（充电结束时电芯 26.9–27.2 °C）；锚点 0（seg1）在 45 °C | prompt §2；WP4 |
| 起点状态 | 约 2 h 静置后弛豫到 11.80–11.95 V；例外为 seg1（静置 0.5 h、45 °C、以 +86 mV/h 上升）和 seg6（11.47 → 11.62 V，未弛豫） | prompt §2；第 6 轮 wp3a |
| 检查结束到锚点之间的状态 | 未知（C/20 放电之后的检查流程未公布） | PDF |
| 进入检查时 | 充电态，13.1–13.3 V | 第 7 轮 WP1 |
| 运行库伦效率 | 无法测量（每块收支 −0.3 到 −1.1 Ah） | prompt §2 |
| CK0→CK7 衰减（代理） | 约 8.2 Ah | Q_fc 序列 |

**与公开数据集之间影响迁移的差异：** 充电倍率 0.2C（LIC 1C）；参考倍率 C/20（LIC 0.1C）；CV 截止 0.05C（LIC 同为 0.05C）；两端都是电池组电压限制（LIC/Yagci/国轩单芯为单芯电压限制）；参考温度未知。
