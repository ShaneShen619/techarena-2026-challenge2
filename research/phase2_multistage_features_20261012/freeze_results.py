"""Finalize research provenance, no mutation of protected files or old research."""
from common import *
def main():
 extra=[SOURCE/'research/charge_capacity_review_20261006/operating_events.csv',SOURCE/'data/checkups/evaluation_points.csv',SOURCE/'research/phase2_literature_reassessment/papers/B_sources/Gasper2025_OSTI.txt',SOURCE/'research/phase2_literature_reassessment/papers/B_sources/Gasper2025_OSTI.pdf',SOURCE/'research/phase2_literature_reassessment/papers/D_old_refs/Zhu2022.txt',SOURCE/'research/phase2_literature_reassessment/papers/D_old_refs/Zhu2022.pdf',SOURCE/'research/phase2_literature_reassessment/papers/D_old_refs/Zhu2022_MOESM1.txt',SOURCE/'research/phase2_literature_reassessment/papers/D_old_refs/Zhu2022_MOESM1.pdf',SOURCE/'research/phase2_literature_reassessment/outputs/LFP_SOH_核心论文精读与证据附册.md',SOURCE/'research/phase2_literature_reassessment/outputs/LFP_SOH_第二阶段文献综述与技术路线_深度重评.md',SOURCE/'research/phase2_signal_driven_routes_20261011/阶段二四串电池组_运行信号驱动路线评估.md',SOURCE/'research/phase2_joint_discharge_20261011/README.md',SOURCE/'research/phase2_initial_soc_four_methods_20261011/FINAL_REPORT.md',SOURCE/'research/phase2_method_exploration/data_manifests/source_inventory.csv',SOURCE/'research/phase2_method_exploration/data_manifests/source_inventory_summary.json']
 save('read_materials_manifest.json',[dict(path=str(p),sha256=sha(p),read_only=True) for p in extra if p.exists()])
 save('git_final_audit.json',{'original_branch':subprocess.check_output(['git','branch','--show-current'],cwd=SOURCE,text=True).strip(),'worktree_branch':subprocess.check_output(['git','branch','--show-current'],cwd=WORK,text=True).strip(),'original_HEAD':subprocess.check_output(['git','rev-parse','HEAD'],cwd=SOURCE,text=True).strip(),'worktree_HEAD':subprocess.check_output(['git','rev-parse','HEAD'],cwd=WORK,text=True).strip(),'original_tracked_diff':subprocess.check_output(['git','diff','--name-only'],cwd=SOURCE,text=True).splitlines(),'worktree_tracked_diff':subprocess.check_output(['git','diff','--name-only'],cwd=WORK,text=True).splitlines(),'original_status':subprocess.check_output(['git','status','--short'],cwd=SOURCE,text=True).splitlines(),'task_link_target':str((SOURCE/'research/phase2_multistage_features_20261012').resolve())})
 # Snapshot excludes virtualenv, caches, unneeded staging file, and the manifest itself.
 pending=TASK/'canvas_source_pending.txt'
 if pending.exists():pending.unlink()
 entries=[]
 for p in sorted(TASK.rglob('*')):
  rel=p.relative_to(TASK)
  if not p.is_file() or any(part in ['.venv','__pycache__'] for part in rel.parts) or p.name in ['artifact_manifest.json','RESULTS_FROZEN.json']:continue
  entries.append(dict(path=str(rel),bytes=p.stat().st_size,sha256=sha(p)))
 canvas=Path('/Users/shane/.cursor/projects/Users-shane-Desktop-Arena-2/canvases/phase2-multistage-features.canvas.tsx');entries.append(dict(path=str(canvas),bytes=canvas.stat().st_size,sha256=sha(canvas)))
 save('artifact_manifest.json',entries);save('RESULTS_FROZEN.json',{'utc':pd.Timestamp.now(tz='UTC').isoformat(),'artifact_manifest_sha256':sha(TASK/'artifact_manifest.json'),'artifact_count':len(entries),'protected_files_unchanged':True,'capacity_acceptance':'FAIL','real_group_capacity_status':'UNVERIFIED','public_paper_benchmarks_completed':False,'reproduce_into_new_sibling_only':True})
 print('frozen',len(entries),'artifacts',flush=True)
if __name__=='__main__':main()
