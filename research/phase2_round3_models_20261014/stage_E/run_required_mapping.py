"""Causal per-cell maps of the CK0 loaded discharge and first pack cutoff root.

This physical sensitivity calculation is not scored on exposed proxies.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parent
STUDY=HERE.parent
sys.path.insert(0,str(STUDY/'src'))
from common import dump, bilingual
import harness as H
import registration as R
from events import CELLS, ck0_reference_step
from framework.data import load_reference_discharge
from v2 import anchors_by_checkup, month_steps

def inverse_piecewise(q, point, bottom, top):
    return np.where(q<=bottom*point,q/bottom,point+(q-bottom*point)/top)

def curve_interp(x, grid, volts):
    """Keep the measured loaded curve; explicitly allow a short terminal extension."""
    out=np.interp(x,grid,volts)
    tail=grid>=grid[-1]-.05
    slope=np.polyfit(grid[tail]-grid[-1],volts[tail],1)[0]
    extended=x>grid[-1]
    out=np.where(extended,volts[-1]+slope*(x-grid[-1]),out)
    return np.where(x>grid[-1]+.1,np.nan,out)

def root(voltage, qfc):
    x=np.arange(0.,qfc+2.,.01)
    y=voltage(x)
    crossing=np.flatnonzero(np.isfinite(y)&(y<=11.2))
    if not len(crossing):
        return np.nan
    i=int(crossing[0])
    if i==0:
        return 0.
    lo,hi=x[i-1],x[i]
    if not np.isfinite(y[i-1]):
        return np.nan
    for _ in range(40):
        mid=(lo+hi)/2
        if float(voltage(np.array([mid]))[0])<=11.2:
            hi=mid
        else:
            lo=mid
    return float(hi)

def map_voltage(ref, anc, a4, reg, j, smooth, kind, shifts):
    """Compose the CK0/25-C bridge with a visible anchor's charge map."""
    q0=float(anc[0].Q_Ah); qj=float(anc[j].Q_Ah)
    byseg=a4.set_index('segment')
    r0=byseg.loc[anc[0].segment]
    rj=byseg.loc[anc[j].segment]
    d=ref.discharged_Ah.to_numpy(float)
    reference_curves=ref[CELLS].to_numpy(float)
    params=[]
    for c,cell in enumerate(CELLS):
        p0=float(r0[f'bottom_to_step_{cell}'])
        if kind.startswith('A_map') and j>=2 and j in reg:
            r1=byseg.loc[anc[1].segment]
            p1=float(r1[f'bottom_to_step_{cell}'])
            bridge=(p1/p0,(float(anc[1].Q_Ah)-p1)/(q0-p0))
            fit=reg[j][c]
            params.append((p0,bridge,fit['p1'],fit['s_b'],fit['s_t'],0.,0.))
        else:
            pj=float(rj[f'bottom_to_step_{cell}'])
            scale=(pj/p0,(qj-pj)/(q0-p0))
            shift=float(shifts[c]) if kind=='A4_plus_relative_step' else 0.
            params.append((p0,scale,None,None,None,shift,0.))
    def depths(x):
        mapped=[]
        for p0,sc,p1,sb,st,shift,voff in params:
            q=qj-np.asarray(x)+shift
            if p1 is not None:
                q=inverse_piecewise(q,p1,sb,st)
            q=inverse_piecewise(q,p0,sc[0],sc[1])
            mapped.append(q0-q)
        return np.stack(mapped,axis=1)
    def voltage(x):
        dd=depths(x)
        vs=np.stack([curve_interp(dd[:,c],d,reference_curves[:,c]) for c in range(4)],axis=1)
        return vs.sum(axis=1)
    return voltage,depths

