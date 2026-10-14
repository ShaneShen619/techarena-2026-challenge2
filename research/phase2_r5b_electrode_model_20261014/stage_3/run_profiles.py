"""LLI fixed-grid refits, residual-effective likelihood profiles and pack envelopes."""
import hashlib
import itertools
import json
import pickle
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import chi2
HERE=Path(__file__).resolve().parent
STUDY=HERE.parent
sys.path.insert(0,str(HERE))
sys.path.insert(0,str(STUDY/'src'))
from common5b import H,CACHE5
from edata import anchor_curve
from emodel import OCP,fit_charge
from profile_pack import quantities,restart_health
from audit5b import dump,clean_json,physical_charge,bilingual
from v2 import anchors_by_checkup
from run_fits import cache_key,elapsed

def profile_cell(j,c,row,q,I,V,ocp,all_rows):
    best=np.array([row[n] for n in ['Qn','Qp','QLi','theta_n0','R','h']],float)
    grid=np.unique(np.r_[np.arange(50.,250.01,10.),best[2],best[2]+np.r_[
        -64.,-32.,-16.,-8.,-4.,-2.,-1.,-.5,-.25,.25,.5,1.,2.,4.,8.,16.,32.,64.]])
    grid=grid[(grid>=50)&(grid<=250)]
    records=[];last=best.copy()
    source_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    for value in sorted(grid,key=lambda v:abs(v-best[2])):
        if elapsed()>5400:break
        starts=[best,last]
        starts.append(best*np.array([1.02,.98,1.,1.,1.,1.]))
        key=cache_key(q,I,V,{2:float(value)})
        key=hashlib.sha256((key+source_hash+repr(np.array(starts).tolist())).encode()).hexdigest()
        cache=Path(CACHE5)/f'profile_{key}.pkl'
        if cache.exists():x,info=pickle.loads(cache.read_bytes())
        else:
            x,info=fit_charge(q,I,V,ocp,x0_list=starts,fixed={2:float(value)})
            cache.write_bytes(pickle.dumps((x,info),protocol=5))
        last=x
        valid=physical_charge(x,float(row['Q_fc_obs']),ocp)
        record={'anchor':j,'cell':c+1,'QLi_fixed':float(value),'cost':float(info['cost']),
                'rms_mV':float(info['rms_mV']),'physical_valid':valid,'n':row['n'],'n_eff':row['n_eff'],
                **{name:float(v) for name,v in zip(['Qn','Qp','QLi','theta_n0','R','h'],x)}}
        records.append(record);all_rows.append(record)
    if not records:return []
    minimum=min([float(row['cost'])]+[r['cost'] for r in records if r['physical_valid']])
    sigma=max(2.,float(row['rms_mV']))
    for r in records:
        statistic=max(0.,2*(r['cost']-minimum)/sigma**2*float(row['n_eff'])/float(row['n']))
        r['profile_statistic']=statistic
        r['cell95']=bool(r['physical_valid'] and statistic<=chi2.ppf(.95,1))
        r['pack95_bonferroni']=bool(r['physical_valid'] and statistic<=chi2.ppf(1-.05/4,1))
        r['profile_minimum_below_main']=minimum<float(row['cost'])-1e-6
    return records

def combinations(cells,best,seed):
    lengths=[len(x) for x in cells]
    if any(n==0 for n in lengths):return np.empty((0,4,6)),False,0
    count=int(np.prod(lengths))
    if count<=65536:
        return np.asarray(list(itertools.product(*cells)),float),True,count
    points=[np.asarray(best,float)]
    for c,pool in enumerate(cells):
        for x in pool:
            p=np.asarray(best,float).copy();p[c]=x;points.append(p)
    for parameter in range(6):
        for direction in (1,-1):
            points.append(np.array([sorted(pool,key=lambda a:direction*a[parameter])[0] for pool in cells]))
    for i in range(max(lengths)):
        points.append(np.array([pool[min(i,len(pool)-1)] for pool in cells]))
    rng=np.random.default_rng(seed)
    for _ in range(1024):points.append(np.array([pool[rng.integers(len(pool))] for pool in cells]))
    return np.unique(np.asarray(points),axis=0),False,count

def simulate_batches(points,ocp,etas,reference=None):
    out={'Q_fc':[],'D_prog':[],'Q_C20':[],'limiting':[]}
    for i in range(0,len(points),256):
        cells=points[i:i+256]
        if reference is not None:cells=restart_health(cells,reference,ocp)
        vals=quantities(cells,ocp,etas)
        for key in out:out[key].extend(vals[key].tolist())
    return {k:np.asarray(v) for k,v in out.items()}

