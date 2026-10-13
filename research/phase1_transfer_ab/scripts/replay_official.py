"""Eight official prefix replays plus deletion/shuffle/extreme future checks."""
from __future__ import annotations
import json,sys,time,copy,pickle,hashlib
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pandas as pd
TASK=Path(__file__).resolve().parents[1];ROOT=TASK.parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(TASK/"src"))
from framework.data import load_dataset,Dataset
from age_prior import MyModel
from exposure import intervals,histogram

def json_safe(value):
    if isinstance(value,dict):return {k:json_safe(v) for k,v in value.items()}
    if isinstance(value,list):return [json_safe(v) for v in value]
    if isinstance(value,float) and not np.isfinite(value):return None
    return value

def main():
    full=load_dataset(ROOT/"data")
    artifact=TASK/"artifacts/source_prior.json"
    model=MyModel(artifact);model.fit(full)
    rows=[];checks=[];diags=[];stress=[]
    for row in full.eval_points.itertuples(index=False):
        cutoff=pd.Timestamp(row.date);prefix=full.operation.loc[full.operation.timestamp<=cutoff].copy()
        ds=Dataset(prefix,full.checkups_released,full.eval_points,full.reference_discharge,cutoff)
        t=time.monotonic();base=model.estimate_soh(ds,cutoff);diag=copy.deepcopy(model.last_diagnostics)
        rows.append({"checkup":row.checkup,"date":cutoff.isoformat(),"SOH_est":base,"raw_B_SOH_est":diag.get("raw_soh_pp",base),
                     "charge_EFC":diag.get("charge_EFC",0.),"status":diag["status"],"missing_hours":diag.get("missing_hours",0.),
                     "scenario_span_pp":diag.get("scenario_span_pp",0.),"A_fragments":diag.get("A_fragment_count",0),"A_matched_events":diag.get("A_matched_events",0),
                     "source_rate_OOD_fraction":diag.get("low_rate_observed_fraction",0.),"runtime_s":time.monotonic()-t})
        diags.append({"checkup":row.checkup,**diag})
        future=full.operation.loc[full.operation.timestamp>cutoff].copy()
        variants={"future_delete":prefix,"future_shuffle":pd.concat([prefix,future.sample(frac=1,random_state=20261010)],ignore_index=True)}
        extreme=future.copy()
        for col in ["current_A","temp_mean_C","charge_Ah_cum","discharge_Ah_cum","cell1_V","cell2_V","cell3_V","cell4_V","pack_voltage_V"]:
            if col in extreme:extreme[col]=1e9
        variants["future_extreme"]=pd.concat([prefix,extreme],ignore_index=True)
        for name,op in variants.items():
            test=MyModel(artifact);test.fit(Dataset(op,full.checkups_released,full.eval_points,full.reference_discharge,None))
            value=test.estimate_soh(Dataset(op,full.checkups_released,full.eval_points,full.reference_discharge,None),cutoff)
            ok=abs(value-base)<=1e-10
            checks.append({"checkup":row.checkup,"test":name,"base":base,"prediction":value,"pass":ok})
            assert ok,(row.checkup,name,base,value)
        prefix_fit=MyModel(artifact);prefix_fit.fit(ds)
        value=prefix_fit.estimate_soh(ds,cutoff)
        checks.append({"checkup":row.checkup,"test":"fit_full_vs_prefix","prediction":value,"base":base,"pass":abs(value-base)<=1e-10})
        assert abs(value-base)<=1e-10
        restored=pickle.loads(pickle.dumps(model));value=restored.estimate_soh(ds,cutoff)
        checks.append({"checkup":row.checkup,"test":"pickle_roundtrip","prediction":value,"base":base,"pass":abs(value-base)<=1e-10})
        assert abs(value-base)<=1e-10
        print(row.checkup,'SOH',round(base,6),'raw',round(rows[-1]['raw_B_SOH_est'],6),diag["status"],'A',diag.get('A_matched_events',0),flush=True)
        pd.DataFrame(rows).to_csv(TASK/"outputs/official_predictions.partial.csv",index=False)
    # Reverse/random call order must give the same values; state is prefix replayed.
    baseline={r["checkup"]:r["SOH_est"] for r in rows}
    for row in full.eval_points.iloc[::-1].itertuples(index=False):
        cutoff=pd.Timestamp(row.date)
        value=model.estimate_soh(full,cutoff)
        checks.append({"checkup":row.checkup,"test":"reverse_query_order","prediction":value,"base":baseline[row.checkup],"pass":abs(value-baseline[row.checkup])<=1e-10})
        assert abs(value-baseline[row.checkup])<=1e-10
    # Freeze stress at CK7. Perturb only then-visible records.
    cutoff=pd.Timestamp(full.eval_points.iloc[-1].date)
    prefix=full.operation.loc[full.operation.timestamp<=cutoff].copy();base=baseline[full.eval_points.iloc[-1].checkup]
    variants={}
    for delta in [-5.,-2.,-1.,1.,2.,5.]:
        f=prefix.copy()
        for c in ["temp_mean_C","temp_min_C","temp_max_C"]:
            if c in f:f[c]+=delta
        variants[f"temperature_bias_{delta:g}C"]=f
    for gain in [.95,.99,1.01,1.05]:
        f=prefix.copy();f.current_A*=gain;variants[f"current_gain_{gain:g}"]=f
    for bias in [-.1,.1]:
        f=prefix.copy();f.current_A+=bias;variants[f"current_offset_{bias:g}A"]=f
    for bias in [-.01,-.005,.005,.01]:
        f=prefix.copy()
        for c in ["cell1_V","cell2_V","cell3_V","cell4_V"]:f[c]+=bias
        variants[f"cell_voltage_bias_{bias:g}V"]=f
    f=prefix.copy();f[["charge_Ah_cum","discharge_Ah_cum"]]=f[["discharge_Ah_cum","charge_Ah_cum"]].to_numpy();variants["counter_swap"]=f
    f=prefix.copy();f[["charge_Ah_cum","discharge_Ah_cum"]]=0.;variants["counter_reset"]=f
    f=prefix.drop(columns=["temp_mean_C","temp_min_C","temp_max_C"]);variants["temperature_columns_missing"]=f
    f=prefix.drop(columns=["cell4_V"]);variants["one_cell_voltage_missing"]=f
    f=prefix.loc[prefix.segment!=6].copy();variants["additional_segment6_deleted"]=f
    variants["no_history"]=prefix.iloc[:0]
    for name,op in variants.items():
        ds=Dataset(op,full.checkups_released,full.eval_points,full.reference_discharge,cutoff)
        test=MyModel(artifact);test.fit(ds);value=test.estimate_soh(ds,cutoff)
        stress.append({"scenario":name,"SOH_est":value,"change_pp":value-base,"status":test.last_diagnostics['status'],
                       "A_matched_events":test.last_diagnostics.get('A_matched_events',0),"raw_B_SOH":test.last_diagnostics.get('raw_soh_pp',value)})
        if name in ['counter_swap','counter_reset']:assert abs(value-base)<=1e-10
        assert np.isfinite(value) and 50<=value<=110
        print('stress',name,round(value-base,6),flush=True)
    pd.DataFrame(rows).to_csv(TASK/"outputs/official_predictions_unlabeled.csv",index=False)
    pd.DataFrame(checks).to_csv(TASK/"outputs/official_causal_checks.csv",index=False)
    pd.DataFrame(stress).to_csv(TASK/"outputs/official_stress.csv",index=False)
    (TASK/"outputs/official_diagnostics.json").write_text(json.dumps(json_safe(diags),indent=2,allow_nan=False)+"\n")
    (TASK/"outputs/official_check_summary.json").write_text(json.dumps({"causal_checks":len(checks),"all_pass":all(z['pass'] for z in checks),
       "stress_scenarios":len(stress),"official_CK1_CK7_MAE":None,"performance_status":"not_testable","raw_input_rows":len(full.operation),
       "numeric_A_enabled":False,"temperature_shift_is_sensor_bias_not_physical_reheating":True},indent=2)+"\n")

if __name__=="__main__":main()
