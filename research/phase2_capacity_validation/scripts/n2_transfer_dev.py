"""Development-only Ji single-cell transfer experiment. No sealed labels are read."""
import csv
import hashlib
import json
import math
from datetime import datetime
from pathlib import Path

import numpy as np
from openpyxl import load_workbook

T = Path(__file__).resolve().parents[1]
SPLIT = list(csv.DictReader((T/'outputs/split_manifest.csv').open()))
LABELS = {r['entity_id']: r for r in csv.DictReader((T/'sealed/ji_23_private_label_map.csv').open()) if r['split']=='development'}

def features(path):
    sheet = load_workbook(path, read_only=True, data_only=True).active
    it = iter(sheet.values)
    header = next(it)
    assert header[:3] == ('Date_Time','Voltage(V)','Current(A)')
    assert header[3] in ('SOC','SOC_fake')  # both excluded from features
    rows=[]
    for r in it:
        if not isinstance(r[1], (int,float)) or not isinstance(r[2], (int,float)):
            continue
        rows.append((datetime.fromisoformat(r[0]).timestamp(),float(r[1]),float(r[2])))
    # Source records one or two duplicate seconds per file; use last record at that second.
    dedup=[]
    for row in rows:
        if dedup and row[0]==dedup[-1][0]:dedup[-1]=row
        else:dedup.append(row)
    rows=dedup
    assert len(rows)>100 and all(b[0]>a[0] for a,b in zip(rows,rows[1:]))
    dt=np.diff([x[0] for x in rows])
    assert max(dt)<=10 and min(dt)>0
    v=np.array([x[1] for x in rows]); i=np.array([x[2] for x in rows]); t=np.array([x[0] for x in rows])
    # Fixed physics-motivated upper charge plateau, with initial SOC field excluded.
    # Both endpoints occur in all 23 source files based on schema-only audit.
    lo=np.flatnonzero(v>=3.35); hi=np.flatnonzero(v>=3.50)
    assert len(lo) and len(hi) and hi[0]>lo[0]
    a,b=lo[0],hi[0]
    q=float(np.sum((i[a:b]+i[a+1:b+1])*np.diff(t[a:b+1])/7200))
    # Whole charge is kept only as a negative-control feature: starts differ.
    q_all=float(np.sum((i[:-1]+i[1:])*dt/7200))
    return dict(q_335_350_Ah=q,q_all_Ah=q_all,elapsed_335_350_s=float(t[b]-t[a]),
                start_V=float(v[0]),end_V=float(v[-1]),max_gap_s=float(max(dt)),n_rows=len(rows))

def fit_predict(train_x,train_y,test_x,kind):
    if kind=='median':return float(np.median(train_y))
    col={'q_window':'q_335_350_Ah','q_whole_negative_control':'q_all_Ah'}[kind]
    x=np.array([v[col] for v in train_x]); z=np.array([v[col] for v in test_x])
    slope=float(np.dot(x-x.mean(),train_y-train_y.mean())/max(np.dot(x-x.mean(),x-x.mean()),1e-12))
    return float(train_y.mean()+slope*(z[0]-x.mean()))

dev=[r for r in SPLIT if r['split']=='development']
held=[r for r in SPLIT if r['split']=='sealed_holdout']
assert len(dev)==15 and len(held)==8 and len(LABELS)==15
rows=[]
for r in SPLIT:
    f=features(T/r['staging_path'])
    rows.append(dict(entity_id=r['entity_id'],split=r['split'],**f))
with (T/'outputs/transfer_features_v2.csv').open('w',newline='') as o:
    w=csv.DictWriter(o,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
df=[r for r in rows if r['split']=='development']
ys=np.array([float(LABELS[r['entity_id']]['capacity_Ah_author_mean_3']) for r in df])
pred=[];metrics=[]
for kind in ['median','q_window','q_whole_negative_control']:
    errors=[]
    for j,r in enumerate(df):
        idx=[k for k in range(len(df)) if k!=j]
        p=fit_predict([df[k] for k in idx],ys[idx],[r],kind)
        e=p-ys[j]
        pred.append(dict(source_id='Ji_second_life_23',tier='different_protocol_single_cell',entity_id=r['entity_id'],
                         split='development_LOOCV',candidate=kind,target_Ah=ys[j],prediction_Ah=p,error_Ah=e,
                         target_provenance='author_mean_three_prior_tests_filename',
                         official_four_series_SOH_pp='',late_stage='unavailable'))
        errors.append(abs(e))
    metrics.append(dict(candidate=kind,dev_n=15,dev_macro_MAE_Ah=float(np.mean(errors)),dev_worst_Ah=float(max(errors)),
                        target='author_prior_mean_capacity_Ah',status='development_only'))
with (T/'outputs/transfer_dev_predictions_v2.csv').open('w',newline='') as o:
    w=csv.DictWriter(o,fieldnames=pred[0].keys());w.writeheader();w.writerows(pred)
with (T/'outputs/transfer_dev_metrics_v2.csv').open('w',newline='') as o:
    w=csv.DictWriter(o,fieldnames=metrics[0].keys());w.writeheader();w.writerows(metrics)
eligible=[m for m in metrics if m['candidate'] in ('median','q_window')]
selection=sorted(eligible,key=lambda m:(m['dev_macro_MAE_Ah'],m['dev_worst_Ah'],['median','q_window'].index(m['candidate'])))[0]['candidate']
config=dict(version='2026-09-30-transfer-final-freeze-v2',initial_config_sha256=hashlib.sha256((T/'configs/transfer_initial_v1.json').read_bytes()).hexdigest(),
  split_sha256=hashlib.sha256((T/'outputs/split_manifest.csv').read_bytes()).hexdigest(),
  staging_source_zip_sha256=hashlib.sha256((T/'downloads/SLBs_LFP_charging_data.zip').read_bytes()).hexdigest(),
  feature_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
  selected_candidate=selection,comparators=['median','q_window'],
  excluded_diagnostic='q_whole_negative_control excluded before holdout: whole-curve integral nearly reconstructs same-test capacity target in development; not a legitimate predictive signal',
  fitting='one feature ordinary least squares with intercept on 15 development cells; median comparator; LOOCV selection',
  voltage_window_V=[3.35,3.50],crossing_rule='first recorded sample at or above each threshold',integral='trapezoid current over observed interval',
  valid_gap_s_max=10,duplicate_timestamp_rule='keep last record at that second',eval_holdout_once=True,metrics=['MAE_Ah','max_AE_Ah','signed_bias_Ah','overestimate_fraction'],
  prohibit_fields=['SOC','source filename','target RPT/discharge'],
  exposure='researcher nonblind to some source member label filenames; program separated; limited one-shot holdout',
  scope='different-protocol 23 single LFP cells only; not official 4S SOH',
  stop_condition='one final holdout evaluation; no retuning after scores')
out=T/'configs/transfer_final_freeze_v2.json';out.write_text(json.dumps(config,indent=2,ensure_ascii=False))
run=T/'runs/N2_transfer_development_20260930_v2';run.mkdir(exist_ok=True)
(run/'result.json').write_text(json.dumps({'selected_candidate':selection,'dev_metrics':metrics,
 'config_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'holdout_labels_accessed':False},indent=2))
(run/'COMPLETED').write_text('complete\n')
print((run/'result.json').read_text())
