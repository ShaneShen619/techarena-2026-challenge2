"""A-only shape observations from strictly registered shallow fragments."""
from __future__ import annotations
import json
import numpy as np
import pandas as pd

OBS_COLUMNS=[f"logratio_{i:02d}" for i in range(9)]


def summarize(fragments, event_ids=None):
    f=fragments.sort_values("fragment_end",kind="stable").reset_index(drop=True)
    features={key:np.nan for key in OBS_COLUMNS}
    features.update({"valid_windows":0,"matched_events":0,"ratio_spread":np.nan,
                     "current_temp_C":np.nan,"current_A":np.nan,"reference_depends_on_B":False})
    if f.empty:return features
    reference=f.head(10);recent=f.tail(5)
    ratios=[[] for _ in range(9)]; used=set()
    for index,row in recent.iterrows():
        candidates=reference.loc[(pd.to_datetime(reference.fragment_end)<pd.Timestamp(row.fragment_end))&
            ((reference.temperature_C-row.temperature_C).abs()<=5)&
            ((reference.current_A-row.current_A).abs()<=.2*reference.current_A.abs())]
        for j in range(9):
            values=candidates[f"w{j:02d}_Ah"].dropna()
            current=row[f"w{j:02d}_Ah"]
            if len(values) and np.isfinite(current) and current>0 and values.median()>0:
                ratios[j].append(float(np.log(current/values.median())))
                used.add(index)
    for j,values in enumerate(ratios):
        if values: features[OBS_COLUMNS[j]]=float(np.median(values))
    vals=np.array([features[x] for x in OBS_COLUMNS])
    features["valid_windows"]=int(np.isfinite(vals).sum())
    features["matched_events"]=len(used)
    features["ratio_spread"]=float(np.nanmax(vals)-np.nanmin(vals)) if np.isfinite(vals).any() else np.nan
    features["current_temp_C"]=float(recent.temperature_C.median())
    features["current_A"]=float(recent.current_A.median())
    features["last_event_end"]=str(f.fragment_end.iloc[-1])
    features["latest_matched_event_end"]=str(f.fragment_end.iloc[max(used)]) if used else ""
    return features


def build_features(views,crop):
    index=crop.set_index(["event_id","budget_Ah"],verify_integrity=True)
    output=[]
    for row in views.loc[views.history_mode.eq("persistent")].itertuples(index=False):
        ids=json.loads(row.allowed_event_ids_json)
        f=pd.DataFrame([index.loc[(eid,int(row.budget_Ah))].to_dict() for eid in ids]) if ids else crop.iloc[:0]
        if len(f):assert (pd.to_datetime(f.fragment_end)<pd.Timestamp(row.target_discharge_start)).all()
        features=summarize(f,ids)
        output.append({"cell_id":row.cell_id,"target_ordinal":int(row.target_ordinal),"budget_Ah":int(row.budget_Ah),
                       "allowed_event_count":len(ids),"anchor_soh_pp":float(row.anchor_capacity_Ah)*100/102.,**features})
    return pd.DataFrame(output)
