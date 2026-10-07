"""Version 2 source registry after checking published primary data descriptions."""
import csv,hashlib,json
from pathlib import Path
T=Path(__file__).resolve().parents[1]
O=T/'outputs'
def rw(path,rows):
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
d=list(csv.DictReader((O/'data_eligibility.csv').open()))
gaps={'official_CK1_CK7':'true_reference_capacity_hidden_for_same_pack',
 'Ji_second_life_23':'single_cell_not_4S; prior_three_RPT_raw_curves_absent; license_unknown',
 'TU_BattGP':'8S_field_no_paired_capacity_RPT',
 'UConn_108':'single_1p2Ah_not_4S; large_raw_not_downloaded',
 'Che_Dataset3':'single_cell_charge_normalized_label_not_official_RPT',
 'new_independent_4S_D2':'no_independent_physical_4S_pack_with_same_protocol_paired_RPT'}
for r in d:
 if r['source_id'] in gaps:r['qualification_gap']=gaps[r['source_id']]
rw(O/'data_eligibility.csv',d)
s=list(csv.DictReader((O/'source_registry.csv').open()))
for id,url,unit in [
 ('He_ESSL1','https://zenodo.org/records/20132842','one_16S_pack_and_six_cells'),
 ('Xu_1P10S','https://data.mendeley.com/datasets/4nww8p6vxf/1','one_10S_module_and_one_cell'),
 ('UConn_108','https://digitalcommons.lib.uconn.edu/reil_datasets/3/','108_single_cells'),
 ('DOE_ROVI','https://www.energy.gov/oe/rapid-operational-validation-initiative-rovi','reference_only_not_data')]:
 s.append(dict(source_id=id,source_url_or_path=url,local_path='',bytes='',sha256='',
               access_status='published_page_reviewed_not_raw_downloaded',prior_use='metadata_only',entity_unit=unit))
rw(O/'source_registry.csv',s)
z=T/'downloads/SLBs_LFP_charging_data.zip'
rw(O/'download_log.csv',[dict(source_id='Ji_second_life_23',url='https://zenodo.org/records/18630889',
 action='downloaded_public_zip',http_status='success',bytes=z.stat().st_size,
 published_md5='ffacb176a7be606067b5d0c805fe8892',observed_md5=hashlib.md5(z.read_bytes()).hexdigest(),
 sha256=hashlib.sha256(z.read_bytes()).hexdigest(),member_count=23,
 license='unknown_blank_on_published_page',status='verified_archive_local_research_only'),
 dict(source_id='UConn_108',url='https://digitalcommons.lib.uconn.edu/reil_datasets/3/',
 action='metadata_only',http_status='not_requested',bytes='',published_md5='',observed_md5='',sha256='',
 member_count='',license='CC_BY_4_0_page',status='not_downloaded_large_single_cell_non_D2')])
rw(O/'label_provenance.csv',[
 dict(source_id='official',entity_id='one_4S_pack',target_name='CK0_C20_capacity_Ah',target_source='official_released_CSV_and_full_RPT',
 derivation='5p1A_discharge_first_11p2V',raw_reference_available='true',protocol_match='true',
 exposure_status='public_anchor',uncertainty='meter_uncertainty_not_provided; CSV_100p41Ah_curve_last_100p412Ah',version='2026-09-30-v2'),
 dict(source_id='official',entity_id='same_4S_pack',target_name='CK1_CK7_C20_capacity_Ah',target_source='official_hidden',
 derivation='unknown_truth',raw_reference_available='false',protocol_match='true',exposure_status='hidden',
 uncertainty='unavailable',version='2026-09-30-v2'),
 dict(source_id='Ji_second_life_23',entity_id='23_separate_single_cells',target_name='prior_mean_capacity_Ah',
 target_source='author_Zenodo_description_and_member_filenames',derivation='reported_mean_of_three_prior_capacity_tests_not_raw_reintegrated',
 raw_reference_available='false',protocol_match='false',exposure_status='researcher_nonblind_due_source_filenames; program_split_15_8',
 uncertainty='individual_three_repeats_unavailable; nominal_SOH_denominator_unverified',version='2026-09-30-v2')])
run=T/'runs/N1_registry_20260930_v2';run.mkdir(exist_ok=True)
(run/'result.json').write_text(json.dumps({'n_sources':len(d),'n_qualified_D2':0,'Ji_zip_verified':True,'source_registry_rows':len(s)},indent=2))
(run/'COMPLETED').write_text('complete\n')
