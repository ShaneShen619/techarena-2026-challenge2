<a id="en"></a>

# WP4 — cap and fallback record

> **Language:** English · [中文](#zh)

**State: capped** under the prompt's cap rule (§5: "At a cap, write up what exists (including 'inconclusive'), commit, push and mark the WP capped"). The WP4 cap is 3 h. WP4 started with protocol commit `b3108bd` (2026-10-16 ≈ 00:25 CEST), and the cap passed at ≈ 03:25 while the Yagci download was still pending.

**Registered clauses applied (all in [protocol.json](protocol.json), committed before any download or fit):**

1. `download.decision`: "… time cap 45 min … on any failure skip Yagci and record it".
   - Attempt 1: curl exit 35 (SSL).
   - Attempt 2: reached 0.82 GB, then a retry truncated the file to 0 bytes and the process stalled.
   - A manual download did not arrive within 7.5 h.
   - Recorded in [D4.1–D4.3](../notes/DECISIONS.md).
2. `fits.fallback`: "if Yagci is unavailable, A_b, tau_b and A_cal come from prior2 and only A_cyc is refitted on LIC/Gotion". Applied by `fit_prior3.py` (run without a Yagci table).
3. `fits.fallback`: "a term whose jackknife SD > ln 3 or that hits a bound falls back to the 5C prior2 value". The A_cyc estimate hit its 1e-12 floor on both cycling datasets, so A_cyc fell back to prior2. The script did not encode this rule for A_cyc, so it was applied explicitly and recorded in `prior3.json` (D4.3). This is the registered rule, executed by hand, not a new rule.

**What exists (written up, committed, pushed):**

- the qualification audit;
- the cycling axes;
- the prior2 check on open data (prior2 over-predicts LIC by +50 % and Gotion by +24 %);
- `prior3.json` (= prior2);
- the evaluation of S_A3 / F2_S_A3 / F1_S_A3 on pseudo + cold-start, then real (identical to WP2; no candidate);
- [REPORT.md](REPORT.md).

**Not done because of the cap:** the Yagci storage-cell fit of the calendar and break-in terms, and its evaluation. It is inconclusive, not negative. If the data become available, it can be run later under the same protocol as a supplement, without changing any registered main.

---

<a id="zh"></a>

# WP4——上限与回退记录

> **语言：** [English](#en) · 中文

**状态：到达上限**，按 prompt 的上限规则处理（第 5 节："到上限时，把已有结果（包括'无定论'）写成报告、提交、推送，并把该工作包标为到达上限"）。WP4 的上限为 3 小时。WP4 从协议提交 `b3108bd`（2026-10-16 约 00:25 CEST）开始，约 03:25 到达上限，而当时 Yagci 下载仍未完成。

**所适用的登记条款（全部在 [protocol.json](protocol.json) 中，于任何下载或拟合之前提交）：**

1. `download.decision`："……时间上限 45 分钟……任何失败都跳过 Yagci 并记录"。
   - 第 1 次：curl 错误码 35（SSL）。
   - 第 2 次：下载到 0.82 GB 后，一次重试把文件截成 0 字节，进程停滞。
   - 手动下载在 7.5 小时内没有到位。
   - 记录在 [D4.1–D4.3](../notes/DECISIONS.md)。
2. `fits.fallback`："如果拿不到 Yagci，A_b、tau_b 和 A_cal 取自 prior2，只在 LIC/Gotion 上重新拟合 A_cyc"。由 `fit_prior3.py` 执行（运行时不带 Yagci 表）。
3. `fits.fallback`："jackknife SD > ln 3 或撞到边界的项回退到 5C 的 prior2 值"。A_cyc 的估计在两个循环数据集上都撞到 1e-12 的下限，因此回退到 prior2。脚本没有为 A_cyc 编写这条规则，所以是显式执行的，并记录在 `prior3.json` 中（D4.3）。这是登记过的规则，只是由人工执行，不是新规则。

**已有结果（已写成报告、提交、推送）：**

- 资格审计；
- 循环数据时间轴；
- 用开放数据检查 prior2（prior2 高估 LIC +50 %、Gotion +24 %）；
- `prior3.json`（= prior2）；
- S_A3 / F2_S_A3 / F1_S_A3 先在伪场景 + 冷启动上、再在真实场景上的评估（与 WP2 相同；无候选）；
- [REPORT.md](REPORT.md)。

**因上限未完成的部分：** 用 Yagci 存储电芯拟合日历项和磨合项，以及相应的评估。结论是无定论，而不是否定。如果数据到位，可以之后在同一份协议下作为补充运行，不改变任何登记的主配置。
