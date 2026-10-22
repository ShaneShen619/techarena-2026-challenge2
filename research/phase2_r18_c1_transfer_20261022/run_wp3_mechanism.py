"""WP3: mechanism checks C2, C2b, C6, C7, C10, C11, C12 (descriptive; protocol.json).

Reads cache/views/*__w30.pkl. Writes outputs/wp3_windows.csv, wp3_per_cell.csv, wp3_summary.json.

    python3 -B run_wp3_mechanism.py [--work DIR]
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src import model_adapter, store  # noqa: E402
from src.common import PROTOCOL, mt  # noqa: E402

INFO = PROTOCOL["information_structure"]
KEYS = PROTOCOL["steps"]["keys_primary"]


def theil_sen(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    return mt._theil_sen(x, y) if len(x) >= 2 else np.nan


def ls_origin(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    return float((x * y).sum() / (x * x).sum()) if len(x) and (x * x).sum() > 0 else np.nan


def r2_origin(x, y, b):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 2 or not np.isfinite(b):
        return np.nan
    ss = ((y - y.mean()) ** 2).sum()
    return float(1 - ((y - b * x) ** 2).sum() / ss) if ss > 0 else np.nan


def scope(vw, k, level):
    lim = INFO["scope_primary_min_rel"] if level == "primary" else INFO["scope_extended_min_rel"]
    return k in vw.truth and vw.truth[k] >= lim * vw.label0


def window_rows(cell, vw):
    anchors = {a["m"]: a for a in vw.anchors}
    rows = []
    for k in sorted(vw.truth):
        row = {"cell": cell, "k": k, "truth": vw.truth[k], "truth_sd": vw.truth_sd[k],
               "scope_primary": scope(vw, k, "primary"), "scope_extended": scope(vw, k, "extended"),
               "fade": vw.label0 - vw.truth[k]}
        if k in anchors:
            row["anchor_q"] = anchors[k]["q"]
            row["anchor_top"] = anchors[k]["top"]
            row["eps"] = vw.truth[k] - anchors[k]["q"]
        if (k - 1) in anchors:
            base = vw.label0 if k - 1 == 0 else anchors[k - 1]["q"] + vw.eps0
            row["r"] = vw.truth[k] - base
        for key in KEYS:
            p = model_adapter.predict(vw, k, key=key)
            row[f"branch_{key}"] = p["branch"]
            row[f"x_{key}"] = p["x"] if p["branch"] == "phase" else np.nan
            row[f"beta_v2_{key}"] = p["beta_v2"] if p["branch"] == "phase" else np.nan
        rows.append(row)
    return rows


def step_noise(vw, key):
    """Median over windows of the residual SD of program depths around their Theil-Sen line."""
    sds = []
    for m in sorted({p["m"] for p in vw.programs}):
        ps = [p for p in vw.programs if p["m"] == m and p["detected"] and np.isfinite(p[key])]
        if len(ps) < 3:
            continue
        t = np.array([(p["t_end"] - ps[0]["t_end"]).total_seconds() / 86400 for p in ps])
        d = np.array([p[key] for p in ps])
        b = theil_sen(t, d)
        a = np.median(d - b * t)
        sds.append(float(np.std(d - a - b * t, ddof=1)))
    return float(np.median(sds)) if sds else np.nan


def per_cell(cell, vw, win):
    w = win[win["cell"] == cell]
    rate = re.search(r"_(0p5C|1C)(_|$)", cell)
    row = {"cell": cell, "c_rate": rate.group(1) if rate else "?",
           "windows_scored": int(len(w)), "windows_primary": int(w["scope_primary"].sum())}
    for level in ("primary", "extended"):
        s = w[w[f"scope_{level}"]]
        for key in KEYS:
            ph = s.dropna(subset=[f"x_{key}", "r"])
            x, r = ph[f"x_{key}"].to_numpy(), ph["r"].to_numpy()
            b = ls_origin(x, r)
            row[f"C2_beta_ls_{key}_{level}"] = b
            ok = np.abs(x) > 0
            row[f"C2_beta_median_ratio_{key}_{level}"] = float(np.median(r[ok] / x[ok])) if ok.any() else np.nan
            row[f"C2_r2_{key}_{level}"] = r2_origin(x, r, b)
            row[f"C2_resid_sd_{key}_{level}"] = float(np.std(r - b * x, ddof=1)) if len(x) >= 2 else np.nan
            row[f"C2_n_{key}_{level}"] = int(len(x))
            last = ph.sort_values("k").tail(1)
            row[f"C3_beta_v2_last_{key}_{level}"] = float(last[f"beta_v2_{key}"].iloc[0]) if len(last) else np.nan
        a = s.dropna(subset=["anchor_top", "anchor_q"])
        a0 = vw.anchors[0]
        dtop = a["anchor_top"].to_numpy() - a0["top"]
        row[f"C2b_beta_charge_anchor_{level}"] = ls_origin(dtop, a["anchor_q"].to_numpy() - a0["q"])
        row[f"C2b_beta_charge_truth_{level}"] = ls_origin(dtop, a["truth"].to_numpy() - vw.label0)
        e = s.dropna(subset=["eps"])
        row[f"C7_eps_drift_{level}"] = (float(np.polyfit(e["fade"], e["eps"], 1)[0])
                                        if len(e) >= 3 and e["fade"].std() > 0 else np.nan)
    row["C7_eps0"] = vw.eps0
    for key in KEYS + ["v0", "v4"]:
        row[f"C6_noise_{key}"] = step_noise(vw, key)
    full = [abs(p["robust"] - p["robust_full"]) for p in vw.programs
            if np.isfinite(p.get("robust_full", np.nan)) and np.isfinite(p["robust"])]
    row["C10_trunc_median_abs"] = float(np.median(full)) if full else np.nan
    depths = [p["robust"] for p in vw.programs if np.isfinite(p["robust"])]
    row["C12_share_below_27Ah"] = float(np.mean(np.array(depths) < 27.0)) if depths else np.nan
    row["detected_share"] = float(np.mean([p["detected"] for p in vw.programs])) if vw.programs else np.nan
    return row


def main():
    args = store.parser(__doc__).parse_args()
    cache, out = store.dirs(args.work)
    views = store.load_views(cache)
    if not views:
        sys.exit("no views: run run_wp2_extract.py first")
    win = pd.DataFrame([r for c, vw in views.items() for r in window_rows(c, vw)])
    win.to_csv(out / "wp3_windows.csv", index=False)
    cells = pd.DataFrame([per_cell(c, vw, win) for c, vw in views.items()])
    cells.to_csv(out / "wp3_per_cell.csv", index=False)
    summ = {"n_cells": len(cells), "references": {
        "pack_beta_V2": "1.06-1.51 (CK4-CK7)", "pack_round8_inverse_b": "1.34 (b 0.745, CI 0.674-0.765)",
        "essl_packs": "1.1-1.2", "pack_step_noise_ah": "0.012-0.036", "pack_eps_drift_bound": "-0.036 to +0.052"}}
    for col in cells.columns:
        if col.startswith(("C2", "C6", "C7", "C10", "C12", "detected")):
            v = pd.to_numeric(cells[col], errors="coerce")
            summ[col] = {"median": float(v.median()), "min": float(v.min()), "max": float(v.max())}
        if col.startswith(("C2_beta_ls", "C6_noise_robust")):
            summ[col + "_by_rate"] = {r: float(pd.to_numeric(g[col]).median()) for r, g in cells.groupby("c_rate")}
    for key in KEYS:
        b, v2 = cells[f"C2_beta_ls_{key}_primary"], cells[f"C3_beta_v2_last_{key}_primary"]
        gap = (v2 - b).abs()
        summ[f"C3_mismatch_median_abs_{key}"] = float(gap.median())
        summ[f"C3_mismatch_flag_{key}"] = bool(gap.median() > 0.30)
        summ[f"C3_mismatch_cells_over_0.30_{key}"] = [c for c, g in zip(cells["cell"], gap) if g > 0.30]
    with open(out / "wp3_summary.json", "w") as f:
        json.dump(summ, f, indent=2, default=str)
    pd.set_option("display.width", 220)
    print(cells.round(3).T.to_string())


if __name__ == "__main__":
    main()
