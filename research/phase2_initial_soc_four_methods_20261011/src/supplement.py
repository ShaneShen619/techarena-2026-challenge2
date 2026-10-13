"""Preplanned structural, waiting-budget and oracle diagnostics.

Executed after primary freeze scoring, reported as exploratory diagnostics.
No retuning or overwriting primary predictions/thresholds.
"""
from __future__ import annotations
import json,pickle
import numpy as np
import pandas as pd
from scipy.optimize import minimize,minimize_scalar
from audit import ROOT,RUN,CFG
from engine import Template,prepare,design,linfit,choose,restore,forecast,errors
from official import key,hist,cached_profile
from synthetic import generate,baseline_par

def structured_profile(template,e,tau,mode):
    p=prepare(e,tau);base=cached_profile(template,e,tau);grid=base['sgrid']
    losses=[];params=[]
    for k,s in enumerate(grid):
        upper=min(65,template.x[-1]+2-p['q'].max()/s)
        def cell(d,c):
            a,x=design(p,s,d,tau)
            return linfit(a,p['y'][:,c]-template.values(x,c))
        def objective(ds):
            raw=np.mean([cell(float(ds[c]),c)[0] for c in range(4)])*1e6
            if mode=='shrunk':raw+=np.mean(((ds-np.mean(ds))/2)**2)
            return raw
        if mode=='common':
            probe=np.unique(np.minimum(np.r_[0,.2,2,10,30,50,upper],upper))
            vals=[objective(np.full(4,d)) for d in probe];best=int(np.argmin(vals));d=probe[best]
            for ix in np.argsort(vals)[:2]:
                lo=probe[max(0,ix-1)];hi=probe[min(len(probe)-1,ix+1)]
                if hi>lo:
                    opt=minimize_scalar(lambda z:objective(np.full(4,z)),bounds=(lo,hi),method='bounded',options={'xatol':.01,'maxiter':20})
                    if opt.fun<objective(np.full(4,d)):d=opt.x
            ds=np.full(4,d)
        else:
            start=np.minimum(base['params'][k,:,0],upper)
            opt=minimize(objective,start,method='L-BFGS-B',bounds=[(0,upper)]*4,options={'maxiter':35,'ftol':1e-10,'maxls':15})
            ds=opt.x
        pars=[];raw=[]
        for c in range(4):
            l,coef=cell(float(ds[c]),c);raw.append(l);pars.append(np.r_[ds[c],coef])
        losses.append(raw);params.append(pars)
    return dict(sgrid=grid,loss=np.array(losses),params=np.array(params))

def structure_and_waiting(events,selected):
    template=Template();structures={};rows=[];curves=[];waiting=[]
    for e in events:
        tau=selected[key(e)]['tau'];history=hist(events,e)
        if e['split']=='evaluation' and history:
            for mode in ['common','shrunk']:
                sm=[];pm=[]
                for h in history:
                    ss,pp=choose(structures[(h['id'],mode)]);sm.append(ss);pm.append(pp)
                s=np.median(sm,axis=0);par=np.median(pm,axis=0)
                for name,budget in [('A',0),('B',1)]:
                    try:p,pred,_=forecast(template,e,s,par,tau,budget,calibration='shift');score=errors(p['y'],pred,p['q'])
                    except ValueError:score=dict(mae_mV=np.nan,rms_mV=np.nan)
                    rows.append(dict(id=e['id'],panel=e['panel'],T=e['T'],budget=name,method='M2_full_'+mode+'_d',s_mean=float(s.mean()),d_spread=float(np.ptp(par[:,0])),**score))
            history_par=np.median([choose(cached_profile(template,h,tau),'shift')[1] for h in history],axis=0)
            for seconds in [300,900,1800]:
                amp,ok,vinf=restore(e,tau,seconds)
                prefix=e['pre_t']<=e['pre_t'][0]+seconds if len(e['pre_t']) else np.zeros(0,bool)
                priorends=[]
                for h in history:
                    if len(h['pre_t']):
                        use=h['pre_t']<=h['pre_t'][0]+seconds
                        if use.any():priorends.append(h['pre_y'][use][-1])
                for mode in ['endpoint','shape']:
                    par=history_par.copy()
                    if len(e['pre_t']) and prefix.any() and priorends:par[:,1]+=e['pre_y'][prefix][-1]-np.median(priorends,axis=0)
                    if mode=='shape' and ok:par[:,-1]=amp
                    for name,budget in [('A',0),('B',1)]:
                        if not ok and mode=='shape':score=dict(mae_mV=np.nan,rms_mV=np.nan)
                        else:
                            try:p,pred,_=forecast(template,e,1,par,tau,budget);score=errors(p['y'],pred,p['q'])
                            except ValueError:score=dict(mae_mV=np.nan,rms_mV=np.nan)
                        waiting.append(dict(id=e['id'],panel=e['panel'],T=e['T'],budget=name,method=mode,waiting_budget_s=seconds,shape_qualified=ok,**score))
        for mode in ['common','shrunk']:
            path=RUN/'profiles'/f"supplement_{e['id'].replace(':','-')}_{mode}.npz"
            if path.exists():z=np.load(path);pr={k:z[k] for k in ['sgrid','loss','params']}
            else:pr=structured_profile(template,e,tau,mode);np.savez_compressed(path,**pr)
            structures[(e['id'],mode)]=pr
            if e['split']=='evaluation':
                for s,l in zip(pr['sgrid'],pr['loss']):curves.append(dict(id=e['id'],panel=e['panel'],T=e['T'],method=mode,s=s,rms_mV=float(np.sqrt(np.mean(l))*1000),conditional_capacity_Ah=float(template.capacity(s))))
        print('supplement structure',e['id'],flush=True)
    pd.DataFrame(rows).to_csv(RUN/'supplement_full_structure_forecasts.csv',index=False)
    pd.DataFrame(curves).to_csv(RUN/'supplement_full_structure_profiles.csv',index=False)
    pd.DataFrame(waiting).to_csv(RUN/'supplement_waiting_budget_forecasts.csv',index=False)

