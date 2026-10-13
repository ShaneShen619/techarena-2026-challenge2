"""Develop first, freeze, then causal replay. Refuses scored-version overwrite."""
import argparse,json,time,platform
import numpy as np
import pandas as pd
import model
from common import *

def verify_freeze():
    frozen=json.loads((TASK/'freeze_manifest.json').read_text())
    for name,digest in frozen['files'].items():
        if sha(ROOT/name)!=digest:raise RuntimeError('Frozen dependency changed: '+name)
    if protected()!=json.loads((TASK/'protected_before.json').read_text()):
        raise RuntimeError('Original protected source/result changed')

def cache(es,phase):
    template=StrictTemplate();selected=json.loads((TASK/'selected_legacy.json').read_text())
    pulses=pd.read_csv(TASK/'pulse_registry.csv')
    rows=[]
    for e in es:
        if e['split']!=phase:continue
        tau=selected[key(e)]['tau']
        for loss in ['L2','LAD']:
            for mode in ['free','independent']:
                start=time.perf_counter();pr=model.profile(template,e,tau,loss,mode,pulses)
                d,_=model.diagnosis([pr],loss,template.q0)
                rows.append(dict(id=e['id'],split=phase,panel=e['panel'],T=e['T'],loss=loss,mode=mode,
                    direct_constraints=int(pr['direct_constraints']),runtime_s=time.perf_counter()-start,**d))
        print('profile',phase,e['id'],flush=True)
    pd.DataFrame(rows).to_csv(TASK/f'offline_{phase}_diagnostics.csv',index=False)

def old_profile(e,tau):
    p=OLD_RUN/'profiles'/f"{e['id'].replace(':','-')}_{tau}_free.npz"
    z=np.load(p);return {k:z[k] for k in z.files}

def replay(es,phase):
    template=StrictTemplate();oldtemplate=legacy.Template()
    selected=json.loads((TASK/'selected_legacy.json').read_text())
    rows=[];traces=[];profiles=[]
    for e in es:
        if e['split']!=phase:continue
        histories=history(es,e,CFG['history_count']);tau=selected[key(e)]['tau']
        if not histories:continue
        hpars=[legacy.choose(old_profile(h,tau),'shift')[1] for h in histories]
        pbase=np.median(hpars,axis=0)
        for budgetname,budget in [('A',0),('B',1)]:
            oldbase=selected[key(e)]['baseline'][budgetname]
            def baseline():
                if oldbase=='B1_previous':
                    return e['y'],legacy.last_curve(e,histories[-1],budget),e['q']
                p,pred,_=legacy.forecast(oldtemplate,e,1,pbase,tau,budget)
                return p['y'],pred,p['q']
            yy,bpred,bq=baseline();score=legacy.errors(yy,bpred,bq)
            rows.append(dict(id=e['id'],panel=e['panel'],T=e['T'],split=phase,budget=budgetname,
                method='frozen_baseline',fallback=False,reason='',history_events=len(histories),
                latest_parameter_data_end=histories[-1]['available_after'],target_voltage_prefix_Ah=budget,**score))
            p,pred,_=legacy.forecast(oldtemplate,e,1,pbase,tau,budget)
            rows.append(dict(id=e['id'],panel=e['panel'],T=e['T'],split=phase,budget=budgetname,
                method='legacy_fixed',fallback=False,reason='',**legacy.errors(p['y'],pred,p['q'])))
            for loss in ['L2','LAD']:
                for mode in ['free','independent']:
                    prs=[]
                    for h in histories:
                        z=np.load(profile_path(h,loss,mode));prs.append({k:z[k] for k in z.files})
                    diag,curve=model.diagnosis(prs,loss,template.q0)
                    if budgetname=='A':
                        for s,v in zip(prs[0]['sgrid'],curve):profiles.append(dict(id=e['id'],panel=e['panel'],T=e['T'],loss=loss,mode=mode,s=float(s),loss_mV=float(v),history_events=len(histories)))
                    for kind in ['fixed','single_common','multi_common','multi_shrunk4','multi_free4_diagnostic','gated_common']:
                        subset=prs[-1:] if kind=='single_common' else prs
                        s,params,obj=model.select(subset,kind='free4' if kind in ['multi_shrunk4','multi_free4_diagnostic'] else 'common',
                            fixed=kind=='fixed',shrink=kind=='multi_shrunk4',loss=loss)
                        fallback=False;reason=''
                        if kind=='gated_common' and not diag['gate']:
                            fallback=True;reason='scale_profile_not_identifiable'
                        try:
                            if fallback:raise ValueError(reason)
                            p,pred,par=model.forecast(template,e,s,params,tau,budget)
                            score=legacy.errors(p['y'],pred,p['q']);qy=p['q'];actual=p['y']
                            if not np.isfinite(pred).all():raise ValueError('nonfinite_prediction')
                        except (ValueError,np.linalg.LinAlgError) as ex:
                            fallback=True;reason=str(ex);score=legacy.errors(yy,bpred,bq)
                            pred=bpred;qy=bq;actual=yy
                        method=f'{loss}_{mode}_{kind}'
                        rows.append(dict(id=e['id'],panel=e['panel'],T=e['T'],split=phase,budget=budgetname,
                            method=method,loss=loss,mode=mode,kind=kind,fallback=fallback,reason=reason,
                            history_events=len(histories),latest_parameter_data_end=histories[-1]['available_after'],
                            target_voltage_prefix_Ah=budget,s1=float(s[0]),s2=float(s[1]),s3=float(s[2]),s4=float(s[3]),
                            s_spread=float(np.ptp(s)),profile_width_Ah=diag['width_Ah'],profile_gate=diag['gate'],
                            historical_constraints=int(sum(int(pr['direct_constraints']) for pr in prs)),**score))
                        if kind in ['multi_common','gated_common'] and mode=='independent':
                            for k in np.linspace(0,len(qy)-1,min(25,len(qy))).round().astype(int):
                                traces.append(dict(id=e['id'],budget=budgetname,method=method,q_Ah=float(qy[k]),
                                    actual_mean_V=float(actual[k].mean()),prediction_mean_V=float(pred[k].mean()),
                                    suffix_voltage_used=False,fallback=fallback))
        print('causal replay',phase,e['id'],flush=True)
    pd.DataFrame(rows).to_csv(TASK/f'forward_{phase}_metrics.csv',index=False)
    pd.DataFrame(traces).to_csv(TASK/f'forward_{phase}_traces.csv',index=False)
    pd.DataFrame(profiles).to_csv(TASK/f'historical_{phase}_profiles.csv',index=False)

