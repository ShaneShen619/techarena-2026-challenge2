<a id="en"></a>

# DECISIONS (round 5A)

> **Language:** English · [中文](#zh)

- D0.1 The run is driven from a session whose primary directory is `/Users/shane/Desktop/Arena_1013_model`; every command uses absolute paths or `git -C` into this worktree only. No file outside this worktree is written.
- D0.2 Harness cache stays in this worktree's git-ignored `research/phase2_round3_models_20261014/cache/`; own caches in the study's `cache/`.

- D1.1 Throughput = d(charge_Ah_cum) + d(discharge_Ah_cum); verified against the integral of |I| (< 0.01 % per segment).
- D1.2 The public schedule (data description: segment 3 is 45 C, 19 Feb - 11 Mar; every month ends with a 45 C segment) is used for hidden operating time. Its end is estimated as CK date + median visible end offset (0 h if none).
- D1.3 The hidden tail is split at the estimated month end: 45 C operation before it, checkup (25 C, 0 Ah) after it. This refines the prompt's single-rule wording so that checkup intervals follow the prompt's checkup rule.
- D1.4 Next-checkup index uses ck < t_last (a cut row exactly at 00:00 of a CK date belongs to the month ending at that CK).

- D2.1 The Challenge 1 joint fit puts z at its registered lower bound 0.2. The registered prior rule is applied unchanged (z ~ N(0.20, 0.253^2)); the bound hit is flagged in the stage 2 report.
- D2.2 Ea and both log A fall back to Yagci 2025 per the registered rules (Challenge 1 is not identifiable for them).
- D2.3 Stage 3 adds one report-only variant, z = 0.5, motivated by the stage 2 idle-gap diagnostic. It is registered before any stage 3 evaluation, is not part of G-robust and is never promoted.

---

<a id="zh"></a>

# 决策记录（第五轮 A）

> **语言：** [English](#en) · 中文

- D0.1 本次运行由主目录为 `/Users/shane/Desktop/Arena_1013_model` 的会话驱动；所有命令都用绝对路径或 `git -C` 指向本 worktree，不在本 worktree 之外写任何文件。
- D0.2 harness 缓存留在本 worktree 中被忽略的 `research/phase2_round3_models_20261014/cache/`；自己的缓存放在研究目录的 `cache/`。
- D1.1 吞吐 = d(charge_Ah_cum) + d(discharge_Ah_cum)；已与 |I| 的积分核对（每段相差 < 0.01 %）。
- D1.2 隐藏的运行时间使用公开日程（数据说明：第 3 段为 45 C，2 月 19 日至 3 月 11 日；每月以 45 C 段结束）。其结束时间估计为 CK 日期 + 可见段末偏差的中位数（没有则为 0 h）。
- D1.3 隐藏尾段在估计的月末处分开：之前为 45 C 运行，之后为检查（25 C，0 Ah）。这是对 prompt 单一规则措辞的细化，使检查区间遵循 prompt 的检查规则。
- D1.4 "下一个检查"的索引用 ck < t_last（恰好在 CK 日 00:00 的截断行属于在该 CK 结束的月份）。
- D2.1 Challenge 1 联合拟合把 z 推到登记的下界 0.2。按登记的先验规则原样使用（z ~ N(0.20, 0.253^2)）；撞界在第 2 阶段报告中标注。
- D2.2 按登记的规则，Ea 和两个 log A 都回退到 Yagci 2025（Challenge 1 对它们不可辨识）。
- D2.3 第 3 阶段增加一个仅报告的变体 z = 0.5，依据是第 2 阶段的空档诊断。它在第 3 阶段任何评估之前登记，不计入 G-robust，绝不升为主配置。
