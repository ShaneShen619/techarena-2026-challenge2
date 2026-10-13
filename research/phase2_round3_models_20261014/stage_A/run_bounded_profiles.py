"""Unscored bounded-voltage, three-parameter profile audit of anchor maps."""
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

if __name__=='__main__':
    op=H.cut_op(7)
    fc,_,a4=H.tables(op,'real_ck7')
    anc=anchors_by_checkup(fc,H.CK)
    reference=R.anchor_curve(op,anc[1])
    ref_a4=a4[2.].set_index('segment').loc[anc[1].segment]
    original=pd.read_csv(HERE/'outputs/A_registration.csv')
    original=original[(original['mode']=='V')&(original['fit']=='full')]
    profiles=[]; fits=[]
    for j in range(2,7):
        target=R.anchor_curve(op,anc[j])
        for cell,c in enumerate(CELLS):
            prior=original[(original.anchor==j)&(original.cell==cell+1)].iloc[0]
            cb=np.unique(np.r_[np.arange(.94,1.04001,.002),np.arange(prior.s_b-.004,prior.s_b+.00401,.0002)])
            ct=np.unique(np.r_[np.arange(.80,1.05001,.005),np.arange(prior.s_t-.01,prior.s_t+.01001,.0005)])
            cb=cb[(cb>=.94)&(cb<=1.04)];ct=ct[(ct>=.80)&(ct<=1.05)]
            sb,st=np.meshgrid(cb,ct,indexing='ij')
            p1=float(ref_a4[f'bottom_to_step_{c}'])
            select=(reference[0]>=3)&(reference[0]<=reference[2]-1)
            q=reference[0][select][None,:]
            mapped=np.where(q<=p1,sb.ravel()[:,None]*q,sb.ravel()[:,None]*p1+st.ravel()[:,None]*(q-p1))
            residual=np.interp(mapped,target[0],target[1][:,cell])-reference[1][select,cell][None,:]
            residual[mapped>target[2]-.5]=np.nan
            mean=np.nanmean(residual,axis=1)
            variance=np.nanmean((residual-mean[:,None])**2,axis=1)
            voltage=np.clip(mean,-.02,.02)
            loss=(variance+(mean-voltage)**2).reshape(sb.shape)
            i,k=np.unravel_index(np.nanargmin(loss),loss.shape)
            best=float(loss[i,k]);voff=float(voltage.reshape(sb.shape)[i,k])
            vg=np.unique(np.r_[np.arange(-.02,.02001,.0005),voff])
            vp=np.array([np.nanmin(variance+(mean-v)**2) for v in vg])
            for name,grid,vals,estimate,reference_value in [
                    ('bottom_scale',cb,np.nanmin(loss,axis=1),float(cb[i]),1.),
                    ('top_scale',ct,np.nanmin(loss,axis=0),float(ct[k]),1.),
                    ('voltage_offset_V',vg,vp,voff,0.)]:
                accepted=grid[vals<=1.05*best]
                span=float(np.ptp(accepted)) if len(accepted) else np.nan
                identified=bool(len(accepted)>0 and span<=.5*max(abs(estimate-reference_value),1e-6))
                fits.append({'anchor':j,'cell':cell+1,'parameter':name,'estimate':estimate,
                             'profile_span_at_5pct':span,'identified':identified,'min_MSE_V2':best})
                profiles.extend({'anchor':j,'cell':cell+1,'parameter':name,'value':float(x),
                                 'profile_MSE_V2':float(y),'within_5pct':bool(y<=1.05*best)} for x,y in zip(grid,vals))
    fits=pd.DataFrame(fits)
    fits.to_csv(HERE/'outputs/A_bounded_profile_summary.csv',index=False)
    pd.DataFrame(profiles).to_csv(HERE/'outputs/A_bounded_profile_curves.csv',index=False)
    shares=fits.groupby('parameter').identified.mean().to_dict()
    bilingual(HERE/'BOUNDED_PROFILE_REPORT.md','Bounded nuisance profile audit',
       f'''Exposed-exploratory; proxies are not hidden truth. The original A model used an unconstrained, analytically eliminated voltage offset and reported only scale profiles. This did not fully implement the prescribed bounded nuisance/profile requirement.

This unscored supplement bounds the charge-specific offset to ±20 mV and exports nuisance-optimized profiles for all three parameters, without changing or rescoring the main beta model. Definitions and grids were committed in bounded_profile_protocol.json before this computation. Identified fractions: {shares}. The original main result remains rejected; these post-main diagnostics cannot create a pre-registered winning candidate.''',
       f'''已曝光探索性研究；代理不是隐藏真值。原 A 模型把电压偏置解析消除，未限定范围，且只报告两个缩放参数的剖面，因此没有完整实现所要求的有界干扰和逐参数剖面。

本不评分补充将充电特有偏置限制到 ±20 mV，输出三个参数在其他参数优化后的残差剖面，不改变或重评主 β 模型。定义和网格已在计算前提交 bounded_profile_protocol.json。各参数可辨识比例：{shares}。原主结果仍被拒绝，主评估后的诊断不能产生预登记赢家。''')
    print(shares)
