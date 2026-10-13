from common import *
def main():
 f=pd.read_csv(TASK/'official_features.csv');d=f[f.budget=='dis_end'].copy()
 d.groupby(['type','m_chamber_T']).agg(events=('event_id','size'),initial_pack_average_V=('c5_raw_V_0','median'),dV30_V=('c5_f3_dV_t30','median'),dV300_V=('c5_f3_dV_t300','median'),early_current_C=('c5_f3_Iearly_C','median'),current_std_C=('c5_f3_Iearly_std_C','median')).to_csv(TASK/'official_type_temperature_summary.csv')
 rows=[]
 for r in d.itertuples():
  change=np.array([getattr(r,f'c{i}_f3_dV_t30') for i in range(1,5)]);start=np.array([getattr(r,f'c{i}_raw_V_0') for i in range(1,5)]);end=np.array([getattr(r,f'c{i}_raw_V_300') for i in range(1,5)])
  rows.append(dict(event_id=r.event_id,type=r.type,available_after=r.available_after,temperature_C=r.m_chamber_T,initial_lowest_observed_cell=int(np.argmin(start)+1),lowest_at300s_cell=int(np.argmin(end)+1),largest30s_drop_cell=int(np.argmin(change)+1),initial_spread_V=float(np.ptp(start)),spread300s_V=float(np.ptp(end)),drop_spread_V=float(np.ptp(change)),meaning='observed voltage rankings, not known capacities/SOC/pack cutoff-limiting cell'))
 pd.DataFrame(rows).to_csv(TASK/'official_cell_order_trajectories.csv',index=False)
 # Four-channel imbalance stress: fixed INTRINSIC Q_i, no assertion fixed usable pack Ah under altered initial states.
 t=np.arange(0,1801,10);out=[]
 for delta in [0,.01,.03,.06]:
  for T in [25,45]:
   voltages=np.array([3.37+offset+.08*(1+.05*i)*np.exp(-t/(300*(1+.1*i)*np.exp(-(T-25)/60))) for i,offset in enumerate([-delta,-delta/3,delta/3,delta])]);st=np.array([stats(v)['Var'] for v in voltages])
   out.append(dict(intrinsic_Q1_Ah=102,intrinsic_Q2_Ah=102,intrinsic_Q3_Ah=102,intrinsic_Q4_Ah=102,initial_voltage_imbalance_V=delta,temperature_C=T,cell_Max_range_V=float(np.ptp(voltages[:,0])),cell_Var_mean=float(st.mean()),cell_Var_range=float(np.ptp(st)),pack_average_Var=float(stats(voltages.mean(axis=0))['Var']),usable_pack_capacity_status='not fixed by intrinsic Q alone; not claimed or scored'))
 pd.DataFrame(out).to_csv(TASK/'independent_four_channel_imbalance_stress.csv',index=False)
if __name__=='__main__':main()
