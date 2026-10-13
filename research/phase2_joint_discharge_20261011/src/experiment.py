"""R02 prototype: official loaded template, bounded nuisance profiles, no B prior."""
from __future__ import annotations
import hashlib, json, sys, time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import lsq_linear, minimize_scalar
from scipy.integrate import cumulative_trapezoid

TASK=Path(__file__).resolve().parents[1]
ROOT=TASK.parents[1]
OUT=TASK/'outputs'
sys.path.insert(0,str(ROOT/'research/phase1_pack_trend_20261011/src'))
from pack import PackPrototype

Q0=100.41
SGRID=np.round(np.arange(.70,1.051,.01),6)
CELLS=[f'cell{i}_V' for i in range(1,5)]
CONFIGS={
 'base':dict(dmax=10.,bias=.05,taus=(60.,600.),rests=True),
 'tight_SOC':dict(dmax=3.,bias=.05,taus=(60.,600.),rests=True),
 'wide_SOC':dict(dmax=20.,bias=.05,taus=(60.,600.),rests=True),
 'tight_bias':dict(dmax=10.,bias=.01,taus=(60.,600.),rests=True),
 'wide_bias':dict(dmax=10.,bias=.10,taus=(60.,600.),rests=True),
 'fast_RC':dict(dmax=10.,bias=.05,taus=(30.,300.),rests=True),
 'slow_RC':dict(dmax=10.,bias=.05,taus=(120.,1200.),rests=True),
 'pulse_only':dict(dmax=10.,bias=.05,taus=(60.,600.),rests=False),
}

class Template:
 def __init__(self):
  released=pd.read_csv(ROOT/'data/checkups/checkup_capacities_released.csv')
  assert list(released.checkup)==['CK0'] and float(released.capacity_Ah.iloc[0])==Q0
  self.raw=pd.read_csv(ROOT/'data/checkups/CK0_reference_discharge.csv.gz')
  self.pack=PackPrototype(self.raw)
  r=self.raw.copy();r['bin']=(r.discharged_Ah/self.pack.axis_factor/.02).round().astype(int)
  f=r.groupby('bin',sort=True)[CELLS].median()
  self.x=f.index.to_numpy(float)*.02
  self.v=f.to_numpy(float)
 def values(self,x,cell):
  if np.min(x)<-1e-9 or np.max(x)>self.x[-1]:raise ValueError('template domain')
  return np.interp(x,self.x,self.v[:,cell])

def rest_indices(raw,index,step):
 ids=[];last=None
 while 0<=index<len(raw) and abs(raw.current_A.iat[index])<=.5:
  if last is not None and not 0<abs((raw.timestamp.iat[index]-raw.timestamp.iat[last]).total_seconds())<=20:break
  ids.append(index);last=index;index+=step
 return sorted(ids)

