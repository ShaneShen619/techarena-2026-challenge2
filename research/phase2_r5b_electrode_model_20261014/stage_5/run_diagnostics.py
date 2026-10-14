"""Nominal degradation profiles, causal cell-limit diagnostics and recovery coverage."""
import hashlib
import json
import pickle
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import chi2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent
STUDY=HERE.parent
sys.path[:0]=[str(STUDY/'src'),str(STUDY/'stage_3')]
from common5b import H,CACHE5
from edata import anchor_curve
from emodel import OCP,fit_charge
from events import iter_segments,segment_arrays,_cv_ends
from v2 import anchors_by_checkup
from audit5b import dump,clean_json,physical_charge,bilingual
from profile_pack import quantities,c20_root,individual_limits
from run_fits import cache_key

if __name__=='__main__':
    (HERE/'outputs').mkdir(exist_ok=True)
    start=time.time();cap=2700
    fits=pd.read_csv(STUDY/'stage_3/outputs/S3_main_fits.csv')
    lli=pd.read_csv(STUDY/'stage_3/outputs/S3_LLI_profile_fits.csv')
    intervals=[];profile_rows=[]
    threshold=chi2.ppf(.975,1)
    ocp=OCP('main');op=H.full_op();anc=anchors_by_checkup(H.full_charges(op),H.CK)
    source_hash=hashlib.sha256(Path(__file__).read_bytes()+(HERE/'protocol.json').read_bytes()).hexdigest()
    for j in range(8):
        q,I,V,_,qt=anchor_curve(op,anc[j])
        for c in range(4):
            row=fits[(fits.anchor==j)&(fits.cell==c+1)].iloc[0]
            base=row[['Qn','Qp','QLi','theta_n0','R','h']].to_numpy(float)
            l=lli[(lli.anchor==j)&(lli.cell==c+1)&lli.physical_valid&(lli.profile_statistic<=threshold)]
            intervals.append({'anchor':j,'cell':c+1,'parameter':'QLi','lower':float(l.QLi.min()),'upper':float(l.QLi.max()),
                              'boundary':bool((l.QLi<=50).any() or (l.QLi>=250).any()),'grid_complete':True})
            for index,name in [(0,'Qn'),(1,'Qp')]:
                grid=np.unique(np.r_[np.arange(60.,200.01,10.),base[index],base[index]+np.r_[
                    -64.,-32.,-16.,-8.,-4.,-2.,-1.,-.5,-.25,.25,.5,1.,2.,4.,8.,16.,32.,64.]])
                grid=grid[(grid>=60)&(grid<=200)]
                last=base.copy();records=[]
                for value in sorted(grid,key=lambda v:abs(v-base[index])):
                    if time.time()-start>cap:break
                    starts=[base,last]
                    key=cache_key(q,I,V[:,c],{index:float(value)})
                    key=hashlib.sha256((key+source_hash+repr(np.asarray(starts).tolist())).encode()).hexdigest()
                    path=Path(CACHE5)/f'modeprofile_{key}.pkl'
                    if path.exists():x,info=pickle.loads(path.read_bytes())
                    else:
                        x,info=fit_charge(q,I,V[:,c],ocp,x0_list=starts,fixed={index:float(value)})
                        path.write_bytes(pickle.dumps((x,info),protocol=5))
                    last=x
                    records.append({'anchor':j,'cell':c+1,'parameter':name,'fixed_value':float(value),
                        'cost':float(info['cost']),'rms_mV':float(info['rms_mV']),
                        'physical_valid':physical_charge(x,qt,ocp),**{n:float(v) for n,v in zip(['Qn','Qp','QLi','theta_n0','R','h'],x)}})
                valid=[r for r in records if r['physical_valid']]
                minimum=min([row.cost]+[r['cost'] for r in valid])
                for r in records:
                    stat=max(0.,2*(r['cost']-minimum)/max(2.,row.rms_mV)**2*row.n_eff/row.n)
                    r['profile_statistic']=stat;r['accepted97p5']=bool(r['physical_valid'] and stat<=threshold)
                accepted=[r['fixed_value'] for r in records if r['accepted97p5']]
                intervals.append({'anchor':j,'cell':c+1,'parameter':name,
                    'lower':min(accepted) if accepted else np.nan,'upper':max(accepted) if accepted else np.nan,
                    'boundary':bool(accepted and (min(accepted)<=60 or max(accepted)>=200)),
                    'grid_complete':len(records)==len(grid)})
                profile_rows.extend(records)
                pd.DataFrame(profile_rows).to_csv(HERE/'outputs/S5_material_profiles.csv',index=False)
                print(f'mode profile anchor{j}, cell{c+1}, {name}: {len(records)} refits; elapsed {time.time()-start:.1f}s',flush=True)
    raw=pd.DataFrame(intervals)
    raw.to_csv(HERE/'outputs/S5_health_component_intervals.csv',index=False)
    by=raw.set_index(['anchor','cell','parameter'])
    modes=[]
    for r in fits.itertuples():
        ref=fits[(fits.anchor==0)&(fits.cell==r.cell)].iloc[0]
        out={'anchor':r.anchor,'cell':r.cell,'n_eff':r.n_eff,'rms_mV':r.rms_mV,
             'identifiability':'unidentified by stage3; model-conditional diagnostics only'}
        for mode,param in [('LLI','QLi'),('LAM_NE','Qn'),('LAM_PE','Qp')]:
            out[mode+'_point']=float(ref[param]-getattr(r,param))
            ri=by.loc[(0,r.cell,param)];ci=by.loc[(r.anchor,r.cell,param)]
            out[mode+'_lower95']=0. if r.anchor==0 else float(ri['lower']-ci['upper'])
            out[mode+'_upper95']=0. if r.anchor==0 else float(ri['upper']-ci['lower'])
            out[mode+'_prior_boundary']=bool(ri.boundary or ci.boundary)
        modes.append(out)
    modes=pd.DataFrame(modes)
    modes.to_csv(HERE/'outputs/S5_modes_per_cell.csv',index=False)
    mean=modes.groupby('anchor')[['LLI_point','LAM_NE_point','LAM_PE_point']].mean().reset_index()
    mean['observed_anchor_loss_Ah']=[anc[0].Q_Ah-anc[int(j)].Q_Ah for j in mean.anchor]
    mean['LLI_over_observed_anchor_loss']=np.where(mean.observed_anchor_loss_Ah>0,mean.LLI_point/mean.observed_anchor_loss_Ah,np.nan)
    mean['model_total_capacity_share']='unavailable: reference CCCV chain lacks a valid passive taper'
    mean['identifiability']='unidentified; ratio is not a physical loss decomposition'
    mean.to_csv(HERE/'outputs/S5_mode_share_comparison.csv',index=False)
    calibration=json.loads((STUDY/'stage_2/outputs/S2_ck0_check.json').read_text())['main_anchor0']
    etas=calibration['ck0_fit']['eta_dis']
    limits=[]
    for k in range(8):
        if k==0:
            cells=np.asarray(calibration['ref_fit'],float);cells[:,3]=calibration['ck0_fit']['theta_n_start']
            end=0.;q,lim=c20_root(cells[None,:,:],np.array([0.]),etas,ocp)
            capacity=float(q[0]);limiting=int(lim[0]);source='CK0 heldout calibration; not online';j=0
        else:
            j=k-1;cells=fits[fits.anchor==j][['Qn','Qp','QLi','theta_n0','R','h']].to_numpy()
            vals=quantities(cells[None,:,:],ocp,etas)
            end=float(vals['Q_fc'][0]);capacity=float(vals['Q_C20'][0]);limiting=int(vals['limiting'][0])
            source='last visible anchor; unidentified diagnostic'
        if np.isfinite(end):individual,domain=individual_limits(cells,end,etas,ocp)
        else:individual=domain=np.full(4,np.nan)
        finite=np.flatnonzero(np.isfinite(individual));order=finite[np.argsort(individual[finite])] if len(finite) else []
        dorder=np.argsort(domain) if np.isfinite(domain).all() else []
        limits.append({'k':k,'date':str(H.CK[k].date()),'state_anchor':j,'Q_C20_model_Ah':capacity,
            'minimum_voltage_cell_at_pack_root':limiting if limiting else None,
            'first_2p8V_cell':int(order[0])+1 if len(order) else None,
            'second_2p8V_gap_Ah':float(individual[order[1]]-individual[order[0]]) if len(order)>=2 else np.nan,
            'first_stoichiometry_end_cell':int(dorder[0])+1 if len(dorder) else None,
            'second_stoichiometry_end_gap_Ah':float(domain[dorder[1]]-domain[dorder[0]]) if len(dorder) else np.nan,
            'root_available':np.isfinite(capacity),'source':source,
            'identifiability':'unidentified; single-cell thresholds do not replace the pack11.2V cutoff',
            **{f'cell{c+1}_2p8V_root_Ah':float(individual[c]) for c in range(4)}})
    pd.DataFrame(limits).to_csv(HERE/'outputs/S5_limiting_cells.csv',index=False)
    charges=[]
    for seg,g in iter_segments(op):
        _,current,ah=segment_arrays(g)
        pack=g.pack_voltage_V.to_numpy(float)
        for e in _cv_ends(current,pack):
            start_index=e
            while start_index>0 and current[start_index-1]>.5:start_index-=1
            charges.append({'segment':seg,'t_start':g.timestamp.iloc[start_index],'t_end':g.timestamp.iloc[e],
                'charge_Ah':float(ah[e]-ah[max(start_index-1,0)]),'setpoint_C':float(g.chamber_temperature_C.iloc[start_index])})
    charges=pd.DataFrame(charges);coverage=[]
    for j in range(8):
        s=charges[charges.t_start>anc[j].t_end]
        if j+1 in anc:s=s[s.t_end<anc[j+1].t_start]
        s=s.sort_values('t_end')
        if len(s):
            r=s.iloc[0]
            coverage.append({'anchor':j,'event_available':True,'days_after_anchor':(r.t_start-anc[j].t_end).total_seconds()/86400,
                'charge_depth_Ah':r.charge_Ah,'crosses_step_region':bool(r.charge_Ah>=45),
                'decision':'no recovery fit; below graphite/lower-plateau coverage' if r.charge_Ah<45 else 'coverage allows further audit'})
        else:coverage.append({'anchor':j,'event_available':False,'days_after_anchor':np.nan,'charge_depth_Ah':np.nan,
                             'crosses_step_region':False,'decision':'no complete periodic charge available'})
    coverage=pd.DataFrame(coverage)
    coverage.to_csv(HERE/'outputs/S5_recovery_coverage.csv',index=False)
    assert not coverage.crosses_step_region.any(), 'Coverage permits fitting: required independent recovery fit remains'
    colors=['#1f77b4','#d95f02','#7570b3','#222222']
    fig,axes=plt.subplots(1,3,figsize=(13,4.7))
    for ax,mode in zip(axes,['LLI','LAM_NE','LAM_PE']):
        for c in range(1,5):
            g=modes[modes.cell==c].sort_values('anchor')
            x=g.anchor.to_numpy()+(-.09+.06*(c-1));y=g[mode+'_point'].to_numpy()
            lower=g[mode+'_lower95'].to_numpy();upper=g[mode+'_upper95'].to_numpy()
            ax.vlines(x,lower,upper,color=colors[c-1],alpha=.6,linewidth=.9)
            ax.plot(x,y,'o-',color=colors[c-1],label=f'Cell {c}',markersize=3,linewidth=.9)
        ax.axhline(0,color='.7',linewidth=.7)
        ax.set_title(mode.replace('_',' '));ax.set_xlabel('Post-checkup anchor index')
        ax.set_ylabel('Change from anchor 0 (Ah)');ax.grid(axis='y',alpha=.2)
        ax.set_xticks(range(8))
    axes[0].legend(loc='lower left',fontsize=8,ncol=2)
    fig.suptitle('Electrode degradation diagnostics — unidentified under the real-anchor audit',fontsize=12)
    fig.text(.5,.015,'Nominal 95% profile intervals with autocorrelation adjustment; literature OCPs, one pack.\nSource: operating anchors 0–7; no hidden capacity labels.',ha='center',fontsize=8)
    fig.tight_layout(rect=(0,.065,1,.92));fig.savefig(HERE/'outputs/S5_degradation_modes.png',dpi=180);plt.close(fig)
    summary={'mode_rows':len(modes),'additional_material_profile_rows':len(profile_rows),
        'all_health_component_grids_complete':bool(raw.grid_complete.all()),'elapsed_seconds':time.time()-start,
        'cap_reached':time.time()-start>cap,'recovery_fit_permitted':False,'all_modes_identified':False,
        'reference_zero_by_definition':True,'limiting_checkups_reported':len(limits)}
    dump(HERE/'outputs/S5_completion.json',clean_json(summary))
    bilingual(HERE/'REPORT.md','Stage 5 — degradation and cell-limit diagnostics',
      '''Exposed-exploratory; every value inherits stage3's unidentified status. All32 anchor-cell LLI/LAM_NE/LAM_PE points and nominal95 profile-difference intervals are supplied, including separate Qn/Qp profiles. They are model-conditional, often prior-boundary limited, and not physical inventory measurements. Reference changes are exactly zero by definition. Negative LAM values imply apparent material growth in the fit, which is a warning about OCP/temperature/nuisance mismatch, not evidence of regeneration.

The figure and CSV show uncertainty dominating the fitted mode trajectories. The model's LLI/observed anchor-charge-loss ratio is provided only as an unvalidated numerical comparison with V2's68–79% step-to-top share. The model's total C20 loss fraction is unavailable because the reference passive CCCV chain is not valid. Literature expectations of LLI-dominated LFP ageing (Yagci/Bilfinger) do not establish that these cells' fitted quantities represent that mechanism.

Every CK has a limiting-cell row. CK1..7 use only the last visible anchor. CK0 is the prescribed heldout calibration. Minimum voltage at the pack11.2V root, per-cell2.8V first/second crossings, and stoichiometry-end gaps are distinguished. None substitutes the single weakest cell for official pack capacity. The labels are unstable/uncertified under the profile audit; round3's causal map had15 unavailable roots out of105, also offering no independent validation.

The first periodic CCCV charges span about21Ah, below the graphite/lower-plateau region; no recovery fit is permitted by coverage. The0.02→0.87Ah recovery signal from round4 remains an empirical observation that this electrode model cannot attribute to irreversible ageing or reversible lithium redistribution.

Files: S5_modes_per_cell.csv, S5_health_component_intervals.csv, S5_material_profiles.csv, S5_degradation_modes.png, S5_limiting_cells.csv, S5_mode_share_comparison.csv and S5_recovery_coverage.csv.''',
      '''已曝光探索性研究；每个数值均继承阶段3不可辨识状态。提供全部32个锚点-电芯的 LLI/LAM_NE/LAM_PE 拟合点与名义95剖面差分区间，另补 Qn/Qp 剖面。它们依赖模型，常受参数先验边界限制，不是实际电极库存测量。参考变化按定义精确为零。负 LAM 是拟合中表观材料增长，提示 OCP/温度/干扰失配，不证明电池再生。

图和表显示不确定性远大于模式轨迹。模型 LLI/实测锚点充入量损失的比值，只与 V2 68–79% 台阶到顶端份额做未验证数值比较；参考被动 CCCV 链无效，无法给出模型 C20 总损失的真实模式份额。Yagci/Bilfinger 文献中 LFP 老化以 LLI 为主的预期，不能证明这些拟合量对应本电池组机制。

每个 CK 都有一行限制电芯诊断，CK1..7只用此前最后可见锚点，CK0为规定留出标定。明确区分组端11.2V时最低芯压、逐芯2.8V首个/第二个到达点及化学计量末端间隔，不以最弱单芯替代官方组容量。剖面审计下这些标签不稳定/未认证；第三轮因果映射105例有15个不可求根，也不提供独立验证。

首次周期性 CCCV 仅覆盖约21Ah，低于石墨台阶和下平台范围，覆盖退出规则不允许恢复拟合。第四轮0.02→0.87Ah恢复信号仍是经验观察，本电极模型无法把它归因为不可逆老化或可逆锂再分布。

文件包括模式、健康参数区间、材料剖面、退化图、限制电芯、份额比较及恢复覆盖表。''')
    print(json.dumps(clean_json(summary),indent=2),flush=True)
