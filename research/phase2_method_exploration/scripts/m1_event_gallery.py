"""Render every certified pulse without selecting events by prediction error."""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

ROOT=Path(__file__).resolve().parents[3]
TASK=Path(__file__).resolve().parents[1]
OUT=TASK/'runs/M1_voltage_forecast_v1'
cert=pd.read_csv(TASK/'runs/M1_certification_v2/event_certification.csv',parse_dates=['start','end'])
cert=cert.loc[cert.accepted].sort_values('start')
summary=pd.read_csv(OUT/'event_method_mae.csv')
with PdfPages(OUT/'all_41_certified_pulses.pdf') as book:
    for filename,group in cert.groupby('file',sort=True):
        raw=pd.read_csv(ROOT/'data/operation'/filename,parse_dates=['timestamp'])
        for row in group.itertuples(index=False):
            part=raw.loc[(raw.timestamp>=row.start)&(raw.timestamp<=row.end)&
                         raw.current_A.between(-20.5,-19.5)].copy()
            t=part.timestamp.astype('int64').to_numpy()/1e9
            current=-part.current_A.to_numpy(float)
            q=np.r_[0,np.cumsum((current[1:]+current[:-1])*np.diff(t)/7200)]
            fig,axes=plt.subplots(2,1,figsize=(9,7),sharex=True,height_ratios=(3,1))
            for cell in range(1,5):
                axes[0].plot(q,part[f'cell{cell}_V'].to_numpy(),label=f'cell {cell}',linewidth=1.1)
            axes[0].set_ylabel('Cell voltage (V)')
            axes[0].legend(ncol=4,loc='upper right')
            axes[0].grid(alpha=.2)
            axes[1].plot(q,current,color='black',linewidth=1)
            axes[1].set(xlabel='Integrated discharge charge (Ah)',ylabel='Current magnitude (A)')
            axes[1].grid(alpha=.2)
            fig.suptitle(f'{row.start.isoformat()}  chamber {int(row.chamber_C)} C | '
                         f'{q[-1]:.2f} Ah | pre-rest {row.pre_rest_s/60:.1f} min | '
                         f'post-rest {row.post_rest_s/60:.1f} min',fontsize=11)
            fig.tight_layout()
            book.savefig(fig)
            plt.close(fig)

method_order=['matched_last_shift','last_two_calendar_trend','fixed_ECM','early_dynamic_slope']
fig,ax=plt.subplots(figsize=(9,5))
data=[summary.loc[summary.method==m,'abs_mV'].to_numpy() for m in method_order]
ax.boxplot(data,tick_labels=method_order,showfliers=True)
ax.set_yscale('symlog',linthresh=1)
ax.set_ylabel('Held 2–10 Ah cell-event mean absolute error (mV)')
ax.set_title('Forward voltage prediction, equal first-1-Ah input')
ax.grid(axis='y',alpha=.25)
fig.autofmt_xdate(rotation=15)
fig.tight_layout()
fig.savefig(OUT/'forward_method_comparison.png',dpi=180)
plt.close(fig)
print({'pages':len(cert),'gallery':str(OUT/'all_41_certified_pulses.pdf')})
