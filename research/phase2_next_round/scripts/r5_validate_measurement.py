"""Validate a proposed four-series measurement file and integrate capacity."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

REQUIRED=['group_id','cell1_id','cell2_id','cell3_id','cell4_id','checkup_id','timestamp','stage','current_A','pack_voltage_V','cell1_V','cell2_V','cell3_V','cell4_V','temp1_C','temp2_C','temp3_C','temp4_C','chamber_C','balance_state','stop_reason','instrument_id','calibration_version']

def validate(path:Path):
    d=pd.read_csv(path)
    missing=[c for c in REQUIRED if c not in d]
    if missing: raise ValueError(f'missing columns: {missing}')
    d['timestamp']=pd.to_datetime(d.timestamp,utc=True,errors='raise')
    rows=[]
    for (group,check),g in d.groupby(['group_id','checkup_id'],sort=False):
        g=g.sort_values('timestamp',kind='stable')
        if g.timestamp.duplicated().any(): raise ValueError(f'duplicate timestamp: {group}/{check}')
        cap=g.loc[g.stage.eq('capacity_discharge')].copy()
        if len(cap)<3: raise ValueError(f'capacity_discharge too short: {group}/{check}')
        if (cap.current_A>=0).any(): raise ValueError(f'non-discharge current in capacity stage: {group}/{check}')
        crossed=np.flatnonzero(cap.pack_voltage_V.to_numpy(float)<=11.2)
        if len(crossed)==0: raise ValueError(f'no group 11.2V crossing: {group}/{check}')
        end=int(crossed[0]); used=cap.iloc[:end+1]
        t=(used.timestamp-used.timestamp.iloc[0]).dt.total_seconds().to_numpy(float)
        q=float(np.trapezoid(-used.current_A.to_numpy(float),t)/3600)
        terminal=used.iloc[-1]
        reason=str(terminal.stop_reason)
        complete=reason=='group_11p2V'
        counter=np.nan
        if 'discharge_Ah_cum' in used and used.discharge_Ah_cum.notna().all():
            counter=float(used.discharge_Ah_cum.iloc[-1]-used.discharge_Ah_cum.iloc[0])
        rows.append({'group_id':group,'checkup_id':check,'capacity_Ah_integrated':q,'SOH_pp':100*q/102,
                     'counter_capacity_Ah':counter,'counter_minus_integrated_Ah':counter-q if np.isfinite(counter) else np.nan,
                     'first_crossing_timestamp':terminal.timestamp.isoformat(),'terminal_pack_voltage_V':float(terminal.pack_voltage_V),
                     'minimum_terminal_cell_V':float(terminal[['cell1_V','cell2_V','cell3_V','cell4_V']].min()),
                     'stop_reason':reason,'official_protocol_complete':complete,'samples':len(used)})
    return pd.DataFrame(rows)

def self_test(outdir:Path):
    outdir.mkdir(parents=True,exist_ok=True)
    n=1202; t=pd.date_range('2026-01-01T00:00:00Z',periods=n,freq='60s')
    current=np.full(n,-5.1); q=np.arange(n)*5.1/60; v=13.1-1.89*np.minimum(q/102,1)
    v[-1]=11.19
    d=pd.DataFrame({'group_id':'SYNTH_4S_01','cell1_id':'c1','cell2_id':'c2','cell3_id':'c3','cell4_id':'c4','checkup_id':'T0','timestamp':t,'stage':'capacity_discharge','current_A':current,'pack_voltage_V':v,'cell1_V':v/4,'cell2_V':v/4,'cell3_V':v/4,'cell4_V':v/4,'temp1_C':25,'temp2_C':25,'temp3_C':25,'temp4_C':25,'chamber_C':25,'discharge_Ah_cum':q,'charge_Ah_cum':0,'balance_state':'off','stop_reason':'running','instrument_id':'synthetic','calibration_version':'self-test'})
    d.loc[d.index[-1],'stop_reason']='group_11p2V'
    fixture=outdir/'synthetic_measurement.csv'; d.to_csv(fixture,index=False)
    result=validate(fixture); result.to_csv(outdir/'validation_result.csv',index=False)
    assert bool(result.official_protocol_complete.iloc[0]) and abs(result.capacity_Ah_integrated.iloc[0]-102.085)<0.01
    (outdir/'summary.json').write_text(json.dumps({'passed':True,'capacity_Ah':float(result.capacity_Ah_integrated.iloc[0]),'SOH_pp':float(result.SOH_pp.iloc[0]),'note':'synthetic integration/interface self-test only'},indent=2)+'\n')
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('csv',nargs='?'); ap.add_argument('--self-test',action='store_true'); ap.add_argument('--output-dir',default='research/phase2_next_round/runs/R5_measurement_validator_v1'); a=ap.parse_args()
    if a.self_test: result=self_test(Path(a.output_dir))
    elif a.csv: result=validate(Path(a.csv)); print(result.to_csv(index=False))
    else: raise SystemExit('provide CSV or --self-test')
    print(result.to_string(index=False))