def freeze():
    if (TASK/'freeze_manifest.json').exists():raise RuntimeError('already frozen')
    # Actual selection rules and scoring scripts included before any evaluation.
    paths=list(TASK.glob('*.py'))+[TASK/'config.json',TASK/'protocol.md',TASK/'selected_legacy.json',TASK/'events.pkl']
    paths+=list((OLD/'src').glob('*.py'))+[OLD/'configs/frozen_protocol.json',ROOT/'research/phase1_pack_trend_20261011/src/pack.py']
    paths+=list((OLD_RUN/'profiles').glob('*_free.npz'))+[OLD_RUN/'selected_configuration.json',OLD_RUN/'official_evaluation_metrics.csv']
    paths += [TASK/'literature_evidence.json',TASK/'raw_manifest.json',TASK/'pulse_registry.csv',TASK/'raw_voltage_verification.csv']
    files={str(p.relative_to(ROOT)):sha(p) for p in paths}
    savejson('freeze_manifest.json',dict(files=files,python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,
        execution_date='2026-10-13',exposure='old history already exposed; no claim of first blind evaluation',
        thresholds=CFG,scope='all new implementation/scoring code frozen; report rendering may be added without changing metrics'))
    print('FROZEN',len(files),'dependencies',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['development','freeze','evaluation']);a=parser.parse_args()
    if a.phase=='freeze':freeze()
    else:
        if a.phase=='evaluation':
            verify_freeze()
            if (TASK/'EVALUATION_STARTED').exists():raise RuntimeError('evaluation already started; no overwrite')
            (TASK/'EVALUATION_STARTED').write_text('2026-10-13\n')
        es=events();cache(es,a.phase);replay(es,a.phase)
        if a.phase=='evaluation':verify_freeze();(TASK/'OFFICIAL_COMPLETE').write_text('2026-10-13\n')
