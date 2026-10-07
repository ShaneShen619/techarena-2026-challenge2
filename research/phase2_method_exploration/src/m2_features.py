"""Feature construction from the only model-facing D1 visibility adapter."""
from __future__ import annotations
import numpy as np
import pandas as pd
from visibility import D1Visibility

AGE=['age_days','age_log1p','history_count','last_gap_days','prefix_prequalified_charge_count']
WINDOWS=list(range(9))

def frame_for_condition(budget_Ah:int,history_mode:str,visibility_path=None,crop_path=None)->pd.DataFrame:
    boundary=D1Visibility(visibility_path,crop_path) if visibility_path is not None and crop_path is not None else D1Visibility()
    audit=boundary._v.loc[(boundary._v.budget_Ah==budget_Ah)&
                           (boundary._v.history_mode==history_mode),
                           ['cell_id','target_ordinal']]
    rows=[]
    for item in audit.itertuples(index=False):
        view=boundary.get(item.cell_id,int(item.target_ordinal),budget_Ah,history_mode)
        fragments=view['fragments']
        current=fragments.iloc[-1] if len(fragments) else None
        cutoff=pd.Timestamp(view['target_cutoff'])
        age=max(0.,(cutoff-pd.Timestamp(view['anchor_time'])).total_seconds()/86400)
        lastgap=(cutoff-pd.Timestamp(current.fragment_end)).total_seconds()/86400 if current is not None else np.nan
        row={'cell_id':item.cell_id,'target_ordinal':int(item.target_ordinal),
             'anchor_pp':100*view['anchor_capacity_Ah']/102,
             'age_days':age,'age_log1p':np.log1p(age),
             'history_count':len(fragments),'last_gap_days':lastgap,
             'prefix_prequalified_charge_count':int(view['prefix_prequalified_charge_count']),
             'current_A':float(current.current_A) if current is not None else np.nan,
             'current_temp_C':float(current.temperature_C) if current is not None else np.nan,
             'v_start_V':float(current.v_start_V) if current is not None else np.nan,
             'v_end_V':float(current.v_end_V) if current is not None else np.nan,
             'observed_span_Ah':float(current.observed_span_Ah) if current is not None else np.nan,
             'history_temp_C':float(fragments.temperature_C.median()) if len(fragments) else np.nan}
        initial=fragments.iloc[:10] if history_mode=='persistent' else fragments.iloc[:0]
        for wi in WINDOWS:
            key=f'w{wi:02d}_Ah'
            value=float(current[key]) if current is not None and pd.notna(current[key]) else np.nan
            available=int(np.isfinite(value))
            reference=float(initial[key].median()) if len(initial) and initial[key].notna().any() else np.nan
            ratio=value/reference if np.isfinite(value) and np.isfinite(reference) and reference>0 else np.nan
            row[f'w{wi:02d}_Ah']=value
            row[f'w{wi:02d}_mask']=available
            row[f'w{wi:02d}_ref_Ah']=reference
            row[f'w{wi:02d}_ratio']=ratio
            row[f'w{wi:02d}_diff_Ah']=value-reference if np.isfinite(value) and np.isfinite(reference) else np.nan
        rows.append(row)
    frame=pd.DataFrame(rows)
    assert len(frame)==180 and not frame[['cell_id','target_ordinal']].duplicated().any()
    assert not {'target_soh_pp','target_capacity_Ah','full_cc_Ah_audit_only'} & set(frame)
    return frame
