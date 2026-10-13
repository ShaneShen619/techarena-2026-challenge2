"""Small entity-OOF residual mapper plus event-deduplicated bounded updates."""
from __future__ import annotations
import numpy as np


def fit_ridge(x,y,alpha):
    a=np.asarray(x,float);y=np.asarray(y,float)
    med=np.array([np.nanmedian(v) if np.isfinite(v).any() else 0. for v in a.T])
    a=np.where(np.isfinite(a),a,med)
    mu=a.mean(0);sd=a.std(0);sd=np.where(sd<1e-8,1.,sd)
    z=np.column_stack([np.ones(len(a)),np.clip((a-mu)/sd,-6,6)])
    penalty=np.diag(np.r_[1e-8,np.full(a.shape[1],alpha)])
    coef=np.linalg.solve(z.T@z+penalty,z.T@y)
    return {"median":med.tolist(),"mean":mu.tolist(),"scale":sd.tolist(),"coef":coef.tolist(),"alpha":float(alpha)}


def ridge_predict(model,x):
    a=np.asarray(x,float);a=np.where(np.isfinite(a),a,np.asarray(model["median"]))
    z=np.column_stack([np.ones(len(a)),np.clip((a-np.asarray(model["mean"]))/np.asarray(model["scale"]),-6,6)])
    return z@np.asarray(model["coef"])


def correction_sequence(prior,residual,quality,event_ends,K,L):
    prior=np.asarray(prior,float);values=[];logs=[];offset=0.;last=""
    for i,(b,r,q,event) in enumerate(zip(prior,residual,quality,event_ends)):
        accept=bool(q and event and event!=last)
        increment=float(K*np.clip(r-offset,-L,L)) if accept else 0.
        offset+=increment
        if accept:last=str(event)
        values.append(float(b+offset))
        logs.append({"target_ordinal":i+1,"accepted_new_observation":accept,"matched_event_end":str(event),
                     "innovation_pp":float(r-offset+increment),"increment_pp":increment,"offset_pp":offset,
                     "prior_soh_pp":float(b),"corrected_soh_pp":float(b+offset)})
    return np.asarray(values),logs
