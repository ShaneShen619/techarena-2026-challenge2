"""All-system metadata plus bounded stratified TU field-data audit."""
from pathlib import Path
import json,subprocess,sys
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3];TASK=Path(__file__).resolve().parents[1]
OUT=TASK/'runs/M6_TU_inventory_v1';OUT.mkdir(parents=True,exist_ok=False)
sys.path.insert(0,str(TASK/'src'))
from tu_sampling import sampled_blocks
cfg=json.loads((TASK/'configs/m6_tu_sampling.json').read_text())
cols=['Timestamp','I_Battery','SOC_Battery',*[f'Temperature_{i}' for i in range(1,5)],
      *[f'I_CNV_Cell_{i}' for i in range(1,9)],*[f'U_Cell_{i}' for i in range(1,9)]]
rows=[];blocks=[]
paths=sorted((ROOT/'TU Darmstadt').glob('data_sys_*.csv'),key=lambda p:int(p.stem.split('_')[-1]))
assert len(paths)==28
for path in paths:
    system=int(path.stem.split('_')[-1]);size=path.stat().st_size
    total_lines=int(subprocess.run(['wc','-l',str(path)],capture_output=True,text=True,check=True).stdout.split()[0])
    with path.open('rb') as f:
        f.readline();first=f.readline().decode('utf-8',errors='replace').split(',')[0]
        f.seek(max(0,size-10000));last=[x for x in f.readlines() if x.strip()][-1].decode('utf-8',errors='replace').split(',')[0]
    samples=[]
    for block_id,offset,frame in sampled_blocks(path,cfg['byte_fraction_block_starts'],cfg['rows_per_block'],usecols=cols):
        t=pd.to_datetime(frame.Timestamp,errors='coerce')
        current=pd.to_numeric(frame.I_Battery,errors='coerce')
        soc=pd.to_numeric(frame.SOC_Battery,errors='coerce')
        temp=frame[[f'Temperature_{i}' for i in range(1,5)]].mean(axis=1)
        bal=frame[[f'I_CNV_Cell_{i}' for i in range(1,9)]].abs().max(axis=1)>.05
        eligible=current.gt(-200)&current.lt(-5)&soc.gt(40)&soc.lt(94)&temp.gt(10)&temp.lt(100)
        dt=t.diff().dt.total_seconds()
        voltage=frame[[f'U_Cell_{i}' for i in range(1,9)]]
        blocks.append({'system':system,'block_id':block_id,'byte_offset':offset,'sample_rows':len(frame),
                       'first_time':t.iloc[0].isoformat() if pd.notna(t.iloc[0]) else None,
                       'last_time':t.iloc[-1].isoformat() if pd.notna(t.iloc[-1]) else None,
                       'eligible_fraction':float(eligible.mean()),'balancing_fraction':float(bal.mean()),
                       'eligible_unbalanced_count':int((eligible&~bal).sum()),
                       'duplicate_time_count':int(dt.eq(0).sum()),'negative_time_count':int(dt.lt(0).sum()),
                       'gap_gt100s_count':int(dt.gt(100).sum()),
                       'median_positive_dt_s':float(dt.loc[dt.gt(0)].median()) if dt.gt(0).any() else None,
                       'discharge_lt5_count':int(current.lt(-5).sum()),
                       'max_abs_current_A':float(current.abs().max())})
        samples.append(pd.DataFrame({'I':current,'SOC':soc,'T':temp,'bal':bal,'eligible':eligible,
                                     'mean_cell_V':voltage.mean(axis=1),
                                     'voltage_spread_V':voltage.max(axis=1)-voltage.min(axis=1)}))
    sample=pd.concat(samples,ignore_index=True)
    elig=sample.loc[sample.eligible]
    rows.append({'system':system,'filename':path.name,'size_bytes':size,'file_data_rows':total_lines-1,
                 'first_timestamp_file':first,'last_timestamp_file':last,
                 'sample_rows':len(sample),'sample_discharge_lt5_fraction':float((sample.I<-5).mean()),
                 'sample_paper_eligible_fraction':float(sample.eligible.mean()),
                 'sample_paper_eligible_unbalanced_count':int((sample.eligible&~sample.bal).sum()),
                 'sample_balancing_fraction':float(sample.bal.mean()),
                 'sample_eligible_balancing_fraction':float(elig.bal.mean()) if len(elig) else None,
                 'sample_I_05_A':float(sample.I.quantile(.05)),
                 'sample_I_50_A':float(sample.I.quantile(.5)),
                 'sample_I_95_A':float(sample.I.quantile(.95)),
                 'sample_SOC_05_pct':float(sample.SOC.quantile(.05)),
                 'sample_SOC_50_pct':float(sample.SOC.quantile(.5)),
                 'sample_SOC_95_pct':float(sample.SOC.quantile(.95)),
                 'sample_T_05_C':float(sample['T'].quantile(.05)),
                 'sample_T_50_C':float(sample['T'].quantile(.5)),
                 'sample_T_95_C':float(sample['T'].quantile(.95)),
                 'sample_voltage_spread_95_V':float(sample.voltage_spread_V.quantile(.95)),
                 'sample_current_lt_minus100_fraction':float((sample.I<-100).mean())})
    print(f'system {system:02d} {total_lines-1} rows sampled {len(sample)} eligible {len(elig)}',flush=True)
pd.DataFrame(rows).to_csv(OUT/'system_inventory.csv',index=False)
pd.DataFrame(blocks).to_csv(OUT/'stratified_blocks.csv',index=False)
summary={'local_systems':len(paths),'total_file_rows':int(sum(x['file_data_rows'] for x in rows)),
         'total_sample_rows':int(sum(x['sample_rows'] for x in rows)),
         'sampled_eligible_unbalanced_rows':int(sum(x['sample_paper_eligible_unbalanced_count'] for x in rows)),
         'systems_with_sampled_eligible_rows':int(sum(x['sample_paper_eligible_unbalanced_count']>0 for x in rows)),
         'sample_design':cfg['sample_scope'],
         'literature':'Schaeffer et al. BattGP arxiv v3 says 29/232/131M; local Zenodo release has 28 systems; no capacity labels; warranty-return bias'}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False),flush=True)
