#!/usr/bin/env python3
"""Read-only structural audit of the authors' public HDF5/MAT dataset."""
import json
from pathlib import Path

import h5py
import numpy as np

root = Path(__file__).resolve().parent
with h5py.File(root / "sources/BatPackdata.mat") as f:
    g = f["BatPackdata"]
    vehicles = []
    for i in range(g["SOH"].shape[0]):
        data = f[g["data"][i, 0]]["Inf"]
        blocks = [f[data[j, 0]] for j in range(data.shape[0])]
        numeric_blocks = [b for b in blocks if isinstance(b, h5py.Group) and "Q" in b]
        fields = sorted({name for b in numeric_blocks for name in b.keys()})
        q_block_ends = [float(np.asarray(b["Q"]).ravel()[-1]) for b in numeric_blocks]
        vehicles.append({
            "vehicle": i + 1,
            "rated_capacity_Ah_MAT": float(f[g["Cn"][i, 0]][0, 0]),
            "n_series_cells_MAT": int(f[g["Ncell"][i, 0]][0, 0]),
            "SOH_percent_MAT": float(f[g["SOH"][i, 0]][0, 0] * 100),
            "charging_blocks": len(numeric_blocks),
            "raw_rows_across_blocks": sum(int(b["Q"].size) for b in numeric_blocks),
            "fields_per_block": fields,
            "sum_Q_block_ends_Ah": sum(q_block_ends),
        })

out = {
    "file": "sources/BatPackdata.mat",
    "interpretation": "one MAT entry per tested vehicle, one SOH field per vehicle; blocks/windows are not independent capacity labels",
    "vehicle_count": len(vehicles),
    "total_rows_across_blocks": sum(v["raw_rows_across_blocks"] for v in vehicles),
    "vehicles": vehicles,
    "vehicle_5_paper_and_README_vs_MAT": {
        "paper_and_README_Cn_Ah": 174,
        "paper_and_README_SOH_percent": 82.21,
        "MAT_Cn_Ah": vehicles[4]["rated_capacity_Ah_MAT"],
        "MAT_SOH_percent": vehicles[4]["SOH_percent_MAT"],
        "Q_Ah_sum_blocks": vehicles[4]["sum_Q_block_ends_Ah"],
        "Q_over_174_percent": vehicles[4]["sum_Q_block_ends_Ah"] / 174 * 100,
        "Q_over_147_percent": vehicles[4]["sum_Q_block_ends_Ah"] / 147 * 100,
    },
}
(root / "AUDIT_DENG_MAT.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
print(root / "AUDIT_DENG_MAT.json")
