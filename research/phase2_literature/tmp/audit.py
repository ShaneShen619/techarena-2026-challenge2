from pathlib import Path
import pandas as pd
import numpy as np

root = Path(__file__).resolve().parents[3]
files = sorted((root / 'data/operation').glob('*.csv.gz'))
out = []
for p in files:
    d = pd.read_csv(p, parse_dates=['timestamp'])
    ts = d.timestamp
    dt = ts.diff().dt.total_seconds()
    i = d.current_A.to_numpy()
    v = d.pack_voltage_V.to_numpy()
    # Only contiguous near-constant-current charging windows suitable for a first event audit.
    cc = (i > 0.5) & (i < 40) & (v > 12.6) & (v < 13.95)
    changes = np.r_[True, (np.diff(cc.astype(int)) != 0) | (dt.to_numpy()[1:] > 60)]
    ids = np.cumsum(changes)
    groups = pd.DataFrame({'id': ids[cc], 'v': v[cc]}).groupby('id').agg(n=('v','size'), vmin=('v','min'), vmax=('v','max')) if cc.any() else pd.DataFrame()
    useful = groups[(groups.n >= 60) & ((groups.vmax-groups.vmin) >= 0.2)] if len(groups) else groups
    out.append(dict(file=p.name,rows=len(d),first=str(ts.min()),last=str(ts.max()),duplicate_ts=int(ts.duplicated().sum()),gaps_gt_60s=int((dt>60).sum()),median_dt_s=float(dt[(dt>0)&(dt<60)].median()),temp_mean_min=float(d.temp_mean_C.min()),temp_mean_max=float(d.temp_mean_C.max()),cc_candidate_windows=int(len(useful)),cc_candidate_vspan_median=float((useful.vmax-useful.vmin).median()) if len(useful) else None))
pd.DataFrame(out).to_csv(Path(__file__).with_name('audit.csv'),index=False)
print(pd.DataFrame(out).to_string(index=False))