def load_events():
 cat=pd.read_csv(ROOT/'research/phase2_method_exploration/outputs/event_catalog.csv',parse_dates=['event_start','event_end'])
 cat=cat.loc[cat.quality_status.eq('certified')&cat.before_CK7].sort_values('event_start')
 events=[];audit=[]
 for file,group in cat.groupby('source_file',sort=True):
  raw=pd.read_csv(ROOT/'data/operation'/file,parse_dates=['timestamp'])
  for row in group.itertuples(index=False):
   loaded=raw.current_A.between(-20.5,-19.5)
   first=int(np.flatnonzero(raw.timestamp.eq(row.event_start)&loaded)[0]);last=int(np.flatnonzero(raw.timestamp.eq(row.event_end)&loaded)[-1])
   pulse=raw.iloc[first:last+1];pre=raw.iloc[rest_indices(raw,first-1,-1)];post=raw.iloc[rest_indices(raw,last+1,1)]
   tp=(pulse.timestamp-row.event_start).dt.total_seconds().to_numpy(float)
   j=-pulse.current_A.to_numpy(float);qp=cumulative_trapezoid(j,tp,initial=0)/3600
   pre_s=float((pre.timestamp.iat[-1]-pre.timestamp.iat[0]).total_seconds())
   post_s=float((post.timestamp.iat[-1]-post.timestamp.iat[0]).total_seconds())
   counter=float(pulse.charge_Ah_cum.iat[-1]+pulse.discharge_Ah_cum.iat[-1]-pulse.charge_Ah_cum.iat[0]-pulse.discharge_Ah_cum.iat[0])
   temp_span=float(pulse.temp_mean_C.max()-pulse.temp_mean_C.min())
   gates=dict(current=bool(pulse.current_A.between(-20.5,-19.5).all()),continuous=bool(((np.diff(tp)>0)&(np.diff(tp)<=20)).all()),
    duration=1700<=tp[-1]<=1900,pre_rest=pre_s>=1500,post_rest=post_s>=1500,counter=abs(counter-qp[-1])<=.2,temp=temp_span<=2)
   charge_end=raw.iloc[pre.index[0]-1]
   gates['prior_charge_end']=bool(charge_end.current_A>5 and charge_end.pack_voltage_V>=13.90)
   audit.append(dict(start=row.event_start.isoformat(),file=file,T=row.temperature_C,actual_T_C=float(pulse.temp_mean_C.mean()),actual_T_span_C=temp_span,
    q_Ah=float(qp[-1]),current_A=float(j.mean()),pre_s=pre_s,post_s=post_s,counter_sum_Ah=counter,
    named_discharge_Ah=float(pulse.discharge_Ah_cum.iat[-1]-pulse.discharge_Ah_cum.iat[0]),pack_sum_median_mV=float((pulse.pack_voltage_V-pulse[CELLS].sum(axis=1)).median()*1000),passed=all(gates.values()),**gates))
   if not all(gates.values()):continue
   selpre=pre.loc[pre.timestamp>=row.event_start-pd.Timedelta(seconds=600)]
   selpost=post.loc[post.timestamp<=row.event_end+pd.Timedelta(seconds=1200)]
   chain=pd.concat([selpre,pulse,selpost])
   t=(chain.timestamp-row.event_start).dt.total_seconds().to_numpy(float)
   q=np.interp(t,tp,qp,left=0,right=qp[-1])
   phase=np.where(t<0,0,np.where(t<=tp[-1],1,2))
   # Select every ~30 s; omit stale first step sample and unresolved 0--20 s switches.
   keep=np.zeros(len(chain),bool)
   for ph in range(3):
    inds=np.flatnonzero(phase==ph)[::3]
    keep[inds]=True
   keep&=~((t>=0)&(t<20));keep&=~((t>tp[-1])&(t<tp[-1]+20))
   events.append(dict(start=row.event_start.isoformat(),end=(row.event_end+pd.Timedelta(seconds=post_s+10)).isoformat(),T=int(row.temperature_C),file=file,
    t_full=t,j_full=-chain.current_A.to_numpy(float),keep=keep,t=t[keep],q=q[keep],phase=phase[keep],y=chain[CELLS].to_numpy(float)[keep],
    q_pulse=qp,v_pulse=pulse[CELLS].to_numpy(float),t_pulse=tp,pre_v=pre[CELLS].to_numpy(float)[-1],q_total=float(qp[-1])))
  print('raw audit',file,flush=True)
 events.sort(key=lambda e:e['start'])
 pd.DataFrame(audit).to_csv(OUT/'raw_event_audit.csv',index=False)
 assert len(events)==39, f'{len(events)} qualified, revise only with disclosed exclusions'
 return events

def filtered_current(t,j,tau):
 h=np.zeros(len(t))
 for k in range(1,len(t)):
  decay=np.exp(-(t[k]-t[k-1])/tau)
  h[k]=decay*h[k-1]+(1-decay)*j[k-1]
 return h

def prepare(e,conf,mask=None):
 keep=e['keep']
 use=np.ones(len(e['q']),bool) if conf['rests'] else e['phase']==1
 if mask is not None:use&=mask
 t=e['t'][use];j=e['j_full'][keep][use];q=e['q'][use];phase=e['phase'][use]
 h=np.stack([filtered_current(e['t_full'],e['j_full'],tau)[keep][use] for tau in conf['taus']],axis=1)
 counts=np.bincount(phase,minlength=3);nphase=int((counts>0).sum())
 w=np.array([1/np.sqrt(nphase*counts[ph]) for ph in phase])
 return dict(t=t,j=j,q=q,h=h,w=w,y=e['y'][use],phase=phase,use=use,
  initial=np.exp(-(t-e['t_full'][0])/600))

