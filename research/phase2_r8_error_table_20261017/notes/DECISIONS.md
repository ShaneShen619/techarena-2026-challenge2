<a id="en"></a>

# DECISIONS (round 8)

> **Language:** English · [中文](#zh)

- **D0.1 (WP0, cache location).** The round 3 harness writes its pickle cache next to its own study. To avoid writing into an earlier study directory, `harness.py` is copied into `src/` unchanged except for a docstring line, so the cache lives in this study's git-ignored `cache/`. Events and V2 are still imported from their original directories in this worktree.
- **D0.2 (WP0, scenario set).** "Every scenario" is the round 7 WP0 set: real, PG1, PG2, PC5 and PC10 (k = 3..7, as in the pseudo metric), CS, CSE, plus PC5_all and PC10_all (k = 2..7). That gives 47 cases per Δ, the "about 48 causal cases" of the prompt. Pseudo = mean MAE over PG1, PG2, PC5, PC10; cold start = mean over CS, CSE (Δ = 0.4), as in round 7.

---

<a id="zh"></a>

# 决策记录（第 8 轮）

> **语言：** [English](#en) · 中文

- **D0.1（WP0，缓存位置）。** 第 3 轮 harness 把 pickle 缓存写在它自己的研究目录旁。为了不写入较早的研究目录，把 `harness.py` 原样复制到 `src/`（只改一行文档字符串），缓存因此位于本研究被 git 忽略的 `cache/`。events 和 V2 仍从本 worktree 中原目录导入。
- **D0.2（WP0，场景集合）。** "所有场景"取第 7 轮 WP0 的集合：real、PG1、PG2、PC5 和 PC10（k = 3..7，与伪场景指标一致）、CS、CSE，加上 PC5_all 和 PC10_all（k = 2..7）。每个 Δ 共 47 个案例，即 prompt 中的"约 48 个因果案例"。伪场景 = PG1、PG2、PC5、PC10 的 MAE 均值；冷启动 = CS、CSE 的均值（Δ = 0.4），与第 7 轮相同。
