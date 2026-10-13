"""Training-budget-matched anchored age/charge regression baselines."""
import numpy as np


def design(n,days,name):
    n=np.clip(np.asarray(n,float),0,None);days=np.clip(np.asarray(days,float),0,None)
    if name=="linear":return n[:,None]
    if name=="power":return np.column_stack([np.sqrt(n),n])
    if name=="age":return np.column_stack([np.sqrt(days),days])
    if name=="charge_age":return np.column_stack([np.sqrt(n),n,np.sqrt(days),days])
    raise ValueError(name)


def fit_baseline(records,name,alpha):
    X=[];y=[]
    for rec in records:
        n=np.maximum(rec["hist"].sum(axis=1)-rec["anchor_hist"].sum(),0.)
        days=(rec["label_time_ns"]-rec["anchor_time_ns"])/86400e9
        raw=np.asarray(rec["soh"],float)
        ok=np.isfinite(raw)&(raw>=50)&(raw<=106)&(days>0)&(n>0)
        ix=np.flatnonzero(ok);ix=ix[np.unique(np.rint(np.linspace(0,len(ix)-1,min(len(ix),512))).astype(int))]
        X.append(design(n[ix],days[ix],name));y.append(raw[ix]-rec["anchor_soh"])
    a=np.vstack(X); target=np.concatenate(y)
    scale=np.sqrt(np.mean(a*a,axis=0));scale=np.maximum(scale,1e-12)
    a=a/scale
    coef=np.linalg.solve(a.T@a+alpha*np.eye(a.shape[1]),a.T@target)
    return {"name":name,"alpha":alpha,"scale":scale.tolist(),"coef":coef.tolist(),"training_cells":[r["cell_id"] for r in records]}


def predict_baseline(model,n,days,anchor):
    return anchor+design(n,days,model["name"])/np.array(model["scale"])@np.array(model["coef"])