def oracle_and_temperature():
    rows=[];thermal=[]
    for seed in CFG['synthetic_test_seeds']:
        for scenario in CFG['synthetic_scenarios']:
            template,e=generate(seed,scenario)
            for mode in ['known_capacity_only','known_start_and_capacity']:
                ss=e['truth_s'];net=e['net_since_anchor_Ah']
                d=e['truth_d'] if mode=='known_start_and_capacity' else (max(0,net)/ss if np.isfinite(net) else np.zeros(4))
                x=e['q'][:,None]/ss[None,:]+d
                z=e['reference_z'][None,:]-x/102
                rows.append(dict(seed=seed,scenario=scenario,oracle=mode,SOC_mae_pp=float(abs(z-e['truth_z']).mean()*100),initial_SOC_mae_pp=float(abs(z[0]-e['truth_z'][0]).mean()*100)))
        for stage,scenario in enumerate(['constant_25C','temperature_45C','constant_25C']):
            template,e=generate(seed,scenario)
            from engine import profile
            pr=profile(template,e,600);ss,pp=choose(pr)
            rms=np.sqrt(pr['loss'].mean(axis=1))*1000;k=int(rms.argmin());allowed=pr['sgrid'][rms<=rms[k]+1]
            width=template.capacity(allowed.max())-template.capacity(allowed.min())
            gate=bool(width<=5 and k not in [0,len(rms)-1])
            thermal.append(dict(seed=seed,stage=stage,T=e['T'],true_capacity_scale=1,estimated_scale=float(ss.mean()),conditional_reference_capacity_Ah=float(template.capacity(ss)),accepted_update=gate,profile_width_Ah=width,protocol='paired_controller_reset_25_45_25_no_irreversible_aging'))
        print('supplement oracle and temperature',seed,flush=True)
    pd.DataFrame(rows).to_csv(RUN/'oracle_state_diagnostics.csv',index=False)
    pd.DataFrame(thermal).to_csv(RUN/'temperature_return_diagnostics.csv',index=False)

def continuous_daily(events):
    anchors=pd.read_csv(RUN/'charge_anchors.csv');rows=[];summaries=[]
    for file,group in anchors[anchors.qualified].groupby('file'):
        raw=pd.read_csv(ROOT/'data/operation'/file,parse_dates=['timestamp'])
        ends=sorted(group.end_index.astype(int).tolist())
        for k,start in enumerate(ends):
            stop=ends[k+1] if k+1<len(ends) else len(raw)-1
            p=raw.iloc[start:stop+1].drop_duplicates('timestamp',keep='last');t=(p.timestamp-p.timestamp.iat[0]).dt.total_seconds().to_numpy(float);I=p.current_A.to_numpy(float)
            dt=np.diff(t);net=np.r_[0,np.cumsum(-.5*(I[1:]+I[:-1])*dt/3600)]
            valid=np.r_[True,np.cumsum(dt>20)==0]
            chain_id=file+'|'+raw.timestamp.iat[start].isoformat()
            for idx in range(0,len(p),30):rows.append(dict(chain_id=chain_id,timestamp=p.timestamp.iloc[idx].isoformat(),net_reference_position_Ah=float(net[idx]),current_A=float(I[idx]),actual_temperature_C=float(p.temp_mean_C.iloc[idx]),chain_continuous=bool(valid[idx]),interpretation='relative_charge_only_no_absolute_SOC'))
            summaries.append(dict(chain_id=chain_id,file=file,duration_h=float(t[-1]/3600),rows=len(p),gap_count=int((dt>20).sum()),max_gap_s=float(dt.max()) if len(dt) else 0,net_min_Ah=float(net[valid].min()),net_max_Ah=float(net[valid].max()),max_negative_return_Ah=float(-min(0,net[valid].min())),all_rows_continuous=bool(valid.all())))
        print('continuous daily audit',file,flush=True)
    pd.DataFrame(rows).to_csv(RUN/'daily_relative_charge_trace.csv',index=False)
    pd.DataFrame(summaries).to_csv(RUN/'daily_chain_summary.csv',index=False)

def main():
    with open(RUN/'events.pkl','rb') as f:events=pickle.load(f)
    selected=json.loads((RUN/'selected_configuration.json').read_text())
    (RUN/'SUPPLEMENT_SCOPE.md').write_text('''# 补充诊断范围

主冻结评分已完成，本文件中的诊断对应START_PROMPT预先要求的共同/收缩起点完整优化、静置等待预算、已知容量/起点理想对照、温度往返及连续日常电量追踪。诊断在看过主结果后执行，故标为探索性，不覆盖主评分，不调主算法/超参数/接纳门，不把补充最佳结果选作正式模型。

共同/收缩起点拟合明确优化全曲线干扰参数；目标前向只使用历史模型及合法前缀。静置预算使用最早前缀，形状不足的结果留空，不以额外长等待结果补成有效SOC。温度往返每阶段控制复位，保持同芯参数与容量，无不可逆老化，检验可逆热效应导致的虚假伸缩；不是全天连续热动力学验证。全天原始电流追踪以相对Ah记录，遇缺口停止宣称连续，充电方向不套用放电OCV模板。
''')
    structure_and_waiting(events,selected);oracle_and_temperature();continuous_daily(events)
    print('SUPPLEMENT_COMPLETE',flush=True)

if __name__=='__main__':main()
