"""Vectorized pack quantities with explicit electrochemical-domain rejection.

CCCV roots solve the registered 14 V/5.1 A endpoint without a negative-R floor.
Positive total R is required for a physical constant-voltage taper. Literature
OCP tables are monotonic, so bisection returns the first threshold crossing.
"""
import numpy as np

def stoich(cells,q):
    a=np.asarray(cells,float)
    q=np.asarray(q,float)
    tn=a[:,:,3]+q[:,None]/a[:,:,0]
    tp=(a[:,:,2]-a[:,:,3]*a[:,:,0])/a[:,:,1]-q[:,None]/a[:,:,1]
    return tn,tp

def valid_start(cells):
    tn,tp=stoich(cells,np.zeros(len(cells)))
    return np.all(np.isfinite(np.r_[tn,tp]) & (np.r_[tn,tp]>=0) & (np.r_[tn,tp]<=1),axis=1).reshape(2,-1).all(axis=0)

def voltage(cells,q,ocp):
    tn,tp=stoich(cells,q)
    return ocp.Up(tp)-ocp.Un(tn)

def charge_end(cells,ocp):
    a=np.asarray(cells,float)
    tn,tp=stoich(a,np.zeros(len(a)))
    upper=np.min(np.minimum((1-tn)*a[:,:,0],tp*a[:,:,1]),axis=1)
    good=valid_start(a)&(a[:,:,4].sum(axis=1)>0)&(upper>=0)
    def pack(q,current):
        return voltage(a,q,ocp).sum(axis=1)+a[:,:,4].sum(axis=1)*current+a[:,:,5].sum(axis=1)
    start=pack(np.zeros(len(a)),5.1)
    terminal=pack(upper,5.1)
    good&=(start<=14)&(terminal>=14)
    lo=np.zeros(len(a));hi=np.maximum(upper,0)
    for _ in range(45):
        mid=(lo+hi)/2
        low=pack(mid,5.1)<14
        lo=np.where(low,mid,lo);hi=np.where(low,hi,mid)
    end=(lo+hi)/2
    tn,tp=stoich(a,end)
    good&=np.all((tn>=0)&(tn<=1)&(tp>=0)&(tp<=1),axis=1)
    return np.where(good,end,np.nan)

def c20_root(cells,end,etas,ocp,c_pack=-.003):
    tn,tp=stoich(cells,np.nan_to_num(end))
    limit=np.min(np.minimum(tn*cells[:,:,0],(1-tp)*cells[:,:,1]),axis=1)
    good=np.isfinite(end)&(limit>=0)
    def pack(d):
        return (voltage(cells,np.nan_to_num(end)-d,ocp)-np.asarray(etas)[None,:]).sum(axis=1)+c_pack
    good&=(pack(np.zeros(len(cells)))>=11.2)&(pack(limit)<=11.2)
    lo=np.zeros(len(cells));hi=np.maximum(limit,0)
    for _ in range(45):
        mid=(lo+hi)/2
        above=pack(mid)>11.2
        lo=np.where(above,mid,lo);hi=np.where(above,hi,mid)
    root=(lo+hi)/2
    atroot=voltage(cells,np.nan_to_num(end)-root,ocp)-np.asarray(etas)[None,:]
    limiting=np.argmin(atroot,axis=1)+1
    return np.where(good,root,np.nan),np.where(good,limiting,0)

def program_depth(cells,end,ocp):
    depth=np.arange(0.,56.0001,.05)
    q=np.nan_to_num(end)[:,None]-depth[None,:]
    tn=cells[:,None,:,3]+q[:,:,None]/cells[:,None,:,0]
    tp=(cells[:,None,:,2]-cells[:,None,:,3]*cells[:,None,:,0])/cells[:,None,:,1]-q[:,:,None]/cells[:,None,:,1]
    volts=ocp.Up(tp)-ocp.Un(tn)-cells[:,None,:,4]*10.782-cells[:,None,:,5]
    valid=(tn>=0)&(tn<=1)&(tp>=0)&(tp<=1)
    upper=(depth>=15)&(depth<=25);lower=(depth>=42)&(depth<=50)
    usable=np.all(valid[:,upper|lower,:],axis=1)&np.isfinite(end)[:,None]
    threshold=(np.median(volts[:,upper,:],axis=1)+np.median(volts[:,lower,:],axis=1))/2
    crossing=(depth[None,:,None]>20)&(volts<threshold[:,None,:])&valid
    exists=np.any(crossing,axis=1)&usable
    first=np.argmax(crossing,axis=1)
    percell=np.where(exists,depth[first],np.nan)
    mean=percell.mean(axis=1)
    return mean,percell

def quantities(cells,ocp,etas=None):
    a=np.asarray(cells,float)
    assert a.ndim==3 and a.shape[1:]==(4,6)
    assert np.all(np.diff(ocp.up)<=1e-12) and np.all(np.diff(ocp.un)<=1e-12)
    end=charge_end(a,ocp)
    depth,percell=program_depth(a,end,ocp)
    result={'Q_fc':end,'D_prog':depth,'steps':percell}
    if etas is not None:
        capacity,limiting=c20_root(a,end,etas,ocp)
        result.update(Q_C20=capacity,limiting=limiting)
    return result

def restart_health(cells,reference,ocp):
    """Common reference start OCV and common reference R/h for health-only beta."""
    a=np.asarray(cells,float).copy()
    ref=np.asarray(reference,float)
    target=voltage(ref[None,:,:],np.zeros(1),ocp)[0]
    lo=np.maximum(0.,(a[:,:,2]-a[:,:,1])/a[:,:,0])
    hi=np.minimum(.6,a[:,:,2]/a[:,:,0])
    def f(tn):
        tp=(a[:,:,2]-tn*a[:,:,0])/a[:,:,1]
        return ocp.Up(tp)-ocp.Un(tn)-target[None,:]
    good=np.isfinite(a).all(axis=(1,2))&np.all((hi>=lo)&(f(lo)<=0)&(f(hi)>=0),axis=1)
    for _ in range(45):
        mid=(lo+hi)/2
        low=f(mid)<0
        lo=np.where(low,mid,lo);hi=np.where(low,hi,mid)
    a[:,:,3]=(lo+hi)/2
    a[:,:,4:]=ref[None,:,4:]
    a[~good]=np.nan
    return a

def individual_limits(cells,end,etas,ocp):
    """Per-cell 2.8-V crossing and stoichiometry end; neither replaces pack cutoff."""
    a=np.asarray(cells,float)[None,:,:]
    tn,tp=stoich(a,np.array([end]))
    limits=np.minimum(tn[0]*a[0,:,0],(1-tp[0])*a[0,:,1])
    roots=[]
    for c in range(4):
        if not np.isfinite(limits[c]) or limits[c]<0:roots.append(np.nan);continue
        qn,qp,li,t0,R,h=a[0,c]
        def v(d):return float(ocp.ocv(end-d,(qn,qp,li,t0))-etas[c])
        if v(0)<2.8 or v(limits[c])>2.8:roots.append(np.nan);continue
        lo,hi=0.,float(limits[c])
        for _ in range(45):
            mid=(lo+hi)/2
            if v(mid)>2.8:lo=mid
            else:hi=mid
        roots.append((lo+hi)/2)
    return np.asarray(roots),limits
