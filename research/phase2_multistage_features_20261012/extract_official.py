"""Official chain features with explicit stage availability and no capacity labels."""
from common import *
from scipy.integrate import cumulative_trapezoid

def main():
 catalog=pd.read_csv(SOURCE/'research/charge_capacity_review_20261006/operating_events.csv')
 candidates=catalog[catalog.kind.isin(['scheduled_pulse','long_dynamic_discharge'])].copy()
 candidates=candidates[(candidates.kind=='scheduled_pulse')|candidates.Q_Ah.between(32.7,33)]
 rows=[];registry=[];inputs=[];past_charge_Ah=0.
 for file in sorted(candidates.file.unique()):
  path=SOURCE/'data/operation'/file;raw=pd.read_csv(path,parse_dates=['timestamp']).sort_values('timestamp',kind='stable').reset_index(drop=True)
  t=ns(raw.timestamp);I=raw.current_A.to_numpy();V=raw[[f'cell{i}_V' for i in range(1,5)]].to_numpy();temp=raw.temp_mean_C.to_numpy();pack=raw.pack_voltage_V.to_numpy()/4
  inputs.append(dict(path=str(path),sha256=sha(path)))
  sample_dt=np.r_[0,np.diff(t)];sample_dt[(sample_dt<0)|(sample_dt>20)]=0
  cumulative_charge=np.cumsum(np.maximum(I,0)*sample_dt)/3600
  for event in candidates[candidates.file==file].itertuples():
   a=int(raw.timestamp.searchsorted(pd.Timestamp(event.t_start)));b=int(raw.timestamp.searchsorted(pd.Timestamp(event.t_end)))
   negative=np.flatnonzero(I[a:b+1]<-.5)+a
   if not len(negative):continue
   a,b=int(negative[0]),int(negative[-1])
   tt=t[a:b+1]-t[a];j=-I[a:b+1];q=cumulative_trapezoid(j,tt,initial=0)/3600
   qualified=bool(np.min(j)>.5 and np.max(np.diff(tt))<=20 and abs(q[-1]-event.Q_Ah)<.05)
   typ='standard' if event.kind=='scheduled_pulse' else 'wide33'
   eid=f'{typ}_{raw.timestamp.iat[a].isoformat()}'
   pre=[];k=a-1
   while k>=0 and abs(I[k])<=.5:
    if pre and t[pre[-1]]-t[k]>20:break
    pre.append(k);k-=1
   pre=np.array(sorted(pre),int)
   post=[];k=b+1
   while k<len(t) and abs(I[k])<=.5:
    if post and t[k]-t[post[-1]]>20:break
    post.append(k);k+=1
   post=np.array(post,int)
   charging=catalog[(catalog.file==file)&(catalog.kind=='full_charge')&(catalog.t_end<=event.t_start)]
   charge=None
   if typ=='standard' and len(charging):
    cr=charging.iloc[-1];ca=int(raw.timestamp.searchsorted(pd.Timestamp(cr.t_start)));cb=int(raw.timestamp.searchsorted(pd.Timestamp(cr.t_end)))
    positive=np.flatnonzero(I[ca:cb+1]>.001)+ca
    if len(positive):ca,cb=int(positive[0]),int(positive[-1])
    if len(positive) and t[a]-t[cb]<=7200:charge=(ca,cb)
   registry.append(dict(event_id=eid,type=typ,start=raw.timestamp.iat[a].isoformat(),end=raw.timestamp.iat[b].isoformat(),Q_Ah=float(q[-1]),qualified=qualified,
    charge_paired=charge is not None,pre_rest_s=float(np.ptp(t[pre])) if len(pre) else 0,post_rest_s=float(np.ptp(t[post])) if len(post) else 0,
    chamber_T=int(event.setpoint_C),max_gap_s=float(np.diff(tt).max()),file=file))
   pt=t[pre]-t[pre[0]] if len(pre) else np.array([]);at=t[post]-t[post[0]] if len(post) else np.array([])
   base=dict(event_id=eid,type=typ,entity='official_pack',chemistry='LFP',nominal_Ah=102,
    event_start=raw.timestamp.iat[a].isoformat(),
    charge_start=raw.timestamp.iat[charge[0]].isoformat() if charge else None,charge_end=raw.timestamp.iat[charge[1]].isoformat() if charge else None,m_age_days=float((raw.timestamp.iat[a]-pd.Timestamp('2025-01-14')).total_seconds()/86400),
    m_chamber_T=int(event.setpoint_C),m_actual_T=float(temp[a:b+1].mean()),label_Ah=np.nan,label_scope='unlabelled official group')
   cfeatures={};mcharge={}
   if charge:
    ca,cb=charge;ct=t[ca:cb+1]-t[ca];ci=I[ca:cb+1];cq=cumulative_trapezoid(ci,ct,initial=0)/3600
    mcharge=dict(m_charge_C=float(np.quantile(ci,.8)/102),m_charge_duration_s=float(ct[-1]),m_charge_start_V=float(pack[ca]),m_charge_end_V=float(pack[cb]))
    for c in range(5):
     vv=V[ca:cb+1,c] if c<4 else pack[ca:cb+1]
     one=charge_features(ct,vv,ci,cq,102,control_v=pack[ca:cb+1]);cfeatures.update({f'c{c+1}_{k}':v for k,v in one.items()})
   for budget in ['pre300','pre900','pre1800','dis_end','post300','post900','post1800']:
    if not budget.startswith('pre') and not qualified:continue
    if budget.startswith('pre'):
     duration=int(budget[3:]);availability=raw.timestamp.iat[int(pre[0])]+pd.Timedelta(seconds=duration) if len(pre) else raw.timestamp.iat[a]
     if not len(pre) or pt.max()<duration:continue
     if not charge:continue
    elif budget=='dis_end':duration=1800;availability=raw.timestamp.iat[b]
    else:
     duration=int(budget[4:]);availability=raw.timestamp.iat[int(post[0])]+pd.Timedelta(seconds=duration) if len(post) else raw.timestamp.iat[b]
     if not len(post) or at.max()<duration:continue
    r={**base,**mcharge,**cfeatures,'budget':budget,'available_after':availability.isoformat(),
       'm_pre_rest_s':float(min(pt.max(),duration if budget.startswith('pre') else 1800)) if len(pt) else 0,'m_post_rest_s':float(duration) if budget.startswith('post') else np.nan}
    r['m_cumulative_charge_Ah']=float(past_charge_Ah+cumulative_charge[np.flatnonzero(t<=availability.value/1e9)[-1]])
    r['m_age_days']=float((availability-pd.Timestamp('2025-01-14')).total_seconds()/86400)
    visible=(raw.timestamp<=availability)&(raw.timestamp>=raw.timestamp.iat[charge[0] if charge else a])
    r['m_actual_T']=float(temp[visible].mean()) if visible.any() else float(temp[a])
    pre_duration=duration if budget.startswith('pre') else 1800
    for c in range(5):
     pre_v=V[pre,c] if c<4 else pack[pre];post_v=V[post,c] if c<4 else pack[post];dis_v=V[a:b+1,c] if c<4 else pack[a:b+1]
     if len(pre):r.update({f'c{c+1}_{k}':v for k,v in stage_features(pt[pt<=pre_duration],pre_v[pt<=pre_duration],'f2',10,20).items() if not k.startswith(('f2_900','f2_1800')) or pre_duration>=int(k.split('_')[1])})
     if not budget.startswith('pre'):r.update({f'c{c+1}_{k}':v for k,v in discharge_features(tt,dis_v,j,q,102).items()})
     if budget.startswith('post'):r.update({f'c{c+1}_{k}':v for k,v in stage_features(at[at<=duration],post_v[at<=duration],'f4',10,20).items()})
    for suffix in ['f2_300_Var','f2_1800_Var','f2_1800_Max','f3_dV_t30','f3_dV_Ah10','f4_1800_drop']:
     values=np.array([r.get(f'c{c+1}_{suffix}',np.nan) for c in range(4)])
     if np.isfinite(values).all():r[f'f5_{suffix}_mean']=float(values.mean());r[f'f5_{suffix}_std']=float(values.std());r[f'f5_{suffix}_range']=float(np.ptp(values))
    if not budget.startswith('pre'):
     for time in [0,30,60,120,300]:r[f'raw_T_{time}']=float(np.interp(time,tt,temp[a:b+1])) if tt.max()>=time else np.nan
    if charge:
     for cc in range(4):
      r[f'quality_cell{cc+1}_charge_end_V']=float(V[charge[1],cc]);r[f'quality_cell{cc+1}_charge_start_V']=float(V[charge[0],cc])
     r['quality_charge_end_cell_range_V']=float(np.ptp(V[charge[1]]))
    r['quality_pack_sum_residual_mV']=float(abs(raw.pack_voltage_V[visible].to_numpy()-V[visible].sum(axis=1)).mean()*1000)
    rows.append(r)
  past_charge_Ah+=float(cumulative_charge[-1])
  print('official',file,flush=True)
 pd.DataFrame(rows).to_csv(TASK/'official_features.csv',index=False);pd.DataFrame(registry).to_csv(TASK/'official_registry.csv',index=False)
 save('official_input_manifest.json',inputs)
 f=pd.DataFrame(rows);prefix=[]
 for ck in pd.read_csv(SOURCE/'data/checkups/evaluation_points.csv').itertuples():
  p=f[f.available_after<=pd.Timestamp(ck.date).isoformat()]
  prefix.append(dict(checkup=ck.checkup,date=ck.date,available_feature_rows=len(p),available_events=p.event_id.nunique(),
   paired_CK0_feature=False,capacity_label_released=ck.checkup=='CK0',pack_capacity_status='UNVERIFIED',new_SOH_estimate=None))
 save('official_prefix_availability.json',prefix)

if __name__=='__main__':main()
