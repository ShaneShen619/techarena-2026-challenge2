"""Cache LIC raw CSV (1.1 GB) to npz in chunks. Usage: python3 -I -B lic_cache.py <LIC_aging_data.csv> <out.npz>"""
import sys
import numpy as np
import pandas as pd

src, out = sys.argv[1], sys.argv[2]
parts = {k: [] for k in ("t", "V", "I", "Tm", "Te")}
for ch in pd.read_csv(src, chunksize=2_000_000, header=0, names=list(parts), dtype="float64"):
    for k in parts:
        parts[k].append(ch[k].to_numpy(np.float64 if k in ("t", "I") else np.float32))
np.savez(out, **{k: np.concatenate(v) for k, v in parts.items()})
print("rows", sum(len(x) for x in parts["t"]))
