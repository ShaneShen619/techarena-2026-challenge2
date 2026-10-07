"""Independent two-RC/hysteretic four-cell simulator and C/20 label evaluation."""
from pathlib import Path
from types import SimpleNamespace
import json,sys,time
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
TASK=ROOT/'research/phase2_validation'
sys.path.insert(0,str(TASK/'candidates/route_a'))
from my_model.model_route_a import RouteA
for key in list(sys.modules):
    if key=='my_model' or key.startswith('my_model.'):
        del sys.modules[key]
sys.path[0]=str(TASK/'candidates/route_b')
from my_model.model_route_b import RouteB

def ocv(z,cell,shape_shift=0.0):
    z=np.asarray(z)
    low=0.56/(1+np.exp(np.clip((z-0.055)/0.018,-50,50)))
    high=0.105/(1+np.exp(np.clip(-(z-0.90-shape_shift)/0.032,-50,50)))
    return 3.15+0.20*z+high-low+0.004*(cell-1.5)

def trace(capacity, current, temp, seconds, z_start, rng, *, noise=0.001,
          v_bias=0.0, i_bias=0.0, shape_shift=0.0):
    """Two RC modes and current hysteresis; hidden Q is never read by estimators."""
    n=len(seconds); z=np.full(4,z_start,float); p1=np.zeros(4);p2=np.zeros(4)
    voltage=np.zeros((n,4)); group_current=np.full(n,current+i_bias)
    temp_factor=1+0.004*(25-temp)
    for k in range(n):
        if k:
            dt=seconds[k]-seconds[k-1]
            z=np.maximum(-0.1,np.minimum(1.1,z+current*dt/(3600*capacity)))
            p1=p1*np.exp(-dt/90)+0.0017*current*(1-np.exp(-dt/90))
            p2=p2*np.exp(-dt/800)+0.0012*current*(1-np.exp(-dt/800))
        voltage[k]=ocv(z,np.arange(4),shape_shift)*temp_factor+0.0013*current+p1+p2
        voltage[k]+=0.007*np.sign(current)+v_bias+rng.normal(0,noise,4)
    return voltage,group_current,z

def measured_c20(capacity,temp,rng,shape_shift=0):
    seconds=np.arange(0,100000,60,dtype=float)
    v,i,z=trace(capacity,-5.1,temp,seconds,1.0,rng,noise=0,
                shape_shift=shape_shift)
    cutoff=np.flatnonzero(v.sum(axis=1)<=11.2)
    end=int(cutoff[0]) if len(cutoff) else len(v)-1
    q=5.1*seconds[:end+1]/3600.0
    ref=pd.DataFrame({'timestamp':pd.Timestamp('2025-01-01')+pd.to_timedelta(seconds[:end+1],unit='s'),
        'current_A':-5.1,'voltage_V':v[:end+1].sum(axis=1),'discharged_Ah':q,
        **{f'cell{j+1}_V':v[:end+1,j] for j in range(4)}})
    return float(q[-1]),ref

def capacities(seed,scenario,stage):
    rng=np.random.default_rng(seed)
    base=101+rng.normal(0,0.5,4)
    if scenario=='stable': loss=np.zeros(4)
    elif scenario=='linear': loss=np.full(4,stage*1.8)
    elif scenario=='accelerating': loss=np.full(4,0.8*stage+0.8*stage**2)
    elif scenario=='limiting_cell': loss=np.array([stage*0.8,stage*0.8,stage*3.5,stage*0.8])
    else: raise ValueError(scenario)
    return base-loss

