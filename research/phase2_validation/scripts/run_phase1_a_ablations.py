"""Same 18 held-cell forward targets, A component ablations after development reuse."""
from pathlib import Path
from types import SimpleNamespace
import sys,json
import pandas as pd
ROOT=Path(__file__).resolve().parents[3]
TASK=ROOT/'research/phase2_validation'
sys.path.insert(0,str(TASK/'candidates/route_a'))
from my_model.model_route_a import RouteA

VARIANTS={
 'A_default':{},'A_no_condition_match':{'match_conditions':False},
 'A_mean_instead_median':{'robust':False},
 'A_no_depth_split':{'split_depth':False},
 'A_disagreement_gate':{'disagreement_gate':True},
 'B2_single_cell_window':{}}

def main():
    labels=pd.read_csv(TASK/'preflight/downloaded_data/phase1_label_inventory.csv')
    folds=json.loads((TASK/'outputs/phase1_folds.json').read_text())
    rows=[]
    for fold in folds:
        cid=fold['heldout_cell'];folder=ROOT/'dataset original'/cid
        cols=['absolute_time','cycle_number','step_type','voltage_V','current_A','temperature_C','step_capacity_Ah']
        raw=pd.concat([pd.read_csv(f,usecols=cols,parse_dates=['absolute_time']) for f in sorted(folder.glob('*.csv'))],ignore_index=True)
        raw=raw.sort_values('absolute_time',kind='stable')
        dis=raw[raw.step_type.eq('cc_discharge')]
        starts=dis.groupby('cycle_number').absolute_time.min()
        lab=labels[(labels.cell_id==cid)&labels.old_official_label_valid].set_index('cycle')
        anchor=fold['anchor_cycle'];q0=fold['anchor_Ah']
        refrows=dis[dis.cycle_number.eq(anchor)].sort_values('absolute_time',kind='stable')
        ref=pd.DataFrame({'discharged_Ah':refrows.step_capacity_Ah.to_numpy(float),
                          'voltage_V':refrows.voltage_V.to_numpy(float)})
        inputrows=raw[~raw.step_type.eq('cc_discharge')][['absolute_time','cycle_number','voltage_V','current_A','temperature_C']]
        for stage,cycle in zip(('early','middle','late'),fold['target_cycles']):
            cutoff=starts.loc[cycle]
            visible=inputrows[inputrows.absolute_time<cutoff]
            ds=SimpleNamespace(operation=visible,bol_capacity_Ah=q0,reference_discharge=ref)
            target=float(lab.loc[cycle,'soh_pp'])
            for variant,config in VARIANTS.items():
                model=RouteA(single_cell=True,**config);model.fit(ds)
                if variant=='B2_single_cell_window':model.windows=((3.36,3.43),)
                pred=model.estimate_soh(ds,cutoff)
                rows.append({'run_id':'E3P1_A_ablation_reused_development_cells',
                    'evidence':'E3-P1','dataset':'phase1_six_cells',
                    'protocol':'single_cell_0.5C_or_1C_discharge_to_2.5V',
                    'cell_id':cid,'stage':stage,'target_cycle':cycle,'variant':variant,
                    'prediction_soh_pp':pred,'target_soh_pp':target,'error_pp':pred-target,
                    'fallback':model.last_diagnostics['fallback'],
                    'updates':model.last_diagnostics['updates']})
        print(cid,'A ablations complete',flush=True)
    df=pd.DataFrame(rows)
    assert len(df)==108 and df.cell_id.nunique()==6
    df.to_csv(TASK/'outputs/phase1_a_ablations.csv',index=False)
    print(df.groupby('variant').error_pp.agg(MAE=lambda x:x.abs().mean(),RMSE=lambda x:(x.pow(2).mean())**0.5).to_string())

if __name__=='__main__':main()
