"""Evidence gate for OCV, identity, resolution, and independent capacity labels."""
from __future__ import annotations
import re
import numpy as np
import pandas as pd
from common import ROOT,OUT,CELLS,CFG,digest,json_dump
from audit_events import load

def audit_calibration():
    source=ROOT/'dataset original'
    files=sorted(source.rglob('*.csv'))
    records=[]
    for p in files:
        sample=pd.read_csv(p,nrows=5000)
        types=sample.step_type.value_counts().to_dict() if 'step_type' in sample else {}
        rests=sample[sample.step_type.eq('rest')] if 'step_type' in sample else pd.DataFrame()
        records.append(dict(file=str(p.relative_to(ROOT)),entity=p.parent.name,rows_sampled=len(sample),step_types='|'.join(sorted(types)),
            has_explicit_SOC_column=any(str(c).lower() in ['soc','soc_pct','soc_true'] for c in sample.columns),
            has_explicit_OCV_column=any('ocv' in str(c).lower() for c in sample.columns),rest_rows=len(rests),
            source_sha256=digest(p)))
    pd.DataFrame(records).to_csv(OUT/'source_calibration_inventory.csv',index=False)
    source_project=ROOT.parents[0]/'项目/Current State_Challenge1'
    explicit_candidates=[str(p) for parent in [source,source_project] if parent.exists() for p in parent.rglob('*') if p.is_file() and re.search(r'(^|[_\-])(ocv|hppc|gitt)([_\-.]|$)',p.name,re.I)]
    ref=pd.read_csv(ROOT/'data/checkups/CK0_reference_discharge.csv.gz',parse_dates=['timestamp'])
    events=load();row=pd.read_csv(OUT/'event_ledger.csv')
    resolution={c:float(np.quantile(np.diff(np.sort(np.unique(ref[c]))),.1)) for c in CELLS}
    eligibility=pd.read_csv(ROOT/'research/phase2_capacity_validation/outputs/data_eligibility.csv')
    summary=dict(
        path='L',OCV_gate='UNVERIFIED',reason='No qualified independent target-cell OCV/SOC versus charge coordinate and direction/temperature calibration. Loaded CK0 and endpoint rests are not OCV.',
        source_project=str(source_project),source_project_exists=source_project.exists(),source_csv_files=len(files),source_entities=len({r['entity'] for r in records}),
        source_inventory_scan='all filenames and SHA256; first 5000 rows per file inspected, not exhaustive OCV protocol reconstruction',
        explicit_calibration_filename_candidates=explicit_candidates,nominal_chemistry_similarity='102Ah LFP',same_manufacturer_model_batch='unproven',
        initial_SOCs='unavailable',temperature_channels='mean/min/max shared across four cells',
        CK0_record_start=ref.timestamp.min().isoformat(),CK0_record_end=ref.timestamp.max().isoformat(),CK0_nominal_date='2025-01-14',CK0_reference_authorization='released reference separately allowed by framework even though timestamp later than nominal CK0',
        CK0_columns=list(ref.columns),voltage_reporting_resolution_V=resolution,
        sample_period_s=10,Nyquist_Hz=.05,Yi_0p5Hz_recoverable=False,Yi_0p01Hz='within bandwidth; no demonstrated dedicated injection',
        group_sum_residual_mV=dict(median=float(row.pack_sum_median_mV.median()),minimum=float(row.pack_sum_median_mV.min()),maximum=float(row.pack_sum_median_mV.max())),
        independent_same_protocol_4S_capacity_gate='UNVERIFIED',eligibility_registry=str(ROOT/'research/phase2_capacity_validation/outputs/data_eligibility.csv'),
        registered_sources=eligibility.source_id.tolist(),capacity_truth_available=['CK0'],
        release_temperatures='CK0 reference temperature not independently certified in supplied metadata',
        usable_charging_information='CCCV operational anchors, signed coulomb ledger, historical current propagation; charging voltage is not treated as discharge-template observation')
    json_dump(OUT/'calibration_gate.json',summary)
    print({k:summary[k] for k in ['path','OCV_gate','source_csv_files','source_entities','independent_same_protocol_4S_capacity_gate']},flush=True)
    return summary

if __name__=='__main__':audit_calibration()
