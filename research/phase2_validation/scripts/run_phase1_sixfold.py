"""Six-cell developmental holdout proxy: prediction before each measured discharge.

The target's cc_discharge rows and step_capacity are never passed to either
estimator. Only the first eligible capacity and its reference trace are public.
Shared hyperparameters were fixed in notes/PROTOCOL.md before this run.
"""
from pathlib import Path
import glob, sys, time, json
from types import SimpleNamespace
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
TASK=ROOT/'research/phase2_validation'
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(TASK/'candidates/route_a'))
from my_model.model_route_a import RouteA
for k in list(sys.modules):
    if k=='my_model' or k.startswith('my_model.'):
        del sys.modules[k]
sys.path[0]=str(TASK/'candidates/route_b')
from my_model.model_route_b import RouteB

def main():
    labels=pd.read_csv(TASK/'preflight/downloaded_data/phase1_label_inventory.csv')
    cell_ids=sorted(labels.cell_id.unique())
    predictions=[]; fold_manifest=[]
    out=TASK/'runs/phase1_sixfold_v2'
    out.mkdir(parents=True,exist_ok=True)
    for held in cell_ids:
        started=time.monotonic()
        folder=ROOT/'dataset original'/held
        cols=['absolute_time','cycle_number','step_type','voltage_V','current_A','temperature_C','step_capacity_Ah']
        raw=pd.concat([pd.read_csv(p,usecols=cols,parse_dates=['absolute_time']) for p in sorted(folder.glob('*.csv'))],ignore_index=True)
        raw=raw.sort_values('absolute_time',kind='stable').reset_index(drop=True)
        dis=raw.loc[raw.step_type.eq('cc_discharge')]
        starts=dis.groupby('cycle_number').absolute_time.min()
        lab=labels[(labels.cell_id==held)&labels.old_official_label_valid].copy()
        lab['discharge_start']=lab.cycle.map(starts)
        lab=lab.dropna(subset=['discharge_start']).sort_values('discharge_start',kind='stable')
        anchor=lab.iloc[0]
        targets=lab[lab.discharge_start>anchor.discharge_start].reset_index(drop=True)
        indices=np.unique(np.rint(np.quantile(np.arange(len(targets)),[.1,.5,.9])).astype(int))
        selected=targets.iloc[indices]
        aref=dis[dis.cycle_number.eq(anchor.cycle)].sort_values('absolute_time',kind='stable')
        reference=pd.DataFrame({'discharged_Ah':aref.step_capacity_Ah.to_numpy(float),
                                'voltage_V':aref.voltage_V.to_numpy(float)})
        anchor_q=float(anchor.capacity_Ah)
        charging=raw.loc[~raw.step_type.eq('cc_discharge'),
                         ['absolute_time','cycle_number','voltage_V','current_A','temperature_C']].copy()
        charge_end=charging.absolute_time.max()
        assert 'step_capacity_Ah' not in charging
        train_ids=[x for x in cell_ids if x!=held]
        fold_manifest.append({'heldout_cell':held,'training_cells':train_ids,'anchor_cycle':int(anchor.cycle),
                              'anchor_Ah':anchor_q,'target_cycles':selected.cycle.astype(int).tolist(),
                              'label_protocol':'single_cell_0.5C_or_1C_CC_to_2.5V','supervised_training':'none'})
        for stage,(_,target) in enumerate(selected.iterrows()):
            cutoff=pd.Timestamp(target.discharge_start)
            visible=charging.loc[charging.absolute_time<cutoff]
            if not visible.empty:
                assert visible.absolute_time.max()<cutoff
            # Both estimators receive exactly this same input frame and BOL.
            ds=SimpleNamespace(operation=visible,bol_capacity_Ah=anchor_q,
                               reference_discharge=reference)
            for name,model in [('B0',None),('A',RouteA(single_cell=True)),('B',RouteB(single_cell=True))]:
                t0=time.monotonic()
                if model:
                    model.fit(ds)
                    pred=model.estimate_soh(ds,cutoff)
                    diag=model.last_diagnostics
                else:
                    pred=100*anchor_q/102
                    diag={'fallback':True,'updates':0}
                predictions.append({'run_id':'E3P1_sixfold_v2_reused_development_cells','evidence':'E3-P1','cell_id':held,
                    'training_cells':'|'.join(train_ids),'stage':('early','middle','late')[stage],
                    'target_cycle':int(target.cycle),'anchor_cycle':int(anchor.cycle),
                    'anchor_capacity_Ah':anchor_q,'target_discharge_start':cutoff,
                    'input_end':visible.absolute_time.max() if len(visible) else pd.NaT,
                    'visible_charge_rows':len(visible),'method':name,
                    'prediction_soh_pp':float(pred),'target_soh_pp':float(target.soh_pp),
                    'prediction_Ah':float(pred*102/100),'target_Ah':float(target.capacity_Ah),
                    'error_pp':float(pred-target.soh_pp),'fallback':bool(diag.get('fallback',False)),
                    'updates':int(diag.get('updates',0)),
                    'elapsed_s':round(time.monotonic()-t0,4),
                    'note':'single-cell high-rate discharge proxy; not C/20 pack validation'})
            pd.DataFrame(predictions).to_csv(out/'predictions.partial.csv',index=False)
        print(held,'targets',selected.cycle.tolist(),'seconds',round(time.monotonic()-started,1),flush=True)
        del raw,dis,charging
    df=pd.DataFrame(predictions)
    assert df.cell_id.nunique()==6 and len(df)==54
    assert (pd.to_datetime(df.input_end)<pd.to_datetime(df.target_discharge_start)).all()
    df.to_csv(TASK/'outputs/phase1_crossvalidation_predictions.csv',index=False)
    (TASK/'outputs/phase1_folds.json').write_text(json.dumps(fold_manifest,ensure_ascii=False,indent=2))
    print(df.groupby('method').agg(n=('error_pp','size'),mae=('error_pp',lambda x:x.abs().mean()),
        rmse=('error_pp',lambda x:np.sqrt(np.mean(x*x))),fallback=('fallback','mean')).to_string())

if __name__=='__main__':main()
