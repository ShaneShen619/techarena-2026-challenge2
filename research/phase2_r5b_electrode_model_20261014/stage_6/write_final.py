"""Generate bilingual synthesis from frozen study outputs; no model selection."""
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
import matplotlib

STUDY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDY / 'src'))
from audit5b import bilingual, dump, update_status


def read(name):
    return json.loads((STUDY / name).read_text())


def table(frame):
    cols = list(frame.columns)
    lines = ['| ' + ' | '.join(cols) + ' |', '| ' + ' | '.join(['---'] * len(cols)) + ' |']
    for row in frame.itertuples(index=False, name=None):
        vals = []
        for value in row:
            if isinstance(value, (float, np.floating)):
                vals.append(f'{value:.6f}' if np.isfinite(value) else 'unavailable')
            else:
                vals.append(str(value))
        lines.append('| ' + ' | '.join(vals) + ' |')
    return '\n'.join(lines)


if __name__ == '__main__':
    synth = read('stage_1/outputs/S1_synthetic_summary.json')
    samples = pd.read_csv(STUDY / 'stage_1/outputs/S1_synthetic.csv')
    ck0 = read('stage_2/outputs/S2_ck0_check.json')
    audit = read('independent/outputs/audit.json')
    fit = pd.read_csv(STUDY / 'stage_3/outputs/S3_main_fits.csv')
    packs = pd.read_csv(STUDY / 'stage_3/outputs/S3_pack_intervals.csv')
    metrics = pd.read_csv(STUDY / 'stage_4/outputs/S4_baseline_metrics.csv')
    pseudo = pd.read_csv(STUDY / 'stage_4/outputs/S4_baseline_pseudo_decision_scope.csv')
    errors = pd.read_csv(STUDY / 'stage_4/outputs/S4_baseline_errors.csv')
    modes = pd.read_csv(STUDY / 'stage_5/outputs/S5_mode_share_comparison.csv')
    limits = pd.read_csv(STUDY / 'stage_5/outputs/S5_limiting_cells.csv')
    recovery = pd.read_csv(STUDY / 'stage_5/outputs/S5_recovery_coverage.csv')
    source = read('ocp/ocp_meta.json')
    env = {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__,
           'scipy': scipy.__version__, 'matplotlib': matplotlib.__version__, 'pybamm_ocp': source['pybamm_version']}
    dump(STUDY / 'stage_6/outputs/environment.json', env)
    synthesis = pd.DataFrame([
        ['Q_C20', synth['median_abs_err_Q_C20'], 'Ah'],
        ['beta_E', synth['median_abs_err_beta'], 'dimensionless'],
        ['Q_fc', synth['median_abs_err_Q_fc'], 'Ah'],
        ['LLI', synth['median_abs_err_LLI'], 'Ah'],
        ['LAM_NE fraction', audit['synthetic']['median_abs_LAM_NE_error_pct'], 'percentage points of reference electrode capacity'],
        ['LAM_PE fraction', audit['synthetic']['median_abs_LAM_PE_error_pct'], 'percentage points of reference electrode capacity'],
    ], columns=['Quantity', 'Median absolute recovery error', 'Unit'])
    synthesis.to_csv(STUDY / 'stage_6/outputs/synthetic_recovery_all_modes.csv', index=False)
    synthetic_table = table(synthesis)
    main = ck0['main_anchor0']
    variant = ck0['variant_anchor1']
    baseline_rows = []
    for model in ['M4', 'V2']:
        real = metrics[(metrics.scenario == 'real') & (metrics.model == model)].sort_values('delta')
        pv = pseudo[pseudo.model == model].set_index('scenario').MAE
        baseline_rows.append([model, 7, ' / '.join(f'{v:.6f}' for v in real.MAE),
                              ' / '.join(f'{v:.6f}' for v in real.MAX),
                              ' / '.join(f'{v:.6f}' for v in real.RMSE), float(real.iloc[1].CK2_7_MAE),
                              ' / '.join(f'{pv[k]:.6f}' for k in ['PG1', 'PG2', 'PC5', 'PC10']), float(pv.mean()),
                              'context only; no R5B selection'])
    for name in ['E1 main', 'E1 shrink tau=1', 'E1 anchor1 reference', 'E1 Ecker2015 graphite', 'E1 dV/dQ residual']:
        baseline_rows.append([name, 0, 'not evaluated', 'not evaluated', 'not evaluated', 'not evaluated',
                              'not evaluated', 'not evaluated', 'stage3 registered exit; all 7 application gates not run'])
    baseline_table = table(pd.DataFrame(baseline_rows, columns=['Model', 'n', 'MAE delta0 / .4 / .8',
                        'MAX delta0 / .4 / .8', 'RMSE delta0 / .4 / .8', 'epsilon-free CK2–7 MAE',
                        'PG1 / PG2 / PC5 / PC10 MAE (k>=3)', 'Mean pseudo MAE', 'Gate status']))
    capacity_table = table(packs.loc[packs.anchor >= 1, ['anchor', 'Q_C20_lower_witness', 'Q_C20_upper_witness',
                                      'Q_C20_width_witness', 'Q_C20_missing', 'denominator_includes_zero']])
    mode_table = table(modes[['anchor', 'LLI_point', 'LAM_NE_point', 'LAM_PE_point', 'LLI_over_observed_anchor_loss']])
    limit_table = table(limits[['k', 'state_anchor', 'minimum_voltage_cell_at_pack_root', 'first_2p8V_cell',
                                  'second_2p8V_gap_Ah', 'first_stoichiometry_end_cell', 'second_stoichiometry_end_gap_Ah']])
    reproduction = '''```bash
cd /Users/shane/Desktop/Arena_1014_r5b_electrode
export MPLCONFIGDIR="$PWD/research/phase2_r5b_electrode_model_20261014/cache/matplotlib"
cd research/phase2_r5b_electrode_model_20261014
# Audit delivered outputs without refitting; clean/pushed branch required:
python3 -B stage_6/audit_completion.py --post-commit
# Independently re-check frozen numerical outputs (no fit rerun):
python3 -B stage_6/audit_completion.py
```

Intentional full numerical reproduction, in the same designated worktree, after saving any personal changes:

```bash
# Research dependencies: versions in stage_6/outputs/environment.json.
# OCP environment, only if absent:
/opt/homebrew/bin/python3.11 -m venv cache/venv_ocp
cache/venv_ocp/bin/pip install pybamm==26.10.1.0
cache/venv_ocp/bin/python -B stage_1/tabulate_ocp.py
python3 -B stage0_reproduce.py
python3 -B stage_1/fit_1c.py
python3 -B stage_1/synthetic_1d.py
python3 -B stage_2/run_2.py
python3 -B independent/run_audit.py
# Start a new 5400-second computation budget for this intentional rerun.
# The historical runtime file must not make run_fits exit immediately.
python3 -B -c 'from pathlib import Path; Path("stage_3/outputs/runtime.json").unlink(missing_ok=True)'
python3 -B stage_3/run_fits.py
python3 -B stage_3/run_profiles.py
python3 -B stage_4/run_exit.py
python3 -B stage_5/run_diagnostics.py
python3 -B stage_6/write_final.py
python3 -B stage_6/audit_completion.py
```

The OCP-source verification was also performed against installed function values, with maximum CSV rounding error below 5.1e-9 V; source and CSV hashes are in [ocp_provenance_verified.json](stage_6/outputs/ocp_provenance_verified.json). All caches belong to this worktree; extraction uses its private earlier-study cache. Cached scientific fits include inputs, protocols, OCP/source and fixed-parameter hashes; original legacy stage2 snapshots are retained as provenance. `all_main_fits.pkl` is a write-only aggregation snapshot, not a lookup cache. Reproduction preserves scientific definitions, not historical wall times, git pre-registration order or guaranteed optimizer bit identity across platforms. No candidate environment is needed because no model is eligible.'''
    en = f'''**Keep V2. The literature-electrode model does not identify the target capacity or mechanistic beta on these real anchors. No E1/E3 prediction or new candidate is produced.** Stages 0–3, 5 and 6 are completed; stage4 is skipped by its committed exit rule. These are **exposed-exploratory** results: only CK0 has a released capacity label; CK1–CK7 proxies are not hidden truth. The submission package and earlier studies remain unchanged.

The main CK0 scalar check passes (100.698604 Ah, +0.288604 Ah), but this uses a separately fitted discharge start. It does not validate the anchor-CCCV-to-C/20 chain. For real anchors1–7, admitted parameter combinations already differ by 8.101–10.516 Ah, versus the 0.6-Ah gate, and all beta denominator envelopes contain zero. The appropriate outcome is a documented negative result, not a fitted mechanistic replacement for V2.

## OCP sources and synthetic experiment

PyBaMM **26.10.1.0**, BSD-3-Clause: `Prada2013.LFP_ocp_Afshar2017`, `Chen2020.graphite_LGM50_ocp_Chen2020` (main), and `Ecker2015.graphite_ocp_Ecker2015` (registered alternative). Each table has 1001 stoichiometry points, 0..1 at 0.001 spacing. Functions were inspected locally and their output rechecked against the CSVs. See [sources](ocp/SOURCES.md), [metadata](ocp/ocp_meta.json), [full licence](ocp/PyBaMM_LICENSE.txt). None was measured on this pack.

All 30 surrogate synthetic states yield finite fitted/true target quantities. Recovery errors are:

{synthetic_table}

The numerical Q_C20/beta thresholds pass (<=0.2 Ah / <=0.10). **This is a surrogate experiment, not a faithful test of the requested measured-current replay.** The original simulation uses generated 20.4-A CCCV at 10-s sampling instead of anchor1's measured current; start OCV shifts are uniform±30mV rather than sampled directly from observed start voltages. The pack simulation likewise uses ideal CCCV instead of the full measured-current trajectory. Noise is 2 mV white+2mV AR(1), rho=.9, plus uniform±3mV per-cell offset. Six states have true step shifts below 0.5Ah, so beta is ill-conditioned. The result cannot validate the OCPs on these cells. All six requested recovery quantities, with LAM in explicitly labelled fractional units, are now reported. [Verified stage1 clarification](stage_1/REPORT_VERIFIED.md) supersedes stronger claims in the preserved original report.

## CK0: the only true-label check

Health is fitted to 45°C anchor0 using 25°C literature OCPs. CK0 temperature is unavailable and assumed 25°C. Discharge-side eta and start lithiation are fitted only on **5–85.412 Ah**; the last 15Ah are prediction diagnostics and never fit data.

Main predicted root: **100.698604 Ah**, versus 100.41 (+0.288604) and the earlier bounded-extension root100.416854 (+0.281750). Four cell step errors are 0.218/0.044/0.235/0.132Ah, all within1Ah. Thus the registered scalar credibility gate passes. Heldout-tail RMS is 23.399/23.930/25.773/24.131mV; cell 3 has the minimum voltage at the group root. Anchor1-reference variant predicts 107.476813Ah (+7.066813), with54.6–60.7mV tail RMS, and fails the gate.

**The full anchor chain is unsupported.** The legacy anchor0 chain gives 102.398747Ah and epsilon_sim(0)=2.276360Ah versus observed epsilon0=0.287614 Ah. It floors total fitted R={sum(x[4] for x in main['ref_fit']):.9f}Ohm to 1e-6 in its CV equation, which is not a valid passive taper. Stage3 rejects this chain and reports the target unavailable. A separately fitted CK0 start can pass a scalar gate despite this chain problem. [Stage2 report](stage_2/REPORT.md), [all numbers](stage_2/outputs/S2_ck0_check.json).

## Identifiability and registered exit

All 32 main fits and 1266 fixed-QLi nuisance refits are supplied, with per-cell RMS, R/h, starting theta, mode changes, residual autocorrelation and n_eff. Main n_eff spans{fit.n_eff.min():.2f}–{fit.n_eff.max():.2f}, far below the raw10-s sample counts. Profiles use residual autocorrelation, sigma=max(2mV,RMS), and Bonferroni-adjusted per-cell nominal 95 envelopes for the pack. These are conditional on the misspecified OCP/nuisance model, not calibrated confidence limits.

{capacity_table}

Finite extrema above are **admissible witnessed spans, hence lower bounds on full nominal-box widths**, not complete 95 intervals. Full boxes contain about 0.73–0.92million combinations each; the preregistered deterministic design samples about 1180 with all single-cell excursions and parameter extrema. Hundreds have unavailable roots. A finite full 95 capacity range is therefore unsupported, and no narrow interval is certified. Exact parameter witnesses for the lower/upper values and domain-valid11.2V roots are in [capacity_witnesses.json](stage_6/outputs/capacity_witnesses.json).

The [pack table](stage_3/outputs/S3_pack_intervals.csv) also supplies Q_fc,sim−Q_fc,obs envelopes and beta numerator/denominator support. Every denominator envelope includes zero; no finite beta range <=0.3 is certified. **0/7** anchors pass either target-identification gate, versus at least 5/7 required for each. Fitted LLI points and their intervals admit monotonicity, but LLI/start-voltage correlation r=0.454717 is descriptive and does not establish a mechanism. QLi/Qn/Qp intervals often hit prior bounds. [Stage3 report](stage_3/REPORT.md), [exit record](stage_3/outputs/S3_exit.json).

## E1, variants and contextual baselines

The registered stage3 exit skips the entire stage4 application. **E1 and all four variants are not evaluated; E3 has no leaderboard-only SOH table; all 7 candidate/application gates are not run.** No alternative is silently substituted. A numpy/pandas-only candidate and its G-causal/G-impl tests are conditional on passing all gates, so no candidate class is required or generated.

The following are copied, independently checked M4/V2 context, not new R5B model scores. Errors are SOH percentage points; real scenarios use 7 checks and delta=0/.4/.8. Pseudo columns use PG1/PG2 k4..7 and PC5/PC10 k3..7 (CK2 excluded from decision scope).

{baseline_table}

Per-checkup real errors at delta=.4:

{table(errors)}

E1 and every variant have unavailable per-checkup errors by the registered exit. Full contextual pseudo reporting including PC CK2 is in [metrics](stage_4/outputs/S4_baseline_metrics.csv); the decision-scope table above uses [k>=3 pseudo metrics](stage_4/outputs/S4_baseline_pseudo_decision_scope.csv). There is no new proxy selection, and no claim of improving hidden truth or epsilon. [Stage4 exit report](stage_4/REPORT.md).

## Degradation, limiting cells and recovery

**Every number in the following diagnostics is unidentified/model-conditional.** Complete32 per-cell trajectories and nominal 95 profile-difference ranges are in [mode table](stage_5/outputs/S5_modes_per_cell.csv), with 1916 additional fixed-Qn/Qp refits and 96 component intervals. Component/reference differences use 97.5% intervals to form nominal 95 differences; reference0 is exactly zero by definition. These remain discrete grid ranges, often boundary-limited, not inventory measurements.

![Unidentified electrode degradation profiles](stage_5/outputs/S5_degradation_modes.png)

Means across cells (Ah), for descriptive comparison only:

{mode_table}

The negative LAM_PE near−92.59Ah comes from Qp changing from about107Ah to its200Ah upper bound. It is apparent material growth caused by fit mismatch, not physical regeneration. LLI/observed anchor-charge loss is1.37–1.82, which cannot be treated as a validated total-capacity decomposition or equated with V2's68–79% step-to-top fraction. A model C20 total-loss share is unavailable because the reference chain is invalid. The LLI-dominant expectation cited in the task's Yagci2025/Bilfinger2024 literature background does not validate these fitted modes.

Checkup diagnostics use the last visible anchor for CK1..7; CK0 is the prescribed heldout calibration. All are **uncertified**, and CK1 is unavailable due to the invalid reference chain. Minimum-voltage cell at pack 11.2V, per-cell 2.8V threshold crossings and stoichiometric-domain endpoints are distinct:

{limit_table}

The second-cell gap is shown separately for2.8V and the domain endpoint; neither replaces the official four-cell 11.2V capacity. Cell3 is the CK0 point limiter and cell 1 the CK2–7 point limiter, with no uncertainty-certified stable label. Round3's causal mapping had15/105 unavailable roots and offers no independent validation. [Full cell table](stage_5/outputs/S5_limiting_cells.csv).

All 8 first periodic CCCV events span only{recovery.charge_depth_Ah.min():.3f}–{recovery.charge_depth_Ah.max():.3f}Ah, at{recovery.days_after_anchor.min():.2f}–{recovery.days_after_anchor.max():.2f}days after the anchor. None reaches the required 45Ah graphite/lower-plateau coverage, so **no recovery fit is permitted**. This model cannot attribute round4's empirical0.02→0.87Ah recovery to irreversible ageing or reversible redistribution. [Coverage](stage_5/outputs/S5_recovery_coverage.csv), [stage5 report](stage_5/REPORT.md).

## Deviations, risks and scope

- Proxies have already been exposed; pseudo scenarios reuse one pack and add no independent hidden labels. No CK1–CK7 true capacity was reconstructed.
- Literature OCPs are not from these cells. A45°C reference is compared with25°C OCPs; CK0 has no measured temperature. A beta from25°C OCPs applied to 45°C programs would assume cancellation in phase differences, which was not validated.
- The checkup full-charge state being the same as operating-anchor CCCV is an assumption, and the chain diagnostic does not support it. Constant eta_dis fitted at CK0 does not establish transfer under ageing. Epsilon and post-checkup recovery remain unresolved by proxies.
- Original synthetic measured-current replay and observed-start-range requirements were not followed exactly. Ideal-current simulation was a registered simplification; the surrogate synthetic generator departed from the protocol's replay line and was disclosed after the computation. These are deviations, not original faithful implementation.
- The144-start solver runs60-evaluation coarse searches then refines the best3; a development anchor1 fit preceded stage1 registration (fit quality only, not a proxy selection). Original fitting used soft domain penalties and np.interp endpoint clipping, and legacy CCCV used a negative-R floor. These violate hard rejection for arbitrary states. Preserved legacy results are qualified; stage3 onward hard-checks every accepted domain and never promotes clipped/invalid target roots. Continuous endpoint bisection and frozen reference R/h/start-OCV for health-only beta were registered before stage3 computation.
- Original shared files and protocols were preserved after concurrent work was detected. Later independent audit/clarification does not rewrite earlier pre-registration history. The source history proves protocol files preceded their evaluation-artifact commits; it does not erase the explicitly disclosed development fit or current-profile deviations.
- Available discrete profiles/witnesses do not identify tight95 target intervals. Nonidentifiability rejects this implementation; it does not prove that electrode modelling with pack-specific OCPs and independent same-protocol labels could never work.

## Reproduction and completion evidence

{reproduction}

[Requirement audit](stage_6/outputs/requirements_audit.json) maps 35 scoped obligations and conditional exits. [Completion evidence](stage_6/outputs/completion_evidence.json) checks full grid coverage, all fit/profile domain flags and effective-sample statistics, 14 explicit capacity endpoints, heldout CK0 predictions, baseline metrics, bilingual reports and protected tracked paths. [Status](notes/STATUS.md) records all seven numbered stages. All protocol hashes are checked against distinct earlier ancestor commits; stage6 ordering, clean study status and remote/local HEAD equality are checked after final push using `--post-commit`.

Branch: `exp/phase2-r5b-electrode-model-20261014`. Only this study changes relative to `a6bc61f`; no submission wiring or other-branch push. No stage exhausted its computation cap in the recorded stage3/5/6 runtime evidence; earlier stages are completed with the deviations above, not claimed as exact implementations.'''
    zh = f'''**保留 V2。文献电极模型在这些真实锚点上无法辨识目标容量或机理 β，不生成 E1/E3 预测及新候选。** 阶段0–3、5、6已完成；阶段4按已提交退出规则跳过。本轮是**已曝光探索性研究（exposed-exploratory）**：只有 CK0 有公开容量标签，CK1–CK7代理不是隐藏真值。提交包和此前研究保持不变。

CK0 主标量检查通过（100.698604Ah，偏差+0.288604Ah），但使用单独拟合的放电起点，不能验证“锚点CCCV→C/20”的完整链条。真实锚点1–7的允许参数组合之间容量已相差8.101–10.516Ah，远超0.6Ah门槛；全部 β 分母包络包含零。因此结论是有证据的负面结果，不用机理拟合替换 V2。

## OCP 来源与合成实验

PyBaMM **26.10.1.0**，BSD-3-Clause：正极`Prada2013.LFP_ocp_Afshar2017`；石墨主配置`Chen2020.graphite_LGM50_ocp_Chen2020`；登记备选`Ecker2015.graphite_ocp_Ecker2015`。三表均为0..1、间隔0.001、1001点。已检查安装函数并重核表值，最大舍入误差低于5.1e-9V。[来源](ocp/SOURCES.md)、[元数据](ocp/ocp_meta.json)、[完整许可证](ocp/PyBaMM_LICENSE.txt)。曲线均非来自本电池组。

30个替代合成状态的真实/拟合目标量均有限，六类恢复误差及材料损失比例误差如下：

{synthetic_table}

Q_C20/β数值门通过（<=0.2Ah / <=0.10）。**这是替代合成实验，并非按要求精确回放实测电流的试验。** 原生成器用10s步长、自身20.4A CCCV，未用锚点1实测电流；起点为±30mV均匀扰动，未直接从实测起始电压范围抽样。组端模拟同样用理想CCCV而非完整实测电流轨迹。噪声为2mV白噪声+2mV、rho=.9的AR(1)+每芯±3mV常数。6个状态的真实台阶变化不足0.5Ah，β病态。不能据此验证文献OCP适用于本电芯。[阶段1核验澄清](stage_1/REPORT_VERIFIED.md)替代原报告中更强的表述。

## CK0：唯一真实标签检查

健康参数来自45℃锚点0，使用25℃文献OCP；CK0温度缺失，假设25℃。仅用**5–85.412Ah**拟合放电侧η和起始嵌锂度，最后15Ah只预测、不参与拟合。

主首根**100.698604Ah**，相对100.41偏差+0.288604，相对已有有界外延首根100.416854偏差+0.281750。四芯台阶误差0.218/0.044/0.235/0.132Ah，均小于1Ah，登记的标量可信度门通过。留出尾段RMS为23.399/23.930/25.773/24.131mV；组端首根时最低压为电芯3。锚点1参考变体预测107.476813Ah，误差+7.066813，尾段54.6–60.7mV，不通过。

**完整锚点链条不受支持。** 旧锚点0链条给出102.398747Ah，ε_sim(0)=2.276360Ah，而公开ε0=0.287614Ah。其总拟合R={sum(x[4] for x in main['ref_fit']):.9f}Ohm为负，却被旧CV公式截成1e-6，不构成有效被动恒压递减。阶段3拒绝该链条并报告目标不可得；独立CK0起点的标量通过不能消除这一问题。[阶段2报告](stage_2/REPORT.md)、[完整数值](stage_2/outputs/S2_ck0_check.json)。

## 可辨识性与登记退出

完成32个主拟合及1266个固定QLi后重拟合干扰参数的剖面；逐芯RMS、R/h、起始theta、模式变化、残差自相关和n_eff均已提供。主n_eff仅{fit.n_eff.min():.2f}–{fit.n_eff.max():.2f}，远少于原始10s点数。使用残差自相关、sigma=max(2mV,RMS)，以及Bonferroni逐芯包络组合名义95组参数盒；是失配模型条件诊断，并非校准后的置信限。

{capacity_table}

表中有限跨度是**允许组合的见证跨度，即完整名义参数盒宽度的下界**，不是完整95区间。完整盒每个约73–92万组合；按预登记设计取约1180组合，含全部单芯扰动及参数极值。数百组不可求根，不能报告完整有限95容量范围或认证窄区间。上下端点的具体参数及有效域内11.2V根见[见证证书](stage_6/outputs/capacity_witnesses.json)。

[组端表](stage_3/outputs/S3_pack_intervals.csv)同时提供Q_fc,sim−Q_fc,obs包络及β支持信息。全部分母包络含零，没有可认证宽度<=0.3的有限β区间。两项目标门均为**0/7**通过，要求各至少5/7。LLI点及区间容许单调，LLI与起始组压r=0.454717只作诊断，不证明机理；QLi/Qn/Qp区间常触及参数边界。[阶段3报告](stage_3/REPORT.md)、[退出记录](stage_3/outputs/S3_exit.json)。

## E1、变体与背景基线

阶段3登记退出规则跳过整个阶段4。**E1及四个变体均未评估，E3没有排行榜SOH表，七项候选/应用门均未运行。** 不替换成其他模型。仅全部门通过才要求numpy/pandas候选及G-causal/G-impl证据，本轮不构建候选。

下表M4/V2是复制并独立核验的背景值，不是本轮新增模型成绩。误差单位为SOH百分点，真实场景7个检查点、Δ=0/.4/.8；伪情景PG1/PG2用k4..7，PC5/PC10用k3..7，决策范围排除CK2。

{baseline_table}

Δ=.4逐检查点实际代理误差：

{table(errors)}

E1及各变体按退出规则无逐点误差。含PC场景CK2的完整背景统计见[总指标](stage_4/outputs/S4_baseline_metrics.csv)，表中决策范围见[k>=3伪场景表](stage_4/outputs/S4_baseline_pseudo_decision_scope.csv)。没有新代理选择，不声称改善隐藏真值或ε。[阶段4退出报告](stage_4/REPORT.md)。

## 退化模式、限制电芯与恢复

**以下诊断所有数值均不可辨识、依赖模型。** [逐芯模式表](stage_5/outputs/S5_modes_per_cell.csv)包含32行轨迹和名义95剖面差分范围，另有1916个Qn/Qp固定剖面及96个分量区间。参考与当前各用97.5%区间组合名义95差分，参考0按定义精确为零。区间仍是离散网格范围，常受边界限制，不是实际库存测量。

![不可辨识的电极退化诊断](stage_5/outputs/S5_degradation_modes.png)

四芯均值（Ah），仅描述性对照：

{mode_table}

LAM_PE约−92.59Ah来自Qp从约107Ah变到200Ah上界，是失配造成的表观材料增长，不是再生。LLI/实测锚点充入量损失为1.37–1.82，不能当作已验证总容量损失分解，也不能等同V2的68–79%台阶到顶端份额。参考链无效，模型C20总损失份额不可得。任务给出的Yagci2025/Bilfinger2024文献中LLI主导预期不能验证这些拟合模式。

CK1..7只用此前最后可见锚点，CK0为规定的留出标定；所有限制电芯诊断均**未认证**，CK1因参考链无效而不可得。区分组端11.2V时最低压芯、逐芯2.8V及化学计量域末端：

{limit_table}

分别列出第二芯到2.8V和域末端的Ah间隔，均不替代官方四芯11.2V容量。CK0点限制为芯3，CK2–7为芯1，不证明标签在不确定性下稳定。第三轮映射105组有15组不可求根，不提供独立验证。[完整限制电芯表](stage_5/outputs/S5_limiting_cells.csv)。

首次周期CCCV共8个，只跨{recovery.charge_depth_Ah.min():.3f}–{recovery.charge_depth_Ah.max():.3f}Ah，距锚点{recovery.days_after_anchor.min():.2f}–{recovery.days_after_anchor.max():.2f}天。全部未到45Ah石墨/下平台要求，**覆盖退出不允许恢复拟合**。不能解释第四轮0.02→0.87Ah经验恢复来自不可逆老化还是可逆再分布。[覆盖表](stage_5/outputs/S5_recovery_coverage.csv)、[阶段5报告](stage_5/REPORT.md)。

## 偏差、风险与范围

- 代理已曝光；伪情景复用单电池组，不增加独立隐藏标签；未重建CK1–CK7真实容量。
- 文献OCP并非本电芯；45℃参考对25℃OCP；CK0无测温。若将25℃OCP的β用于45℃程序，还需假设温度效应在同相位差分抵消，本轮未验证。
- “检查满充=运行锚点CCCV”是假设，链条诊断不支持它。CK0常数放电η不证明老化后可迁移；ε及检查后恢复仍不能由代理验证。
- 未精确执行合成实测电流回放和实测起点抽样。理想电流模拟是登记简化；合成生成器另偏离协议回放条款，计算后披露，不能称原实验忠实实现。
- 144起点先各60评估、再细化最优3；阶段1登记前有锚点1开发拟合，只看拟合质量、未用代理选择。原拟合用软域罚项/np.interp端点截值，旧CCCV还用负电阻下限，任意状态不满足硬拒绝。保留旧产物但限定其解释；阶段3起对接受域硬检查，不提升截值/无效根。连续端点求根、健康β固定参考R/h及起始OCV在阶段3前登记。
- 发现并发工作后保留原文件/协议。后续独立审计不改写早期预登记；git可证明协议先于评估产物提交，不抹除开发拟合与电流偏差。
- 离散剖面和见证不能辨识紧致95目标范围；负面结果针对该实现，不证明专用OCP及独立同协议标签下的电极模型永远不可行。

## 复现与完成证据

以下命令均在指定worktree运行。第一组核验交付及冻结数值，不重新拟合；第二组仅用于主动完整复现。阶段3历史runtime必须重置，否则会因旧起始时间立即退出。复现不能重建历史预登记顺序、耗时，或保证不同平台优化器逐位一致。

{reproduction}

[逐项审计](stage_6/outputs/requirements_audit.json)列出35项范围义务及条件退出。[完成证据](stage_6/outputs/completion_evidence.json)核验全部网格、拟合/剖面有效域及有效样本统计、14个容量端点、CK0留出预测、基线指标、双语产物及受保护路径。[状态](notes/STATUS.md)列出全部七个编号阶段。所有协议哈希检查其早于评估提交；阶段6最终顺序、研究目录干净、远端HEAD一致由推送后的`--post-commit`只读审计核验。

分支`exp/phase2-r5b-electrode-model-20261014`；相对`a6bc61f`仅改本研究，不接提交包、不推其他分支。阶段3/5/6记录的计算耗时未到上限；更早阶段以披露偏差后的完成结果报告，不声称原要求全部精确实现。'''
    bilingual(STUDY / 'FINAL_REPORT.md', 'Round 5B — electrode model: final report', en, zh)
    clarification_en = f'''**Surrogate synthetic numerical gates pass; real-electrode interpretation remains unsupported.** Exposed-exploratory; no hidden labels. This clarification qualifies the preserved original [REPORT.md](REPORT.md): the electrode equations match, but the complete implementation does not exactly meet the current-replay and hard-domain rules.

{synthetic_table}

All 30 states are finite. LAM recovery uses the saved per-cell-normalized fraction errors in percentage points; the original run did not retain per-state individual electrode fits, so exact mean-cell Ah recovery errors cannot be reconstructed and are not invented. The synthetic input is model-generated10-s CCCV, not the specified measured anchor1 current. The start shift is uniform±30mV, not an empirical observed-start-range sample. Therefore the numeric gate is a surrogate pass, not confirmation of the exact prescribed experiment or these cells' mechanism.

The144-start two-phase solver, ideal-current CCCV, development fit before registration, soft state penalties, endpoint clipping and negative-total-R floor are disclosed in the final report. The independent invalid-theta test produced a finite legacy charge despite theta_n0=1.2; legacy simulation is unsuitable for arbitrary accepted targets. Stage3 preregistered strict domain rejection and rejects the negative-R anchor0 chain. Completed originals are preserved, not overwritten or retroactively called compliant.

OCP source version/functions and full BSD-3 licence are in [../ocp/](../ocp/). Anchor1 main/alternative/dVdQ fits hit Qp200Ah and have strongly autocorrelated residuals. These observations suggest mismatch/confounding, not unique evidence of an ageing mechanism. See [final report](../FINAL_REPORT.md) for the CK0/free-start versus full-chain distinction and registered no-model exit.'''
    clarification_zh = f'''**替代合成实验的数值门通过，真实电极机理仍无支持。** 已曝光探索性（exposed-exploratory），无隐藏标签。本澄清限定保留的原[REPORT.md](REPORT.md)：电极方程相同，不代表完整实现精确满足电流回放和硬有效域要求。

{synthetic_table}

30状态均有限。LAM恢复误差用原保存的逐芯归一比例，以百分点报告；原运行未保留各状态逐芯电极拟合，不能重建精确平均Ah恢复误差，也不编造。合成输入为自身10s CCCV，非要求的锚点1实测电流；起点±30mV均匀扰动，非实测起点范围抽样。因此只称替代数值门通过，不确认原实验或真实电芯机制。

144起点分段搜索、理想电流CCCV、登记前开发拟合、软域罚项、端点截值及负总R下限均在最终报告披露。独立测试theta_n0=1.2仍得到有限旧充电结果，故旧模拟器不能用于任意接受目标。阶段3预登记硬域拒绝并拒绝负R锚点0链；保留原完成文件，不覆盖，也不事后称其合规。

OCP函数版本及完整BSD-3许可证见[../ocp/](../ocp/)。锚点1主/备选/dVdQ拟合撞Qp200Ah边界、残差强自相关，提示失配/混淆，不能唯一证明退化机制。完整CK0起点与链条区别及登记退出见[最终报告](../FINAL_REPORT.md)。'''
    bilingual(STUDY / 'stage_1/REPORT_VERIFIED.md', 'Stage1 — verified interpretation and deviations', clarification_en, clarification_zh)
    readme_en = '''**Keep V2; no electrode-model candidate qualifies.** This exposed-exploratory study completes stages 0–3,5,6 and skips stage4 by the committed identifiability exit. CK0 scalar calibration passes, but the anchor chain and real target intervals are unsupported. Proxies are not hidden capacity truth.

Start with [FINAL_REPORT.md](FINAL_REPORT.md), then [STATUS](notes/STATUS.md), [decisions](notes/DECISIONS.md) and [execution specification](EXECUTION_PROMPT.md). Stage1's [verified clarification](stage_1/REPORT_VERIFIED.md) qualifies legacy implementation claims. Stage2 separates CK0 fitted-start success from chain failure; stage3 provides profiles and exit; stage4 records no E1/E3; stage5 provides uncertain degradation/cell/recovery diagnostics.

The final report contains all six synthetic recovery quantities, OCP provenance/licence, baseline metrics at all three offsets, per-checkup errors, all variants' explicit not-evaluated status, limiting-cell gaps, recovery coverage, risks and exact reproduction commands. [Completion evidence](stage_6/outputs/completion_evidence.json) and [14 admissible capacity endpoints](stage_6/outputs/capacity_witnesses.json) provide numerical audit evidence. The figure is [S5_degradation_modes.png](stage_5/outputs/S5_degradation_modes.png).

From this worktree's study directory, run `python3 -B stage_6/audit_completion.py --post-commit` for clean/pushed delivery checks, or `python3 -B stage_6/audit_completion.py` to recheck frozen numerical outputs without refitting. Run `python3 -B stage_6/write_final.py` to regenerate report/README/status. Full numerical reproduction is documented in the final report; it intentionally reruns analyses and cannot recreate historical registration timing. Research dependencies are recorded in stage_6/outputs/environment.json. PyBaMM is needed only to regenerate OCP tables. There is no candidate class because the eligibility exit failed.

Only `/Users/shane/Desktop/Arena_1014_r5b_electrode` and branch `exp/phase2-r5b-electrode-model-20261014` are used. All new tracked files belong here; cache/ is ignored. No submission or earlier-study tracked files are changed.'''
    readme_zh = '''**保留V2，没有电极模型候选合格。** 本轮为已曝光探索性（exposed-exploratory）；完成阶段0–3、5、6，按已提交可辨识性退出规则跳过阶段4。CK0标量标定通过，但锚点链条及真实目标区间不受支持。代理不是隐藏容量真值。

先读[FINAL_REPORT.md](FINAL_REPORT.md)，再看[STATUS](notes/STATUS.md)、[决策](notes/DECISIONS.md)、[执行规范](EXECUTION_PROMPT.md)。阶段1[核验澄清](stage_1/REPORT_VERIFIED.md)限定旧实现表述；阶段2区分CK0单独起点成功与完整链失败，阶段3提供剖面退出，阶段4记录无E1/E3，阶段5提供有不确定性的模式/限制电芯/恢复诊断。

最终报告包含六类合成恢复误差、OCP来源及许可证、三种偏置下基线指标、逐检查点误差、全部变体未评估状态、限制电芯间隔、恢复覆盖、风险和精确复现命令。[完成证据](stage_6/outputs/completion_evidence.json)和[14个允许容量端点](stage_6/outputs/capacity_witnesses.json)提供数值核验。[诊断图](stage_5/outputs/S5_degradation_modes.png)亦已提供。

在本worktree研究目录用`python3 -B stage_6/audit_completion.py --post-commit`查干净/推送交付；用`python3 -B stage_6/audit_completion.py`不重拟合核验冻结数值。`python3 -B stage_6/write_final.py`重建报告/README/状态。完整复现命令见报告，会主动重跑分析，不能重建历史登记时间顺序；环境见stage_6/outputs/environment.json。只有重新生成OCP表才需PyBaMM。资格退出不通过，不生成候选类。

只用`/Users/shane/Desktop/Arena_1014_r5b_electrode`及分支`exp/phase2-r5b-electrode-model-20261014`；新增跟踪文件均在本研究，cache/忽略。不改提交包或旧研究跟踪文件。'''
    bilingual(STUDY / 'README.md', 'Round5B electrode-model study', readme_en, readme_zh)
    update_status('Final synthesis complete; commit/push delivery audit remains', {
        0: ('complete; exact M4/V2 reproduction', '完成；精确复现M4/V2'),
        1: ('complete with disclosed current/state-rejection deviations; surrogate synthetic numeric pass', '完成，披露电流/状态拒绝偏差；替代合成数值门通过'),
        2: ('complete; CK0 scalar gate passes, chain unsupported', '完成；CK0标量门通过，链条不受支持'),
        3: ('complete; all 32 main fits/1266 QLi profiles; target identifiability exit fails', '完成；32主拟合/1266QLi剖面；目标可辨识退出门不通过'),
        4: ('skipped by registered stage3/stage4 exit; E1/variants/E3 not evaluated, no candidate', '按已登记阶段3/4退出跳过；E1/变体/E3未评估，无候选'),
        5: ('complete; 1916 material profiles,32 mode rows/95 ranges, figure,8 cell/recovery rows', '完成；1916材料剖面，32模式行/95区间、图、8电芯/恢复行'),
        6: ('complete; bilingual report/README and scientific audit; delivery checked by post-commit command', '完成；双语报告/README及科学审计，提交后命令核验交付')},
        ('Commit and push final artifacts; run read-only --post-commit audit; do not redo finished stages',
         '提交推送最终产物；运行只读--post-commit审计，不重做完成阶段'))
    print('Generated FINAL_REPORT, README, verified stage1 clarification, synthetic recovery table and status.')
