<a id="en"></a>

# DECISIONS (round 6)

> **Language:** English · [中文](#zh)

- D0.1 The run is driven from a session whose primary directory is `/Users/shane/Desktop/Arena_1013_model`. That checkout is touched only through read-only `git show` / `git archive` of commit 21a7a55; all writes go to this worktree.
- D0.2 Round 5C's `src/` is copied into this study (`src/`). Two edits only: the worktree assertion in `common6.py`, and the prior path in `smodel5c.py` (→ `sources/prior2_5c.json`).
- D0.3 SUB tolerance: research reproduction within 5e-4 pp of the rounded reference table; the archived submitted class within 0.001 pp of SUB at delta 0.4 (observed 0.00037).

- D1.1 WP1 tie window. The registered 0.01 tie window (normalised units) is wide relative to the spread of causal-grid regrets (0.009-0.034); seven models tie there and the tie-break expectation differs by < 0.001. Applied as registered; the report states that, read literally, the causal grid favours the stress ensembles. Not changed after the fact.
- D1.2 WP1 evaluates every model in its submitted configuration (eps0 + 0.4); EX on pseudo/CS uses the scenario's operation data wrapped in a framework Dataset.

- D2.1 WP2 main F2_S_A failed on the real run; per protocol no candidate class is produced. F1 variants are reported only. The exposed-CK1 F1_S_B/S_C would in any case not be selectable (rule 3).

- D3.1 WP3 amendment 1 (3a reference anchor 1) was registered after the audits and before any evaluation, because anchor 0's 0.5 h / 45 C rest is not comparable with the 2 h / 25 C rests of anchors 1-7. The registered main (reference anchor 0) is still reported.
- D3.2 The WP1 grid has no start-state axis, so 3a cannot win there by construction; it is reported as a leaderboard question only.

- D5.1 The user started WP5 while WP4 was still running (the Yagci download had not finished). WP5 depends only on WP0, so it was completed; its drafts mark WP4 as "in progress". WP4 is resumed separately.

---

<a id="zh"></a>

# 决策记录（第六轮）

> **语言：** [English](#en) · 中文

- D0.1 本次运行由主目录为 `/Users/shane/Desktop/Arena_1013_model` 的会话驱动。对那个检出目录只通过只读的 `git show` / `git archive`（提交 21a7a55）访问；所有写入都在本 worktree 中。
- D0.2 第五轮 C 的 `src/` 复制到本研究（`src/`）。只改了两处：`common6.py` 中的 worktree 断言，以及 `smodel5c.py` 中的先验路径（→ `sources/prior2_5c.json`）。
- D0.3 SUB 的容差：研究复现与四舍五入后的参照表相差不超过 5e-4 pp；归档的提交类在 delta 0.4 时与 SUB 相差不超过 0.001 pp（实测 0.00037）。
- D1.1 WP1 的并列阈值。登记的 0.01 并列阈值（归一化单位）相对于因果网格后悔值的分布（0.009–0.034）太宽；在那里七个模型并列，决胜所用的期望值相差不到 0.001。按登记执行；报告中说明，如果直接看数值，因果网格更偏向应力集成。事后没有修改。
- D1.2 WP1 中每个模型都按提交时的配置（eps0 + 0.4）评估；EX 在伪场景 / CS 上用的是该场景的运行数据，封装成框架的 Dataset。
- D2.1 WP2 的主模型 F2_S_A 在真实运行中失败；按协议不产出候选类。F1 各变体只作报告。已曝光 CK1 的 F1_S_B/S_C 无论如何都不能入选（规则 3）。
- D3.1 WP3 修订 1（3a 以锚点 1 为参照）是在审计之后、任何评估之前登记的，因为锚点 0 在 45 C 下 0.5 h 的静置与锚点 1-7 在 25 C 下 2 h 的静置不可比。登记的主配置（以锚点 0 为参照）仍然报告。
- D3.2 WP1 网格里没有起点状态这条轴，所以 3a 按构造不可能在网格上胜出；它只作为需要排行榜回答的问题来报告。
- D5.1 用户在 WP4 仍在运行时（Yagci 下载尚未完成）启动了 WP5。WP5 只依赖 WP0，因此先完成了它；其草稿中把 WP4 标为"进行中"。WP4 另行恢复。
