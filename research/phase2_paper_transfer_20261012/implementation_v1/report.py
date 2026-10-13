"""Post-score report/figure rendering only; no model selection or metric rewriting."""
import json,importlib.util,platform
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import *


def main():
    spec=importlib.util.spec_from_file_location('frozen_runner_for_report',TASK/'run.py')
    runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner);runner.verify_freeze()
    if not (TASK/'EVALUATION_COMPLETE').exists():raise RuntimeError('Formal scoring not complete')
    (TASK/'figures').mkdir(exist_ok=True)
    audit=json.loads((TASK/'audit_summary.json').read_text());decision=json.loads((TASK/'decision.json').read_text())
    forward=pd.read_csv(TASK/'forward_summary.csv');syn=pd.read_csv(TASK/'synthetic_summary.csv')
    ident=pd.read_csv(TASK/'identifiability_summary.csv');curves=pd.read_csv(TASK/'sensitivity_profile_curves.csv')
    rest=pd.read_csv(TASK/'rest_registry.csv');pulses=pd.read_csv(TASK/'pulse_registry.csv')
    paired=pd.read_csv(TASK/'paired_evaluation_metrics.csv');joint=pd.read_csv(TASK/'joint_witnesses.csv')
    pulse_validation=pd.read_csv(TASK/'pulse_forward_validation.csv')
    nchecks=json.loads((TASK/'science_checks.json').read_text())['passed']
    oldmatch=json.loads((TASK/'baseline_reproduction.json').read_text())
    lines=['# 四篇论文迁移执行报告：implementation_v1','', '执行日期：2026-10-13。正式冻结规则评分已完成；旧四方法实验和正式模型未修改。','',
    '## 结论','',
    '受论文启发的电压修正、LAD/L2联合配准、多事件共同尺度和四尺度收缩分支均已实现并比较。本轮未达到可信容量更新门；四个独立尺度没有获得充分辨识证据，不发布新的CK1–CK7 SOH。门控版本全部回退到旧主基线，因此相同误差不能解释为新方法有效。','',
    '最有价值的新证据是电流边沿未提供可辨分的同步瞬时电压变化：边沿电压常与上一条相同，9–10秒后才出现可测响应。直接逐行算IR会得到接近零的错误结果；官方材料说明重复时间戳是步骤切换标记。修正后得到的仍是包含极化/SOC变化的延迟表观电阻。','',
    '## 完成范围与公平比较','',
    f"- 原始再审核{audit['events']}条事件，29条开发、46条冻结前向评分；12个原始文件。逐事件原始积分与旧缓存最大差{audit['max_raw_Ah_discrepancy']:.3g} Ah，四芯电压与时刻逐点完全一致。",
    '- 同一已曝光物理包；不是新盲测或跨包泛化。同一个真实锚点链/物理跳变未跨开发与评分；unknown不是共同物理链，不能据名称合并。',
    '- 四组loss/修正组合：L2/LAD × free/independent；固定、单事件共同、多事件共同、收缩四尺度、自由四尺度诊断、门控共同各分支。',
    '- 前向A无目标放电电压，B最多首1Ah截距校准；2Ah后评分，历史参数available_after早于目标start。后静置不用于本事件预测。',
    '- 16类机制×10固定评分种子，共160个场景—种子组合；四组合和四种状态分支共2560行指标。配对面板5类×2种子，利用前两轨迹预测第三轨迹后缀。',
    f'- {nchecks}项数值、因果、边界及缓存检查通过。105项源码/输入依赖冻结；旧主基线复现{oldmatch["rows"]}条，最大误差差异{oldmatch["max_abs_difference_mV"]:.3g} mV。','',
    '## 阶段1：电压修正提供了什么','',
    f"- {len(pulses)}个候选跳变，{int(pulses.qualified.sum())}个满足最终延迟响应资格。初步直接逐行计数已作开发修订，不能沿用此前17/67的数量。",
    f"- {int((pulses.edge_voltage_change_mV<1).sum())}/{len(pulses)}个边沿的最大四芯变化不足1mV。响应延迟{pulses.voltage_response_delay_s.min():.0f}–{pulses.voltage_response_delay_s.max():.0f}秒；这是测量时序证据，不是瞬时R0标定。",
    '- 合格跳变全部来自约10Ah的恒流事件边界；较宽动态事件没有满足本轮稳定阶跃规则的跳变。以同面板、同温度、可见历史的最近8个测量约束有效R，并保留MAD和0.3mΩ膨胀。',
    '- CK0只有已开始的5.1A放电，没有同步阶跃前零流电压，参考电阻和真实OCV不可独立拆分。模型将当前/参考极化分开，保留参考项的不确定性。','']
    for split in ['development','evaluation']:
        for which in ['pre','post']:
            g=rest[(rest.split==split)&(rest.which==which)&rest.valid]
            lines.append(f"- {split}/{which}静置：{len(g)}条有效；前60%拟合后预测后40%，一阶恢复MAE {g.heldout_mae_mV.mean():.3f} mV，末值保持 {g.last_value_mae_mV.mean():.3f} mV；逐条更优{int((g.heldout_mae_mV<g.last_value_mae_mV).sum())}/{len(g)}。")
    if len(pulse_validation):
        g=pulse_validation[pulse_validation.split=='evaluation']
        lines.append(f'- 延迟跳变留出：{g.pulse_uid.nunique()}个物理跳变、{len(g)}个芯—跳变；历史滚动表观R预测MAE {g.prediction_error_mV.mean():.3f}mV，冻结开发中位数对照 {g.frozen_dev_baseline_error_mV.mean():.3f}mV。个别零/低误差不能证明对真实R0的精度。')
    lines += ['', '![电流和电压更新时序](figures/pulse_timing.png)','',
    '静置一阶模型未获得总体预测优势。仅对自身末值对照更优、时长/条件性合格的前静置施加振幅范围；不能将其渐近电压换成真实SOC。','',
    '## 阶段2–3：官方前向结果','', '以下为按物理事件平均的单芯MAE（mV），总分包含回退；A/B输入预算分开评价。','']
    names=['frozen_baseline','legacy_fixed','L2_free_multi_common','L2_independent_multi_common','LAD_free_multi_common','LAD_independent_multi_common','LAD_independent_multi_shrunk4','LAD_independent_gated_common']
    for name in names:
        g=forward[forward.method==name]
        a=g[g.budget=='A'].iloc[0];b=g[g.budget=='B'].iloc[0]
        lines.append(f'- `{name}`：A {a.mae_mV:.3f}、B {b.mae_mV:.3f}；直接覆盖A/B {a.direct_coverage:.0%}/{b.direct_coverage:.0%}；前向接纳A/B {bool(a.forward_gate)}/{bool(b.forward_gate)}。')
    lines += ['', '![官方前向误差](figures/forward_MAE.png)','',
    '约束修正可以改善某些相对于本轮自由修正模型的结果，但全部主要候选仍未超过强旧基线。各温度/跨度层见forward_by_layer.csv，禁止评分后挑选最好的子层作为整体成功。','',
    '## 阶段4：可辨识性与敏感性','']
    for _,r in ident.iterrows():
        lines.append(f'- {r.layer}/{r.loss}：最佳共同s={r.primary_s:.3f}；1mV容差条件容量跨度{r.conditional_width_Ah:.2f}Ah；tau/偏置/采样扰动最佳投影跨度{r.nuisance_best_capacity_span_Ah:.2f}Ah；辨识门{bool(r.identification_gate)}。')
    for layer,g in joint.groupby('layer'):
        accepted=g[g.within_tolerance];strict=accepted[accepted.strict_domain_valid]
        span=float(np.ptp(strict.strict_capacity_Ah)) if len(strict) else np.nan
        tail=accepted[accepted.tail2_capacity_Ah.notna()]
        tailspan=float(np.ptp(tail.tail2_capacity_Ah)) if len(tail) else np.nan
        lines.append(f'- {layer}四维搜索：容差内{len(accepted)}/{len(g)}组；严格域容量可算{len(strict)}/{len(accepted)}，其跨度{span:.2f}Ah；允许旧2Ah尾延拓的敏感性跨度{tailspan:.2f}Ah。搜索非穷尽，未找到反例不能证明唯一性。')
    lines += ['', '![尺度与电压误差剖面](figures/capacity_profiles.png)','',
    '以上条件范围不叫95%置信区间。最后四事件的free/independent剖面仍重合：恒流时b−I_D*R只提供一个电压截距，电阻约束可以被未知偏置补偿；较宽事件又没有合格独立跳变或长静置。多事件降低噪声，并不会自动消除共同的起点、电压偏置、参考极化或温度假设。收缩四尺度的稳定性包含先验贡献，不能作为四个独立容量已被数据识别的证明。','',
    '## 独立机制验证','', '下列均为共同尺度分支；有信息正例是60Ah，负例定义为物理容量参数不变，负例仍可能因起点/温度/协议变化而改变可用包容量。','']
    for _,r in syn[syn.kind=='common'].iterrows():
        lines.append(f'- {r.loss}/{r["mode"]}：正例尺度MAE {r.positive_s_mae:.4f}，95分位 {r.positive_p95:.4f}，最坏 {r.positive_worst:.4f}；接受{r.positive_coverage:.0%}。恒容量负例{int(r.negative_n)}个、接受{int(r.negative_accepted)}个，错误接受总率{r.false_negative_total_rate:.1%}；严格容量输出覆盖{r.capacity_coverage:.1%}。机制门{bool(r.mechanism_gate)}。')
    lines += ['', '机制条件下的参数恢复收益与正式接纳分开。拒绝没有算成容量准确；严格投影越域均留空。生成器与拟合器不同，但它仍是固定机制模拟，不替代真实电池标签。','',
    '配对轨迹面板使用真实可见的操作净Ah传播起点，不读取真实初始SOC或目标后缀。逐行结果见paired_evaluation_metrics.csv；下面的总体均值仅为小样本描述：','']
    for kind,g in paired[(paired.loss=='LAD')&(paired['mode']=='independent')].groupby('kind'):
        lines.append(f'- {kind}：尺度MAE {g.s_mae.mean():.4f}；B前向MAE {g.B_forward_mae_mV.mean():.3f}mV；有效输出{int(g.valid.sum())}/{len(g)}。')
    lines += ['', '## 阶段5：容量投影','',
    '原有历史充电量＋温度加权B已作为独立先验基线登记到history_B_prior_baseline.csv及指纹文件；它没有用于本轮电压拟合、门控或真值。现有CK7基线为95.341%（97.248Ah），只是旧预测，缺隐藏标签不能与新曲线模型排名容量精度。','',
    '已核对CK0发布100.41Ah及5.1A、包端首次11.2V的规则。共同尺度在参考d=0、无额外压降的假设下对应Q=s×100.41，计算恒等检查通过。保存了每个历史窗口的条件容量范围，但辨识门未通过，不作为新的检查点SOH。',
    '四尺度投影采用严格模板域，任何芯先越域都拒绝；旧2Ah尾延拓仅另列敏感性。官方材料已确认满充后5.1A放电至11.2V，但没有明示检查点充电末电流、均衡方式、静置时长、逐芯起点和参考温度，不能把运行事件d带入满充检查点，也不能用历史B输出作真值。','',
    '## 阶段6：Sun方法的适用条件','',
    '已对CK0带载曲线用11/21/41点平滑审核dV/dQ极值并保存特征目录。约10Ah事件虽为恒流，但约20.4A（相对102Ah约0.2C），与CK0约0.05C不同；较宽事件是变流运行。当前没有可认证的后续低倍率完整单芯OCV曲线，无法验证老化特征对应规律。',
    'Sun完整变换公式仍未取得，故完成特征可行性审核后保留此分支为条件不满足；没有编造MPGA/重构公式。特征目录是带载导数，不能标成已确认电化学ICA路标。','',
    '## 四层结论与下一步','',
    '1. 可保留：同步时序核对、延迟表观电阻记录、静置恢复诊断、LAD/L2对照、条件剖面和门控拒绝。它们具有研究用途；修正模块总体预测增益尚未通过。',
    '2. 共同尺度仍缺可靠辨识，四尺度没有获得可信增量；初始状态继续用参考Ah位置，无需人为分成SOC档位。',
    '3. 可做清楚假设下的包级条件投影；尚不能接纳为可靠实际检查点容量预测。',
    '4. 缺少独立逐芯SOC与CK1–CK7同协议容量标签，真实SOC/SOH精度不可测。',
    '下一步最有价值的是补一条独立、同协议、宽跨度的低倍率检查记录：明确充电终止/均衡/静置条件，保存同步四芯电压、电流和温度，并覆盖明显曲率或末端区间；至少提供一个独立实际容量标签。若采用电流中断法，电压采样必须真正同步、足够快，不能继续把现有9–10秒延迟观测当作瞬时IR。',
    '这一信息能同时检验CK0压缩假设、约束起点/电压修正，并评价容量真值；仅再增加短平台片段、优化器或自由参数无法补足这些约束。','',
    '## 文献与实现边界','',
    '- [Liu 2022](https://www.sciencedirect.com/science/article/pii/S2590116822000108)：借用LAD与物理曲线变换，未取得完整方法章节。',
    '- [Tsai & Chen 2023](https://www.sciencedirect.com/science/article/pii/S2352152X22024914)：借用电流中断校准思路，未搬用NMC多项式或未知修正公式。',
    '- [Sun 2022](https://www.sciencedirect.com/science/article/pii/S0360544221031315)：完成特征可行性审核，完整重构公式缺失。',
    '- [Wang 2025完整预印本](https://arxiv.org/html/2511.06989v1)：借用联合起点/容量配准；本项目仍是带载模板，未满足独立OCV前提。','',
    '开发修订的早期输出单独保存。冻结后的模块重名导入问题以指定绝对路径加载同一冻结执行器解决，记录于runtime_import_audit.json；未改变模型、阈值、种子或评分。','',
    '复现方法、数据文件和完成标记见README.md。']
    extra=TASK/'supplement_wide50'
    if (extra/'COMPLETE').exists():
        sf=pd.read_csv(extra/'summary.csv');sd=pd.read_csv(extra/'identifiability.csv')
        split=json.loads((extra/'data_split.json').read_text())
        lines += ['', '## 评分后补充：现有45–50Ah片段', '',
            f"补审发现CK7前还存在419条动态放电，其中107条>40Ah、70条>45Ah。全部70条重新审核，{split['development']}条开发、{split['evaluation']}条前向评分。选择窗口发生在主评分后，属于明确标注的探索性验证，不改变主接纳结论。", '',
            '沿用已冻结模型、网格、tau与门槛；按温度和45.7/50.22Ah重复程序分组。程序分类来自事件目录积分跨度，因此结果条件于已知放电程序，不声称未知调度下的纯在线预测。新补充源码与协议在读取新电压结果前另存指纹。', '']
        for loss in ['L2','LAD']:
            g=sf[(sf.loss==loss)&(sf.kind=='common')];base=sf[(sf.loss==loss)&(sf.kind=='baseline')]
            lines.append(f"- {loss}共同尺度A/B：{g[g.budget=='A'].mae_mV.iloc[0]:.3f}/{g[g.budget=='B'].mae_mV.iloc[0]:.3f}mV；历史曲线基线 {base[base.budget=='A'].mae_mV.iloc[0]:.3f}/{base[base.budget=='B'].mae_mV.iloc[0]:.3f}mV。")
        lines += [f"- 条件容量跨度{sd.width_Ah.min():.2f}–{sd.width_Ah.max():.2f}Ah，{int(sd.gate.sum())}/{len(sd)}个损失—历史窗口通过辨识门；门控全部回退。", '',
            '更宽运行片段提供了一些约束，但现有45–50Ah记录仍不能可靠确定尺度。不是因为没有查找更宽现有记录；进一步研究应关注独立起点/电压标尺与明显曲率覆盖，而非仅把33Ah窗口换成50Ah。详细结果见supplement_wide50/summary.csv、identifiability.csv及PROTOCOL.md。']
    (TASK/'FINAL_REPORT.md').write_text('\n'.join(lines)+'\n')
    draw_figures(forward,curves,pulses)
    savejson('environment.json',dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,matplotlib=matplotlib.__version__,date='2026-10-13'))
    runner.verify_freeze()
    files={str(p.relative_to(TASK)):sha(p) for p in TASK.rglob('*') if p.is_file() and '__pycache__' not in str(p) and 'development_revision' not in str(p) and p.name!='artifact_manifest.json'}
    savejson('artifact_manifest.json',dict(files=files,protected_originals_unchanged=decision['protected_unchanged']))
    print('Report and scientific figures rendered',flush=True)


