from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
TASK=Path(__file__).resolve().parents[1];O=TASK/'outputs';O.mkdir(exist_ok=True)
c=pd.read_csv(O/'event_coverage_by_ck.csv')
fig,ax=plt.subplots(figsize=(8,4))
ax.plot(c.checkup,c.completed_strict_5p1_events,label='Completed near 5.1 A fragments',marker='o')
ax.plot(c.checkup,c.completed_pulse_20A_events,label='Completed near 20 A pulses',marker='s')
ax.plot(c.checkup,c.strict_current_shape_candidates_min5Ah,label='Qualified >=5 Ah near 5.1 A',marker='x')
ax.set_ylabel('Cumulative completed events');ax.set_xlabel('Checkup prefix');ax.legend(fontsize=8)
fig.tight_layout();fig.savefig(O/'fig_v1_event_coverage.png',dpi=180);plt.close(fig)
m=pd.read_csv(TASK/'runs/V3_R05_D1_20260929_v1/metrics.csv');m=m[m.objective.eq('average')]
fig,ax=plt.subplots(figsize=(8,4))
ax.bar(m.arm,m.macro_mae_pp,label='Macro MAE')
ax.plot(m.arm,m.worst_cell_mae_pp,'ro-',label='Worst-cell MAE')
ax.tick_params(axis='x',rotation=25);ax.set_ylabel('SOH percentage points');ax.legend()
fig.tight_layout();fig.savefig(O/'fig_r05_d1_comparison.png',dpi=180);plt.close(fig)
p=pd.read_csv(TASK/'runs/V2_R02_sensitivity_20260929_v3/paired_profiles.csv')
fig,ax=plt.subplots(figsize=(8,4))
for w in ['plateau','long']:
    z=p[(p.window==w)&(p.case=='same_capacity_hysteresis')&(p.observation=='dense_1mV')&(p.nuisance=='free')]
    ax.plot(z.apparent_axis_Ah,z.data_rmse_mV,label=f'{w}, unchanged capacity + hysteresis')
ax.set_xlabel('Apparent voltage-axis Ah (not reference capacity)');ax.set_ylabel('Data RMSE (mV)');ax.legend(fontsize=8)
fig.tight_layout();fig.savefig(O/'fig_r02_mismatch_profile.png',dpi=180);plt.close(fig)
print('3 figures')
