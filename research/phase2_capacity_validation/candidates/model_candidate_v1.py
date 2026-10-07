"""Causal repair of the supplied partial-charge baseline; no hidden labels."""
import numpy as np
import pandas as pd

V_LO, V_FULL, I_END, MAX_BACK = 13.4, 13.95, 1.5, 6 * 360


def events(op):
    if op.empty:
        return pd.DataFrame(columns=['t_end', 'Q_partial_Ah', 'segment', 'max_gap_s', 'n_rows', 'start_current_A'])
    ts=op.timestamp.values.astype('datetime64[s]').astype('int64')
    I=op.current_A.to_numpy(float); U=op.pack_voltage_V.to_numpy(float); seg=op.segment.to_numpy()
    dt=np.diff(ts,prepend=ts[0]).astype(float); clean=dt.copy();clean[(clean>600)|(clean<0)]=0
    ah=np.maximum(I*clean/3600,0)
    hi=U>=V_FULL
    ends=np.where(hi&(I<I_END)&(np.r_[False,I[:-1]>=5]|np.r_[False,hi[:-1]]))[0]
    ends=ends[np.r_[True,np.diff(ends)>60]] if len(ends) else ends
    rows=[]
    for e in ends:
        j=e
        while j>0 and I[j]>-0.5 and U[j]>=V_LO and seg[j]==seg[e] and e-j<MAX_BACK:
            j-=1
        if e-j<30 or U[j]>V_LO+0.05: continue
        rows.append((op.timestamp.iloc[e],float(ah[j:e+1].sum()),int(seg[e]),float(dt[j:e+1].max()),int(e-j+1),float(I[j])))
    return pd.DataFrame(rows,columns=['t_end','Q_partial_Ah','segment','max_gap_s','n_rows','start_current_A'])


class ActiveModel:
    def __init__(self, gate='none'):
        self.gate=gate
        self.soh0=100.0
        self.last_q_ref=None

    def fit(self,dataset):
        ck=dataset.checkups_released.sort_values('date')
        self.soh0=float(ck.SOH_pct.iloc[0]) if len(ck) else 100.0

    def estimate_soh(self,dataset,at_date):
        self.last_q_ref=None
        if dataset.operation.empty:return self.soh0
        ev=events(dataset.operation)
        ev=ev[ev.t_end<=pd.Timestamp(at_date)]
        if ev.empty:return self.soh0
        first=ev[ev.segment==ev.segment.min()]
        if self.gate in ('range','combined'):
            anchor=float(first.Q_partial_Ah.median())
            first=first[(first.Q_partial_Ah>=0.5*anchor)&(first.Q_partial_Ah<=1.5*anchor)]
        if self.gate in ('gap','combined','start_gap'):first=first[first.max_gap_s<=60]
        if self.gate in ('start','start_gap'):first=first[first.start_current_A<=5]
        if first.empty:return self.soh0
        q_ref=float(first.Q_partial_Ah.median())
        self.last_q_ref=q_ref
        if self.gate in ('range','combined'):
            ev=ev[(ev.Q_partial_Ah>=0.5*q_ref)&(ev.Q_partial_Ah<=1.5*q_ref)]
        if self.gate in ('gap','combined','start_gap'):ev=ev[ev.max_gap_s<=60]
        if self.gate in ('start','start_gap'):ev=ev[ev.start_current_A<=5]
        if ev.empty:return self.soh0
        q=float(ev.tail(3).Q_partial_Ah.median())
        return float(np.clip(self.soh0*q/q_ref,0,120))
