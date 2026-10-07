"""Test whether 'historical exposure' helps beyond the first ten event temperatures."""
from __future__ import annotations
import json,re,sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3]
TASK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TASK/'src'))
from m2_features import frame_for_condition
OUT=TASK/'runs/M3_static_vs_rolling_v1'
OUT.mkdir(parents=True,exist_ok=False)
source=ROOT/'research/phase2_temperature_improvement/runs/M4_feature_audit_v1/events.csv'
events=pd.read_csv(source,usecols=['cell_id','event_end','cc_Ah','temp_C'],parse_dates=['event_end'])
X=frame_for_condition(20,'persistent')
panel=pd.read_csv(ROOT/'research/phase2_temperature_improvement/outputs/panel_main.csv',
                  usecols=['cell_id','target_ordinal','target_discharge_start',
                           'anchor_discharge_start','target_soh_pp'])
full=pd.read_csv(TASK/'runs/M3_prefix_temperature_v1/prefix_temperature_manifest.csv',
                 usecols=['cell_id','target_ordinal','prefix_mean_event_T_C'])
model=X.merge(panel,on=['cell_id','target_ordinal'],validate='one_to_one').merge(
    full,on=['cell_id','target_ordinal'],validate='one_to_one')
static=[]
for row in model.itertuples(index=False):
    prior=events.loc[(events.cell_id==row.cell_id)&
                     (events.event_end>pd.Timestamp(row.anchor_discharge_start))&
                     (events.event_end<pd.Timestamp(row.target_discharge_start))&
                     (events.cc_Ah>=20)].sort_values('event_end')
    first=prior.temp_C.head(10)
    static.append(float(first.mean()) if first.notna().any() else np.nan)
model['initial10_mean_T_C']=static
assert model.initial10_mean_T_C.notna().all()
model[['cell_id','target_ordinal','initial10_mean_T_C','prefix_mean_event_T_C',
       'current_temp_C']].to_csv(OUT/'temperature_channels.csv',index=False)
y=model.target_soh_pp.to_numpy(float)
cell=model.cell_id.to_numpy(str)
groups=np.array([int(re.search(r'_(\d+)degC_',s).group(1)) for s in cell])
anchor=model.anchor_pp.to_numpy(float)
base=['age_days','age_log1p','prefix_prequalified_charge_count']
methods={'noT':base,'currentT':base+['current_temp_C'],
         'static_initial10_plus_currentT':base+['initial10_mean_T_C','current_temp_C'],
         'rolling_fullprefix_plus_currentT':base+['prefix_mean_event_T_C','current_temp_C']}
def predict(train,test,cols,alpha):
    a=model.iloc[train][cols].to_numpy(float);b=model.iloc[test][cols].to_numpy(float)
    med=np.array([np.nanmedian(z) if np.isfinite(z).any() else 0. for z in a.T])
    a=np.where(np.isfinite(a),a,med);b=np.where(np.isfinite(b),b,med)
    mean=a.mean(axis=0);scale=a.std(axis=0);scale=np.where(scale>=1e-10,scale,1.)
    a=(a-mean)/scale;b=(b-mean)/scale
    aa=np.column_stack([np.ones(len(a)),a]);bb=np.column_stack([np.ones(len(b)),b])
    coef=np.linalg.solve(aa.T@aa+np.diag([1e-10]+[alpha+1e-10]*a.shape[1]),
                         aa.T@(y[train]-anchor[train]))
    return anchor[test]+bb@coef
def selected(train,cols):
    result=[]
    for alpha in [.1,1,10,100,1000]:
        errs=[]
        for c in np.unique(cell[train]):
            val=train[cell[train]==c];fit=train[cell[train]!=c]
            errs.append(float(np.abs(predict(fit,val,cols,alpha)-y[val]).mean()))
        result.append((np.mean(errs),alpha))
    return min(result)
preds=[];select=[]
for split in ['cell','temperature_group']:
    holdouts=np.unique(cell) if split=='cell' else np.unique(groups)
    for held in holdouts:
        chosen=(cell==held) if split=='cell' else (groups==held)
        train=np.flatnonzero(~chosen);test=np.flatnonzero(chosen)
        for name,cols in methods.items():
            score,alpha=selected(train,cols)
            select.append({'split':split,'held':held,'method':name,'alpha':alpha,'inner_macro_mae_pp':score})
            result=predict(train,test,cols,alpha)
            for i,index in enumerate(test):
                preds.append({'split':split,'held':held,'cell_id':cell[index],
                              'target_ordinal':int(model.target_ordinal.iat[index]),
                              'method':name,'actual_pp':float(y[index]),
                              'pred_pp':float(result[i]),'error_pp':float(result[i]-y[index])})
    print('finished',split,flush=True)
out=pd.DataFrame(preds);out.to_csv(OUT/'predictions.csv',index=False)
pd.DataFrame(select).to_csv(OUT/'inner_selections.csv',index=False)
metrics=[]
for (split,name),part in out.groupby(['split','method']):
    per=part.assign(ae=part.error_pp.abs()).groupby('cell_id').ae.mean()
    metrics.append({'split':split,'method':name,'macro_mae_pp':float(per.mean()),
                    'worst_cell_mae_pp':float(per.max()),
                    'max_abs_error_pp':float(part.error_pp.abs().max())})
(OUT/'summary.json').write_text(json.dumps({'metrics':metrics,
    'first10_temperature_definition':'first ten post-anchor completed >=20Ah event temperatures known by each target',
    'rolling_definition':'all post-anchor completed >=20Ah event temperatures known by each target',
    'input_budget_note':'Both historical summaries read complete event median temperatures; supplemental, not D1 15 cropped fragment budget.'},
    ensure_ascii=False,indent=2)+'\n')
print(json.dumps(metrics,ensure_ascii=False),flush=True)
