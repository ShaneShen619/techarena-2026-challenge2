"""Strict extraction of a full 4S C/20 reference discharge."""
from dataclasses import dataclass
import numpy as np
import pandas as pd

@dataclass(frozen=True)
class RPTResult:
    status:str
    capacity_Ah:float|None
    cutoff_index:int|None
    reason:str
    max_gap_s:float|None

def extract_reference_capacity(frame, protocol):
    needed={'series_count':4,'nominal_Ah':102,'reference_current_A':5.1,
            'cutoff_pack_V':11.2,'full_charge_confirmed':True}
    for k,v in needed.items():
        if protocol.get(k)!=v:
            return RPTResult('rejected',None,None,f'{k}_unconfirmed_or_mismatch',None)
    required={'timestamp','current_A','voltage_V'}
    if not required.issubset(frame.columns):
        return RPTResult('rejected',None,None,'required_columns_missing',None)
    d=frame.copy();d['timestamp']=pd.to_datetime(d.timestamp,errors='coerce')
    if d[list(required)].isna().any().any() or len(d)<100:
        return RPTResult('rejected',None,None,'invalid_or_short_curve',None)
    if not d.timestamp.is_monotonic_increasing:
        return RPTResult('rejected',None,None,'time_reversal',None)
    d=d.drop_duplicates('timestamp',keep='last').reset_index(drop=True)
    t=d.timestamp.to_numpy().astype('datetime64[ms]').astype('int64')/1000
    dt=np.diff(t)
    if len(dt)==0 or np.any(dt<=0):return RPTResult('rejected',None,None,'nonpositive_interval',None)
    max_gap=float(max(dt))
    if max_gap>10:return RPTResult('rejected',None,None,'unrecorded_gap_over_10s',max_gap)
    v=d.voltage_V.to_numpy(float);i=d.current_A.to_numpy(float)
    hits=np.flatnonzero(v<=11.2)
    if len(hits)==0:return RPTResult('rejected',None,None,'cutoff_not_reached',max_gap)
    j=int(hits[0])
    if j<100:return RPTResult('rejected',None,None,'cutoff_too_early',max_gap)
    if abs(float(np.median(i[:j+1]))+5.1)>0.2 or np.any((i[:j+1]>-4.8)|(i[:j+1]<-5.4)):
        return RPTResult('rejected',None,None,'current_not_5p1A_CC',max_gap)
    # Trapezoid through first observed crossing, with linear interpolation when crossing lies between samples.
    if j>0 and v[j]<11.2<v[j-1]:
        fraction=(v[j-1]-11.2)/(v[j-1]-v[j])
        last_dt=dt[j-1]*fraction
        last_i=i[j-1]+(i[j]-i[j-1])*fraction
        q=-float(np.sum((i[:j-1]+i[1:j])*dt[:j-1]/7200))
        q-=float((i[j-1]+last_i)*last_dt/7200)
    else:
        q=-float(np.sum((i[:j]+i[1:j+1])*dt[:j]/7200))
    return RPTResult('accepted',q,j,'full_charge_flag_and_first_cutoff_verified',max_gap)
