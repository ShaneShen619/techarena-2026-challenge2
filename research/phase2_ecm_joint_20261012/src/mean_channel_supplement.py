"""Complete mean-only input ablation; separate post-scoring mean-voltage task."""
from __future__ import annotations
import copy,json
import numpy as np
import pandas as pd
from common import OUT,json_dump,qualified_history
from audit_events import load
from ecm import Reference,predict
from joint_estimation import Window,initialized,previous_curve

def averaged(e):
    # Four identical computational columns reuse the solver, not four new entities.
    out=dict(e);out['y']=np.repeat(e['y'].mean(axis=1)[:,None],4,axis=1)
    return out

def run():
    if (OUT/'MEAN_CHANNEL_SUPPLEMENT_COMPLETE').exists():raise RuntimeError('Mean-channel scoring already complete')
    json_dump(OUT/'mean_channel_supplement_protocol.json',dict(task='Mean of four-cell voltage, not mean of individual absolute errors',
        input='Historical reference and target initialization all mean-only; no per-cell signal retained in mean branch',
        budgets_Ah=[0,1],parameters='Frozen existing tau, capacity fixed, no tuning',post_primary_scoring=True,selection_use=False))
    events=load();means=[averaged(e) for e in events];refs=Reference();meanref=copy.deepcopy(refs)
    meanref.raw_v=np.repeat(meanref.raw_v.mean(axis=1)[:,None],4,axis=1);meanref.v=np.repeat(meanref.v.mean(axis=1)[:,None],4,axis=1)
    selected=json.loads((OUT/'selected_configuration.json').read_text());params=json.loads((OUT/'historical_parameters.json').read_text())
    stored={(r['id'],r['budget']):r for r in params if r['method']=='M_fixed'};rows=[]
    for e in [e for e in means if e['split']=='evaluation']:
        original=next(x for x in events if x['id']==e['id']);history=qualified_history(means,e)
        last=[h for h in means if h['T']==e['T'] and h['panel']==e['panel'] and h['available_after']<e['start']][-1]
        tau=selected[str(e['T'])]['tau'];fit=None
        if e['chain_ok'] and history:
            try:fit=Window(meanref,history,tau).fit(False)
            except ValueError:pass
        for budgetname,budget in [('A',0),('B',1)]:
            baseline=previous_curve(e,last,budget);meanprediction=baseline;direct=False
            if fit:
                try:meanprediction=predict(meanref,e,initialized(meanref,e,fit,budget));direct=True
                except ValueError:pass
            key=(e['id'],budgetname)
            if key in stored:
                r=stored[key];fullfit=dict(alpha=r['alpha'],params=np.asarray(r['params']),tau=r['tau'],charge_history=True,temperature=True)
                fullprediction=predict(refs,original,fullfit)
            else:
                original_last=next(x for x in events if x['id']==last['id']);fullprediction=previous_curve(original,original_last,budget)
            score=(e['phase']==1)&(e['q']>=2)
            for method,pred in [('previous_mean',baseline),('full_cell_model_mean_output',fullprediction),('mean_only_model',meanprediction)]:
                error=np.abs(pred[score].mean(axis=1)-e['y'][score].mean(axis=1))*1000
                coverage=direct if method=='mean_only_model' else (key in stored if method=='full_cell_model_mean_output' else True)
                rows.append(dict(id=e['id'],budget=budgetname,T=e['T'],panel=e['panel'],method=method,mean_voltage_mae_mV=float(error.mean()),direct=coverage))
    df=pd.DataFrame(rows);df.to_csv(OUT/'mean_channel_event_scores.csv',index=False)
    df.groupby(['budget','method'],as_index=False).agg(events=('id','count'),mean_voltage_mae_mV=('mean_voltage_mae_mV','mean'),direct_coverage=('direct','mean')).to_csv(OUT/'mean_channel_summary.csv',index=False)
    (OUT/'MEAN_CHANNEL_SUPPLEMENT_COMPLETE').write_text('Post-primary mean-voltage input ablation complete, not used for main selection.\n')
    print('Mean-only ablation completed',flush=True)

if __name__=='__main__':run()
