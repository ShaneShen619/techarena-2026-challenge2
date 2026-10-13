"""Dual-reference per-cell derivative features, under template_protocol.json."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'src'))
import harness as H
import registration as R
from events import CELLS
from v2 import anchors_by_checkup
from common import bilingual

def smooth_derivative(q,v,width):
    n=max(1,int(round(width/.25)))
    left=(n-1)//2; right=n-1-left
    vs=np.convolve(np.pad(v,(left,right),mode='edge'),np.ones(n)/n,mode='valid')
    return np.gradient(vs,q)

if __name__=='__main__':
    op=H.cut_op(2)
    fc,st,a4=H.tables(op,'real_ck2')
    anc=anchors_by_checkup(fc,H.CK)
    rows=[]; curves=[]
    for j in (0,1):
        q,v,qcc=R.anchor_curve(op,anc[j])
        for cell,c in enumerate(CELLS):
            for width in (1.,2.,3.):
                slope=smooth_derivative(q,v[:,cell],width)
                search=(q>50)&(q<80)
                main=float(q[search][np.argmax(slope[search])])
                top=(q>=main+5)&(q<=qcc-2)
                high=np.nan
                if top.any():
                    i=np.flatnonzero(top)[np.argmax(slope[top])]
                    if slope[i]>=2*np.median(slope[top]):
                        high=float(q[i])
                threshold=.25*float(slope[(q>=0)&(q<=5)].max())
                tail=np.nan
                for i in np.flatnonzero((q>=3)&(q<=20)):
                    if i+4<len(q) and np.all(slope[i:i+5]<=threshold):
                        tail=float(q[i]); break
                rows.append({'anchor':j,'cell':cell+1,'smooth_Ah':width,'main_step_Ah':main,
                             'high_SOC_feature_Ah':high,'low_tail_onset_Ah':tail,'Q_CC_Ah':qcc})
                curves.extend({'anchor':j,'cell':cell+1,'smooth_Ah':width,'q_Ah':float(x),
                               'voltage_V':float(y),'dVdQ_V_per_Ah':float(dv)} for x,y,dv in zip(q,v[:,cell],slope))
    tab=pd.DataFrame(rows)
    tab.to_csv(HERE/'outputs/A_dual_reference_features.csv',index=False)
    pd.DataFrame(curves).to_csv(HERE/'outputs/A_dual_reference_derivatives.csv',index=False)
    robust=[]
    for (j,c),g in tab.groupby(['anchor','cell']):
        for feature in ['main_step_Ah','high_SOC_feature_Ah','low_tail_onset_Ah']:
            finite=g[feature].dropna()
            span=float(finite.max()-finite.min()) if len(finite) else np.nan
            robust.append({'anchor':j,'cell':c,'feature':feature,'available_windows':len(finite),
                           'span_Ah':span,'robust_all_three':bool(len(finite)==3 and span<=1.)})
    robust=pd.DataFrame(robust)
    robust.to_csv(HERE/'outputs/A_dual_reference_robustness.csv',index=False)
    counts=robust.groupby('feature').robust_all_three.sum().to_dict()
    bilingual(HERE/'TEMPLATE_REPORT.md','Dual-reference derivative templates',
      f'''Exposed-exploratory; proxies are not hidden truth. This supplement supplies CK0 (45 C) and first25C (anchor1) templates on a 0.25-Ah grid for every cell and 1/2/3-Ah smoothing. Definitions were frozen in template_protocol.json before this supplement ran; they were not available in the original A pre-registration and never alter its main model.

Robust feature counts out of eight anchor-cell pairs: {counts}. A feature is robust only when all three windows locate it within a 1-Ah span. Missing high-SOC peaks and unstable low tails are reported as unavailable/unreliable. See A_dual_reference_features.csv, A_dual_reference_robustness.csv and the derivative curves. This is measurement diagnosis, not ICA-peak-to-capacity regression.''',
      f'''已曝光探索性研究；代理不是隐藏真值。本补充提供 CK0（45℃）及首个25℃锚点1的逐芯模板：0.25 Ah 网格，1/2/3 Ah 平滑。定义已在本补充运行前写入 template_protocol.json；原 A 协议未包含这些定义，补充不会改变主模型。

八个锚点-电芯组合中的稳健特征数量：{counts}。只有三个窗口都能定位且跨度不超过 1 Ah，才算稳健；不存在的高 SOC 峰和不稳定低端尾段如实标记。详见特征表、稳健性表和导数曲线。本项是测量诊断，不是 ICA 峰位到容量的回归。''')
    print(robust.to_string(index=False))
