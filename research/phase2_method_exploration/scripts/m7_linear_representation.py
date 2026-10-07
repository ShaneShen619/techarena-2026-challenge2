"""Nested physical-cell PCA self-supervision and capacity-head comparison."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3];TASK=Path(__file__).resolve().parents[1]
OUT=TASK/'runs/M7_linear_representation_v1';OUT.mkdir(parents=True,exist_ok=False)
cfg=json.loads((TASK/'configs/m7_representation.json').read_text())
seq=np.load(TASK/'runs/M7_sequences_v1/native_sequences.npz')
inp=np.load(TASK/'runs/M7_target_map_v1/target_inputs.npz')
X=seq['X'].astype(float);event_cells=seq['cell_ids'].astype(str)
slots=inp['indices'].astype(int);meta=inp['metadata'].astype(float)
cells=inp['cell_ids'].astype(str);ordinal=inp['target_ordinals'].astype(int)
panel=ROOT/'research/phase2_temperature_improvement/outputs/panel_main.csv'
assert hashlib.sha256(panel.read_bytes()).hexdigest()=='7188b662900f84312292a7062d6023e5eeb4f2e32798b6d61a3547ed40cdc59c'
labels=pd.read_csv(panel,usecols=['cell_id','target_ordinal','target_soh_pp']).set_index(['cell_id','target_ordinal'])
y=np.array([labels.loc[(c,int(o)),'target_soh_pp'] for c,o in zip(cells,ordinal)],float)
anchor=meta[:,0];ages=meta[:,1:6]
assert len(cells)==180 and len(np.unique(cells))==6

def pca_embed(train_event_mask,no_voltage=False):
    data=X.copy()
    if no_voltage:data[:,:,0]=0
    flat=data.reshape(len(data),-1)
    fitting=flat[train_event_mask]
    mean=fitting.mean(axis=0);std=fitting.std(axis=0);std[std<1e-8]=1
    z=(fitting-mean)/std
    _,_,vt=np.linalg.svd(z,full_matrices=False)
    components=vt[:16].T
    emb=(flat-mean)/std@components
    return emb,mean,std,components

def aggregate(emb):
    result=[]
    for row in slots:
        curr=emb[row[0]] if row[0]>=0 else np.zeros(emb.shape[1])
        first=emb[row[1:11][row[1:11]>=0]].mean(axis=0) if np.any(row[1:11]>=0) else np.zeros(emb.shape[1])
        recent=emb[row[11:16][row[11:16]>=0]].mean(axis=0) if np.any(row[11:16]>=0) else np.zeros(emb.shape[1])
        result.append(np.r_[curr,first,recent])
    return np.array(result)

def predict(F,train,test,alpha):
    a=F[train];b=F[test]
    med=np.array([np.nanmedian(col) if np.isfinite(col).any() else 0 for col in a.T])
    a=np.where(np.isfinite(a),a,med);b=np.where(np.isfinite(b),b,med)
    mean=a.mean(axis=0);std=a.std(axis=0);std[std<1e-8]=1
    a=np.column_stack([np.ones(len(a)),(a-mean)/std]);b=np.column_stack([np.ones(len(b)),(b-mean)/std])
    penalty=np.diag([0]+[alpha]*(a.shape[1]-1))
    coef=np.linalg.solve(a.T@a+penalty+np.eye(a.shape[1])*1e-9,a.T@(y[train]-anchor[train]))
    return anchor[test]+b@coef

rows=[];choices=[];recon=[]
for held in np.unique(cells):
    outer_train=np.flatnonzero(cells!=held);outer_test=np.flatnonzero(cells==held)
    inner_data={method:[] for method in ('age_count_ridge','PCA_frozen_ridge','PCA_no_voltage_control')}
    for valcell in np.unique(cells[outer_train]):
        fitidx=outer_train[cells[outer_train]!=valcell]
        validx=outer_train[cells[outer_train]==valcell]
        f_age=ages
        pca,_,_,_=pca_embed(np.isin(event_cells,np.unique(cells[fitidx])))
        pca_noV,_,_,_=pca_embed(np.isin(event_cells,np.unique(cells[fitidx])),True)
        feats={'age_count_ridge':f_age,
               'PCA_frozen_ridge':np.column_stack([ages,meta[:,6:8],aggregate(pca)]),
               'PCA_no_voltage_control':np.column_stack([ages,meta[:,6:8],aggregate(pca_noV)])}
        for method,F in feats.items():
            for alpha in cfg['PCA_head_alpha_grid']:
                p=predict(F,fitidx,validx,alpha)
                inner_data[method].append({'validation_cell':valcell,'alpha':alpha,
                                           'mae_pp':float(np.mean(abs(p-y[validx])))})
    model={}
    pca,mean,std,comp=pca_embed(event_cells!=held)
    pca_noV,_,_,_=pca_embed(event_cells!=held,True)
    model['age_count_ridge']=ages
    model['PCA_frozen_ridge']=np.column_stack([ages,meta[:,6:8],aggregate(pca)])
    model['PCA_no_voltage_control']=np.column_stack([ages,meta[:,6:8],aggregate(pca_noV)])
    # Unsupervised voltage reconstruction on entirely unseen held cell events.
    held_ev=event_cells==held
    flat=X[held_ev].reshape(int(held_ev.sum()),-1)
    restored=((flat-mean)/std@comp@comp.T)*std+mean
    observed=X[held_ev,:,0];estimated=restored.reshape(-1,X.shape[1],X.shape[2])[:,:,0]
    mask=X[held_ev,:,4]>0.5
    recon.append({'held_cell':held,'held_unlabeled_events':int(held_ev.sum()),
                  'PCA_voltage_reconstruction_MAE_mV':float(np.mean(abs((observed-estimated)[mask]))*100)})
    for method,F in model.items():
        scores=pd.DataFrame(inner_data[method]).groupby('alpha').mae_pp.mean()
        alpha=float(scores.idxmin())
        choices.append({'held_cell':held,'method':method,'selected_alpha':alpha,
                        'inner_macro_mae_pp':float(scores.min())})
        p=predict(F,outer_train,outer_test,alpha)
        for j,idx in enumerate(outer_test):
            rows.append({'cell_id':cells[idx],'target_ordinal':ordinal[idx],
                         'held_cell':held,'method':method,'target_soh_pp':y[idx],
                         'anchor_soh_pp':anchor[idx],'pred_soh_pp':p[j],
                         'error_pp':p[j]-y[idx]})
    print('held',held,'PCA MAE',round(np.mean(abs(np.array([r['error_pp'] for r in rows if r['held_cell']==held and r['method']=='PCA_frozen_ridge']))),3),flush=True)
pred=pd.DataFrame(rows);pred.to_csv(OUT/'predictions.csv',index=False)
pd.DataFrame(choices).to_csv(OUT/'inner_alpha_selections.csv',index=False)
pd.DataFrame(recon).to_csv(OUT/'unseen_event_reconstruction.csv',index=False)
metrics=[]
for method,g in pred.groupby('method'):
    cell_mae=g.assign(abs_pp=g.error_pp.abs()).groupby('cell_id').abs_pp.mean()
    metrics.append({'method':method,'macro_MAE_pp':float(cell_mae.mean()),
                    'worst_cell_MAE_pp':float(cell_mae.max()),
                    'max_abs_error_pp':float(g.error_pp.abs().max())})
summary={'targets':len(np.unique(list(zip(cells,ordinal)),axis=0)),'physical_cells':6,
         'metrics':metrics,'mean_unseen_PCA_voltage_reconstruction_MAE_mV':float(pd.DataFrame(recon).PCA_voltage_reconstruction_MAE_mV.mean()),
         'claim_limit':'Six P1 development cells, cropped deep-charge fragments, high-rate single-cell proxy labels; no official or independent D2 capacity confirmation.'}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False),flush=True)
