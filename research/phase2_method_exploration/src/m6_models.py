"""Low-dimensional workpoint RBF and causal Wiener residual filter for TU steps.

This is an explicitly simplified approximation to BattGP's additive spatial
RBF plus temporal Wiener idea, not the authors' exact GP implementation.
"""
from __future__ import annotations
import numpy as np

def features(frame):
    x=np.column_stack([frame.I_after_A.to_numpy(float)/70,
                       (frame.SOC_BMS_pct.to_numpy(float)-70)/20,
                       (frame.temperature_C.to_numpy(float)-25)/15,
                       frame.delta_I_A.to_numpy(float)/70])
    return np.clip(x,-4,4)

def centers_farthest(X,n=64,seed=20260928):
    rng=np.random.default_rng(seed)
    pool=X[rng.choice(len(X),min(10000,len(X)),replace=False)]
    center=[pool[np.argmin(np.sum((pool-np.median(pool,axis=0))**2,axis=1))]]
    dist=np.sum((pool-center[0])**2,axis=1)
    while len(center)<min(n,len(pool)):
        j=int(np.argmax(dist));center.append(pool[j]);dist=np.minimum(dist,np.sum((pool-pool[j])**2,axis=1))
    return np.array(center)

def rbf(X,C):
    distance=np.maximum(0,np.sum(X**2,axis=1)[:,None]+np.sum(C**2,axis=1)[None,:]-2*X@C.T)
    return np.exp(-.5*distance)

def ridge_fit(Phi,y,alpha=10):
    A=Phi.T@Phi+alpha*np.eye(Phi.shape[1]);A[0,0]-=alpha
    return np.linalg.solve(A,Phi.T@y),A

class WienerResidual:
    def __init__(self,measurement_std_mOhm,process_std_mOhm_per_sqrt_day=.03,
                 initial_std_mOhm=.5,max_abs_state_mOhm=3):
        self.measurement_var=max(.1,measurement_std_mOhm)**2
        self.process_var_per_day=process_std_mOhm_per_sqrt_day**2
        self.mean=0.;self.var=initial_std_mOhm**2;self.last_time=None
        self.max_abs_state=max_abs_state_mOhm

    def predict(self,time):
        if self.last_time is not None:
            days=max(0,(time-self.last_time).total_seconds()/86400)
            self.var+=self.process_var_per_day*days
        self.last_time=time
        return self.mean,self.var

    def update(self,observation_minus_spatial,innovation_clip_std=3):
        innovation=observation_minus_spatial-self.mean
        sigma=np.sqrt(self.var+self.measurement_var)
        innovation=float(np.clip(innovation,-innovation_clip_std*sigma,innovation_clip_std*sigma))
        gain=self.var/(self.var+self.measurement_var)
        self.mean=float(np.clip(self.mean+gain*innovation,-self.max_abs_state,self.max_abs_state))
        self.var=(1-gain)*self.var

class AdaptiveWorkpointResidual:
    """Five-state causal Kalman residual: offset plus four local workpoint slopes."""
    def __init__(self,measurement_std_mOhm,initial_offset_std=.5,
                 initial_slope_std=.15,process_offset_std_per_sqrt_day=.03,
                 process_slope_std_per_sqrt_day=.005):
        self.mean=np.zeros(5)
        self.cov=np.diag([initial_offset_std**2]+[initial_slope_std**2]*4)
        self.measurement_var=max(.1,measurement_std_mOhm)**2
        self.process=np.diag([process_offset_std_per_sqrt_day**2]+[process_slope_std_per_sqrt_day**2]*4)
        self.last_time=None

    def predict(self,time,x):
        if self.last_time is not None:
            days=max(0,(time-self.last_time).total_seconds()/86400)
            self.cov+=self.process*days
        self.last_time=time
        h=np.r_[1.,np.asarray(x,float)]
        return float(h@self.mean),float(h@self.cov@h),h

    def update(self,residual,h,innovation_clip_std=3):
        forecast=float(h@self.mean)
        variance=float(h@self.cov@h+self.measurement_var)
        innovation=float(np.clip(residual-forecast,-innovation_clip_std*np.sqrt(variance),
                                 innovation_clip_std*np.sqrt(variance)))
        gain=self.cov@h/variance
        self.mean+=gain*innovation
        self.mean=np.clip(self.mean,[-3,-1,-1,-1,-1],[3,1,1,1,1])
        self.cov-=np.outer(gain,h@self.cov)
        self.cov=(self.cov+self.cov.T)/2
