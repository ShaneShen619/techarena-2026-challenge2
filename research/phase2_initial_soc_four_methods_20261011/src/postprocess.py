"""Publication diagnostics from saved scores, without refitting frozen models."""
from __future__ import annotations
import ast,json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from audit import RUN,TASK,ROOT,digest

STRESS=['shallow_10Ah','start_only','cell_start_imbalance','temperature_45C','resistance_growth','path_hysteresis','voltage_bias','current_bias_gap','undercharge','unobserved_balancing','shape_change']

def wilson(k,n):
    if not n:return [None,None]
    z=1.96;p=k/n;den=1+z*z/n
    mid=(p+z*z/(2*n))/den;half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [float(mid-half),float(mid+half)]

def enrich(o,s,result):
    # A raw optimization flag is not a valid accepted capacity if projection failed.
    updated=[];per_scenario=[]
    for method in ['M2_joint_common','M2_joint_free4','M2_gated']:
        allm=s[s.method.eq(method)];stress=allm[allm.scenario.isin(STRESS)];pos=allm[allm.scenario.eq('informative_60Ah')]
        finite=np.isfinite(stress.capacity_est_Ah);valid=stress.accepted_update & finite
        wrong=valid & stress.capacity_delta_from_anchor_Ah.gt(2)
        posvalid=pos.accepted_update & np.isfinite(pos.capacity_est_Ah)
        row=dict(method=method,n_seed_scenarios=len(stress),finite_capacity_count=int(finite.sum()),no_capacity_output_count=int((~finite).sum()),raw_accepted_fraction=float(stress.accepted_update.mean()),valid_accepted_fraction=float(valid.mean()),false_update_count=int(wrong.sum()),false_update_rate_all=float(wrong.mean()),false_update_rate_finite=float(wrong[finite].mean()) if finite.any() else None,positive_raw_acceptance=float(pos.accepted_update.mean()),positive_valid_acceptance=float(posvalid.mean()),positive_valid_acceptance_wilson95=wilson(int(posvalid.sum()),len(pos)),positive_SOC_mae_pp=float(pos.SOC_mae_pp.mean()),positive_s_mae=float(pos.s_mae.mean()))
        row['mechanism_gate_passed']=bool(row['positive_SOC_mae_pp']<=3 and row['positive_s_mae']<=.03 and row['positive_valid_acceptance']>=.8 and row['false_update_rate_all']<=.05 and row['no_capacity_output_count']==0)
        updated.append(row)
        for scenario,g in stress.groupby('scenario'):
            f=np.isfinite(g.capacity_est_Ah);bad=g.accepted_update & f & g.capacity_delta_from_anchor_Ah.gt(2)
            per_scenario.append(dict(method=method,scenario=scenario,n_seeds=len(g),finite_capacity_count=int(f.sum()),false_update_count=int(bad.sum()),false_rate_all=float(bad.mean()),wilson95_low=wilson(int(bad.sum()),len(g))[0],wilson95_high=wilson(int(bad.sum()),len(g))[1],scope='conditional_generator_repeats_not_real_pack_generalization'))
    pd.DataFrame(updated).to_csv(RUN/'false_capacity_updates_coverage_audited.csv',index=False)
    pd.DataFrame(per_scenario).to_csv(RUN/'false_updates_by_scenario.csv',index=False)
    result['false_capacity_updates_raw_flag_only']=result.pop('false_capacity_updates')
    result['false_capacity_updates']=updated
    result['raw_accepted_update_caveat']='For unconstrained M2 joint models, accepted_update is an optimization flag. Nonfinite capacity projections are failures/no output, never successful capacity updates.'
    result['methods']['M2']['synthetic_evidence']='SOC_recovery_supported_in_informative_synthetic_case_capacity_update_gate_not_passed'
    result['methods']['M2']['mechanism_capacity_gates']=updated
    result['methods']['M1']['recommendation']='operation_bookkeeping_only_not_accepted_SOC_or_voltage_predictor'
    result['methods']['M3']['recommendation']='rest_diagnostic_only_not_accepted_SOC_or_voltage_predictor'
    result['methods']['M4']['synthetic_evidence']='range_limited_online_SOC_support_no_independent_capacity_projection_test'
    result['methods']['M1']['synthetic_evidence']='anchor_improves_over_naive_full_reset_but_state_accuracy_gate_not_demonstrated'
    result['methods']['M3']['synthetic_evidence']='calibrated_synthetic_OCV_initialization_limited_by_plateau_and_path_state_gate_not_demonstrated'
    result['final_combination']=dict(deployable_new_SOC_or_capacity_estimator='none_accepted',retain='development_frozen_baseline_for_voltage; audited_relative_Ah_as_operation_state',s_updates='freeze_without_identifiability_and_valid_reference_projection',initialization='reference_charge_position_without_absolute_SOC; bounded_cell_offsets_are_a_modeling_choice_not_verified_cell_truth',continuous_chain='inherit_only_with_audited_signed_current; after_unknown_gap_keep_unknown_until_new_anchor',SOC_partition='no_hard_low_mid_high_SOC_partition; use_observable_span_slope_and_uncertainty')
    variability=[]
    for (scenario,method),g in s.groupby(['scenario','method']):
        for metric in ['SOC_mae_pp','initial_SOC_mae_pp','s_mae','capacity_error_Ah','position_interval_coverage']:
            a=g[metric].dropna().to_numpy(float)
            if len(a):variability.append(dict(scenario=scenario,method=method,metric=metric,n_seed_scenarios=len(g),n_finite=len(a),mean=float(a.mean()),seed_sd=float(a.std(ddof=1)) if len(a)>1 else None,seed_p05=float(np.quantile(a,.05)),seed_p95=float(np.quantile(a,.95)),worst=float(a.max()),interpretation='seed_distribution_not_real_entity_confidence_interval'))
    pd.DataFrame(variability).to_csv(RUN/'synthetic_seed_variability.csv',index=False)
    cells=[]
    for row in o.itertuples():
        for c,v in enumerate(ast.literal_eval(row.per_cell_mae_mV)):
            cells.append(dict(id=row.id,panel=row.panel,T=row.T,budget=row.budget,method=row.method,cell=c+1,mae_mV=v,pack_mae_mV=row.pack_mae_mV))
    pd.DataFrame(cells).to_csv(RUN/'official_per_cell_metrics.csv',index=False)
    trace=pd.read_csv(RUN/'official_evaluation_predictions.csv')
    trace=trace[trace.q_Ah.ge(2)].copy()
    trace['region']=np.where(trace.q_Ah<=trace.groupby(['id','budget','method']).q_Ah.transform('max')/2,'early_suffix','late_suffix')
    trace['four_cell_mean_abs_error_mV']=abs(trace.actual_cell_mean_V-trace.predicted_cell_mean_V)*1000
    trace.groupby(['id','panel','T','budget','method','region'],as_index=False).four_cell_mean_abs_error_mV.mean().to_csv(RUN/'official_early_late_mean_voltage_metrics.csv',index=False)
    conv=pd.read_csv(RUN/'initial_error_convergence.csv')
    conv.groupby('initial_error_pp',as_index=False).agg(n_seeds=('seed','size'),converged_count=('convergence_Ah','count'),mean_convergence_Ah=('convergence_Ah','mean'),mean_final_error_pp=('final_error_pp','mean'),worst_final_error_pp=('final_error_pp','max'),min_finite_fraction=('finite_fraction','min')).to_csv(RUN/'initial_error_convergence_summary.csv',index=False)
    result['initial_error_test_scope']='synthetic oracle-centered perturbation; criterion is 10 consecutive points below 3 pp, not sustained convergence to trajectory end'
    supplement={}
    for source,groups in [('supplement_full_structure_forecasts',['method','budget','panel','T']),('supplement_waiting_budget_forecasts',['method','budget','waiting_budget_s','panel','T'])]:
        d=pd.read_csv(RUN/(source+'.csv'))
        lookup=o.set_index(['id','budget','method']).mae_mV
        baseline=o.drop_duplicates(['id','budget']).set_index(['id','budget']).baseline
        d['baseline_mae_mV']=[lookup[(x.id,x.budget,baseline[(x.id,x.budget)])] for x in d.itertuples()]
        d['valid_output']=np.isfinite(d.mae_mV)
        d['paired_baseline_mV']=d.baseline_mae_mV.where(d.valid_output)
        agg=d.groupby(groups,as_index=False).agg(n_events=('id','size'),n_output=('mae_mV','count'),mae_mV=('mae_mV','mean'),paired_baseline_mV=('paired_baseline_mV','mean'))
        agg['coverage']=agg.n_output/agg.n_events
        agg.to_csv(RUN/(source+'_summary.csv'),index=False)
        total=d.groupby(groups[:2] if source.endswith('structure_forecasts') else groups[:3],as_index=False).agg(n_events=('id','size'),n_output=('mae_mV','count'),mae_mV=('mae_mV','mean'),paired_baseline_mV=('paired_baseline_mV','mean'))
        supplement[source]=total.to_dict('records')
    oracle=pd.read_csv(RUN/'oracle_state_diagnostics.csv')
    supplement['oracle_diagnostics']=oracle.groupby('oracle',as_index=False).SOC_mae_pp.mean().to_dict('records')
    thermal=pd.read_csv(RUN/'temperature_return_diagnostics.csv')
    pivot=thermal.pivot(index='seed',columns='stage',values='conditional_reference_capacity_Ah')
    supplement['temperature_return']=dict(n_seeds=len(pivot),mean_abs_25_to_45_capacity_change_Ah=float(abs(pivot[1]-pivot[0]).mean()),max_abs_25_return_difference_Ah=float(abs(pivot[2]-pivot[0]).max()),accepted_update_count=int(thermal.accepted_update.sum()),interpretation='paired_controller_reset_not_continuous_thermal_state_validation')
    daily=pd.read_csv(RUN/'daily_chain_summary.csv');dailytrace=pd.read_csv(RUN/'daily_relative_charge_trace.csv')
    dailytrace.loc[~dailytrace.chain_continuous,'net_reference_position_Ah']=np.nan
    dailytrace.to_csv(RUN/'daily_relative_charge_qualified_trace.csv',index=False)
    supplement['daily_chains']=dict(n_chains=len(daily),n_fully_continuous=int(daily.all_rows_continuous.sum()),n_chains_with_gap=int((~daily.all_rows_continuous).sum()),rows=int(daily.rows.sum()),max_observed_relative_Ah=float(daily.net_max_Ah.max()),SOC_accuracy='not_testable')
    result['post_primary_exploratory_supplements']=supplement
    # Frozen code/config hashes are verified without deleting/reopening scoring.
    manifest=json.loads((RUN/'freeze_manifest.json').read_text())
    mismatches=[x['path'] for x in manifest['files'] if digest(ROOT/x['path'])!=x['sha256']]
    assert not mismatches,mismatches
    result['frozen_source_fingerprints_unchanged']=True
    return result

