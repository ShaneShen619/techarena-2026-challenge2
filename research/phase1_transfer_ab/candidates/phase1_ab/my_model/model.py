"""Official-interface research candidate: frozen source prior + A monitoring."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .exposure import intervals,histograms_at,histogram,GRID_T,GRID_C,rate_weights
from .observation_a import summarize

WINDOWS=[(3.35,3.39),(3.38,3.42),(3.41,3.45),(3.44,3.48),(3.35,3.42),(3.38,3.45),(3.41,3.48),(3.35,3.45),(3.38,3.48)]


def _loss(shape,xi):
    _,a,p,b,w=shape
    x=np.clip(np.asarray(xi,float),0,None)
    hinge=lambda z:.5*((z-1)+np.sqrt((z-1)**2+w*w)-w)
    return a*x**p+b*(hinge(x)-hinge(0.))


def prior_value(model,hist,anchor,xi0):
    x=np.asarray(hist)@rate_weights(model["parameters"],model["rate_mode"])
    return np.asarray(anchor)-_loss(model["shape"],xi0+x)+_loss(model["shape"],xi0)


def shallow_observations(frame,budget=20):
    """First cell-voltage endpoint visible within current prefix, even if open.

    No complete-event depth, later temperature, or full event end is read.
    Ratios are monitoring-only until independent residual evidence passes.
    """
    if frame.empty:return pd.DataFrame()
    f=frame.sort_values("timestamp",kind="stable").reset_index(drop=True)
    times=pd.to_datetime(f.timestamp).astype("int64").to_numpy()/1e9
    current=f.current_A.to_numpy(float)
    seg=f.segment.to_numpy() if "segment" in f else np.zeros(len(f),int)
    dt=np.diff(times,prepend=times[0]);good=np.isfinite(current)&(current>=5)
    boundary=(dt<=0)|(dt>60)|(seg!=np.r_[seg[0],seg[:-1]])
    starts=np.flatnonzero(good&(boundary|~np.r_[False,good[:-1]]))
    stops=np.flatnonzero(good&((~np.r_[good[1:],False])|np.r_[boundary[1:],True]))
    rows=[]
    for a,b in zip(starts,stops):
        if b-a+1<10:continue
        for column in [c for c in ("cell1_V","cell2_V","cell3_V","cell4_V") if c in f]:
            v=f[column].to_numpy(float)[a:b+1]
            crossing=np.flatnonzero((v[:-1]<3.50)&(v[1:]>=3.50))
            if not len(crossing):continue
            stop=int(crossing[0]+1);cc=current[a:a+stop+1]
            if stop+1<10 or np.std(cc)/max(np.mean(cc),1e-8)>.08:continue
            ts=times[a:a+stop+1];q=np.cumsum(np.r_[0.,np.diff(ts)*cc[1:]/3600.])
            if q[-1]<budget:continue
            mask=q>=q[-1]-budget;vs=v[:stop+1][mask];qs=q[mask];qs-=qs[0];crop_ts=ts[mask]
            if len(qs)<3:continue
            temp=f.temp_mean_C.to_numpy(float)[a:a+stop+1][mask] if "temp_mean_C" in f else np.full(len(qs),np.nan)
            rec={"cell":column,"charge_run_id":f"{seg[a]}:{pd.Timestamp(times[a],unit='s').isoformat()}",
                 "fragment_start":pd.Timestamp(crop_ts[0],unit="s").isoformat(),
                 "fragment_end":pd.Timestamp(crop_ts[-1],unit="s").isoformat(),
                 "temperature_C":float(np.nanmedian(temp)) if np.isfinite(temp).any() else np.nan,"current_A":float(np.median(cc[mask]))}
            for j,(lo,hi) in enumerate(WINDOWS):
                # Match the verified three-point median inside the observed crop.
                vv=pd.Series(vs).rolling(3,center=True,min_periods=1).median().to_numpy()
                vals=[];begin=0
                for threshold in (lo,hi):
                    ix=np.flatnonzero((vv[begin:-1]<threshold)&(vv[begin+1:]>=threshold))
                    if not len(ix):break
                    k=int(ix[0]+begin);frac=(threshold-vv[k])/(vv[k+1]-vv[k])
                    vals.append(qs[k]+frac*(qs[k+1]-qs[k]));begin=k+1
                rec[f"w{j:02d}_Ah"]=float(vals[1]-vals[0]) if len(vals)==2 and vals[1]>vals[0] else np.nan
            rows.append(rec)
    return pd.DataFrame(rows)


class MyModel:
    def __init__(self,artifact_path=None):
        if artifact_path is None:artifact_path=Path(__file__).parent/"source_prior.json"
        self.artifact=json.loads(Path(artifact_path).read_text())
        self.q0=100.41;self.anchor_date=pd.Timestamp("2025-01-14");self.last_diagnostics={}
    def fit(self,dataset):
        ck=dataset.checkups_released.sort_values("date").iloc[0]
        self.q0=float(ck.capacity_Ah);self.anchor_date=pd.Timestamp(ck.date)
        # Deliberately do not touch the full campaign operation or its counters.
    def estimate_soh(self,dataset,at_date):
        cutoff=pd.Timestamp(at_date);anchor=100*self.q0/102.
        op=dataset.operation
        if op.empty or "timestamp" not in op or cutoff<=self.anchor_date:
            self.last_diagnostics={"status":"CK0_anchor","raw_soh_pp":anchor,"A_matched_events":0,"charge_EFC":0.}
            return anchor
        f=op.loc[pd.to_datetime(op.timestamp).le(cutoff)&pd.to_datetime(op.timestamp).ge(self.anchor_date)].copy()
        if f.empty:
            self.last_diagnostics={"status":"no_observed_history","raw_soh_pp":anchor,"A_matched_events":0,"charge_EFC":0.}
            return anchor
        f=f.sort_values("timestamp",kind="stable").reset_index(drop=True)
        ledger,diag=intervals(f)
        model=self.artifact["model"];xi0=self.artifact["xi0"]
        raw=float(prior_value(model,histogram(ledger),anchor,xi0))
        # Evaluate deterministic checkpoints from visible segment tails. Hold
        # state is rebuilt each call, never inherited from query order.
        points=[pd.Timestamp(x) for x in f.groupby("segment").timestamp.max()] if "segment" in f else []
        points=sorted(set(points+[cutoff]));hist=histograms_at(ledger,[p+pd.Timedelta(nanoseconds=1) for p in points])
        ts=pd.to_datetime(f.timestamp).astype("int64").to_numpy();dt=np.diff(ts,prepend=ts[0])/1e9
        seg=f.segment.to_numpy() if "segment" in f else np.zeros(len(f))
        valid=(dt>0)&(dt<=60)&(seg==np.r_[seg[0],seg[:-1]])
        observed=np.cumsum(np.where(valid,dt,0.))
        amps=f.current_A.to_numpy(float);current_max=np.maximum.accumulate(np.where(np.isfinite(amps),np.maximum(amps,0),0))
        temp=f.temp_mean_C.to_numpy(float) if "temp_mean_C" in f else np.repeat(25.,len(f))
        temp_max=np.maximum.accumulate(np.where(np.isfinite(temp),temp,25.))
        trusted=anchor;status="prior";scenarios=[];last_missing=0.;last_upper=0.;last_span=0.
        for p,h in zip(points,hist):
            idx=int(np.searchsorted(ts,p.value,side="right")-1)
            if idx<0:continue
            missing=max(0.,(p-self.anchor_date).total_seconds()-observed[idx])
            extraN=missing*current_max[idx]/(3600*102)
            upper=h.copy();bin_index=int(np.clip(round(temp_max[idx]),0,80))*8+int(np.argmin(abs(np.array([.01,.025,.05,.1,.2,.5,1,2])-current_max[idx]/102)))
            upper[bin_index]+=extraN
            estimate=float(prior_value(model,h,anchor,xi0));lower=float(prior_value(model,upper,anchor,xi0))
            span=abs(estimate-lower)
            severe=not np.isfinite(estimate) or not 50<=estimate<=110 or span>5.
            if not severe:trusted=estimate;status="prior"
            else:status="hold_due_to_exposure_uncertainty"
            scenarios.append({"date":p.isoformat(),"observed_prior_soh_pp":estimate,"empirical_missing_all_charge_soh_pp":lower,
                              "missing_hours":missing/3600.,"extra_charge_EFC":extraN,"span_pp":span,"severe":bool(severe)})
            last_missing=missing;last_upper=extraN;last_span=span
        a=shallow_observations(f)
        observations=[]
        if len(a):
            for cell,part in a.groupby("cell"):
                s=summarize(part)
                values=[s[f'logratio_{j:02d}'] for j in range(9) if np.isfinite(s[f'logratio_{j:02d}'])]
                signal=float(np.median(values)) if values else None
                observations.append({"cell":cell,**s,"median_log_window_ratio":signal,
                    "trend_status":"unavailable" if signal is None else ("disagrees_with_prior_decline" if signal>0 and trusted<anchor else "no_direction_conflict"),
                    "last_fragment_age_days":(cutoff-pd.Timestamp(s['last_event_end'])).total_seconds()/86400.,
                    "direction_agreement_is_accuracy_validation":False})
        matched=sum(z["matched_events"] for z in observations)
        positive_current=f.current_A[f.current_A>0.]
        self.last_diagnostics={**diag,"status":status,"raw_soh_pp":raw,"output_soh_pp":trusted,
                               "missing_hours":last_missing/3600.,"empirical_extra_EFC":last_upper,"scenario_span_pp":last_span,
                               "range_type":"empirical missing-exposure sensitivity; not calibrated confidence",
                               "low_rate_observed_fraction":float((positive_current/102<.5).mean()) if len(positive_current) else 0.,
                               "A_fragment_count":len(a),"A_matched_events":matched,"A_observations":observations,
                               "A_independent_charge_runs":int(a.charge_run_id.nunique()) if len(a) else 0,
                               "A_matched_events_count_scope":"sum of per-cell matched rows; correlated, not independent events",
                               "A_numeric_correction_enabled":False,"F_monitor_equals_B":True,
                               "counter_gap_fill_enabled":False,"scenarios":scenarios,
                               "source_training_cells":model["training_cells"],"input_max_time":pd.Timestamp(f.timestamp.max()).isoformat()}
        return float(trusted)
