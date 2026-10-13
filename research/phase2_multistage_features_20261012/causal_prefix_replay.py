"""Identify completed full charge/rest from query-visible RAW rows, no future event catalog."""
from common import *
from scipy.integrate import cumulative_trapezoid

def main():
 inputs={p.name:pd.read_csv(p,parse_dates=['timestamp']) for p in sorted((SOURCE/'data/operation').glob('*.csv.gz'))};rows=[];checks=[]
 for point in pd.read_csv(SOURCE/'data/checkups/evaluation_points.csv').itertuples():
  cutoff=pd.Timestamp(point.date);count=0
  for filename,original in inputs.items():
   f=original[original.timestamp<=cutoff].sort_values('timestamp',kind='stable').reset_index(drop=True)
   if len(f)<3:continue
   t=ns(f.timestamp);I=f.current_A.to_numpy();dt=np.r_[0,np.diff(t)];positive=I>.5
   starts=np.flatnonzero(positive&(~np.r_[False,positive[:-1]]|(dt>20)));ends=np.flatnonzero(positive&(~np.r_[positive[1:],False]|np.r_[dt[1:]>20,True]))
   for a,b in zip(starts,ends):
    # End must be confirmed by a visible recorded zero-current step; never an open charge.
    if b+1>=len(f) or abs(I[b+1])>.5 or t[b+1]-t[b]>20:continue
    if t[b]-t[a]<600 or f.pack_voltage_V.iat[b]<13.95:continue
    peak=np.quantile(I[a:b+1],.8)
    if I[b]>.5*peak:continue
    rest=[];k=b+1
    while k<len(f) and abs(I[k])<=.5:
     if rest and t[k]-t[rest[-1]]>20:break
     rest.append(k);k+=1
    if len(rest)<3:continue
    rt=t[rest]-t[rest[0]];charge_t=t[a:b+1]-t[a];q=cumulative_trapezoid(I[a:b+1],charge_t,initial=0)/3600
    for duration in [300,900,1800]:
     if rt.max()<duration:continue
     available=f.timestamp.iat[rest[0]]+pd.Timedelta(seconds=duration)
     if available>cutoff:continue
     r=dict(checkup=point.checkup,query_date=point.date,charge_id='charge_'+f.timestamp.iat[b].isoformat(),charge_start=f.timestamp.iat[a].isoformat(),charge_end=f.timestamp.iat[b].isoformat(),available_after=available.isoformat(),budget='pre'+str(duration),chamber_T=float(f.chamber_temperature_C.iat[b]),file=filename)
     use=rt<=duration
     for c in range(1,6):
      voltage=f[f'cell{c}_V'].to_numpy() if c<5 else f.pack_voltage_V.to_numpy()/4
      r.update({f'c{c}_{kk}':vv for kk,vv in charge_features(charge_t,voltage[a:b+1],I[a:b+1],q,102,control_v=f.pack_voltage_V.iloc[a:b+1].to_numpy()/4).items()})
      r.update({f'c{c}_{kk}':vv for kk,vv in stage_features(rt[use],voltage[np.array(rest)[use]],'f2',10,20).items() if kk.startswith(f'f2_{duration}_')})
     rows.append(r);count+=1
  checks.append(dict(checkup=point.checkup,visible_charge_rest_rows=count,all_availability_before_query=True,no_future_catalog_access=True))
 out=pd.DataFrame(rows);out.to_csv(TASK/'official_charge_rest_causal_prefix_replay.csv',index=False)
 reference=pd.read_csv(TASK/'official_features.csv');matches=[]
 for r in out.itertuples():
  match=reference[(reference.charge_end==r.charge_end)&(reference.budget==r.budget)]
  if len(match):
   duration=int(r.budget[3:]);key=f'c5_f2_{duration}_Var';ok=np.isclose(getattr(r,key),match[key].iat[0],equal_nan=True);matches.append(dict(checkup=r.checkup,charge_end=r.charge_end,budget=r.budget,var_matches_full_inventory=bool(ok)))
 pd.DataFrame(matches).to_csv(TASK/'causal_prefix_inventory_matches.csv',index=False)
 save('causal_prefix_replay_audit.json',{'query_inputs_truncated_before_stage_identification':True,'uses_future_event_ids_or_catalog':False,'source':'raw timestamp/current/voltage only','thresholds':'completed >=600s positive charge, terminal pack>=13.95V, final current<=half80%peak, recorded rest; gap<=20s','prefixes':checks,'matched_inventory_rows':len(matches),'all_matched_variances_equal':all(x['var_matches_full_inventory'] for x in matches),'rows':len(out),'future_capacity_inference':'none'})
 print('causal replay',len(out),'rows; matches',sum(x['var_matches_full_inventory'] for x in matches),'/',len(matches),flush=True)
if __name__=='__main__':main()
