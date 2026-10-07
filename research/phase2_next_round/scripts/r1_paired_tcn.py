"""Matched D1-v1.5 fine-tuned TCN ablations with raw-voltage pretrain targets.

Each condition uses identical splits, seeds, optimizer and epoch budget. When a
channel is hidden it is hidden in both pretraining and supervised phases; the
self-supervised target remains the next *raw* voltage increment. Output is
checkpointed per held-cell/seed so an interrupted condition can resume.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, sys, time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
OLD = ROOT / "research/phase2_method_exploration"
sys.path.insert(0, str(OLD / "src"))
from m7_tcn import ChargeEncoder, CapacityResidualNet

parser = argparse.ArgumentParser()
parser.add_argument("--condition", required=True)
args = parser.parse_args()
new_cfg = json.loads((TASK / "configs/r1_paired_tcn.json").read_text())
if args.condition not in new_cfg["conditions"]:
    raise SystemExit(f"unknown condition: {args.condition}")
condition = new_cfg["conditions"][args.condition]
cfg = json.loads((OLD / "configs/m9_d1_v15_representation.json").read_text())
OUT = TASK / "runs" / f"R1_paired_TCN_{args.condition}_v1"
OUT.mkdir(parents=True, exist_ok=True)
torch.set_num_threads(2)

seq = np.load(OLD / "runs/M9_D1_v15_inputs_v1/native_sequences.npz")
inp = np.load(OLD / "runs/M9_D1_v15_target_map_v1/target_inputs.npz")
X_raw = seq["X"].astype(np.float32)
X_in = X_raw.copy()
for channel in condition["zero_channels"]:
    X_in[:, :, int(channel)] = 0.0
event_cells = seq["cell_ids"].astype(str)
all_in = torch.tensor(X_in)
all_raw = torch.tensor(X_raw)
slots_np = inp["indices"].astype(np.int64)
slots = torch.tensor(slots_np)
meta = inp["metadata"].astype(np.float32).copy()
for column in condition.get("zero_metadata_columns", []):
    meta[:, int(column)] = 0.0
cells = inp["cell_ids"].astype(str)
ordinal = inp["target_ordinals"].astype(int)
panel = ROOT / "research/phase2_temperature_improvement/outputs/panel_main.csv"
assert hashlib.sha256(panel.read_bytes()).hexdigest() == "7188b662900f84312292a7062d6023e5eeb4f2e32798b6d61a3547ed40cdc59c"
labels = pd.read_csv(panel, usecols=["cell_id", "target_ordinal", "target_soh_pp"]).set_index(["cell_id", "target_ordinal"])
y = np.array([labels.loc[(c, int(o)), "target_soh_pp"] for c, o in zip(cells, ordinal)], np.float32)
anchor = meta[:, 0].astype(float)
ages = meta[:, 1:6].astype(float)
alpha_table = pd.read_csv(OLD / "runs/M9_D1_v15_linear_v1/inner_alpha_selections.csv")

def ridge(train, apply, target, alpha):
    a, b = ages[train].copy(), ages[apply].copy()
    med = np.array([np.nanmedian(v) if np.isfinite(v).any() else 0.0 for v in a.T])
    a = np.where(np.isfinite(a), a, med); b = np.where(np.isfinite(b), b, med)
    mu, sd = a.mean(0), a.std(0); sd[sd < 1e-8] = 1
    a = np.c_[np.ones(len(a)), (a-mu)/sd]; b = np.c_[np.ones(len(b)), (b-mu)/sd]
    penalty = np.diag([0.0] + [alpha] * (a.shape[1]-1))
    beta = np.linalg.solve(a.T@a + penalty + np.eye(a.shape[1])*1e-9, a.T@target[train])
    return b@beta

def pretrain_loss(encoder, indices):
    source = all_in[indices]
    raw = all_raw[indices]
    _, forecast = encoder(source)
    valid = raw[:, :, 4]
    pair = valid[:, :-1] * valid[:, 1:]
    target = (raw[:, 1:, 0] - raw[:, :-1, 0]) * 100.0
    error = (forecast[:, :-1] - target) * pair
    return (error**2).sum() / pair.sum().clamp(min=1)

def pretrain(held, seed):
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    encoder = ChargeEncoder(cfg["temporal_encoder"]["width"])
    opt = torch.optim.AdamW(encoder.parameters(), lr=cfg["temporal_encoder"]["pretrain_learning_rate"])
    train_events = np.flatnonzero(event_cells != held)
    held_events = np.flatnonzero(event_cells == held)
    losses=[]; start=time.perf_counter()
    for _ in range(cfg["temporal_encoder"]["pretrain_epochs"]):
        encoder.train(); per=[]
        for block in np.array_split(rng.permutation(train_events), max(1, int(np.ceil(len(train_events)/cfg["temporal_encoder"]["pretrain_batch_events"])))):
            opt.zero_grad(); loss=pretrain_loss(encoder, block); loss.backward(); opt.step(); per.append(float(loss.item()))
        losses.append(float(np.mean(per)))
    encoder.eval()
    with torch.no_grad():
        held_loss = float(np.mean([float(pretrain_loss(encoder, b).item()) for b in np.array_split(held_events, max(1, int(np.ceil(len(held_events)/128))))]))
    return encoder, losses, held_loss, time.perf_counter()-start

def fit_head(encoder, train, test, prior, seed, scaled):
    torch.manual_seed(seed+100)
    net = CapacityResidualNet(copy.deepcopy(encoder), meta_dim=scaled.shape[1], width=cfg["temporal_encoder"]["width"])
    opt = torch.optim.AdamW(net.parameters(), lr=cfg["supervised_learning_rate"], weight_decay=cfg["supervised_weight_decay"])
    rng=np.random.default_rng(seed+100); target=torch.tensor((y-prior).astype(np.float32)); meta_t=torch.tensor(scaled)
    weights=np.ones(len(cells), np.float32); weights[ordinal>=21]=float(condition["late_weight"]); weights_t=torch.tensor(weights)
    losses=[]; start=time.perf_counter()
    for _ in range(cfg["supervised_epochs"]):
        net.train(); per=[]
        for block in np.array_split(rng.permutation(train), max(1, int(np.ceil(len(train)/cfg["supervised_batch_targets"])))):
            opt.zero_grad(); corr=net(all_in, slots[block], meta_t[block])
            elem=torch.nn.functional.smooth_l1_loss(corr, target[block], reduction="none")
            loss=(elem*weights_t[block]).sum()/weights_t[block].sum(); loss.backward(); opt.step(); per.append(float(loss.item()))
        losses.append(float(np.mean(per)))
    net.eval()
    with torch.no_grad():
        corr=np.concatenate([net(all_in, slots[b], meta_t[b]).numpy() for b in np.array_split(test,max(1,int(np.ceil(len(test)/64))))])
    return prior[test]+corr, losses, time.perf_counter()-start, net

pred_path=OUT/"predictions.csv"; log_path=OUT/"training_logs.csv"
existing=pd.read_csv(pred_path) if pred_path.exists() else pd.DataFrame()
done=set(zip(existing.get("held_cell",[]).astype(str), existing.get("seed",[]).astype(int))) if len(existing) else set()
for held in np.unique(cells):
    train=np.flatnonzero(cells!=held); test=np.flatnonzero(cells==held)
    alpha=float(alpha_table.loc[alpha_table.held_cell.eq(held)&alpha_table.method.eq("age_count_ridge"),"selected_alpha"].iloc[0])
    prior=anchor+ridge(train,np.arange(len(cells)),y-anchor,alpha)
    mu=np.nanmean(meta[train],axis=0); sd=np.nanstd(meta[train],axis=0); sd[sd<1e-8]=1
    scaled=((np.where(np.isfinite(meta),meta,mu)-mu)/sd).astype(np.float32)
    for seed in cfg["seeds"]:
        if (held,int(seed)) in done: continue
        encoder, preloss, heldloss, presec = pretrain(held,int(seed))
        prediction, headloss, headsec, net = fit_head(encoder,train,test,prior,int(seed),scaled)
        torch.save(net.state_dict(), OUT/f"model_{held}_{seed}.pt")
        rows=[]
        for j,i in enumerate(test):
            rows.append({"condition":args.condition,"cell_id":cells[i],"target_ordinal":int(ordinal[i]),"held_cell":held,"seed":int(seed),"method":f"TCN_finetune_{args.condition}","target_soh_pp":float(y[i]),"age_prior_pp":float(prior[i]),"pred_soh_pp":float(prediction[j]),"error_pp":float(prediction[j]-y[i]),"late":bool(ordinal[i]>=21)})
        pd.DataFrame(rows).to_csv(pred_path, mode="a", header=not pred_path.exists(), index=False)
        log=pd.DataFrame([{"condition":args.condition,"held_cell":held,"seed":int(seed),"pretrain_initial_loss_mV2":preloss[0],"pretrain_final_loss_mV2":preloss[-1],"held_event_next_voltage_loss_mV2":heldloss,"head_initial_loss":headloss[0],"head_final_loss":headloss[-1],"pretrain_seconds":presec,"head_seconds":headsec}])
        log.to_csv(log_path,mode="a",header=not log_path.exists(),index=False)
        print(args.condition,held,seed,"MAE",round(float(np.mean(abs(prediction-y[test]))),4),flush=True)

pred=pd.read_csv(pred_path)
assert len(pred)==len(np.unique(cells))*len(cfg["seeds"])*30
ens=pred.groupby(["cell_id","target_ordinal"],as_index=False).agg(target_soh_pp=("target_soh_pp","first"),pred_soh_pp=("pred_soh_pp","mean"),late=("late","first"))
ens["error_pp"]=ens.pred_soh_pp-ens.target_soh_pp
ens.to_csv(OUT/"ensemble_predictions.csv",index=False)
per=ens.assign(abs_pp=ens.error_pp.abs()).groupby("cell_id").abs_pp.mean()
late=ens.loc[ens.late].assign(abs_pp=lambda d:d.error_pp.abs()).groupby("cell_id").abs_pp.mean()
summary={"condition":args.condition,"zero_channels":condition["zero_channels"],"zero_metadata_columns":condition.get("zero_metadata_columns",[]),"late_weight":condition["late_weight"],"targets":len(ens),"cells":ens.cell_id.nunique(),"macro_MAE_pp":float(per.mean()),"worst_cell_MAE_pp":float(per.max()),"max_abs_error_pp":float(ens.error_pp.abs().max()),"p95_abs_error_pp":float(ens.error_pp.abs().quantile(.95)),"late_macro_MAE_pp":float(late.mean()),"late_worst_cell_MAE_pp":float(late.max()),"per_cell_MAE_pp":{k:float(v) for k,v in per.items()},"pretraining_target":"next raw voltage increment; held physical cell excluded","claim_limit":new_cfg["claim_limit"]}
(OUT/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(summary,ensure_ascii=False),flush=True)
