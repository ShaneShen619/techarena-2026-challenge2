<a id="en"></a>

# DECISIONS (round 5C)

> **Language:** English · [中文](#zh)

- D0.1 The run is driven from a session whose primary directory is `/Users/shane/Desktop/Arena_1013_model`; all commands use absolute paths or `git -C` into this worktree only.
- D0.2 Cold-start scenarios keep the stress history and remove earlier anchors, steps and A4 rows, because at CK1 the full history is known but no anchor pair exists. Removing the history would reset the ageing clock and test a different situation.

---

<a id="zh"></a>

# 决策记录（第五轮 C）

> **语言：** [English](#en) · 中文

- D0.1 本次运行由主目录为 `/Users/shane/Desktop/Arena_1013_model` 的会话驱动；所有命令都用绝对路径或 `git -C` 指向本 worktree。
- D0.2 冷启动场景保留应力历史，删除更早的锚点、台阶和 A4 行，因为 CK1 时完整历史已知、只是没有锚点对。删掉历史会把老化时钟清零，检验的就是另一种情形了。
