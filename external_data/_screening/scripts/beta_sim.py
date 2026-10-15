"""Simulate the V2 in-month update on external series: checkpoints every ~1.2 % fade up to ~8.5 %;
predict Q_{k+1} = Q_k + beta * (d_{k+1} - d_k) with several beta rules. Errors in pp of nominal."""
import pandas as pd, numpy as np
S = pd.read_csv("beta_series.csv"); S = S[(S.Q > 0) & (S.Q < 1.2 * S.nominal)]
def shrink(pairs, b0, tau):
    if not pairs: return b0
    x, q = np.array(pairs, float).T; s = (x ** 2).sum()
    return (tau * b0 + s * (x * q).sum() / s) / (tau + s) if s > 0 else b0
rows = []
for src, g in S.groupby("src"):
    g = g.sort_values("x").reset_index(drop=True); nom = g.nominal.iloc[0]; tau = (nom / 100) ** 2
    w = 15 if len(g) > 100 else 1
    Qs = g.Q.rolling(w, center=True, min_periods=1).median(); Q0 = Qs.iloc[:max(w, 1)].median()
    fade = (1 - Qs / Q0) * 100
    for upd in ["d_chg", "d_dis"]:
        if g[upd].isna().all(): continue
        cal = "d_chg"                                   # V2 calibrates beta on charge-direction steps
        idx = [int((fade - f).abs().idxmin()) for f in np.arange(0, 8.6, 1.2)]
        idx = sorted(set(i for i in idx if abs(fade[i] - fade[idx[0]]) >= 0 or True))
        if len(idx) < 5: continue
        def val(col, i):                                # median of 3 cycles around a checkpoint (1 for LIC)
            lo, hi = max(0, i - 1), min(len(g), i + 2) if w > 1 else i + 1
            return float(g[col].iloc[lo:hi].median())
        Q = [val("Q", i) for i in idx]; dC = [val(cal, i) for i in idx]; dU = [val(upd, i) for i in idx]
        for k in range(1, len(idx) - 1):                # predict checkpoint k+1 from k
            pairs = [(dC[j] - dC[0], Q[j] - Q[0]) for j in range(1, k + 1)]
            b_v2 = shrink(pairs, 1.0, tau)
            dd = dU[k + 1] - dU[k]; true = Q[k + 1]
            for rule, b in [("persist", 0.0), ("beta1", 1.0), ("beta1.3", 1.3), ("v2_shrink", b_v2)]:
                rows.append(dict(src=src, upd=upd[2:], k=k, rule=rule, beta=b, err_pp=(Q[k] + b * dd - true) / nom * 100))
R = pd.DataFrame(rows); R.to_csv("beta_sim.csv", index=False)
R["ae"] = R.err_pp.abs()
t = R.pivot_table(index=["src", "upd"], columns="rule", values="ae", aggfunc="mean").round(3)
print(t.to_string())
cells = R[R.src.str.contains("ESSL")]
print("\nESSL all series, MAE pp by rule:", cells.groupby("rule").ae.mean().round(3).to_dict())
print("ESSL median per-series MAE:", cells.groupby(["src", "rule"]).ae.mean().groupby("rule").median().round(3).to_dict())
print("v2 beta distribution at last k (ESSL):", R[(R.rule == "v2_shrink") & R.src.str.contains("ESSL")].groupby("src").beta.last().describe().round(2).to_dict())