if __name__=='__main__':
    ref=load_reference_discharge(H.DATA)
    refstep=ck0_reference_step(ref)
    rel0=np.array([refstep[f'mid_{c}'] for c in CELLS])
    rel0-=rel0.mean()
    base_root=root(lambda x:sum(curve_interp(x,ref.discharged_Ah.to_numpy(float),ref[c].to_numpy(float)) for c in CELLS),100.41)
    rows=[]
    variants={'A_map_V_full':('V','full'),'A_map_dVdQ_full':('dVdQ','full'),
              'A_map_V_bottom':('V','bottom'),'A4_only':None,'A4_plus_relative_step':None}
    for k in range(1,8):
        op=H.cut_op(k)
        fc,steps,a4s=H.tables(op,f'real_ck{k}')
        anc=anchors_by_checkup(fc,H.CK)
        j=max(anc)
        assert j<k and anc[j].t_end<=H.CK[k]
        s=month_steps(steps['main'],anc,j)
        s=s[(s.setpoint_C==45)&s.step_mean.notna()]
        shifts=np.zeros(4)
        if len(s):
            last=s.iloc[-1]
            shifts=np.array([last[f'step_{c}']-last.step_mean for c in CELLS])-rel0
        for smooth in (1.,2.,3.):
            for name,modefit in variants.items():
                reg={}
                if modefit and j>=2:
                    _,reg=R.anchor_registrations(op,fc,a4s[2.],H.CK,*modefit)
                voltage,depths=map_voltage(ref,anc,a4s[smooth],reg,j,smooth,name,shifts)
                qfc=float(anc[j].Q_Ah)
                q=root(voltage,qfc)
                epsilon=q-qfc
                raw_delta=epsilon-H.EPS0
                normalized=epsilon-(base_root-H.QFC[0])
                extension=float(np.maximum(depths(np.array([q]))-ref.discharged_Ah.max(),0.).max()) if np.isfinite(q) else np.nan
                rows.append({'k':k,'state_anchor':j,'state_time':str(anc[j].t_end),'variant':name,'smooth_Ah':smooth,
                             'model_root_Ah':q,'Q_fc_Ah':qfc,'epsilon_Ah':epsilon,
                             'epsilon_minus_eps0_pp':raw_delta/102*100,
                             'CK0_normalized_drift_pp':normalized/102*100,
                             'tail_extension_Ah':extension,'root_found':bool(np.isfinite(q)),
                             'causal_state':True,'physical_status':'diagnostic only; charge/discharge map transfer unvalidated'})
    result=pd.DataFrame(rows)
    result.to_csv(HERE/'outputs/E_required_causal_maps.csv',index=False)
    ranges=result.groupby('k').epsilon_minus_eps0_pp.agg(min='min',max='max').reset_index()
    ranges.to_csv(HERE/'outputs/E_required_causal_ranges.csv',index=False)
    maximum=float(result.epsilon_minus_eps0_pp.abs().max())
    complete=bool(result.root_found.all())
    missing=int((~result.root_found).sum())
    dump(HERE/'outputs/E_required_mapping_summary.json',{'maximum_absolute_epsilon_drift_pp_among_finite_roots':maximum,
         'negligible_under_0_10_pp':complete and maximum<.1,'reference_raw_cell_sum_root_Ah':base_root,
         'finite_roots':int(result.root_found.sum()),'total_roots':len(result),
         'all_roots_found':bool(result.root_found.all()),'all_states_visible_before_cutoff':True,
         'model_voltage_offset':'No voltage offset transferred between charge and discharge; it is a nuisance specific to charge fit.',
         'selection':'no proxy scoring, no replacement; sensitivity diagnostics only'})
    bilingual(HERE/'REQUIRED_MAPPING_REPORT.md','Causal pack-root mapping supplement',
      f'''Exposed-exploratory. This supplement is not scored on proxies and does not validate hidden capacity.

The prescribed per-cell maps were applied to the CK0 loaded discharge. Stage-A maps were composed with a CK0-to-anchor1 A4 bridge; per-cell A4 maps and relative discharge-step offsets provide fallback variants. Every state comes from the last anchor visible before CK_k (anchor k−1), so no post-checkup anchor is used to correct that checkup.

The raw four-cell sum ends at 11.203 V. Its 11.2 V root requires a short, explicitly reported linear tail extension (at most 0.1 Ah); the baseline root is {base_root:.6f} Ah. No absolute IR or polarization term was added. Charge-fit voltage offsets were treated as charge-specific nuisance terms and were not transferred to discharge.

Maximum |model ε−ε0| among finite roots: {maximum:.6f} pp. {missing} of {len(result)} roots are unavailable within the allowed tail extension; the overall drift is therefore inconclusive, not established negligible. The finite range and each per-cell-map root are in E_required_causal_ranges.csv and E_required_causal_maps.csv. This is a physical sensitivity range, not a calibrated interval. Charge-to-discharge transfer, the 45/25-C bridge, map identifiability and start-state confounding remain unvalidated. It cannot support promoting an ε correction without independent evidence.''',
      f'''已曝光探索性研究。本补充不按代理评分，也不验证隐藏容量。

按执行文件要求，把逐芯映射应用于 CK0 带载放电曲线。阶段 A 映射与 CK0→锚点1 的 A4 桥接组合，并提供逐芯 A4 及相对放电台阶偏移作为回退变体。所有状态均来自 CK_k 前最后可见锚点（k−1），没有用检查后的锚点修正该检查点。

原始四芯和末端为 11.203 V，因此首次 11.2 V 根需要明确报告的短尾段线性外延（最多 0.1 Ah）；基准首根为 {base_root:.6f} Ah。没有重复添加绝对 IR 或极化项。充电拟合的电压偏置视为充电特有干扰，没有移植到放电。

可找到的首根中 |模型 ε−ε0| 最大为 {maximum:.6f} pp；{len(result)} 个首根中有 {missing} 个在允许的尾段外延内无法找到，因此整体漂移无定论，不能判定可忽略。逐根和有限范围见 E_required_causal_maps.csv 与 E_required_causal_ranges.csv。这是物理敏感性范围，不是校准区间。充放电映射迁移、45/25℃ 桥接、映射可辨识性和起点混淆仍未验证，不能据此直接提升 ε 修正模型。''')
    print(ranges.to_string(index=False))
    print('Maximum absolute drift:',maximum)
