"""Post-score audit metadata correction; never changes frozen candidates or predictions."""
import csv,hashlib,json,zipfile
from pathlib import Path
T=Path(__file__).resolve().parents[1];O=T/'outputs'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=json.loads((O/'pipeline_result.json').read_text())
assert old['official_hidden_targets']==35
new={k:v for k,v in old.items() if k!='official_hidden_targets'}
new['official_hidden_unique_checkups']=7
new['official_hidden_prediction_rows']=35
new['correction']='v1 key official_hidden_targets counted prediction rows, not unique CK targets; v1 retained for audit'
(O/'pipeline_result_v2.json').write_text(json.dumps(new,indent=2,ensure_ascii=False))
mapping=list(csv.DictReader((T/'sealed/ji_23_private_label_map.csv').open()))
split={x['entity_id']:x for x in csv.DictReader((O/'split_manifest.csv').open())}
with zipfile.ZipFile(T/'downloads/SLBs_LFP_charging_data.zip') as z:
 assert len(mapping)==23 and len(split)==23
 for r in mapping:
  public=split[r['entity_id']]
  assert r['split']==public['split']
  b=z.read(r['source_member'])
  assert hashlib.sha256(b).hexdigest()==public['source_member_sha256']
  assert b==(T/public['staging_path']).read_bytes()
  assert float(r['source_member'].split('Ah')[0])==float(r['capacity_Ah_author_mean_3'])
post=dict(status='postscore_provenance_verified_not_original_freeze',
 source_zip_sha256=sha(T/'downloads/SLBs_LFP_charging_data.zip'),
 sealed_mapping_sha256=sha(T/'sealed/ji_23_private_label_map.csv'),
 member_stage_label_triplets_verified=23,
 original_freeze_missing_label_map_hash=True,
 original_freeze_sha256=sha(T/'configs/freeze_manifest.json'),
 one_shot_flag_sha256=sha(T/'sealed/HOLDOUT_SCORED_ONCE'))
(T/'sealed/provenance_postscore.json').write_text(json.dumps(post,indent=2))
run=T/'runs/N8_audit_response_20260930_v1';run.mkdir(exist_ok=True)
(run/'result.json').write_text(json.dumps({'corrected_hidden_unique_ck':7,'source_map_verified':23,
 'postscore_provenance_sha256':sha(T/'sealed/provenance_postscore.json')},indent=2))
(run/'COMPLETED').write_text('complete\n')
print((run/'result.json').read_text())
