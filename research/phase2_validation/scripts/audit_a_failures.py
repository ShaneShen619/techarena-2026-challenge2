"""Read-only diagnostic of current A reference selection on recorded targets.

This reproduces the existing rule to explain failures, without modifying any
candidate or using the recorded labels to select a new model.
"""
from pathlib import Path
import sys
import pandas as pd
import numpy as np

TASK=Path(__file__).resolve().parents[1]
ROOT=TASK.parents[1]
sys.path.insert(0,str(TASK/'src'))
from event_core import extract_charge_events,partial_ah

def main():
    targets=pd.read_csv(TASK/'outputs/phase1_crossvalidation_predictions.csv')
    targets=targets[targets.method.eq('A')]
    details=[];summaries=[]
    for cid,ct in targets.groupby('cell_id'):
        cols=['absolute_time','cycle_number','step_type','voltage_V','current_A','temperature_C']
        raw=pd.concat([pd.read_csv(p,usecols=cols,parse_dates=['absolute_time'])
                       for p in sorted((ROOT/'dataset original'/cid).glob('*.csv'))],ignore_index=True)
        raw=raw[~raw.step_type.eq('cc_discharge')]
        for row in ct.itertuples():
            cutoff=pd.Timestamp(row.target_discharge_start)
            events=extract_charge_events(raw,until=cutoff,voltage_cols=('voltage_V',),
                time_col='absolute_time',temp_col='temperature_C',segment_col='cycle_number',counter_col=None)
            refs={};recent=[];outside=0
            for ev in events:
                if not np.isfinite(ev.median_temp) or ev.ah<15:continue
                depth='deep' if ev.ah>=50 else 'shallow'
                tb=int(round(ev.median_temp/20))
                for wi,(lo,hi) in enumerate(((3.33,3.40),(3.36,3.43))):
                    q=partial_ah(ev,0,lo,hi)
                    if q is None or q<1:continue
                    key=(wi,tb,depth)
                    if key not in refs:
                        refs[key]=(q,ev)
                        continue
                    if abs(ev.median_temp-20*tb)>7:
                        outside+=1;continue
                    rq,re=refs[key]
                    if abs(ev.median_current-re.median_current)>0.2*max(re.median_current,1):continue
                    if (cutoff-ev.end).total_seconds()>30*86400:continue
                    recent.append({'cell_id':cid,'stage':row.stage,'target_cycle':row.target_cycle,
                        'target_soh_pp':row.target_soh_pp,'prediction_soh_pp':row.prediction_soh_pp,
                        'window':f'{lo:.2f}-{hi:.2f}','temperature_bin_center_C':20*tb,
                        'event_end':ev.end,'event_cycle':ev.segment,'event_temp_C':ev.median_temp,
                        'event_current_A':ev.median_current,'event_Ah':ev.ah,'window_Ah':q,
                        'reference_end':re.end,'reference_cycle':re.segment,'reference_temp_C':re.median_temp,
                        'reference_current_A':re.median_current,'reference_window_Ah':rq,
                        'ratio':q/rq,'true_capacity_ratio_for_diagnosis_only':row.target_Ah/row.anchor_capacity_Ah})
            latest=sorted({x['event_end'] for x in recent})[-5:]
            chosen=[x for x in recent if x['event_end'] in latest]
            details.extend(chosen)
            summaries.append({'cell_id':cid,'stage':row.stage,'target_cycle':row.target_cycle,
                'error_pp':row.error_pp,'reference_keys':len(refs),'selected_events':len(latest),
                'selected_windows':len(chosen),'eligible_windows_rejected_temperature':outside,
                'max_selected_reference_cycle':max([x['reference_cycle'] for x in chosen],default=0),
                'earliest_reference_temp_C':min([x['reference_temp_C'] for x in chosen],default=np.nan),
                'latest_event_temp_C':max([x['event_temp_C'] for x in chosen],default=np.nan)})
        print(cid,'done',flush=True)
    out=TASK/'outputs/a_failure_review';out.mkdir(exist_ok=True)
    pd.DataFrame(details).to_csv(out/'selected_event_references.csv',index=False)
    pd.DataFrame(summaries).to_csv(out/'target_diagnostics.csv',index=False)
    print(pd.DataFrame(summaries).to_string(index=False))

if __name__=='__main__':main()
