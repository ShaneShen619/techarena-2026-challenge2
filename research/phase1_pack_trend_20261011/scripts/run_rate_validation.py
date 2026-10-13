"""Nested entity validation of A-driven rate versus metadata-driven rate."""
from __future__ import annotations
import hashlib,itertools,json,sys
from pathlib import Path
import numpy as np
import pandas as pd
TASK=Path(__file__).resolve().parents[1]; PREV=TASK.parent/"phase1_transfer_ab"
sys.path[:0]=[str(TASK/"src"),str(PREV/"src"),str(PREV/"scripts")]
from trend import summarize_trend,signal_columns,CONTROL,feedback,training_log_ratios
from source_model import fit_source,predict
from fusion import fit_ridge,ridge_predict
from reproduce_source import load_records
from run_nested_validation import metrics

def main():
    axis="events" if "--event-axis" in sys.argv else "days"
    result=TASK/"event_axis" if axis=="events" else TASK
    SIGNAL=signal_columns(axis)
    for name in ["outputs","artifacts"]:(result/name).mkdir(exist_ok=True,parents=True)
    protocol_hash=hashlib.sha256((TASK/"protocol.md").read_bytes()).hexdigest()
    panel=pd.read_csv(PREV/"outputs/panel_scoring.csv")
    hist=pd.read_csv(PREV/"outputs/history_features.csv")
    crops=pd.read_csv(PREV/"artifacts/shallow_observations.csv")
    views=pd.read_csv(PREV/"artifacts/shallow_visibility.csv")
    c20=crops.loc[crops.budget_Ah.eq(20)].sort_values(["cell_id","fragment_end"],kind="stable").copy()
    index=c20.set_index("event_id",verify_integrity=True)
    rows=[]
    for row in views.loc[views.history_mode.eq("persistent")&views.budget_Ah.eq(20)].itertuples(index=False):
        ids=json.loads(row.allowed_event_ids_json)
        f=pd.DataFrame([index.loc[x].to_dict() for x in ids]) if ids else crops.iloc[:0]
        if axis=="events" and ids:
            # Cache contains only the union of allowed crops, not every past
            # charge. Use registered PAST qualified-event counts, never ranks
            # among that subsample or source cycle counters.
            initial=json.loads(row.initial_event_ids_json); recent=json.loads(row.recent_event_ids_json)
            ranks={eid:i+1 for i,eid in enumerate(initial)}
            ranks.update({eid:int(row.candidate_event_count)-len(recent)+i+1 for i,eid in enumerate(recent)})
            assert set(ids)<=set(ranks)
            f["event_ordinal"]=[ranks[eid] for eid in ids]
        rows.append(dict(cell_id=row.cell_id,target_ordinal=row.target_ordinal,
                         **summarize_trend(f,row.target_discharge_start,axis)))
    features=pd.DataFrame(rows).merge(hist,on=["cell_id","target_ordinal"])
    features.to_csv(result/"outputs/A_trend_features.csv",index=False)
    records=load_records(); by_id={r["cell_id"]:r for r in records};cells=sorted(by_id)
    for r in records:r["anchor_soh"]=float(panel.loc[panel.cell_id.eq(r["cell_id"]),"anchor_soh_pp"].iloc[0])
    config=json.loads((PREV/"configs/experiment.json").read_text())
    stamp=hashlib.sha256(b"".join((PREV/"src"/n).read_bytes() for n in ["source_model.py","exposure.py","baselines.py"])).hexdigest()[:12]
    model_cache={}; pred_cache={}; choice_cache={}; label_cache={}; mapper_cache={}; audit=[]; permutation_audit=[]
    def truth(c):return panel.loc[panel.cell_id.eq(c)].sort_values("target_ordinal").target_soh_pp.to_numpy()
    def frame(ids):return pd.concat([features.loc[features.cell_id.eq(c)].sort_values("target_ordinal") for c in ids],ignore_index=True)
    def model(ids,name):
        key=(tuple(sorted(ids)),name)
        if key not in model_cache:
            filename=f"{stamp}_{name}_{'__'.join(x.replace('102Ah_','') for x in sorted(ids))}.json"
            p=PREV/"artifacts/model_cache"/filename
            if p.exists():m=json.loads(p.read_text())
            else:
                m=fit_source([by_id[x] for x in ids],name)
                (result/"artifacts"/filename).write_text(json.dumps(m,indent=2)+"\n")
            assert set(m["training_cells"])==set(ids)
            model_cache[key]=m
        return model_cache[key]
    def bp(ids,held,name,xi0):
        key=(tuple(sorted(ids)),held,name,xi0)
        if key not in pred_cache:
            r=by_id[held];pred_cache[key]=predict(model(ids,name),r["target_hist"],r["anchor_soh"],xi0,nominal_T=r["nominal_T"])
        return pred_cache[key]
    def choose(ids):
        key=tuple(sorted(ids))
        if key not in choice_cache:
            scores=[(float(np.mean([np.mean(abs(bp([c for c in ids if c!=v],v,n,x)-truth(v))) for v in ids])),n,x)
                    for n,x in itertools.product(config["b_configs"],config["xi0_candidates"])]
            choice_cache[key]=min(scores)[1:]
        return choice_cache[key]
    def selected(ids,held):return bp(ids,held,*choose(ids))
    def labels(ids,mode):
        key=(tuple(ids),mode)
        if key not in label_cache:
            ys=[]
            for held in ids:
                train=[c for c in ids if c!=held]
                prior=selected(train,held)
                ys.append(training_log_ratios(prior,truth(held),by_id[held]["anchor_soh"],mode))
                audit.append(dict(outer_pool=list(ids),label_entity=held,B_fit_and_selection_cells=train,
                                  config=choose(train)[0],xi0=choose(train)[1],mode=mode))
            label_cache[key]=np.concatenate(ys)
        return label_cache[key]
    def mapper(ids,family,mode,alpha,permuted=False):
        key=(tuple(ids),family,mode,alpha,permuted)
        if key not in mapper_cache:
            f=frame(ids);cols=CONTROL+(SIGNAL if family=="signal" else [])
            x=f[cols].to_numpy(float); moved=0
            if permuted:
                rng=np.random.default_rng(20261011)
                for entity in ids:
                    groups={}
                    for i in np.flatnonzero(f.cell_id.eq(entity).to_numpy()):
                        temp,amps=x[i,2:4]
                        if not np.isfinite([temp,amps]).all() or amps<=0:continue
                        k=(int(np.floor(temp/5)),int(np.floor(np.log(amps)/np.log(1.2))),tuple(np.isfinite(x[i,len(CONTROL):])))
                        groups.setdefault(k,[]).append(i)
                    for g in groups.values():
                        p=rng.permutation(g);moved+=int(np.sum(np.asarray(g)!=p));x[g,len(CONTROL):]=x[p,len(CONTROL):]
                permutation_audit.append(dict(training_cells=list(ids),rows=len(f),rows_with_permuted_position=moved))
            y=labels(ids,mode);valid=np.isfinite(y)
            if not valid.any():raise ValueError("No eligible rate labels")
            m=fit_ridge(x[valid],y[valid],alpha)
            m.update(columns=cols,training_cells=list(ids),mode=mode,family=family,training_rows=int(valid.sum()),trend_axis=axis)
            mapper_cache[key]=m
        return mapper_cache[key]
    def apply(m,ids,held,gain):
        f=frame([held]); b=selected(ids,held)
        return feedback(b,by_id[held]["anchor_soh"],ridge_predict(m,f[m["columns"]].to_numpy(float)),
                        f.eligible.to_numpy(bool),f.event_end.fillna("").tolist(),gain,m["mode"])
    predictions=[];selections=[];logs=[];fold_models=[]
    def append(cell,method,values):
        for i,v in enumerate(values):predictions.append(dict(cell_id=cell,target_ordinal=i+1,method=method,
                                     prediction_soh_pp=float(v),target_soh_pp=float(truth(cell)[i])))
    for held in cells:
        train=[c for c in cells if c!=held]
        append(held,"B_new_nested",selected(train,held))
        for mode,family in itertools.product(["forward","damage"],["metadata","signal"]):
            scores=[]
            for alpha,gain in itertools.product([10.,100.],[0.,.1,.3]):
                errs=[]
                for val in train:
                    ids=[c for c in train if c!=val]
                    m=mapper(ids,family,mode,alpha);v,_=apply(m,ids,val,gain)
                    errs.append(float(np.mean(abs(v-truth(val)))))
                scores.append((float(np.mean(errs)),alpha,gain))
            score,alpha,gain=min(scores)
            m=mapper(train,family,mode,alpha);values,log=apply(m,train,held,gain)
            method=f"{mode}_{family}";append(held,method,values)
            selections.append(dict(outer_held=held,method=method,inner_MAE_pp=score,alpha=alpha,gain=gain,B_config=choose(train)[0],B_xi0=choose(train)[1]))
            fold_models.append(dict(outer_held=held,gain=gain,**m))
            logs.extend([dict(cell_id=held,method=method,**r) for r in log])
            if family=="signal":
                pm=mapper(train,family,mode,alpha,True);v,_=apply(pm,train,held,gain)
                append(held,f"{mode}_permuted",v)
        print("completed outer",held,flush=True)
    pred=pd.DataFrame(predictions);pred.to_csv(result/"outputs/rate_predictions.csv",index=False)
    pd.DataFrame(logs).to_csv(result/"outputs/rate_updates.csv",index=False)
    pd.DataFrame(selections).to_csv(result/"outputs/rate_selections.csv",index=False)
    scored=pd.DataFrame([dict(method=n,**metrics(f)) for n,f in pred.groupby("method")]);scored.to_csv(result/"outputs/rate_metrics.csv",index=False)
    per=pred.assign(ae=lambda f:abs(f.prediction_soh_pp-f.target_soh_pp)).groupby(["method","cell_id"]).ae.mean().reset_index()
    per.to_csv(result/"outputs/rate_per_cell.csv",index=False)
    summary={};b=scored.set_index("method").loc["B_new_nested"]
    for mode in ["forward","damage"]:
        s=scored.set_index("method").loc[f"{mode}_signal"];meta=scored.set_index("method").loc[f"{mode}_metadata"]
        pb=per.loc[per.method.eq("B_new_nested")].set_index("cell_id").ae
        ps=per.loc[per.method.eq(f"{mode}_signal")].set_index("cell_id").ae
        pm=per.loc[per.method.eq(f"{mode}_metadata")].set_index("cell_id").ae
        tails={k:float(s[k]-b[k]) for k in ["worst_cell_MAE_pp","max_error_pp","late_macro_MAE_pp"]}
        imp=float(b.macro_MAE_pp-s.macro_MAE_pp);inc=float(meta.macro_MAE_pp-s.macro_MAE_pp)
        accepted=imp>=.1 and imp/b.macro_MAE_pp>=.05 and inc>=.1 and int((ps<=pb).sum())>=4 and int((ps<=pm).sum())>=4 and all(v<=.5 for v in tails.values())
        summary[mode]=dict(improvement_over_B_pp=imp,A_increment_over_metadata_pp=inc,
                           noninferior_cells_B=int((ps<=pb).sum()),noninferior_cells_metadata=int((ps<=pm).sum()),
                           tail_degradation_pp=tails,accepted=bool(accepted))
    summary.update(protocol_sha256=protocol_hash,trend_axis=axis,exploratory=axis=="events",primary_budget_Ah=20,decision_scope="frozen 30 past-only decision dates, not event-level deployment",
                   independent_blind_validation=False,official_capacity_validation="not_testable",eligible_fraction=float(features.eligible.mean()))
    (result/"outputs/rate_gate.json").write_text(json.dumps(summary,indent=2)+"\n")
    (result/"outputs/nested_audit.json").write_text(json.dumps(audit,indent=2)+"\n")
    (result/"outputs/permutation_audit.json").write_text(json.dumps(permutation_audit,indent=2)+"\n")
    (result/"artifacts/fold_rate_models.json").write_text(json.dumps(fold_models,indent=2)+"\n")
    # Frozen full-source research artifact. No official target capacity used.
    full=[]
    for mode,family in itertools.product(["forward","damage"],["metadata","signal"]):
        candidates=[]
        for alpha,gain in itertools.product([10.,100.],[0.,.1,.3]):
            errs=[]
            for held in cells:
                ids=[c for c in cells if c!=held];v,_=apply(mapper(ids,family,mode,alpha),ids,held,gain)
                errs.append(np.mean(abs(v-truth(held))))
            candidates.append((float(np.mean(errs)),alpha,gain))
        _,alpha,gain=min(candidates);full.append(dict(gain=gain,**mapper(cells,family,mode,alpha)))
    (result/"artifacts/full_source_rate_models.json").write_text(json.dumps(full,indent=2)+"\n")
    print(scored.to_string(index=False),flush=True);print(json.dumps(summary),flush=True)

if __name__=="__main__":main()
