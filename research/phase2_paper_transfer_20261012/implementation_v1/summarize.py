"""Frozen metric aggregation and decision logic; report prose handled separately."""
import json
import numpy as np
import pandas as pd
from common import *

def official_summary():
    f=pd.read_csv(TASK/'forward_evaluation_metrics.csv')
    if len(f[f.method=='frozen_baseline'])!=92:raise AssertionError('46 events x 2 budgets required')
    grouped=f.groupby(['budget','method']);rows=[];layers=[]
    for (budget,method),g in grouped:
        base=f[(f.budget==budget)&(f.method=='frozen_baseline')]
        joined=g.merge(base[['id','mae_mV']],on='id',suffixes=('','_baseline'))
        mae=float(joined.mae_mV.mean());b=float(joined.mae_mV_baseline.mean());gain=1-mae/b
        layer_ok=True
        for (panel,T),h in joined.groupby(['panel','T']):
            bb=float(h.mae_mV_baseline.mean());vv=float(h.mae_mV.mean());worse=vv/bb-1
            if len(h)>=5 and worse>CFG['layer_worsening_gate']:layer_ok=False
            layers.append(dict(budget=budget,method=method,panel=panel,T=T,n=len(h),mae_mV=vv,
                baseline_mV=bb,relative_worsening=worse,direct_coverage=float((~h.fallback).mean())))
        direct=joined[~joined.fallback]
        rows.append(dict(budget=budget,method=method,n=len(joined),mae_mV=mae,baseline_mV=b,
            relative_gain=gain,direct_coverage=float((~joined.fallback).mean()),
            direct_mae_mV=float(direct.mae_mV.mean()) if len(direct) else np.nan,
            forward_gate=bool(gain>=CFG['voltage_gain_gate'] and layer_ok)))
    out=pd.DataFrame(rows);out.to_csv(TASK/'forward_summary.csv',index=False)
    pd.DataFrame(layers).to_csv(TASK/'forward_by_layer.csv',index=False)
    curves=pd.read_csv(TASK/'historical_evaluation_profiles.csv');capacity_rows=[]
    for (event_id,loss,mode),g in curves.groupby(['id','loss','mode']):
        allowed=g[g.loss_mV<=g.loss_mV.min()+CFG['profile_tolerance_mV']]
        capacity_rows.append(dict(id=event_id,loss=loss,mode=mode,
            conditional_capacity_min_Ah=float(100.41*allowed.s.min()),
            conditional_capacity_max_Ah=float(100.41*allowed.s.max()),
            width_Ah=float(100.41*np.ptp(allowed.s)),
            protocol='CK0 loaded state, d=0, no additional voltage shift; not measured capacity',
            statistical_confidence_interval=False,checkpoint_SOH_identified=False))
    pd.DataFrame(capacity_rows).to_csv(TASK/'conditional_capacity_windows.csv',index=False)
    # Same frozen baselines must reproduce old metrics; history cache is read-only.
    old=pd.read_csv(OLD_RUN/'official_evaluation_metrics.csv')
    old=old[old.method==old.baseline]
    new=f[f.method=='frozen_baseline']
    compare=new.merge(old[['id','budget','mae_mV']],on=['id','budget'],suffixes=('_new','_old'))
    savejson('baseline_reproduction.json',dict(rows=len(compare),max_abs_difference_mV=float(abs(compare.mae_mV_new-compare.mae_mV_old).max())))
    return out

