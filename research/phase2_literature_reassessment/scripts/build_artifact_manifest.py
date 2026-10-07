"""Create SHA256 inventory of final deliverables and acceptance evidence."""
import csv
import hashlib
from pathlib import Path

task = Path(__file__).resolve().parents[1]
files = sorted((task / "outputs").glob("*"))
files += [task / p for p in (
    "notes/DOCX_VISUAL_QA.md",
    "notes/READER_TEST.md",
    "notes/AUDIT_CORRECTIONS.md",
    "notes/INDEPENDENT_EVIDENCE_AUDIT.md",
    "notes/INDEPENDENT_EVIDENCE_AUDIT_ADDENDUM.md",
    "notes/INDEPENDENT_EVIDENCE_AUDIT_FINAL_ADDENDUM.md",
    "notes/STATUS.md",
    "notes/TASK_LEDGER.csv",
)]
files += list((task / "archive").glob("phase2_literature_before_*/backup_inventory.csv"))
target = task / "outputs/artifact_manifest.csv"
with target.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["relative_path", "sha256", "bytes", "kind"])
    for p in files:
        if not p.is_file() or p == target:
            continue
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        kind = "formal_output" if p.parent == task / "outputs" else "acceptance_evidence"
        w.writerow([str(p.relative_to(task)), h, p.stat().st_size, kind])
print("manifest entries", sum(1 for _ in target.open(encoding="utf-8")) - 1)
