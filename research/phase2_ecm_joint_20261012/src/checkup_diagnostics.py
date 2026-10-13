"""Causal CK profiles, structural counterexamples, optional A quality diagnostics."""
from __future__ import annotations
import copy,json,time
import numpy as np
import pandas as pd
from common import CFG,OUT,ROOT,json_dump
from audit_events import load
from ecm import Reference,predict
from joint_estimation import Window,initialized
from identifiability import profile,diagnostics,numerical_refit_witness
from online import track

def run():
    events=load();ref=Reference();selected=json.loads((OUT/'selected_configuration.json').read_text())
    evals=pd.read_csv(ROOT/'data/checkups/evaluation_points.csv',parse_dates=['date'])
    tables=[];rows=[];params=[];sens=[];witness=[];reference=[];Arows=[];online=[]
    charge=pd.read_csv(OUT/'A_charge_windows.csv',parse_dates=['end'])
    start=time.perf_counter()
    for ck in evals.itertuples():
        if ck.checkup=='CK0':
            rows.append(dict(checkup='CK0',T=None,model='released_reference',best_capacity_Ah=ref.capacity(),accepted=True,truth_capacity_Ah=100.41,error_Ah=0.,status='released_anchor_self_consistency'));continue
        for T in [25,45]:
            eligible=[e for e in events if e['T']==T and e['chain_ok'] and pd.Timestamp(e['available_after'])<=ck.date and ck.date-pd.Timestamp(e['available_after'])<=pd.Timedelta(days=60)]
            history=eligible[-4:]
            if len(history)<2:
                rows.append(dict(checkup=ck.checkup,T=T,model='base',status='insufficient_completed_history',accepted=False));continue
            early=ck.date<=pd.Timestamp(CFG['development_until']);tau=CFG['default_tau_s'] if early else selected[str(T)]['tau']
            delta=1. if early else selected['noise']['delta_mV']
            scenarios=[('base',{}),('tight_bias',dict(bias=.01)),('wide_bias',dict(bias=.10)),('fast_RC',dict(tau=max(100,tau/2))),('slow_RC',dict(tau=tau*2)),
                ('tight_start',dict(dmax=3.)),('wide_start',dict(dmax=15.)),('no_rest',dict(rests=False)),('no_charge_history',dict(charge_history=False)),('history8',dict(history8=True))]
            base=None;profile_union=[];all_supported=True
            for name,options in scenarios:
                op=options.copy();n8=op.pop('history8',False);tt=op.pop('tau',tau);h=eligible[-8:] if n8 else history
                window=Window(ref,h,tt,**op);pr=profile(window,delta,fine=True)
                if pr.get('best') is None:
                    rows.append(dict(checkup=ck.checkup,T=T,model=name,accepted=False,status='no_supported_capacity_candidate'));continue
                fit=pr['best'];profile_union.extend([pr['lower_Ah'],pr['upper_Ah']]);all_supported &= not pr['touches_scan_boundary'] and pr['unsupported_candidate_count']==0
                rows.append(dict(checkup=ck.checkup,T=T,model=name,best_capacity_Ah=pr['best_capacity_Ah'],lower_Ah=pr['lower_Ah'],upper_Ah=pr['upper_Ah'],width_Ah=pr['width_Ah'],
                    minimum_RMS_mV=pr['minimum_rms_mV'],delta_mV=delta,local_gate=pr['accepted'],accepted=False,status='conditional_research_only',
                    history_events=len(h),history_end=max(e['available_after'] for e in h),hyperparameter_source='predeclared_default' if early else 'development_only',tau=tt,
                    unsupported_candidates=pr['unsupported_candidate_count'],truth_capacity_Ah=None,error_Ah=None))
                for C,rms in zip(pr['capacity'],pr['rms']):tables.append(dict(checkup=ck.checkup,T=T,model=name,capacity_Ah=C,rms_mV=rms,delta_mV=delta))
                params.append(dict(checkup=ck.checkup,T=T,model=name,alpha=fit['alpha'],params=fit['params'].tolist(),history_ids=[e['id'] for e in h],history_end=fit['available_after']))
                if name=='base':
                    base=(window,pr)
                    sens.append(dict(checkup=ck.checkup,T=T,**diagnostics(window,fit)))
                    for C in [80.,100.]:
                        try:witness.append(dict(checkup=ck.checkup,T=T,**numerical_refit_witness(window,C)))
                        except ValueError as exc:witness.append(dict(checkup=ck.checkup,T=T,capacity_Ah=C,available=False,reason=str(exc)))
                    for tol in CFG['fixed_delta_sensitivity_mV']:
                        allowed=pr['capacity'][pr['rms']<=pr['minimum_rms_mV']+tol]
                        sens.append(dict(checkup=ck.checkup,T=T,delta_mV=tol,width_Ah=float(allowed.max()-allowed.min())))
            if base:
                window,pr=base
                unionwidth=float(max(profile_union)-min(profile_union))
                sens.append(dict(checkup=ck.checkup,T=T,structural_union_lower_Ah=min(profile_union),structural_union_upper_Ah=max(profile_union),
                    structural_union_width_Ah=unionwidth,all_registered_candidates_supported=all_supported,
                    accepted=False,reason='dynamics_gate_not_passed_and_no_independent_reference_calibration'))
                # Conditional reference initial-state/residual perturbations are NOT fitted run states.
                for label,shift,r,chain in [('baseline',None,None,0.),('all_cells_0p5Ah_underfull',np.full(4,.5),None,0.),
                    ('one_cell_1Ah_underfull',np.array([0.,1.,0.,0.]),None,0.),('aging_R_all_0p1mOhm',None,np.full(4,.0001),0.),
                    ('CK0_chain_minus4mV',None,None,-.004),('CK0_chain_plus4mV',None,None,.004)]:
                    try:
                        value=ref.capacity(pr['best']['alpha'],shift,r,chain);status='conditional_projection'
                    except ValueError as exc:value=None;status=str(exc)
                    reference.append(dict(checkup=ck.checkup,T=T,assumption=label,capacity_Ah=value,status=status,not_inferred_from_running_offset=True))
                # A is a past, correlated health indication; no capacity-rate calibration.
                c=charge[(charge['T']==T)&charge.qualified&(charge.end<=ck.date)].tail(8)
                for cell in range(1,5):
                    k=f'A_cell{cell}_Ah';good=c.dropna(subset=[k])
                    slope=None
                    if len(good)>=3:
                        days=(good.end-good.end.iloc[0]).dt.total_seconds().to_numpy()/86400
                        slope=float(np.polyfit(days,good[k].to_numpy(float),1)[0])
                    Arows.append(dict(checkup=ck.checkup,T=T,cell=cell,events=len(good),A_slope_Ah_per_day=slope,
                        capacity_profile_width_Ah=pr['width_Ah'],role='correlated_quality_diagnostic_only',capacity_rate_calibration='UNVERIFIED'))
                print('CK profiles',ck.checkup,T,'width',round(pr['width_Ah'],3),'structural union',round(unionwidth,3),'seconds',round(time.perf_counter()-start,1),flush=True)
    # Online trajectories for fixed predefined representative evaluation events, no capacity update.
    for T in [25,45]:
        for panel in ['short','wide']:
            ee=[e for e in events if e['split']=='evaluation' and e['T']==T and e['panel']==panel and e['chain_ok']]
            if not ee:continue
            e=ee[0];history=[h for h in events if h['T']==T and h['chain_ok'] and h['available_after']<e['start']][-4:]
            if not history:continue
            fit=Window(ref,history,selected[str(T)]['tau']).fit(False)
            trajectory,meta=track(ref,e,fit)
            for r in trajectory:
                if not r['valid']:online.append(dict(id=e['id'],T=T,panel=panel,index=r['index'],valid=False,reason=r['reason']));continue
                for cell in range(4):online.append(dict(id=e['id'],T=T,panel=panel,index=r['index'],t_s=e['t'][r['index']],cell=cell+1,valid=True,
                    reference_position_Ah=r['reference_position_Ah'][cell],conditional_position_sd_Ah=np.sqrt(r['position_variance_Ah2'][cell]),
                    polarization_V=r['polarization_V'][cell],innovation_mV=r['innovation_mV'][cell],capacity_frozen=True))
    pd.DataFrame(rows).to_csv(OUT/'checkup_profiles.csv',index=False)
    pd.DataFrame(tables).to_csv(OUT/'profile_curves.csv',index=False)
    pd.DataFrame(reference).to_csv(OUT/'reference_assumptions.csv',index=False)
    pd.DataFrame(Arows).to_csv(OUT/'A_quality_diagnostics.csv',index=False)
    pd.DataFrame(online).to_csv(OUT/'online_fixed_capacity.csv',index=False)
    json_dump(OUT/'checkup_parameters.json',params);json_dump(OUT/'identifiability_diagnostics.json',sens);json_dump(OUT/'independent_optimizer_witnesses.json',witness)
    json_dump(OUT/'diagnostics_completion.json',dict(runtime_s=time.perf_counter()-start,hidden_capacity_labels_used=False,
        reference_initial_imbalance_certified=False,A_capacity_correction='not admitted without rate calibration and main-model dynamics pass'))
    print('CK/structure diagnostics seconds',round(time.perf_counter()-start,1),flush=True)

if __name__=='__main__':run()