def publish(o,s,result):
    out=RUN/'figures'
    fig,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained')
    thermal=pd.read_csv(RUN/'temperature_return_diagnostics.csv');p=thermal.pivot(index='seed',columns='stage',values='conditional_reference_capacity_Ah')
    for _,g in p.iterrows():axes[0].plot([0,1,2],g.to_numpy(),color='gray',alpha=.3)
    axes[0].plot([0,1,2],p.mean().to_numpy(),color='black',linewidth=2,label='Mean of 20 paired seeds')
    axes[0].set_xticks([0,1,2],['25 C','45 C','25 C return']);axes[0].set_xlabel('Controller-reset temperature stage');axes[0].set_ylabel('Conditional reference capacity from fitted scale (Ah)');axes[0].set_title('Synthetic constant health: all 60 updates rejected');axes[0].legend(fontsize=8)
    names=['M2_joint_common','M2_joint_free4','M2_gated'];positive=s[s.scenario.eq('informative_60Ah') & s.method.isin(names)]
    for i,name in enumerate(names):
        g=positive[positive.method.eq(name)];axes[1].scatter(np.full(len(g),i),g.capacity_error_Ah,color='gray',alpha=.55)
        if g.capacity_error_Ah.notna().any():axes[1].plot([i-.2,i+.2],[g.capacity_error_Ah.mean()]*2,color='black',linewidth=2)
    axes[1].set_xticks(range(3),['M2 common','M2 free4\n9/20 valid','M2 gated']);axes[1].set_xlabel('Synthetic reconstruction method');axes[1].set_ylabel('Reference group capacity absolute error (Ah)');axes[1].set_title('Informative 60 Ah: missing projections excluded, counted')
    fig.suptitle('Saved-score diagnostics: synthetic evidence, not real capacity accuracy')
    fig.savefig(out/'capacity_recovery_temperature_return.png',dpi=180);fig.savefig(out/'capacity_recovery_temperature_return.svg');plt.close(fig)
    # The optimized d(s) trace is a profile ridge, not a confidence region.
    import pickle
    events=pickle.loads((RUN/'events.pkl').read_bytes());selected=json.loads((RUN/'selected_configuration.json').read_text())
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for panel,ax in zip(['short','wide'],axes):
        e=[e for e in events if e['panel']==panel and e['T']==25][-1];tau=selected[f'{panel}_25']['tau'];z=np.load(RUN/'profiles'/f"{e['id'].replace(':','-')}_{tau}_free.npz")
        for c in range(4):ax.plot(z['sgrid'],z['params'][:,c,0],label=f'Cell {c+1}')
        ax.set_xlabel('Fixed common horizontal scale s (dimensionless)');ax.set_ylabel('Reoptimized start position d (reference Ah)');ax.set_title(panel+' 25 C; '+e['id'].split('_')[1][:10]);ax.legend(fontsize=8)
    fig.suptitle('Official post-event shift / stretch compensation: all nuisance terms refitted')
    fig.savefig(out/'shift_stretch_profile_ridges.png',dpi=180);plt.close(fig)
    # Add transparent supplements and failure coverage to the main narrative.
    free=[r for r in result['false_capacity_updates'] if r['method']=='M2_joint_free4'][0]
    gated=[r for r in result['false_capacity_updates'] if r['method']=='M2_gated'][0]
    common=[r for r in result['false_capacity_updates'] if r['method']=='M2_joint_common'][0]
    sup=result['post_primary_exploratory_supplements'];daily=sup['daily_chains'];thermal=sup['temperature_return']
    text=f'''\n## 合成机制、有效覆盖与补充诊断\n\n
以下补充项在主冻结评分后执行，属于探索诊断。主预测、模型、阈值和失败结果未改；补充结果不用于重新选择部署模型。

有信息60 Ah正例中，M2共同伸缩SOC MAE为{common['positive_SOC_mae_pp']:.3f} pp、s MAE为{common['positive_s_mae']:.4f}；四芯自由伸缩分别为{free['positive_SOC_mae_pp']:.3f} pp和{free['positive_s_mae']:.4f}。后者支持该模拟条件下的状态重建，但容量投影仅9/20个正例有效，全部300组合仅43个有效，257个因参考模板无法覆盖所需四芯坐标而无容量输出。因此不是已通过容量恢复。

恒容量压力场景：共同伸缩有{common['false_update_count']}/{common['n_seed_scenarios']}个已接受投影偏离参考容量超过2 Ah。四芯自由伸缩的错误投影为{free['false_update_count']}/{free['n_seed_scenarios']}个，但有{free['no_capacity_output_count']}个无法投影；低的全体错误率不能当成功。门控分支拒绝全部220个恒容量压力组合，但正例只接受{gated['positive_valid_acceptance']*100:.0f}%且s MAE={gated['positive_s_mae']:.4f}，未达到80%接受率和0.03误差目标。三种伸缩更新分支均未通过机制门。Wilson区间及按场景有效分母见`false_updates_by_scenario.csv`；种子误差分布见`synthetic_seed_variability.csv`。这些区间仅描述固定生成器的机制重复，不是跨真实电池泛化。

共同／收缩起点完成全参数优化后的前向补充结果：共同起点A/B分别1.248/1.323 mV；收缩芯间偏移A/B分别2.152/1.250 mV，均有46个输出。主基线A/B分别0.489/0.636 mV，仍未获得部署增量。主评分中的共同／收缩先验投影与这些完整优化版分开存储。

静置5/15/30分钟：形状法各只有24/46条事件满足长度条件。补充A的配对直接误差为3.660/3.380/3.188 mV，B为4.205/2.744/2.398 mV。该补充版沿用历史固定伸缩动态参数，与主评分中联用恢复形状拟合历史的M3_shape不同，不是同一模型只改等待预算。末点法只取预算内实际存在的末点，短静置事件没有凭空延长；三个预算不能用来声称宽事件有完整静置。分层和配对基线见补充评分表。

理想对照中，已知容量但仍用操作锚点初始化的SOC MAE均值1.631 pp；同时给定真实起点和容量后为0.006 pp。说明起点、容量和测量误差是不同来源；理想信息不可用于部署。25→45→25°C配对控制复位模拟中，容量物理参数恒定，拟合容量平均可逆变化{thermal['mean_abs_25_to_45_capacity_change_Ah']:.3f} Ah；返回25°C后配对差为0（同种子同控制轨迹），全部60次更新被门控拒绝。这不构成连续热状态模型或未知路径的验证。

日常运行另审核{daily['n_chains']}条锚点区间、{daily['rows']:,}条原始记录，其中{daily['n_fully_continuous']}条全程连续、{daily['n_chains_with_gap']}条有缺口。可观察的净Ah位置最大约{daily['max_observed_relative_Ah']:.2f} Ah；不是逐芯SOC。供使用的`daily_relative_charge_qualified_trace.csv`将首次缺口后的电量位置留空，原积分诊断保留且标记无连续资格。充电方向未套放电模板，没有全天电压预测或SOC真值精度结论。

正式接纳结论：本轮没有新的SOC／容量估计分支达到部署接纳门。M1可以保留为操作电量记账；M3可以保留为恢复诊断。两者的真实SOC作用及前向预测增量均未验证，不能称已接纳的辅助估计器。M2/M4保留研究用途。四个s暂不进入可信容量输出；这不意味着电池容量没有变化。\n'''
    p=TASK/'FINAL_REPORT.md';report=p.read_text()
    report=report.replace('M2共同/收缩起点预测消融不代替全局模型选择；四维搜索为否定见证而非全域证书。M3三个预算有恢复拟合诊断，正式主预测采用30分钟预算，尚未比较每个等待预算的完整部署性能。上述边界保留在决策文件，不能称所有扩展均已通过。','共同/收缩起点完整优化与各等待预算预测已另做评分后补充诊断，结果如下；四维搜索仍为否定见证而非全域证书。未验证完整全天充放电电压／SOC模型和外部真实精度，不能称所有扩展均已通过。')
    report=report.replace('主基线与时常','主基线与时间常数')
    report=report.replace('## 复现入口',text+'\n## 复现入口')
    p.write_text(report)
    (TASK/'NEXT_STEPS.md').write_text('''# 本轮仍未解决的问题与所需证据

1. 真实SOC与容量收益不可测：需要独立逐芯端点／OCV标定，以及同参考协议的四串组容量标签；不能从本模型生成标签。
2. 参考容量输出超域：四芯自由伸缩257/300模拟组合无法完成组截止投影。下一版本需要独立、更完整的参考电压标定与超域资格门；不允许增加任意外推来补齐成绩。
3. 相对动态模型事件外预测弱：需要能约束偏置、极化与路径的训练资料。共同/收缩模型及5/15/30分钟预算补充仍无基线增量；下一版本须预先冻结新规则，用新的测试资料验证。
4. 全天连续模型尚未验证：本轮完成了锚点内原始Ah记账和事件级状态继承，需要充放电双向标定、缺口／均衡观测及连续温度路径，才能评价全天SOC与电压预测。
5. 容量可辨性仍不成立：取得有形状信息的完整跨度，联合审查起点、偏置、动态和参考初态，确保容量投影有输出且对干扰稳定，再考虑释放四个s。
''')
    p=TASK/'README.md';p.write_text(p.read_text()+'''\n评分后的探索诊断和只读报告可运行：\n\n```sh
python3 research/phase2_initial_soc_four_methods_20261011/src/supplement.py
python3 research/phase2_initial_soc_four_methods_20261011/src/report.py
```

supplement.py有缓存；该命令不重新打开主测试、不修改主算法或评分。postprocess.py由report.py调用，读取保存输出，计数超域/无输出并生成补充图表。主报告明确记录评分后探索边界。`false_capacity_updates.csv`是原始优化旗标汇总，最终容量结论使用`false_capacity_updates_coverage_audited.csv`，其中无投影结果是失败/无输出。`daily_relative_charge_qualified_trace.csv`在缺口后留空。\n''')
    stage={
      'M1':('找起点，再记账','可信操作终点与连续净Ah能减少任意重置的自由度。','已结束CCCV、前静置、原始共同电流与连续时间链；未使用未来满充。','按固定锚点规则追踪参考Ah，比较共同／逐芯起点、固定／更新伸缩、朴素满充重置。','71/75条事件可连接，评分直接覆盖44/46；M1_cell前向A/B为1.882/1.320 mV，配对主基线0.489/0.636 mV。模拟正例M1 SOC MAE 7.066 pp，优于朴素满充31.576 pp，但未到3 pp状态目标。','少充、均衡、电流偏差和容量变化时，同一Ah不对应同一SOC百分比。操作充电终点并不能证明四芯100%。','相对Ah传播规则传入后续探索；不作为已通过精度门的SOC观测。'),
      'M2':('曲线平移与伸缩','形状和跨度足够时，起点与容量尺度可分别约束。','CK0各芯带载模板、完成的历史同层事件；目标仅预算A/B前缀。','共同／逐芯s、固定／自由／先验d及动态干扰联合剖面；完整共同／收缩d另做补充优化。','主联合A/B 2.205/4.574 mV；完整共同d补充1.248/1.323 mV，均未胜冻结基线。四芯自由s在模拟正例SOC MAE0.708 pp、s MAE0.0194，但容量输出仅9/20正例和43/300全部组合。','官方条件容量剖面宽20.08–35.14 Ah，联合见证跨度7.56–25.10 Ah；共同s在220恒容量压力中189次虚假投影。四芯自由s有208/220压力无投影。','容量不可辨时冻结s；剖面与历史动态信息可进入探索，不传入可信容量输出。'),
      'M3':('静置末点与恢复形状','恢复信息能约束极化；独立OCV标定才可能约束SOC。','当时已出现的5/15/30分钟静置前缀；官方无适用逐芯OCV–SOC标尺。','末点相对电压对齐；未知渐近电压＋受限恢复项；模拟单列独立初始OCV标定。','主M3_shape前向A/B 1.766/0.887 mV，直接覆盖24/46。模拟标定OCV末点／形状SOC MAE为6.340/5.428 pp；不是官方精度。三个等待预算的完整补充预测已保存。','宽事件前静置常约50秒，不具备完整预算；平台电压、前序路径、温度和偏置不能全解释成SOC差。补充形状分支的直接前向误差仍明显高于同集合基线。','恢复诊断传入M4消融，但不是已接纳SOC或电压辅助估计器。'),
      'M4':('连续状态校正','积分传播与合理不确定性配合有信息观测，能改善状态跟踪。','原始电压一次性更新、M1操作链和历史参数；预测快照在允许前缀后只接收I/T。','参考位置＋极化EKF，固定／无门控／门控s及去除M1/M2/M3消融；在线与前向分开存储。','主M4_fixed A/B 9.747/9.397 mV，未过前向门。模拟第二事件M4固定／门控s在线SOC MAE2.856/1.419 pp，输入角色与M2重建不同。正例名义95%位置区间覆盖66.3%/89.7%，不确定性尚未充分校准。','去M1后模拟SOC MAE32.202 pp；去M3为2.845 pp，未见该正例静置增量。-20 pp扰动仅2/20种子达到短期收敛判据；达到判据也可能末段再发散。全拒绝压力更新不能证明容量辨识。','当前实现仅研究；保留有资格链的状态继承，不释放无证据容量更新。'),
    }
    for m,(title,hypothesis,inputs,implementation,findings,counterexample,nextstage) in stage.items():
        info=result['methods'][m]
        body=f'''# {m}：{title}\n\n
假设：{hypothesis}\n\n输入与因果边界：{inputs}\n\n实现与对照：{implementation}\n\n结果：{findings}\n\n反例与失败：{counterexample}\n\n证据等级：S为固定生成器机制重复，O为此前曝光官方单组的冻结规则前向回放；合法R独立逐芯SOC与后续同协议容量真值缺失，真实准确性不可测。18项科学不变量检查通过，不等于统计精度或容量门通过。\n\n传入下一阶段：{nextstage}\n\n最终用途：{info['recommendation']}。补充诊断在主评分后完成、未更改冻结模型，不当作新的封存接纳证据。\n\n逐事件／模拟指标：runs/v1/official_evaluation_metrics.csv与synthetic_evaluation_metrics.csv；最终结构化状态见decision.json，详细边界见FINAL_REPORT.md。\n'''
        (TASK/f'{m}_STAGE_REPORT.md').write_text(body)
    p=TASK/'FINAL_REPORT.md';p.write_text(p.read_text()+'''\n## 不确定性与初值压力的补充说明\n\n
模拟正例中，M4固定s／门控s的名义95%参考位置区间实际覆盖约66.3%／89.7%，不能认为区间已经校准。初值±5/10/20 pp试验以生成器真实起点为中心施加扰动，属于理想中心压力测试，不是可部署初始化。-20 pp只有2/20个种子出现连续10点低于3 pp；其他扰动中也存在达到该短期判据后末段再次发散。缺失／超域时点计入有限输出比例，具体见initial_error_convergence_summary.csv。M4的在线SOC分数不能与M2已看完整当前曲线的重建分数作同预算排名。\n''')
