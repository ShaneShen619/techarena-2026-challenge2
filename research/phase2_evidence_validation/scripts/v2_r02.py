"""R02 numerical back-substitution, identifiability, and D3 gated fallback."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
import numpy as np
import pandas as pd
TASK=Path(__file__).resolve().parents[1];ROOT=TASK.parents[1]
sys.path.insert(0,str(TASK/'src'))
from r02 import LoadedTemplate,fit_profile,local_svd
RUN=TASK/'runs/V2_R02_20260929_v1';RUN.mkdir(parents=True,exist_ok=True)
assert not (RUN/'COMPLETED').exists()
t=LoadedTemplate.from_csv(ROOT/'data/checkups/CK0_reference_discharge.csv.gz')
released=pd.read_csv(ROOT/'data/checkups/checkup_capacities_released.csv')
ck0=float(released.loc[released.checkup.eq('CK0'),'capacity_Ah'].iloc[0]); qroot=t.first_root()
assert qroot is not None and abs(qroot-ck0)<0.005,(qroot,ck0)
assert abs(t.voltage([0,t.q[-1]])[0]-t.pack_v[0])<1e-9
scales=np.arange(.85,1.0501,.005); offsets=np.arange(-3,3.001,.25);biases=np.arange(-.010,.0101,.002)
cases=[('same_model_capacity_loss',.94,0.,0.,'same_model'),
 ('start_only',1.,2.,0.,'same_model'),('bias_only',1.,0.,.006,'same_model'),
 ('thermal_or_hysteresis',1.,0.,0.,'different_model'),
 ('polarization_drift',1.,0.,0.,'different_model'),
 ('aging_curve_deformation',1.,0.,0.,'different_model'),
 ('mixed_mismatch',.96,1.,.004,'different_model')]
windows=[('plateau_20_30',20,10),('plateau_60_70',60,10),('knee_85_95',85,10),('long_40_90',40,50)]
profiles=[];summaries=[];sing=[]
rng=np.random.default_rng(29092026)
for w,start,span in windows:
    x=np.linspace(0,span,101)
    singular=local_svd(t,x,start)
    sing.append({'window':w,'largest':float(singular[0]),'middle':float(singular[1]),'smallest':float(singular[2]),
                 'condition_number':float(singular[0]/singular[-1])})
    for case,c,s,b,gen in cases:
        q=(start+s+x)/c
        if np.max(q)>t.q.max():continue
        y=np.interp(q,t.q,t.pack_v)+b
        if case=='thermal_or_hysteresis':y=y+.008*np.sin(np.pi*x/span)
        if case=='polarization_drift':y=y-.006*(1-np.exp(-x/2))
        if case=='aging_curve_deformation':y=y+.010*np.sin(2*np.pi*x/span)+.003*(x/span)
        if case=='mixed_mismatch':y=y+.008*np.sin(np.pi*x/span)-.004*(x/span)
        y=y+rng.normal(0,.001,len(x))
        p=fit_profile(t,x,y,start,scales,offsets,biases,.001)
        p.insert(0,'case',case);p.insert(0,'window',w)
        minm=p.data_mse_V2.min();p['delta_rmse_mV']=1000*(np.sqrt(p.data_mse_V2)-np.sqrt(minm))
        # Explicit illustrative penalty; its tightening is not evidence from data.
        p['penalized_objective_V2']=p.data_mse_V2+(.0015*(p.C_scale-1))**2
        profiles.append(p)
        best=p.loc[p.data_mse_V2.idxmin()]
        plausible=p.loc[p.delta_rmse_mV<=1.0,'C_scale']
        penal=p.loc[p.penalized_objective_V2.idxmin()]
        summaries.append({'window':w,'case':case,'generator':gen,'true_event_scale':c,
          'data_best_scale':float(best.C_scale),'data_best_start_offset_Ah':float(best.best_start_offset_Ah),
          'data_best_bias_mV':float(best.best_voltage_bias_V*1000),'data_rmse_mV':float(best.data_rmse_mV),
          'sensitivity_scale_min':float(plausible.min()),'sensitivity_scale_max':float(plausible.max()),
          'penalized_best_scale':float(penal.C_scale),'capacity_inference_valid':False,
          'note':'event state/reference full-charge mapping unavailable; interval is assumed 1mV RMSE sensitivity, not CI'})
pd.concat(profiles,ignore_index=True).to_csv(RUN/'loss_profiles.csv',index=False)
pd.DataFrame(summaries).to_csv(RUN/'scenario_summary.csv',index=False)
pd.DataFrame(sing).to_csv(RUN/'local_svd.csv',index=False)
# The official callable receives only CK0 anchor until reference condition and qualified events exist.
points=pd.read_csv(ROOT/'data/checkups/evaluation_points.csv')
rows=[]
for i,row in points.iterrows():
    ck=f'CK{i}'
    rows.append({'checkup':ck,'evidence_tier':'D3','protocol':'official_5p1A_pack_first_11p2V',
      'C_scale_estimate':np.nan,'Q_ref_estimate_Ah':np.nan,'prediction_Ah':ck0,
      'prediction_soh_percent':ck0/102*100,'fallback':'R01_CK0_constant',
      'capacity_update_qualified':False,
      'reason':'reference_temperature/full_charge_initial_state_unknown; zero strict >=5Ah qualified operational windows',
      'true_capacity_Ah':ck0 if i==0 else np.nan})
pd.DataFrame(rows).to_csv(RUN/'predictions_official_unlabeled.csv',index=False)
result={'run_id':RUN.name,'ck0_released_Ah':ck0,'ck0_first_pack_root_Ah':qroot,
 'ck0_backsub_abs_error_Ah':abs(qroot-ck0),'reference_temperature':'unknown',
 'capacity_validation_status':'not_testable_CK1_CK7_hidden','r02_official_update':'closed',
 'synthetic_scenarios':len(summaries),'root_boundary_example':{str(v):t.first_root(relative_pack_bias_V=v/1000) for v in [-10,-5,-2,0,2,5,10]},
 'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(RUN/'result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
(RUN/'COMPLETED').write_text('immutable run completed\n')
print(json.dumps(result,ensure_ascii=False))
