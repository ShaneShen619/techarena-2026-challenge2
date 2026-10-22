"""WP2: build the emulated views of every cell, record data facts and QC, check causality.

Reads the Challenge 1 files (read only). Writes cache/views/*.pkl and outputs/wp2_*.csv.
No estimator error is computed here; truth values are stored inside the views for WP3/WP4.

    python3 -I -B run_wp2_extract.py [--c1-dir DIR] [--cells A B ...] [--work DIR]
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src import baselines, c1io, model_adapter, store, view  # noqa: E402
from src.common import PROTOCOL  # noqa: E402

STEP = PROTOCOL["data"]["step_types"]


def facts(cell, raw):
    """Structural facts of the raw file (no labels)."""
    row = {"cell": cell, "rows": len(raw), "cycles": int(raw["cycle_number"].nunique()),
           "t_first": raw["absolute_time"].min(), "t_last": raw["absolute_time"].max(),
           "step_types": json.dumps(sorted(map(str, raw["step_type"].unique())))}
    for name, kind in (("chg", STEP["charge"]), ("dis", STEP["discharge"])):
        s = raw[raw["step_type"] == kind]
        dt = s.groupby("cycle_number")["absolute_time"].diff().dt.total_seconds().dropna()
        row[f"{name}_dt_median_s"] = float(dt.median()) if len(dt) else np.nan
        row[f"{name}_current_sign"] = float(np.sign(s["current_A"].median())) if len(s) else np.nan
        row[f"{name}_abs_current_median_A"] = float(s["current_A"].abs().median()) if len(s) else np.nan
        row[f"{name}_v_max"] = float(s["voltage_V"].max()) if len(s) else np.nan
        row[f"{name}_v_min"] = float(s["voltage_V"].min()) if len(s) else np.nan
    row["temperature_median_C"] = float(raw["temperature_C"].median())
    return row


def qc(cell, spec, vw):
    """Counts and detection rates of one view."""
    p = pd.DataFrame(vw.programs)
    row = {"cell": cell, "view": spec, "windows": len(vw.boundaries) - 1, "anchors": len(vw.anchors),
           "programs": len(p), "truth_targets": len(vw.truth), "label0": vw.label0, "eps0": vw.eps0,
           **{f"meta_{k}": v for k, v in vw.meta.items()}}
    if len(p):
        row["detected_share"] = float(p["detected"].mean())
        for key in ("robust", "robust_interp") + tuple(f"v{n}" for n in range(6)):
            row[f"finite_{key}"] = float(np.isfinite(p[key]).mean())
        for col in ("n_visible", "i_dis", "resistance"):
            row[f"{col}_median"] = float(p[col].median())
        row["anchor_top_first"] = vw.anchors[0]["top"]
        row["anchor_top_last"] = vw.anchors[-1]["top"]
    return row


def causality(cell, raw, vw, rng):
    """Rows after B_k replaced by noise: every estimator's prediction for B_k must be identical."""
    rows = []
    ks = [k for k in sorted(vw.truth) if k >= 1]
    for k in sorted({ks[0], ks[len(ks) // 2], ks[-1]} if ks else set()):
        noisy = raw.copy()
        fut = noisy["absolute_time"] > vw.boundaries[k]
        for col in ("voltage_V", "current_A", "step_capacity_Ah", "temperature_C"):
            noisy.loc[fut, col] = rng.uniform(-5, 120, int(fut.sum()))
        cut = view.build_view(noisy, cell)
        for key in ("robust", "robust_interp"):
            for scen in ("main", "gap", "no_steps"):
                a = model_adapter.predict(vw, k, scenario=scen, key=key)["q"]
                b = model_adapter.predict(cut, k, scenario=scen, key=key)["q"]
                rows.append({"cell": cell, "k": k, "est": f"model_{scen}", "key": key,
                             "full": a, "noised_future": b, "identical": a == b})
        for name, fn in (("E4", baselines.e4_baseline), ("E5", baselines.e5_trend)):
            a, b = fn(vw, k), fn(cut, k)
            rows.append({"cell": cell, "k": k, "est": name, "key": "-", "full": a,
                         "noised_future": b, "identical": a == b})
    return rows


def main():
    p = store.parser(__doc__)
    p.add_argument("--c1-dir", default=PROTOCOL["data"]["c1_dir_default"])
    p.add_argument("--cells", nargs="*", default=PROTOCOL["data"]["cells"])
    args = p.parse_args()
    cache, out = store.dirs(args.work)
    rng = np.random.default_rng(PROTOCOL["controls"]["seed"])
    fact_rows, qc_rows, caus_rows = [], [], []
    for cell in args.cells:
        t0 = time.time()
        raw = c1io.read_cell(args.c1_dir, cell)
        fact_rows.append(facts(cell, raw))
        for spec, kw in store.VIEW_SPECS.items():
            vw = view.build_view(raw, cell, **kw)
            store.save_view(cache, cell, spec, vw)
            qc_rows.append(qc(cell, spec, vw))
            if spec == store.PRIMARY:
                caus_rows += causality(cell, raw, vw, rng)
        print(f"{cell}: {len(raw)} rows, {time.time() - t0:.0f} s", flush=True)
    pd.DataFrame(fact_rows).to_csv(out / "wp2_facts.csv", index=False)
    pd.DataFrame(qc_rows).to_csv(out / "wp2_qc.csv", index=False)
    caus = pd.DataFrame(caus_rows)
    caus.to_csv(out / "wp2_causality.csv", index=False)
    ok = bool(caus["identical"].all()) if len(caus) else False
    print(f"causality: {int(caus['identical'].sum()) if len(caus) else 0}/{len(caus)} identical")
    if not ok:
        sys.exit("causality check failed: see outputs/wp2_causality.csv")


if __name__ == "__main__":
    main()
