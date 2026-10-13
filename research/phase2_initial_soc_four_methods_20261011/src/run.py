"""Sequential implementation checks, frozen choices, evaluation, diagnostics."""
from __future__ import annotations
import argparse,json,pickle,sys,time
from pathlib import Path
import numpy as np
import pandas as pd
from audit import RUN,TASK,ROOT,CFG,audit,digest
from engine import Template
from checks import run_checks
from official import develop,run_replay,identifiability
from synthetic import mechanism_scores,initial_error_test

def main():
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['prepare','develop','evaluate','diagnose','all']);args=parser.parse_args()
    start=time.time()
    if not (RUN/'events.pkl').exists():audit()
    with open(RUN/'events.pkl','rb') as f:events=pickle.load(f)
    template=Template()
    if args.stage in ['prepare','all']:run_checks(events)
    if args.stage in ['develop','all']:
        selected=develop(template,events)
        mechanism_scores(CFG['synthetic_development_seeds'],'development')
        # Four-method code and all numerical choices fixed before final scoring.
        files=[*sorted((TASK/'src').glob('*.py')),TASK/'protocol.md',TASK/'configs/frozen_protocol.json',RUN/'selected_configuration.json']
        freeze=dict(files=[dict(path=str(p.relative_to(ROOT)),sha256=digest(p)) for p in files],evaluation_opened=False,selected=selected,python=sys.version)
        (RUN/'freeze_manifest.json').write_text(json.dumps(freeze,indent=2))
    if args.stage in ['evaluate','all']:
        freeze=json.loads((RUN/'freeze_manifest.json').read_text())
        for r in freeze['files']:
            if digest(ROOT/r['path'])!=r['sha256']:raise ValueError('postfreeze_code_change: '+r['path'])
        if (RUN/'EVALUATION_COMPLETE').exists():raise ValueError('already_scored: use a new version, do not overwrite final results')
        selected=freeze['selected']
        print('M1→M4 frozen sequential official replay',flush=True)
        metrics,profiles=run_replay(template,events,selected)
        mechanism_scores(CFG['synthetic_test_seeds'],'evaluation')
        initial_error_test(CFG['synthetic_test_seeds'])
        identifiability(template,events,selected,profiles)
        (RUN/'EVALUATION_COMPLETE').write_text('Frozen v1 evaluation complete; no tuning on these outcomes.\n')
    if args.stage=='diagnose':
        selected=json.loads((RUN/'selected_configuration.json').read_text());profiles={}
        from official import cached_profile,key
        for e in events:profiles[e['id']]=cached_profile(template,e,selected[key(e)]['tau'])
        identifiability(template,events,selected,profiles)
    print('stage complete',args.stage,'seconds',time.time()-start,flush=True)

if __name__=='__main__':main()
