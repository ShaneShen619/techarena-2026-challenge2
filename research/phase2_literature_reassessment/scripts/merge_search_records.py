"""Preserve actual OpenAlex and workstream discovery/screening provenance."""
import csv
import json
from pathlib import Path

TASK=Path(__file__).resolve().parents[1]
WS=TASK/'notes/workstreams'
oa=list(csv.DictReader((TASK/'runs/L1_openalex_20260929/screening_openalex.csv').open(encoding='utf-8')))
registry={r['paper_id']:r for r in csv.DictReader((TASK/'outputs/paper_registry.csv').open(encoding='utf-8'))}
queries=[]
for r in csv.DictReader((TASK/'runs/L1_openalex_20260929/search_queries_openalex.csv').open(encoding='utf-8')):
 queries.append(dict(query_id='OA_'+r['query_id'],date_utc=r['date_utc'],entry=r['entry'],family=r['query_id'],exact_query=r['query'],observed_scope=r['range_read'],selection_or_gap=r['error'] or 'raw metadata records in runs/L1_openalex_20260929',source_log=r['raw_path']))
for src,prefix in [(WS/'A_partial_temperature/search_queries.csv','A'),(WS/'B_search_queries.csv','B'),(WS/'C_search_queries.csv','C')]:
 for r in csv.DictReader(src.open(encoding='utf-8')):
  queries.append(dict(query_id=prefix+'_'+r['query_id'],date_utc=r.get('access_date',r.get('date_utc','')),entry=r.get('entry_type',r.get('entry','')),family=r.get('family',''),exact_query=r.get('actual_query',r.get('query_or_access',r.get('exact_query',''))),observed_scope=r.get('result_scope',r.get('range_seen',r.get('observed_scope',''))),selection_or_gap=r.get('access_status',r.get('selected_or_action',r.get('selection_or_gap',''))) + ' ' + r.get('limitation',''),source_log=str(src.relative_to(TASK))))
for r in csv.DictReader((WS/'D_old_refs/screening.csv').open(encoding='utf-8')):
 queries.append(dict(query_id='D_access_'+r['paper_id'],date_utc='2026-09-29',entry='old-reference source re-verification',family='cross-cutting',exact_query=r['doi_or_stable_id'],observed_scope='publisher/arXiv original plus source manifest',selection_or_gap=r['access_status']+'; '+r['decision'],source_log='notes/workstreams/D_old_refs/screening.csv'))
for r in csv.DictReader((WS/'E_forward_pack/screening.csv').open(encoding='utf-8')):
 queries.append(dict(query_id='E_access_'+r['paper_id'],date_utc='2026-09-29',entry='OpenAlex forward citation plus publisher/author access',family='F02 F06',exact_query=r['doi'],observed_scope='publisher/TUM source access attempts',selection_or_gap=r['access_status']+'; '+r['decision'],source_log='notes/workstreams/E_forward_pack/screening.csv'))
for r in csv.DictReader((WS/'F_forward_limited/search_queries.csv').open(encoding='utf-8')):
 queries.append(dict(query_id=r['query_id'],date_utc=r['date'],entry=r['source'],family='F03 F09',exact_query=r['query'],observed_scope=r['result'],selection_or_gap=r['screening_note'],source_log='notes/workstreams/F_forward_limited/search_queries.csv'))