def synthetic_summary():
    f=pd.read_csv(TASK/'synthetic_evaluation_metrics.csv');rows=[];by_scenario=[];gates=[]
    for (loss,mode,kind),g in f.groupby(['loss','mode','kind']):
        for scenario,h in g.groupby('scenario'):
            accepted=h[h.accepted_update];valid=h[h.capacity_valid]
            by_scenario.append(dict(loss=loss,mode=mode,kind=kind,scenario=scenario,n=len(h),
                s_mae=float(h.s_mae.mean()),s_p95=float(h.s_mae.quantile(.95)),s_worst=float(h.s_mae.max()),
                accepted_coverage=float(h.accepted_update.mean()),capacity_coverage=float(h.capacity_valid.mean()),
                capacity_error_Ah=float(valid.capacity_error_Ah.mean()) if len(valid) else np.nan,
                false_accepted_total_rate=float(h.false_accepted_scale.mean()),
                false_rate_given_accepted=float(accepted.false_accepted_scale.mean()) if len(accepted) else np.nan,
                voltage_mae_mV=float(h.voltage_mae_mV.mean())))
        positive=g[g.scenario=='informative_60Ah'];negative=g[g.constant_capacity]
        accepted_negative=negative[negative.accepted_update]
        positive_pass=bool(positive.s_mae.mean()<=.02 and positive.accepted_update.mean()>=.8)
        negative_pass=bool(negative.false_accepted_scale.mean()<=.05)
        entry=dict(loss=loss,mode=mode,kind=kind,n=len(g),positive_n=len(positive),
            positive_s_mae=float(positive.s_mae.mean()),positive_p95=float(positive.s_mae.quantile(.95)),
            positive_worst=float(positive.s_mae.max()),positive_coverage=float(positive.accepted_update.mean()),
            negative_n=len(negative),negative_accepted=int(negative.accepted_update.sum()),
            false_negative_total_rate=float(negative.false_accepted_scale.mean()),
            false_given_negative_accepted=float(accepted_negative.false_accepted_scale.mean()) if len(accepted_negative) else np.nan,
            capacity_coverage=float(g.capacity_valid.mean()),positive_gate=positive_pass,negative_gate=negative_pass,
            mechanism_gate=bool(positive_pass and negative_pass))
        rows.append(entry)
        if kind=='common':gates.append(entry)
    out=pd.DataFrame(rows);out.to_csv(TASK/'synthetic_summary.csv',index=False)
    pd.DataFrame(by_scenario).to_csv(TASK/'synthetic_by_scenario.csv',index=False)
    return gates

def main():
    from run import verify_freeze
    verify_freeze()
    for marker in ['OFFICIAL_COMPLETE','SYNTHETIC_COMPLETE','DIAGNOSTICS_COMPLETE','PAIRED_COMPLETE']:
        if not (TASK/marker).exists():raise RuntimeError('unfinished: '+marker)
    official=official_summary();mechanism=synthetic_summary()
    ident=pd.read_csv(TASK/'identifiability.csv');sens=pd.read_csv(TASK/'sensitivity_best_states.csv')
    records=[]
    for (layer,loss),g in sens.groupby(['layer','loss']):
        base=ident[(ident.layer==layer)&(ident.loss==loss)&(ident['mode']=='independent')].iloc[0]
        cap0=100.41*base.best_s
        spread=float(np.ptp(np.r_[cap0,g.best_capacity_Ah]))
        passed=bool(base.gate and spread<=2)
        records.append(dict(layer=layer,loss=loss,primary_s=float(base.best_s),
            conditional_width_Ah=float(base.width_Ah),nuisance_best_capacity_span_Ah=spread,
            identification_gate=passed))
    pd.DataFrame(records).to_csv(TASK/'identifiability_summary.csv',index=False)
    any_ident=any(r['identification_gate'] for r in records)
    # Global adoption additionally requires every relevant layer and validated
    # mechanism. Isolated layer success is reported separately.
    global_ident=all(r['identification_gate'] for r in records if r['loss']=='LAD')
    primary=official[official.method=='LAD_independent_multi_common']
    primary_forward=bool(len(primary)==2 and primary.forward_gate.all())
    mech=next(r for r in mechanism if r['loss']=='LAD' and r['mode']=='independent')
    adoption=bool(global_ident and primary_forward and mech['mechanism_gate'])
    decision=dict(execution_date='2026-10-13',official_events=46,synthetic_scenario_seed_combinations=160,
        literature_reproduction=False,real_per_cell_SOC_accuracy='unmeasurable_no_independent_labels',
        real_later_capacity_accuracy='unmeasurable_no_independent_same_protocol_labels',
        primary_candidate='LAD_independent_multi_common',primary_forward_gate=primary_forward,
        primary_mechanism_gate=bool(mech['mechanism_gate']),global_identification_gate=global_ident,
        some_layer_identification_gate=any_ident,accept_capacity_update=adoption,
        accept_four_independent_scales=False,deploy_formal_model=False,
        publish_new_checkpoint_SOH=False,Sun_reconstruction='feature_audit_only_missing_full_formula_and_OCV_scale',
        protected_unchanged=protected()==json.loads((TASK/'protected_before.json').read_text()),
        conclusion='Independent constraints evaluated; do not identify scale solely from voltage residual. See per-layer outcomes.')
    savejson('decision.json',decision);(TASK/'EVALUATION_COMPLETE').write_text('2026-10-13\n')
    print(json.dumps(decision,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
