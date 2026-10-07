"""Scoped local inventory and source-qualification registry; no model labels read."""
import csv
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
TASK=Path(__file__).resolve().parents[1]
OLD=ROOT/'research/phase2_baseline_repair/outputs/data_eligibility.csv'
ZEN=TASK/'downloads/SLBs_LFP_charging_data.zip'
def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def main():
    run=TASK/'runs/N1_registry_20260930_v1';run.mkdir(exist_ok=True)
    root_files=[]
    for base in [ROOT/'data',ROOT/'dataset original',ROOT/'TU Darmstadt',Path('/Users/shane/Downloads/dataset'),Path('/Users/shane/Downloads/field_data')]:
        if base.exists():
            files=[p for p in base.rglob('*') if p.is_file() and not any(x in p.parts for x in ['.venv','node_modules'])]
            root_files.append(dict(path=str(base),file_count=len(files),bytes=sum(p.stat().st_size for p in files)))
    check=[
      ('official_CK0','official_anchor','4S_102Ah', '100.41Ah_CK0_only','one_existing_pack','official_only_anchor','challenge_package'),
      ('official_CK1_CK7','official_hidden','4S_102Ah','hidden_seven','one_existing_pack','not_testable','challenge_package'),
      ('P1_D1_six_cells','old_development_proxy','single_102Ah','source_discharge_proxy','six_reused_cells','not_independent','challenge_package'),
      ('TU_BattGP','unlabeled_mechanism','8S_field','no_paired_RPT','28_systems','no_capacity_scoring','CC_BY_NC_4_0_README'),
      ('Che_Dataset3','cross_protocol_development','single_cell','normalized_charge_label','11_cells','not_4S_D2','prior_CC_BY_4_0'),
      ('He_ESSL1','conditional_transfer','16S_pack_and_cells','SOH_definition_unverified','one_16S_pack','not_4S_D2','Zenodo_license_blank'),
      ('Xu_1P10S','conditional_transfer','10S_module_and_cell','50_cycle_calibration','one_module_one_cell','not_4S_D2','CC_BY_4_0'),
      ('Yagci_180Ah','conditional_transfer','single_180Ah','RPT_protocol_differs','12_cells','not_4S_D2','README_CC_BY_4_0'),
      ('Ji_second_life_23','cross_protocol_transfer','23_single_cells','author_three_RPT_mean_in_filename','23_cells_one_stage','single_cell_transfer_only','Zenodo_license_blank'),
      ('UConn_108','cross_protocol_not_downloaded','108_single_1p2Ah','periodic_RPT','108_cells','would_require_large_download','CC_BY_4_0'),
      ('new_independent_4S_D2','absent','none_confirmed','none','zero','not_testable','unknown')]
    with (TASK/'outputs/data_eligibility.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['source_id','tier','topology','capacity_label','physical_entities','eligibility','license_or_access','protocol','evidence_level','qualification_gap'])
        for x in check:
            proto='official_4S_5p1A_first_11p2V' if x[0].startswith('official') else 'different_or_unverified'
            gap='none_for_CK0_only' if x[0]=='official_CK0' else ('no_independent_matched_4S_RPT' if x[0]=='new_independent_4S_D2' else 'topology_or_reference_or_prior_use')
            w.writerow([*x,proto,'metadata_plus_local_files',gap])
    with (TASK/'outputs/source_registry.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['source_id','source_url_or_path','local_path','bytes','sha256','access_status','prior_use','entity_unit'])
        files=[('official_operation',ROOT/'data/checkups/evaluation_points.csv','local_challenge'),
               ('P1_source',ROOT/'dataset original/102Ah_25degC_0p5C_cell3/102Ah_25degC_0p5C_cell3_time_series_part01.csv','local_challenge'),
               ('TU_8S',ROOT/'TU Darmstadt/data_sys_1.csv','local_prior'),
               ('Che',ROOT/'Che-Dataset3.mat','local_prior'),
               ('Ji_second_life_23',ZEN,'https://zenodo.org/records/18630889')]
        for id,p,url in files:
            if p.is_file():w.writerow([id,url,str(p),p.stat().st_size,sha(p),'available','prior_reviewed' if id!='Ji_second_life_23' else 'new_this_round','physical_pack' if id in ['official_operation','TU_8S'] else 'physical_cell'])
    if ZEN.is_file():
        with zipfile.ZipFile(ZEN) as z:
            members=z.infolist()
            assert len(members)==23 and all(x.filename.endswith('.xlsx') and not x.filename.startswith('/') and '..' not in Path(x.filename).parts for x in members)
            assert sum(x.file_size for x in members)<8_000_000
            assert hashlib.md5(ZEN.read_bytes()).hexdigest()=='ffacb176a7be606067b5d0c805fe8892'
    (TASK/'outputs/label_provenance.csv').write_text('source_id,entity_id,target_name,target_source,derivation,raw_reference_available,protocol_match,exposure_status,uncertainty,version\nJi_second_life_23,all_23,capacity_Ah,filename_and_author_description,mean_of_three_capacity_tests,false,false,filenames_expose_labels,individual_repeats_unavailable,2026-09-30-v1\n')
    result=dict(python=platform.python_version(),free_GiB=round(shutil.disk_usage(ROOT).free/2**30,2),scoped_directories=root_files,
                zenodo_zip_sha256=sha(ZEN) if ZEN.is_file() else None,zenodo_zip_md5=hashlib.md5(ZEN.read_bytes()).hexdigest() if ZEN.is_file() else None,
                n_qualified_independent_official_4S_D2=0)
    (run/'result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
    (run/'COMPLETED').write_text('complete\n')
    print(json.dumps(result,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
