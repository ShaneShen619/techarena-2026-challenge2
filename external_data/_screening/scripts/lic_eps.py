"""LIC 280 Ah: offset between 0.1C RPT capacity and the first 1C CCCV charge from empty after each RPT,
plus the post-RPT 1C discharge rebound. Input: lic_segments.csv from lic_segments.py."""
import sys, pandas as pd, numpy as np
seg, out = sys.argv[1], sys.argv[2]
s = pd.read_csv(seg); s = s[s.sign != 0].reset_index(drop=True)
rpt = s.index[(s.sign == -1) & s.I_med.between(-35, -20) & (s.Ah < -200)].tolist()
rows = []
for k, idx in enumerate(rpt):
    r = s.loc[idx]
    truncated = abs(-r.Ah - 280.0) < 0.01                      # 10 h time limit at 28 A, not an empty-end
    after = s[(s.index > idx) & (s.sign == 1) & (s.I_med > 200) & (s.Ah > 250)].head(1)
    q1 = after.Ah.iloc[0] if len(after) and after.index[0] < (rpt[k + 1] if k + 1 < len(rpt) else 1e12) else np.nan
    rows.append(dict(k=k, Q_rpt=-r.Ah, Q_1C_first_after=q1, truncated=truncated))
R = pd.DataFrame(rows); R["eps"] = R.Q_rpt - R.Q_1C_first_after
R.to_csv(out, index=False)
ok = R[~R.truncated & R.eps.notna()]
loss = ok.Q_rpt.iloc[0] - ok.Q_rpt
print(R.round(3).to_string())
print(f"eps {ok.eps.iloc[0]:+.3f} -> {ok.eps.iloc[-1]:+.3f} Ah over {loss.iloc[-1]:.2f} Ah loss; slope d eps/d loss = {np.polyfit(loss, ok.eps, 1)[0]:+.4f}")
