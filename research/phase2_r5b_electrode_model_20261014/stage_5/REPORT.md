<a id="en"></a>

# Stage 5 — degradation and cell-limit diagnostics

> English · [中文](#zh)

Exposed-exploratory; every value inherits stage3's unidentified status. All32 anchor-cell LLI/LAM_NE/LAM_PE points and nominal95 profile-difference intervals are supplied, including separate Qn/Qp profiles. They are model-conditional, often prior-boundary limited, and not physical inventory measurements. Reference changes are exactly zero by definition. Negative LAM values imply apparent material growth in the fit, which is a warning about OCP/temperature/nuisance mismatch, not evidence of regeneration.

The figure and CSV show uncertainty dominating the fitted mode trajectories. The model's LLI/observed anchor-charge-loss ratio is provided only as an unvalidated numerical comparison with V2's68–79% step-to-top share. The model's total C20 loss fraction is unavailable because the reference passive CCCV chain is not valid. Literature expectations of LLI-dominated LFP ageing (Yagci/Bilfinger) do not establish that these cells' fitted quantities represent that mechanism.

Every CK has a limiting-cell row. CK1..7 use only the last visible anchor. CK0 is the prescribed heldout calibration. Minimum voltage at the pack11.2V root, per-cell2.8V first/second crossings, and stoichiometry-end gaps are distinguished. None substitutes the single weakest cell for official pack capacity. The labels are unstable/uncertified under the profile audit; round3's causal map had15 unavailable roots out of105, also offering no independent validation.

The first periodic CCCV charges span about21Ah, below the graphite/lower-plateau region; no recovery fit is permitted by coverage. The0.02→0.87Ah recovery signal from round4 remains an empirical observation that this electrode model cannot attribute to irreversible ageing or reversible lithium redistribution.

Files: S5_modes_per_cell.csv, S5_health_component_intervals.csv, S5_material_profiles.csv, S5_degradation_modes.png, S5_limiting_cells.csv, S5_mode_share_comparison.csv and S5_recovery_coverage.csv.

---

<a id="zh"></a>

# Stage 5 — degradation and cell-limit diagnostics

> [English](#en) · 中文

已曝光探索性研究；每个数值均继承阶段3不可辨识状态。提供全部32个锚点-电芯的 LLI/LAM_NE/LAM_PE 拟合点与名义95剖面差分区间，另补 Qn/Qp 剖面。它们依赖模型，常受参数先验边界限制，不是实际电极库存测量。参考变化按定义精确为零。负 LAM 是拟合中表观材料增长，提示 OCP/温度/干扰失配，不证明电池再生。

图和表显示不确定性远大于模式轨迹。模型 LLI/实测锚点充入量损失的比值，只与 V2 68–79% 台阶到顶端份额做未验证数值比较；参考被动 CCCV 链无效，无法给出模型 C20 总损失的真实模式份额。Yagci/Bilfinger 文献中 LFP 老化以 LLI 为主的预期，不能证明这些拟合量对应本电池组机制。

每个 CK 都有一行限制电芯诊断，CK1..7只用此前最后可见锚点，CK0为规定留出标定。明确区分组端11.2V时最低芯压、逐芯2.8V首个/第二个到达点及化学计量末端间隔，不以最弱单芯替代官方组容量。剖面审计下这些标签不稳定/未认证；第三轮因果映射105例有15个不可求根，也不提供独立验证。

首次周期性 CCCV 仅覆盖约21Ah，低于石墨台阶和下平台范围，覆盖退出规则不允许恢复拟合。第四轮0.02→0.87Ah恢复信号仍是经验观察，本电极模型无法把它归因为不可逆老化或可逆锂再分布。

文件包括模式、健康参数区间、材料剖面、退化图、限制电芯、份额比较及恢复覆盖表。
