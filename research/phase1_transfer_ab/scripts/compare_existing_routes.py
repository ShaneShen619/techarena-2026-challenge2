"""Re-run older mechanisms on exactly the legal 20Ah observation budget."""
from __future__ import annotations
import json,sys,time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pandas as pd
TASK=Path(__file__).resolve().parents[1];ROOT=TASK.parents[1]
sys.path.insert(0,str(TASK/"src"));sys.path.insert(0,str(TASK/"scripts"))
from event_core import Event,partial_ah
from legacy_b.model_route_b import RouteB
from fusion import fit_ridge,ridge_predict
from observation_a import OBS_COLUMNS
from run_nested_validation import metrics


def main():
    panel=pd.read_csv(TASK/"outputs/panel_scoring.csv")
    crop=pd.read_csv(TASK/"artifacts/shallow_observations.csv");views=pd.read_csv(TASK/"artifacts/shallow_visibility.csv")
    views=views.loc[views.budget_Ah.eq(20)&views.history_mode.eq("persistent")]
    event_map={};ref_map={};rows=[];log=[]
    for cell in sorted(panel.cell_id.unique()):
        selected=crop.loc[crop.cell_id.eq(cell)&crop.budget_Ah.eq(20)]
        cycles={int(e.split("|")[1]) for e in selected.event_id};anchor_cycle=int(panel.loc[panel.cell_id.eq(cell),"anchor_cycle"].iloc[0]);cycles.add(anchor_cycle)
        pieces=[]
        for path in sorted((ROOT/"dataset original"/cell).glob("*.csv")):
            for chunk in pd.read_csv(path,usecols=["absolute_time","cycle_number","step_type","voltage_V","current_A","temperature_C","step_capacity_Ah"],chunksize=200000):
                f=chunk.loc[chunk.cycle_number.isin(cycles)]
                if len(f):pieces.append(f)
        raw=pd.concat(pieces,ignore_index=True);raw.absolute_time=pd.to_datetime(raw.absolute_time)
        groups={int(c):g.sort_values("absolute_time",kind="stable") for c,g in raw.groupby("cycle_number")}
        reference=groups[anchor_cycle].loc[groups[anchor_cycle].step_type.eq("cc_discharge")].copy()
        ref_map[cell]=pd.DataFrame({"discharged_Ah":reference.step_capacity_Ah.to_numpy(),"voltage_V":reference.voltage_V.to_numpy()})
        for r in selected.itertuples(index=False):
            g=groups[int(r.event_id.split("|")[1])]
            f=g.loc[g.step_type.ne("cc_discharge")&g.absolute_time.between(pd.Timestamp(r.fragment_start),pd.Timestamp(r.fragment_end))&g.current_A.ge(5)]
            times=f.absolute_time.astype("int64").to_numpy()/1e9;current=f.current_A.to_numpy(float)
            q=np.cumsum(np.r_[0.,np.diff(times)*current[1:]/3600.])
            event_map[r.event_id]=Event(pd.Timestamp(r.fragment_start),pd.Timestamp(r.fragment_end),int(r.event_id.split("|")[1]),
                 float(r.current_A),float(r.temperature_C),times[-1]-times[0],q[-1],times,q,f.voltage_V.to_numpy()[:,None],None,("voltage_V",))
        print('comparison raw prepared',cell,len(selected),flush=True)
    for r in views.itertuples(index=False):
        ids=json.loads(r.allowed_event_ids_json);events=[event_map[e] for e in ids]
        q0=float(r.anchor_capacity_Ah);cutoff=pd.Timestamp(r.target_discharge_start)
        b=RouteB(single_cell=True);b.fit(SimpleNamespace(bol_capacity_Ah=q0,reference_discharge=ref_map[r.cell_id]))
        q=q0;accepted=0;rejections={};firsttemp=None
        for ev in events:
            if firsttemp is None and np.isfinite(ev.median_temp):firsttemp=ev.median_temp
            if not np.isfinite(ev.median_temp) or firsttemp is None or abs(ev.median_temp-firsttemp)>5:reason="temperature_mismatch"
            else:
                result,reason=b._event_fit(ev,q)
                if reason=="accepted":q=.8*q+.2*result["q_fit"];accepted+=1
            if reason!="accepted":rejections[reason]=rejections.get(reason,0)+1
        rows.append({"cell_id":r.cell_id,"target_ordinal":int(r.target_ordinal),"method":"B_old_shallow_budget","prediction_soh_pp":100*q/102})
        log.append({"cell_id":r.cell_id,"target_ordinal":int(r.target_ordinal),"accepted":accepted,"rejections":json.dumps(rejections)})
        for name,windows,match in [("A_raw_shallow_budget",[(3.33,3.40),(3.36,3.43)],True),("causal_window_single_cell",[(3.35,3.4875)],False)]:
            refs={};ratios=[]
            for ev in events:
                pool=[]
                for j,(lo,hi) in enumerate(windows):
                    qwin=partial_ah(ev,0,lo,hi)
                    if qwin is None or qwin<1 or ev.ah<15:continue
                    tempbin=round(ev.median_temp/20) if match else 0;key=(j,tempbin)
                    if key not in refs:refs[key]=(qwin,ev.median_current);continue
                    ref,amps=refs[key]
                    if match and (abs(ev.median_temp-20*tempbin)>7 or abs(ev.median_current-amps)>.2*amps):continue
                    if (cutoff-ev.end).total_seconds()>30*86400:continue
                    pool.append(qwin/ref)
                if pool:ratios.append(float(np.median(pool)))
            ratio=float(np.median(ratios[-5:])) if ratios else 1.
            rows.append({"cell_id":r.cell_id,"target_ordinal":int(r.target_ordinal),"method":name,"prediction_soh_pp":100*q0/102*ratio})
    # A plain multi-window Ridge is a competitor, not an independent A
    # observation. It includes the same history age/charge and measured T.
    feature=pd.read_csv(TASK/"outputs/a_observations.csv").loc[lambda f:f.budget_Ah.eq(20)]
    history=pd.read_csv(TASK/"outputs/history_features.csv")
    data=feature.merge(history,on=["cell_id","target_ordinal"]).merge(panel[["cell_id","target_ordinal","target_soh_pp"]],on=["cell_id","target_ordinal"])
    columns=["age_days","charge_EFC","current_temp_C","current_A","valid_windows","matched_events"]+OBS_COLUMNS
    cells=sorted(data.cell_id.unique());selection=[]
    for held in cells:
        train=data.loc[data.cell_id.ne(held)];test=data.loc[data.cell_id.eq(held)].sort_values("target_ordinal")
        scores=[]
        for alpha in [1.,10.,100.]:
            errors=[]
            for val in train.cell_id.unique():
                a=train.loc[train.cell_id.ne(val)];v=train.loc[train.cell_id.eq(val)]
                m=fit_ridge(a[columns].to_numpy(),(a.target_soh_pp-a.anchor_soh_pp).to_numpy(),alpha)
                pred=v.anchor_soh_pp.to_numpy()+ridge_predict(m,v[columns].to_numpy())
                errors.append(np.mean(abs(pred-v.target_soh_pp.to_numpy())))
            scores.append((float(np.mean(errors)),alpha))
        score,alpha=min(scores);m=fit_ridge(train[columns].to_numpy(),(train.target_soh_pp-train.anchor_soh_pp).to_numpy(),alpha)
        values=test.anchor_soh_pp.to_numpy()+ridge_predict(m,test[columns].to_numpy())
        selection.append({"heldout":held,"alpha":alpha,"inner_MAE_pp":score})
        for r,v in zip(test.itertuples(index=False),values):rows.append({"cell_id":held,"target_ordinal":int(r.target_ordinal),"method":"shallow_multiwindow_ridge","prediction_soh_pp":float(v)})
    predictions=pd.DataFrame(rows).merge(panel[["cell_id","target_ordinal","target_soh_pp"]],on=["cell_id","target_ordinal"])
    predictions.to_csv(TASK/"outputs/existing_route_comparison.csv",index=False)
    pd.DataFrame(log).to_csv(TASK/"outputs/B_old_rejections.csv",index=False)
    scores=pd.DataFrame([{"method":name,**metrics(f)} for name,f in predictions.groupby("method")])
    scores.to_csv(TASK/"outputs/metrics_existing_routes.csv",index=False)
    (TASK/"outputs/existing_route_scope.json").write_text(json.dumps({"source_Ridge_version":"new strict shallow nine-window adaptation, not old24-window full-charge1.039pp model",
        "B_old_input":"same registered20Ah fragments; CK0 single-cell reference; _event_fit and gates unchanged; prefix endpoint known",
        "A_raw_input":"old windows/gates on registered20Ah fragments, never full-event future depth",
        "causal_window":"single-cell voltage window adapted from pack13.4/13.95V; same20Ah budget","Ridge_selection":selection},indent=2)+"\n")
    print(scores.to_string(index=False),flush=True)

if __name__=="__main__":main()
