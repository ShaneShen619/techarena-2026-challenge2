"""Frozen CK0 threshold sensitivity and published-table arithmetic checks."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
OUT = TASK / "runs" / "L6_window_table_20260929"
CK = ROOT / "data" / "checkups" / "CK0_reference_discharge.csv.gz"
YAGCI = TASK / "papers" / "D_trajectory" / "Yagci2025_large_LFP_aging.pdf"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(CK)
    v = d["voltage_V"].to_numpy()
    q = d["discharged_Ah"].to_numpy()

    def crossing(threshold):
        ix = np.flatnonzero(v <= threshold)
        return (float(q[ix[0]]), int(ix[0])) if len(ix) else (None, None)

    rows = []
    for high in np.round(np.arange(13.01, 13.261, .01), 3):
        low = round(float(high) - .01, 3)
        result = {"upper_V": float(high), "lower_V": low}
        valid = True
        for name, shift in (("minus2mV", -.002), ("nominal", 0), ("plus2mV", .002)):
            start, ix0 = crossing(float(high) + shift)
            end, ix1 = crossing(low + shift)
            dq = end-start if start is not None and end is not None and ix1 > ix0 else None
            result[name + "_Ah"] = dq
            if dq is None:
                valid = False
        result["valid"] = valid
        if valid and result["nominal_Ah"] >= .1:
            result["max_abs_relative_shift_pct"] = 100 * max(
                abs(result["minus2mV_Ah"]-result["nominal_Ah"]),
                abs(result["plus2mV_Ah"]-result["nominal_Ah"])) / result["nominal_Ah"]
        else:
            result["max_abs_relative_shift_pct"] = None
        rows.append(result)
    with (OUT / "window_sensitivity.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

    # Direct transcription of Yagci et al. 2025, printed p.14, Table 3; not raw data.
    table3 = {"35C_cycle": [10.6, 11.4], "35C_calendar75": [8.6, 6.4],
              "35C_calendar100": [8.0, 7.6], "50C_cycle": [22.2, 22.4],
              "50C_calendar75": [14.4, 12.2], "50C_calendar100": [13.1, 14.9]}
    group_means = {k: sum(x)/len(x) for k, x in table3.items()}
    temp_means = {"35C_all6": sum(sum(v) for k, v in table3.items() if k.startswith("35C"))/6,
                  "50C_all6": sum(sum(v) for k, v in table3.items() if k.startswith("50C"))/6}
    valid_rows = [r for r in rows if r["max_abs_relative_shift_pct"] is not None]
    res = {"run_id": "L6_window_table_20260929", "ck_sha256": sha(CK), "yagci_pdf_sha256": sha(YAGCI),
           "window_count": len(rows), "analyzable_count": len(valid_rows),
           "window_median_max_abs_relative_shift_pct": float(np.median([r["max_abs_relative_shift_pct"] for r in valid_rows])) if valid_rows else None,
           "window_p90_max_abs_relative_shift_pct": float(np.quantile([r["max_abs_relative_shift_pct"] for r in valid_rows], .9)) if valid_rows else None,
           "window_max_max_abs_relative_shift_pct": max([r["max_abs_relative_shift_pct"] for r in valid_rows], default=None),
           "yagci_table3_group_means_pct": group_means,
           "yagci_table3_temperature_means_pct": temp_means,
           "limits": "CK0 is one full low-rate discharge; 2mV is a hypothetical threshold shift, not measured sensor error. Yagci values are printed Table 3, not raw-data replication."}
    (OUT / "result.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
