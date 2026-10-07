"""Compare five official trajectories, with CK1-7 truth deliberately blank."""
from pathlib import Path
import numpy as np
import pandas as pd
import sys
ROOT=Path(__file__).resolve().parents[3]
TASK=ROOT/'research/phase2_validation'
sys.path.insert(0,str(ROOT))
from framework.data import load_dataset,load_eval_points
sys.path.insert(0,str(TASK/'src'))
from event_core import extract_charge_events,partial_ah

def b2_prefix(ds,date):
    events=extract_charge_events(ds.operation,voltage_cols=('pack_voltage_V',),until=date)
    references={};recent=[]
    for ev in events:
        if ev.ah<15 or not np.isfinite(ev.median_temp):continue
        q=partial_ah(ev,0,13.4,13.95)
        if q is None or q<1:continue
        temp=int(round(ev.median_temp/20));depth='deep' if ev.ah>=50 else 'shallow'
        key=(temp,depth)
        if key not in references:
            references[key]=(q,ev.median_current);continue
        ref,ri=references[key]
        if abs(ev.median_current-ri)>0.2*max(ri,1):continue
        if (date-ev.end).total_seconds()>30*86400:continue
        recent.append((ev.end,q/ref))
    if not recent:return 100*100.41/102,0,True
    pooled={t:r for t,r in recent}
    ratio=float(np.median([pooled[t] for t in sorted(pooled)[-5:]]))
    return 100*(100.41*ratio)/102,len(recent),False

def main():
    points=load_eval_points(ROOT/'data')
    files={'B1_original_ExampleModel':TASK/'preflight/baseline_full/output.csv',
           'A_route_v4':TASK/'runs/A_official_v4/output.csv',
           'B_route_v3':TASK/'runs/B_official_v3/output.csv'}
    predictions={k:pd.read_csv(p).set_index('checkup') for k,p in files.items()}
    diag=pd.read_csv(TASK/'runs/official_diagnostics.csv').set_index(['route','checkup'])
    rows=[]
    for p in points.itertuples():
        date=p.date
        ds=load_dataset(ROOT/'data',until=date)
        val,n,fb=b2_prefix(ds,date)
        for name,soh,rid,updates,fallback,note in [
            ('B0_CK0_constant',100*100.41/102,'B0',0,True,'released CK0 only'),
            ('B1_original_ExampleModel',float(predictions['B1_original_ExampleModel'].loc[p.checkup,'SOH_est']),
             'preflight/baseline_full',None,None,'original example; full-operation fit reference'),
            ('B2_prefix_total_voltage',val,'B2_prefix',n,fb,'reference selected within prefix'),
            ('A_route_v4',float(predictions['A_route_v4'].loc[p.checkup,'SOH_est']),'A_official_v4',
             int(diag.loc[('route_a',p.checkup),'updates']),bool(diag.loc[('route_a',p.checkup),'fallback']),
             'deep/shallow and cell-window matched'),
            ('B_route_v3',float(predictions['B_route_v3'].loc[p.checkup,'SOH_est']),'B_official_v3',
             int(diag.loc[('route_b',p.checkup),'updates']),bool(diag.loc[('route_b',p.checkup),'fallback']),
             'capacity frozen when information gate rejects')]:
            rows.append({'run_id':rid,'evidence':'E1','dataset':'official_four_series',
                'checkup':p.checkup,'date':str(date.date()),'method':name,
                'SOH_est_pp':soh,'capacity_est_Ah':soh*102/100,
                'true_capacity_Ah':100.41 if p.checkup=='CK0' else '',
                'true_SOH_pp':100*100.41/102 if p.checkup=='CK0' else '',
                'updates_or_events':updates,'fallback':fallback,'note':note})
    out=TASK/'outputs/predictions_official.csv'
    pd.DataFrame(rows).to_csv(out,index=False)
    print(out,len(rows))
    print(pd.DataFrame(rows).pivot(index='checkup',columns='method',values='SOH_est_pp').to_string())

if __name__=='__main__':main()
