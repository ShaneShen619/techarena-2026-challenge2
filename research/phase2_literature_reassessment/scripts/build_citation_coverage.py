"""Bounded, transparent OpenAlex citation sweep; preserve raw responses."""
import csv, json, subprocess, time
from pathlib import Path
from urllib.parse import quote

TASK=Path(__file__).resolve().parents[1]
RAW=TASK/'runs/L1_citation_sweep_20260929';RAW.mkdir(exist_ok=True)
REG=list(csv.DictReader((TASK/'outputs/paper_registry.csv').open(encoding='utf-8')))
CORE=['A_Deng2022','A_Krupp2021','A_Ruiz2018','A_Zhou2025','B_card_Schaeffer2024','B_card_Gasper2025','C_Che2023_Continual','Lin2015_Fisher_identifiability','Yagci2025_large_LFP_aging','Zhu2022','Zhou2026_dynamic_ICA','BatteryGPT2025']
MAP={r['paper_id']:r for r in REG}
def get(url,name):
 p=RAW/name
 if p.exists():return json.loads(p.read_text())
 q=subprocess.run(['curl','-sS','-L','--fail','--connect-timeout','10','--max-time','25',url],capture_output=True,text=True,timeout=30,check=True)
 d=json.loads(q.stdout);p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');time.sleep(.1);return d
ids={};work={}
for pid in CORE:
 doi=MAP[pid]['doi']
 if not doi:continue
 try:d=get('https://api.openalex.org/works/https://doi.org/'+quote(doi,safe=''),f'{pid}_work.json')
 except Exception as e:print('unavailable',pid,e);continue
 ids[pid]=d['id'].rsplit('/',1)[-1];work[pid]=d
rows=[]
for pid,d in work.items():
 ref=set(d.get('referenced_works') or [])
 for other,oid in ids.items():
  if other!=pid and ('https://openalex.org/'+oid) in ref:
   rows.append(dict(citing_paper_id=pid,cited_paper_id=other,direction_from_citing='backward',original_location='OpenAlex referenced_works metadata; confirm in source references',reason_for_followup='core paper pair; metadata citation edge',status='metadata_edge_only'))
 try:fw=get('https://api.openalex.org/works?filter=cites:'+ids[pid]+'&per-page=100&select=id,title,doi,publication_year,type',f'{pid}_forward_first100.json')
 except Exception as e:print('forward unavailable',pid,e);continue
 for x in fw.get('results',[]):
  title=x.get('title') or ''
  if not any(k in title.lower() for k in ['battery','batteries','health','lifepo4','lithium','diagnos','capacity']):continue
  ident=x.get('doi') or x['id']
  followed={'10.1016/j.etran.2024.100356':'fulltext_followed_Bilfinger2024','10.1016/j.jechem.2023.10.056':'fulltext_followed_F_Deng2024_RapidPackDA','10.1016/j.energy.2022.125802':'abstract_only_Jiang2023'}
  status=next((v for k,v in followed.items() if k in ident.lower()),'metadata_candidate_only')
  rows.append(dict(citing_paper_id=ident,cited_paper_id=pid,direction_from_citing='forward',original_location='OpenAlex cites filter first 100 metadata; '+title,reason_for_followup='title-screened forward candidate; '+('see source card' if status.startswith('fulltext') else 'no fulltext inference'),status=status))
manual=list(csv.DictReader((TASK/'notes/workstreams/A_partial_temperature/citation_chains.csv').open(encoding='utf-8')))
for x in manual:
 rows.append(dict(**x,status='source_reference_verified'))
with (TASK/'citation_chains.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=['citing_paper_id','cited_paper_id','direction_from_citing','original_location','reason_for_followup','status']);w.writeheader();w.writerows(rows)
families=list(csv.DictReader((TASK/'outputs/method_comparison.csv').open(encoding='utf-8')))
with (TASK/'coverage_matrix.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=['family_id','family_cn','source_ids','positive_and_limit_present','capacity_target_status','contest_directness','remaining_gap','next_discriminating_check']);w.writeheader()
 for r in families:
  w.writerow(dict(family_id=r['family_id'],family_cn=r['family_cn'],source_ids=r['support_ids']+';'+r['limitations_ids'],positive_and_limit_present='yes_source_level',capacity_target_status=r['target'],contest_directness='no_full_one_CK0_4S_capacity_validation',remaining_gap=r['identifiability_condition'],next_discriminating_check=r['contest_decision']))
print('core resolved',len(ids),'citation rows',len(rows),'families',len(families),'metadata candidates are not fulltext evidence')
