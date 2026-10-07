"""4S finite-rate voltage model with group-endpoint capacity and explicit flags.

The CK0 curves already contain the 5.1A reference polarization. `delta_R`
therefore means an additional change relative to CK0, not total ohmic R.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.signal import savgol_filter

Q0=100.41
I_DISCHARGE_A=5.1
PACK_CUTOFF_V=11.2

@dataclass(frozen=True)
class PackState:
    capacity_Ah: np.ndarray
    initial_SOC: np.ndarray
    delta_R_ohm: np.ndarray

    def __post_init__(self):
        assert np.shape(self.capacity_Ah)==(4,)
        assert np.shape(self.initial_SOC)==(4,)
        assert np.shape(self.delta_R_ohm)==(4,)
        assert np.all(np.asarray(self.capacity_Ah)>0)
        assert np.all((np.asarray(self.initial_SOC)>=0)&(np.asarray(self.initial_SOC)<=1))

class CK0Pack:
    def __init__(self,reference:pd.DataFrame):
        q=reference.discharged_Ah.to_numpy(float)
        self.axis=np.arange(0,Q0+.001,.01)
        if self.axis[-1]<Q0:self.axis=np.r_[self.axis,Q0]
        cells=[]
        for c in range(1,5):
            original=reference[f'cell{c}_V'].to_numpy(float)
            raw=np.interp(self.axis,q,original)
            smooth=savgol_filter(raw,1001,3)
            u=self.axis/Q0
            corrected=smooth+(original[0]-smooth[0])*(1-u)+(original[-1]-smooth[-1])*u
            # Battery discharge terminal should not rise as discharged Ah
            # increases. Keep measured endpoints after monotone regularization.
            corrected=np.minimum.accumulate(corrected)
            corrected[-1]=original[-1]
            cells.append(corrected)
        self.curves=np.array(cells)
        self.start=np.array([a[0] for a in cells]);self.end=np.array([a[-1] for a in cells])
        self.tail_slope=(self.curves[:,-1]-self.curves[:,-101])/(self.axis[-1]-self.axis[-101])
        self.head_slope=(self.curves[:,100]-self.curves[:,0])/(self.axis[100]-self.axis[0])

    def cell_voltage(self,discharged_Ah,state:PackState,*,truth_shape_mV=None,truth_dynamic_R=False):
        q=np.asarray(discharged_Ah,float)
        Q=np.asarray(state.capacity_Ah,float);z=np.asarray(state.initial_SOC,float)
        equiv=Q0*(1-z+q[...,None]/Q)
        v=np.stack([np.interp(equiv[...,i],self.axis,self.curves[i]) for i in range(4)],axis=-1)
        v=np.where(equiv<0,self.start+self.head_slope*equiv,v)
        v=np.where(equiv>Q0,self.end+self.tail_slope*(equiv-Q0),v)
        R=np.asarray(state.delta_R_ohm,float)
        if truth_dynamic_R:R=R*(1+.4*np.clip(equiv/Q0,0,1.5)**2)
        v=v-I_DISCHARGE_A*R
        if truth_shape_mV is not None:
            amp=np.asarray(truth_shape_mV,float)/1000
            v=v+amp*np.clip(equiv/Q0,0,1.5)**4
        return v

    def group_voltage(self,discharged_Ah,state,**kwargs):
        return np.sum(self.cell_voltage(discharged_Ah,state,**kwargs),axis=-1)

    def cutoff(self,state,**kwargs):
        f=lambda ah:float(self.group_voltage(ah,state,**kwargs)-PACK_CUTOFF_V)
        if f(0)<=0:capacity=0.
        else:
            assert f(125)<0,'Group cutoff absent within 125Ah; scenario outside model domain'
            capacity=float(brentq(f,0,125,xtol=1e-9))
        v=np.asarray(self.cell_voltage(capacity,state,**kwargs),float)
        return {'group_capacity_Ah':capacity,'cutoff_cell_V':v,
                'lowest_voltage_cell':int(np.argmin(v)+1),
                'below_2p5V_at_group_cutoff':bool(np.min(v)<2.5),
                'cutoff_voltage_sum_V':float(v.sum())}

    def stepped_cutoff(self,state,step_s,**kwargs):
        dq=I_DISCHARGE_A*step_s/3600
        q=0.;prev=float(self.group_voltage(0,state,**kwargs))
        if prev<=PACK_CUTOFF_V:return 0.
        while q<125:
            nextq=q+dq;nextv=float(self.group_voltage(nextq,state,**kwargs))
            if nextv<=PACK_CUTOFF_V:
                fraction=(prev-PACK_CUTOFF_V)/(prev-nextv)
                return q+fraction*dq
            q=nextq;prev=nextv
        raise ValueError('Group cutoff absent')

def uniform_mean_state(state:PackState):
    return PackState(np.full(4,np.mean(state.capacity_Ah)),
                     np.full(4,np.mean(state.initial_SOC)),
                     np.full(4,np.mean(state.delta_R_ohm)))

def minimum_cell_usable_Ah(state:PackState):
    return float(np.min(state.capacity_Ah*state.initial_SOC))
