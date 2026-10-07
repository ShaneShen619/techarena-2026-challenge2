"""Matched TCN-from-scratch control with all time-varying charge channels hidden."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
OUT = TASK / "runs/M7_TCN_meta_only_v1"
OUT.mkdir(parents=True, exist_ok=False)
sys.path.insert(0, str(TASK / "src"))
from m7_tcn import ChargeEncoder, CapacityResidualNet

cfg = json.loads((TASK / "configs/m7_representation.json").read_text())
torch.set_num_threads(2)
seq = np.load(TASK / "runs/M7_sequences_v1/native_sequences.npz")
inp = np.load(TASK / "runs/M7_target_map_v1/target_inputs.npz")
X = seq["X"].astype(np.float32)
X[:, :, :4] = 0.0
all_events = torch.tensor(X)
slots = torch.tensor(inp["indices"].astype(np.int64))
meta = inp["metadata"].astype(np.float32)
cells = inp["cell_ids"].astype(str)
ordinal = inp["target_ordinals"].astype(int)
panel = ROOT / "research/phase2_temperature_improvement/outputs/panel_main.csv"
assert hashlib.sha256(panel.read_bytes()).hexdigest() == "7188b662900f84312292a7062d6023e5eeb4f2e32798b6d61a3547ed40cdc59c"
labels = pd.read_csv(panel, usecols=["cell_id", "target_ordinal", "target_soh_pp"]).set_index(["cell_id", "target_ordinal"])
y = np.array([labels.loc[(c, int(o)), "target_soh_pp"] for c, o in zip(cells, ordinal)], np.float32)
anchor = meta[:, 0]
ages = meta[:, 1:6]
alpha = pd.read_csv(TASK / "runs/M7_linear_representation_v1/inner_alpha_selections.csv")


def age_ridge(train, apply, strength):
    a = ages[train].astype(float)
    b = ages[apply].astype(float)
    median = np.array([np.nanmedian(col) if np.isfinite(col).any() else 0.0 for col in a.T])
    a = np.where(np.isfinite(a), a, median)
    b = np.where(np.isfinite(b), b, median)
    mean, std = a.mean(0), a.std(0)
    std[std < 1e-8] = 1
    a = np.c_[np.ones(len(a)), (a - mean) / std]
    b = np.c_[np.ones(len(b)), (b - mean) / std]
    penalty = np.diag([0] + [strength] * (a.shape[1] - 1))
    coef = np.linalg.solve(a.T @ a + penalty + np.eye(a.shape[1]) * 1e-9, a.T @ (y[train] - anchor[train]))
    return anchor[apply] + b @ coef


rows = []
logs = []
for held in np.unique(cells):
    train = np.flatnonzero(cells != held)
    test = np.flatnonzero(cells == held)
    strength = float(alpha.loc[alpha.held_cell.eq(held) & alpha.method.eq("age_count_ridge"), "selected_alpha"].iloc[0])
    prior = age_ridge(train, np.arange(len(cells)), strength)
    mu = np.nanmean(meta[train], axis=0)
    std = np.nanstd(meta[train], axis=0)
    std[std < 1e-8] = 1
    scaled = torch.tensor(((np.where(np.isfinite(meta), meta, mu) - mu) / std).astype(np.float32))
    target = torch.tensor((y - prior).astype(np.float32))
    for seed in cfg["seeds"]:
        # Identical scratch encoder and head initialization/training schedule as M7_TCN_v1.
        torch.manual_seed(seed + 999)
        encoder = ChargeEncoder(cfg["temporal_encoder"]["width"])
        torch.manual_seed(seed + 100)
        net = CapacityResidualNet(encoder, meta_dim=scaled.shape[1], width=cfg["temporal_encoder"]["width"])
        opt = torch.optim.AdamW(net.parameters(), lr=cfg["supervised_learning_rate"], weight_decay=cfg["supervised_weight_decay"])
        rng = np.random.default_rng(seed + 100)
        losses = []
        for epoch in range(cfg["supervised_epochs"]):
            net.train()
            perm = rng.permutation(train)
            batch_losses = []
            for block in np.array_split(perm, max(1, int(np.ceil(len(perm) / cfg["supervised_batch_targets"])))):
                opt.zero_grad()
                correction = net(all_events, slots[block], scaled[block])
                loss = torch.nn.functional.smooth_l1_loss(correction, target[block])
                loss.backward()
                opt.step()
                batch_losses.append(float(loss.item()))
            losses.append(float(np.mean(batch_losses)))
        net.eval()
        with torch.no_grad():
            correction = np.concatenate([net(all_events, slots[block], scaled[block]).numpy()
                                         for block in np.array_split(test, max(1, int(np.ceil(len(test) / 64))))])
        prediction = prior[test] + correction
        for j, i in enumerate(test):
            rows.append({"cell_id": cells[i], "target_ordinal": ordinal[i], "held_cell": held,
                         "seed": seed, "method": "TCN_scratch_meta_only", "target_soh_pp": float(y[i]),
                         "pred_soh_pp": float(prediction[j]), "error_pp": float(prediction[j] - y[i])})
        logs.append({"held_cell": held, "seed": seed, "initial_train_loss": losses[0], "final_train_loss": losses[-1]})
        print(held, seed, "MAE", round(float(np.mean(abs(prediction - y[test]))), 3), flush=True)

pred = pd.DataFrame(rows)
pred.to_csv(OUT / "predictions.csv", index=False)
pd.DataFrame(logs).to_csv(OUT / "training_logs.csv", index=False)
scores = []
for seed, part in pred.groupby("seed"):
    per = part.assign(abs_pp=part.error_pp.abs()).groupby("cell_id").abs_pp.mean()
    scores.append({"seed": int(seed), "macro_MAE_pp": float(per.mean()), "worst_cell_MAE_pp": float(per.max()),
                   "max_abs_error_pp": float(part.error_pp.abs().max())})
pd.DataFrame(scores).to_csv(OUT / "method_scores.csv", index=False)
(OUT / "summary.json").write_text(json.dumps({"method": "TCN_scratch_meta_only", "scores": scores,
    "status": "mechanism ablation on six development cells, not independent confirmation"}, ensure_ascii=False, indent=2) + "\n")
