"""CK0 loaded pack template and restricted capacity-axis experiment.

Official current is positive on charge; the reference discharge is negative.
The template already contains the 5.1 A loaded voltage drop. The sole
relative voltage term is a *change* from CK0, never another absolute IR drop.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd

@dataclass
class LoadedTemplate:
    q: np.ndarray
    pack_v: np.ndarray
    cell_v: np.ndarray
    @classmethod
    def from_csv(cls,path:Path):
        d=pd.read_csv(path)
        q=d.discharged_Ah.to_numpy(float)
        pack=d.voltage_V.to_numpy(float)
        cells=d[[f'cell{i}_V' for i in range(1,5)]].to_numpy(float)
        if np.nanmedian(d.current_A)>0: raise ValueError('expected negative reference discharge current')
        if np.any(np.diff(q)<0): raise ValueError('nonmonotonic Ah axis')
        keep=np.r_[np.diff(q)>0,True]
        return cls(q[keep],pack[keep],cells[keep])
    def voltage(self,reference_q_Ah,scale:float=1.,relative_pack_bias_V:float=0.):
        x=np.asarray(reference_q_Ah,dtype=float)/scale
        if np.any((x<self.q[0])|(x>self.q[-1])): raise ValueError('template extrapolation refused')
        return np.interp(x,self.q,self.pack_v)+relative_pack_bias_V
    def first_root(self,scale:float=1.,relative_pack_bias_V:float=0.,cutoff_V:float=11.2):
        vals=self.pack_v+relative_pack_bias_V-cutoff_V
        hits=np.flatnonzero((vals[:-1]>0)&(vals[1:]<=0))
        if len(hits)==0: return None
        j=int(hits[0]); a,b=vals[j],vals[j+1]
        return float(scale*(self.q[j]+a/(a-b)*(self.q[j+1]-self.q[j])))
    def window(self,start_Ah,span_Ah,scale=1.,offset_Ah=0.,bias_V=0.,n=101):
        x=np.linspace(0,span_Ah,n)
        return x,self.voltage(start_Ah+offset_Ah+x,scale,bias_V)

def fit_profile(t:LoadedTemplate,x,y,base_start_Ah,scales,offsets,biases_V,noise_sd_V):
    """Grid profile over capacity stretch and bounded start/bias nuisance.

    This estimates an *event* voltage-axis stretch. It does not identify the
    full-charge reference initial state or official Q_ref.
    """
    result=[]
    for c in scales:
        best=(float('inf'),None,None)
        for s in offsets:
            q=(base_start_Ah+s+x)/c
            if q.min()<t.q.min() or q.max()>t.q.max(): continue
            curve=np.interp(q,t.q,t.pack_v)
            for b in biases_V:
                mse=float(np.mean((y-(curve+b))**2))
                if mse<best[0]:best=(mse,float(s),float(b))
        result.append({'C_scale':float(c),'data_mse_V2':best[0],
                       'best_start_offset_Ah':best[1],'best_voltage_bias_V':best[2],
                       'data_rmse_mV':float(1000*np.sqrt(best[0])) if np.isfinite(best[0]) else np.nan,
                       'assumed_noise_sd_mV':float(1000*noise_sd_V)})
    return pd.DataFrame(result)

def local_svd(t:LoadedTemplate,x,base_start_Ah,scale=1.,offset=0.,bias=0.):
    p=np.array([scale,offset,bias],float)
    steps=np.array([1e-3,1e-3,1e-4]); cols=[]
    for i in range(3):
        plus=p.copy();minus=p.copy();plus[i]+=steps[i];minus[i]-=steps[i]
        def pred(z):return t.voltage(base_start_Ah+z[1]+x,z[0],z[2])
        cols.append((pred(plus)-pred(minus))/(2*steps[i]))
    j=np.column_stack(cols)
    return np.linalg.svd(j,compute_uv=False)
