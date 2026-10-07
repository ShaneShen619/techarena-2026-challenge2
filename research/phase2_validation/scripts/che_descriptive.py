"""Che D3 partial-Q shape vs same-cycle charge capacity; no fabricated t/I/V."""
from pathlib import Path
import h5py
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3]
TASK=ROOT/'research/phase2_validation'

def text(h,ref):
    return ''.join(chr(int(x)) for x in h[ref][()].ravel())

def main():
    rows=[]
    with h5py.File(ROOT/'Che-Dataset3.mat','r') as h:
        g=h['Dataset3']
        for j in range(g['Capacity'].shape[0]):
            cell=text(h,g['cell'][j,0]);profile=text(h,g['Workingprofile'][j,0])
            cap=h[g['Capacity'][j,0]][()].ravel().astype(float)
            cy=h[g['cycles'][j,0]]
            refs=cy['Partial_Q'][()].ravel()
            assert len(refs)==len(cap)
            qend=np.array([float(h[ref][()].ravel()[-1]) for ref in refs])
            for stage,pct in [('early',.1),('middle',.5),('late',.9)]:
                idx=round((len(cap)-1)*pct)
                pred=cap[0]*qend[idx]/qend[0]
                rows.append({'cell_id':cell,'working_profile':profile,'cycles':len(cap),
                    'stage':stage,'cycle_index':idx,'initial_charge_capacity_recorded':cap[0],
                    'charge_capacity_recorded':cap[idx],
                    'initial_partial_Q_end_recorded':qend[0],
                    'partial_Q_end_recorded':qend[idx],
                    'capacity_relative_pct':100*cap[idx]/cap[0],
                    'partial_Q_relative_pct':100*qend[idx]/qend[0],
                    'same_cycle_proxy_relative_error_pp':100*(qend[idx]/qend[0]-cap[idx]/cap[0]),
                    'note':'descriptive same-charge-process; no raw time/current/voltage or explicit local grid'})
    df=pd.DataFrame(rows)
    assert df.cell_id.nunique()==11 and len(df)==33
    out=TASK/'outputs/che_descriptive.csv';df.to_csv(out,index=False)
    print(out)
    print('11-cell same-cycle partial-Q end ratio MAE pp',round(df.same_cycle_proxy_relative_error_pp.abs().mean(),3))
    print(df.groupby('stage').same_cycle_proxy_relative_error_pp.agg(n='size',MAE=lambda x:x.abs().mean()).to_string())

if __name__=='__main__':main()
