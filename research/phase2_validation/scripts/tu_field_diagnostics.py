"""Bounded-memory early/mid/late field windows for systems 25, 1 and 8."""
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3]
TASK=ROOT/'research/phase2_validation'
COLS=['Timestamp','U_Battery','I_Battery','SOC_Battery']+[f'U_Cell_{i}' for i in range(1,9)]+[f'I_CNV_Cell_{i}' for i in range(1,9)]+[f'Temperature_{i}' for i in range(1,5)]

def windows(path,nrows,width=100000):
    centers=[width//2,nrows//2,nrows-width//2]
    intervals=[(max(0,c-width//2),min(nrows,c+width//2)) for c in centers]
    collected=[[] for _ in intervals]
    offset=0
    for chunk in pd.read_csv(path,usecols=COLS,chunksize=200000):
        stop=offset+len(chunk)
        for k,(a,b) in enumerate(intervals):
            lo=max(a,offset);hi=min(b,stop)
            if lo<hi:collected[k].append(chunk.iloc[lo-offset:hi-offset].copy())
        offset=stop
    assert offset==nrows
    return [(a,b,pd.concat(parts,ignore_index=True)) for (a,b),parts in zip(intervals,collected)]

def main():
    inventory=pd.read_csv(TASK/'preflight/downloaded_data/tu_files.csv')
    result=[]
    for sysid in (25,1,8):
        path=ROOT/'TU Darmstadt'/f'data_sys_{sysid}.csv'
        row=inventory.loc[inventory.path.eq(str(path.relative_to(ROOT)))].iloc[0]
        for stage,(a,b,d) in zip(('early','middle','late'),windows(path,int(row.rows))):
            t=pd.to_datetime(d.Timestamp,errors='coerce')
            dt=t.diff().dt.total_seconds()
            v=d[[f'U_Cell_{i}' for i in range(1,9)]].to_numpy(float)
            balance=d[[f'I_CNV_Cell_{i}' for i in range(1,9)]].to_numpy(float)
            temp=d[[f'Temperature_{i}' for i in range(1,5)]].to_numpy(float)
            residual=d.U_Battery.to_numpy(float)-np.nansum(v,axis=1)
            spread=np.nanmax(v,axis=1)-np.nanmin(v,axis=1)
            i=d.I_Battery.to_numpy(float)
            result.append({'system':sysid,'stage':stage,'source_file':str(path.relative_to(ROOT)),
                'row_start':a,'row_end_exclusive':b,'rows':len(d),'time_first':str(t.iloc[0]),
                'time_last':str(t.iloc[-1]),'dt_median_s':np.nanmedian(dt),
                'dt_p95_s':np.nanpercentile(dt,95),'gaps_gt_60s':int((dt>60).sum()),
                'backward_time_steps':int((dt<0).sum()),
                'current_p05_A':np.nanpercentile(i,5),'current_p95_A':np.nanpercentile(i,95),
                'pack_minus_cell_sum_median_V':np.nanmedian(residual),
                'pack_minus_cell_sum_p95_abs_V':np.nanpercentile(abs(residual),95),
                'cell_spread_median_V':np.nanmedian(spread),'cell_spread_p95_V':np.nanpercentile(spread,95),
                'balancing_nonzero_fraction':np.mean(np.any(abs(balance)>0.01,axis=1)),
                'balancing_current_p95_abs_A':np.nanpercentile(abs(balance),95),
                'temperature_median_C':np.nanmedian(temp),
                'SOC_BMS_p05':np.nanpercentile(d.SOC_Battery,5),
                'SOC_BMS_p95':np.nanpercentile(d.SOC_Battery,95),
                'capacity_label_available':False})
        print('TU system',sysid,'processed',flush=True)
    out=TASK/'outputs/tu_field_diagnostics.csv'
    pd.DataFrame(result).to_csv(out,index=False)
    print(out)
    print(pd.DataFrame(result)[['system','stage','rows','gaps_gt_60s','pack_minus_cell_sum_p95_abs_V','balancing_nonzero_fraction']].to_string(index=False))

if __name__=='__main__':main()
