"""E3/E4: entity-nested source models, equal-source-budget baselines and A tests."""
from __future__ import annotations
import itertools,json,sys,time,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
TASK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TASK/"src"));sys.path.insert(0,str(TASK/"scripts"))
from source_model import fit_source,predict
from baselines import fit_baseline,predict_baseline
from observation_a import build_features,OBS_COLUMNS
from reproduce_source import load_records


def metrics(frame):
    f=frame.copy();f["ae"]=(f.prediction_soh_pp-f.target_soh_pp).abs();f["err"]=f.prediction_soh_pp-f.target_soh_pp
    per=f.groupby("cell_id").ae.mean()
    late=f.loc[f.target_ordinal>=21]
    return {"macro_MAE_pp":float(per.mean()),"worst_cell_MAE_pp":float(per.max()),"max_error_pp":float(f.ae.max()),
            "macro_RMSE_pp":float(f.groupby("cell_id").err.apply(lambda a:np.sqrt(np.mean(a*a))).mean()),
            "late_macro_MAE_pp":float(late.groupby("cell_id").ae.mean().mean()),"bias_pp":float(f.err.mean()),"n_targets":len(f)}


def main():
    config=json.loads((TASK/"configs/experiment.json").read_text())
    panel=pd.read_csv(TASK/"outputs/panel_scoring.csv");features=pd.read_csv(TASK/"outputs/history_features.csv")
    records=load_records();by_id={r["cell_id"]:r for r in records};cells=sorted(by_id)
    for rec in records:
        p=panel.loc[panel.cell_id.eq(rec["cell_id"])].sort_values("target_ordinal")
        rec["anchor_soh"]=float(p.anchor_soh_pp.iloc[0]);rec["anchor_time_ns"]=pd.Timestamp(p.anchor_discharge_start.iloc[0]).value
        rec["target_age_days"]=features.loc[features.cell_id.eq(rec["cell_id"])].sort_values("target_ordinal").age_days.to_numpy()
    a=build_features(pd.read_csv(TASK/"artifacts/shallow_visibility.csv"),pd.read_csv(TASK/"artifacts/shallow_observations.csv"))
    a.to_csv(TASK/"outputs/a_observations.csv",index=False)
    a20=a.loc[a.budget_Ah.eq(20)].merge(panel[["cell_id","target_ordinal","target_soh_pp"]],on=["cell_id","target_ordinal"])
    stamp=hashlib.sha256(b"".join((TASK/"src"/name).read_bytes() for name in ["source_model.py","exposure.py","baselines.py"])).hexdigest()[:12]
    cache=TASK/"artifacts/model_cache";cache.mkdir(exist_ok=True)
    fit_count=0; selection=[];predictions=[];inner_rows=[]
    def model_for(ids,name):
        nonlocal fit_count
        key="__".join([x.replace("102Ah_","") for x in sorted(ids)])
        path=cache/f"{stamp}_{name}_{key}.json"
        if path.exists():return json.loads(path.read_text())
        t=time.monotonic();model=fit_source([by_id[x] for x in ids],name)
        model["fit_seconds"]=time.monotonic()-t;model["code_hash"]=stamp
        path.write_text(json.dumps(model,indent=2)+"\n");fit_count+=1
        print('fit',fit_count,'ntrain',len(ids),name,'seconds',round(model["fit_seconds"],2),flush=True)
        return model
    def b_predict(ids,held,name,xi0):
        r=by_id[held];model=model_for(ids,name)
        return np.asarray(predict(model,r["target_hist"],r["anchor_soh"],xi0,nominal_T=r["nominal_T"]))
    def base_predict(ids,held,name,alpha):
        r=by_id[held];model=fit_baseline([by_id[x] for x in ids],name,alpha)
        return predict_baseline(model,r["target_hist"].sum(axis=1),r["target_age_days"],r["anchor_soh"])
    def y_for(held):return panel.loc[panel.cell_id.eq(held)].sort_values("target_ordinal").target_soh_pp.to_numpy()
    def append(held,method,values,training,**extra):
        p=panel.loc[panel.cell_id.eq(held)].sort_values("target_ordinal")
        for row,value in zip(p.itertuples(index=False),values):
            predictions.append({"cell_id":held,"target_ordinal":int(row.target_ordinal),"target_soh_pp":float(row.target_soh_pp),
                                "prediction_soh_pp":float(value),"method":method,"training_cells":"|".join(training),**extra})
    bconfigs=list(itertools.product(config["b_configs"],config["xi0_candidates"]))
    baseconfigs=list(itertools.product(["linear","power","age","charge_age"],config["baseline_ridge_alpha"]))
    # Produce all entity-OOF predictions needed to select the source model.
    for held in cells:
        training=[c for c in cells if c!=held]
        choices=[]
        for name,xi0 in bconfigs:
            errs=[]
            for inner in training:
                fit=[c for c in training if c!=inner]
                values=b_predict(fit,inner,name,xi0);error=float(np.mean(abs(values-y_for(inner))));errs.append(error)
                for i,value in enumerate(values):inner_rows.append({"outer_held":held,"inner_held":inner,"config":name,"xi0":xi0,"target_ordinal":i+1,"prediction_soh_pp":float(value),"training_cells":"|".join(fit)})
            score=float(np.mean(errs));choices.append((score,name,xi0))
            append(held,f"{name}_xi{xi0:g}",b_predict(training,held,name,xi0),training)
        score,name,xi0=min(choices)
        append(held,"B_new_nested",b_predict(training,held,name,xi0),training,selected_config=name,selected_xi0=xi0)
        selection.append({"heldout":held,"family":"B","config":name,"xi0":xi0,"inner_MAE_pp":score,"training_cells":training})
        bs=[]
        for bname,alpha in baseconfigs:
            scores=[float(np.mean(abs(base_predict([c for c in training if c!=inner],inner,bname,alpha)-y_for(inner)))) for inner in training]
            bs.append((float(np.mean(scores)),bname,alpha))
        bscore,bname,alpha=min(bs)
        append(held,"simple_nested",base_predict(training,held,bname,alpha),training,selected_config=bname,selected_alpha=alpha)
        selection.append({"heldout":held,"family":"simple","config":bname,"alpha":alpha,"inner_MAE_pp":bscore,"training_cells":training})
        append(held,"CK0_hold",np.repeat(by_id[held]["anchor_soh"],30),[])
        # A_raw-like relative window estimate is deliberately an uncalibrated
        # diagnostic; it never supplies a fake absolute z_A to fusion.
        obs=a20.loc[a20.cell_id.eq(held)].sort_values("target_ordinal")
        signal=obs[OBS_COLUMNS].median(axis=1).fillna(0).to_numpy()
        append(held,"A_shallow_ratio",by_id[held]["anchor_soh"]*np.exp(signal),[])
        pd.DataFrame(predictions).to_csv(TASK/"outputs/predictions_E3.partial.csv",index=False)
        (TASK/"outputs/inner_selection.partial.json").write_text(json.dumps(selection,indent=2)+"\n")
        print('outer completed',held,'B',name,xi0,'inner_MAE',score,'baseline',bname,alpha,flush=True)
    pred=pd.DataFrame(predictions);pred.to_csv(TASK/"outputs/predictions_E3.csv",index=False)
    pd.DataFrame(inner_rows).to_csv(TASK/"outputs/inner_B_predictions.csv",index=False)
    (TASK/"outputs/inner_selection.json").write_text(json.dumps(selection,indent=2)+"\n")
    report=pd.DataFrame([{"method":name,**metrics(f)} for name,f in pred.groupby("method")]).sort_values("macro_MAE_pp")
    report.to_csv(TASK/"outputs/metrics_E3.csv",index=False)
    per=pred.assign(ae=lambda f:abs(f.prediction_soh_pp-f.target_soh_pp)).groupby(["method","cell_id"]).ae.mean().reset_index()
    per.to_csv(TASK/"outputs/per_cell_E3.csv",index=False)
    b=report.set_index("method").loc["B_new_nested"];simple=report.set_index("method").loc["simple_nested"]
    relative=1-b.macro_MAE_pp/simple.macro_MAE_pp
    tails={k:float(b[k]-simple[k]) for k in ["worst_cell_MAE_pp","max_error_pp","late_macro_MAE_pp"]}
    passed=relative>=.1 and all(v<=.5 for v in tails.values())
    gate={"B_E3_performance_pass":bool(passed),"relative_improvement_over_simple":float(relative),"tail_degradation_pp":tails,
          "hard_checks":"pending_E6","E5_numeric_fusion_allowed_by_E3":bool(passed),"official_capacity_performance":"not_testable"}
    (TASK/"outputs/E3_gate.json").write_text(json.dumps(gate,indent=2)+"\n")
    # A trend evidence at each shallow budget; evaluate legitimate ratios vs
    # true change only in the scoring process, separately by physical cell.
    trends=[]
    for budget in (15,20,30):
        obs=a.loc[a.budget_Ah.eq(budget)].merge(panel.drop(columns="anchor_soh_pp"),on=["cell_id","target_ordinal"])
        signal=obs[OBS_COLUMNS].median(axis=1)
        for cell,f in obs.assign(signal=signal).groupby("cell_id"):
            valid=f.signal.notna();truth=np.log(f.target_soh_pp/f.anchor_soh_pp)
            rho=spearmanr(f.loc[valid,"signal"],truth[valid]).statistic if valid.sum()>2 else np.nan
            trends.append({"budget_Ah":budget,"cell_id":cell,"targets_with_window_observation":int(valid.sum()),"coverage_fraction":float(valid.mean()),
                           "trend_spearman":float(rho) if np.isfinite(rho) else None,
                           "direction_accuracy":float(((f.loc[valid,"signal"]<0)==(truth[valid]<0)).mean()) if valid.any() else None})
    pd.DataFrame(trends).to_csv(TASK/"outputs/A_trend_validation.csv",index=False)
    # F_monitor is exactly B, with discrepancies only in diagnosis.
    monitor=pred.loc[pred.method.eq("B_new_nested")].copy();monitor["method"]="F_monitor"
    monitor.to_csv(TASK/"outputs/monitor_predictions.csv",index=False)
    print(report.to_string(index=False),flush=True);print(json.dumps(gate),flush=True)

if __name__=="__main__":main()
