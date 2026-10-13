"""Generate Chinese evidence report, scientific export plots and inline canvas data."""
from __future__ import annotations
import json,re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import TASK,ROOT,OUT,CFG,json_dump,digest,environment

NAMES={'B_previous':'上一同温同程序事件','B_previous_rest':'上一事件＋前静置平移','M_fixed':'共享动态，容量固定','M_gated':'门控保留固定容量','M_ungated':'共享动态，容量释放','M_no_charge':'去充电电流历史','M_no_rest':'去静置拟合与初始化','M_mean_cells':'历史拟合用均压，初始化仍用四芯'}

def readjson(name):return json.loads((OUT/name).read_text())

def clean(value):
    if isinstance(value,dict):return {k:clean(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [clean(v) for v in value]
    if isinstance(value,(np.integer,np.floating)):value=value.item()
    if isinstance(value,float) and not np.isfinite(value):return None
    return value

def run():
    required=['EVALUATION_COMPLETE','MECHANISM_TEST_COMPLETE','THERMAL_SUPPLEMENT_COMPLETE','TEMPLATE_SUPPLEMENT_COMPLETE','MEAN_CHANNEL_SUPPLEMENT_COMPLETE']
    missing=[f for f in required if not (OUT/f).exists()]
    if missing:raise RuntimeError('Still required: '+str(missing))
    # A fresh reproduction has the final configuration from its first audit.
    # Preserve the initial audit and match the separate pre-score config hash.
    if not (OUT/'data_manifest_final.json').exists():
        initial=readjson('data_manifest.json');frozen=readjson('freeze_manifest.json');final=[];changes=[]
        for row in initial:
            r=dict(row)
            if r['path']==str((TASK/'configs/protocol.json').relative_to(ROOT)):
                actual=digest(TASK/'configs/protocol.json');assert actual==frozen['config_sha256']
                if r['sha256']!=actual:changes.append(dict(path=r['path'],initial_audit_sha256=r['sha256'],pre_scoring_frozen_sha256=actual))
                r['sha256']=actual;r['bytes']=(TASK/'configs/protocol.json').stat().st_size
            final.append(r)
        json_dump(OUT/'data_manifest_final.json',final)
        json_dump(OUT/'config_registration_history.json',dict(original_manifest_unchanged=True,changes=changes,post_scoring_model_tuning=False))
    if not (OUT/'reference_projection_correction.json').exists():
        provenance=TASK/'runs/v1/reference_projection_correction.json'
        if provenance.exists():
            previous=json.loads(provenance.read_text())
            if previous['corrected_source_sha256']==digest(TASK/'src/ecm.py'):
                previous['inherited_original_v1_provenance']=str(provenance)
                previous['new_correction_in_this_reproduction']=False
                json_dump(OUT/'reference_projection_correction.json',previous)
    summary=pd.read_csv(OUT/'forward_summary.csv');events=pd.read_csv(OUT/'forward_event_metrics.csv')
    ck=pd.read_csv(OUT/'checkup_profiles.csv');curves=pd.read_csv(OUT/'profile_curves.csv');base=ck[(ck.checkup=='CK7')&(ck.model=='base')]
    mechanisms=pd.read_csv(OUT/'mechanism_test_summary.csv');mdecision=readjson('mechanism_test_decision.json')
    science=readjson('science_checks.json');audit=readjson('audit_summary.json');cal=readjson('calibration_gate.json')
    thermal=readjson('thermal_return_summary.json');ident=readjson('identifiability_diagnostics.json');witness=readjson('independent_optimizer_witnesses.json')
    union=[r for r in ident if r.get('checkup')=='CK7' and 'structural_union_width_Ah' in r]
    A=pd.read_csv(OUT/'A_quality_diagnostics.csv');template=pd.read_csv(OUT/'template_supplement.csv');stage=pd.read_csv(OUT/'CK7_stage_reconstruction.csv')
    histparams=readjson('historical_parameters.json');protected=readjson('protected_before.json')
    untouched=[dict(path=r['path'],same_sha256=digest(ROOT/r['path'])==r['sha256']) for r in protected]
    assert all(r['same_sha256'] for r in untouched)
    temporal=[r for r in histparams if pd.Timestamp(r['history_available_after'])>=pd.Timestamp(next(e['start'] for e in events.to_dict('records') if e['id']==r['id']))]
    assert not temporal
    # Whole time-block resampling of paired event differences; one physical pack.
    rng=np.random.default_rng(9081);bootstrap=[]
    for budget in ['A','B']:
        order=events[events.budget.eq(budget)&events.method.eq('M_ungated')].sort_values('start').id.tolist()
        pivot=events[events.budget.eq(budget)].pivot(index='id',columns='method',values='mae_mV').reindex(order)
        delta=pivot.M_ungated-pivot.B_previous
        blocks=[delta.iloc[k:k+5].to_numpy() for k in range(0,len(delta),5)]
        draws=[np.concatenate([blocks[k] for k in rng.integers(0,len(blocks),len(blocks))]).mean() for _ in range(1000)]
        bootstrap.append(dict(budget=budget,paired_difference_mV=float(delta.mean()),block5_resampling_q025_mV=float(np.quantile(draws,.025)),
            block5_resampling_q975_mV=float(np.quantile(draws,.975)),interpretation='Descriptive replay uncertainty within one pack, not cross-pack confidence'))
    # Compare previous and new methods on identical saved event IDs, no old retuning.
    old=pd.read_csv(ROOT/'research/phase2_initial_soc_four_methods_20261011/runs/v1/official_evaluation_metrics.csv')
    paired=[]
    for budget in ['A','B']:
        previous=old[(old.budget==budget)&(old.method=='M4_fixed')][['id','mae_mV']]
        here=events[(events.budget==budget)&(events.method=='M_fixed')][['id','mae_mV']]
        same=previous.merge(here,on='id',suffixes=('_old','_new'))
        paired.append(dict(budget=budget,common_events=len(same),old_M4_mae_mV=float(same.mae_mV_old.mean()),new_shared_fixed_mae_mV=float(same.mae_mV_new.mean()),
            note='Same saved event IDs; old per-panel tuning versus new calendar split differ; descriptive, not new independent test'))
    # Conditional diagnostic point values never become reliable CK capacity output.
    ck_output=[]
    for query in pd.read_csv(ROOT/'data/checkups/evaluation_points.csv').itertuples():
        ck_output.append(dict(checkup=query.checkup,date=query.date,reliable_capacity_Ah=100.41 if query.checkup=='CK0' else None,
            fallback_capacity_Ah=100.41,fallback_SOH_pct=100*100.41/102,
            capacity_update=False,status='released_CK0_anchor' if query.checkup=='CK0' else 'REJECTED_capacity_update_UNVERIFIED_accuracy',hidden_capacity_error_Ah=None))
    pd.DataFrame(ck_output).to_csv(OUT/'checkup_decisions.csv',index=False)
    gated=events[events.method=='M_gated']
    assert np.allclose(gated.alpha.dropna(),1.)
    gates=[dict(id='G0',name='数据与协议审计',status='PASS',note='75事件，71连续锚点；采用带载参考路径L，OCV资格未证实'),
        dict(id='G1',name='共享动态模型可用性',status='FAIL',note='开发与后续向前电压性能均落后简单基线'),
        dict(id='G2',name='容量可辨识性',status='FAIL',note='容量集合宽、结构并集更宽，部分候选超域，不能据优化点更新'),
        dict(id='G3',name='冻结向前与机制验收',status='FAIL',note='50事件无动态增量；信息正例门控接受0/10'),
        dict(id='G4',name='参考组端截止计算',status='PASS',note='仅数值与条件回代；未知满充不均衡/参考温度的实际转换仍未验收'),
        dict(id='G5',name='独立真实容量精度',status='UNVERIFIED',note='后续官方容量和同协议独立4S组标签不可用')]
    evidence=dict(date='2026-10-13',branch=environment()['branch'],decision='REJECT_CURRENT_CAPACITY_MODEL',gates=gates,audit=audit,
        forward=summary.to_dict('records'),strata=pd.read_csv(OUT/'forward_strata.csv').to_dict('records'),
        CK7=base.to_dict('records'),CK7_structural_union=union,mechanism=mdecision,mechanism_summary=mechanisms.to_dict('records'),
        thermal_return=thermal,science_checks_passed=science['passed'],template_sensitivity=template.to_dict('records'),
        mean_channel_supplement=pd.read_csv(OUT/'mean_channel_summary.csv').to_dict('records'),
        A_role='correlated quality trend only; no calibrated capacity-rate/residual correction',
        protection=untouched,temporal_violations=0,paired_block_uncertainty=bootstrap,paired_old_new=paired,
        conditional_covariance_calibrated=False,real_capacity_accuracy='UNVERIFIED',all_hidden_capacity_errors=None)
    json_dump(OUT/'evidence_summary.json',clean(evidence))
    # Export scientific figures with actual numeric axes.
    fig,ax=plt.subplots(2,2,figsize=(12,8),constrained_layout=True)
    methods=['B_previous','M_fixed','M_ungated','M_no_rest']
    labels=['Previous event','Shared fixed Q','Shared free Q','No rest']
    for k,budget in enumerate(['A','B']):
        ss=summary[summary.budget.eq(budget)].set_index('method')
        y=[ss.loc[m,'mae_mV'] for m in methods]
        ax[0,0].bar(np.arange(4)+(k-.5)*.36,y,.36,label='0 Ah prefix' if k==0 else '1 Ah prefix')
    ax[0,0].set_xticks(np.arange(4),labels);ax[0,0].set_ylabel('Cell voltage MAE (mV)');ax[0,0].set_xlabel('Given-drive forecast method');ax[0,0].set_title('50 historical pack events, 2025 Apr-Aug');ax[0,0].legend()
    for T in [25,45]:
        p=curves[(curves.checkup=='CK7')&(curves['T']==T)&(curves.model=='base')]
        finite=p[np.isfinite(p.rms_mV)];minimum=finite.rms_mV.min()
        ax[0,1].plot(finite.capacity_Ah,finite.rms_mV-minimum,label=f'{T} C')
    ax[0,1].axhline(1,color='gray',ls='--',label='Minimum +1 mV');ax[0,1].set_xlabel('Conditional reference-pack capacity (Ah)');ax[0,1].set_ylabel('Increase from min weighted RMS (mV)');ax[0,1].set_title('CK7 profile: not capacity truth');ax[0,1].legend()
    positive=mechanisms[mechanisms.scenario.eq('informative_capacity')]
    pp=positive.set_index('method')
    ax[1,0].bar(['Fixed/fallback','Ungated point'],[pp.loc['local_gated','mean_error_Ah'],pp.loc['ungated','mean_error_Ah']])
    ax[1,0].set_ylabel('Simulated reference-capacity MAE (Ah)');ax[1,0].set_xlabel('Estimator branch');ax[1,0].set_title('10 positive seeds: gated acceptance 0/10')
    uu=sorted(union,key=lambda r:r['T'])
    ax[1,1].bar(['25 C','45 C'],[r['structural_union_width_Ah'] for r in uu]);ax[1,1].axhline(5,color='gray',ls='--',label='5 Ah research target')
    ax[1,1].set_xlabel('Chamber setpoint');ax[1,1].set_ylabel('Structural sensitivity union width (Ah)');ax[1,1].set_title('CK7: uncertainty under registered assumptions');ax[1,1].legend()
    fig.savefig(OUT/'validation_overview.png',dpi=180);fig.savefig(OUT/'validation_overview.svg');plt.close(fig)
    # Canvas data use only the 0.5Ah primary grid, to retain uniform horizontal spacing.
    profile_data=[]
    for (query,T,model),p in curves.groupby(['checkup','T','model']):
        p=p[np.isfinite(p.rms_mV)&np.isclose(p.capacity_Ah*2,np.round(p.capacity_Ah*2))]
        if len(p):profile_data.append(dict(checkup=query,T=int(T),model=model,q=p.capacity_Ah.round(2).tolist(),rms=p.rms_mV.round(4).tolist()))
    traces=pd.read_csv(OUT/'forward_traces.csv');examples=[]
    for T in [25,45]:
        for panel in ['short','wide']:
            subset=traces[(traces['T']==T)&traces.panel.eq(panel)&traces.budget.eq('B')]
            if not len(subset):continue
            event_id=sorted(subset.id.unique())[-1]
            subset=subset[subset.id.eq(event_id)]
            for method in ['B_previous','M_fixed','M_ungated']:
                s=subset[subset.method.eq(method)]
                examples.append(dict(T=T,panel=panel,id=event_id,method=method,q=s.q_Ah.round(3).tolist(),actual=s.actual_mean_cell_V.round(6).tolist(),predicted=s.predicted_mean_cell_V.round(6).tolist()))
    data=dict(summary=evidence,profiles=profile_data,checkups=ck.to_dict('records'),A=A.to_dict('records'),examples=examples)
    json_dump(OUT/'canvas_data.json',clean(data))
    sidx=summary.set_index(['budget','method'])
    def budget_lines(b):return '\n'.join(f"- {NAMES[m]}：{sidx.loc[(b,m),'mae_mV']:.3f} mV；直接输出覆盖 {sidx.loc[(b,m),'direct_coverage']:.0%}。" for m in methods)
    unions={r['T']:r for r in union};bb=base.set_index('T')
    positive=mechanisms[(mechanisms.scenario=='informative_capacity')].set_index('method')
    maximum_opt=max(r['variable_projection_rms_mV']-r['independent_optimizer_rms_mV'] for r in witness if r.get('available'))
    registration_changed=bool(readjson('config_registration_history.json')['changes'])
    registration_note=('初始原始审计之后、开发和首次评分之前，补充登记了温度响应边界与目标前静置初始化设置；初审配置哈希与最终冻结配置不同，原记录保留。' if registration_changed else '本复现从开始使用已经冻结的最终配置，初始审计配置与最终配置一致。')
    report=f'''# 方案 2：四串动态模型与容量联合估计——完整执行验证报告

执行日期：2026-10-13。分支：`{environment()['branch']}`。执行依据：[原始执行 Prompt](../phase2_routes23_prompts_20261012/方案2_四串动态模型与容量联合估计_执行Prompt.md)。本轮代码、配置、数据指纹及结果都保存在本目录。

## 先向导师汇报结论

**这次确实把实际电压、电流、温度和充放电历史放进了容量识别过程，但当前版本没有通过接纳条件。不能用它替换现有 B，也没有得到可信的 CK1–CK7 容量更新。**

我们尝试让几个历史事件共享一套动态参数，减少“每条曲线都能随意调参数”的问题。结果是模型难以同时解释静置、带载放电和不同历史路径：后续事件预测明显落后于简单的上一事件曲线。容量优化能给出数字，但这些数字依赖有缺陷的模型和条件假设。

研究流程、原始审计及数值实现已完成。24 项科学正确性检查通过；这些检查不代表容量精度达标。没有独立 OCV、逐芯 SOC 及后续真实组容量，真实容量精度门保持未验证。

## 1. 我具体做了什么

1. 创建独立分支，保护原研究和正式模型；按原文核对 Zhou/Yi 的公式、起点/OCV前提和更新分工。
2. 重新回读原始记录，认证 39 条约10Ah和36条约32.9Ah放电，共75条组事件；71条可连接合格CCCV操作锚点。温度/芯压不是独立电池样本。
3. 从认证充电终点开始累计净放出Ah，把之前真实充电/日常电流传播到当前极化响应。保持四个芯压通道，加入实际温度偏差，组压作为相关观测质量检查。
4. 建立受约束移动窗模型：最近同温度最多4个已完成事件共享逐芯起点偏移、偏置、表观R及慢响应，一个共同容量伸缩。再做8事件等敏感性。
5. 用前25条事件开发，之后50条事件固定规则向前回放。两种输入预算分开：不使用当前放电电压；或只用首1Ah，2Ah后评分。后段电压不能校正预测。
6. 对每个CK合法前缀扫描最终参考组容量，并让其他参数重新拟合；核查偏置、时常、起点、静置和历史长度等10种结构。额外测试原始模板与小幅形状扰动。
7. 使用独立两阶RC、非线性OCV、温度/路径/控制终点生成器，完成11场景×10测试种子=110个机制组合；另外10种子完成25→45→25°C控制复位对照。
8. 验证四芯参考放电到组端首次11.2V的求根；计算A的过去充电窗口趋势，作为相关质量诊断。

## 2. 论文方法如何进入本项目

Zhou2025 的原模型为 OCV加工况相关电阻，容量/阻抗慢状态由GP表达；其已知起始SOC和初始RPT标定是重要前提。Yi2024的1RC、偏置补偿及高斜率更新策略依赖独立OCV和专用激励。官方10s数据不能恢复其0.5Hz激励，未知SOC也不能照搬分区。

本轮核对阶段一实际路径 `/Users/shane/Desktop/项目/Current State_Challenge1` 及当前原始65个CSV、六颗实体；读取全文件名/哈希和每文件前5000行作资格审计，没有获得可信的目标四芯完整OCV/SOC标尺。型号/批次相同仍未证明。采用Prompt许可的路径L，不伪造OCV。

因此状态叫“参考Ah位置”，不是绝对SOC。CC/CV电压用于阶段/操作锚点和A窗口；充电电流用于电量及极化历史。放电/静置电压进入观察方程。**没有完成独立充电电压观察方程或全天绝对SOC模型验收。**这些是明确缺项，不能宣称论文精度已复现。见[实现对照](paper_to_project.md)、[标定资格](runs/v1/calibration_gate.json)。

## 3. 与上次失败模型有什么实质区别

原方法每事件可独立调整起点和动态参数；本轮强制同温窗口共享这些参数，并从真实充电历史初始化极化。观察式为 `V_i=F_i(net/alpha+d_i)+b_i-r0_i(j-5.1)-r1_i(h-h_ref)+beta_i·(T_actual-T_set)`，j=-I。

F已经含CK0带载压降，只加相对修正；容量由运行电压残差约束，而不是由阶段一N/T衰减曲线提供。变化是真实的输入/参数约束改动，也强化了“跨事件相同参数”的假设。拟合变差说明这一假设和观察表达需要改造；不能把约束更强带来的窄范围当新信息。

旧失败子集复现3个事件，容量范围仍很宽；两个存在的对应缓存误差逐位一致，第三没有可比缓存。原完整评分没有重开。见[子集复现](runs/v1/prior_reproduction.csv)。

## 4. 向前电压验证：当前版本明显落后基线

单位为单芯mV：先平均四芯，再平均物理组事件。50个评价事件全部有输出，含回退；它们来自一个真实组，已经被历史研究曝光。实际I/T作为已给定驱动，不能称未知未来工况预测。这里的输入预算A/B与健康方案A不是同一概念。

### 不使用当前放电电压（预算A）

{budget_lines('A')}

### 仅使用首1Ah，2Ah后评分（预算B）

{budget_lines('B')}

主门控分支保持alpha=1，因此与固定容量分支相同；没有在低信息条件下接纳容量更新。释放容量分支仅作研究反证，不是已接纳模型。去静置版本同时去掉历史静置拟合和目标前静置初始化，仍输给基线；这提示当前静置观察/初始化不相容，不能推广为静置没有价值。

历史均压拟合和去充电历史也没有达到接纳门。主评分的M_mean_cells只平均历史拟合，目标初始化仍保留四芯；它不是完整移除逐芯信息。另执行了从参考、历史到目标初始化都只用均压的完整消融，采用相同“组内均压预测误差”任务比较，单列[补充结果](runs/v1/mean_channel_summary.csv)，不与单芯绝对误差指标混用或用于选模型。尚未证明四个独立容量参数可辨。完整逐事件、分层、覆盖和失败在[回放数据](runs/v1/forward_event_metrics.csv)、[分层](runs/v1/forward_strata.csv)、[性能决定](runs/v1/dynamic_decisions.json)。

## 5. CK7容量数字为何不能接受

25°C条件最优点为 {bb.loc[25,'best_capacity_Ah']:.2f}Ah，基础最小RMS为 {bb.loc[25,'minimum_RMS_mV']:.3f}mV；+1mV集合 {bb.loc[25,'lower_Ah']:.1f}–{bb.loc[25,'upper_Ah']:.1f}Ah，宽 {bb.loc[25,'width_Ah']:.1f}Ah。45°C点为 {bb.loc[45,'best_capacity_Ah']:.2f}Ah，RMS {bb.loc[45,'minimum_RMS_mV']:.3f}mV；集合 {bb.loc[45,'lower_Ah']:.1f}–{bb.loc[45,'upper_Ah']:.1f}Ah，宽 {bb.loc[45,'width_Ah']:.1f}Ah。

**这些点是未过关模型的条件优化结果，不是真实CK7容量或可发布SOH。**基础宽度已超过5Ah目标，结构情景集合并集更宽：25°C {unions[25]['structural_union_width_Ah']:.1f}Ah，45°C {unions[45]['structural_union_width_Ah']:.1f}Ah。每温度14个低容量候选因观察坐标超出模板域未得到有效检验，不能删除它们来制造窄范围。

25°C参数最近可见资料到8月7日，45°C到8月27日；两者不应当作同一时刻、同样暴露下的两个独立容量测量。温度/年龄存在混杂，未用简单平均强行合成一个官方容量。

独立非线性优化器核查80/100Ah的干扰重拟合，所有可比位置最大RMS改善仅 {maximum_opt:.4f}mV，未见会改变拒绝结论的数值优化问题。基础CK7两个温度层的8个逐芯温度响应系数均触+2mV/°C边界，输入仍是共享温度统计量，不能当作独立逐芯测温或已标定温度规律。局部灵敏度和替代参数见[诊断](runs/v1/identifiability_diagnostics.json)、[独立优化核查](runs/v1/independent_optimizer_witnesses.json)。敏感性集合不是95%置信区间。

## 6. 合成反证：避免把“全拒绝”算成功

110个测试组合按事先分开的种子运行。信息正例中，不门控点估计的容量MAE为 {positive.loc['ungated','mean_error_Ah']:.3f}Ah，平均相对误差 {positive.loc['ungated','mean_relative_error']:.2%}；说明受控条件下优化器能找出接近真值的点。

但是+1mV容量集合平均仍宽 {positive.loc['local_gated','width_Ah']:.2f}Ah，门控接受 {mdecision['positive_acceptance']:.0%}，不足80%目标。保留参考容量的回退MAE为 {positive.loc['local_gated','mean_error_Ah']:.3f}Ah，约 {positive.loc['local_gated','mean_relative_error']:.2%}。零接纳意味着也漏掉真正的容量下降。

90个恒物理容量压力组合中，门控全部拒绝，错误接纳0/90；这不能算完整成功。不门控的各场景误差、无输出和缺段拒绝单独保留。参考真值用独立生成器新满充、25°C、5.1A到组端11.2V，不把伸缩参数本身当标签；10/5s积分最大差约 {mdecision['ref_dt_error_max_Ah']:.6f}Ah。证据只支持机制测试，不代表真实组泛化。见[机制评分](runs/v1/mechanism_test_scores.csv)。

温度返回补充采用每温度重新控制满充的25→45→25对照，10个配对种子。条件点估计升温平均改变 {thermal['conditional_warm_minus_initial_mean_Ah']:.2f}Ah，返回后的配对绝对差平均 {thermal['conditional_return_abs_mean_Ah']:.2f}Ah，30次局部门全部拒绝。它支持观察温度混杂，**不是连续未知路径的热状态验证**。该补充和模板扰动在主评分后单列，未用于选模型、调阈值或改主成绩。

## 7. 四芯容量如何转成官方组容量

主条件投影使用四条CK0带载曲线，保留组压与四芯和的基准残差一次，在共同-5.1A下求组端首次11.2V。参考满充初态固定为CK0时，纯共同伸缩Qpack=alpha×100.41Ah。运行d、b、临时极化和温度偏差不带入这个参考状态。

求根回代100.41Ah通过；共同参考起点变化也要同步移动基准组压残差。末轮核查修正了这个映射细节，保存原源码，证明主预测及零起点容量逐点差为0，仅重跑参考扰动和科学检查。详见[修正记录](runs/v1/reference_projection_correction.json)。

共同已知起点偏移可以条件计算；某一芯单独不均衡、正向组压漂移可能需要超出已测末端的电压，不做无边界外推，记录无输出。均衡电流和参考满充状态仍未知，因此四芯不同的容量/起点变化没有获得实际组端容量验收。不能直接求平均、求和或取最小代替协议容量。见[参考假设](runs/v1/reference_assumptions.csv)。

## 8. 方案A怎样参与，实际做到了哪一步

只从查询前已经结束的充电事件提取预先固定的电压窗口ΔAh，按温度和芯号计算过去最多8事件的变化率，单位Ah/day；少于3个合格事件的趋势留空。它可以指示工况/形状冲突，不自动成为容量衰减率或指数系数。

本轮执行了质量诊断用途。主动态模型未过关，且没有独立目标容量标签或变化率标定，未训练A的容量残差/指数修正器。A与主模型同源，不能当额外独立容量观测收窄区间。见[A诊断](runs/v1/A_quality_diagnostics.csv)。

## 9. 验收状态、复现与下一步

G0数据/协议PASS；G1动态模型FAIL；G2辨识FAIL；G3向前与机制FAIL；G4条件数值求根PASS，实际参考初态转换未验证；G5独立真实容量精度UNVERIFIED。依据原Prompt，动态门失败后停止高维GP升级，完成反证、条件投影和辅助诊断。

24项检查包含电流符号/3600、参考恒等/首截止、阶段重复时间戳、历史参数可见性、未来电压/电量不能改变前缀初始化、缺口/超域拒绝、Joseph协方差与NLML数学式、在线协方差PSD和冻结容量。在线输出是固定慢参数条件下的参考位置/极化，未校准成真实SOC或容量区间。正式模型、框架及旧决策文件哈希核验一致。

{registration_note}最终输入索引与首评分前配置哈希对齐，实际数据/论文哈希和评分选择未变。见[配置登记沿革](runs/v1/config_registration_history.json)、[最终输入清单](runs/v1/data_manifest_final.json)。

下一次应先改善方向/温度/恢复观察的标定，并允许经过验证的跨事件动态变化；先在同输入预算下超过上一事件基线，再释放容量。完整充电观察需独立方向标尺，容量输出需同协议后续组容量验收；跨组泛化需独立物理组。单纯改滤波器或降低本轮阈值不能修复已经暴露的模型误差。

复现入口见[README](README.md)。全部结果包括失败、拒绝、回退和可见截止；CK1–CK7真实误差留空。固定CK0回退用于研究决策表，不当作通过验证的新容量估计。完整数值源在runs/v1，图为[PNG](runs/v1/validation_overview.png)及[SVG](runs/v1/validation_overview.svg)。
'''
    report=report.replace('runs/v1',str(OUT.relative_to(TASK)))
    def absolute_link(match):
        label,destination=match.groups()
        if '://' in destination:return match.group(0)
        return '['+label+'](<'+str((TASK/destination).resolve())+'>)'
    report=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',absolute_link,report)
    (OUT/'完整执行验证报告.md').write_text(report)
    if OUT.name=='v1':(TASK/'完整执行验证报告.md').write_text(report)
    json_dump(OUT/'final_integrity.json',dict(protected_files_unchanged=all(r['same_sha256'] for r in untouched),historical_parameter_time_violations=len(temporal),
        capacity_updates_admitted=0,science_checks_passed=science['passed'],primary_results_not_retuned_after_scoring=True,
        conditional_reference_mapping_correction=readjson('reference_projection_correction.json') if (OUT/'reference_projection_correction.json').exists() else 'Already corrected in this fresh reproduction',
        supplemental_analysis_does_not_select_primary_model=True))
    print('Chinese report, evidence summary and scientific plots saved',flush=True)

if __name__=='__main__':run()
