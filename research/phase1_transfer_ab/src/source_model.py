"""Stage-1 master curve refitted on the same observable charging coordinate."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import least_squares
from legacy.collapse import fit_master, fit_tau, master, hinge_n
from legacy.model_template import MyModel
from exposure import GRID_T, GRID_C, rate_weights

PRIOR = json.loads((Path(__file__).parent/"legacy/pretrained.json").read_text())


def loss(shape, xi):
    _, a, p, b, w = np.asarray(shape, float)
    x = np.clip(np.asarray(xi, float),0.,None)
    return a*np.power(x,p)+b*hinge_n(x,w)


class CachedCell:
    def __init__(self, rec):
        self.cell_id=rec["cell_id"]; self.temperature_degC=rec["nominal_T"]
        self.c_rate=rec["nominal_C"]
        self.soh=pd.DataFrame({"cycle_number":rec["cycles"],"soh_percent":rec["soh"]})
        self._temp=rec["raw_mean_T"] if rec["raw_temp_coverage"]>=.2 else np.nan
    def time_series(self): return pd.DataFrame({"temperature_C":[self._temp]*8})


def fit_source(records, config):
    noT=config=="charge_noT"
    nominal=config=="nominal_sat"
    noKnee=config.endswith("noKnee")
    mode="fixed" if config=="dynamic_fixed" else ("extrap" if config=="dynamic_extrap" else "sat")
    curves=[]; info=[]
    for rec in records:
        y=np.asarray(rec["soh"],float); hist=np.asarray(rec["hist"],float)
        ok=np.isfinite(y)&(y>=50)&(y<=106)&(hist.sum(axis=1)>0)
        ys=pd.Series(y).rolling(21,center=True,min_periods=3).median().to_numpy()
        ok &= np.isfinite(ys)
        ix=np.flatnonzero(ok)
        ix=ix[np.unique(np.rint(np.linspace(0,len(ix)-1,min(len(ix),512))).astype(int))]
        x=hist[ix].sum(axis=1); yy=ys[ix]
        curves.append((x,yy))
        total=hist[-1]
        T=float((total*GRID_T).sum()/max(total.sum(),1e-12))
        C=float((total*GRID_C).sum()/max(total.sum(),1e-12))
        info.append((rec,hist[ix],yy,T,C))
    s0_meas=float(np.mean([np.nanmedian(np.asarray(r["soh"])[(np.asarray(r["cycles"])>=2)&(np.asarray(r["cycles"])<=10)]) for r in records]))
    prior={"a":PRIOR["d3_prior"]["a_rel"]*s0_meas/100.,"p":PRIOR["d3_prior"]["p"]}
    n_deep=sum(float(y.min())<=85 for _,y in curves)
    fix={"b":0.,"w":1.} if noKnee or n_deep<2 else {}
    shape, taus, rmse, _, _=fit_master(curves,s0_init=s0_meas+1,s0_bounds=(98.,108.),fix=fix,
        soft_prior=prior,prior_strength=3.)
    head_taus=[]
    for (x,y), joint in zip(curves,taus):
        m=y>=90
        tau=fit_tau(shape,x[m],y[m]) if m.sum()>=8 else fit_tau(shape,x,y)
        head_taus.append(float(tau) if np.isfinite(tau) else float(joint))
    if noT:
        par={"lnA":float(np.mean(np.log(head_taus))),"Ea":0.,"gamma":0.}
    else:
        Ts=np.array([r[0]["nominal_T"] if nominal else r[3] for r in info])+273.15
        Cs=np.array([r[0]["nominal_C"] if nominal else r[4] for r in info])
        if mode=="fixed": Cs[:]=.5
        model=MyModel()
        par=model._arrhenius(Ts,Cs,np.log(head_taus),37300.)
    weights=rate_weights(par,mode)
    if not noT and not nominal:
        # Temperature/cycle-rate link is frozen from training-only head scales;
        # refine shared curve against integrated exposure, without joint scale
        # non-identifiability between lnA and shape amplitudes.
        free=[0,1,2] if fix else [0,1,2,3,4]
        init=shape[free]
        lo=np.array([98.,.01,.1,0.,.01])[free]
        hi=np.array([108.,80.,2.5,400.,3.])[free]
        xis=[h@weights for _,h,_,_,_ in info]
        def unpack(th):
            s=shape.copy();s[free]=th
            if fix:s[3]=0.;s[4]=1.
            return s
        def residual(th):
            s=unpack(th)
            pieces=[(s[0]-loss(s,x)-item[2])/np.sqrt(len(x)) for x,item in zip(xis,info)]
            pieces.append(np.sqrt(3.)*np.array([(s[1]-prior["a"])/prior["a"],(s[2]-prior["p"])/prior["p"]]))
            return np.concatenate(pieces)
        opt=least_squares(residual,init,bounds=(lo,hi),max_nfev=3000)
        shape=unpack(opt.x)
    return {"config":config,"shape":shape.tolist(),"parameters":par,"rate_mode":mode,
            "n_deep":int(n_deep),"head_taus":head_taus,"source_coordinate_fit_rmse_pp":rmse,
            "training_cells":[r["cell_id"] for r in records],
            "source_temperature_axis":"charge-exposure sensor bins" if not nominal and not noT else ("nominal" if nominal else "none"),
            "source_rate_definition":"charge-weighted stable-run median, binned"}


def predict(model,hist,anchor_soh,xi0=0.,temperature_shift=0.,nominal_T=None):
    h=np.asarray(hist,float)
    if model["config"]=="nominal_sat" and nominal_T is not None:
        cols=GRID_C
        c=cols if model["rate_mode"]=="extrap" else np.maximum(cols,.5)
        par=model["parameters"]
        weights=np.exp(-np.clip(par["lnA"]+par["Ea"]/(8.314*(nominal_T+273.15))+par["gamma"]*np.log(c),np.log(20),np.log(1e6)))
    else: weights=rate_weights(model["parameters"],model["rate_mode"],temperature_shift)
    xi=h@weights
    out=np.asarray(anchor_soh)-loss(model["shape"],xi0+xi)+loss(model["shape"],xi0)
    return out
