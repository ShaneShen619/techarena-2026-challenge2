"""Che D3 field qualification and same-charge partial-Q shape check."""
from __future__ import annotations
import json
from pathlib import Path
import h5py
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3]
TASK=Path(__file__).resolve().parents[1]
OUT=TASK/'runs/M2_Che_shape_v1'
OUT.mkdir(parents=True,exist_ok=False)
def string(f,ref):return ''.join(chr(int(x)) for x in f[ref][()].ravel())
rows=[];shape=[]
with h5py.File(ROOT/'Che-Dataset3.mat','r') as f:
    main=f['Dataset3']
    assert set(main.keys())=={'Capacity','Workingprofile','cell','cycles'}
    for j in range(main['Capacity'].shape[0]):
        name=string(f,main['cell'][j,0])
        profile=string(f,main['Workingprofile'][j,0])
        cap=f[main['Capacity'][j,0]][()].ravel().astype(float)
        events=f[main['cycles'][j,0]]
        assert set(events)=={'Partial_Q','Partial_dQ'}
        qref=events['Partial_Q'][()].ravel()
        dqref=events['Partial_dQ'][()].ravel()
        assert len(qref)==len(dqref)==len(cap)
        q=[f[ref][()].ravel().astype(float) for ref in qref]
        assert all(len(x)==101 for x in q)
        shape.append({'cell_id':name,'cycles':len(cap),'all_partial_Q_101_points':True,
                      'all_capacity_finite':bool(np.isfinite(cap).all()),
                      'all_partial_Q_finite':bool(all(np.isfinite(z).all() for z in q))})
        for stage,pct in [('early',.1),('middle',.5),('late',.9)]:
            i=round((len(cap)-1)*pct)
            ratio=float(q[i][-1]/q[0][-1])
            rows.append({'cell_id':name,'working_profile':profile,'stage':stage,
                         'cycle_index':i,'charge_capacity_Ah':float(cap[i]),
                         'partial_Q_end_ratio':ratio,
                         'charge_capacity_ratio':float(cap[i]/cap[0]),
                         'same_charge_process_error_pp':float(100*(ratio-cap[i]/cap[0]))})
pd.DataFrame(rows).to_csv(OUT/'same_charge_diagnostics.csv',index=False)
pd.DataFrame(shape).to_csv(OUT/'field_qualification.csv',index=False)
score=pd.DataFrame(rows)
summary={'physical_cells':len(shape),'cycles':int(sum(s['cycles'] for s in shape)),
         'three_stages_per_cell':len(rows),
         'same_charge_process_proxy_mae_pp':float(score.same_charge_process_error_pp.abs().mean()),
         'explicit_voltage_grid_in_local_file':False,'raw_time_current_voltage_in_local_file':False,
         'target_label':'full charge capacity in same charging process',
         'official_4S_C20_capacity_compatible':False,
         'interpretation':'Only field/shape qualification; shared same-charge input-label process is not independent forward capacity validation.'}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False),flush=True)
