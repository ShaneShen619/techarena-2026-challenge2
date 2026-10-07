"""Source-traceable publication-quality figures from recorded CSVs."""
from pathlib import Path
import ast
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

ROOT=Path(__file__).resolve().parents[3]
TASK=ROOT/'research/phase2_validation'
OUT=TASK/'outputs/figures'
OUT.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.size':10,'figure.dpi':140,'savefig.dpi':180,
    'axes.spines.top':False,'axes.spines.right':False})

def save(fig,name):
    fig.tight_layout();fig.savefig(OUT/f'{name}.png',bbox_inches='tight');fig.savefig(OUT/f'{name}.pdf',bbox_inches='tight');plt.close(fig)

def main():
    official=pd.read_csv(TASK/'outputs/predictions_official.csv')
    fig,ax=plt.subplots(figsize=(8.0,4.4))
    palette={'A_route_v4':'#007c91','B_route_v3':'#9d4edd','B1_original_ExampleModel':'#ef8354',
        'B2_prefix_total_voltage':'#5a9367','B0_CK0_constant':'#555555'}
    for method,g in official.groupby('method'):
        ax.plot(g.checkup,g.SOH_est_pp,marker='o',label=method.replace('_',' '),color=palette.get(method))
    ax.set_ylabel('Estimated SOH (%)');ax.set_xlabel('Official checkup (CK1–CK7 truth hidden)')
    ax.grid(alpha=.22);ax.legend(fontsize=7,ncol=2)
    save(fig,'official_unlabeled_trajectories')

    p1=pd.read_csv(TASK/'outputs/phase1_crossvalidation_predictions.csv')
    heat=p1.assign(abs_error=lambda d:d.error_pp.abs()).groupby(['cell_id','method']).abs_error.mean().unstack()[['B0','A','B']]
    fig,ax=plt.subplots(figsize=(6.6,4.5));im=ax.imshow(heat.values,cmap='YlOrRd',vmin=0,vmax=max(30,heat.values.max()))
    names=[x.replace('102Ah_','').replace('degC_','°C ').replace('_cell',' c') for x in heat.index]
    ax.set_yticks(range(len(names)),names,fontsize=8);ax.set_xticks(range(3),heat.columns)
    for i in range(heat.shape[0]):
        for j in range(3):ax.text(j,i,f'{heat.iloc[i,j]:.1f}',ha='center',va='center',fontsize=8)
    fig.colorbar(im,ax=ax,label='MAE (SOH percentage points)')
    ax.set_title('Six held-cell development folds; 3 checkpoints per cell')
    save(fig,'phase1_held_cell_mae')

    e2=pd.read_csv(TASK/'runs/E2_twoRC_hysteresis_20seeds/predictions.csv')
    summary=e2.assign(abs_error=lambda d:d.error_Ah.abs()).groupby(['scenario','method']).abs_error.mean().unstack()[['B0','A','B']]
    fig,ax=plt.subplots(figsize=(7.6,4.3));xx=np.arange(len(summary));width=.24
    for j,name in enumerate(summary.columns):ax.bar(xx+(j-1)*width,summary[name],width,label=name)
    ax.set_xticks(xx,summary.index);ax.set_ylabel('Mean absolute error (Ah)');ax.set_title('Independent two-RC + hysteresis simulator; 20 seeds')
    ax.legend();ax.grid(axis='y',alpha=.2)
    save(fig,'synthetic_mechanism_errors')

    stress=pd.read_csv(TASK/'outputs/stress_results.csv')
    st=stress[stress.method.eq('A')].assign(abs_error=lambda d:d.error_Ah.abs()).groupby('stress').abs_error.mean().sort_values()
    fig,ax=plt.subplots(figsize=(7.4,4.6));ax.barh(st.index,st.values,color='#007c91')
    ax.set_xlabel('A mean absolute error (Ah)');ax.set_title('20-seed paired sensor and sampling stress; stage 2')
    ax.grid(axis='x',alpha=.2)
    save(fig,'route_a_stress')

    diag=pd.read_csv(TASK/'runs/official_diagnostics.csv')
    b=diag[(diag.route=='route_b')&(diag.checkup=='CK7')].iloc[0]
    reasons=ast.literal_eval(b.rejections)
    reasons.pop('gap_reinitialization',None)  # diagnostic flag, not a separate rejected episode
    fig,ax=plt.subplots(figsize=(7.3,3.7));keys=list(reasons);vals=[reasons[k] for k in keys]
    ax.barh(keys,vals,color='#9d4edd');ax.set_xlabel('Rejected episode count (CK7 prefix)')
    ax.set_title('Route B capacity gate: no accepted update')
    save(fig,'route_b_official_rejections')

    ev=pd.read_csv(TASK/'runs/official_window_events.csv')
    cell=ev[ev.cell.eq(1)].copy();cell['depth']=np.where(cell.total_Ah>=50,'deep charge','shallow top-up')
    cell['end']=pd.to_datetime(cell['end'])
    fig,ax=plt.subplots(figsize=(7.3,4.0))
    for depth,g in cell.groupby('depth'):
        ax.scatter(g.end,g.q2,label=depth,s=32)
    ax.set_ylabel('Cell 1 partial Ah, 3.36–3.43 V');ax.set_xlabel('Event date')
    ax.set_title('Different charge-depth trajectories require separate references')
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.legend();ax.grid(alpha=.2);fig.autofmt_xdate()
    save(fig,'deep_vs_shallow_event_evidence')
    print('figures:',*[p.name for p in sorted(OUT.glob('*.png'))])

if __name__=='__main__':main()