with (TASK/'search_queries.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=list(queries[0]));w.writeheader();w.writerows(queries)

records=[]
seen={}
for r in oa:
 row=dict(record_id=r['paper_id'],identity=r['doi'] or r['source_url'],title=r['title'],entry='OpenAlex API',stage=r['screening_stage'],decision=r['decision'],fulltext_status=r['fulltext_status'],reason=r['reason'],source_log='runs/L1_openalex_20260929/screening_openalex.csv',card_path='',duplicate_of='',query_ids=r['query_ids'])
 records.append(row)
 if r['doi']:
  seen['doi:'+r['doi'].lower()]=row['record_id']

def add(pid, identity, title, entry, stage, decision, fulltext, reason, source, card, queryids=''):
 key=('doi:'+identity.lower()) if identity.startswith('10.') else (identity.lower() if identity else pid.lower())
 dup=seen.get(key,'')
 if not dup:seen[key]=pid
 records.append(dict(record_id=pid,identity=identity,title=title,entry=entry,stage=stage,decision=decision,fulltext_status=fulltext,reason=reason,source_log=source,card_path=card,duplicate_of=dup,query_ids=queryids))

for r in csv.DictReader((WS/'A_partial_temperature/screening.csv').open(encoding='utf-8')):
 pid=r['paper_id']; pr=registry.get(pid,{})
 add(pid,pr.get('identity',r['doi_or_stable_id']),pr.get('title',''), 'A targeted search','fulltext_appraisal' if r['decision'].startswith('included') else 'screened',r['decision'],r['fulltext_or_limit'],r['relevance'], 'notes/workstreams/A_partial_temperature/screening.csv',pr.get('card_path',''),r['query_ids'])
for r in csv.DictReader((WS/'B_screening.csv').open(encoding='utf-8')):
 pid='B_card_'+r['paper_id'];pr=registry.get(pid,{})
 add(pid,pr.get('identity',r['source_url']),pr.get('title',''), 'B targeted search','fulltext_appraisal' if 'full' in r['fulltext_status'] else 'screened',r['decision'],r['fulltext_status'],r['reason']+'; '+r['physical_entity_and_target'],'notes/workstreams/B_screening.csv',pr.get('card_path',''))
for r in csv.DictReader((WS/'C_screening.csv').open(encoding='utf-8')):
 pid=r['paper_id'];pr=registry.get(pid,{})
 add(pid,pr.get('identity',r['source']),pr.get('title',''), 'C targeted search','fulltext_appraisal' if 'full' in r['fulltext_status'] else 'screened',r['screen_decision'],r['fulltext_status'],r['reason']+'; '+r['shared_data_or_label_risk'],'notes/workstreams/C_screening.csv',pr.get('card_path',''))
for r in csv.DictReader((WS/'D_old_refs/screening.csv').open(encoding='utf-8')):
 pid=r['paper_id'];pr=registry.get(pid,{})
 add(pid,pr.get('identity',r['doi_or_stable_id']),pr.get('title',''), 'D old-reference re-verification','fulltext_appraisal',r['decision'],r['access_status'],r['reason'],'notes/workstreams/D_old_refs/screening.csv',pr.get('card_path',''),'D_access_'+pid)
for r in csv.DictReader((WS/'E_forward_pack/screening.csv').open(encoding='utf-8')):
 pid=r['paper_id'];pr=registry.get(pid,{})
 add(pid,pr.get('identity',r['doi']),pr.get('title',''), 'E forward pack citation','fulltext_appraisal' if 'fulltext' in r['access_status'] else 'screened',r['decision'],r['access_status'],r['reason'],'notes/workstreams/E_forward_pack/screening.csv',pr.get('card_path',''),'E_access_'+pid)
for r in csv.DictReader((WS/'F_forward_limited/screening.csv').open(encoding='utf-8')):
 pid='F_Deng2024_RapidPackDA' if r['paper_id'].startswith('Deng') else r['paper_id'];pr=registry.get(pid,{})
 add(pid,pr.get('identity',r['doi']),pr.get('title',r['title']), 'F forward limited-label citation','fulltext_appraisal' if r['decision']=='deep_evidence_card' else 'screened',r['decision'],r['source_depth'],r['reason'],'notes/workstreams/F_forward_limited/screening.csv',pr.get('card_path',''))
with (TASK/'screening.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
flow={
 'date_utc':'2026-09-29','protocol':'notes/SEARCH_PROTOCOL.md',
 'openalex_queries':12,'openalex_first_page_hits':144,'openalex_deduplicated_metadata_candidates':117,
 'openalex_title_abstract_seek_fulltext':sum(r['decision']=='seek_fulltext' for r in oa),
 'targeted_query_or_access_records':len(queries)-12,
 'targeted_screening_rows_A_B_C_D_E_F':len(records)-len(oa),
 'combined_screening_rows_including_duplicate_sources':len(records),
 'known_registry_card_rows_A_B_C_D_E_F':len(registry),
 'known_unique_fulltext_card_studies_after_version_merge':sum(not r['version_duplicate_of'] for r in registry.values()),
 'fulltext_reassessed_but_no_deep_card':'none counted; Bilfinger2026 and Jiang2023 remain metadata/abstract-only and excluded from fulltext count',
 'limitation':'OpenAlex full-text search ranked broadly and returned many reviews/off-topic titles; targeted publisher/author/Zenodo search supplied core studies. This is a scoped evidence review, not an exhaustive systematic review. Candidate screens from multiple entries may duplicate the same study; duplicate_of records first known identity.'}
(TASK/'search_flow.json').write_text(json.dumps(flow,ensure_ascii=False,indent=2),encoding='utf-8')
print('queries',len(queries),'screen rows',len(records),'card unique',flow['known_unique_fulltext_card_studies_after_version_merge'])
