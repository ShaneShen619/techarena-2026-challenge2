"""Freeze on calendar development, then replay given-drive voltage budgets A/B."""
from __future__ import annotations
import copy,json,time
import numpy as np
import pandas as pd
from common import CFG,OUT,TASK,ROOT,json_dump,digest,qualified_history
from audit_events import load
from ecm import Reference,predict
from joint_estimation import Window,initialized,previous_curve,voltage_metrics
from identifiability import profile

def development():
    if (OUT/'EVALUATION_COMPLETE').exists():raise RuntimeError('Evaluation complete; develop cannot be reopened.')
    events=load();ref=Reference();rows=[];selected={};residuals=[]
    dev=[e for e in events if e['split']=='development']
    for T in [25,45]:
        for tau in CFG['tau_candidates_s']:
            for e in dev:
                if e['T']!=T or not e['chain_ok']:continue
                hist=qualified_history(dev,e)
                if not hist:continue
                try:
                    fit=Window(ref,hist,tau).fit(False)
                    for budgetname,budget in CFG['budgets_Ah'].items():
                        m=initialized(ref,e,fit,budget)
                        pred=predict(ref,e,m);metrics=voltage_metrics(e,pred)
                        rows.append(dict(T=T,tau=tau,id=e['id'],budget=budgetname,**metrics))
                        last=past_curve(dev,e)
                        if last is not None and tau==CFG['default_tau_s']:
                            for base,rest in [('B_previous',False),('B_previous_rest',True)]:
                                bm=voltage_metrics(e,previous_curve(e,last,budget,use_rest=rest))
                                rows.append(dict(T=T,tau=0,id=e['id'],budget=budgetname,baseline=base,**bm))
                    if tau==CFG['default_tau_s']:
                        pts=Window(ref,[e],tau).points[0];ff=Window(ref,[e],tau).fit(False)
                        yp=predict(ref,e,ff)
                        keep=(e['phase']==0)&(e['t']>=-300)
                        if keep.sum()>=5:residuals.append((yp[keep]-e['y'][keep])*1000)
                except ValueError as exc:rows.append(dict(T=T,tau=tau,id=e['id'],budget='failed',failure=str(exc)))
        tab=pd.DataFrame([r for r in rows if r['T']==T and r.get('budget')=='B' and r['tau']>0])
        if len(tab):
            means=tab.groupby('tau').mae_mV.mean();tau=float(means.idxmin())
            selected[str(T)]=dict(tau=tau,development_B_mae_mV=float(means.min()),development_points=len(tab),available_after=CFG['development_until'])
            baselines=pd.DataFrame([r for r in rows if r['T']==T and r.get('budget')=='B' and r['tau']==0])
            if len(baselines):
                baseline_mae=float(baselines.groupby('baseline').mae_mV.mean().min())
                selected[str(T)]['development_baseline_B_mae_mV']=baseline_mae
                selected[str(T)]['development_dynamic_gate']=bool(means.min()<=.95*baseline_mae)
            else:selected[str(T)]['development_dynamic_gate']=False
        else:selected[str(T)]=dict(tau=CFG['default_tau_s'],reason='no_development_forward_windows',available_after=CFG['development_until'])
    # Empirical stationary-rest residual block perturbation, explicit model residual.
    rng=np.random.default_rng(CFG['seed_noise']);changes=[]
    for block in residuals:
        centered=block-block.mean(axis=0)
        for _ in range(50):
            noise=np.roll(centered,int(rng.integers(len(centered))),axis=0)+rng.uniform(-.5,.5,block.shape)
            before=float(np.sqrt(np.mean(block**2)));after=float(np.sqrt(np.mean((block+noise)**2)))
            changes.append(abs(after-before))
    q95=float(np.quantile(changes,.95)) if changes else 0.
    selected['noise']=dict(delta_mV=max(CFG['profile_delta_floor_mV'],q95),rest_block_RMS_change_q95_mV=q95,
        residual_blocks=len(residuals),seed=CFG['seed_noise'],interpretation='Sensitivity threshold; block residual includes model discrepancy, not calibrated probability interval')
    pd.DataFrame(rows).to_csv(OUT/'development_choices.csv',index=False)
    json_dump(OUT/'selected_configuration.json',selected)
    json_dump(OUT/'freeze_manifest.json',dict(config_sha256=digest(TASK/'configs/protocol.json'),source_sha256=digest(OUT/'data_manifest.json'),
        selected_sha256=digest(OUT/'selected_configuration.json'),code_sha256={p.name:digest(p) for p in sorted((TASK/'src').glob('*.py'))},
        development_until=CFG['development_until'],future_evaluation_voltage_used=False))
    print('FROZEN',selected,flush=True)
    return selected

