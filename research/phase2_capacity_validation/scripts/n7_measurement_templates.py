import csv,json
from pathlib import Path
T=Path(__file__).resolve().parents[1];O=T/'outputs'
rows=[
 dict(plan='resource_limited_case',physical_packs=1,life_stages_per_pack=2,RPT_repeats_per_stage=2,
  nominal_discharges=4,nominal_discharge_hours_at_102Ah=80,
  scope='pipeline_and_within_pack_case_only',independent_group_generalization='not_testable',
  design='one 4S pack; two stages; paired 0A/20A start conditions; order logged',
  additional_time='full_charges+rest+conditioning+repeats+equipment_queue_extra_unknown',
  assumptions='102Ah/5p1A=20h scenario per discharge; aged pack may be shorter'),
 dict(plan='exploratory_pilot',physical_packs=4,life_stages_per_pack=2,RPT_repeats_per_stage=2,
  nominal_discharges=16,nominal_discharge_hours_at_102Ah=320,
  scope='estimate_between_pack_variance_and_measurement_repeatability',independent_group_generalization='exploratory_only',
  design='randomize physical pack split 2 development 2 held; same-state paired windows per stage',
  additional_time='full_charges+rest+conditioning+repeats+equipment_queue_extra_unknown',
  assumptions='not a sample-size guarantee; lock confirmation size after pilot variance'),
 dict(plan='formal_confirmation_scenario',physical_packs=12,life_stages_per_pack=3,RPT_repeats_per_stage=2,
  nominal_discharges=72,nominal_discharge_hours_at_102Ah=1440,
  scope='prospective_independent_entity_validation_if_power_review_accepts',independent_group_generalization='requires_variance_based_power_and_group_split',
  design='prospective group-level 6 development 6 sealed; stage/temperature balance; no test retuning',
  additional_time='full_charges+rest+conditioning+repeats+equipment_queue_extra_unknown',
  assumptions='scenario not recommended minimum; recalculate from pilot variance and device channels')]
with (O/'measurement_plan.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
fields=['record_type','source_id','source_file_sha256','physical_pack_id','cell_id','series_count','nominal_capacity_Ah',
 'life_stage_id','cycle_count','calendar_age_days','split','prior_exposure','operation_or_RPT','target_id',
 'procedure_step','full_charge_confirmed','full_charge_protocol_id','CV_cutoff_A','rest_before_discharge_s',
 'chamber_set_C','observed_pack_temp_C','temp_sensor_id','temp_calibration_id','current_calibration_id',
 'voltage_calibration_id','channel_count','timestamp_ISO8601_timezone','clock_sync_reference',
 'sample_period_s','current_A_charge_positive','pack_voltage_V','cell1_V','cell2_V','cell3_V','cell4_V',
 'charge_Ah_cum','discharge_Ah_cum','cycler_state_code','program_step_id','start_condition_code',
 'cutoff_pack_V','data_quality_flag','operator_note']
with (O/'acquisition_template.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
 w.writerow({'record_type':'TEMPLATE_NOT_DATA','series_count':4,'nominal_capacity_Ah':102,
  'operation_or_RPT':'RPT_or_operation_required','full_charge_confirmed':'unknown_requires_operator',
  'timestamp_ISO8601_timezone':'YYYY-MM-DDTHH:MM:SS+HH:MM','current_A_charge_positive':'A',
  'pack_voltage_V':'V','cutoff_pack_V':11.2,'data_quality_flag':'not_a_measurement'})
run=T/'runs/N7_measurement_plan_20260930_v1';run.mkdir(exist_ok=True)
(run/'result.json').write_text(json.dumps({'scenarios':len(rows),'template_fields':len(fields),
 'nominal_discharge_hours_each':20,'hardware_operation':False},indent=2));(run/'COMPLETED').write_text('complete\n')
