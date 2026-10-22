"""Graphite-step position vs total charge capacity in ESSL charge curves -> beta = dQtot / d(top-to-step)."""
import pandas as pd, numpy as np, glob
def feats(q, v, qtot, lo, hi):
    grid = np.arange(1, qtot - 1, 0.5); vi = np.interp(grid, q, v)
    dv = np.gradient(np.convolve(vi, np.ones(5) / 5, mode="same"), grid)
    m = (grid > lo) & (grid < hi)
    return grid[m][np.argmax(dv[m])] if m.any() else np.nan
for f in sorted(glob.glob("ESSL1/*/*__timeseries.parquet")) + ["ESSL2/pack/Pack#2__timeseries.parquet"]:
    T = pd.read_parquet(f); vcol = "Vpack" if "Vpack" in T else "voltage(V)"
    rows = []
    for it, g in T.groupby("item"):
        q = g["charge_capacity(Ah)"].values; v = g[vcol].values; qtot = q.max()
        if g["SOC"].iloc[0] > 0.05 or len(q) < 60 or not np.all(np.diff(q) >= -1e-6): continue
        rows.append((it, qtot, feats(q, v, qtot, 8, 30), feats(q, v, qtot, 35, qtot - 12)))
    R = pd.DataFrame(rows, columns=["item", "Q", "qA", "qB"]).dropna()
    if len(R) < 30: print(f, "too few full charges", len(R)); continue
    R = R.rolling(15, center=True).median().dropna()            # damp cycle-to-cycle noise
    out = [f.split("__")[0], f"n={len(R)}", f"Q {R.Q.iloc[0]:.1f}->{R.Q.iloc[-1]:.1f}"]
    for k in ["qA", "qB"]:
        top = R.Q - R[k]; b, a = np.polyfit(top, R.Q, 1); r2 = np.corrcoef(top, R.Q)[0, 1] ** 2
        share = (top.iloc[0] - top.iloc[-1]) / (R.Q.iloc[0] - R.Q.iloc[-1])
        out.append(f"{k}: step@{R[k].iloc[0]:.1f}->{R[k].iloc[-1]:.1f} Ah, top-share {share:.2f}, beta {b:.2f} (R2 {r2:.2f})")
    print(" | ".join(out))
