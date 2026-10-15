"""WP4: time / throughput / temperature axes at each independent capacity point of the cycling datasets.
Usage: python3 -I axes_cycling.py <external_data_dir> <out_csv>"""
import sys

import numpy as np
import pandas as pd

E, OUT = sys.argv[1], sys.argv[2]
rows = []

# ---------------------------------------------------------------- LIC 280 Ah
lic = pd.read_csv(f"{E}/LIC_aging/LIC_aging_data.csv", dtype="float32")
lic.columns = ["t", "V", "I", "Tm", "Te"]
t = lic["t"].to_numpy(np.float64)
I = lic["I"].to_numpy(np.float64)
dt = np.diff(t, prepend=t[0]).clip(0, 10)
sign = np.where(I > 1.0, 1, np.where(I < -1.0, -1, 0))
blk = np.concatenate([[0], np.cumsum(sign[1:] != sign[:-1])])
ah = I * dt / 3600
thr = np.cumsum(np.abs(ah))
Tm = lic["Tm"].to_numpy(np.float64)
seg = pd.DataFrame({"blk": blk, "sign": sign, "ah": ah, "I": I, "t": t})
g = seg.groupby("blk")
s = pd.DataFrame({"sign": g.sign.first(), "Ah": g.ah.sum(), "I_med": g.I.median(), "i0": g.t.idxmin()})
rpt = s[(s.sign == -1) & s.I_med.between(-35, -20) & (s.Ah < -200)]
ana = pd.read_csv(f"{E}/LIC_aging/LIC_aging_analysed.csv")
# match each analysed capacity point to the detected RPT whose throughput is nearest to cycles x per-cycle Ah
# (one RPT is repeated without cycling in between, so a plain index match shifts by one)
thr_rpt = np.array([thr[int(r["i0"])] for _, r in rpt.iterrows()])
per_cycle = (thr_rpt[1] - thr_rpt[0]) / 50.0
pick = [int(np.argmin(np.abs(thr_rpt - thr_rpt[0] - c * per_cycle))) for c in ana["Total_cycles"]]
for k, j in enumerate(pick):
    r = rpt.iloc[j]
    i0 = int(r["i0"])
    days = (t[i0] - t[0]) / 86400
    Tmean = float(np.sum(Tm[:i0] * dt[:i0]) / max(np.sum(dt[:i0]), 1)) if i0 > 0 else float(Tm[0])
    cap = float(ana["Capacity_Ah"].iloc[k])
    rows.append(dict(dataset="LIC280", point=k, cycles=int(ana["Total_cycles"].iloc[k]), rpt_index=j,
                     days=days, thr_Ah_raw=float(thr[i0]), C_nom=280.0, T_mean_C=Tmean, capacity_Ah=cap))
del lic, seg

# ---------------------------------------------------------------- Gotion 53 Ah cell
cyc = pd.read_csv(f"{E}/_screening/outputs/gotion_cell_cycles.csv")
cyc["fdate"] = pd.to_datetime(cyc["file"].str.extract(r"_(\d{4}-\d{2}-\d{2}_\d{2}\.\d{2}\.\d{2})")[0],
                              format="%Y-%m-%d_%H.%M.%S")
# cycle time: spread each file's cycles evenly between its own date and the next file's date
files = cyc.drop_duplicates("file")[["file", "fdate"]].sort_values("fdate").reset_index(drop=True)
nxt = dict(zip(files["file"], list(files["fdate"].iloc[1:]) + [files["fdate"].iloc[-1] + pd.Timedelta(days=3)]))
times = []
for f, gq in cyc.groupby("file", sort=False):
    a, b = gq["fdate"].iloc[0], nxt[f]
    n = len(gq)
    times += [a + (b - a) * (i / n) for i in range(n)]
cyc["time"] = times
cyc = cyc.sort_values("n").reset_index(drop=True)
cyc["thr"] = (cyc["qc"] + cyc["qd"]).cumsum()
cal = pd.read_excel(f"{E}/Battery_expansion_force_data/Cell_Data/Capacity_Calibration_Cell_data.xlsx")
cal.columns = ["cyc", "cap", "soh"]
t0 = cyc["time"].iloc[0]
for _, k in cal.iterrows():
    w = cyc[cyc["n"] <= max(int(k.cyc), 1)]
    last = w.iloc[-1] if len(w) else cyc.iloc[0]
    rows.append(dict(dataset="Gotion53_cell", point=int(k.cyc) // 50, cycles=int(k.cyc),
                     days=float((last["time"] - t0).total_seconds() / 86400) if k.cyc > 0 else 0.0,
                     thr_Ah_raw=float(last["thr"]) if k.cyc > 0 else 0.0, C_nom=56.2,
                     T_mean_C=float(w["T"].mean()) if len(w) else float(cyc["T"].iloc[0]), capacity_Ah=float(k.cap)))

out = pd.DataFrame(rows)
out["thr_Ah_102"] = out["thr_Ah_raw"] * 102.0 / out["C_nom"]
out["rel_loss"] = out.groupby("dataset")["capacity_Ah"].transform(lambda c: 1 - c / c.iloc[0])
out["loss_Ah_102"] = out["rel_loss"] * 102.0
out.to_csv(OUT, index=False)
print(out.round(3).to_string())
