"""Nested residual generation includes B configuration selection in every fold."""
from __future__ import annotations
import itertools,json,hashlib,sys,time
from pathlib import Path
import numpy as np
import pandas as pd
TASK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TASK/"src"));sys.path.insert(0,str(TASK/"scripts"))
from source_model import fit_source,predict
from observation_a import OBS_COLUMNS
from fusion import fit_ridge,ridge_predict,correction_sequence
from reproduce_source import load_records
from run_nested_validation import metrics


def main():
    gate=json.loads((TASK/"outputs/E3_gate.json").read_text())
    if not gate["B_E3_performance_pass"]:
        (TASK/"outputs/E5_gate.json").write_text(json.dumps({"status":"skipped_per_plan_B_E3_failed"},indent=2)+"\n");return
    config=json.loads((TASK/"configs/experiment.json").read_text())
    panel=pd.read_csv(TASK/"outputs/panel_scoring.csv")
    obs=pd.read_csv(TASK/"outputs/a_observations.csv").fillna({"latest_matched_event_end":""})
    history=pd.read_csv(TASK/"outputs/history_features.csv")
    frames={b:obs.loc[obs.budget_Ah.eq(b)].merge(history,on=["cell_id","target_ordinal"]).merge(panel[["cell_id","target_ordinal","target_soh_pp"]],on=["cell_id","target_ordinal"]).sort_values(["cell_id","target_ordinal"]) for b in (15,20,30)}
    records=load_records();by_id={r["cell_id"]:r for r in records};cells=sorted(by_id)
    for r in records:r["anchor_soh"]=float(panel.loc[panel.cell_id.eq(r["cell_id"]),"anchor_soh_pp"].iloc[0])
    stamp=hashlib.sha256(b"".join((TASK/"src"/n).read_bytes() for n in ["source_model.py","exposure.py","baselines.py"])).hexdigest()[:12]
    cache=TASK/"artifacts/model_cache"
    selection_cache={};prediction_cache={};residual_cache={};fit_log=[]
    def fit(ids,name):
        key="__".join(x.replace("102Ah_","") for x in sorted(ids));path=cache/f"{stamp}_{name}_{key}.json"
        if path.exists():return json.loads(path.read_text())
        m=fit_source([by_id[x] for x in ids],name);m["code_hash"]=stamp
        path.write_text(json.dumps(m,indent=2)+"\n");print('E5 source fit',len(ids),name,flush=True);return m
    def bp(ids,held,name,xi0):
        key=(tuple(sorted(ids)),held,name,xi0)
        if key not in prediction_cache:
            r=by_id[held];prediction_cache[key]=predict(fit(ids,name),r["target_hist"],r["anchor_soh"],xi0,nominal_T=r["nominal_T"])
        return prediction_cache[key]
    def truth(cell):return panel.loc[panel.cell_id.eq(cell)].sort_values("target_ordinal").target_soh_pp.to_numpy()
    def choose(ids):
        key=tuple(sorted(ids))
        if key not in selection_cache:
            scores=[]
            for name,xi0 in itertools.product(config["b_configs"],config["xi0_candidates"]):
                scores.append((float(np.mean([np.mean(abs(bp([c for c in ids if c!=held],held,name,xi0)-truth(held))) for held in ids])),name,xi0))
            selection_cache[key]=min(scores)[1:]
        return selection_cache[key]
    def selected_prior(ids,held):
        name,xi0=choose(ids);return bp(ids,held,name,xi0)
    def oof_residual(ids):
        key=tuple(sorted(ids))
        if key not in residual_cache:
            residuals=[]
            for held in ids:
                train=[c for c in ids if c!=held]
                prior=selected_prior(train,held)
                residuals.extend(truth(held)-prior)
                fit_log.append({"residual_held":held,"source_fit_and_selection_cells":train,
                                "selected_config":choose(train)[0],"selected_xi0":choose(train)[1],"outer_pool":list(ids)})
            residual_cache[key]=np.asarray(residuals)
        return residual_cache[key]
    control=["age_days","charge_EFC","current_temp_C","current_A","valid_windows","matched_events"]
    columns={"signal":control+OBS_COLUMNS,"metadata":control}
    rows=[];updates=[];selections=[];models=[]
    def frame(ids,budget):
        f=frames[budget]
        return pd.concat([f.loc[f.cell_id.eq(c)].sort_values("target_ordinal") for c in ids],ignore_index=True)
    def mapper(ids,family,alpha,budget,permuted=False):
        f=frame(ids,budget);x=f[columns[family]].to_numpy(float)
        if permuted and family=="signal":
            rng=np.random.default_rng(20261010)
            for j in range(len(ids)):
                # Preserve cell, window missingness and current conditions.
                # 5C bins imply pairwise temperature difference <=5C;
                # log(1.2) current bins imply max/min current <=1.2.
                groups={}
                for i in range(j*30,(j+1)*30):
                    temp=x[i,2];amps=x[i,3]
                    if not np.isfinite(temp) or not np.isfinite(amps) or amps<=0:continue
                    key=(int(np.floor(temp/5.)),int(np.floor(np.log(amps)/np.log(1.2))),tuple(np.isfinite(x[i,len(control):])))
                    groups.setdefault(key,[]).append(i)
                for indices in groups.values():
                    x[indices,len(control):]=x[rng.permutation(indices),len(control):]
        m=fit_ridge(x,oof_residual(ids),alpha)
        m.update({"columns":columns[family],"training_cells":ids,"budget_Ah":budget,"family":family})
        return m
    def apply(m,ids,held,K,L,budget):
        f=frame([held],budget);prior=selected_prior(ids,held)
        delta=ridge_predict(m,f[m["columns"]].to_numpy(float))
        values,log=correction_sequence(prior,delta,(f.valid_windows>0).to_numpy(),f.latest_matched_event_end.tolist(),K,L)
        return values,log
    candidates=list(itertools.product(config["fusion_ridge_alpha"],config["fusion_K"],config["fusion_L_pp"]))
    for outer in cells:
        train=[c for c in cells if c!=outer]
        for family in ("metadata","signal"):
            scores=[]
            for alpha,K,L in candidates:
                errs=[]
                for val in train:
                    ids=[c for c in train if c!=val]
                    m=mapper(ids,family,alpha,20)
                    values,_=apply(m,ids,val,K,L,20)
                    errs.append(float(np.mean(abs(values-truth(val)))))
                scores.append((float(np.mean(errs)),alpha,K,L))
            score,alpha,K,L=min(scores)
            selections.append({"outer_held":outer,"family":family,"inner_MAE_pp":score,"alpha":alpha,"K":K,"L_pp":L,"training_cells":train})
            for budget in (15,20,30):
                m=mapper(train,family,alpha,budget);models.append({"outer_held":outer,**m,"K":K,"L_pp":L})
                values,log=apply(m,train,outer,K,L,budget)
                for i,v in enumerate(values):rows.append({"cell_id":outer,"target_ordinal":i+1,"method":f"F_{family}","budget_Ah":budget,"prediction_soh_pp":float(v),"target_soh_pp":float(truth(outer)[i])})
                updates.extend([{**z,"cell_id":outer,"method":f"F_{family}","budget_Ah":budget} for z in log])
            # Diagnostic negative control: permute only training signal, keep
            # legal heldout features; never used as a deployed model.
            if family=="signal":
                m=mapper(train,family,alpha,20,permuted=True);values,_=apply(m,train,outer,K,L,20)
                for i,v in enumerate(values):rows.append({"cell_id":outer,"target_ordinal":i+1,"method":"F_train_signal_permuted","budget_Ah":20,"prediction_soh_pp":float(v),"target_soh_pp":float(truth(outer)[i])})
        pd.DataFrame(rows).to_csv(TASK/"outputs/fusion_predictions.partial.csv",index=False)
        print('fusion outer completed',outer,flush=True)
    pred=pd.DataFrame(rows);pred.to_csv(TASK/"outputs/fusion_predictions.csv",index=False)
    logs=pd.DataFrame(updates);logs.to_csv(TASK/"outputs/fusion_update_log.csv",index=False)
    (TASK/"outputs/fusion_selection.json").write_text(json.dumps(selections,indent=2)+"\n")
    (TASK/"outputs/residual_generation_audit.json").write_text(json.dumps(fit_log,indent=2)+"\n")
    (TASK/"artifacts/fusion_fold_models.json").write_text(json.dumps(models,indent=2)+"\n")
    scored=pd.DataFrame([{"method":method,"budget_Ah":budget,**metrics(f)} for (method,budget),f in pred.groupby(["method","budget_Ah"])])
    scored.to_csv(TASK/"outputs/metrics_fusion.csv",index=False)
    baseline=pd.read_csv(TASK/"outputs/predictions_E3.csv");B=baseline.loc[baseline.method.eq("B_new_nested")]
    bs=metrics(B);signal=pred.loc[pred.method.eq("F_signal")&pred.budget_Ah.eq(20)];ms=metrics(signal)
    meta=pred.loc[pred.method.eq("F_metadata")&pred.budget_Ah.eq(20)];meta_score=metrics(meta)
    simple=pd.read_csv(TASK/"outputs/per_cell_E3.csv");bp= simple.loc[simple.method.eq("B_new_nested")].set_index("cell_id").ae
    sp=signal.assign(ae=lambda f:abs(f.prediction_soh_pp-f.target_soh_pp)).groupby("cell_id").ae.mean()
    mp=meta.assign(ae=lambda f:abs(f.prediction_soh_pp-f.target_soh_pp)).groupby("cell_id").ae.mean()
    diff=ms["macro_MAE_pp"]-bs["macro_MAE_pp"];increment=meta_score["macro_MAE_pp"]-ms["macro_MAE_pp"]
    tail={k:ms[k]-bs[k] for k in ["worst_cell_MAE_pp","max_error_pp","late_macro_MAE_pp"]}
    coverage=logs.loc[logs.method.eq("F_signal")&logs.budget_Ah.eq(20)].groupby("cell_id").accepted_new_observation.mean()
    incremental=increment>=.1 and int((sp<=mp).sum())>=4
    accepted=diff<=-.1 and -diff/bs["macro_MAE_pp"]>=.05 and all(v<=.5 for v in tail.values()) and int((sp<=bp).sum())>=4 and incremental
    rng=np.random.default_rng(20261010);pair=(sp-bp).reindex(cells).to_numpy();draws=np.array([rng.choice(pair,len(pair),replace=True).mean() for _ in range(2000)])
    result={"B_macro_MAE_pp":bs["macro_MAE_pp"],"F_signal_macro_MAE_pp":ms["macro_MAE_pp"],"F_metadata_macro_MAE_pp":meta_score["macro_MAE_pp"],
            "fusion_absolute_improvement_pp":-diff,"fusion_relative_improvement":-diff/bs["macro_MAE_pp"],"independent_voltage_increment_pp":increment,
            "A_increment_gate_pass":bool(incremental),"fusion_performance_gate_pass":bool(accepted),"tail_degradation_pp":tail,
            "noninferior_cells_vs_B":int((sp<=bp).sum()),"noninferior_cells_vs_metadata":int((sp<=mp).sum()),
            "A_update_coverage":float(coverage.mean()),"minimum_cell_A_update_coverage":float(coverage.min()),
            "paired_macro_error_delta_bootstrap_95pct":[float(x) for x in np.quantile(draws,[.025,.975])],
            "final_research_strategy":"bounded correction candidate" if accepted else "B plus A monitoring; numeric correction rejected",
            "official_capacity_performance":"not_testable","corrector_runtime_scope":"frozen 30 decision dates; numeric deployment requires event-level replay equivalence"}
    (TASK/"outputs/E5_gate.json").write_text(json.dumps(result,indent=2)+"\n")
    print(scored.to_string(index=False),flush=True);print(json.dumps(result),flush=True)

if __name__=="__main__":main()
