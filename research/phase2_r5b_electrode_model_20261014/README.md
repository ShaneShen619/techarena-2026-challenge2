<a id="en"></a>

# Round5B electrode-model study

> English · [中文](#zh)

**Keep V2; no electrode-model candidate qualifies.** This exposed-exploratory study completes stages 0–3,5,6 and skips stage4 by the committed identifiability exit. CK0 scalar calibration passes, but the anchor chain and real target intervals are unsupported. Proxies are not hidden capacity truth.

Start with [FINAL_REPORT.md](FINAL_REPORT.md), then [STATUS](notes/STATUS.md), [decisions](notes/DECISIONS.md) and [execution specification](EXECUTION_PROMPT.md). Stage1's [verified clarification](stage_1/REPORT_VERIFIED.md) qualifies legacy implementation claims. Stage2 separates CK0 fitted-start success from chain failure; stage3 provides profiles and exit; stage4 records no E1/E3; stage5 provides uncertain degradation/cell/recovery diagnostics.

The final report contains all six synthetic recovery quantities, OCP provenance/licence, baseline metrics at all three offsets, per-checkup errors, all variants' explicit not-evaluated status, limiting-cell gaps, recovery coverage, risks and exact reproduction commands. [Completion evidence](stage_6/outputs/completion_evidence.json) and [14 admissible capacity endpoints](stage_6/outputs/capacity_witnesses.json) provide numerical audit evidence. The figure is [S5_degradation_modes.png](stage_5/outputs/S5_degradation_modes.png).

From this worktree's study directory, run `python3 -B stage_6/audit_completion.py --post-commit` for clean/pushed delivery checks, or `python3 -B stage_6/audit_completion.py` to recheck frozen numerical outputs without refitting. Run `python3 -B stage_6/write_final.py` to regenerate report/README/status. Full numerical reproduction is documented in the final report; it intentionally reruns analyses and cannot recreate historical registration timing. Research dependencies are recorded in stage_6/outputs/environment.json. PyBaMM is needed only to regenerate OCP tables. There is no candidate class because the eligibility exit failed.

Only `/Users/shane/Desktop/Arena_1014_r5b_electrode` and branch `exp/phase2-r5b-electrode-model-20261014` are used. All new tracked files belong here; cache/ is ignored. No submission or earlier-study tracked files are changed.

---

<a id="zh"></a>

# Round5B electrode-model study

> [English](#en) · 中文

**保留V2，没有电极模型候选合格。** 本轮为已曝光探索性（exposed-exploratory）；完成阶段0–3、5、6，按已提交可辨识性退出规则跳过阶段4。CK0标量标定通过，但锚点链条及真实目标区间不受支持。代理不是隐藏容量真值。

先读[FINAL_REPORT.md](FINAL_REPORT.md)，再看[STATUS](notes/STATUS.md)、[决策](notes/DECISIONS.md)、[执行规范](EXECUTION_PROMPT.md)。阶段1[核验澄清](stage_1/REPORT_VERIFIED.md)限定旧实现表述；阶段2区分CK0单独起点成功与完整链失败，阶段3提供剖面退出，阶段4记录无E1/E3，阶段5提供有不确定性的模式/限制电芯/恢复诊断。

最终报告包含六类合成恢复误差、OCP来源及许可证、三种偏置下基线指标、逐检查点误差、全部变体未评估状态、限制电芯间隔、恢复覆盖、风险和精确复现命令。[完成证据](stage_6/outputs/completion_evidence.json)和[14个允许容量端点](stage_6/outputs/capacity_witnesses.json)提供数值核验。[诊断图](stage_5/outputs/S5_degradation_modes.png)亦已提供。

在本worktree研究目录用`python3 -B stage_6/audit_completion.py --post-commit`查干净/推送交付；用`python3 -B stage_6/audit_completion.py`不重拟合核验冻结数值。`python3 -B stage_6/write_final.py`重建报告/README/状态。完整复现命令见报告，会主动重跑分析，不能重建历史登记时间顺序；环境见stage_6/outputs/environment.json。只有重新生成OCP表才需PyBaMM。资格退出不通过，不生成候选类。

只用`/Users/shane/Desktop/Arena_1014_r5b_electrode`及分支`exp/phase2-r5b-electrode-model-20261014`；新增跟踪文件均在本研究，cache/忽略。不改提交包或旧研究跟踪文件。
