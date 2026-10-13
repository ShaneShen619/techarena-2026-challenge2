"""Executable mechanism checks, not a hidden-capacity accuracy benchmark."""
import json,sys
from pathlib import Path
import numpy as np

TASK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TASK/'src'))
from experiment import Template,SGRID,CONFIGS,design,filtered_current,fit_cell,prediction,Q0,OUT,selected

def synthetic(template,qmax,s,shift,coef):
 j0=20.4;duration=qmax*3600/j0
 t=np.r_[np.linspace(-600,-10,20),np.linspace(30,duration,80),duration+np.linspace(30,1200,30)]
 phase=np.where(t<0,0,np.where(t<=duration,1,2));q=np.clip(t,0,duration)*j0/3600;j=np.where(phase==1,j0,0)
 h=np.stack([np.where(t<0,0,np.where(t<=duration,j0*(-np.expm1(-np.maximum(t,0)/tau)),j0*(-np.expm1(-duration/tau))*np.exp(-(t-duration)/tau))) for tau in CONFIGS['base']['taus']],axis=1)
 counts=np.bincount(phase);w=np.array([1/np.sqrt(3*counts[ph]) for ph in phase])
 p=dict(q=q,t=t,j=j,h=h,w=w,phase=phase,initial=np.exp(-(t+600)/600))
 a,x=design(p,s,shift,CONFIGS['base'])
 p['y']=np.stack([template.values(x,c)+a@coef for c in range(4)],axis=1)
 return p

def run():
 template=Template();r=template.raw;pack=template.pack
 back=pack.voltage(pack.x,1.)
 err=float(np.max(np.abs(back-r.groupby('discharged_Ah',sort=True).last().voltage_V.to_numpy(float))))
 assert err<1e-12
 assert abs(pack.capacity(1.)-Q0)<1e-7
 assert abs(pack.capacity(.8)-Q0*.8)<1e-7
 # Relative correction MUST vanish under the CK0 reference current/protocol.
 q=np.linspace(0,80,301);t=q*3600/5.1
 p=dict(q=q,t=t,j=np.full(len(q),5.1),h=np.stack([5.1*(-np.expm1(-t/tau)) for tau in CONFIGS['base']['taus']],axis=1),initial=np.zeros(len(q)))
 a,x=design(p,1.,0,CONFIGS['base']);coef=np.array([0,.07,.1,.05,0])
 assert np.max(np.abs(a@coef))<1e-12
 # Events after midnight on the CK date are unavailable at that CK decision.
 fake=[dict(start='2025-02-03T00:00:00',end='2025-02-03T03:00:00',T=45),dict(start='2025-02-08T09:00:00',end='2025-02-08T11:00:00',T=45)]
 assert selected(fake,'2025-02-08',45)==[0]
 results=[]
 for name,qmax,s in [('wide_known_capacity',60.,.90),('shallow_constant_capacity',10.2,1.)]:
  p=synthetic(template,qmax,s,.7,np.array([.008,.04,.03,.04,.015]));loss=[]
  for candidate in SGRID:
   losses=[fit_cell(template,p,float(candidate),cell,CONFIGS['base'])[0] for cell in range(4)]
   loss.append(np.mean(losses))
  rms=np.sqrt(loss)*1000;best=int(np.argmin(rms));allowed=SGRID[rms<=rms[best]+1]
  result=dict(name=name,true_capacity_Ah=Q0*s,best_capacity_Ah=float(Q0*SGRID[best]),RMS_mV=float(rms[best]),
   low_plus1mV_Ah=float(Q0*allowed.min()),high_plus1mV_Ah=float(Q0*allowed.max()),RMS_Q80_mV=float(np.interp(80,Q0*SGRID,rms)),RMS_Q100_mV=float(np.interp(100,Q0*SGRID,rms)))
  if name=='wide_known_capacity':assert abs(SGRID[best]-s)<=.011,result
  results.append(result)
  print(result,flush=True)
  np.savetxt(OUT/f'synthetic_{name}.csv',np.column_stack([SGRID*Q0,rms]),delimiter=',',header='capacity_Ah,RMS_mV',comments='')
 result=dict(CK0_backsubstitution_max_error_V=err,CK0_first_cutoff_Ah=pack.capacity(1.),reference_increment_identity=True,strict_prefix_boundary=True,synthetic_experiments=results)
 (OUT/'science_checks.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))

if __name__=='__main__':run()
