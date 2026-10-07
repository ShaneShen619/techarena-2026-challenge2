"""Strict outer-cell self-supervised TCN, frozen/fine-tuned/scratch capacity tests."""
from __future__ import annotations
import argparse,copy,hashlib,json,sys,time
from pathlib import Path
import numpy as np
import pandas as pd
import torch

ROOT=Path(__file__).resolve().parents[3];TASK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TASK/'src'))
from m7_tcn import ChargeEncoder,CapacityResidualNet,next_voltage_loss
parser=argparse.ArgumentParser();parser.add_argument('--smoke',action='store_true');arg=parser.parse_args()
OUT=TASK/('runs/M7_TCN_smoke_v1' if arg.smoke else 'runs/M7_TCN_v1')
OUT.mkdir(parents=True,exist_ok=False)
cfg=json.loads((TASK/'configs/m7_representation.json').read_text())
torch.set_num_threads(2)
seq=np.load(TASK/'runs/M7_sequences_v1/native_sequences.npz')
inp=np.load(TASK/'runs/M7_target_map_v1/target_inputs.npz')
X=seq['X'].astype(np.float32);event_cells=seq['cell_ids'].astype(str)
slots=inp['indices'].astype(np.int64);meta=inp['metadata'].astype(np.float32)
cells=inp['cell_ids'].astype(str);ordinal=inp['target_ordinals'].astype(int)
panel=ROOT/'research/phase2_temperature_improvement/outputs/panel_main.csv'
assert hashlib.sha256(panel.read_bytes()).hexdigest()=='7188b662900f84312292a7062d6023e5eeb4f2e32798b6d61a3547ed40cdc59c'
label=pd.read_csv(panel,usecols=['cell_id','target_ordinal','target_soh_pp']).set_index(['cell_id','target_ordinal'])
y=np.array([label.loc[(c,int(o)),'target_soh_pp'] for c,o in zip(cells,ordinal)],np.float32)
anchor=meta[:,0].astype(float);all_events=torch.tensor(X)
slot_t=torch.tensor(slots);age=meta[:,1:6].astype(float)
age_alpha=pd.read_csv(TASK/'runs/M7_linear_representation_v1/inner_alpha_selections.csv')

def ridge(F,train,apply,target,alpha):
    A=F[train].astype(float);B=F[apply].astype(float)
    med=np.array([np.nanmedian(x) if np.isfinite(x).any() else 0 for x in A.T])
    A=np.where(np.isfinite(A),A,med);B=np.where(np.isfinite(B),B,med)
    mu=A.mean(0);std=A.std(0);std[std<1e-8]=1
    A=np.c_[np.ones(len(A)),(A-mu)/std];B=np.c_[np.ones(len(B)),(B-mu)/std]
    P=np.diag([0]+[alpha]*(A.shape[1]-1))
    beta=np.linalg.solve(A.T@A+P+np.eye(A.shape[1])*1e-9,A.T@target[train])
    return B@beta

def embed_all(encoder):
    encoder.eval();items=[]
    with torch.no_grad():
        for begin in range(0,len(X),128):
            e,_=encoder(all_events[begin:begin+128]);items.append(e.numpy())
    return np.concatenate(items)

def aggregate(embedding):
    feats=[]
    for row in slots:
        a=embedding[row[0]]
        first=row[1:11];recent=row[11:16]
        b=embedding[first[first>=0]].mean(0) if np.any(first>=0) else np.zeros(embedding.shape[1])
        c=embedding[recent[recent>=0]].mean(0) if np.any(recent>=0) else np.zeros(embedding.shape[1])
        feats.append(np.r_[a,b,c])
    return np.array(feats)

def pretrain(held,seed,epochs):
    torch.manual_seed(seed);rng=np.random.default_rng(seed)
    encoder=ChargeEncoder(cfg['temporal_encoder']['width'])
    opt=torch.optim.AdamW(encoder.parameters(),lr=cfg['temporal_encoder']['pretrain_learning_rate'])
    train_events=np.flatnonzero(event_cells!=held);held_events=np.flatnonzero(event_cells==held)
    start=time.perf_counter();losses=[]
    for epoch in range(epochs):
        encoder.train();perm=rng.permutation(train_events);epoch_loss=[]
        for block in np.array_split(perm,max(1,int(np.ceil(len(perm)/cfg['temporal_encoder']['pretrain_batch_events'])))):
            batch=all_events[block]
            opt.zero_grad();loss=next_voltage_loss(encoder,batch)
            loss.backward();opt.step();epoch_loss.append(float(loss.item()))
        losses.append(float(np.mean(epoch_loss)))
    encoder.eval()
    with torch.no_grad():
        held_loss=[]
        for block in np.array_split(held_events,max(1,int(np.ceil(len(held_events)/128)))):
            held_loss.append(float(next_voltage_loss(encoder,all_events[block]).item()))
    return encoder,losses,float(np.mean(held_loss)),time.perf_counter()-start

def train_supervised(encoder,train,test,age_pred,seed,epochs,meta_scaled):
    torch.manual_seed(seed)
    net=CapacityResidualNet(encoder,meta_dim=meta_scaled.shape[1],width=cfg['temporal_encoder']['width'])
    opt=torch.optim.AdamW(net.parameters(),lr=cfg['supervised_learning_rate'],weight_decay=cfg['supervised_weight_decay'])
    rng=np.random.default_rng(seed);target=torch.tensor((y-age_pred).astype(np.float32))
    meta_t=torch.tensor(meta_scaled.astype(np.float32));losses=[];begin=time.perf_counter()
    for epoch in range(epochs):
        net.train();perm=rng.permutation(train);batchloss=[]
        for block in np.array_split(perm,max(1,int(np.ceil(len(perm)/cfg['supervised_batch_targets'])))):
            opt.zero_grad()
            correction=net(all_events,slot_t[block],meta_t[block])
            loss=torch.nn.functional.smooth_l1_loss(correction,target[block])
            loss.backward();opt.step();batchloss.append(float(loss.item()))
        losses.append(float(np.mean(batchloss)))
    net.eval()
    with torch.no_grad():
        corrections=[]
        for block in np.array_split(test,max(1,int(np.ceil(len(test)/64)))):
            corrections.extend(net(all_events,slot_t[block],meta_t[block]).numpy())
    return np.array(corrections),losses,time.perf_counter()-begin,net

