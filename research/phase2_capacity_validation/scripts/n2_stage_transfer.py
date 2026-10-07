"""Freeze source-specific group split before parsing charging curves or scoring labels."""
import csv
import hashlib
import json
import random
import re
import zipfile
from pathlib import Path

TASK=Path(__file__).resolve().parents[1]
ZIP=TASK/'downloads/SLBs_LFP_charging_data.zip'
OUT=TASK/'staging/ji_23_charges';OUT.mkdir(exist_ok=True)
SEALED=TASK/'sealed/ji_23_private_label_map.csv'
SPLIT=TASK/'outputs/split_manifest.csv'
with zipfile.ZipFile(ZIP) as z:
    names=[i.filename for i in z.infolist()]
    assert len(names)==23 and all(n.endswith('.xlsx') and re.match(r'^\d+(?:\.\d+)?Ah_charge\.xlsx$',n) for n in names)
    indices=list(range(len(names)))
    random.Random(20260930).shuffle(indices)
    holdout=set(indices[:8])
    public=[];secret=[]
    for i,n in enumerate(names):
        entity=f'J{i+1:02d}'
        data=z.read(n)
        dest=OUT/f'{entity}.xlsx';dest.write_bytes(data)
        split='sealed_holdout' if i in holdout else 'development'
        public.append(dict(source_id='Ji_second_life_23',entity_id=entity,physical_unit='one_single_cell',split=split,
                           staging_path=str(dest.relative_to(TASK)),source_member_sha256=hashlib.sha256(data).hexdigest(),
                           protocol='single_cell_1C_25C_one_charge',target_status='label_from_source_filename_not_visible_in_staged_path',
                           prior_exposure='researcher_saw_source_filenames_labels_nonblind'))
        secret.append(dict(source_id='Ji_second_life_23',entity_id=entity,source_member=n,capacity_Ah_author_mean_3=float(n.split('Ah')[0]),split=split,
                           target_provenance='Zenodo_author_description_mean_of_three_RPTs_in_filename_not_raw_reintegrated'))
with SPLIT.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=public[0].keys());w.writeheader();w.writerows(public)
with SEALED.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=secret[0].keys());w.writeheader();w.writerows(secret)
config={
 'version':'2026-09-30-transfer-initial-freeze-v1','source':'Ji_second_life_23','source_zip_sha256':hashlib.sha256(ZIP.read_bytes()).hexdigest(),
 'split_unit':'source workbook equals one physical single cell per author description','split_seed':20260930,'n_dev':15,'n_holdout':8,
 'holdout_score_limit':'one after final freeze; individual source filename labels were previously seen so researcher is nonblind',
 'target':'reported mean of three prior capacity tests in Ah; not official four-series SOH',
 'candidate_families':['T0_dev_median_capacity','T1_charge_integral_window_linear','T2_voltage_shape_linear'],
 'feature_inputs':['elapsed_time_s','current_A','voltage_V','temperature_C_if_valid'],
 'forbidden_inputs':['source_filename','label_capacity','SOC_field_if_derived_from_capacity','cumulative_capacity_field','same_test_reference_discharge'],
 'model_training':'development only; leave-one-cell-out for candidate/regularization selection; final holdout eight cells once',
 'uncertainties':['license field blank at Zenodo; local research only','no raw triple RPT curves in this ZIP','no longitudinal late-life points','nominal SOH denominator unverified']}
p=TASK/'configs/transfer_initial_v1.json';p.write_text(json.dumps(config,ensure_ascii=False,indent=2))
run=TASK/'runs/N2_transfer_split_20260930_v1';run.mkdir(exist_ok=True)
(run/'result.json').write_text(json.dumps({'n_dev':15,'n_holdout':8,'split_sha256':hashlib.sha256(SPLIT.read_bytes()).hexdigest(),
                                            'config_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                                            'label_file':str(SEALED.relative_to(TASK)),
                                            'exposure_status':'program_separated_researcher_nonblind_due_filename'},indent=2))
(run/'COMPLETED').write_text('complete\n')
print((run/'result.json').read_text())
