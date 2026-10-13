from common import *
def main():
 audit=json.loads((TASK/'audit_checks.json').read_text());assert all(x['pass_'] for x in audit)
 gate=json.loads((TASK/'acceptance.json').read_text());assert not gate['replace_current_B']
 labels=pd.read_csv(TASK/'label_inventory.csv');assert labels[(labels.source=='official')&(labels.event_id!='CK0')].label_Ah.isna().all();assert labels[labels.source=='official'].label_temperature_C.isna().all()
 p=pd.read_csv(TASK/'official_support_by_event.csv');assert not p.capacity_transfer_accepted.any();assert p[['Qpack_Ah','SOH_percent']].isna().all().all()
 models=json.loads((TASK/'source_budget_models_provenance.json').read_text());assert len(models)==7 and all(m['official_rows_used']==0 for m in models)
 protected=json.loads((TASK/'protected_files.json').read_text());assert all(sha(WORK/r['path'])==r['sha256'] and sha(SOURCE/r['path'])==r['sha256'] for r in protected)
 metrics=pd.read_csv(TASK/'metrics_P1_main.csv');assert (metrics.family=='F0_raw').sum()==1;assert metrics[metrics.family=='joint'].MAE_Ah.iat[0]>metrics[metrics.family=='F0_F1_CCCV'].MAE_Ah.iat[0]
 assert not subprocess.check_output(['git','diff','--name-only'],cwd=SOURCE,text=True).strip();assert not subprocess.check_output(['git','diff','--name-only'],cwd=WORK,text=True).strip()
 save('final_verification.json',{'passed':True,'scientific_checks':len(audit),'source_only_budget_models':len(models),'formal_files_identical':True,'unreleased_labels_and_errors_not_filled':True,'official_reference_temperature_not_invented':True,'capacity_gate_fail_preserved':True,'tracked_git_diffs_empty':True})
 print('final verification PASS',flush=True)
if __name__=='__main__':main()
