<a id="en"></a>

# DECISIONS (round 5C)

> **Language:** English · [中文](#zh)

- D0.1 The run is driven from a session whose primary directory is `/Users/shane/Desktop/Arena_1013_model`; all commands use absolute paths or `git -C` into this worktree only.
- D0.2 Cold-start scenarios keep the stress history and remove earlier anchors, steps and A4 rows, because at CK1 the full history is known but no anchor pair exists. Removing the history would reset the ageing clock and test a different situation.

- D1.1 Candidate reading (conservative): "designs" are the registered D1, D2, D3, D4 with the selection-chosen w (0.5 for all three) and D5. The non-chosen w grid points (0.25, 0.75) are evaluated but are not candidates, because choosing w after the real run would select on real proxies (rule 2). Round 1 therefore has no candidate: every registered design fails at least one gate. The w = 0.25 ensembles pass every gate on the real run; this is reported as an exposed observation only.
- D1.2 Round 2 is opened because no model passed every gate. Its diagnosis (stage_2/DIAGNOSIS_round2.md) uses only pseudo/cold-start outputs.

---

<a id="zh"></a>

# 决策记录（第五轮 C）

> **语言：** [English](#en) · 中文

- D0.1 本次运行由主目录为 `/Users/shane/Desktop/Arena_1013_model` 的会话驱动；所有命令都用绝对路径或 `git -C` 指向本 worktree。
- D0.2 冷启动场景保留应力历史，删除更早的锚点、台阶和 A4 行，因为 CK1 时完整历史已知、只是没有锚点对。删掉历史会把老化时钟清零，检验的就是另一种情形了。
- D1.1 对"候选"的从严解读：所谓"设计"，指登记的 D1、D2、D3、按选择规则选出 w（三者都是 0.5）的 D4，以及 D5。未被选中的 w 网格点（0.25、0.75）只作评估，不算候选，因为在真实结果出来后再选 w 就是在真实代理上做选择（规则 2）。因此第一轮没有候选：每个登记的设计都至少有一个门槛没过。w = 0.25 的集成在真实结果上通过了全部门槛，这只作为已曝光的观察报告。
- D1.2 由于没有模型通过全部门槛，开启第二轮。其诊断（stage_2/DIAGNOSIS_round2.md）只使用伪场景 / 冷启动的输出。
