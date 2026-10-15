"""Build (label capacity, step-to-top distance) series for LIC 0.1C RPTs and ESSL packs/cells; save to beta_series.csv."""
import pandas as pd, numpy as np, glob, os
CONV = "/Users/shane/Desktop/Arena_1013_model/external_data/_converted"
def step_pos(q, v, nominal, lo_f, hi_f, sign, sm_per100=2.0):
    o = np.argsort(q); q, v = q[o], v[o]; qq, i = np.unique(q, return_index=True); v = v[i]
    h = nominal / 400; g = np.arange(0, qq.max(), h); vi = np.interp(g, qq, v)
    k = max(1, int(round(sm_per100 * nominal / 100 / h)))
    s = np.gradient(np.convolve(vi, np.ones(k) / k, mode="same"), g) * sign
    m = (g > lo_f * nominal) & (g < hi_f * nominal)
    return float(g[m][np.argmax(s[m])]) if m.any() else np.nan
def main():
    rows = []
    # LIC: independent 0.1C RPT label; charge- and discharge-direction steps
    c = pd.read_parquet("lic_curves.parquet")
    chg = [g for _, g in c[c.kind == "rpt_chg"].groupby("seg")]; dis = [g for _, g in c[c.kind == "rpt_dis"].groupby("seg")]
    for g in dis:
        Q = g.q.max()
        if abs(Q - 280.0) < 0.05: continue                       # truncated RPT
        prev = [h for h in chg if h.t0.iloc[0] < g.t0.iloc[0]]
        if not prev: continue
        h = prev[-1]; Qc = h.q.max()
        rows.append(dict(src="LIC_RPT", unit="cell", x=g.t0.iloc[0], Q=Q, nominal=280.0,
                         d_chg=Qc - step_pos(h.q.values, h.V.values, 280, .45, .80, 1),
                         d_dis=step_pos(g.q.values, g.V.values, 280, .20, .55, -1)))
    # ESSL: label = same-cycle charge Ah; charge-direction step only
    for f in sorted(glob.glob(CONV + "/ESSL*/*/*__timeseries.parquet")):
        T = pd.read_parquet(f); vcol = "Vpack" if "Vpack" in T else "voltage(V)"
        nom = 105.0 if "ESSL2" in f else 102.0
        ncell = (16 if "ESSL1" in f else 15) if "Vpack" in T else 1
        name = os.path.basename(f).split("__")[0]
        for it, g in T.groupby("item"):
            q = g["charge_capacity(Ah)"].values; v = g[vcol].values / ncell
            if g["SOC"].iloc[0] > 0.05 or len(q) < 60 or q.max() < 0.6 * nom: continue
            rows.append(dict(src=("ESSL1" if "ESSL1" in f else "ESSL2") + "_" + name, unit="pack" if ncell > 1 else "cell",
                             x=it, Q=q.max(), nominal=nom, d_chg=q.max() - step_pos(q, v, nom, .50, .80, 1), d_dis=np.nan))
    pd.DataFrame(rows).to_csv("beta_series.csv", index=False)
    print(pd.DataFrame(rows).groupby("src").size())


if __name__ == "__main__":
    main()
