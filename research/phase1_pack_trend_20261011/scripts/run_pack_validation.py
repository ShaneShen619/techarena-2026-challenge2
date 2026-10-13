"""4S prototype, independent mechanism and official unlabeled replay."""
from __future__ import annotations
import ast,hashlib,json,sys
from pathlib import Path
import numpy as np
import pandas as pd
TASK=Path(__file__).resolve().parents[1];ROOT=TASK.parents[1];PREV=TASK.parent/"phase1_transfer_ab"
sys.path[:0]=[str(TASK/"src"),str(PREV/"src"),str(ROOT)]
from pack import PackPrototype
from trend import summarize_trend,SIGNAL,CONTROL,feedback
from age_prior import MyModel,shallow_observations
from fusion import ridge_predict
from framework.data import load_dataset

def independent_functions():
    # Reuse ONLY independent truth definitions, without executing experiment main.
    source=TASK.parent/"phase2_temperature_improvement/scripts/run_m6_mechanism.py"
    tree=ast.parse(source.read_text());names={"pack_voltage","discharge_truth","charge_event"}
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    env={"np":np,"pd":pd};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),"exec"),env)
    return env,hashlib.sha256(source.read_bytes()).hexdigest()

def main():
    (TASK/"outputs").mkdir(exist_ok=True)
    full=load_dataset(ROOT/"data");q0=full.bol_capacity_Ah
    p=PackPrototype(full.reference_discharge,q0=q0)
    checks=[]
    def check(name,error,tol=1e-8):
        checks.append(dict(test=name,error=float(error),tolerance=tol,passed=bool(error<=tol)))
        assert error<=tol,(name,error)
    check("CK0 published capacity identity",abs(p.capacity(1.)-q0))
    for s in [.7,.85,.95,1.]:check(f"common stretch {s}",abs(p.capacity(s)-q0*s))
    # Measured chain residual retained; compare pointwise on calibrated axis.
    ref=full.reference_discharge.drop_duplicates("discharged_Ah",keep="last").sort_values("discharged_Ah")
    q=ref.discharged_Ah.to_numpy()/p.axis_factor
    check("loaded CK0 pack voltage pointwise",float(np.max(abs(p.voltage(q,1)-ref.voltage_V.to_numpy()))))
    scenarios=[]
    for name,s,d,r in [
        ("shared B",np.full(4,.97),np.zeros(4),np.zeros(4)),
        ("one cell additional 0.5 percent",np.array([.965,.97,.97,.97]),np.zeros(4),np.zeros(4)),
        ("one cell additional 1 percent",np.array([.96,.97,.97,.97]),np.zeros(4),np.zeros(4)),
        ("one cell initial deficit 1Ah",np.full(4,.97),np.array([1.,0,0,0]),np.zeros(4)),
        ("one cell initial deficit 2Ah",np.full(4,.97),np.array([2.,0,0,0]),np.zeros(4)),
        ("all cells added resistance 1mOhm",np.full(4,.97),np.zeros(4),np.full(4,.001)),
        ("all cells added resistance 3mOhm",np.full(4,.97),np.zeros(4),np.full(4,.003)),
        ("extreme mismatch rejected",np.array([.7,.97,.97,.97]),np.zeros(4),np.zeros(4))]:
        try:capacity=p.capacity(s,d,r);status="computed"
        except ValueError as e:capacity=np.nan;status=str(e)
        scenarios.append(dict(scenario=name,capacity_Ah=capacity,shift_from_common_Ah=capacity-q0*.97,
                              status=status,mean_stretch_shortcut_Ah=q0*float(np.mean(s)),min_stretch_shortcut_Ah=q0*float(np.min(s))))
    pd.DataFrame(scenarios).to_csv(TASK/"outputs/pack_sensitivity.csv",index=False)
    # Independent OCV + ohmic + dynamic-polarization truth. Shape differs from
    # official template and stage-1 loss curve. Deformation parameters here are
    # deliberately supplied true: verifies projection, NOT their identifiability.
    env,truth_hash=independent_functions();voltage=env["pack_voltage"];truth=env["discharge_truth"]
    cap0=np.full(4,102.);T=np.full(4,25.);soc=np.ones(4);R=np.array([.006,.007,.008,.009]);rp=np.full(4,.002)
    aq=truth(cap0,T,soc,R,rp,5.1,11.2,1.)
    q=np.arange(0.,aq+.005,.005);cols={}
    for i in range(4):
        ss=1-q/102.
        cols[f"cell{i+1}_V"]=2.84+.49*ss+.055*np.tanh((ss-.12)/.055)+.035*np.tanh((ss-.84)/.065)-5.1*R[i]-5.1*rp[i]*(1-np.exp(-q/5.1*3600/900))
    synthetic=PackPrototype(pd.DataFrame(dict(discharged_Ah=q,voltage_V=voltage(q,cap0,T,soc,R,rp,5.1),**cols)),q0=aq)
    syn=[]
    for name,s,d,dr in [
        ("common fade",np.full(4,.9),np.zeros(4),np.zeros(4)),
        ("small intercell mismatch",np.array([.90,.902,.898,.9]),np.zeros(4),np.zeros(4)),
        ("one initial SOC deficit",np.full(4,.9),np.array([1.,0,0,0]),np.zeros(4)),
        ("added resistance",np.full(4,.9),np.zeros(4),np.full(4,.002)),
        ("large intercell mismatch",np.array([.80,.93,.96,.99]),np.zeros(4),np.zeros(4))]:
        latent_cap=cap0*s;ss=1-d/102.;actual=truth(latent_cap,T,ss,R+dr,rp,5.1,11.2,1.)
        coarse=truth(latent_cap,T,ss,R+dr,rp,5.1,11.2,10.)
        try:estimate=synthetic.capacity(s,d,dr);status="computed with supplied truth parameters"
        except ValueError as e:estimate=np.nan;status=str(e)
        syn.append(dict(scenario=name,true_group_Ah=actual,predicted_group_Ah=estimate,error_Ah=estimate-actual,
                        mean_stretch_shortcut_Ah=aq*float(np.mean(s)),min_stretch_shortcut_Ah=aq*float(np.min(s)),
                        coarse_fine_difference_Ah=abs(actual-coarse),status=status))
    pd.DataFrame(syn).to_csv(TASK/"outputs/independent_pack_mechanism.csv",index=False)
    # A mechanistic diagnostic: independent charge curves; no target-capacity
    # labels given to trend extraction. Known synthetic k_B supplies mapping.
    charge=env["charge_event"];diagnostics=[]; start=pd.Timestamp("2025-01-01")
    for scenario in ["true_fade_constant_temperature","constant_capacity_hidden_self_heating"]:
        crops=[];priors=[];measurements=[];quality=[];eventends=[];targets=[];slopes=[]
        kB=.0005;k=.0008 if scenario.startswith("true_fade") else 0.
        for i in range(12):
            days=10.*i; capacity=np.full(4,102.*np.exp(-k*days))
            temp=np.full(4,25.+(.06*days if k==0 else 0.))
            event=charge(start+pd.Timedelta(days=days),capacity,temp,25.,7.,1801,30.,0.,i)
            frag=shallow_observations(event,20);frag=frag.loc[frag.cell.eq("cell1_V")]
            crops.append(frag)
            # Same allowed memory as the source panel: first10 + recent5.
            visible=pd.concat(crops,ignore_index=True);visible=pd.concat([visible.head(10),visible.tail(5)]).drop_duplicates("fragment_end")
            tr=summarize_trend(visible,start+pd.Timedelta(days=days+1))
            b=aq*np.exp(-kB*days);priors.append(b);targets.append(aq*np.exp(-k*days))
            rate=tr["median_slope_per_day"];slopes.append(rate)
            measurements.append(float(np.log(np.clip(rate/kB,.5,2.))) if np.isfinite(rate) else 0.)
            quality.append(tr["eligible"]);eventends.append(tr["event_end"])
        corrected,log=feedback(priors,aq,measurements,quality,eventends,.3,"forward")
        for i in range(12):diagnostics.append(dict(scenario=scenario,day=i*10,A_log_window_decline_per_day=slopes[i],
            B_capacity_Ah=priors[i],rate_feedback_capacity_Ah=corrected[i],true_capacity_Ah=targets[i],
            multiplier_next=log[i]["multiplier_next"],eligible=quality[i]))
    pd.DataFrame(diagnostics).to_csv(TASK/"outputs/independent_A_rate_mechanism.csv",index=False)
    # Official prototype: past-only CK decision grid; no automatic deployment.
    frozen=json.loads((TASK/"artifacts/full_source_rate_models.json").read_text())
    rate=next(m for m in frozen if m["mode"]=="forward" and m["family"]=="signal")
    baseline=MyModel(PREV/"artifacts/source_prior.json");baseline.fit(full)
    def replay(operation,queries):
        entries=[];features=[];bs=[]
        for ev in queries.itertuples(index=False):
            at=pd.Timestamp(ev.date)
            prefix=operation.loc[(operation.timestamp<=at)&(operation.timestamp>=baseline.anchor_date)].copy()
            ds=type(full)(prefix,full.checkups_released,full.eval_points,full.reference_discharge,at)
            b=baseline.estimate_soh(ds,at);diag=baseline.last_diagnostics;bs.append(b)
            crops=shallow_observations(prefix,20);parts=[]
            for cell in [f"cell{i}_V" for i in range(1,5)]:
                cf=crops.loc[crops.cell.eq(cell)] if len(crops) else crops
                if len(cf):cf=pd.concat([cf.sort_values("fragment_end").head(10),cf.sort_values("fragment_end").tail(5)]).drop_duplicates("fragment_end")
                tr=summarize_trend(cf,at);parts.append(dict(cell=cell,**tr))
            f={k:float(np.median([z[k] for z in parts if np.isfinite(z[k])])) if any(np.isfinite(z[k]) for z in parts) else np.nan for k in CONTROL+SIGNAL if k not in ["age_days","charge_EFC"]}
            f.update(age_days=(at-baseline.anchor_date).total_seconds()/86400,charge_EFC=diag.get("charge_EFC",0.))
            eligible=sum(z["eligible"] for z in parts)
            # Research aggregate with two observed channels: cannot infer missing
            # cell trends. Common feedback is an explicit assumption only.
            features.append(dict(**f,eligible=eligible>=2,event_end=max((z["event_end"] for z in parts),default="")))
            entries.append(dict(checkup=ev.checkup,date=at.isoformat(),B_SOH_pp=b,eligible_A_cells=eligible,
                                missing_hours=diag.get("missing_hours",0.),source_low_rate_fraction=diag.get("low_rate_observed_fraction",0.),
                                cell_trends=parts))
        x=pd.DataFrame(features)
        out,log=feedback(bs,100*q0/102.,ridge_predict(rate,x[rate["columns"]].to_numpy(float)),
                         x.eligible.to_numpy(),x.event_end.tolist(),rate["gain"],"forward")
        for i,e in enumerate(entries):
            s=bs[i]/(100*q0/102.);sf=out[i]/(100*q0/102.)
            e.update(B_4S_capacity_Ah=p.capacity(s),research_rate_4S_capacity_Ah=p.capacity(sf),
                     research_rate_SOH_pp=out[i],rate_multiplier_next=log[i]["multiplier_next"],numeric_rate_accepted=False,
                     mode_scope="frozen CK decision grid; common-rate two-channel assumption")
        return entries
    entries=replay(full.operation,full.eval_points)
    # End-to-end future perturbation, deletion, and query prefix at CK3.
    qeval=full.eval_points.iloc[:4];at=qeval.date.iloc[-1];pref=full.operation.loc[full.operation.timestamp<=at].copy()
    causal_base=replay(pref,qeval)[-1]["research_rate_4S_capacity_Ah"]
    future=full.operation.loc[full.operation.timestamp>at].copy()
    for c in ["current_A","temp_mean_C","cell1_V","cell2_V","cell3_V","cell4_V"]:
        if c in future:future[c]=1e9
    changed=replay(pd.concat([pref,future],ignore_index=True),qeval)[-1]["research_rate_4S_capacity_Ah"]
    check("official future extremes do not alter CK3",abs(causal_base-changed))
    check("official prefix versus full campaign CK3",abs(causal_base-entries[3]["research_rate_4S_capacity_Ah"]))
    pd.DataFrame([{k:v for k,v in e.items() if k!="cell_trends"} for e in entries]).to_csv(TASK/"outputs/official_4S_prototype.csv",index=False)
    # JSON nulls rather than nonstandard NaN.
    def safe(obj):
        if isinstance(obj,dict):return {k:safe(v) for k,v in obj.items()}
        if isinstance(obj,list):return [safe(v) for v in obj]
        if isinstance(obj,float) and not np.isfinite(obj):return None
        return obj
    (TASK/"outputs/official_cell_trends.json").write_text(json.dumps(safe(entries),indent=2,allow_nan=False)+"\n")
    pd.DataFrame(checks).to_csv(TASK/"outputs/pack_checks.csv",index=False)
    summary=dict(q0_Ah=q0,raw_CK0_first_cutoff_Ah=p.raw_cutoff_Ah,axis_factor=p.axis_factor,
                 chain_residual_median_V=float(np.median(p.residual)),passed_checks=len(checks),
                 truth_code_sha256=truth_hash,official_rate_gain=rate["gain"],official_accuracy="not_testable",
                 projection_parameter_identification="not demonstrated",shared_stretch_reduces_to_B_capacity=True)
    (TASK/"outputs/pack_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(pd.DataFrame(scenarios).to_string(index=False),flush=True)
    print(pd.DataFrame(syn).to_string(index=False),flush=True);print(json.dumps(summary),flush=True)

if __name__=="__main__":main()