rows=[];logs=[]
held_cells=np.unique(cells)[:1] if arg.smoke else np.unique(cells)
seeds=cfg['seeds'][:1] if arg.smoke else cfg['seeds']
for held in held_cells:
    train=np.flatnonzero(cells!=held);test=np.flatnonzero(cells==held)
    alpha=float(age_alpha.loc[age_alpha.held_cell.eq(held)&age_alpha.method.eq('age_count_ridge'),'selected_alpha'].iloc[0])
    age_pred=anchor+ridge(age,train,np.arange(len(cells)),y-anchor,alpha)
    mu=np.nanmean(meta[train],axis=0);std=np.nanstd(meta[train],axis=0);std[std<1e-8]=1
    meta_scaled=(np.where(np.isfinite(meta),meta,mu)-mu)/std
    for seed in seeds:
        start=time.perf_counter()
        encoder,preloss,heldloss,preseconds=pretrain(held,seed,2 if arg.smoke else cfg['temporal_encoder']['pretrain_epochs'])
        ckpt=OUT/f'pretrain_{held.replace("/","_")}_{seed}.pt'
        torch.save(encoder.state_dict(),ckpt)
        embedding=embed_all(encoder)
        F=np.column_stack([meta.astype(float),aggregate(embedding)])
        frozen=age_pred[test]+np.clip(ridge(F,train,test,y-age_pred,cfg['TCN_frozen_head_alpha']),-10,10)
        finecorr,fineloss,finesec,finenet=train_supervised(copy.deepcopy(encoder),train,test,age_pred,
                                  seed+100,3 if arg.smoke else cfg['supervised_epochs'],meta_scaled)
        torch.manual_seed(seed+999)
        scratch_encoder=ChargeEncoder(cfg['temporal_encoder']['width'])
        scratchcorr,scratchloss,scratchsec,scratchnet=train_supervised(scratch_encoder,train,test,age_pred,
                                  seed+100,3 if arg.smoke else cfg['supervised_epochs'],meta_scaled)
        torch.save(finenet.state_dict(),OUT/f'finetune_{held.replace("/","_")}_{seed}.pt')
        torch.save(scratchnet.state_dict(),OUT/f'scratch_{held.replace("/","_")}_{seed}.pt')
        predictions={'age_count_ridge':age_pred[test],
                     'TCN_frozen_ridge':frozen,
                     'TCN_finetune':age_pred[test]+finecorr,
                     'TCN_from_scratch':age_pred[test]+scratchcorr}
        for method,pred in predictions.items():
            for j,idx in enumerate(test):
                rows.append({'cell_id':cells[idx],'target_ordinal':ordinal[idx],
                             'held_cell':held,'seed':seed,'method':method,
                             'target_soh_pp':float(y[idx]),'age_prior_pp':float(age_pred[idx]),
                             'pred_soh_pp':float(pred[j]),'error_pp':float(pred[j]-y[idx])})
        logs.append({'held_cell':held,'seed':seed,'pretrain_initial_loss_mV2':preloss[0],
                     'pretrain_final_loss_mV2':preloss[-1],'held_event_next_voltage_loss_mV2':heldloss,
                     'finetune_initial_train_loss_pp':fineloss[0],
                     'finetune_final_train_loss_pp':fineloss[-1],
                     'scratch_initial_train_loss_pp':scratchloss[0],
                     'scratch_final_train_loss_pp':scratchloss[-1],
                     'pretrain_seconds':preseconds,'finetune_seconds':finesec,
                     'scratch_seconds':scratchsec,'total_seconds':time.perf_counter()-start})
        print('held',held,'seed',seed,'pretrain held mV RMSE',round(heldloss**.5,3),
              'MAEs',{m:round(float(np.mean(abs(p-y[test]))),3) for m,p in predictions.items()},flush=True)
pd.DataFrame(rows).to_csv(OUT/'predictions.csv',index=False)
pd.DataFrame(logs).to_csv(OUT/'training_logs.csv',index=False)
pred=pd.DataFrame(rows)
metric=[]
for (seed,method),g in pred.groupby(['seed','method']):
    per=g.assign(abs_pp=g.error_pp.abs()).groupby('cell_id').abs_pp.mean()
    metric.append({'seed':int(seed),'method':method,'macro_MAE_pp':float(per.mean()),
                   'worst_cell_MAE_pp':float(per.max()),'max_abs_error_pp':float(g.error_pp.abs().max()),
                   'n_targets':len(g)})
pd.DataFrame(metric).to_csv(OUT/'method_scores.csv',index=False)
summary={'smoke':arg.smoke,'outer_cells':len(held_cells),'seeds':list(seeds),
         'mean_scores_by_method':{m:float(g.macro_MAE_pp.mean()) for m,g in pd.DataFrame(metric).groupby('method')},
         'mean_unseen_event_next_voltage_RMSE_mV':float(np.mean(np.sqrt(pd.DataFrame(logs).held_event_next_voltage_loss_mV2))),
         'pretrain_entity_isolation':'entire held cell excluded for each fold, including future unlabeled events',
         'claim_limit':cfg['claim_limit']}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False),flush=True)