def draw_figures(forward,curves,pulses):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    names=['frozen_baseline','legacy_fixed','L2_independent_multi_common','LAD_independent_multi_common','LAD_independent_multi_shrunk4']
    labels=['Frozen baseline','Legacy fixed s','L2 constrained common','LAD constrained common','LAD shrunk 4 scales']
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for ax,budget in zip(axes,['A','B']):
        values=[forward[(forward.budget==budget)&(forward.method==n)].mae_mV.iloc[0] for n in names]
        ax.barh(labels,values,color=['#4f4f4f']+['#7795a7']*4);ax.invert_yaxis();ax.set_xlabel('Mean per-event cell MAE (mV)');ax.set_title(f'Budget {budget}: 46 historical events')
        for k,v in enumerate(values):ax.text(v+.025,k,f'{v:.3f}',va='center')
    fig.suptitle('Frozen forward replay: current suffix voltage excluded');fig.savefig(TASK/'figures/forward_MAE.png',dpi=180);fig.savefig(TASK/'figures/forward_MAE.svg');plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(11,7),layout='constrained')
    for ax,layer in zip(axes.flat,['short_25','short_45','wide_25','wide_45']):
        for variant,color in [('free','#777777'),('independent','#235e79')]:
            g=curves[(curves.layer==layer)&(curves.loss=='L2')&(curves.variant==variant)].sort_values('s')
            ax.plot(g.conditional_capacity_Ah,g.loss_mV,label=variant,color=color,marker='o',markersize=3)
        ax.set_title(layer);ax.set_xlabel('Conditional CK0 capacity (Ah)');ax.set_ylabel('Profile RMS (mV)');ax.legend(frameon=False)
    fig.suptitle('Last 4 events per layer: broad profiles are not confidence intervals');fig.savefig(TASK/'figures/capacity_profiles.png',dpi=180);fig.savefig(TASK/'figures/capacity_profiles.svg');plt.close(fig)
    first=pulses.iloc[0];raw=pd.read_csv(ROOT/'data/operation'/first.file,parse_dates=['timestamp']);edge=pd.Timestamp(first.timestamp)
    raw=raw.sort_values('timestamp',kind='stable').drop_duplicates('timestamp',keep='last');raw=raw[(raw.timestamp>=edge-pd.Timedelta(seconds=22))&(raw.timestamp<=edge+pd.Timedelta(seconds=22))]
    x=(raw.timestamp-edge).dt.total_seconds().to_numpy();y=raw[[f'cell{i}_V' for i in range(1,5)]].to_numpy();baseline=y[x<0][-1]
    fig,axes=plt.subplots(2,1,figsize=(9,5),sharex=True,layout='constrained');axes[0].step(x,-raw.current_A,where='post',color='#444444');axes[0].scatter(x,-raw.current_A,color='#444444',s=18);axes[0].set_ylabel('Discharge current (A)')
    for c in range(4):axes[1].plot(x,(y[:,c]-baseline[c])*1000,marker='o',label=f'Cell {c+1}',markersize=4)
    for ax in axes:ax.axvline(0,color='#777777',linestyle=':')
    axes[1].set_ylabel('Change from pre-edge V (mV)');axes[1].set_xlabel('Time from current edge (s)');axes[1].legend(frameon=False,ncol=4);fig.suptitle('Raw observed samples: first development pulse, 2025-01-20');fig.savefig(TASK/'figures/pulse_timing.png',dpi=180);fig.savefig(TASK/'figures/pulse_timing.svg');plt.close(fig)

if __name__=='__main__':main()
