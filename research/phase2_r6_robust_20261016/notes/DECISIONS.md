<a id="en"></a>

# DECISIONS (round 6)

> **Language:** English · [中文](#zh)

- D0.1 The run is driven from a session whose primary directory is `/Users/shane/Desktop/Arena_1013_model`. That checkout is touched only through read-only `git show` / `git archive` of commit 21a7a55; all writes go to this worktree.
- D0.2 Round 5C's `src/` is copied into this study (`src/`). Two edits only: the worktree assertion in `common6.py`, and the prior path in `smodel5c.py` (→ `sources/prior2_5c.json`).
- D0.3 SUB tolerance: research reproduction within 5e-4 pp of the rounded reference table; the archived submitted class within 0.001 pp of SUB at delta 0.4 (observed 0.00037).

---

<a id="zh"></a>

# 决策记录（第六轮）

> **语言：** [English](#en) · 中文

- D0.1 本次运行由主目录为 `/Users/shane/Desktop/Arena_1013_model` 的会话驱动。对那个检出目录只通过只读的 `git show` / `git archive`（提交 21a7a55）访问；所有写入都在本 worktree 中。
- D0.2 第五轮 C 的 `src/` 复制到本研究（`src/`）。只改了两处：`common6.py` 中的 worktree 断言，以及 `smodel5c.py` 中的先验路径（→ `sources/prior2_5c.json`）。
- D0.3 SUB 的容差：研究复现与四舍五入后的参照表相差不超过 5e-4 pp；归档的提交类在 delta 0.4 时与 SUB 相差不超过 0.001 pp（实测 0.00037）。
