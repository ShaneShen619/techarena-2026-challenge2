"""Fit witnesses, denser shift audit, exported charts, and reviewable results."""
from __future__ import annotations
import json,sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from experiment import Template,load_events,prepare,fit_cell,prediction,CONFIGS,SGRID,Q0,OUT,TASK,ROOT,selected,design,linear_fit,summarize_profile

def main():
 template=Template();events=load_events();conf=CONFIGS['base'];z=np.load(OUT/'profile_base.npz')
 # Exploratory AFTER the primary fit: compare starts within 15 mV per cell.
 # Use only that CK's previously selected events to compute the matching center.
 matched=[]
 for ck in pd.read_csv(ROOT/'data/checkups/evaluation_points.csv').itertuples(index=False):
  for T in [25,45]:
   inds=selected(events,ck.date,T)
   if len(inds)<2:continue
   pre=np.stack([events[i]['pre_v'] for i in inds]);delta=np.abs(pre-np.median(pre,axis=0)).max(axis=1)
   retained=[i for i,d in zip(inds,delta) if d<=.015]
   if len(retained)<2:continue
   row,_=summarize_profile(template,z['loss'],retained,ck.checkup,T,'exploratory_start_matching_15mV',events)
   row['excluded_starts']='|'.join(events[i]['start'] for i in inds if i not in retained);matched.append(row)
 pd.DataFrame(matched).to_csv(OUT/'exploratory_start_matching.csv',index=False)
 witnesses=[];audit=[];parrows=[];overlays=[]
 for T in [25,45]:
  inds=selected(events,'2025-08-28',T);e=events[inds[-1]];p=prepare(e,conf)
  for capacity in [80.,100.]:
   s=capacity/Q0
   for cell in range(4):
    loss,param=fit_cell(template,p,s,cell,conf)
    pred=prediction(template,p,s,cell,conf,param)
    for k in range(len(p['q'])):
     witnesses.append(dict(T=T,start=e['start'],cell=cell+1,capacity_Ah=capacity,t_s=float(p['t'][k]),q_Ah=float(p['q'][k]),phase=int(p['phase'][k]),actual_V=float(p['y'][k,cell]),predicted_V=float(pred[k])))
    parrows.append(dict(T=T,start=e['start'],cell=cell+1,capacity_Ah=capacity,RMS_mV=float(np.sqrt(loss)*1000),shift_Ah=float(param[0]),bias_mV=float(param[1]*1000),relative_ohmic_mOhm=float(param[2]/20*1000),RP_fast_mOhm=float(param[3]/20*1000),RP_slow_mOhm=float(param[4]/20*1000),initial_mV=float(param[5]*1000)))
  # Dense grid is independent of the original optimizer's warm starts.
  for capacity in [80.,100.]:
   exact=[];dense=[]
   for idx in inds:
    pp=prepare(events[idx],conf);s=capacity/Q0
    for cell in range(4):
     loss,_=fit_cell(template,pp,s,cell,conf);exact.append(loss)
     grid=np.r_[np.arange(0,1.001,.01),np.arange(1.1,10.001,.1)];scores=[]
     for d in grid:
      a,x=design(pp,s,float(d),conf);l,_=linear_fit(a,pp['y'][:,cell]-template.values(x,cell),pp['w'],conf);scores.append(l)
     dense.append(min(scores))
   audit.append(dict(T=T,capacity_Ah=capacity,optimizer_RMS_mV=float(np.sqrt(np.mean(exact))*1000),dense_shift_RMS_mV=float(np.sqrt(np.mean(dense))*1000)))
  local=[e for e in events if e['T']==T]
  for period,subset in [('early3',local[:3]),('late3',local[-3:])]:
   for cell in range(4):
    q=np.arange(0,10.001,.2);curves=np.stack([np.interp(q,e['q_pulse'],e['v_pulse'][:,cell]) for e in subset]);v=curves.mean(axis=0)
    for qi,vi in zip(q,v):overlays.append(dict(T=T,cell=cell+1,period=period,q_Ah=float(qi),voltage_V=float(vi),relative_to_2Ah_mV=float((vi-np.interp(2,q,v))*1000)))
 pd.DataFrame(witnesses).to_csv(OUT/'alternative_capacity_waveforms.csv',index=False)
 pd.DataFrame(parrows).to_csv(OUT/'alternative_capacity_parameters.csv',index=False)
 pd.DataFrame(overlays).to_csv(OUT/'aligned_early_late_curves.csv',index=False)
 (OUT/'dense_optimization_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
 profile=pd.read_csv(OUT/'profile_curves.csv');features=pd.read_csv(OUT/'waveform_features.csv');summary=json.loads((OUT/'summary.json').read_text())
 fig,axes=plt.subplots(2,2,figsize=(13,8.5),constrained_layout=True)
 for T,color in [(25,'#28536b'),(45,'#9c5a2b')]:
  g=features.loc[features['T'].eq(T)]
  g=g.groupby('start',as_index=False).drop_2to10_mV.mean()
  axes[0,0].plot(pd.to_datetime(g.start),g.drop_2to10_mV,'o-',ms=3,label=f'{T} C',color=color)
  g=profile.loc[profile.label.eq('CK7')&profile['T'].eq(T)&profile.configuration.eq('base')].drop_duplicates('capacity_Ah')
  axes[0,1].plot(g.capacity_Ah,g.RMS_mV,label=f'{T} C',color=color)
 axes[0,0].set(title='Observed late-pulse voltage change (four-cell mean)',xlabel='Event date (2025)',ylabel='V(2 Ah) - V(10 Ah) [mV]')
 axes[0,0].tick_params(axis='x',rotation=20);axes[0,0].legend()
 axes[0,1].set(title='CK7: refit nuisance for each candidate capacity',xlabel='Projected reference pack capacity [Ah]',ylabel='Phase-weighted voltage RMS [mV]',ylim=(0,2.))
 axes[0,1].axhline(1.665,color='grey',ls='--',lw=.8,label='45 C minimum + 1 mV');axes[0,1].legend()
 w=pd.DataFrame(witnesses);g=w[(w['T']==45)&(w.cell==3)&(w.phase==1)]
 actual=g[g.capacity_Ah==80];axes[1,0].plot(actual.q_Ah,actual.actual_V,'o',ms=3,color='black',label='Observed cell 3')
 for cap,color in [(80,'#28536b'),(100,'#9c5a2b')]:
  t=g[g.capacity_Ah==cap];axes[1,0].plot(t.q_Ah,t.predicted_V,label=f'{cap} Ah refit',color=color)
 axes[1,0].set(title='Same 2025-08-27 waveform, two capacity explanations',xlabel='Discharged charge [Ah]',ylabel='Cell 3 loaded voltage [V]');axes[1,0].legend()
 methods=summary['forward_voltage_test'];labelmap={'profile_capacity':'Fitted capacity','fixed_CK0_capacity':'Fixed CK0','matched_last_shift':'Matched last event'}
 axes[1,1].bar([labelmap[m['method']] for m in methods],[m['mae_mV'] for m in methods],color='#28536b')
 axes[1,1].set(title='Forward 2-10 Ah prediction: 35 physical pack events',xlabel='Method (pre-rest + first 1 Ah calibration)',ylabel='Mean absolute cell voltage error [mV]')
 for ax in axes.ravel():ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.15)
 fig.suptitle('R02 prototype: good in-sample fit does not identify capacity',fontsize=16)
 fig.supxlabel('Source: official CK0 + operation signals, Jan-Aug 2025 | one pack; CK1-CK7 capacities unavailable',fontsize=10)
 fig.savefig(OUT/'joint_discharge_findings.png',dpi=170);fig.savefig(OUT/'joint_discharge_findings.svg');plt.close(fig)
 print(json.dumps(audit,indent=2))

if __name__=='__main__':main()