def design(p,s,d,conf):
 x=p['q']/s+d
 href=np.stack([5.1*(-np.expm1(-3600*x/(5.1*tau))) for tau in conf['taus']],axis=1)
 return np.column_stack([np.ones(len(x)),-(p['j']-5.1)/20,-(p['h']-href)/20,p['initial']]),x

def linear_fit(a,y,w,conf):
 aw=a*w[:,None];yw=y*w
 low=np.array([-conf['bias'],0,0,0,-.1]);high=np.array([conf['bias'],.3,.3,.3,.1])
 coef=np.linalg.lstsq(aw,yw,rcond=None)[0]
 if np.any(coef<low) or np.any(coef>high):
  coef=lsq_linear(aw,yw,bounds=(low,high),method='bvls',tol=1e-9,max_iter=40).x
 residual=(a@coef-y)*w
 return float(residual@residual),coef

def fit_cell(template,p,s,cell,conf,warm=None):
 def calc(d):
  a,x=design(p,s,d,conf)
  err,coef=linear_fit(a,p['y'][:,cell]-template.values(x,cell),p['w'],conf)
  return err,coef
 grid=np.unique(np.r_[0,.03,.1,.3,.7,1.5,3.,5.,conf['dmax'], ([] if warm is None else [warm])])
 grid=grid[(grid>=0)&(grid<=conf['dmax'])]
 scores=np.array([calc(d)[0] for d in grid]);best=int(scores.argmin());d=float(grid[best]);loss=float(scores[best])
 # Two basins reduce sensitivity to flat/non-monotone template plateaus.
 for idx in np.argsort(scores)[:2]:
  lo=float(grid[max(0,idx-1)]);hi=float(grid[min(len(grid)-1,idx+1)])
  if hi-lo>.0001:
   result=minimize_scalar(lambda z:calc(z)[0],bounds=(lo,hi),method='bounded',options={'xatol':.003,'maxiter':24})
   if result.fun<loss:d=float(result.x);loss=float(result.fun)
 loss,coef=calc(d)
 return loss,np.r_[d,coef]

def prediction(template,p,s,cell,conf,param):
 a,x=design(p,s,float(param[0]),conf)
 return template.values(x,cell)+a@param[1:]

def profile_events(template,events,conf,name):
 loss=np.zeros((len(SGRID),len(events),4));param=np.zeros((len(SGRID),len(events),4,6))
 for ei,e in enumerate(events):
  p=prepare(e,conf);warm=[None]*4
  for si,s in enumerate(SGRID):
   for cell in range(4):
    loss[si,ei,cell],param[si,ei,cell]=fit_cell(template,p,s,cell,conf,warm[cell]);warm[cell]=param[si,ei,cell,0]
  print('profile',name,ei+1,len(events),e['start'],flush=True)
 np.savez_compressed(OUT/f'profile_{name}.npz',s=SGRID,loss=loss,param=param,event_starts=np.array([e['start'] for e in events]))
 return loss,param

def selected(events,date,T):
 t=pd.Timestamp(date)
 return [i for i,e in enumerate(events) if e['T']==T and pd.Timestamp(e['end'])<t and pd.Timestamp(e['start'])>=t-pd.Timedelta(days=60)][-4:]

def summarize_profile(template,loss,indices,label,T,confname,events):
 rms=np.sqrt(loss[:,indices,:].mean(axis=(1,2)))*1000
 best=int(rms.argmin());caps=np.array([template.pack.capacity(s) for s in SGRID])
 row=dict(label=label,T=T,configuration=confname,n_events=len(indices),first_event=events[indices[0]]['start'],last_event_end=events[indices[-1]]['end'],
  best_capacity_Ah=float(caps[best]),best_s=float(SGRID[best]),best_RMS_mV=float(rms[best]),boundary=best in [0,len(SGRID)-1],
  RMS_Q80_mV=float(np.interp(80,caps,rms)),RMS_Q100_mV=float(np.interp(100,caps,rms)))
 for tol in [.5,1.,2.]:
  allowed=caps[rms<=rms[best]+tol];tag=str(tol).replace('.','p')
  row[f'low_{tag}_Ah']=float(allowed.min());row[f'high_{tag}_Ah']=float(allowed.max());row[f'width_{tag}_Ah']=float(allowed.max()-allowed.min())
 row['profile_gate']=bool(row['width_1p0_Ah']<=5 and not row['boundary'])
 return row,[dict(label=label,T=T,configuration=confname,capacity_Ah=float(q),RMS_mV=float(v)) for q,v in zip(caps,rms)]

