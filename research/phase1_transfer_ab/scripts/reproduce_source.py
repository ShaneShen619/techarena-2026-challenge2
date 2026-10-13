"""Refit the exact designated legacy model, without changing its repository."""
from __future__ import annotations
import json,sys,time
from pathlib import Path
import numpy as np
import pandas as pd
TASK=Path(__file__).resolve().parents[1];ROOT=TASK.parents[1]
sys.path.insert(0,str(TASK/"src"))
from source_model import CachedCell
from legacy.model_template import MyModel
from legacy.collapse import cross


def load_records():
    records=json.loads((TASK/"artifacts/data_metadata.json").read_text())
    for rec in records:
        data=np.load(TASK/"artifacts"/f'data_{rec["cell_id"]}.npz')
        rec.update({k:data[k] for k in data.files})
    return records


def main():
    records=load_records();cells=[CachedCell(r) for r in records]
    panel=pd.read_csv(TASK/"outputs/panel_scoring.csv")
    old_path=ROOT/"research/phase2_temperature_improvement/runs/M3_B_age_sixfold_v2/predictions.csv"
    old=pd.read_csv(old_path)
    rows=[];details=[];folds=[]
    for held in cells:
        train=[c for c in cells if c.cell_id!=held.cell_id]
        t=time.monotonic();model=MyModel();model.fit(train)
        curve=model.predict_soh(held.temperature_degC,held.c_rate)
        target=panel.loc[panel.cell_id.eq(held.cell_id)].merge(old[["cell_id","target_ordinal","visible_last_charge_cycle","input_end"]],on=["cell_id","target_ordinal"],validate="one_to_one")
        anchor=int(target.anchor_cycle.iloc[0]);shift=float(target.anchor_soh_pp.iloc[0])-curve[anchor-1]
        for row in target.itertuples(index=False):
            assert pd.Timestamp(row.input_end)<pd.Timestamp(row.target_discharge_start)
            pred=float(curve[int(row.visible_last_charge_cycle)-1]+shift)
            rows.append({"cell_id":held.cell_id,"target_ordinal":int(row.target_ordinal),"prediction_soh_pp":pred,
                         "input_end":row.input_end,"age_coordinate":"inherited frozen v2 visible_last_charge_cycle; prediction refitted"})
        x,y,_=model._clean(held);pred=curve[x.astype(int)-1]
        mono=np.minimum.accumulate(y)
        item={"cell_id":held.cell_id,"trajectory_rmse_unconstrained_truth_pp":float(np.sqrt(np.mean((pred-y)**2))),
              "trajectory_rmse_monotone_truth_pp":float(np.sqrt(np.mean((pred-mono)**2)))}
        for threshold in (90,80,70):
            true=cross(x,mono,threshold);estimate=cross(np.arange(1,len(curve)+1),curve,threshold)
            item[f"n{threshold}_true"]=float(true) if np.isfinite(true) else None
            item[f"n{threshold}_estimate"]=float(estimate) if np.isfinite(estimate) else None
            item[f"n{threshold}_MAPE_pct"]=float(abs(estimate-true)/true*100) if np.isfinite(true) and np.isfinite(estimate) else None
        details.append(item)
        folds.append({"heldout":held.cell_id,"training_cells":[c.cell_id for c in train],"shape":model.shape_.tolist(),
                      "parameters":model.ax_,"thermal_theta":None if model.dT_theta_ is None else model.dT_theta_.tolist(),
                      "fit_seconds":time.monotonic()-t})
        print('E1',held.cell_id,'fit_seconds',round(time.monotonic()-t,2),flush=True)
    prediction=pd.DataFrame(rows);prediction.to_csv(TASK/"outputs/legacy_reproduced_predictions.csv",index=False)
    joined=prediction.merge(old[["cell_id","target_ordinal","prediction_soh_pp"]],on=["cell_id","target_ordinal"],suffixes=("_new","_old"))
    scoring=prediction.merge(panel,on=["cell_id","target_ordinal"])
    ae=(scoring.prediction_soh_pp-scoring.target_soh_pp).abs()
    summary={"B_age_180_macro_MAE_pp":float(ae.groupby(scoring.cell_id).mean().mean()),
             "B_age_max_error_pp":float(ae.max()),"max_prediction_difference_from_history_pp":float(abs(joined.prediction_soh_pp_new-joined.prediction_soh_pp_old).max()),
             "sixfold_trajectory_RMSE_mean_cell_pp":float(np.mean([d["trajectory_rmse_unconstrained_truth_pp"] for d in details])),
             "sixfold_monotone_truth_RMSE_mean_cell_pp":float(np.mean([d["trajectory_rmse_monotone_truth_pp"] for d in details])),
             "n70_MAPE_pct":float(np.mean([d["n70_MAPE_pct"] for d in details if d["n70_MAPE_pct"] is not None])),
             "history_RMSE_aggregation_unknown":"both truth conventions reported; no retuning to 1.972",
             "v2_harness":"not run: accesses late_stretch attributes absent in designated source",
             "source_sample_validator":"see runs/source_smoke/validation_report.txt",
             "old_age_coordinates":"reused frozen input coordinates; numerical fit and predictions freshly regenerated"}
    (TASK/"outputs/legacy_reproduction.json").write_text(json.dumps({"summary":summary,"per_cell":details,"folds":folds},indent=2)+"\n")
    full=MyModel();full.fit(cells)
    (TASK/"artifacts/legacy_full_model.json").write_text(json.dumps({"shape":full.shape_.tolist(),"parameters":full.ax_,"thermal_theta":full.dT_theta_.tolist(),"training_cells":[c.cell_id for c in cells]},indent=2)+"\n")
    print(json.dumps(summary),flush=True)

if __name__=="__main__":main()
