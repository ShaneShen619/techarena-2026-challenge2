"""Nested scalar RBF and small MLP against the same D1 age prior."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn

ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
OUT = TASK / "runs/M9_D1_v15_scalar_models_v1"
OUT.mkdir(parents=True, exist_ok=False)
cfg = json.loads((TASK / "configs/m9_scalar_models.json").read_text())
torch.set_num_threads(2)
inp = np.load(TASK / "runs/M9_D1_v15_target_map_v1/target_inputs.npz")
meta = inp["metadata"].astype(float)
cells = inp["cell_ids"].astype(str)
ordinal = inp["target_ordinals"].astype(int)
panel = ROOT / "research/phase2_temperature_improvement/outputs/panel_main.csv"
assert hashlib.sha256(panel.read_bytes()).hexdigest() == "7188b662900f84312292a7062d6023e5eeb4f2e32798b6d61a3547ed40cdc59c"
label = pd.read_csv(panel, usecols=["cell_id", "target_ordinal", "target_soh_pp"]).set_index(["cell_id", "target_ordinal"])
y = np.array([label.loc[(c, int(o)), "target_soh_pp"] for c, o in zip(cells, ordinal)], float)
assert len(y) == 180 and len(set(cells)) == 6
anchor, ages = meta[:, 0], meta[:, 1:6]


def prepare(features, train, apply):
    a, b = features[train].copy(), features[apply].copy()
    med = np.array([np.nanmedian(col) if np.isfinite(col).any() else 0.0 for col in a.T])
    a = np.where(np.isfinite(a), a, med)
    b = np.where(np.isfinite(b), b, med)
    mu, sd = a.mean(0), a.std(0)
    sd[sd < 1e-8] = 1
    return (a - mu) / sd, (b - mu) / sd


def age_fit(train, apply):
    a, b = prepare(ages, train, apply)
    a = np.c_[np.ones(len(a)), a]
    b = np.c_[np.ones(len(b)), b]
    alpha = 100.0
    beta = np.linalg.solve(a.T @ a + np.diag([0] + [alpha] * (a.shape[1] - 1)) + np.eye(a.shape[1]) * 1e-9,
                           a.T @ (y[train] - anchor[train]))
    return anchor[apply] + b @ beta


def rbf_predict(train, test, length, penalty):
    age_train, age_test = age_fit(train, train), age_fit(train, test)
    a, b = prepare(meta, train, test)
    sq = ((a[:, None, :] - a[None, :, :]) ** 2).mean(2)
    cross = ((b[:, None, :] - a[None, :, :]) ** 2).mean(2)
    kernel = np.exp(-sq / (2 * length ** 2))
    coef = np.linalg.solve(kernel + np.eye(len(a)) * penalty, y[train] - age_train)
    return age_test + np.clip(np.exp(-cross / (2 * length ** 2)) @ coef, -10, 10)


class ScalarResidual(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(8, 32), nn.ReLU(), nn.Linear(32, 16), nn.ReLU(), nn.Linear(16, 1))

    def forward(self, x):
        return 10 * torch.tanh(self.net(x).squeeze(1))


rows, selected, train_logs = [], [], []
for held in np.unique(cells):
    train = np.flatnonzero(cells != held)
    test = np.flatnonzero(cells == held)
    age_train, age_test = age_fit(train, train), age_fit(train, test)
    scores = []
    for length in cfg["RBF"]["length_scales"]:
        for penalty in cfg["RBF"]["penalties"]:
            inner = []
            for valcell in np.unique(cells[train]):
                valid = train[cells[train] == valcell]
                fit = train[cells[train] != valcell]
                forecast = rbf_predict(fit, valid, length, penalty)
                inner.append(float(np.mean(abs(forecast - y[valid]))))
            scores.append((float(np.mean(inner)), float(length), float(penalty)))
    best = min(scores)
    selected.append({"held_cell": held, "inner_macro_MAE_pp": best[0],
                     "length_scale": best[1], "penalty": best[2]})
    rbf = rbf_predict(train, test, best[1], best[2])
    for method, prediction in (("fixed_age_ridge", age_test), ("scalar_RBF", rbf)):
        for j, i in enumerate(test):
            rows.append({"cell_id": cells[i], "target_ordinal": ordinal[i], "held_cell": held, "seed": -1,
                         "method": method, "target_soh_pp": y[i], "pred_soh_pp": prediction[j],
                         "error_pp": prediction[j] - y[i]})
    xtrain, xtest = prepare(meta, train, test)
    xtrain = torch.tensor(xtrain.astype(np.float32))
    xtest = torch.tensor(xtest.astype(np.float32))
    residual = torch.tensor((y[train] - age_train).astype(np.float32))
    for seed in cfg["MLP"]["seeds"]:
        torch.manual_seed(seed)
        net = ScalarResidual()
        opt = torch.optim.AdamW(net.parameters(), lr=cfg["MLP"]["learning_rate"],
                                weight_decay=cfg["MLP"]["weight_decay"])
        rng = np.random.default_rng(seed)
        losses = []
        for epoch in range(cfg["MLP"]["epochs"]):
            perm = rng.permutation(len(train))
            epoch_losses = []
            for block in np.array_split(perm, max(1, int(np.ceil(len(perm) / cfg["MLP"]["batch_targets"])))):
                opt.zero_grad()
                loss = nn.functional.smooth_l1_loss(net(xtrain[block]), residual[block])
                loss.backward()
                opt.step()
                epoch_losses.append(float(loss.item()))
            losses.append(float(np.mean(epoch_losses)))
        with torch.no_grad():
            prediction = age_test + net(xtest).numpy()
        for j, i in enumerate(test):
            rows.append({"cell_id": cells[i], "target_ordinal": ordinal[i], "held_cell": held, "seed": seed,
                         "method": "scalar_MLP", "target_soh_pp": y[i], "pred_soh_pp": float(prediction[j]),
                         "error_pp": float(prediction[j] - y[i])})
        train_logs.append({"held_cell": held, "seed": seed, "initial_loss": losses[0], "final_loss": losses[-1]})
    print(held, "RBF", round(float(np.mean(abs(rbf-y[test]))), 3), "MLP seeds",
          [round(float(pd.DataFrame(rows).loc[lambda q: q.held_cell.eq(held) & q.method.eq("scalar_MLP") & q.seed.eq(s)].error_pp.abs().mean()), 3)
           for s in cfg["MLP"]["seeds"]], flush=True)

pred = pd.DataFrame(rows)
pred.to_csv(OUT / "predictions.csv", index=False)
pd.DataFrame(selected).to_csv(OUT / "selected_RBF.csv", index=False)
pd.DataFrame(train_logs).to_csv(OUT / "MLP_training_logs.csv", index=False)
metrics = []
for (method, seed), part in pred.groupby(["method", "seed"]):
    per = part.assign(abs_pp=part.error_pp.abs()).groupby("cell_id").abs_pp.mean()
    metrics.append({"method": method, "seed": int(seed), "macro_MAE_pp": float(per.mean()),
                    "worst_cell_MAE_pp": float(per.max()), "max_abs_error_pp": float(part.error_pp.abs().max())})
pd.DataFrame(metrics).to_csv(OUT / "method_scores.csv", index=False)
(OUT / "summary.json").write_text(json.dumps({"scores": metrics, "claim_limit": cfg["claim_limit"]},
                                                ensure_ascii=False, indent=2) + "\n")
