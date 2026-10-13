"""Raw registry and outcome-free pulse qualification; dev-only calibration summaries."""
import json,pickle
import numpy as np
import pandas as pd
from scipy.optimize import lsq_linear
from common import *

CELLS=[f'cell{i}_V' for i in range(1,5)]

def restfit(e,tau,which='pre'):
    t=np.asarray(e[which+'_t']);y=np.asarray(e[which+'_y'])
    duration=float(t[-1]-t[0]) if len(t)>1 else 0.
    if len(t)<CFG['rest_min_samples'] or duration<CFG['rest_min_duration_s']:
        return dict(valid=False,reason='short_rest',duration_s=duration)
    n=max(5,int(len(t)*CFG['rest_train_fraction']));train=t[:n]-t[0]
    a=np.c_[np.ones(n),np.exp(-train/tau)]
    coef=np.linalg.lstsq(a,y[:n],rcond=None)[0]
    extrap=np.c_[np.ones(len(t)-n),np.exp(-(t[n:]-t[0])/tau)]@coef
    mae=float(np.abs(extrap-y[n:]).mean()*1000)
    baseline=float(np.abs(y[n:]-y[n-1]).mean()*1000)
    full=np.linalg.lstsq(np.c_[np.ones(len(t)),np.exp(-(t-t[0])/tau)],y,rcond=None)[0]
    amp_at_start=full[1]*np.exp(t[0]/tau) if which=='pre' else full[1]
    return dict(valid=True,reason='',duration_s=duration,heldout_mae_mV=mae,
        last_value_mae_mV=baseline,amp_V=amp_at_start.tolist(),
        asymptote_V=full[0].tolist(),condition=float(np.linalg.cond(a)),
        amplitude_over_bound=bool(np.max(np.abs(amp_at_start))>.1))

