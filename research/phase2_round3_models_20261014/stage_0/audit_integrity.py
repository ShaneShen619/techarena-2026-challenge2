"""Independent non-mutating audit of protocols, git scope and candidate evidence."""
import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from common import STUDY, REPO, dump

def audit():
    changed = subprocess.check_output(['git','diff','--name-only','24728fa'],cwd=REPO,text=True).splitlines()
    protected = [p for p in changed if not p.startswith('research/phase2_round3_models_20261014/')]
    protocols = {}
    for stage in ('B','D','A','C','E','F'):
        p = STUDY / f'stage_{stage}/protocol.json'
        sha = p.with_suffix('.sha256')
        if p.exists() and sha.exists():
            actual = hashlib.sha256(p.read_bytes()).hexdigest()
            expected = sha.read_text().split()[0]
            protocols[stage] = {'hash_matches': actual == expected, 'sha256':actual}
        else:
            protocols[stage] = {'present':False}
    candidates = {}
    for p in sorted((STUDY/'candidate_model').glob('*_model.py')):
        tree = ast.parse(p.read_text())
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(n.name.split('.')[0] for n in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append((node.module or '').split('.')[0])
        disallowed = sorted(set(imports) - set(sys.stdlib_module_names) - {'numpy','pandas'})
        candidates[p.name] = {'imports': sorted(set(imports)), 'additional_imports_to_inspect':disallowed}
    supplement_hashes={}
    for sha in sorted(STUDY.rglob('*.sha256')):
        p=sha.with_suffix('.json')
        if p.exists():
            supplement_hashes[str(p.relative_to(STUDY))]=hashlib.sha256(p.read_bytes()).hexdigest()==sha.read_text().split()[0]
    documents={str(p.relative_to(STUDY)):all(marker in p.read_text() for marker in ['<a id="en"></a>','<a id="zh"></a>','---']) for p in STUDY.rglob('*.md') if 'cache' not in p.relative_to(STUDY).parts}
    return {'protected_paths_modified':protected, 'scope_passed':not protected,
            'protocols':protocols, 'candidate_import_audit':candidates,
            'all_protocol_hashes':supplement_hashes,'markdown_bilingual_markers':documents,
            'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()}

if __name__ == '__main__':
    result=audit()
    dump(STUDY/'stage_0/outputs/independent_integrity_audit.json',result)
    print(json.dumps(result,indent=2))
    assert result['scope_passed']
    assert all(x.get('hash_matches',True) for x in result['protocols'].values())
    assert all(result['all_protocol_hashes'].values())
    assert all(result['markdown_bilingual_markers'].values())
