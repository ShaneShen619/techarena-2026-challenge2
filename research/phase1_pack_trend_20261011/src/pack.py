"""Four series loaded curves; explicit first PACK voltage crossing."""
from __future__ import annotations
import numpy as np
from scipy.optimize import brentq

class PackPrototype:
    def __init__(self, reference, q0=100.41, current=5.1, cutoff=11.2, tail_Ah=2.):
        f=reference.sort_values("discharged_Ah", kind="stable").groupby("discharged_Ah", sort=True).last()
        q=f.index.to_numpy(float)
        v=f[[f"cell{i}_V" for i in range(1,5)]].to_numpy(float)
        pack=f.voltage_V.to_numpy(float)
        ix=np.flatnonzero(pack<=cutoff)
        if not len(ix) or ix[0]==0:
            raise ValueError("Reference does not bracket first pack cutoff")
        k=int(ix[0]); qr=float(np.interp(cutoff, pack[k-1:k+1][::-1], q[k-1:k+1][::-1]))
        self.q0=float(q0);self.current=float(current);self.cutoff=float(cutoff);self.tail=float(tail_Ah)
        self.axis_factor=qr/self.q0
        self.x=q/self.axis_factor;self.v=v;self.residual=pack-v.sum(axis=1)
        self.raw_cutoff_Ah=qr

    def _interp(self, x, y):
        x=np.asarray(x,float)
        if np.any(x<self.x[0]-1e-9) or np.any(x>self.x[-1]+self.tail+1e-9):
            raise ValueError("Template domain exceeded")
        z=np.interp(x,self.x,y)
        # Use a finite last-0.2-Ah slope, never unrestricted tail extension.
        a=max(self.x[0], self.x[-1]-.2)
        slope=(y[-1]-np.interp(a,self.x,y))/(self.x[-1]-a)
        return np.where(x>self.x[-1], y[-1]+slope*(x-self.x[-1]), z)

    def voltage(self, q, stretch, shift_Ah=None, delta_R=None):
        s=np.broadcast_to(np.asarray(stretch,float),(4,))
        d=np.zeros(4) if shift_Ah is None else np.asarray(shift_Ah,float)
        r=np.zeros(4) if delta_R is None else np.asarray(delta_R,float)
        if (s<=0).any() or len(d)!=4 or len(r)!=4:
            raise ValueError("Invalid pack state")
        q=np.asarray(q,float)
        cells=np.stack([self._interp(q/s[i]+d[i],self.v[:,i])-self.current*r[i] for i in range(4)],axis=-1)
        chain=self._interp(q/np.mean(s), self.residual)
        return cells.sum(axis=-1)+chain

    def capacity(self, stretch, shift_Ah=None, delta_R=None):
        s=np.broadcast_to(np.asarray(stretch,float),(4,))
        d=np.zeros(4) if shift_Ah is None else np.asarray(shift_Ah,float)
        # Positive shifts mean an initially less charged cell. Negative shift
        # would require unavailable higher-SOC data; reject, do not invent it.
        if (s<=0).any() or (d<0).any():
            raise ValueError("Nonpositive stretch or higher-SOC template unavailable")
        upper=min(float(np.min(s*(self.x[-1]+self.tail-d))),float(np.mean(s)*(self.x[-1]+self.tail)))
        if upper<=0:
            raise ValueError("No usable discharge domain")
        # Every piecewise-linear knot of each deformed cell AND chain residual.
        knots=np.concatenate([np.array([0.,upper]), *(s[i]*(self.x-d[i]) for i in range(4)), np.mean(s)*self.x])
        knots=np.unique(knots[(knots>=0)&(knots<=upper)])
        v=self.voltage(knots,s,d,delta_R)
        hits=np.flatnonzero(v<=self.cutoff)
        if not len(hits):
            raise ValueError("First cutoff outside bounded template domain")
        k=int(hits[0])
        if k==0:return 0.
        return float(brentq(lambda q:float(self.voltage(q,s,d,delta_R))-self.cutoff,knots[k-1],knots[k],xtol=1e-10))