def main():
    if (TASK/'events.pkl').exists(): raise RuntimeError('audit already exists; use a new version')
    es=pickle.loads((OLD_RUN/'events.pkl').read_bytes())
    protected_before=protected();savejson('protected_before.json',protected_before)
    selected=json.loads((OLD_RUN/'selected_configuration.json').read_text())
    savejson('selected_legacy.json',selected)
    pulses=[];registry=[];rests=[];files=[];checked=[]
    for file in sorted({e['file'] for e in es}):
        path=ROOT/'data/operation'/file
        raw=pd.read_csv(path,parse_dates=['timestamp'])
        files.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),rows=len(raw)))
        # pandas 3 may parse at microsecond resolution; request ns explicitly.
        t=raw.timestamp.to_numpy(dtype='datetime64[ns]').astype('int64')/1e9
        j=-raw.current_A.to_numpy(float);yy=raw[CELLS].to_numpy(float)
        clean=raw.sort_values('timestamp',kind='stable').drop_duplicates('timestamp',keep='last')
        ct=clean.timestamp.to_numpy(dtype='datetime64[ns]').astype('int64')/1e9
        cj=-clean.current_A.to_numpy(float);cy=clean[CELLS].to_numpy(float)
        for e in [v for v in es if v['file']==file]:
            k0=e['raw_start_index'];k1=e['raw_end_index']
            idx=np.arange(k0,k1+1)
            ti=t[idx];jj=j[idx];v=yy[idx]
            valid=np.r_[True,np.diff(ti)>0];ti=ti[valid];jj=jj[valid];v=v[valid]
            q=np.r_[0,np.cumsum(.5*(jj[1:]+jj[:-1])*np.diff(ti)/3600)]
            sample_indices=np.searchsorted(ti-ti[0],e['t'])
            checked.append(dict(id=e['id'],q_raw_Ah=float(q[-1]),q_cached_Ah=e['q_total'],
                delta_q_Ah=float(q[-1]-e['q_total']),max_gap_s=float(np.diff(ti).max()),
                voltage_cache_exact=bool(np.allclose(v[sample_indices],e['y'],atol=1e-12)),
                max_cell_voltage_cache_delta_mV=float(np.max(abs(v[sample_indices]-e['y']))*1000)))
            # No charging transition is used to calibrate the discharge response.
            first_clean=int(np.searchsorted(ct,t[k0]-20));last_clean=int(np.searchsorted(ct,t[k1]+20))
            for k in range(max(3,first_clean),min(len(clean)-4,last_clean+1)):
                dj=cj[k]-cj[k-1]
                if abs(dj)<CFG['step_min_delta_A']:continue
                reason=[]
                dt=ct[k]-ct[k-1]
                if not 0<dt<=CFG['step_max_dt_s']:reason.append('step_sampling')
                pre=cj[k-3:k];post=cj[k:k+3]
                if np.ptp(pre)>CFG['step_stability_A'] or np.ptp(post)>CFG['step_stability_A']:reason.append('unstable_current')
                if np.min(np.r_[pre,post])<-.5:reason.append('charge_direction')
                if np.any(np.diff(ct[k-3:k+3])<=0) or np.any(np.diff(ct[k-3:k+3])>10):reason.append('gap')
                # Current and voltage updates may be asynchronous at the edge.
                # Use next voltage sample and explicitly retain its time scale.
                dv=cy[k+1]-cy[k-1];r=-dv/dj
                if np.any(abs(dv)<.003):reason.append('unresolved_voltage_response')
                if np.any(r<0) or np.any(r>.015):reason.append('implausible_apparent_R')
                if e['start']<=clean.timestamp.iat[k].isoformat()<=e['end'] and e['panel']=='wide': location='in_event'
                else:location='boundary'
                rec=dict(id=e['id'],file=file,split=e['split'],panel=e['panel'],T=e['T'],
                    timestamp=clean.timestamp.iat[k].isoformat(),available_after=clean.timestamp.iat[k+2].isoformat(),
                    location=location,dt_s=float(dt),delta_I_D_A=float(dj),
                    voltage_response_delay_s=float(ct[k+1]-ct[k]),
                    measurement_span_s=float(ct[k+1]-ct[k-1]),
                    edge_voltage_change_mV=float(np.max(abs(cy[k]-cy[k-1]))*1000),
                    elapsed_from_event_s=float(ct[k]-t[k0]),qualified=not reason,reason=';'.join(reason))
                for c in range(4):rec[f'R{c+1}_ohm']=float(r[c]);rec[f'delta_V{c+1}_V']=float(dv[c])
                pulses.append(rec)
            tau=selected[key(e)]['tau']
            for which in ['pre','post']:
                rr=restfit(e,tau,which);rr.pop('amp_V',None);rr.pop('asymptote_V',None)
                rests.append(dict(id=e['id'],split=e['split'],panel=e['panel'],T=e['T'],which=which,**rr))
            registry.append({k:e[k] for k in ['id','file','panel','T','start','end','available_after','split','chain_id','anchor_end','chain_ok','q_total','net_since_anchor_Ah','temp_mean','temp_span','max_gap_s','raw_rows']})
        print('raw re-audit',file,len(raw),flush=True)
    f=pd.DataFrame(pulses)
    f['pulse_uid']=f.file+':'+f.timestamp
    # Event boundary windows may share a physical pulse; group and mark explicitly.
    f.to_csv(TASK/'pulse_registry.csv',index=False)
    pd.DataFrame(registry).to_csv(TASK/'event_registry.csv',index=False)
    pd.DataFrame(checked).to_csv(TASK/'raw_reaudit.csv',index=False)
    pd.DataFrame(rests).to_csv(TASK/'rest_registry.csv',index=False)
    savejson('raw_manifest.json',files)
    (TASK/'events.pkl').write_bytes(pickle.dumps(es))
    dev=f[(f.split=='development') & f.qualified].drop_duplicates('pulse_uid')
    calibrations=[]
    for T in [25,45]:
        tt=dev[dev['T']==T]
        for c in range(4):
            values=tt[f'R{c+1}_ohm'].to_numpy();median=float(np.median(values)) if len(values) else None
            mad=float(np.median(abs(values-median))) if len(values) else None
            calibrations.append(dict(T=T,cell=c+1,n=len(values),R_app_median_ohm=median,MAD_ohm=mad))
    savejson('development_pulse_calibration.json',calibrations)
    summary=dict(events=len(es),development=sum(e['split']=='development' for e in es),
        evaluation=sum(e['split']=='evaluation' for e in es),raw_files=len(files),
        max_raw_Ah_discrepancy=max(abs(r['delta_q_Ah']) for r in checked),
        candidate_pulses=len(f),qualified_pulses=int(f.qualified.sum()),
        qualified_unique_pulses=f.loc[f.qualified,'pulse_uid'].nunique(),
        real_per_cell_SOC_labels=False,later_same_protocol_capacity_labels=False,
        CK0_temperature_certified=False,exposure='Previously studied single physical pack; temporal replay, not new blind evaluation')
    savejson('audit_summary.json',summary);print(summary,flush=True)

if __name__=='__main__':main()
