"""Recompute deliverable, source-integrity and report-number checks."""
from pathlib import Path
import hashlib
import json
import math

import pandas as pd
from docx import Document
from pypdf import PdfReader

root=Path(__file__).resolve().parents[3]
task=Path(__file__).resolve().parents[1]
checks={}

def check(name,ok,detail=''):
    checks[name]={'status':'PASS' if ok else 'FAIL','detail':detail}
    if not ok:
        raise AssertionError(name+': '+detail)

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):
            h.update(block)
    return h.hexdigest()

original=json.loads((task/'preflight/original_sha256.json').read_text())
check('official_original_SHA256',all(sha(root/p)==v for p,v in original.items()),f'{len(original)} original files')
manifest=json.loads((task/'preflight/downloaded_data/audit_report.json').read_text())['quick_manifest']
check('external_data_size_mtime',all((root/x['path']).stat().st_size==x['bytes'] and
      (root/x['path']).stat().st_mtime_ns==x['mtime_ns'] for x in manifest),f'{len(manifest)} Phase1/Che/TU files')
for route in ('route_a','route_b'):
    candidate=task/'candidates'/route
    fixed=['run_model.py','validate_submission.py']+[x for x in original if x.startswith(('framework/','sample_data/'))]
    check(f'{route}_official_framework_unchanged',all(sha(candidate/x)==original[x] for x in fixed),f'{len(fixed)} files')
    log=(task/f'runs/package_check/{route}_validator.log').read_text()
    check(f'{route}_clean_zip_validator','PASSED - output schema satisfied' in log,
          'local clean extraction; not Linux scoring')
    check(f'{route}_eight_official_points',len(pd.read_csv(task/f'runs/{"A_official_v4" if route=="route_a" else "B_official_v3"}/output.csv'))==8)

p1=pd.read_csv(task/'outputs/phase1_crossvalidation_predictions.csv')
check('phase1_six_cells_18_targets',len(p1)==54 and p1.cell_id.nunique()==6 and
      set(p1.method)=={'B0','A','B'} and p1.groupby('cell_id').target_cycle.nunique().eq(3).all())
check('phase1_causal_cutoff',(pd.to_datetime(p1.input_end)<pd.to_datetime(p1.target_discharge_start)).all())
metrics=pd.read_csv(task/'outputs/metrics.csv')
expected={'A':10.57,'B':15.27,'B0':14.86}
report=(task/'outputs/LFP_SOH_双方案设计验证与比较报告.md').read_text()
for method,rounded in expected.items():
    actual=p1[p1.method.eq(method)].error_pp.abs().mean()
    recorded=metrics[(metrics.evidence=='E3-P1')&metrics.method.eq(method)].iloc[0].MAE_micro
    check(f'{method}_real_MAE_csv_and_report',math.isclose(actual,recorded,abs_tol=1e-9)
          and f'{actual:.2f}' in report,f'{actual:.6f} pp')

official=pd.read_csv(task/'outputs/predictions_official.csv')
check('official_40_rows',len(official)==40 and official.groupby('method').checkup.nunique().eq(8).all())
hidden=official[official.checkup.ne('CK0')]
check('official_hidden_truth_blank',hidden.true_capacity_Ah.isna().all() and hidden.true_SOH_pp.isna().all())
funnel=pd.read_csv(task/'outputs/route_b_rejection_funnel.csv')
end=funnel.iloc[-1]
check('B_funnel_conservation',int(end.cumulative_charge_runs)==1016 and
      int(end.cumulative_short_event)==527 and int(end.cumulative_temperature_mismatch)==142 and
      int(end.cumulative_fit_attempt)==347 and int(end.cumulative_accepted)==0 and
      (funnel.new_charge_runs>=0).all())
e2=pd.read_csv(task/'runs/E2_twoRC_hysteresis_20seeds/predictions.csv')
check('E2_20seeds_four_mechanisms',len(e2)==720 and e2.seed.nunique()==20 and
      e2.scenario.nunique()==4 and e2.groupby(['seed','scenario','method']).size().eq(3).all())
stress=pd.read_csv(task/'outputs/stress_results.csv')
check('stress_four_sample_rates',set(['baseline','coarse_10s','coarse_30s','coarse_60s'])<=set(stress.stress)
      and stress.groupby(['stress','method']).seed.nunique().eq(20).all(),f'{len(stress)} rows')
for label,path,min_rows in [('Che','che_descriptive.csv',33),('TU','tu_field_diagnostics.csv',9),
                             ('A_ablations','phase1_a_ablations.csv',108),('E2_ablations','ablation_results.csv',260)]:
    check(label+'_results_exist',len(pd.read_csv(task/'outputs'/path))>=min_rows)

docx=task/'outputs/LFP_SOH_双方案设计验证与比较报告.docx'
doc=Document(docx)
doc_text='\n'.join(x.text for x in doc.paragraphs)
for phrase in ('10.57','15.27','527 个','347 个','30/60 s','CK1–CK7'):
    check('Word_contains_'+phrase,phrase in doc_text)
pdf=task/'runs/report_render_v6/LFP_SOH_双方案设计验证与比较报告.pdf'
pages=len(PdfReader(pdf).pages)
pngs=list((task/'runs/report_render_v6').glob('page-*.png'))
check('Word_rendered_all_pages',pages==len(pngs) and pages>=7,f'{pages} pages, {len(pngs)} PNGs')

status='PASS' if all(x['status']=='PASS' for x in checks.values()) else 'FAIL'
out={'status':status,'checks':checks,'source_report_sha256':sha(task/'outputs/LFP_SOH_双方案设计验证与比较报告.md'),
     'word_sha256':sha(docx),'rendered_pages':pages}
(task/'notes/final_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(status,len(checks),'checks;',pages,'rendered pages')
