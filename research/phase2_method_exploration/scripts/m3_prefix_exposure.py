"""Supplemental prior-event temperature scalars, kept outside D1 main ranking."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3]
TASK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TASK/'src'))
from m2_features import frame_for_condition
OUT=TASK/'runs/M3_prefix_temperature_v1'
OUT.mkdir(parents=True,exist_ok=False)
source=ROOT/'research/phase2_temperature_improvement/runs/M4_feature_audit_v1/events.csv'
events=pd.read_csv(source,usecols=['cell_id','event_id','event_end','cc_Ah','temp_C'],
                   parse_dates=['event_end'])
X=frame_for_condition(20,'persistent')
panel=pd.read_csv(ROOT/'research/phase2_temperature_improvement/outputs/panel_main.csv',
                  usecols=['cell_id','target_ordinal','target_discharge_start',
                           'anchor_discharge_start','target_soh_pp'])
joined=X[['cell_id','target_ordinal']].merge(panel,on=['cell_id','target_ordinal'],validate='one_to_one')
EA=37300.;RGAS=8.314
features=[]
for item in joined.itertuples(index=False):
    prior=events.loc[(events.cell_id==item.cell_id)&
                     (events.event_end>pd.Timestamp(item.anchor_discharge_start))&
                     (events.event_end<pd.Timestamp(item.target_discharge_start))&
                     (events.cc_Ah>=20)]
    if len(prior) and not prior.event_end.max()<pd.Timestamp(item.target_discharge_start):
        raise AssertionError('future temperature event')
    t=prior.temp_C.to_numpy(float)
    valid=t[np.isfinite(t)]
    acceleration=np.exp(np.clip(EA/RGAS*(1/298.15-1/(valid+273.15)),-3,3))
    features.append({'cell_id':item.cell_id,'target_ordinal':item.target_ordinal,
                     'qualified_completed_event_count_after_anchor':len(prior),
                     'temperature_observed_fraction':len(valid)/len(t) if len(t) else 0.,
                     'prefix_mean_event_T_C':float(valid.mean()) if len(valid) else np.nan,
                     'prefix_hot_event_fraction_above40C':float((valid>40).mean()) if len(valid) else np.nan,
                     'prefix_arrhenius_event_sum':float(acceleration.sum()/1000),
                     'max_source_event_end_audit':prior.event_end.max().isoformat() if len(prior) else ''})
feat=pd.DataFrame(features)
feat.to_csv(OUT/'prefix_temperature_manifest.csv',index=False)
model=X.merge(feat.drop(columns='max_source_event_end_audit'),on=['cell_id','target_ordinal'],validate='one_to_one')
keys=pd.MultiIndex.from_frame(model[['cell_id','target_ordinal']])
y=panel.set_index(['cell_id','target_ordinal']).loc[keys,'target_soh_pp'].to_numpy(float)
cell=model.cell_id.to_numpy(str);anchor=model.anchor_pp.to_numpy(float)
base=['age_days','age_log1p','prefix_prequalified_charge_count']
methods={
    'stable_noT':base,
    'current_T_only':base+['current_temp_C'],
    'full_prefix_meanT':base+['prefix_mean_event_T_C'],
    'full_prefix_hot_fraction':base+['prefix_hot_event_fraction_above40C'],
    'full_prefix_arrhenius':base+['prefix_arrhenius_event_sum'],
    'full_prefix_meanT_plus_currentT':base+['prefix_mean_event_T_C','current_temp_C']
}
def predict(train,test,cols,alpha):
    a=model.iloc[train][cols].to_numpy(float)
    b=model.iloc[test][cols].to_numpy(float)
    med=np.array([np.nanmedian(z) if np.isfinite(z).any() else 0. for z in a.T])
    a=np.where(np.isfinite(a),a,med);b=np.where(np.isfinite(b),b,med)
    mean=a.mean(axis=0);scale=a.std(axis=0);scale=np.where(scale>=1e-10,scale,1.)
    a=(a-mean)/scale;b=(b-mean)/scale
    aa=np.column_stack([np.ones(len(a)),a]);bb=np.column_stack([np.ones(len(b)),b])
    coef=np.linalg.solve(aa.T@aa+np.diag([1e-10]+[alpha+1e-10]*a.shape[1]),
                         aa.T@(y[train]-anchor[train]))
    return anchor[test]+bb@coef
rows=[];selected=[]
for held in np.unique(cell):
    train=np.flatnonzero(cell!=held);test=np.flatnonzero(cell==held)
    for name,cols in methods.items():
        candidates=[]
        for alpha in [.1,1,10,100,1000]:
            errors=[]
            for inner in np.unique(cell[train]):
                val=train[cell[train]==inner];fit=train[cell[train]!=inner]
                errors.append(float(np.abs(predict(fit,val,cols,alpha)-y[val]).mean()))
            candidates.append((np.mean(errors),alpha))
        score,alpha=min(candidates)
        selected.append({'held_cell':held,'method':name,'alpha':alpha,'inner_macro_mae_pp':score})
        result=predict(train,test,cols,alpha)
        for i,index in enumerate(test):
            rows.append({'cell_id':held,'target_ordinal':int(model.target_ordinal.iat[index]),
                         'method':name,'actual_pp':float(y[index]),
                         'pred_pp':float(result[i]),'error_pp':float(result[i]-y[index])})
pred=pd.DataFrame(rows);pred.to_csv(OUT/'predictions.csv',index=False)
pd.DataFrame(selected).to_csv(OUT/'inner_selections.csv',index=False)
metrics=[]
for name,part in pred.groupby('method'):
    per=part.assign(ae=part.error_pp.abs()).groupby('cell_id').ae.mean()
    metrics.append({'method':name,'macro_mae_pp':float(per.mean()),
                    'worst_cell_mae_pp':float(per.max()),
                    'max_abs_error_pp':float(part.error_pp.abs().max())})
summary={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
         'event_temperature_definition':'median of complete earlier P1 charging event, after anchor; extra scalar channel',
         'temperature_observation_fraction_median':float(feat.temperature_observed_fraction.median()),
         'event_count_range':[int(feat.qualified_completed_event_count_after_anchor.min()),
                              int(feat.qualified_completed_event_count_after_anchor.max())],
         'metrics':metrics,
         'claim_limit':'Not the main D1 15-fragment input budget; full-event T differs from official clipped shallow charge. Six cells cannot isolate aging vs conditions.'}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({z['method']:z['macro_mae_pp'] for z in metrics},ensure_ascii=False),flush=True)
