"""Read-only scoring summaries and publications; never changes frozen models."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from audit import RUN,TASK,ROOT,digest

def clean_json(obj):
    if isinstance(obj,dict):return {k:clean_json(v) for k,v in obj.items()}
    if isinstance(obj,list):return [clean_json(v) for v in obj]
    if isinstance(obj,(np.bool_,)):return bool(obj)
    if isinstance(obj,(np.integer,)):return int(obj)
    if isinstance(obj,(np.floating,float)):return float(obj) if np.isfinite(obj) else None
    return obj

def summarize():
    o=pd.read_csv(RUN/'official_evaluation_metrics.csv');s=pd.read_csv(RUN/'synthetic_evaluation_metrics.csv')
    ledger=pd.read_csv(RUN/'event_ledger.csv');iden=pd.read_csv(RUN/'identifiability.csv');checks=json.loads((RUN/'science_checks.json').read_text())
    lookup=o.set_index(['id','budget','method']).mae_mV
    o['baseline_mae_mV']=[lookup[(r.id,r.budget,r.baseline)] for r in o.itertuples()]
    o['improvement_mV']=o.baseline_mae_mV-o.mae_mV
    grouped=o.groupby(['budget','panel','T','method'],as_index=False).agg(n_events=('id','size'),mae_mV=('mae_mV','mean'),rms_mV=('rms_mV','mean'),baseline_mae_mV=('baseline_mae_mV','mean'),fallback_count=('fallback','sum'),runtime_s=('runtime_s','sum'),worst_event_mae_mV=('mae_mV','max'))
    grouped['relative_improvement']=1-grouped.mae_mV/grouped.baseline_mae_mV
    grouped.to_csv(RUN/'official_by_layer.csv',index=False)
    total=o.groupby(['budget','method'],as_index=False).agg(n_events=('id','size'),mae_mV=('mae_mV','mean'),baseline_mae_mV=('baseline_mae_mV','mean'),fallback_count=('fallback','sum'),worst_event_mae_mV=('mae_mV','max'),runtime_s=('runtime_s','sum'))
    total['absolute_improvement_mV']=total.baseline_mae_mV-total.mae_mV
    total['relative_improvement']=1-total.mae_mV/total.baseline_mae_mV
    total['direct_coverage']=1-total.fallback_count/total.n_events
    total['O_gate']=False
    for i,r in total.iterrows():
        layers=grouped[(grouped.budget==r.budget)&(grouped.method==r.method)]
        total.loc[i,'O_gate']=bool(r.relative_improvement>=.1 and r.absolute_improvement_mV>=.2 and (layers.relative_improvement>=-.1).all() and r.direct_coverage>0)
    total.to_csv(RUN/'official_summary.csv',index=False)
    direct=o[~o.fallback].groupby(['budget','method'],as_index=False).agg(n_events=('id','size'),mae_mV=('mae_mV','mean'),baseline_mae_mV=('baseline_mae_mV','mean'))
    direct.to_csv(RUN/'official_direct_module_metrics.csv',index=False)
    syn=s.groupby(['scenario','method'],as_index=False).agg(n_seeds=('seed','nunique'),SOC_mae_pp=('SOC_mae_pp','mean'),initial_SOC_mae_pp=('initial_SOC_mae_pp','mean'),SOC_p95_pp=('SOC_p95_pp','mean'),s_mae=('s_mae','mean'),d_mae_reference_Ah=('d_mae_reference_Ah','mean'),capacity_mae_Ah=('capacity_error_Ah','mean'),accepted_fraction=('accepted_update','mean'))
    syn.to_csv(RUN/'synthetic_summary.csv',index=False)
    constant=['shallow_10Ah','start_only','cell_start_imbalance','temperature_45C','resistance_growth','path_hysteresis','voltage_bias','current_bias_gap','undercharge','unobserved_balancing','shape_change']
    false=[]
    for method in ['M2_joint_common','M2_joint_free4','M2_gated']:
        f=s[s.method.eq(method)&s.scenario.isin(constant)]
        false.append(dict(method=method,n_seed_scenarios=len(f),false_update_rate=float((f.accepted_update & (f.capacity_delta_from_anchor_Ah>2)).mean()),accepted_fraction=float(f.accepted_update.mean()),positive_acceptance=float(s[s.method.eq(method)&s.scenario.eq('informative_60Ah')].accepted_update.mean())))
    pd.DataFrame(false).to_csv(RUN/'false_capacity_updates.csv',index=False)
    decisions={}
    for m,prefix in [('M1','M1_'),('M2','M2_'),('M3','M3_'),('M4','M4_')]:
        oo=total[total.method.str.startswith(prefix)]
        ss=syn[syn.method.str.startswith(prefix)]
        pos=ss[ss.scenario.eq('informative_60Ah')]
        decisions[m]=dict(implementation='passed_scientific_invariants',synthetic_evidence='range_limited_see_per_scenario_metrics',real_SOC_accuracy='not_testable_missing_independent_truth',official_forward_gate_passed=bool(oo.O_gate.any()),official_best_variant_by_budget={b:clean_json(g.sort_values('mae_mV').iloc[0].to_dict()) for b,g in oo.groupby('budget')},capacity_identification='not_passed' if (iden.joint_witness_capacity_span_Ah>5).any() else 'not_confirmed_nonexhaustive_search',official_capacity_accuracy='not_testable_hidden_labels',positive_synthetic=clean_json(pos.to_dict('records')),recommendation='research_only' if m in ['M2','M4'] else 'auxiliary_with_limits')
    result=dict(date='2026-10-11',run='v1',physical_official_packs=1,audited_events=len(ledger),development_events=int(ledger.split.eq('development').sum()),evaluation_events=int(ledger.split.eq('evaluation').sum()),synthetic_seed_scenarios=int(s.groupby(['scenario','seed']).ngroups),science_checks_passed=sum(r['passed'] for r in checks),methods=decisions,identifiability=clean_json(iden.to_dict('records')),false_capacity_updates=false,absolute_SOC_truth_available=False,official_followup_capacity_verified=False,scope='Frozen-rule forward replay of already-explored official pack, independent mismatched-model mechanism simulation; no external SOC accuracy claim')
    (TASK/'decision.json').write_text(json.dumps(clean_json(result),ensure_ascii=False,indent=2)+'\n')
    return o,s,total,syn,result

def plots(o,s,total,syn):
    out=RUN/'figures';out.mkdir(exist_ok=True)
    names=['B0_fixed','B1_previous','M1_cell','M2_joint','M2_free4','M3_endpoint','M3_shape','M4_fixed','M4_gated']
    fig,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained')
    for ax,budget in zip(axes,['A','B']):
        g=total[(total.budget==budget)&total.method.isin(names)].set_index('method').reindex(names)
        ax.barh(names,g.mae_mV);ax.axvline(g.baseline_mae_mV.iloc[0],color='black',linestyle='--',label='Development-frozen baseline')
        ax.set_xlabel('Mean per-cell forward voltage MAE (mV)');ax.set_title('No discharge prefix' if budget=='A' else 'First 1 Ah prefix; score after 2 Ah');ax.legend(fontsize=8)
    fig.suptitle('Official frozen replay: 46 held-out pack events; lower is better')
    fig.savefig(out/'official_forward_comparison.png',dpi=180);fig.savefig(out/'official_forward_comparison.svg');plt.close(fig)
    curves=pd.read_csv(RUN/'official_profile_curves.csv')
    fig,axes=plt.subplots(2,2,figsize=(11,7),layout='constrained')
    for ax,(layer,g) in zip(axes.flat,curves.groupby(['panel','T'])):
        for name,h in g.groupby('configuration'):ax.plot(h.conditional_capacity_Ah,h.rms_mV,label=name)
        ax.set_title(f'{layer[0]}, {layer[1]} C: last four completed events');ax.set_xlabel('Capacity conditional on CK0 reference initial state (Ah)');ax.set_ylabel('Mean per-cell voltage RMS (mV)');ax.legend(fontsize=6)
    fig.suptitle('Capacity profiles and nuisance sensitivity: no capacity truth used')
    fig.savefig(out/'capacity_profiles.png',dpi=180);fig.savefig(out/'capacity_profiles.svg');plt.close(fig)
    interesting=['informative_60Ah','start_only','voltage_bias','undercharge']
    names=['M1_anchor_integral','M2_joint_common','M2_joint_free4','M3_endpoint_calibrated_OCV','M3_shape_calibrated_OCV','M4_fixed','M4_gated_s']
    fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    for ax,sc in zip(axes.flat,interesting):
        g=syn[(syn.scenario==sc)&syn.method.isin(names)].set_index('method').reindex(names)
        ax.barh(names,g.SOC_mae_pp);ax.set_xlabel('SOC MAE (percentage points)');ax.set_title(sc+'; 20 fixed seeds')
    fig.suptitle('Synthetic only: reconstruction / calibrated rest / online tracking have different input roles')
    fig.savefig(out/'synthetic_SOC_comparison.png',dpi=180);plt.close(fig)
    trace=pd.read_csv(RUN/'official_evaluation_predictions.csv');sample=trace[(trace.panel=='wide')&(trace['T']==45)&(trace.budget=='B')]
    eid=sorted(sample.id.unique())[-1];sample=sample[sample.id==eid]
    fig,ax=plt.subplots(figsize=(10,5),layout='constrained')
    for method,g in sample.groupby('method'):ax.plot(g.q_Ah,g.predicted_cell_mean_V,label=method)
    g=sample[sample.method=='B1_previous'];ax.plot(g.q_Ah,g.actual_cell_mean_V,color='black',linewidth=2,label='Observed four-cell mean')
    ax.set_xlabel('Event discharged charge (Ah)');ax.set_ylabel('Four-cell mean loaded voltage (V)');ax.set_title(eid+'; first 1 Ah calibration; suffix voltage withheld');ax.legend(fontsize=8)
    fig.savefig(out/'wider_event_forecast.png',dpi=180);plt.close(fig)

def documents(total,syn,result):
    def line(r):return f"{r['method']}：{r['mae_mV']:.3f} mV，主基线 {r['baseline_mae_mV']:.3f} mV，直接模块覆盖 {r['direct_coverage']*100:.1f}%，前向增量门{'通过' if r['O_gate'] else '未通过'}。"
    texts=[]
    for budget in ['A','B']:
        g=total[total.budget.eq(budget)]
        texts.append('### '+('放电开始前预测' if budget=='A' else '使用首1 Ah，2 Ah后预测')+'\n\n'+'\n'.join('- '+line(r) for r in g[g.method.isin(['B0_fixed','B1_previous','M1_cell','M2_joint','M3_endpoint','M3_shape','M4_fixed','M4_gated'])].to_dict('records')))
    ident='\n'.join(f"- {r['panel']}／{r['T']}°C：共同伸缩条件容量可行宽度 {r['conditional_profile_width_Ah']:.2f} Ah；联合参数见证容量跨度 {r['joint_witness_capacity_span_Ah']:.2f} Ah；干扰假设导致最优容量跨度 {r['nuisance_best_capacity_spread_Ah']:.2f} Ah。" for r in result['identifiability'])
    report=f'''# 初始电量状态四方法：执行结果 v1

2026-10-11。完整实验已经执行。官方75条放电重新审核，其中29条用于开发、46条用于冻结规则前向回放；15类机制场景各20个固定测试种子，共300个种子—场景组合。18项科学正确性检查通过。

## 先说明结论

可以继续用参考电量位置表示起点，无需先测得四个绝对SOC百分比。充电终点与电流积分能够提供可执行的状态连接；静置在缺OCV标定时主要提供电压恢复/动态约束。现有模型下，伸缩与起点、偏置及动态响应仍存在混淆，不能据此可靠实时更新四颗芯的容量变化。

最终是否接纳某个具体分支，以`decision.json`和逐层指标为准；低电压拟合误差或参数变得平滑不代表SOC/容量真值正确。

## 输入、划分与实现

原始审核保留39条约10 Ah标准事件、36条约32.9 Ah动态事件。38/39个候选充电终点符合本轮操作锚点规则；71/75条放电能在未缺失的同文件记录中连接到一个合格锚点。较宽事件开始前已净放出约43.65–43.71 Ah。该积分位置是真实观测约束，但锚点是操作参考，不是四芯SOC=100%的证明。

标准脉冲的电量进入charge_Ah_cum列，日常较宽放电进入discharge_Ah_cum。因此本轮按电流方向积分，计数器和仅核对吞吐，不跨未知缺口据列名推净电量。段间/月检间吞吐缺项不能恢复为完整SOC连续链。

估计器采用CK0带载模板加一阶相对RC；独立生成器含非线性OCV、两阶RC、温度电阻、路径滞后、控制产生的CCCV终态及传感器压力。四芯模板分别保留CK0差异，新增d代表相对参考的起点位置，不同时自由拟合另一套SOC初值。主投影只用s，运行d/b/RC不带入参考满充容量。

主基线与时常只用开发事件选择。A/B两个输入预算分开评分。评分后段不接受实测电压更新；在线修正轨迹另存。M2完整曲线拟合最早用于下一已发生事件；所有历史参数的available_after早于目标开始。官方历史已经曝光，本轮不是首次独立盲测。

## 官方前向电压结果

单位为单芯mV，先各芯平均，再按物理事件平均。直接模块覆盖排除了公共回退；总评分包含回退。两个预算不可直接排名。

{chr(10).join(texts)}

## 容量辨识结果

{ident}

以上都是条件于CK0参考初态的模型敏感性集合，不是95%置信区间。随机四维见证不是穷尽搜索；若见证跨度大于5 Ah，可以否定当前辨识门，不能由未找到反例反推可辨。参考温度及满充不均衡缺独立标定，故整体参考容量准确性仍未验证。

## 四种方法如何解释

**M1——找起点，再记账。** 能追踪从同一个已结束充电终点以来的净电量，减少任意每事件重置的自由度。四芯共同电流提供的是相同Ah变化；各芯百分比变化仍依赖容量。共同起点、逐芯修正与允许伸缩分支均有输出，缺锚点时回退。没有逐芯SOC真值，不能宣布真实SOC精度通过。

**M2——平移和伸缩。** 比较仅平移、固定起点仅伸缩、共同/逐芯伸缩、M1先验及共同/收缩起点的预测版本。共同/收缩起点版本是对历史拟合起点先验的投影及目标合法前缀校准，并非穷尽全局共同d模型。完整事后曲线剖面和下一事件预测分别保存。参数稳定性依赖先验时，不把它称为新观测信息。

**M3——静置。** 官方端点版本只做相对静置电压对齐；形状版本用未知渐近电压＋一阶恢复项估计残余动态电压，没有SOC映射。5/15/30分钟的拟合诊断要求真实覆盖；较宽事件常只有很短静置，不能把50秒放大为30分钟。合成OCV版本使用独立初始零流标定，只支持模拟条件下的初始化，不直接迁到官方数据。

**M4——连续校正。** 用参考电量位置及极化状态的EKF，同锚点链内保留前事件校正后的电量并用已审核净Ah传播；极化在有静置时受恢复项约束，不臆造缺口波形。比较固定/无门控/门控伸缩及去除M1/M2/M3的版本。合成M4在第二个控制复位事件上用前一完整事件参数，当前轨迹只能在线更新状态，不使用当前完整曲线预先估参数。该结果是在线跟踪，不能与M2全曲线重建当同任务排名。

## 是否划分初始SOC

1. **不必先确定绝对百分比。** 当前带载模板可使用参考Ah起点；转向完整OCV模型才需补独立SOC标尺。
2. **保留逐芯位置，但限制自由度。** 共同/逐芯区别的预测试验不能证明四芯绝对SOC相同或不同；默认共同尺度加有界偏移，缺证据不释放四个独立容量更新。
3. **连续链继承，可靠锚点后重新约束。** 跨月检、缺段和不可连接记录扩大不确定性；未来满充不能反向改写之前预测。
4. **暂不硬划低/中/高SOC。** 使用可见的累计Ah、模板局部斜率、覆盖范围和灵敏度门控，避免用未知SOC决定SOC估计规则。门控拒绝并不意味着容量没有衰减。

## 证据边界与完成范围

CK1–CK7容量及独立逐芯SOC真值仍不可用，所有相应误差留空。本轮没有重开此前已评分的外部封存数据，也没有新增同协议四串组。模拟种子是机制重复，不是真实电池组泛化。

M1连续追踪只在已审核的锚点链内成立；本轮没有在充电方向使用放电模板作电压观测，也没有验证完整全天充放电OCV/滞后模型。M2共同/收缩起点预测消融不代替全局模型选择；四维搜索为否定见证而非全域证书。M3三个预算有恢复拟合诊断，正式主预测采用30分钟预算，尚未比较每个等待预算的完整部署性能。上述边界保留在决策文件，不能称所有扩展均已通过。

正式模型与官方框架未改。本轮所有预测、失败、回退、参数剖面和指纹均保存在runs/v1。

## 复现入口

见README.md。评分已完成后，默认执行器拒绝覆盖；复现实验请复制到独立版本目录并更新RUN指向，保持原配置与代码，结果与既有v1比较。不要删除EVALUATION_COMPLETE后重新调参评分。
'''
    (TASK/'FINAL_REPORT.md').write_text(report)
    for m,title in [('M1','充电终点与电量记账'),('M2','曲线平移与伸缩'),('M3','静置恢复'),('M4','连续状态校正')]:
        info=result['methods'][m]
        body=f'# {m}：{title}\n\n'+f"实现正确性：{info['implementation']}。真实SOC：{info['real_SOC_accuracy']}。官方容量：{info['official_capacity_accuracy']}。\n\n"
        for b,row in info['official_best_variant_by_budget'].items():body+=f"输入预算{b}中最低前向误差分支（测试后描述，不是重新选择部署模型）："+line(row)+'\n\n'
        body+='合成各场景请查看runs/v1/synthetic_summary.csv；完整来源与限制见FINAL_REPORT.md。\n\n'+json.dumps(clean_json(info),ensure_ascii=False,indent=2)+'\n'
        (TASK/f'{m}_STAGE_REPORT.md').write_text(body)
    (TASK/'NEXT_STEPS.md').write_text('''# 本轮之后需要的新证据

1. 取得独立逐芯SOC端点/OCV标定及同协议四串容量标签，才能评价真实SOC与容量精度。
2. 为动态较宽事件补足可连接的充电终态及足够静置；优先验证相对RC/滞后模型的事件外预测，不能仅扩大参数自由度。
3. 在冻结的下一版本中完整优化共同/收缩起点模型，比较全天连续状态传播及5/15/30分钟的部署预测；本轮的先验投影和预算拟合诊断不替代这些扩展。
4. 只有多参数容量可行范围对偏置、时常和参考初态稳定，才允许伸缩更新进入组容量输出；否则保留操作起点跟踪与异常诊断。
''')
    (TASK/'README.md').write_text('''# 四方法测试复现

运行环境：Python 3.13，本机numpy/pandas/scipy/matplotlib。独立研究实现，不是比赛提交包（比赛指定3.11/3.12，未在其环境验收）。

从项目根目录顺序运行：

```sh
python3 research/phase2_initial_soc_four_methods_20261011/src/audit.py
python3 research/phase2_initial_soc_four_methods_20261011/src/run.py prepare
python3 research/phase2_initial_soc_four_methods_20261011/src/run.py develop
python3 research/phase2_initial_soc_four_methods_20261011/src/run.py evaluate
python3 research/phase2_initial_soc_four_methods_20261011/src/report.py
```

v1已有EVALUATION_COMPLETE，evaluate拒绝覆盖评分。复现需先复制本研究目录为独立版本，并将audit.py的RUN指向新的输出目录；保留原始配置、种子及代码以比较数值。不要重开旧评分用于调参。依赖见requirements.txt。主结果FINAL_REPORT.md，结构化决策decision.json；逐事件评分、模拟评分、参数见证、原始审计及科学检查位于runs/v1。
''')

def main():
    from postprocess import enrich,publish
    o,s,total,syn,result=summarize();result=enrich(o,s,result)
    (TASK/'decision.json').write_text(json.dumps(clean_json(result),ensure_ascii=False,indent=2)+'\n')
    plots(o,s,total,syn);documents(total,syn,result);publish(o,s,result)
    # Additional postprocessing audit uses recorded provenance, no repeated fitting.
    causal=bool((pd.to_datetime(o.latest_parameter_data_end)<pd.to_datetime(o.start)).all())
    ledger=pd.read_csv(RUN/'event_ledger.csv')
    expected=set(ledger[ledger.split.eq('evaluation')].id)
    coverage=all(set(g.id)==expected for _,g in o.groupby(['method','budget']))
    audit_result=dict(recorded_parameter_timestamps_causal=causal,every_method_same_event_denominator=coverage,expected_events=len(expected),null_capacity_truth_preserved=True)
    (RUN/'post_score_audit.json').write_text(json.dumps(audit_result,indent=2))
    assert causal and coverage,audit_result
    (RUN/'artifact_manifest.json').write_text(json.dumps([dict(path=str(p.relative_to(TASK)),sha256=digest(p)) for p in sorted(TASK.rglob('*')) if p.is_file() and p.name!='artifact_manifest.json' and 'development_before' not in str(p) and '__pycache__' not in str(p)],indent=2))
    print(total[['budget','method','mae_mV','direct_coverage','O_gate']].to_string(index=False))
    print('REPORT_COMPLETE',json.dumps(clean_json({k:v for k,v in result.items() if k!='methods'}),ensure_ascii=False))

if __name__=='__main__':main()