def span(values):
    finite=values[np.isfinite(values)]
    if not len(finite):return (np.nan,np.nan,np.nan)
    return float(finite.min()),float(finite.max()),float(np.ptp(finite))

if __name__=='__main__':
    fits=pd.read_csv(HERE/'outputs/S3_main_fits.csv')
    ocp=OCP('main');op=H.full_op();anc=anchors_by_checkup(H.full_charges(op),H.CK)
    ref_json=json.loads((STUDY/'stage_2/outputs/S2_ck0_check.json').read_text())['main_anchor0']
    etas=ref_json['ck0_fit']['eta_dis']
    all_rows=[];groups={};cell_intervals=[]
    for j in range(8):
        q,I,V,_,_=anchor_curve(op,anc[j]);groups[j]=[]
        for c in range(4):
            row=fits[(fits.anchor==j)&(fits.cell==c+1)].iloc[0].to_dict()
            records=profile_cell(j,c,row,q,I,V[:,c],ocp,all_rows)
            candidates=[np.array([r[n] for n in ['Qn','Qp','QLi','theta_n0','R','h']]) for r in records if r.get('pack95_bonferroni',False)]
            groups[j].append(candidates)
            cell95=[r['QLi'] for r in records if r.get('cell95',False)]
            cell_intervals.append({'anchor':j,'cell':c+1,'QLi_lower':min(cell95) if cell95 else np.nan,
                'QLi_upper':max(cell95) if cell95 else np.nan,'cell95_count':len(cell95),
                'pack95_count':len(candidates),'grid_complete':len(records)>=len(np.unique(np.r_[np.arange(50.,250.01,10.),row['QLi']])),
                'grid_boundary_accepted':bool(cell95 and (min(cell95)<=50 or max(cell95)>=250))})
            pd.DataFrame(all_rows).to_csv(HERE/'outputs/S3_LLI_profile_fits.csv',index=False)
            pd.DataFrame(cell_intervals).to_csv(HERE/'outputs/S3_LLI_cell_intervals.csv',index=False)
            print(f'profile anchor {j}, cell {c+1}: {len(records)} grid points; {len(candidates)} pack-envelope states; elapsed {elapsed():.1f}s',flush=True)
            if elapsed()>5400:break
        if elapsed()>5400:break
    best={j:fits[fits.anchor==j][['Qn','Qp','QLi','theta_n0','R','h']].to_numpy() for j in range(8)}
    pack_rows=[];quantile_rows=[];health_states={}
    if 1 in groups and len(groups[1])==4:
        reference=best[1]
        refsets,refexact,refcount=combinations(groups[1],reference,20261016)
        ref_values=simulate_batches(refsets,ocp,etas,reference)
        rq=span(ref_values['Q_fc']);rd=span(ref_values['D_prog'])
    else:
        reference=best[1];refexact=False;refcount=0;rq=rd=(np.nan,np.nan,np.nan)
    for j,pools in groups.items():
        if len(pools)!=4:continue
        points,exact,count=combinations(pools,best[j],20261015+j)
        if not len(points):continue
        vals=simulate_batches(points,ocp,etas)
        health_states[j]=points
        cap=span(vals['Q_C20']);qfc=span(vals['Q_fc'])
        main=quantities(best[j][None,:,:],ocp,etas)
        health_vals=simulate_batches(points,ocp,etas,reference)
        cq=span(health_vals['Q_fc']);cd=span(health_vals['D_prog'])
        numerator=(cq[0]-rq[1],cq[1]-rq[0])
        denominator=(cd[0]-rd[1],cd[1]-rd[0])
        zero=bool(not np.isfinite(denominator).all() or denominator[0]<=0<=denominator[1])
        if zero:bmin=bmax=bwidth=np.nan
        else:
            ratios=[a/b for a in numerator for b in denominator]
            bmin,bmax=min(ratios),max(ratios);bwidth=bmax-bmin
        complete_roots=bool(np.isfinite(vals['Q_C20']).all())
        certified=exact and complete_roots
        beta_certified=bool(exact and refexact and np.isfinite(health_vals['Q_fc']).all() and np.isfinite(health_vals['D_prog']).all() and not zero)
        pack_rows.append({'anchor':j,'combinations_total':count,'combinations_evaluated':len(points),'exhaustive':exact,
            'Q_C20_main':float(main['Q_C20'][0]),'Q_C20_lower_witness':cap[0],'Q_C20_upper_witness':cap[1],
            'Q_C20_width_witness':cap[2],'Q_C20_missing':int((~np.isfinite(vals['Q_C20'])).sum()),
            'Q_C20_interval_certified':certified,'Q_fc_obs':float(anc[j].Q_Ah),
            'Q_fc_sim_lower':qfc[0],'Q_fc_sim_upper':qfc[1],'Q_fc_error_lower':qfc[0]-anc[j].Q_Ah,'Q_fc_error_upper':qfc[1]-anc[j].Q_Ah,
            'beta_lower':bmin,'beta_upper':bmax,'beta_width':bwidth,'denominator_lower':denominator[0],
            'denominator_upper':denominator[1],'denominator_includes_zero':zero,'beta_interval_certified':beta_certified,
            'capacity_gate_pass':bool(certified and cap[2]<=.6),'beta_gate_pass':bool(beta_certified and bwidth<=.3),
            'interval_status':'exact finite discrete profile box' if certified else 'unidentified: partial box or unavailable roots'})
        for i in range(len(points)):
            quantile_rows.append({'anchor':j,'tuple':i,'Q_fc':vals['Q_fc'][i],'Q_C20':vals['Q_C20'][i],
                                 'D_prog':vals['D_prog'][i],'limiting':vals['limiting'][i]})
        pd.DataFrame(pack_rows).to_csv(HERE/'outputs/S3_pack_intervals.csv',index=False)
        print(f'pack anchor {j}: {len(points)}/{count} states; capacity witnessed width {cap[2]:.3f}; zero denominator={zero}; elapsed {elapsed():.1f}s',flush=True)
    pd.DataFrame(quantile_rows).to_csv(HERE/'outputs/S3_pack_profile_quantities.csv',index=False)
    intervals=pd.DataFrame(cell_intervals)
    baseline=intervals[intervals.anchor==0].set_index('cell')
    trajectory=[]
    for j in range(8):
        g=intervals[intervals.anchor==j]
        if len(g)!=4:continue
        lower=np.mean([baseline.loc[int(r.cell),'QLi_lower']-r.QLi_upper for r in g.itertuples()])
        upper=np.mean([baseline.loc[int(r.cell),'QLi_upper']-r.QLi_lower for r in g.itertuples()])
        point=float(fits[fits.anchor==j].LLI.mean())
        trajectory.append({'anchor':j,'LLI_point':point,'LLI_lower_nominal':lower,'LLI_upper_nominal':upper,
                           'pack_start_V':float(anc[j].pack_start_V)})
    trajectory=pd.DataFrame(trajectory)
    trajectory.to_csv(HERE/'outputs/S3_LLI_trajectory.csv',index=False)
    chosen=-np.inf;feasible=True
    for r in trajectory[trajectory.anchor>=1].itertuples():
        chosen=max(chosen,r.LLI_lower_nominal)
        feasible&=np.isfinite(r.LLI_upper_nominal) and chosen<=r.LLI_upper_nominal
    real=trajectory[trajectory.anchor>=1]
    correlation=float(real[['LLI_point','pack_start_V']].corr().iloc[0,1]) if len(real)>1 else np.nan
    pack=pd.DataFrame(pack_rows);wanted=pack[pack.anchor>=1] if len(pack) else pack
    capacity_wins=int(wanted.capacity_gate_pass.sum()) if len(wanted) else 0
    beta_wins=int(wanted.beta_gate_pass.sum()) if len(wanted) else 0
    synthetic=json.loads((STUDY/'stage_1/outputs/S1_synthetic_summary.json').read_text())['pass']
    complete=len(all_rows)>0 and len(cell_intervals)==32 and len(pack_rows)==8
    proceed=bool(synthetic and complete and capacity_wins>=5 and beta_wins>=5 and feasible)
    summary={'synthetic_numeric_pass':synthetic,'profile_cells':len(cell_intervals),'expected_profile_cells':32,
        'anchors_with_capacity_width_under_0_6':capacity_wins,'anchors_with_beta_width_under_0_3':beta_wins,
        'LLI_interval_monotonic_compatible':bool(feasible),'LLI_point_monotonic':bool(np.all(np.diff(real.LLI_point)>=0)),
        'LLI_start_voltage_correlation':correlation,'stage4_proceed':proceed,'elapsed_seconds':elapsed(),
        'stage3_cap_reached':elapsed()>5400,'interpretation':'Nominal model-conditional profiles. Witnessed ranges are lower bounds when full boxes exceed enumeration cap; no narrow eligibility claim is made from sampling.'}
    dump(HERE/'outputs/S3_exit.json',clean_json(summary))
    print(json.dumps(clean_json(summary),indent=2),flush=True)
