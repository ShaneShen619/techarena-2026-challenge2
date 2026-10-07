"""Qualify local and external datasets without promoting labels across protocols."""
import csv
from pathlib import Path

TASK=Path(__file__).resolve().parents[1]
src=TASK/'notes/workstreams/C_dataset_registry.csv'
rows=list(csv.DictReader(src.open(encoding='utf-8')))
for r in rows:
    r['independence_unit'] = 'physical_pack' if 'system' in r['physical_entities'] or 'module' in r['topology'] else 'physical_cell'
    r['qualification_note'] = 'See notes/workstreams/C_DATA_QUALIFICATION.md; protocol and label definitions do not establish official 4S C/20 capacity performance.'
    r['source_check'] = 'README_and_representative_fields_or_metadata_as_local_status'
    if r['dataset_id']=='P1_local':
        r['dataset_id']='P1_stage1_target_6cells'
        r['allowed_role']='D0_historical_development;shared_with_D1_six_proxy'
        r['qualification_note']='Challenge 1 target six 102Ah single cells. Its label and repeated usage cannot be independent confirmation for Challenge 2 pack; six D1 proxy conditions reuse the same physical panel.'
    if r['dataset_id']=='Yagci_180Ah_v1_1':
        r['qualification_note']='Zenodo v1.1 later release linked to 2025 paper; paper Table 2/RPT 20C protocol reviewed, 2.5GB raw archive not downloaded; single 180Ah cells and differing reference remain conditional transfer only.'
    if r['dataset_id']=='TU_BattGP_v1':
        r['qualification_note']='Formal paper 28 systems/224 cells; Zenodo README 28/232 internally inconsistent. No periodic reference capacity. Use as resistance/fault mechanism only.'
rows.append(dict.fromkeys(rows[0].keys(),''))
rows[-1].update(dataset_id='Bilfinger2024_vehicle_cases',source_doi='10.1016/j.etran.2024.100356',local_status='paper_and_code_data_pointers_only',chemistry='1_LFP_Tesla_1_NMC_VW',physical_entities='2_vehicles',topology='106S1P_LFP_and_108S2P_NMC',target_definition='near_full_low_power_charge_energy_over_nominal_net_energy',representative_fields='vehicle_pack_cell_voltage|current|SOC|charging_energy',protocol_gap='energy_not_Ah_near_full_AC_charge_vs_4S_C20_discharge',prior_use='new_forward_citation',allowed_role='mechanism_and_BMS_cutoff_negative_control_only',license_status='paper_CC_BY_NC_ND_4_0_data_code_license_check_pending',independence_unit='physical_vehicle',qualification_note='Single LFP Tesla case; strong evidence of feature transfer and BMS cutoff confounding, no independent official capacity labels.',source_check='Bilfinger2024 full PDF p7/10/11; mediatum and GitHub pointers')
rows.append(dict.fromkeys(rows[0].keys(),''))
rows[-1].update(dataset_id='Deng2024_10vehicle_MAT',source_doi='10.1016/j.jechem.2023.10.056',local_status='author_MAT_downloaded_structural_audit',chemistry='NCM_ternary',physical_entities='10_vehicles_10_capacity_labels',topology='84_to_108_series_cells',target_definition='one_full_charge_Ah_per_vehicle_over_rated_Ah',representative_fields='I_load|Q|Vmax|Vmean|Cn|SOH|SOC_OCV',protocol_gap='NCM_full_charge_target_not_LFP_4S_C20_discharge; vehicle_5_Cn_conflict',prior_use='new_forward_citation',allowed_role='external_method_stress_test_not_D2',license_status='author_GitHub_academic_noncommercial_terms_check_before_reuse',independence_unit='physical_vehicle',qualification_note='Vehicle 5 paper/README 174Ah 82.21% vs MAT 147Ah 97.30765%; same Q~143.04225Ah. README fields overstate actual MAT. Preserve both protocols and exclude/sensitivity-test vehicle 5.',source_check='F_Deng2024_RapidPackDA card; AUDIT_DENG_MAT.json; original MAT SHA')
rows.append(dict.fromkeys(rows[0].keys(),''))
rows[-1].update(dataset_id='D1_six_cell_shallow_proxy',source_doi='derived_from_P1_stage1_target_6cells',local_status='existing_repeated_development_panel',chemistry='LFP',physical_entities='same_6_P1_cells',topology='single_cell',target_definition='source_specific_capacity_proxy',representative_fields='see phase2_next_round R1 predictions and P1 raw files',protocol_gap='0.5C_or_1C_single_cell_to_2.5V_vs_C20_4S_to_11.2V',prior_use='repeated_method_selection',allowed_role='D1_development_and_refutation_only',license_status='challenge_provided',independence_unit='physical_cell',qualification_note='Same entities as Stage1 P1; do not double count as independent external confirmation.',source_check='phase2_next_round outputs/acceptance_results.json')
rows.append(dict.fromkeys(rows[0].keys(),''))
rows[-1].update(dataset_id='D3_official_challenge2_pack',source_doi='CHALLENGE2_DESCRIPTION.pdf',local_status='local_operation_CK0_only',chemistry='LFP',physical_entities='1_pack_4_cells',topology='4S_group_voltage_cutoff',target_definition='CK0_5.1A_discharge_to_pack_11.2V_100.41Ah_over_102Ah',representative_fields='timestamp|current_A|cell1_V..cell4_V|pack_voltage_V|temp_mean_min_max_C|chamber_temperature_C|charge_discharge_Ah_cum',protocol_gap='CK1_CK7_capacity_hidden',prior_use='official_anchor_and_unlabeled_prefix',allowed_role='D3_causal_feature_and_interface_checks_only',license_status='challenge_provided',independence_unit='physical_pack',qualification_note='Only CK0 released; no hidden monthly capacity error/coverage can be measured locally.',source_check='official PDF; framework/data.py; CK0 CSV')
out=TASK/'outputs/dataset_registry.csv'
with out.open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print(len(rows),'datasets')