def waveform_changes(events):
 rows=[]
 for e in events:
  for cell in range(4):
   v=e['v_pulse'][:,cell];q=e['q_pulse']
   rows.append(dict(start=e['start'],T=e['T'],cell=cell+1,v_pre_V=float(e['pre_v'][cell]),
    drop_2to10_mV=float((np.interp(2,q,v)-np.interp(10,q,v))*1000),drop_1to10_mV=float((np.interp(1,q,v)-np.interp(10,q,v))*1000),
    v2_V=float(np.interp(2,q,v)),v10_V=float(np.interp(10,q,v)),apparent_30s_mOhm=float((e['pre_v'][cell]-np.interp(30,e['t_pulse'],v))/20.4*1000)))
 f=pd.DataFrame(rows);f.to_csv(OUT/'waveform_features.csv',index=False)
 summary=[]
 for T,g in f.groupby('T'):
  starts=sorted(g.start.unique());early=g[g.start.isin(starts[:3])];late=g[g.start.isin(starts[-3:])]
  summary.append(dict(T=int(T),events=len(starts),early_3_drop_2to10_mV=float(early.drop_2to10_mV.mean()),late_3_drop_2to10_mV=float(late.drop_2to10_mV.mean()),
   change_drop_2to10_mV=float(late.drop_2to10_mV.mean()-early.drop_2to10_mV.mean()),early_3_R30_mOhm=float(early.apparent_30s_mOhm.mean()),late_3_R30_mOhm=float(late.apparent_30s_mOhm.mean())))
 return summary

def forward_test(template,events,base_loss):
 rows=[]
 for ei,e in enumerate(events):
  history=[k for k,old in enumerate(events[:ei]) if old['T']==e['T'] and pd.Timestamp(old['end'])<pd.Timestamp(e['start']) and pd.Timestamp(old['start'])>=pd.Timestamp(e['start'])-pd.Timedelta(days=60)][-4:]
  if len(history)<2:continue
  si=int(base_loss[:,history,:].mean(axis=(1,2)).argmin());estimated=float(SGRID[si]);conf=CONFIGS['base']
  calibration=(e['phase']==0)|((e['phase']==1)&(e['q']<=1))
  p=prepare(e,conf,calibration);target=prepare(e,conf,(e['phase']==1)&(e['q']>=2)&(e['q']<=10))
  last=events[history[-1]]
  for cell in range(4):
   for name,s in [('profile_capacity',estimated),('fixed_CK0_capacity',1.)]:
    _,par=fit_cell(template,p,s,cell,conf)
    pred=prediction(template,target,s,cell,conf,par);error=(pred-target['y'][:,cell])*1000
    rows.append(dict(start=e['start'],T=e['T'],cell=cell+1,method=name,history_events=len(history),capacity_input_Ah=Q0*s,mae_mV=float(np.mean(np.abs(error))),RMS_mV=float(np.sqrt(np.mean(error**2)))))
   q=e['q_pulse'];v=e['v_pulse'][:,cell];old=np.interp(q,last['q_pulse'],last['v_pulse'][:,cell]);observe=(q>=.2)&(q<=1);shift=np.median(v[observe]-old[observe])
   pred=np.interp(target['q'],q,old+shift);error=(pred-target['y'][:,cell])*1000
   rows.append(dict(start=e['start'],T=e['T'],cell=cell+1,method='matched_last_shift',history_events=len(history),capacity_input_Ah=np.nan,mae_mV=float(np.mean(np.abs(error))),RMS_mV=float(np.sqrt(np.mean(error**2)))))
  print('forward',e['start'],flush=True)
 f=pd.DataFrame(rows);f.to_csv(OUT/'forward_voltage_metrics.csv',index=False)
 ev=f.groupby(['start','T','method'],as_index=False).agg(mae_mV=('mae_mV','mean'),RMS_mV=('RMS_mV','mean'))
 ev.to_csv(OUT/'forward_pack_event_metrics.csv',index=False)
 return [dict(method=name,n_pack_events=len(g),mae_mV=float(g.mae_mV.mean()),RMS_mV=float(g.RMS_mV.mean())) for name,g in ev.groupby('method')]

