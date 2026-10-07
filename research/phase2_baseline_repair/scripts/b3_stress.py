"""Predeclared mechanism stress tests on official CK2 prefix, no capacity labels."""
import importlib.util
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3];TASK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from framework.data import load_dataset
spec=importlib.util.spec_from_file_location('candidate',TASK/'candidates/causal_baseline/my_model/model_baseline.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

def predict(ds,op,gate='range'):
    m=mod.ActiveModel(gate);m.fit(ds)
    ds.operation=op
    y=m.estimate_soh(ds,pd.Timestamp('2025-03-11'))
    return float(y),m.last_q_ref,len(mod.events(op))

def main():
    run=TASK/'runs/B3_mechanism_stress_20260930_v3';run.mkdir(exist_ok=True)
    ds=load_dataset(ROOT/'data',until='2025-03-11')
    source=ds.operation
    base=predict(ds,source)
    cases={}
    cases['missing_temperature']=source.copy();cases['missing_temperature'][['temp_mean_C','temp_min_C','temp_max_C']]=np.nan
    cases['swap_Ah_counters']=source.copy();cases['swap_Ah_counters'][['charge_Ah_cum','discharge_Ah_cum']]=source[['discharge_Ah_cum','charge_Ah_cum']].to_numpy()
    cases['remove_segment_3']=source[source.segment!=3].copy()
    cases['no_charge_events']=source.iloc[:0].copy()
    cases['duplicate_one_timestamp']=source.copy();cases['duplicate_one_timestamp'].loc[1001,'timestamp']=cases['duplicate_one_timestamp'].loc[1000,'timestamp']
    cases['reverse_one_local_interval']=source.copy();cases['reverse_one_local_interval'].loc[1001,'timestamp']=cases['reverse_one_local_interval'].loc[1000,'timestamp']-pd.Timedelta(seconds=10)
    cases['flip_all_current']=source.copy();cases['flip_all_current']['current_A']=-source.current_A
    cases['temperature_plus_10C']=source.copy();cases['temperature_plus_10C'][['temp_mean_C','temp_min_C','temp_max_C']]+=10
    cases['pack_voltage_plus_10mV']=source.copy();cases['pack_voltage_plus_10mV']['pack_voltage_V']+=.01
    cases['pack_voltage_minus_10mV']=source.copy();cases['pack_voltage_minus_10mV']['pack_voltage_V']-=.01
    cases['pack_voltage_plus_100mV']=source.copy();cases['pack_voltage_plus_100mV']['pack_voltage_V']+=.1
    cases['pack_voltage_minus_100mV']=source.copy();cases['pack_voltage_minus_100mV']['pack_voltage_V']-=.1
    cases['current_gain_plus_5pct']=source.copy();cases['current_gain_plus_5pct']['current_A']*=1.05
    cases['current_offset_plus_0p1A']=source.copy();cases['current_offset_plus_0p1A']['current_A']+=.1
    cases['current_offset_minus_0p1A']=source.copy();cases['current_offset_minus_0p1A']['current_A']-=.1
    cases['targeted_gap_90s']=source.copy();cases['targeted_gap_90s'].loc[43400,'timestamp']+=pd.Timedelta(seconds=90)
    cases['targeted_duplicate_stamp']=source.copy();cases['targeted_duplicate_stamp'].loc[43400,'timestamp']=cases['targeted_duplicate_stamp'].loc[43399,'timestamp']
    # Remove anomalous segment-first full charge while retaining ordinary cycles.
    cases['remove_44_58_Ah_rows']=source.copy()
    cases['remove_44_58_Ah_rows']=cases['remove_44_58_Ah_rows'][~(((source.timestamp>='2025-01-19 22:26:21')&(source.timestamp<='2025-01-20 00:36:08'))|((source.timestamp>='2025-02-12 01:02:05')&(source.timestamp<='2025-02-12 03:57:43')))].reset_index(drop=True)
    rows=[]
    for name,x in cases.items():
        try:
            y,q,n=predict(ds,x)
            err=None
        except Exception as ex:
            y=q=n=None;err=repr(ex)
        rows.append(dict(intervention=name,baseline_pct=base[0],prediction_pct=y,delta_pp=None if y is None else y-base[0],
            q_ref_Ah=q,n_events=n,error=err,capacity_truth_held_constant='assumed_intervention_only',
            task='same_checkpoint_signal_stress',evidence_level='mechanism_not_capacity_accuracy'))
    d=pd.DataFrame(rows);d.to_csv(TASK/'outputs/stress_results.csv',index=False)
    cross=[]
    for gate in ['none','range','gap','combined','start']:
        by=predict(ds,source,gate)[0]
        gy=predict(ds,cases['targeted_gap_90s'],gate)[0]
        cross.append(dict(candidate=gate,baseline_pct=by,targeted_gap_pct=gy,delta_pp=gy-by,
            evidence_level='synthetic_gap_mechanism_not_capacity_accuracy'))
    pd.DataFrame(cross).to_csv(TASK/'outputs/stress_gate_cross.csv',index=False)
    assert not d.error.notna().any()
    for name in ['missing_temperature','swap_Ah_counters','remove_segment_3','temperature_plus_10C']:
        assert float(d.set_index('intervention').loc[name,'delta_pp'])==0
    (run/'result.json').write_text(json.dumps(dict(baseline_pct=base[0],tests=len(d),all_no_crash=True,invariant_controls_passed=True),indent=2))
    (run/'COMPLETED').write_text('completed\n')
    print(d[['intervention','prediction_pct','delta_pp','n_events']].to_string(index=False))

if __name__=='__main__':main()
