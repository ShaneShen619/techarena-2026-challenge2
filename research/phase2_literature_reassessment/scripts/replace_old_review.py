"""Hash-guarded, checkpointed replacement of the prior literature review.

Usage: python3 scripts/replace_old_review.py prepare|apply|rollback
Only run `apply` after final acceptance. Each file is atomic; the batch is not.
"""
import csv
import hashlib
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

TASK = Path(__file__).resolve().parents[1]
RESEARCH = TASK.parent
OLD = RESEARCH / "phase2_literature"
MANIFEST = TASK / "outputs/replacement_manifest.json"
MAP = [
    ("outputs/LFP_SOH_第二阶段文献综述与技术路线_深度重评.md", "outputs/LFP_SOH_第二阶段文献综述与技术路线.md"),
    ("outputs/LFP_SOH_第二阶段文献综述与技术路线_深度重评.docx", "outputs/LFP_SOH_第二阶段文献综述与技术路线.docx"),
    ("outputs/method_comparison.csv", "outputs/方法对比.csv"),
    ("outputs/references.bib", "outputs/references.bib"),
    ("outputs/NEXT_STEPS.md", "outputs/NEXT_STEPS.md"),
    ("outputs/CURRENT_REVIEW_FOR_OLD.md", "CURRENT_REVIEW.md"),
    ("outputs/HISTORICAL_ENTRY_FOR_OLD.md", "HISTORICAL_ENTRY.md"),
]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".replacement_", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def replace_from(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".review_", dir=target.parent)
    try:
        with os.fdopen(fd, "wb") as dst, Path(source).open("rb") as src:
            shutil.copyfileobj(src, dst)
            dst.flush()
            os.fsync(dst.fileno())
        os.replace(tmp, target)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def prepare():
    if MANIFEST.exists():
        raise RuntimeError("Replacement manifest exists; inspect/resume instead of preparing another backup")
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    archive = TASK / "archive" / f"phase2_literature_before_{stamp}"
    selected = []
    for dirname in ("outputs", "notes"):
        selected += [p for p in (OLD / dirname).rglob("*") if p.is_file()]
    selected += [OLD / "START_PROMPT.md", OLD / "ENVIRONMENT.md"]
    inventory = []
    for old_file in sorted(selected):
        rel = old_file.relative_to(OLD)
        dest = archive / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(old_file, dest)
        old_hash = sha(old_file)
        if sha(dest) != old_hash:
            raise RuntimeError(f"Backup hash mismatch: {rel}")
        inventory.append((str(rel), old_hash, str(dest.relative_to(TASK))))
    with (archive / "backup_inventory.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["old_relative_path", "sha256", "backup_relative_to_new_task"])
        w.writerows(inventory)
    entries = []
    for source_rel, target_rel in MAP:
        source, target = TASK / source_rel, OLD / target_rel
        if not source.is_file():
            raise RuntimeError(f"Missing replacement source: {source}")
        existed = target.exists()
        backup = archive / target_rel if existed else None
        if existed and (not backup.is_file() or sha(backup) != sha(target)):
            raise RuntimeError(f"Target backup missing/mismatch: {target_rel}")
        entries.append({
            "source": str(source.relative_to(TASK)),
            "target": str(target.relative_to(RESEARCH)),
            "target_existed": existed,
            "old_sha256": sha(target) if existed else None,
            "new_sha256": sha(source),
            "backup": str(backup.relative_to(TASK)) if backup else None,
            "status": "prepared",
        })
    state = {"created_at": datetime.now().isoformat(), "archive": str(archive.relative_to(TASK)),
             "backup_inventory_sha256": sha(archive / "backup_inventory.csv"),
             "batch_status": "prepared", "entries": entries,
             "atomicity": "Per-file os.replace only; batch may be partial. Resume using this manifest.",
             "schema_note": "Old 方法对比.csv had paper-level rows/来源ID; new CSV has 12 method-family rows/family_id. Use paper_registry.csv and claim_evidence.csv for paper IDs."}
    write_json(MANIFEST, state)
    print("prepared", len(inventory), "archived files", len(entries), "replacement entries", archive)


def apply():
    state = json.loads(MANIFEST.read_text(encoding="utf-8"))
    accepted = json.loads((TASK / "outputs/review_acceptance.json").read_text(encoding="utf-8"))
    if accepted.get("research_review_complete") is not True or accepted.get("word_render_verified") is not True:
        raise RuntimeError("Final research/Word acceptance has not passed")
    if accepted.get("reader_test_status") != "passed" or accepted.get("independent_audit_status") != "passed":
        raise RuntimeError("Independent audit or fresh-reader acceptance has not passed")
    state["batch_status"] = "in_progress"
    write_json(MANIFEST, state)
    for e in state["entries"]:
        source = TASK / e["source"]
        target = RESEARCH / e["target"]
        if sha(source) != e["new_sha256"]:
            e["status"] = "source_conflict"
            write_json(MANIFEST, state)
            raise RuntimeError(f"Source changed: {source}")
        if e["status"] == "replaced":
            if not target.is_file() or sha(target) != e["new_sha256"]:
                e["status"] = "postwrite_conflict"
                write_json(MANIFEST, state)
                raise RuntimeError(f"Already replaced target changed: {target}")
            continue
        if e["target_existed"]:
            backup = TASK / e["backup"]
            if sha(backup) != e["old_sha256"]:
                raise RuntimeError(f"Backup changed: {backup}")
            if not target.is_file() or sha(target) != e["old_sha256"]:
                e["status"] = "target_conflict"
                write_json(MANIFEST, state)
                raise RuntimeError(f"Old target changed; no overwrite: {target}")
        elif target.exists():
            e["status"] = "target_conflict"
            write_json(MANIFEST, state)
            raise RuntimeError(f"New entry already exists; no overwrite: {target}")
        replace_from(source, target)
        if sha(target) != e["new_sha256"]:
            raise RuntimeError(f"Postwrite hash mismatch: {target}")
        e["status"] = "replaced"
        e["replaced_at"] = datetime.now().isoformat()
        write_json(MANIFEST, state)
    for e in state["entries"]:
        if e["status"] != "replaced" or sha(RESEARCH / e["target"]) != e["new_sha256"]:
            raise RuntimeError("Batch consistency check failed")
    state["batch_status"] = "complete"
    state["completed_at"] = datetime.now().isoformat()
    write_json(MANIFEST, state)
    print("complete", len(state["entries"]), "replacements")


def rollback():
    state = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for e in reversed(state["entries"]):
        if e["status"] != "replaced":
            continue
        target = RESEARCH / e["target"]
        if not target.is_file() or sha(target) != e["new_sha256"]:
            e["status"] = "rollback_conflict"
            write_json(MANIFEST, state)
            raise RuntimeError(f"Refusing to overwrite changed target: {target}")
        if e["target_existed"]:
            replace_from(TASK / e["backup"], target)
            expected = e["old_sha256"]
            if sha(target) != expected:
                raise RuntimeError(f"Rollback verification failed: {target}")
        else:
            target.unlink()
        e["status"] = "rolled_back"
        write_json(MANIFEST, state)
    state["batch_status"] = "rolled_back"
    write_json(MANIFEST, state)
    print("rolled back")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("prepare", "apply", "rollback"):
        raise SystemExit("Usage: replace_old_review.py prepare|apply|rollback")
    {"prepare": prepare, "apply": apply, "rollback": rollback}[sys.argv[1]]()
