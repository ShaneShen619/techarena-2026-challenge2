"""Post-score, metadata-selected wide events; frozen estimator reused verbatim."""
from pathlib import Path
import importlib.util,sys,json,pickle
HERE=Path(__file__).resolve().parent
PARENT=HERE.parent
sys.path.insert(0,str(PARENT))
import model
from common import *
from audit_stage import restfit
from scipy.integrate import cumulative_trapezoid

def verify_main():
    spec=importlib.util.spec_from_file_location('frozen_main',PARENT/'run.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);mod.verify_freeze()

def main():
    verify_main()
    if (HERE/'STARTED').exists():raise RuntimeError('supplement already started; preserve existing run')
    freeze={'scope':'post-score exploratory; fixed main estimator unchanged','date':'2026-10-13',
        'files':{str(p.relative_to(ROOT)):sha(p) for p in [HERE/'execute.py',HERE/'PROTOCOL.md']}}
    (HERE/'freeze_manifest.json').write_text(json.dumps(freeze,indent=2)+'\n');(HERE/'STARTED').write_text('2026-10-13\n')
    catalog=pd.read_csv(ROOT/'research/charge_capacity_review_20261006/operating_events.csv')
    chosen=catalog[(catalog.kind=='long_dynamic_discharge')&(catalog.Q_Ah>45)&(catalog.t_end<'2025-08-28')]
    es=[];registry=[];source_files=[]
    for file in sorted(chosen.file.unique()):
        path=ROOT/'data/operation'/file;raw=pd.read_csv(path,parse_dates=['timestamp'])
        clean=raw.sort_values('timestamp',kind='stable').drop_duplicates('timestamp',keep='last')
        tt=clean.timestamp.to_numpy(dtype='datetime64[ns]').astype('int64')/1e9
        jj=-clean.current_A.to_numpy(float);yy=clean[[f'cell{i}_V' for i in range(1,5)]].to_numpy(float)
        source_files.append({'file':file,'sha256':sha(path)})
        for row in chosen[chosen.file==file].itertuples():
            start=pd.Timestamp(row.t_start);end=pd.Timestamp(row.t_end)
            a=int(clean.timestamp.searchsorted(start));b=int(clean.timestamp.searchsorted(end))
            t=tt[a:b+1]-tt[a];j=jj[a:b+1];y=yy[a:b+1];q=cumulative_trapezoid(j,t,initial=0)
            q/=3600
            ix=np.arange(0,len(t),3)
            if ix[-1]!=len(t)-1:ix=np.r_[ix,len(t)-1]
            def rest_indices(k,step):
                indices=[];prev=None
                while 0<=k<len(tt) and abs(jj[k])<=.5:
                    if prev is not None and abs(tt[k]-tt[prev])>20:break
                    indices.append(k);prev=k;k+=step
                return np.array(sorted(indices),int)
            pre=rest_indices(a-1,-1);post=rest_indices(b+1,1)
            program='p46' if row.Q_Ah<48 else 'p50';T=int(row.setpoint_C)
            old_full=catalog[(catalog.file==file)&(catalog.kind=='full_charge')&(catalog.t_end<row.t_start)]
            anchor=str(old_full.t_end.max()) if len(old_full) else f'unknown_{file}_{row.t_start}'
            availability=clean.timestamp.iat[int(post[-1])].isoformat() if len(post) else end.isoformat()
            valid=bool(np.max(np.diff(t))<=20 and np.min(j)>.5 and abs(q[-1]-row.Q_Ah)<.05)
            registry.append(dict(id=f'{program}_{start.isoformat()}',file=file,T=T,program=program,
                start=start.isoformat(),end=end.isoformat(),available_after=availability,
                Q_Ah=float(q[-1]),catalog_Q_Ah=float(row.Q_Ah),max_gap_s=float(np.diff(t).max()),
                pre_rest_s=float(np.ptp(tt[pre])) if len(pre) else 0.,
                post_rest_s=float(np.ptp(tt[post])) if len(post) else 0.,qualified=valid,anchor_chain=anchor))
            if not valid:continue
            e=dict(id=f'{program}_{start.isoformat()}',panel=program,T=T,start=start.isoformat(),end=end.isoformat(),
                available_after=availability,file=file,t=t[ix],j=j[ix],q=q[ix],y=y[ix],
                q_total=float(q[-1]),pre_t=tt[pre]-tt[a],pre_y=yy[pre],post_t=tt[post]-tt[b],post_y=yy[post],
                anchor_chain=anchor,net_since_anchor_Ah=np.nan)
            es.append(e)
        print('wide raw audit',file,flush=True)
    es.sort(key=lambda e:e['start'])
    for T in [25,45]:
        group=[e for e in es if e['T']==T];n=max(2,int(.4*len(group)))
        development_chains={e['anchor_chain'] for e in group[:n]}
        for e in group:e['split']='development' if e['anchor_chain'] in development_chains else 'evaluation'
    pd.DataFrame(registry).to_csv(HERE/'registry.csv',index=False)
    (HERE/'source_manifest.json').write_text(json.dumps(source_files,indent=2)+'\n')
    (HERE/'events.pkl').write_bytes(pickle.dumps(es))
    profs={};metrics=[];diags=[];curves=[];empty=pd.DataFrame(columns=['id','T','panel','qualified','available_after','pulse_uid'])
    template=StrictTemplate()
    for e in es:
        tau=300 if e['T']==25 else 600
        hist=[h for h in es if h['panel']==e['panel'] and h['T']==e['T'] and h['available_after']<e['start']][-4:]
        if e['split']=='evaluation' and hist:
            for loss in ['L2','LAD']:
                prs=[profs[(h['id'],loss)] for h in hist];diag,curve=model.diagnosis(prs,loss,template.q0)
                diags.append(dict(id=e['id'],T=e['T'],program=e['panel'],history_n=len(hist),**diag,loss=loss))
                for s,v in zip(prs[0]['sgrid'],curve):curves.append(dict(id=e['id'],T=e['T'],program=e['panel'],loss=loss,s=s,loss_mV=v))
                for budgetname,budget in [('A',0),('B',1)]:
                    base=legacy.last_curve(e,hist[-1],budget);base_score=legacy.errors(e['y'],base,e['q'])
                    for kind in ['baseline','fixed','common','gated']:
                        fallback=False;reason='';s=np.ones(4)
                        if kind=='baseline':score=base_score
                        else:
                            s,params,_=model.select(prs,fixed=kind=='fixed',loss=loss)
                            try:
                                if kind=='gated' and not diag['gate']:raise ValueError('profile_gate_rejected')
                                p,pred,_=model.forecast(template,e,s,params,tau,budget)
                                score=legacy.errors(p['y'],pred,p['q'])
                            except ValueError as ex:fallback=True;reason=str(ex);score=base_score
                        metrics.append(dict(id=e['id'],T=e['T'],program=e['panel'],budget=budgetname,loss=loss,
                            kind=kind,fallback=fallback,reason=reason,s=float(s.mean()),
                            profile_width_Ah=diag['width_Ah'],latest_parameter_end=hist[-1]['available_after'],**score))
        # Full target observations become available only after its prediction.
        for loss in ['L2','LAD']:
            path=HERE/f"{e['id'].replace(':','-')}_{loss}.npz"
            if path.exists():
                z=np.load(path);pr={k:z[k] for k in z.files}
            else:
                pr=model.profile(template,e,tau,loss,'independent',empty,cache=False)
                np.savez_compressed(path,**pr)
            profs[(e['id'],loss)]=pr
        print('wide replay',e['split'],e['id'],flush=True)
        pd.DataFrame(metrics).to_csv(HERE/'forward_metrics.csv',index=False)
    pd.DataFrame(diags).to_csv(HERE/'identifiability.csv',index=False)
    pd.DataFrame(curves).to_csv(HERE/'profiles.csv',index=False)
    summary=pd.DataFrame(metrics).groupby(['budget','loss','kind']).agg(n=('id','size'),mae_mV=('mae_mV','mean'),direct_coverage=('fallback',lambda v:1-v.mean())).reset_index()
    summary.to_csv(HERE/'summary.csv',index=False)
    (HERE/'data_split.json').write_text(json.dumps({'eligible_events':len(es),'development':sum(e['split']=='development' for e in es),'evaluation':sum(e['split']=='evaluation' for e in es),'scope':'post-score exploratory'},indent=2)+'\n')
    verify_main()
    for name,digest in freeze['files'].items():
        if sha(ROOT/name)!=digest:raise RuntimeError('supplement source changed')
    (HERE/'COMPLETE').write_text('2026-10-13\n')
    print(summary.to_string(index=False),flush=True)

if __name__=='__main__':main()
