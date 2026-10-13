from pathlib import Path
import hashlib,json,subprocess,sys
sys.dont_write_bytecode=True
import numpy as np
import pandas as pd
TASK=Path(__file__).resolve().parent
WORK=TASK.parents[1]
SOURCE=Path('/Users/shane/Desktop/Arena 阶段 2 官方材料')

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save(name,value):(TASK/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def ns(s):return pd.to_datetime(s).to_numpy(dtype='datetime64[ns]').astype('int64')/1e9

def stats(v):
 v=np.asarray(v,float);n=len(v);mean=float(v.mean());var=float(v.var(ddof=1)) if n>1 else 0.
 if var<1e-16:ske=kur=0.;zero=1
 else:ske=float(np.mean(((v-mean)/np.sqrt(var))**3));kur=float(np.mean(((v-mean)/np.sqrt(var))**4)-3);zero=0
 return dict(Var=var,Ske=ske,Max=float(v.max()),Min=float(v.min()),Mean=mean,Kur=kur,zero_var=zero)

def grid(t,v,duration,dt,max_gap):
 t=np.asarray(t,float);v=np.asarray(v,float)
 ix=np.argsort(t,kind='stable');t=t[ix];v=v[ix]
 keep=np.r_[True,np.diff(t)>0];t=t[keep];v=v[keep]
 if len(t)<3 or t[0]>.1 or t[-1]<duration or np.max(np.diff(t[t<=duration+max_gap]))>max_gap:return None
 return np.interp(np.arange(0,duration+.001,dt),t,v)

def fit_exp(t,v):
 t=np.asarray(t,float);v=np.asarray(v,float);candidates=[60,300,900,1800];scores=[]
 for tau in candidates:
  a=np.c_[np.ones(len(t)),np.exp(-t/tau)];coef=np.linalg.lstsq(a,v,rcond=None)[0]
  scores.append((float(np.mean((a@coef-v)**2)),tau,coef))
 loss,tau,coef=min(scores,key=lambda z:z[0])
 return {'tau_s':tau,'exp_rmse':np.sqrt(loss),'exp_amp':float(coef[1]),'tau_boundary':int(tau in [60,1800])}

def stage_features(t,v,prefix,dt=30,max_gap=45):
 out={}
 for duration in [300,900,1800]:
  a=grid(t,v,duration,dt,max_gap)
  for n in ['Var','Ske','Max','Min','Mean','Kur','zero_var','drop','drift','tau_s','exp_rmse','exp_amp','tau_boundary']:
   out[f'{prefix}_{duration}_{n}']=np.nan
  if a is None:continue
  st=stats(a);st.update(drop=float(a[-1]-a[0]),drift=float((a[-1]-a[-min(11,len(a))])/(min(10,len(a)-1)*dt)))
  st.update(fit_exp(np.arange(len(a))*dt,a))
  out.update({f'{prefix}_{duration}_{k}':v for k,v in st.items()})
 return out

def charge_features(t,v,I,q,nominal,control_v=None):
 out={};peak=np.quantile(I,.8);cc=I>=.95*peak;control_v=v if control_v is None else control_v;cv=(control_v>=np.max(control_v)-.01)&(I<.95*peak)
 out['f1_Qcharge']=float(q.max());out['f1_cv_seconds']=float(np.ptp(t[cv])) if cv.sum()>1 else 0.;out['f1_cv_Ah']=float(np.ptp(q[cv])) if cv.sum()>1 else 0.
 out['f1_cv_tail_C']=float(I[-1]/nominal)
 for fraction in [.5,.1]:
  hit=np.flatnonzero(cv&(I<=fraction*peak));out[f'f1_cv_to_{fraction}_s']=float(t[hit[0]]-t[np.flatnonzero(cv)[0]]) if len(hit) else np.nan
 if cv.sum()>=5:
  st=fit_exp(t[cv]-t[cv][0],I[cv]/nominal);out.update({f'f1_cv_{k}':v for k,v in st.items()})
 for a,b in [(3.35,3.40),(3.40,3.45),(3.45,3.50)]:
  hit_a=np.flatnonzero(v>=a);hit_b=np.flatnonzero(v>=b)
  out[f'f1_dAh_{a}_{b}']=float(q[hit_b[0]]-q[hit_a[0]]) if len(hit_a) and len(hit_b) and hit_b[0]>hit_a[0] else np.nan
 for ah in [2,5,10,20]:out[f'f1_V_Ah{ah}']=float(np.interp(ah,q,v)) if q.max()>=ah and q.min()<=ah else np.nan
 return out

def discharge_features(t,v,j,q,nominal,temperature=None):
 out={}
 for time in [10,30,60,300]:
  out[f'f3_dV_t{time}']=float(np.interp(time,t,v)-v[0]) if t.max()>=time else np.nan
 for ah in [2,5,10]:out[f'f3_dV_Ah{ah}']=float(np.interp(ah,q,v)-v[0]) if q.max()>=ah else np.nan
 out['f3_Rapp_30']=-(out['f3_dV_t30'])/j[0] if j[0]>.5 else np.nan
 # Metadata confined to the first 300s, never full discharge Ah/duration.
 use=t<=300;out['f3_Iearly_C']=float(j[use].mean()/nominal);out['f3_Iearly_std_C']=float(j[use].std()/nominal)
 for time in [0,30,60,120,300]:
  out[f'raw_V_{time}']=float(np.interp(time,t,v)) if t.max()>=time else np.nan
  out[f'raw_P_{time}']=out[f'raw_V_{time}']-v[0]
  out[f'raw_I_C_{time}']=-float(np.interp(time,t,j)/nominal) if t.max()>=time else np.nan
  observed_I=out[f'raw_I_C_{time}']*nominal
  valid=np.isfinite(observed_I) and abs(observed_I)>1e-6
  out[f'raw_PI_{time}']=out[f'raw_P_{time}']/observed_I if valid else 0.
  out[f'raw_zeroI_{time}']=float(not valid)
  if temperature is not None:out[f'raw_T_{time}']=float(np.interp(time,t,temperature)) if t.max()>=time else np.nan
 return out
