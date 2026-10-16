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

- D4.1 Yagci download. Attempt 1 failed with curl exit 35 (SSL connect error). Attempt 2 (retry/resume) reached 0.82 GB, then a retry truncated the file to 0 bytes and the process stalled; it was stopped. Range requests are supported (HTTP 206). At the user's request the archive is downloaded manually by the user into cache/downloads/yagci/ (same record, same licence, expected 2,456,145,428 bytes). It is still treated as untrusted data (unzip into its own directory, read with python3 -I, execute nothing).
- D4.2 The user switched the goal to WP6 while WP4 was waiting for the download, then asked to wait for the download. WP6's global Done needs WP4 done, capped or exited, so WP4 is completed first.

- D4.3 The manual download had not arrived after 7.5 h (WP4's 3 h cap long passed). WP4 was completed under its registered Yagci-unavailable fallback; the waiter was stopped. The cycle-term estimate hit its 1e-12 floor and fell back to prior2 by the registered bound rule (the fit script had omitted that rule for A_cyc; it was applied explicitly and recorded in prior3.json).
- D4.4 Data.zip was later obtained by a resumable download (curl -C - on a .part file; 2,456,145,428 bytes, the expected size). Following the user's "wait for the download and continue", the registered Yagci path was run as a supplement under the unchanged protocol. The fallback-run outputs are kept in wp4/outputs/fallback_no_yagci/. Only the summary xlsx files and the checkup file headers (test start dates) were read; nothing from the archive was executed.
- D4.5 Yagci axes, fixed before the fit: day 0 = Checkup_0 IR date (file name), later days = "Start of Test" header of the standard capacity-check file; capacity = max_CCCV_DIS; sheet #1500 excluded (identical to #1000); cycling throughput = cycles x 2 x nominal (180 Ah) scaled to 102 Ah, because the raw cycling .mat files (2.3-2.4 GB each) were not extracted. Checkup #0 is a formation test, so part of the early drop may be protocol, not ageing.
- D4.6 The A_cyc bound fallback is now encoded in fit_prior3.py (same rule as D4.3). An exploratory run with the unruled Yagci break-in (explore_yagci_unruled.py, outputs/exploratory/) is labelled exploratory and is not a candidate.
- D4.7 The user also supplied the extracted Yagci Data folder (~/Desktop/data). Its summary xlsx files have the same SHA-256 as the copies from Data.zip, so the data are identical. Its per-cycle sheet ("Analysis individual cycles - cyclic aging cells.xlsx", also in Data.zip and extracted from there) replaces the D4.5 throughput approximation, as the protocol asks for "cycling throughput from the data". Measured throughput is 0-11 % above cycles x 2 x 180 Ah, and the cells run 1-2 C above the chamber; the cycling cells now use the mean cell temperature, as LIC/Gotion do. prior3 is unchanged in every mean and SD (A_cyc median still at the floor; Yagci 50 C A_cyc 4.8e-6 / 3.0e-6 instead of 5.7e-6 / 3.6e-6), so the evaluation outputs stand.

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
- D4.1 Yagci 下载。第 1 次以 curl 错误码 35（SSL 连接错误）失败。第 2 次（重试 / 续传）下载到 0.82 GB 后，一次重试把文件截成了 0 字节，进程随之停滞，已被终止。服务器支持 Range 请求（HTTP 206）。应用户要求，压缩包改由用户手动下载到 cache/downloads/yagci/（同一记录、同一许可证，预期大小 2,456,145,428 字节）。它仍按不可信数据处理（在单独目录中解压，用 python3 -I 读取，不执行任何内容）。
- D4.2 WP4 在等待下载时，用户把目标切换到了 WP6，随后又要求等待下载完成。WP6 的整体完成标准要求 WP4 已完成、到达上限或已退出，因此先完成 WP4。
- D4.3 7.5 小时后手动下载仍未到位（远超 WP4 的 3 小时上限）。WP4 按登记的 Yagci 不可用回退方案完成；等待任务已停止。循环项的估计撞到 1e-12 的下限，按登记的边界规则回退到 prior2（拟合脚本漏掉了对 A_cyc 应用这条规则，已显式补上并记录在 prior3.json 中）。
- D4.4 之后通过可续传下载（对 .part 文件用 curl -C -）拿到了 Data.zip（2,456,145,428 字节，与预期一致）。按用户"等待下载完继续推进"的指示，在不变的协议下把登记的 Yagci 路径作为补充运行。回退运行的输出保留在 wp4/outputs/fallback_no_yagci/。只读取了汇总 xlsx 和检查文件的文件头（测试开始日期）；没有执行压缩包里的任何内容。
- D4.5 Yagci 时间轴在拟合之前确定：第 0 天 = Checkup_0 内阻测试日期（文件名），之后的天数 = 标准容量检查文件头中的 "Start of Test"；容量 = max_CCCV_DIS；排除 #1500 表（与 #1000 相同）；循环吞吐 = 循环数 x 2 x 标称容量（180 Ah），折算到 102 Ah，因为没有解压原始循环 .mat 文件（每个 2.3-2.4 GB）。检查 #0 是化成测试，所以早期下降里可能有一部分来自流程而不是老化。
- D4.6 A_cyc 的边界回退现已写进 fit_prior3.py（与 D4.3 同一条规则）。用不受规则约束的 Yagci 磨合项做的运行（explore_yagci_unruled.py，outputs/exploratory/）标为探索性，不是候选。
- D4.7 用户另外提供了解压好的 Yagci Data 文件夹（~/Desktop/data）。其中汇总 xlsx 的 SHA-256 与从 Data.zip 中取出的副本相同，数据完全一致。其中的逐循环表（"Analysis individual cycles - cyclic aging cells.xlsx"，Data.zip 里也有，从那里取出）替代了 D4.5 的吞吐近似，因为协议要求"循环吞吐取自数据"。实测吞吐比 循环数 x 2 x 180 Ah 高 0-11 %，电芯温度比温箱高 1-2 C；循环电芯现在与 LIC/Gotion 一样用平均芯温。prior3 的每个均值和 SD 都没有变化（A_cyc 中位数仍在下限；Yagci 50 C 的 A_cyc 由 5.7e-6 / 3.6e-6 变为 4.8e-6 / 3.0e-6），所以评估输出保持不变。
