"""Prefix counter audit and sensor temperature sensitivity on source folds."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
import pandas as pd
TASK=Path(__file__).resolve().parents[1];ROOT=TASK.parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(TASK/'src'));sys.path.insert(0,str(TASK/'scripts'))
from framework.data import load_dataset
from reproduce_source import load_records
from source_model import fit_source,loss
from exposure import rate_weights,intervals,histogram
from age_prior import MyModel,prior_value
from run_nested_validation import metrics

def main():
    ds=load_dataset(ROOT/'data');rows=[]
    for ev in ds.eval_points.itertuples(index=False):
        f=ds.operation.loc[ds.operation.timestamp.le(ev.date)].sort_values('timestamp',kind='stable')
        if f.empty:continue
        ts=f.timestamp.astype('int64').to_numpy();dt=np.diff(ts,prepend=ts[0])/1e9
        seg=f.segment.to_numpy();valid=(dt>0)&(dt<=60)&(seg==np.r_[seg[0],seg[:-1]])
        current=f.current_A.to_numpy();previous=np.r_[current[0],current[:-1]]
        masks={'charge':valid&(current>0)&(previous>0),'negative_normal':valid&(current<0)&(previous<0)&(np.abs(current)<15),
               'negative_20A_pulse':valid&(current<=-15)&(previous<=-15)}
        dc=np.diff(f.charge_Ah_cum.to_numpy(),prepend=f.charge_Ah_cum.iloc[0]);dd=np.diff(f.discharge_Ah_cum.to_numpy(),prepend=f.discharge_Ah_cum.iloc[0])
        for name,mask in masks.items():
            rows.append({'checkup':ev.checkup,'class':name,'intervals':int(mask.sum()),'integrated_magnitude_Ah':float((np.abs(current)*dt/3600)[mask].sum()),
                         'charge_counter_increment_Ah':float(dc[mask].sum()),'discharge_counter_increment_Ah':float(dd[mask].sum()),
                         'counter_negative_steps':int(((dc<0)|(dd<0))[mask].sum()),'counter_used_for_B':False})
    pd.DataFrame(rows).to_csv(TASK/'outputs/counter_semantics_by_prefix.csv',index=False)
    sensitivity=[]
    for ev in ds.eval_points.itertuples(index=False):
        prefix=ds.operation.loc[ds.operation.timestamp.le(ev.date)].copy()
        for stat in ['temp_mean_C','temp_min_C','temp_max_C']:
            op=prefix.copy();op['temp_mean_C']=op[stat] if stat in op else np.nan
            test=MyModel(TASK/'artifacts/source_prior.json');test.fit(ds)
            view=type(ds)(op,ds.checkups_released,ds.eval_points,ds.reference_discharge,ev.date)
            value=test.estimate_soh(view,ev.date)
            sensitivity.append({'checkup':ev.checkup,'temperature_input':stat,'SOH_est':value,'status':test.last_diagnostics['status'],
                'range_scope':'sensor statistics scenarios, not cell-core bounds or confidence interval'})
    pd.DataFrame(sensitivity).to_csv(TASK/'outputs/official_temperature_statistics_sensitivity.csv',index=False)
    selection=json.loads((TASK/'outputs/inner_selection.json').read_text());records=load_records();byid={r['cell_id']:r for r in records}
    panel=pd.read_csv(TASK/'outputs/panel_scoring.csv');out=[]
    for s in selection:
        if s['family']!='B':continue
        r=byid[s['heldout']];p=panel.loc[panel.cell_id.eq(s['heldout'])].sort_values('target_ordinal')
        model=fit_source([byid[x] for x in s['training_cells']],s['config']);anchor=float(p.anchor_soh_pp.iloc[0]);xi0=s['xi0']
        for delta in [-5,-2,-1,0,1,2,5]:
            xi=r['target_hist']@rate_weights(model['parameters'],model['rate_mode'],temperature_shift=delta)
            vals=anchor-loss(model['shape'],xi0+xi)+loss(model['shape'],xi0)
            for row,v in zip(p.itertuples(index=False),vals):out.append({'cell_id':row.cell_id,'target_ordinal':row.target_ordinal,
                  'target_soh_pp':row.target_soh_pp,'prediction_soh_pp':float(v),'temperature_sensor_bias_C':delta})
    f=pd.DataFrame(out);f.to_csv(TASK/'outputs/P1_temperature_bias_predictions.csv',index=False)
    pd.DataFrame([{'temperature_sensor_bias_C':d,**metrics(part)} for d,part in f.groupby('temperature_sensor_bias_C')]).to_csv(TASK/'outputs/P1_temperature_bias_summary.csv',index=False)
    files=[]
    for p in sorted((ROOT/'data').rglob('*')):
        if p.is_file() and p.name!='.DS_Store':files.append({'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
    (TASK/'outputs/official_input_registry.json').write_text(json.dumps(files,indent=2)+'\n')

if __name__=='__main__':main()
