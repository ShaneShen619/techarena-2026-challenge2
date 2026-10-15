"""Per-cell charge-direction step inside ESSL packs; which aggregation of cell step-to-top distances tracks pack Q."""
import pandas as pd, numpy as np, sys
sys.path.insert(0, "."); from beta_series import step_pos  # noqa: E402  (re-use detector)
CONV = "/Users/shane/Desktop/Arena_1013_model/external_data/_converted"
for name, nom, ncell in [("ESSL1/pack/Pack#1", 102.0, 16), ("ESSL2/pack/Pack#2", 105.0, 15)]:
    T = pd.read_parquet(f"{CONV}/{name}__timeseries.parquet"); rows = []
    for it, g in T.groupby("item"):
        q = g["charge_capacity(Ah)"].values
        if g["SOC"].iloc[0] > 0.05 or len(q) < 60 or q.max() < 0.6 * nom: continue
        r = dict(item=it, Q=q.max())
        vend = {}
        for c in range(1, ncell + 1):
            v = g[f"V{c}"].values.astype(float)
            r[f"d{c}"] = q.max() - step_pos(q, v, nom, .50, .80, 1); vend[c] = v[-1]
        r["d_packV"] = q.max() - step_pos(q, g["Vpack"].values / ncell, nom, .50, .80, 1)
        r["top_cell"] = max(vend, key=vend.get)
        rows.append(r)
    D = pd.DataFrame(rows); dc = D[[f"d{c}" for c in range(1, ncell + 1)]]
    D["d_mean"] = dc.mean(1); D["d_median"] = dc.median(1); D["d_min"] = dc.min(1); D["d_max"] = dc.max(1)
    D["d_topcell"] = [D.loc[i, f"d{int(t)}"] for i, t in zip(D.index, D.top_cell)]
    Q0 = D.Q.iloc[:15].median(); D = D[(1 - D.Q / Q0) * 100 <= 8.5]
    sm = D.rolling(15, center=True, min_periods=8).median().dropna()
    print(f"== {name}: n={len(D)}, fade to {(1 - sm.Q.min() / Q0) * 100:.1f}%, top-limiting cell counts:", D.top_cell.value_counts().head(4).to_dict())
    for k in ["d_packV", "d_mean", "d_median", "d_min", "d_max", "d_topcell"]:
        b = np.polyfit(sm[k], sm.Q, 1)[0]; r2 = np.corrcoef(sm[k], sm.Q)[0, 1] ** 2
        noise = (D[k] - D[k].rolling(15, center=True, min_periods=1).median()).abs().median()
        print(f"   {k:10s} slope dQ/dd {b:5.2f}  R2 {r2:.2f}  single-cycle noise {noise:.2f} Ah")
    cs = [np.polyfit(sm[f"d{c}"], sm.Q, 1)[0] for c in range(1, ncell + 1)]
    print("   per-cell slopes:", np.round(cs, 2))
