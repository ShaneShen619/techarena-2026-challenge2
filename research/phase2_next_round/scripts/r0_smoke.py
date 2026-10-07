"""Single-event, one-fold, CK1 prefix, serialization, and plot M0 smoke.

Uses old source as read-only inputs and never writes an old result directory.
This is execution/causality smoke, not a new capacity accuracy test.
"""
from __future__ import annotations

import hashlib
import json
import pickle
import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
OLD = ROOT/'research/phase2_temperature_improvement'
sys.path.insert(0, str(OLD/'src'))
sys.path.insert(0, str(OLD/'scripts'))
from event_core import extract_charge_events, partial_ah
from route_a_repaired import stable_cc_prefix
from run_m2_repaired import load_charging
from multi_window_ridge import add_derived_features, RidgeFeatureModel
from official_fallback import OfficialFallback

OUT = TASK/'runs/R0_smoke_v1'
OUT.mkdir(parents=True, exist_ok=False)
panel_path = OLD/'outputs/panel_main.csv'
assert hashlib.sha256(panel_path.read_bytes()).hexdigest() == '7188b662900f84312292a7062d6023e5eeb4f2e32798b6d61a3547ed40cdc59c'
panel = pd.read_csv(panel_path)
key = ['cell_id','target_ordinal']
f = pd.read_csv(OLD/'runs/M4_feature_audit_v1/features.csv')
a = pd.read_csv(OLD/'runs/M4_feature_audit_v1/throughput.csv')
f = f.merge(a[key+['qualified_charge_efc']],on=key,validate='one_to_one')
f = f.merge(panel[key+['anchor_soh_pp','target_soh_pp']],on=key,validate='one_to_one')
f = add_derived_features(f,age_col='qualified_charge_efc')
held = sorted(f.cell_id.unique())[0]
train = f[f.cell_id!=held]
target = f[f.cell_id==held].sort_values('target_ordinal').head(1)
model = RidgeFeatureModel.fit(train,'0.04V',1.0,with_temperature=False)
prediction = float(model.predict(target)[0])
if not np.isfinite(prediction): raise AssertionError('nonfinite fold prediction')
with (OUT/'model.pkl').open('wb') as h: pickle.dump(model,h)
target[model.columns+['anchor_soh_pp']].to_csv(OUT/'single_target.csv',index=False)
fresh_code = '''import pickle,pandas as pd,sys
sys.path.insert(0,sys.argv[3])
with open(sys.argv[1],'rb') as f:m=pickle.load(f)
x=pd.read_csv(sys.argv[2]);print(float(m.predict(x)[0]))'''
fresh = subprocess.run([sys.executable,'-c',fresh_code,str(OUT/'model.pkl'),str(OUT/'single_target.csv'),str(OLD/'src')],
                       capture_output=True,text=True)
if fresh.returncode:
    raise RuntimeError(f'fresh process failed: {fresh.stderr}')
fresh_prediction = float(fresh.stdout.strip())
assert abs(fresh_prediction-prediction)<1e-10

cutoff = pd.Timestamp(panel.loc[panel.cell_id.eq(held)].sort_values('target_ordinal').iloc[0].target_discharge_start)
raw = load_charging(held)
raw = raw[raw.absolute_time<cutoff]
events = extract_charge_events(raw,time_col='absolute_time',voltage_cols=('voltage_V',),
                               temp_col='temperature_C',segment_col='cycle_number',counter_col=None)
event_result = None
for event in reversed(events):
    cc,status = stable_cc_prefix(event)
    if status=='pass' and cc is not None:
        q=partial_ah(cc,0,3.38,3.42)
        if q is not None:
            event_result={'event_start':event.start.isoformat(),'event_end':event.end.isoformat(),
                          'target_cutoff':cutoff.isoformat(),'cc_Ah':float(cc.ah),
                          'window_3p38_3p42_Ah':float(q),
                          'observed_modal_dt_s':float(pd.Series(np.diff(cc.times_s)).mode().iat[0])}
            assert event.end<cutoff
            break
if event_result is None: raise RuntimeError('no valid P1 smoke event')

ck1=pd.Timestamp('2025-02-08')
parts=[]
for path in sorted((ROOT/'data/operation').glob('*.csv.gz')):
    # Only segments whose first timestamp precedes CK1 can contribute.
    head=pd.read_csv(path,nrows=1,usecols=['timestamp'],parse_dates=['timestamp'])
    if head.timestamp.iat[0]>=ck1: continue
    frame=pd.read_csv(path,parse_dates=['timestamp'])
    parts.append(frame.loc[frame.timestamp<ck1])
official=pd.concat(parts,ignore_index=True).sort_values('timestamp',kind='stable')
assert official.timestamp.max()<ck1 and len(official)>0
official_model=OfficialFallback(100.41,anchor_time=pd.Timestamp('2025-01-14'))
official_prediction=float(official_model.estimate(official,ck1))
assert np.isfinite(official_prediction)

fig,ax=plt.subplots(figsize=(6,3))
ax.plot([0,1],[float(panel.loc[panel.cell_id.eq(held)].iloc[0].anchor_soh_pp),prediction],marker='o')
ax.set(xlabel='Anchor / smoke target index',ylabel='Estimated SOH (percentage points)',
       title='M0 execution smoke: one held physical cell')
fig.tight_layout();fig.savefig(OUT/'smoke.png',dpi=130);plt.close(fig)
if (OUT/'smoke.png').stat().st_size<1000: raise AssertionError('plot too small')
pd.DataFrame([{'cell_id':held,'prediction_soh_pp':prediction,'actual_soh_pp':float(target.target_soh_pp.iat[0]),
               'note':'single-target smoke, not a validated method result'}]).to_csv(OUT/'smoke_prediction.csv',index=False)
summary={'fold_held_cell':held,'one_fold_prediction_soh_pp':prediction,
         'serialization_fresh_process_max_diff_pp':abs(fresh_prediction-prediction),
         'event':event_result,'official_ck1_prefix_rows':len(official),
         'official_ck1_prefix_end':official.timestamp.max().isoformat(),
         'official_ck1_unlabeled_prediction_soh_pp':official_prediction,
         'official_branch':official_model.last_diagnostics.get('mode'),
         'note':'Execution smoke only; CK1 hidden truth and P1 single point do not establish accuracy.'}
(OUT/'smoke.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False),flush=True)
