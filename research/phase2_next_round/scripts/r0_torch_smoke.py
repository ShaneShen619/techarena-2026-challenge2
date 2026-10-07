"""Minimal fixed-config tensor forward/backward smoke; never used for model selection."""
from __future__ import annotations
import hashlib, json, os, platform
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
OLD = ROOT / "research/phase2_method_exploration"
OUT = TASK / "runs/R0_torch_smoke_v1"
OUT.mkdir(parents=True, exist_ok=False)

seq_path = OLD / "runs/M9_D1_v15_inputs_v1/native_sequences.npz"
data = np.load(seq_path)
x = torch.tensor(data["X"][:8].astype(np.float32))
torch.manual_seed(20260929)
net = torch.nn.Sequential(
    torch.nn.Conv1d(5, 8, 3, padding=1),
    torch.nn.ReLU(),
    torch.nn.AdaptiveAvgPool1d(1),
    torch.nn.Flatten(),
    torch.nn.Linear(8, 1),
)
optim = torch.optim.Adam(net.parameters(), lr=1e-3)
target = torch.linspace(-1, 1, len(x)).reshape(-1, 1)
before = float(torch.nn.functional.mse_loss(net(x.transpose(1, 2)), target))
optim.zero_grad()
loss = torch.nn.functional.mse_loss(net(x.transpose(1, 2)), target)
loss.backward(); optim.step()
after = float(torch.nn.functional.mse_loss(net(x.transpose(1, 2)), target))
ckpt = OUT / "smoke.pt"
torch.save(net.state_dict(), ckpt)
clone = type(net)(*[]) if False else torch.nn.Sequential(
    torch.nn.Conv1d(5, 8, 3, padding=1), torch.nn.ReLU(),
    torch.nn.AdaptiveAvgPool1d(1), torch.nn.Flatten(), torch.nn.Linear(8, 1))
clone.load_state_dict(torch.load(ckpt, map_location="cpu", weights_only=True))
delta = float(torch.max(torch.abs(net(x.transpose(1, 2))-clone(x.transpose(1, 2)))))
summary = {
    "purpose": "fixed-config execution smoke only; not model selection or capacity evidence",
    "python": platform.python_version(), "torch": torch.__version__,
    "device": "cpu", "threads": torch.get_num_threads(),
    "input_shape": list(x.shape), "loss_before": before, "loss_after": after,
    "reload_max_abs_diff": delta,
    "source_sha256": hashlib.sha256(seq_path.read_bytes()).hexdigest(),
    "cache_root": os.environ.get("XDG_CACHE_HOME", "")
}
assert np.isfinite(before) and np.isfinite(after) and delta == 0.0
(OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary))
