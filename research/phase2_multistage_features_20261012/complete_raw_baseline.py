"""Complete prespecified actual V/I/T/P/PI raw waveform baseline, same main folds."""
from source_benchmarks import *
def main():
 f=pd.read_csv(TASK/'P1_features.csv');g=f[f[['f2_1800_Var','f4_1800_Var']].notna().all(axis=1)].reset_index(drop=True)
 cols=families(g)['F0_raw'];run(g,{'F0_raw':cols},'P1_raw_complete')
 # Keep earlier raw baseline as a named development record; main canonical row uses completed actual T/PI input.
 for prefix in ['metrics','predictions','tuning','entity_errors']:
  suffix='.json' if prefix=='tuning' else '.csv';old=TASK/f'{prefix}_P1_main{suffix}';new=TASK/f'{prefix}_P1_raw_complete{suffix}'
  if suffix=='.csv':
   o=pd.read_csv(old);n=pd.read_csv(new);n['dataset']='P1_main' if 'dataset' in n else 'P1_main'
   if 'dataset' not in o:n=n.drop(columns='dataset')
   backup=TASK/'development_before_pairing_and_F0_completion'/f'raw_without_temperature_{old.name}';backup.write_bytes(old.read_bytes())
   pd.concat([o[o.family!='F0_raw'],n],ignore_index=True).to_csv(old,index=False)
  else:
   o=json.loads(old.read_text());n=json.loads(new.read_text());save(old.name,[x for x in o if x['family']!='F0_raw']+n)
 save('raw_baseline_provenance.json',{'inputs':cols,'availability':'fixed0/30/60/120/300 seconds, budget discharge ended','current_sign':'negative discharge, nominal normalization; actual amps used for PI','T':'actual observed discharge temperature, shared for each physical event','zero_current':'PI=0 with explicit mask','scope':'small fixed-grid project baseline, not Gasper rapid pulse protocol; mandatory V/I/T/P input completed before final freeze','all_other_main_predictions_unchanged':True})
if __name__=='__main__':main()
