<a id="en"></a>

# Post-Checkup Full-Charge Anchor + Graphite-Step Displacement: Capacity-Estimation Validation — Standalone Execution Prompt

> **Language:** English · [中文](#zh)

Written 2026-10-13. Hand this whole document to the executor to start; it does not depend on the original chat. This task is a research validation and does not directly replace the competition submission model.

> **Translation note:** This English text is a translation of the original Chinese brief below, which remains the authoritative record of what the executor was asked to do. Paths and file names are quoted as they were at the time.

> **Layout update (note added 2026-10-13 when the branch was tidied):** The text below is the original brief as executed and is kept unchanged. After execution, the branch was reorganised into `main` plus this study directory.
> - The standalone worktree and the symlink in the main directory described in §1 no longer exist.
> - `framework/`, `my_model/` and `data/` are under `TechArena_Challenge2_Team_Package/`.
> - The other research material listed in §2 is on branch `research-archive-20261010`.
> - Files were renamed: this document was originally `执行Prompt.md`, and `run_candidate.py` in §5 is now `stage_f_candidate.py`. See [README.md](README.md) for the other scripts.

## 0. Task and questions to answer

You are the research engineer responsible for battery capacity estimation and experimental validation. The project root is `/Users/shane/Desktop/Arena 阶段 2 官方材料` (the "main directory" below).

The official task:

- A 4 × 102 Ah LFP series pack. Estimate SOH = Qpack/102 on each checkup date.
- Qpack is the Ah discharged at 5.1 A, after a reference full charge, until the pack voltage first reaches 11.2 V.
- Only CK0 = 100.41 Ah is public; CK1–CK7 are hidden.
- The score is the SOH error (including the worst-case error) divided by the corresponding error of the official ExampleModel.

The three previous routes failed for lack of identifiability or because of model mismatch. They were paper transfer, joint four-cell ECM estimation and multistage joint features, and all three tried to infer capacity from local voltage windows in the middle of the plateau.

The first-principles diagnosis of 2026-10-13 found two problems with those routes:

- They freed the start offset and used an ageing template that "stretches the whole curve uniformly".
- They never used two near-direct capacity observations that the data already contain:

1. **Post-checkup full charge.** After each checkup, the first operating segment opens with a charge from near empty (rest at about 2.89–2.99 V/cell) to the end of the CCCV 14.0 V phase. The charged Ah are about:
   - 100.12 after CK0 (45 °C);
   - 97.00, 95.66, 94.64, 93.75, 93.08, 92.64 and 91.95 after CK1–CK7 (25 °C).
2. **The fixed program crossing the graphite step.**
   - About every 5 days, the sequence "CCCV full charge → 20 A pulse of about 10.2 Ah → dynamic discharge of about 45.7 Ah" reaches a cumulative depth of about 55.9 Ah.
   - It crosses the graphite staging step, which on the CK0 curve lies about 33 Ah below full.
   - The "step → top of charge" Ah distance falls monotonically from about 32.8 to about 25.9 Ah over 41 events.
   - It is insensitive to temperature, and recovers by about 0.3–0.6 Ah after each checkup.

These preliminary numbers come from a quick probe script. They must be re-derived independently and reproducibly in this task, not copied.

Questions you must answer:

1. Can the post-checkup full charge serve as a proxy for the CK capacity? What is a reasonable range for the offset ε = Q_CK − Q_fc, and which assumptions determine it?
2. Is the "step → top of charge" distance a stable, repeatable health quantity that is insensitive to detection parameters? How does it relate to the change in full-charge capacity (LLI 1:1 or another ratio)?
3. Under strict causality (predicting CK_k uses only data before the CK_k date), what is the proxy error of "latest full-charge anchor + step-displacement update" compared with ExampleModel and the existing B baseline? How sensitive is it to ε and to the ratio assumption?
4. Can CK1 be estimated reliably, when only CK0 and the first month of data come before it?
5. Which conclusions hold only at proxy level, and what remains unverifiable?

## 1. Work isolation (already done; check before running)

**Where the work lives.**

- **Branch:** `exp/phase2-anchor-step-20261013`, based on `3b0909e`.
- **Standalone worktree:** `/Users/shane/.cursor/worktrees/arena-phase2/anchor-step-20261013` (the "worktree" below). All code, configuration and results go into `research/phase2_anchor_step_20261013/` of the worktree.
- **Symlink:** `research/phase2_anchor_step_20261013` in the main directory is a symlink to it.

**What not to touch.**

- **The main directory.** It currently has another experiment branch checked out and many untracked research directories.
  - Do not switch branches there, `git add .`, clean or reset anything.
  - Uncommitted research material in the main directory is referenced read-only; record its absolute paths and SHA256.
- **The parallel "information ladder" task.** `exp/phase2-information-ladder-20261013` runs that task in another worktree. This task does not modify its files. The two may cite each other's conclusions but are not merged.
- **The framework and the active model.** Do not modify `framework/`, `run_model.py`, `validate_submission.py` or the active `my_model/`. The candidate model lives as a separate file in this study directory.

**What to record.** Write the following to `environment.json` and `input_manifest.json`:

- `git status --short --branch`;
- HEAD;
- the Python, numpy, pandas and scipy versions;
- the SHA256 of every input file.

## 2. Required reading

**Official materials.**

- `submission_instructions_2026.md`: interface, causal cut, score normalisation.
- `data/DATA_DESCRIPTION.md`.
- `framework/data.py`: the cut logic of `load_dataset(until=...)` is `timestamp <= until`.
- `my_model/model_example.py`: ExampleModel is the scoring reference and must be reproduced unchanged in the same causal pipeline.

**Earlier research.** Paths are in the main directory unless noted.

- **First-principles diagnosis:** `research/phase2_first_principles_20261013/研究诊断与下一轮路线.md`.
- **The three failure reports:**
  - `research/phase2_paper_transfer_20261012/implementation_v1/FINAL_REPORT.md`
  - `research/phase2_ecm_joint_20261012/完整执行验证报告.md`
  - `research/phase2_multistage_features_20261012/FINAL_REPORT.md`

  You only need the reasons for failure and the reusable audit conclusions.
- **Event and counter audit:** `research/charge_capacity_review_20261006/` (`operating_events.csv`, `findings.json`). It contains an existing event segmentation and an audit of counter semantics. **The 20 A pulse is booked as charge in the cumulative counters**, so net charge must be integrated from `current_A` over actual time steps.
- **B baseline:** `research/phase2_paper_transfer_20261012/implementation_v1/history_B_prior_baseline.csv`. These are its per-CK predictions, for comparison only, not truth.
- **Identifiability card:** `research/phase2_literature_reassessment/notes/papers/Lin2015_Fisher_identifiability.md`. Capacity information ∝ slope × span, and the start offset is collinear with capacity.

## 3. Physical assumptions (to be tested, not conclusions)

- **Electrode limits and the step.** In an LFP/graphite full cell, the top of charge is set by full delithiation of LFP and the empty end by full delithiation of graphite. The graphite staging transition (around x ≈ 0.5) produces a step on the Ah axis.
- **LLI vs LAM.**
  - If ageing is dominated by loss of lithium inventory (LLI), almost all capacity loss shows up as a shorter "step → top" section, while "empty end → step" stays the same, i.e. ΔQ ≈ Δ(step → top).
  - Loss of negative-electrode active material (LAM_NE) also shortens "empty end → step", which makes the ratio > 1.
- **Measurement sensitivities.**
  - The position of a feature on the Ah axis is insensitive to voltage offset and to constant IR drop, and weakly sensitive to temperature.
  - It depends somewhat on current and smoothing window, so only measurements from the same program and the same current band are compared.
- **Post-checkup recovery.** It may come from reversible effects such as the negative-electrode overhang. It makes the states "before" and "after" a checkup different and must be handled explicitly.

Each assumption must come with a check that could overturn it, and the result must be reported.

## 4. Data and causality rules

1. **Integration.**
   - Charge current is positive; integrate over adjacent time steps (Ah = ΣIΔt/3600).
   - Do not integrate Δt > 600 s or Δt ≤ 0 (duplicate timestamps mark step transitions).
   - Duplicate timestamps are deduplicated within a phase; never replace the last discharge point with a rest point.
2. **The causal cut.**
   - A prediction for CK_k may use only the data returned by `load_dataset(data_dir, until=CK_k date)`, including CK0 and the CK0 reference curve.
   - `fit()` receives the full data, but nothing after the CK_k date may be used for that CK's prediction: not for event selection, thresholds, ratios, ε, normalisation or extrapolation parameters.
   - Implement this by re-running per CK with the framework's `until` cut, plus an automatic check: replace or delete data after the cutoff date, and the prediction must stay bit-identical.
3. **When Q_fc,k may be used.** The post-checkup full charge Q_fc,k happens after CK_k. It may be used **only as the evaluation proxy for CK_k**; as an input it may be used only for CK_{k+1} and later.
4. **Proxies are not truth.**
   - Proxy labels are not the hidden truth, and all errors are called "proxy errors".
   - Do not use proxies to back out "true CK values" for any submission file, README conclusion or external statement.
   - Under the submission rules, CK1–CK7 must not be reconstructed from external sources.
5. **Pre-registration.**
   - Some of the numbers in this task have already been seen during probing (see §0), so this is an exposed, exploratory validation.
   - The main model and all variants must be written into `protocol.json`, with its SHA256 recorded, before the evaluation scripts are run.
   - After that, do not pick a variant as the main result based on proxy error.

## 5. Experimental steps

### Stage A: event extraction and audit

**A1 Post-checkup full charge.**

- **Rule (written into the protocol in advance):** the first charge in an operating segment that meets all of these:
  - rest before the start, with pack voltage < 12.3 V;
  - continuous positive current;
  - reaches pack voltage ≥ 13.95 V and ends in CV (end current < 6 A).
- **Output:**
  - start and end times, rest time before the start, the four cell voltages at the start, temperature;
  - CC/CV split of Ah, end current, the four cell voltages at the end;
  - integrated Ah and its difference from the counter, maximum sampling interval.
- **Start-state check:** confirm that all four cells start in the steep tail of the CK0 curve. Use the loaded CK0 curve to convert the start voltage into a maximum Ah uncertainty, and explain the difference between loaded and rest voltage.

**A2 Step measurement in the fixed program.**

- **Tracking:**
  - Take the CV end as zero and track the following discharge along the integrated net discharged Ah, until a recharge exceeds 2 Ah.
  - Require a maximum depth ≥ 50 Ah.
  - Use only samples whose current is in a pre-specified band (main setting −12.5 to −8 A).
- **Per-cell location, main method:** the depth at which the voltage first crosses the midpoint between the median voltage of the upper plateau (15–25 Ah) and that of the lower plateau (42–50 Ah).
- **Comparison methods:**
  - (a) the extremum of the smoothed dV/dQ;
  - (b) a current band of −11.5 to −9 A;
  - (c) plateau windows shifted by ±3 Ah;
  - (d) a rough IR correction V + R̂·|I|, with R̂ estimated only from history visible at that time.
- **Output:**
  - step depth per event, per cell and per method;
  - four-cell consistency and differences between methods;
  - comparison of neighbouring 45 °C and 25 °C events;
  - jumps across checkups.

**A3 CK0 reference.** Locate the step in the same way on the CK0 reference curve (5.1 A), compare it with the first operating event (about 10 A), and explain the current dependence.

**A4 Step split inside the full charge.**

- For each A1 charge, locate the charge-direction step to get two sections, "empty end → step" and "step → top of charge".
- Test which section the ageing is concentrated in (LLI/LAM discrimination).
- Give uncertainties: sensitivity to the detection grid and the smoothing window.

**Stop condition.** In either of these cases the step channel is not used for capacity updates and only the full-charge anchor is kept:

- the step cannot be located in most events;
- the typical four-cell difference or difference between methods is > 1 Ah.

### Stage B: proxy labels and ε

**The proxy.**

- P_k = Q_fc,k + ε, for k = 1..7.
- ε is defined by CK0: ε0 = 100.41 − Q_fc,0. However, Q_fc,0 is at 45 °C and the others at about 26.7 °C.

**Registered values of ε.**

- The set is registered in advance: {ε0, ε0 + lower temperature correction, ε0 + upper temperature correction}.
- Base the temperature-correction range on the 25 vs 45 °C charge-capacity difference, either from retrievable literature or from the phase-one data of the same 102 Ah LFP single cell (`dataset original` in the main directory, read-only). State the source.
- If no reliable basis can be found, use [0.3, 1.1] Ah and mark it as an assumption.

**ε-independent quantities.** Report quantities that do not depend on ε: the relative errors of the predictors (prediction error of P_k − P_{k−1}, extrapolation error).

**Mechanisms that could make ε drift.** List them:

- the checkup protocol's full-charge termination;
- steps after the checkup;
- the effect of resistance growth on the CC/CV split;
- the recovery.

Bound them with checks the visible data allow, for example:

- the change of Q_CC/Q_fc over time;
- the end current;
- the consistency of start voltage and rest time.

### Stage C: pre-registered causal predictors

All predictors go through the same causal loop: for each CK_k, `ds = load_dataset(data_dir, until=CK_k)`, and everything is computed from `ds`. Event-extraction code is shared.

**Predictors.**

- **M0 ExampleModel:** `my_model/model_example.py`, called unchanged.
- **M1 existing B baseline:** read from CSV, for comparison only.
- **M2 anchor persistence:** Q̂_k = Q_fc,last + ε. "last" is the latest post-checkup full charge before the cutoff; for CK1 it is CK0 itself.
- **M3 anchor + √t extrapolation:**
  - Fit a + b√t to all 25 °C post-checkup full charges before the cutoff.
  - With fewer than 2 points, fall back to M2.
  - The extrapolation is not allowed to increase.
- **M4 (main model) anchor + step displacement:**
  - Q̂_k = Q_anchor + β·(s_last − s_anchor), with β = 1 (LLI 1:1).
  - s_anchor is the first step measurement after the anchor, and s_last the last one before the cutoff.
  - For CK1: Q_anchor = 100.41 Ah (CK0), and s_anchor is the first step measurement after CK0.
- **M4 sensitivity:**
  - β ∈ {0.7, 1.0, 1.3, 1.5};
  - s_last = the last measurement before the cutoff, or the mean of the last two;
  - step detection with each A2 comparison method.
- **M5 causally fitted β:** robust regression on the visible (Q_fc,j, s_after,j) pairs before the cutoff; with fewer than 2 pairs, β = 1.

**Two pre-registered treatments of the recovery.**

- (i) No treatment.
- (ii) The main setting: s_anchor is the first measurement in the 25 °C segment of the anchor, and s_last the last measurement before the cutoff. Separately report the mean jump "last measurement before the checkup vs first measurement after it", for interpretation.

For each predictor, save per CK: the input events, the available_after time, the parameters and the output.

### Stage D: evaluation

- **Error metrics.**
  - Proxy SOH error: e_k = Ŝ_k − P_k/1.02 × 100 (pp).
  - For each value of ε, report MAE, RMSE, maximum absolute error and per-CK errors.
  - Also report ratios relative to ExampleModel (MAE ratio and maximum-error ratio), because the official score is normalised by the baseline. The exact metric set is not public, so this is only an approximation.
- **ε-independent metric:** the incremental prediction error on CK2–CK7.
- **Stratification.**
  - Report CK1 separately.
  - Segment 3 (19 February – 11 March) is missing before CK2; explain this separately.
- **No cherry-picking.** Do not report only the most favourable ε or variant. The main table is fixed as the M4 main setting × all ε values.

### Stage E: robustness and falsification

1. **Data-deletion check:** delete or shuffle data after the CK_k date; the CK_k prediction must stay bit-identical.
2. **Detection-parameter perturbation:** the maximum change in the M4 output under each A2 comparison method.
3. **Leave-one-anchor-out:** remove one full charge, simulating missing data, and check whether M4 degrades smoothly to the step channel or to M2.
4. **Synthetic falsification (small scale).**
   - **Generator:** build a simplified half-cell-level model from the CK0 curve: a flat LFP positive electrode plus a graphite negative electrode with a two-level step, with parameters roughly matched to the CK0 curve.
   - **Ageing cases:** apply known ageing of pure LLI, pure LAM_NE and LLI + LAM.
   - **Generated quantities:** the "full-charge capacity", the "step → top" distance and the "C/20 discharge capacity".
   - **Test:** check the error of M4 and of β under each mechanism.
   - **Limits:** explain the generator's limits, and do not treat it as a real calibration.
5. **β-driven checkpoints:** if the step's sensitivity to β moves the CK7 prediction by more than 1 pp, label it clearly as "driven by the ratio assumption".
6. **The four cells:** the pack cutoff is set by the weakest cell. Check whether the step displacement is consistent across the four cells; if one cell is clearly faster, explain the effect on pack capacity.

### Stage F: candidate model package

- **The class.**
  - Create `candidate_model/anchor_step_model.py` in this study directory, with a class that has the same interface as `MyModel` (`fit`, `estimate_soh`) and depends only on numpy/pandas.
  - It must have a defined fallback when no event is usable (M2 → CK0 SOH), and output diagnostics for each CK.
- **Local evaluation entry.** Write `run_candidate.py`: it calls the model per CK through the framework's `load_dataset(until=...)` and writes a CSV.
- **Smoke test.** Also run it on `sample_data/` to confirm that it does not fail and that the fallback is sensible.
- **No switch.** Do not switch `my_model/__init__.py`. Whether to wire it into the active submission is the user's decision.

### Stage G: report

**`FINAL_REPORT.md`.** In Chinese, conclusions first. It covers:

- what was done;
- the key numbers and figures from A–E;
- the main model's proxy performance, relative to ExampleModel and B;
- ε and β sensitivity;
- what cannot be verified;
- whether to recommend it as a formal submission candidate, and on what conditions.

**Attachments:**

- `README.md` (reproduction commands);
- `protocol.json`;
- all CSV/JSON;
- figures (PNG).

## 6. Acceptance gates (pre-registered)

- **G1 data:**
  - all seven A1 full charges (plus the one after CK0) are identified;
  - the integral differs from the counter by < 0.05 Ah;
  - every start lies in the steep tail.
- **G2 step channel:**
  - ≥ 90 % of fixed-program events can be located with the main method;
  - the median four-cell range is ≤ 0.8 Ah;
  - each comparison method changes M4's CK7 output by ≤ 0.5 Ah.

  If not met, M4 falls back to M3/M2.
- **G3 causality:** every data-deletion check is bit-identical.
- **G4 proxy performance:**
  - for every registered ε, M4's MAE and maximum error are both below ExampleModel's;
  - the CK2–CK7 incremental-error MAE is ≤ 0.5 pp.
- **G5 mechanism:**
  - In the synthetic falsification, M4's error is ≤ 0.5 Ah in the LLI-dominated case.
  - In the LAM-dominated case the error is reported as found, together with an explanation of how the A4 split determines which case the real data belong to.

**Outcomes.**

- **All pass:** label it "a formal candidate that passes at proxy level", still noting that the hidden truth is unverified.
- **Partial pass:** state which part is usable (for example the anchor only).
- **G1 or G3 fails:** stop and report.

## 7. Prohibitions

- **Proxies:** do not treat proxies as truth, and do not claim official accuracy.
- **Variant selection:** after seeing proxy errors, do not switch the main variant, ε or β to report better numbers. Exploratory results are reported separately.
- **Causality:** do not use data after CK_k to predict CK_k.
- **Git and the framework:**
  - do not modify the framework or the active model;
  - do not commit to main;
  - do not push to the remote, unless the user asks otherwise.
- **Other research:** do not delete or rewrite other research directories.

---

<a id="zh"></a>

# 检查后完整充电锚点 + 石墨台阶位移：容量估计验证——独立执行 Prompt

> **语言：** [English](#en) · 中文

编写日期：2026-10-13。将本文全文交给执行者即可开始，不依赖原聊天。本任务是研究验证，不直接替换比赛提交模型。

> **布局更新（2026-10-13 整理分支时补注）：** 下文是执行时的原始任务书，保留原文。执行完成后，分支已重组为 `main` + 本研究目录：§1 所述独立 worktree 与主目录符号链接已不存在；`framework/`、`my_model/`、`data/` 位于 `TechArena_Challenge2_Team_Package/`；§2 列出的其他研究资料在分支 `research-archive-20261010` 上。文件已改名：本文原名 `执行Prompt.md`，§5 中的 `run_candidate.py` 现为 `stage_f_candidate.py`，其他脚本见 [README.md](README.md)。

## 0. 任务与要回答的问题

你是负责电池容量估计与实验验证的研究工程师。项目根目录 `/Users/shane/Desktop/Arena 阶段 2 官方材料`（下称“主目录”）。官方任务：4×102 Ah LFP 串联组，在每个检查点日期估计 SOH=Qpack/102，Qpack 为参考满充后 5.1 A 放电至组端首次 11.2 V 的 Ah；只有 CK0=100.41 Ah 公开，CK1–CK7 隐藏，评分为 SOH 误差（含最坏误差）除以官方 ExampleModel 的对应误差。

此前三条路线（论文迁移、四串 ECM 联合估计、多阶段联合特征）都试图从平台中段的局部电压窗口反推容量，均因可辨识性不足或模型失配未通过。2026-10-13 的第一性原理诊断指出：它们放开了起点偏移、使用“整条曲线等比伸缩”的老化模板，而数据中已有两类近乎直接的容量观测从未作为容量观测使用：

1. **检查后完整充电**：每个检查之后的首个运行段以一次从近空（静置约 2.89–2.99 V/芯）到 CCCV 14.0 V 末端的充电开头，充入 Ah 依次约 100.12（CK0 后，45°C）、97.00、95.66、94.64、93.75、93.08、92.64、91.95（CK1–CK7 后，25°C）。
2. **固定程序越过石墨台阶**：约每 5 天的“CCCV 满充 → 20 A 脉冲约 10.2 Ah → 约 45.7 Ah 动态放电”累计深度约 55.9 Ah，越过 CK0 曲线中距满充约 33 Ah 的石墨分阶台阶；“台阶→满充端”的 Ah 距离从约 32.8 单调降至约 25.9 Ah（41 次），对温度不敏感，每次检查后有约 0.3–0.6 Ah 的回弹。

初步数字来自快速探查脚本，必须在本任务中重新、独立、可复现地得到；不得直接抄用。

必须回答：

1. 检查后完整充电能否作为 CK 容量的代理？偏置 ε=Q_CK−Q_fc 的合理范围是多少？哪些假设决定它？
2. “台阶→满充端”距离是否是稳定、可重复、对检测参数不敏感的健康量？它与完整充电量的变化是什么关系（LLI 1:1 还是其他比例）？
3. 在严格因果条件下（预测 CK_k 只用 CK_k 日期前的数据），“最近完整充电锚点 + 台阶位移更新”相对 ExampleModel 和既有 B 基线的代理误差是多少？对 ε 与比例假设有多敏感？
4. CK1（之前只有 CK0 与第一个月数据）能否可靠估计？
5. 哪些结论只是代理层面的，什么仍不可验证？

## 1. 工作隔离（已完成，执行前核对）

- 分支：`exp/phase2-anchor-step-20261013`，基于 `3b0909e`。
- 独立 worktree：`/Users/shane/.cursor/worktrees/arena-phase2/anchor-step-20261013`（下称“工作树”）。所有代码、配置、结果放在工作树的 `research/phase2_anchor_step_20261013/`。主目录 `research/phase2_anchor_step_20261013` 是指向它的符号链接。
- 主目录当前检出其他实验分支，并有大量未跟踪研究目录；不要在主目录切换分支、`git add .`、清理或重置任何东西。主目录未提交的研究资料只读引用，记录绝对路径与 SHA256。
- 另有 `exp/phase2-information-ladder-20261013` 在别的 worktree 进行“信息阶梯”任务；本任务不修改其文件，结论可互相引用但不合并。
- 不修改 `framework/`、`run_model.py`、`validate_submission.py`、正式 `my_model/`。候选模型以独立文件形式放在本研究目录。
- 记录 `git status --short --branch`、HEAD、Python 与 numpy/pandas/scipy 版本、所有输入文件 SHA256 到 `environment.json`、`input_manifest.json`。

## 2. 必读资料

- `submission_instructions_2026.md`（接口、因果截断、评分归一化）、`data/DATA_DESCRIPTION.md`、`framework/data.py`（`load_dataset(until=...)` 的截断逻辑：`timestamp <= until`）。
- `my_model/model_example.py`：ExampleModel 是评分基准，必须原样在同一因果流程中复现。
- 主目录 `research/phase2_first_principles_20261013/研究诊断与下一轮路线.md`。
- 主目录三份失败报告：`research/phase2_paper_transfer_20261012/implementation_v1/FINAL_REPORT.md`、`research/phase2_ecm_joint_20261012/完整执行验证报告.md`、`research/phase2_multistage_features_20261012/FINAL_REPORT.md`。只需理解失败原因与可复用审计结论。
- 主目录 `research/charge_capacity_review_20261006/`（`operating_events.csv`、`findings.json`）：已有事件切分与计数器语义审计；**20 A 脉冲在累计计数器中记为充电**，净电量必须以 `current_A` 按实际时间差积分。
- 主目录 `research/phase2_paper_transfer_20261012/implementation_v1/history_B_prior_baseline.csv`：既有 B 基线逐 CK 预测，作为对照，不是真值。
- `research/phase2_literature_reassessment/notes/papers/Lin2015_Fisher_identifiability.md`（容量信息 ∝ 斜率 × 跨度；起点与容量共线）。

## 3. 物理假设（待检，不是结论）

- LFP/石墨全电池：满充端由 LFP 完全脱锂决定，放空端由石墨完全脱锂决定；石墨分阶相变（约 x≈0.5）在 Ah 轴上产生台阶。
- 若老化以活性锂损失（LLI）为主，容量损失几乎全部体现为“台阶→满充端”段缩短，“放空端→台阶”段不变，即 ΔQ≈Δ(台阶→满充端)；负极活性物质损失（LAM_NE）会让“放空端→台阶”段也缩短，使比例 >1。
- 特征在 Ah 轴上的位置对电压偏置和恒定 IR 压降不敏感，对温度弱敏感；对电流和平滑窗口有一定依赖，所以只比较同程序、同电流段的测量。
- 检查后回弹可能来自负极 overhang 等可逆效应；它使“检查前”和“检查后”的状态不同，需要显式处理。

每条假设都要配一个可能推翻它的检查，并报告结果。

## 4. 数据与因果规则

1. 电流充电为正，按相邻时间差积分（Ah=ΣIΔt/3600）；Δt>600 s 或 ≤0（重复时间戳是阶段切换标记）不积分。重复时间戳在阶段内去重，不得把放电末点替换为静置点。
2. 预测 CK_k 只能用 `load_dataset(data_dir, until=CK_k 日期)` 返回的数据（含 CK0 与 CK0 参考曲线）。`fit()` 收到全量数据，但不得把 CK_k 日期之后的任何量用于该 CK 的预测：不得用于事件筛选、阈值、比例、ε、归一化或外推参数。实现上用框架的 `until` 截断逐 CK 重跑，并加自动检查：把截止日期后的数据替换/删除，预测必须逐位不变。
3. 检查后完整充电 Q_fc,k 发生在 CK_k 之后，**只能作为 CK_k 的评估代理**；作为输入时只能用于 CK_{k+1} 及以后。
4. 代理标签不是隐藏真值。所有误差称为“代理误差”。禁止用代理反推“真实 CK 值”写进任何提交文件、README 结论或对外表述；按提交规则，不得从外部来源重建 CK1–CK7。
5. 本任务的部分数字已在探查中被看到（见 §0），属于已曝光的探索性验证。主模型和全部变体须在运行评估脚本之前写入 `protocol.json` 并记录 SHA256；之后不得根据代理误差挑选变体当主结果。

## 5. 实验步骤

### 阶段 A：事件提取与审计

A1 检查后完整充电。规则（预先写入协议）：运行段内首个满足以下条件的充电：起点前静置、组压 <12.3 V；连续正电流；达到组压 ≥13.95 V 并以 CV 结束（末电流 <6 A）。输出：起止时间、起点前静置时长、起点四芯电压、温度、CC/CV 分段 Ah、末电流、末端四芯电压、积分 Ah 与计数器差、最大采样间隔。核查四芯起点是否处于 CK0 曲线陡峭尾段（用 CK0 带载曲线换算起点电压对应的最大 Ah 不确定度，并说明带载与静置的差异）。

A2 固定程序台阶测量。CV 末端作为零点，沿积分净放电 Ah 追踪后续放电，直到回充超过 2 Ah；要求最大深度 ≥50 Ah。只取电流在预先规定区间（主设置 −12.5~−8 A）的样本，逐芯定位台阶：主方法为“上平台（15–25 Ah）中位电压与下平台（42–50 Ah）中位电压的中点首次穿越深度”；对照方法：(a) 平滑后 dV/dQ 极值；(b) 电流区间 −11.5~−9 A；(c) 平台窗口各移 ±3 Ah；(d) IR 粗校正 V+R̂·|I|（R̂ 只用当时可见历史估计）。输出逐事件、逐芯、各方法的台阶深度；四芯一致性；方法间差异；45°C 与 25°C 近邻事件对比；检查前后跳变。

A3 在 CK0 参考曲线（5.1 A）上做同样的台阶定位，比较与运行首事件（约 10 A）的差异，说明电流依赖。

A4 完整充电内的台阶分解：对每次 A1 充电定位充电方向台阶，得到“放空端→台阶”和“台阶→满充端”两段 Ah，检验老化集中在哪一段（LLI/LAM 判别），给出不确定度（检测网格、平滑窗口敏感性）。

停止条件：若台阶在多数事件中不可定位、四芯差异或方法间差异的典型值 >1 Ah，则台阶通道不作为容量更新，只保留完整充电锚点。

### 阶段 B：代理标签与 ε

- 代理：P_k=Q_fc,k+ε，k=1..7。ε 由 CK0 定义：ε0=100.41−Q_fc,0，但 Q_fc,0 在 45°C，其余在约 26.7°C。ε 的取值集合预先登记：{ε0, ε0+温度修正下限, ε0+温度修正上限}，温度修正范围依据可查文献/阶段一同型 102 Ah LFP 单芯数据（主目录 `dataset original`，只读）中 25 与 45°C 的充电容量差确定，写清来源；找不到可靠依据就用 [0.3, 1.1] Ah 并标为假设。
- 报告不依赖 ε 的量：预测器的相对误差（P_k−P_{k−1} 的预测误差、外推误差）。
- 列出可能使 ε 随时间漂移的机制（检查协议的满充终止、检查后步骤、电阻增长对 CC/CV 分配的影响、回弹），并用可见数据能做的检查给出上界：例如 Q_CC/Q_fc 随时间的变化、末电流、起点电压与静置时长的一致性。

### 阶段 C：预先登记的因果预测器

全部预测器通过同一因果循环：对每个 CK_k，`ds=load_dataset(data_dir, until=CK_k)`，再从 `ds` 计算。共享事件提取代码。

- M0 ExampleModel（原样调用 `my_model/model_example.py`）。
- M1 既有 B 基线（读 CSV，仅对照）。
- M2 锚点持续：Q̂_k=Q_fc,last+ε（last 为截止前最近一次检查后完整充电；CK1 时为 CK0 本身）。
- M3 锚点 + √t 外推：用截止前所有 25°C 检查后完整充电拟合 a+b√t；点数 <2 时退回 M2；外推不允许升高。
- M4（主模型）锚点 + 台阶位移：Q̂_k=Q_anchor+β·(s_last−s_anchor)，s_anchor 为锚点之后首次台阶测量，s_last 为截止前最后一次；β=1（LLI 1:1）。CK1：Q_anchor=100.41 Ah（CK0），s_anchor 为 CK0 后首次台阶测量。
- M4 敏感性：β∈{0.7, 1.0, 1.3, 1.5}；s_last 用截止前最后 1 次或最后 2 次的均值；台阶检测用 A2 各对照方法。
- M5 因果拟合 β：用截止前可见的（Q_fc,j, s_after,j）配对做稳健回归，配对 <2 时 β=1。
- 处理回弹的两个预登记版本：(i) 不处理；(ii) s_anchor 使用锚点所在 25°C 段的首测量，s_last 使用截止前最后测量（即主设置），并另报“检查前末测量对检查后首测量”的平均跳变，用于解释。

每个预测器保存逐 CK 的输入事件、available_after 时间、参数和输出。

### 阶段 D：评估

- 代理 SOH 误差 e_k=Ŝ_k−P_k/1.02×100（pp），对每个 ε 值：MAE、RMSE、最大绝对误差、逐 CK 误差；并给“相对 ExampleModel 的比值”（MAE 比与最大误差比），因为官方评分按基准归一化（具体指标集未公开，只作近似）。
- 与 ε 无关的指标：CK2–CK7 的增量预测误差。
- 分层：CK1 单独报告；CK2 前有缺失的第 3 段（2/19–3/11），单独说明。
- 不得只报告最有利的 ε 或变体；主表固定为 M4 主设置 × 全部 ε。

### 阶段 E：稳健性与反证

1. 删数据检查：把 CK_k 日期后的数据删除或打乱，CK_k 预测逐位不变。
2. 检测参数扰动（A2 各对照）对 M4 输出的最大变化。
3. 留一锚点：去掉某一次完整充电（模拟数据缺失），M4 是否平稳退化到台阶通道或 M2。
4. 合成反证（小规模）：用 CK0 曲线构造半电池级简化模型（LFP 平坦正极 + 带两级台阶的石墨负极，参数由 CK0 曲线粗配），分别施加纯 LLI、纯 LAM_NE、LLI+LAM 的已知老化，生成“完整充电量”“台阶→满充端距离”“C/20 放电容量”，检验 M4 与 β 在每种机制下的误差；说明该生成器的局限，不把它当真实标定。
5. 若台阶对 β 的敏感性使 CK7 预测变化超过 1 pp，明确标为“比例假设驱动”。
6. 检查四芯：组端截止由最弱芯决定，确认四芯台阶位移是否一致；若某芯明显更快，说明对组容量的影响。

### 阶段 F：候选模型包

- 在本研究目录新建 `candidate_model/anchor_step_model.py`，实现与 `MyModel` 相同接口的类（`fit`、`estimate_soh`），只依赖 numpy/pandas；无可用事件时有确定的回退（M2→CK0 SOH），并在每个 CK 输出诊断。
- 写一个本地评估入口 `run_candidate.py`：用框架的 `load_dataset(until=...)` 逐 CK 调用，输出 CSV。另在 `sample_data/` 上冒烟运行，确认不报错且回退合理。
- 不切换 `my_model/__init__.py`；是否接入正式提交由用户决定。

### 阶段 G：报告

`FINAL_REPORT.md`（中文，先给结论）：做了什么；A–E 的关键数字与图；主模型在代理上的表现及相对 ExampleModel/B；ε 与 β 敏感性；不可验证部分；是否建议进入正式提交候选以及前提。附 `README.md`（复现命令）、`protocol.json`、全部 CSV/JSON、图（PNG）。

## 6. 接纳门（预先登记）

- G1 数据：A1 七次（加 CK0 后一次）完整充电全部识别，积分与计数器差 <0.05 Ah，起点均在陡峭尾段。
- G2 台阶通道：主方法下 ≥90% 固定程序事件可定位；四芯中位极差 ≤0.8 Ah；各对照方法对 M4 的 CK7 输出变化 ≤0.5 Ah。不满足则 M4 退回 M3/M2。
- G3 因果：删数据检查全部逐位一致。
- G4 代理表现：在全部登记 ε 下，M4 的 MAE 与最大误差都低于 ExampleModel，且 CK2–CK7 增量误差 MAE ≤0.5 pp。
- G5 机制：合成反证中，在 LLI 主导的情形下 M4 误差 ≤0.5 Ah；在 LAM 主导的情形下误差被如实报告，并说明在真实数据中用 A4 分解判别属于哪种情形。

全部通过：标为“代理层面通过的正式候选”，仍注明隐藏真值未验证。部分通过：说明哪一部分可用（如只用锚点）。G1 或 G3 失败：停止并报告。

## 7. 禁止事项

- 不把代理当真值，不宣称官方精度。
- 不在看到代理误差后更换主变体、ε 或 β 来报告更好的数字；探索性结果单列。
- 不使用 CK_k 之后的数据预测 CK_k。
- 不修改框架与正式模型，不提交到 main，不推送远程（除非用户另行要求）。
- 不删除或改写其他研究目录。