def main():
 template=Template();events=load_events();changes=waveform_changes(events)
 basepath=OUT/'profile_base.npz'
 if basepath.exists():
  z=np.load(basepath);loss=z['loss'];params=z['param'];assert list(z['event_starts'])==[e['start'] for e in events]
 else:loss,params=profile_events(template,events,CONFIGS['base'],'base')
 dates=pd.read_csv(ROOT/'data/checkups/evaluation_points.csv');summaries=[];curves=[]
 for ck in dates.itertuples(index=False):
  if ck.checkup=='CK0':continue
  for T in [25,45]:
   inds=selected(events,ck.date,T)
   if len(inds)<2:continue
   row,curve=summarize_profile(template,loss,inds,ck.checkup,T,'base',events);summaries.append(row);curves+=curve
 pd.DataFrame(summaries).to_csv(OUT/'checkup_profiles.csv',index=False)
 sensitivity=[];lastdate=str(dates.iloc[-1].date)
 selected7=sorted(set(selected(events,lastdate,25)+selected(events,lastdate,45)))
 subset=[events[i] for i in selected7]
 for name,conf in CONFIGS.items():
  if name=='base':l=loss[:,selected7,:]
  else:
   cache=OUT/f'profile_{name}.npz'
   if cache.exists():l=np.load(cache)['loss']
   else:l,_=profile_events(template,subset,conf,name)
  for T in [25,45]:
   inds=[i for i,e in enumerate(subset) if e['T']==T]
   if len(inds)<2:continue
   row,curve=summarize_profile(template,l,inds,'CK7',T,name,subset);sensitivity.append(row);curves+=curve
 pd.DataFrame(sensitivity).to_csv(OUT/'CK7_sensitivity.csv',index=False)
 pd.DataFrame(curves).to_csv(OUT/'profile_curves.csv',index=False)
 forward=forward_test(template,events,loss)
 gate=[]
 for T in [25,45]:
  sub=[r for r in sensitivity if r['T']==T];spread=max(r['best_capacity_Ah'] for r in sub)-min(r['best_capacity_Ah'] for r in sub)
  base=next(r for r in sub if r['configuration']=='base')
  gate.append(dict(T=T,base_gate=base['profile_gate'],best_capacity_spread_Ah=spread,accept=bool(base['profile_gate'] and spread<=2)))
 result=dict(date='2026-10-11',physical_packs=1,qualified_events=len(events),anchor_capacity_Ah=Q0,capacity_truth_available=['CK0'],
  input_scope='CK0 loaded curve and official raw I/V/T; no B aging parameters, no hidden capacity labels',waveform_changes=changes,forward_voltage_test=forward,CK7_update_gates=gate,
  limitations=['Voltage validation is not capacity validation','RC plus loaded-template deembedding is a prototype assumption; no independent OCV','Profile ranges are tolerance sensitivity sets, not confidence intervals','Four cells share one physical event','Projection assumes matched full-charge reference state; operating nuisance is not carried to reference cutoff'])
 (OUT/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 paths=[ROOT/'data/checkups/CK0_reference_discharge.csv.gz',ROOT/'data/checkups/checkup_capacities_released.csv',ROOT/'data/checkups/evaluation_points.csv',ROOT/'research/phase2_method_exploration/outputs/event_catalog.csv',TASK/'protocol.md',Path(__file__),*sorted((ROOT/'data/operation').glob('*.csv.gz'))]
 provenance=[dict(path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths]
 (OUT/'provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
