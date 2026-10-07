"""M0 read-only source inventory, preserving old frozen evidence.

P1 bytes are rehashed; official data are checked against the earlier official
hash manifest; TU 18.5 GiB uses file size/mtime against full-scan audit and
does not claim fresh byte-level confirmation.
"""
from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parents[1]
OLD = ROOT / 'research/phase2_temperature_improvement'
AUDIT = ROOT / 'research/phase2_validation/preflight/downloaded_data/audit_report.json'


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


old = json.loads((OLD / 'runs/M7_frozen_manifest.json').read_text())
audit = json.loads(AUDIT.read_text())
original_hashes = json.loads((ROOT/'research/phase2_validation/preflight/original_sha256.json').read_text())
rows = []
for item in old['raw_p1_files']:
    path = ROOT / item['path']
    actual = sha256(path)
    rows.append({'source': 'P1', 'path': item['path'], 'bytes': path.stat().st_size,
                 'prior_sha256': item['sha256'], 'current_sha256': actual,
                 'verification': 'byte_hash_match' if actual == item['sha256'] else 'HASH_MISMATCH'})
for rel, prior in original_hashes.items():
    if rel.startswith(('data/operation/', 'data/checkups/')):
        path = ROOT / rel
        actual = sha256(path)
        rows.append({'source': 'official', 'path': rel, 'bytes': path.stat().st_size,
                     'prior_sha256': prior, 'current_sha256': actual,
                     'verification': 'byte_hash_match' if actual == prior else 'HASH_MISMATCH'})
for item in audit['quick_manifest']:
    rel = item['path']
    if not rel.startswith('TU Darmstadt/'):
        continue
    path = ROOT / rel
    stat = path.stat()
    match = stat.st_size == item['bytes'] and stat.st_mtime_ns == item['mtime_ns']
    rows.append({'source': 'TU', 'path': rel, 'bytes': stat.st_size,
                 'prior_sha256': '', 'current_sha256': '',
                 'verification': 'size_mtime_match_to_prior_full_scan' if match else 'METADATA_MISMATCH'})
che = ROOT / 'Che-Dataset3.mat'
rows.append({'source': 'Che', 'path': che.name, 'bytes': che.stat().st_size,
             'prior_sha256': '', 'current_sha256': sha256(che),
             'verification': 'current_hash_no_publisher_comparison'})
manifest = pd.DataFrame(rows)
manifest.to_csv(TASK/'data_manifests/source_inventory.csv', index=False)
fail = manifest.loc[manifest.verification.str.contains('MISMATCH')]
panel = OLD/'outputs/panel_main.csv'
panel_hash = sha256(panel)
panel_rows = pd.read_csv(panel)
if panel_hash != '7188b662900f84312292a7062d6023e5eeb4f2e32798b6d61a3547ed40cdc59c':
    raise RuntimeError('Frozen P1 panel changed')
if len(panel_rows) != 180 or panel_rows.groupby('cell_id').size().ne(30).any():
    raise RuntimeError('P1 panel shape changed')
if len(fail):
    raise RuntimeError(f'Input changed: {fail.path.tolist()}')
summary = {'source_counts': manifest.groupby('source').size().to_dict(),
           'panel_sha256': panel_hash, 'panel_rows': len(panel_rows),
           'panel_physical_cells': panel_rows.cell_id.nunique(),
           'tu_verification_limit': 'prior full-scan hashes are not rehashed in M0; file size and mtime match only',
           'che_verification_limit': 'current local SHA256 only; publisher byte hash unavailable',
           'python': platform.python_version(), 'platform': platform.platform()}
(TASK/'data_manifests/source_inventory_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(summary, ensure_ascii=False), flush=True)