def operation(seed,scenario,stage,capacity,rng,stress=None):
    temp=25.0 if stage%2==0 else 45.0
    start=pd.Timestamp('2025-01-15')+pd.Timedelta(days=30*stage)
    dt={'coarse_10s':10,'coarse_30s':30,'coarse_60s':60}.get(stress,20)
    duration=int(0.38*min(capacity)/20*3600)
    sec=np.arange(0,duration+1,dt,dtype=float)
    volts,cur,_=trace(capacity,20,temp,sec,0.60,rng,
        noise=0.001 if stress!='voltage_noise' else 0.008,
        v_bias={'voltage_bias':0.01,'voltage_bias_50mV':0.05}.get(stress,0.0),
        i_bias={'current_bias':0.2,'current_bias_5pct':1.0}.get(stress,0.0),
        shape_shift=0.025*stage if stress=='shape_drift' else 0.0)
    if stress=='single_cell_bias':
        volts[:,0]+=0.05
    f=pd.DataFrame({'timestamp':start+pd.to_timedelta(sec,unit='s'),
        'elapsed_s':sec,'segment':stage+1,'chamber_temperature_C':temp,
        'current_A':cur,'charge_Ah_cum':cur*sec/3600,
        'discharge_Ah_cum':0.0,'pack_voltage_V':volts.sum(axis=1),
        'temp_mean_C':temp,'temp_min_C':temp-0.4,'temp_max_C':temp+0.4,
        **{f'cell{j+1}_V':volts[:,j] for j in range(4)}})
    if stress in ('drop_10pct','drop_30pct'):
        fraction=0.1 if stress=='drop_10pct' else 0.3
        keep=rng.random(len(f))>=fraction;keep[0]=keep[-1]=True;f=f.loc[keep].copy()
    rest=f.tail(1).copy();rest['timestamp']=f.timestamp.iloc[-1]+pd.Timedelta(seconds=dt)
    rest['current_A']=0.0
    return pd.concat([f,rest],ignore_index=True)

def main():
    started=time.monotonic();rows=[]
    scenarios=('stable','linear','accelerating','limiting_cell')
    for seed in range(100,120):
        for scenario in scenarios:
            rng=np.random.default_rng(seed+10_000*scenarios.index(scenario))
            q0,ref=measured_c20(capacities(seed,scenario,0),25,rng)
            A=RouteA();B=RouteB()
            base=SimpleNamespace(bol_capacity_Ah=q0,reference_discharge=ref,operation=pd.DataFrame())
            A.fit(base);B.fit(base)
            frames=[]
            for stage in range(4):
                cap=capacities(seed,scenario,stage)
                f=operation(seed,scenario,stage,cap,rng)
                frames.append(f)
                if stage==0: continue
                op=pd.concat(frames,ignore_index=True)
                ds=SimpleNamespace(bol_capacity_Ah=q0,reference_discharge=ref,operation=op)
                label,_=measured_c20(cap,25,rng)
                cutoff=f.timestamp.iloc[-1]+pd.Timedelta(days=1)
                for method,model in [('B0',None),('A',A),('B',B)]:
                    pred=100*q0/102 if model is None else model.estimate_soh(ds,cutoff)
                    diag={} if model is None else model.last_diagnostics
                    rows.append({'run_id':'E2_twoRC_hysteresis_20seeds','evidence':'E2',
                        'seed':seed,'scenario':scenario,'stage':stage,'method':method,
                        'true_C20_Ah':label,'predicted_Ah':pred*102/100,
                        'error_Ah':pred*102/100-label,'true_soh_pp':100*label/102,
                        'predicted_soh_pp':pred,'fallback':diag.get('fallback',True),
                        'updates':diag.get('updates',0),'temperature_C':25 if stage%2==0 else 45})
        print('seed',seed,'seconds',round(time.monotonic()-started,1),flush=True)
    out=TASK/'runs/E2_twoRC_hysteresis_20seeds'
    out.mkdir(parents=True,exist_ok=True)
    df=pd.DataFrame(rows);df.to_csv(out/'predictions.csv',index=False)
    (out/'config.json').write_text(json.dumps({'seeds':list(range(100,120)),'scenarios':scenarios,
        'generator':'two RC modes, hysteresis, nonlinear OCV, independent 5.1 A to 11.2 V C20 target',
        'prediction_methods':['B0','A','B']},indent=2))
    print(df.groupby(['scenario','method']).error_Ah.agg(['count',lambda x:x.abs().mean(),'mean','max']).to_string())

if __name__=='__main__':main()
