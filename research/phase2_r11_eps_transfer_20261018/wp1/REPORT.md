<a id="en"></a>

# WP1 — Protocol audit and registration

> English · [中文](#zh)

**Conclusions first.**

- **Registration.** [protocol.json](protocol.json) was committed in `d183743`, before any ε value of this round was computed; its SHA256 is in `protocol.sha256`. It fixes:
  - the decomposition ε_total = T_CE + T_path for each dataset;
  - the statistics: Theil–Sen and OLS slopes, leave-one-RPT-out ranges, BIC (a) / (b) / (c), and the outlier rule;
  - the pack driver definitions for WP4;
  - the transfer rules (§4 of the prompt, verbatim plus an operational form) and the decision rule.
- **Identifiability:**

| Dataset | T_CE | T_path | ε_total | Registered event |
|---|---|---|---|---|
| LIC | ✓ (k = 0..14) | ✓ (k = 0..13) | ✓ | between k = 4 and 5 |
| Yagci 35/50 °C | ✓ | ✓ | ✓ | none |
| Gotion cell | ✗ | ✗ | ✓ | none |

- **Key audit findings** (details in [AUDIT.md](AUDIT.md)):
  - LIC's "truncated RPT" is an extra test that follows an **unrecorded charge**. It coincides with an RPT temperature step from 29.7 to 35.1 °C.
  - A second unrecorded jump precedes RPT 10.
  - Both are registered as audit flags.
  - These flags are not blind: the ε totals were already visible in the prompt (see `note_on_blindness`). Flagged points therefore stay in the main estimate.
- **What the LIC operating charge differs in.** Both LIC charges end with CV to 0.05C and start from a 0.1C-empty state, so T_path there measures rate (1C vs 0.1C), rest length (0.25 h vs 0.98 h) and self-heating (+7 to +8 °C). In Yagci, T_path measures temperature (about 22 °C vs 35/50 °C) at the same current.

---

<a id="zh"></a>

# WP1 — 协议审查与登记

> [English](#en) · 中文

**结论先读。**

- **登记。** [protocol.json](protocol.json) 于 `d183743` 提交，早于本轮任何 ε 值的计算；SHA256 见 `protocol.sha256`。它固定了：
  - 各数据集的分解 ε_total = T_CE + T_path；
  - 统计方法：Theil–Sen 和 OLS 斜率、逐一剔除 RPT 的范围、BIC (a)/(b)/(c)、离群点规则；
  - WP4 的电池组驱动量定义；
  - 迁移规则（prompt §4 原文加上可操作的形式）和决策规则。
- **可识别性：** LIC 三项都可识别（T_CE 为 k = 0..14，T_path 为 k = 0..13），登记事件在 k = 4 与 5 之间；Yagci 三项都可识别，无登记事件；国轩只有 ε_total。
- **主要审查发现**（详见 [AUDIT.md](AUDIT.md)）：
  - LIC 的"截断 RPT"是一次**未记录充电**之后的额外测试，并且与 RPT 温度从 29.7 °C 升到 35.1 °C 同时发生。
  - RPT 10 之前还有第二次未记录的跳变。
  - 两者都登记为审查标记。
  - 这些标记不是盲的：ε 总量在 prompt 中已经可见（见 `note_on_blindness`），所以被标记的点保留在主估计中。
- **LIC 运行充电的差异在哪里。** LIC 的两次充电都以恒压到 0.05C 结束，并且都从 0.1C 放空状态开始，所以 T_path 衡量的是倍率（1C 对 0.1C）、静置时长（0.25 h 对 0.98 h）和自热（+7 到 +8 °C）。Yagci 的 T_path 衡量的是同一电流下的温度差（约 22 °C 对 35/50 °C）。