def past_curve(events,e):
    same=[h for h in events if h['panel']==e['panel'] and h['T']==e['T'] and h['available_after']<e['start']]
    return same[-1] if same else None

def replay():
    if (OUT/'EVALUATION_COMPLETE').exists():raise RuntimeError('Immutable evaluation. New ECM_RUN_ID required.')
    selected=json.loads((OUT/'selected_configuration.json').read_text());events=load();ref=Reference()
    rows=[];traces=[];parameters=[];gates=[];failures=[]
    methods=['B_previous','B_previous_rest','M_fixed','M_ungated','M_gated','M_no_charge','M_no_rest','M_mean_cells']
    clock=time.perf_counter()
    for e in [x for x in events if x['split']=='evaluation']:
        hist=qualified_history(events,e);last=past_curve(events,e);tau=selected[str(e['T'])]['tau'];fits={};pr=None
        if hist:
            for method,options in [('M_fixed',{}),('M_ungated',{}),('M_no_charge',dict(charge_history=False)),('M_no_rest',dict(rests=False)),('M_mean_cells',dict(mean_cells=True))]:
                try:
                    win=Window(ref,hist,tau,**options)
                    fits[method]=win.fit(free=method=='M_ungated')
                    if method=='M_ungated':
                        pr=profile(win,selected['noise']['delta_mV'],fine=True)
                        # Local profile alone cannot certify structural robustness.
                        # No certified structural union and development dynamics failed:
                        # this is an explicit state-only/fixed-capacity deployment fallback.
                        fits['M_gated']=copy.deepcopy(fits['M_fixed']);fits['M_gated']['profile_accepted']=False
                        gates.append(dict(target_id=e['id'],T=e['T'],panel=e['panel'],history_ids='|'.join(h['id'] for h in hist),
                            history_available_after=max(h['available_after'] for h in hist),best_capacity_Ah=pr.get('best_capacity_Ah'),
                            profile_width_Ah=pr['width_Ah'],capacity_local_update=bool(pr.get('accepted',False)),
                            unsupported_candidates=pr.get('unsupported_candidate_count'),structural_update_certified=False))
                except ValueError as exc:failures.append(dict(id=e['id'],method=method,reason=str(exc)))
        for budgetname,budget in CFG['budgets_Ah'].items():
            for method in methods:
                direct=False;reason='';fitted=None
                try:
                    if method.startswith('B_'):prediction=previous_curve(e,last,budget,use_rest=method=='B_previous_rest');direct=True
                    else:
                        if not e['chain_ok']:raise ValueError('target_has_no_certified_continuous_anchor')
                        if method not in fits:raise ValueError('no_history_fit')
                        fitted=initialized(ref,e,fits[method],budget,use_rest=method!='M_no_rest')
                        prediction=predict(ref,e,fitted);direct=True
                except ValueError as exc:
                    reason=str(exc)
                    try:prediction=previous_curve(e,last,budget)
                    except ValueError:prediction=np.full_like(e['y'],np.nan)
                try:met=voltage_metrics(e,prediction)
                except ValueError:met=dict(mae_mV=np.nan,rms_mV=np.nan,p95_mV=np.nan,max_mV=np.nan,sample_coverage=0.,n_score=0,per_cell_mae_mV=[np.nan]*4)
                rows.append(dict(id=e['id'],start=e['start'],T=e['T'],panel=e['panel'],budget=budgetname,method=method,direct=direct,
                    fallback_reason=reason,history_events=len(hist),alpha=float(fitted['alpha']) if fitted else None,**met))
                if fitted:
                    parameters.append(dict(id=e['id'],budget=budgetname,method=method,alpha=fitted['alpha'],tau=fitted['tau'],
                        history_available_after=fitted['available_after'],current_loaded_voltage_budget_Ah=budget,params=fitted['params'].tolist()))
                if method in ['B_previous','M_fixed','M_ungated','M_gated']:
                    use=(e['phase']==1)&(e['q']>=2)
                    for k in np.flatnonzero(use)[::4]:traces.append(dict(id=e['id'],T=e['T'],panel=e['panel'],budget=budgetname,method=method,q_Ah=e['q'][k],
                        actual_pack_V=e['pack'][k],predicted_sum_cells_V=float(prediction[k].sum()),actual_mean_cell_V=float(e['y'][k].mean()),predicted_mean_cell_V=float(prediction[k].mean())))
        print('replay',e['id'],'history',len(hist),'profile',pr.get('width_Ah') if pr else None,'elapsed',round(time.perf_counter()-clock,1),flush=True)
    df=pd.DataFrame(rows);df.to_csv(OUT/'forward_event_metrics.csv',index=False)
    pd.DataFrame(traces).to_csv(OUT/'forward_traces.csv',index=False)
    pd.DataFrame(gates).to_csv(OUT/'causal_update_gates.csv',index=False)
    pd.DataFrame(failures).to_csv(OUT/'fit_failures.csv',index=False)
    json_dump(OUT/'historical_parameters.json',parameters)
    summary=df.groupby(['budget','method'],as_index=False).agg(events=('id','count'),finite_events=('mae_mV','count'),mae_mV=('mae_mV','mean'),rms_mV=('rms_mV','mean'),direct_coverage=('direct','mean'),worst_event_mV=('mae_mV','max'))
    strata=df.groupby(['budget','method','T','panel'],as_index=False).agg(events=('id','count'),mae_mV=('mae_mV','mean'),direct_coverage=('direct','mean'))
    summary.to_csv(OUT/'forward_summary.csv',index=False);strata.to_csv(OUT/'forward_strata.csv',index=False)
    decisions=[]
    for budget in ['A','B']:
        sub=summary[summary.budget.eq(budget)];baseline=sub[sub.method.str.startswith('B_')].sort_values('mae_mV').iloc[0]
        for method in [m for m in methods if m.startswith('M_')]:
            r=sub[sub.method.eq(method)].iloc[0];relative=1-r.mae_mV/baseline.mae_mV
            old=strata[(strata.budget==budget)&(strata.method==baseline.method)].set_index(['T','panel'])
            new=strata[(strata.budget==budget)&(strata.method==method)].set_index(['T','panel'])
            degradation=(new.mae_mV/old.mae_mV-1).max()
            pass_gate=bool(relative>=.05 and r.direct_coverage>=.9 and r.finite_events==r.events and degradation<=.1)
            decisions.append(dict(budget=budget,method=method,baseline=baseline.method,baseline_mae_mV=float(baseline.mae_mV),mae_mV=float(r.mae_mV),relative_improvement=float(relative),
                direct_coverage=float(r.direct_coverage),worst_stratum_degradation=float(degradation),gate='PASS' if pass_gate else 'FAIL'))
    json_dump(OUT/'dynamic_decisions.json',decisions)
    json_dump(OUT/'evaluation_completion.json',dict(runtime_s=time.perf_counter()-clock,events=len({r['id'] for r in rows}),science_boundary='given measured drive, no scored-suffix voltage updates; official follow-up capacity error unavailable'))
    (OUT/'EVALUATION_COMPLETE').write_text('Frozen-rule evaluation completed. Do not reopen tuning.\n')
    print(summary.to_string(index=False),flush=True)

if __name__=='__main__':
    import sys
    if sys.argv[1]=='develop':development()
    elif sys.argv[1]=='evaluate':replay()
    else:raise SystemExit('develop | evaluate')
