"""Create and inspect a source-only candidate ZIP; never follow data symlinks."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

TASK = Path(__file__).resolve().parents[1]
SOURCE = TASK / "candidates/multi_temp"
OUTPUT = TASK / "outputs/multi_temp_candidate.zip"
SAFE_ROOT_FILES = {"README.md", "run_model.py", "validate_submission.py", "requirements.txt"}
SAFE_DIRS = {"framework", "my_model"}


def main() -> None:
    selected = []
    for path in SOURCE.rglob("*"):
        if path.is_symlink():
            continue
        if not path.is_file() or path.suffix == ".pyc" or "__pycache__" in path.parts:
            continue
        rel = path.relative_to(SOURCE)
        if len(rel.parts) == 1 and rel.name in SAFE_ROOT_FILES:
            selected.append((path, rel))
        elif len(rel.parts) > 1 and rel.parts[0] in SAFE_DIRS:
            selected.append((path, rel))
    selected.sort(key=lambda item: str(item[1]))
    with ZipFile(OUTPUT, "w", ZIP_DEFLATED) as archive:
        for path, rel in selected:
            archive.write(path, str(rel))
    with ZipFile(OUTPUT) as archive:
        names = archive.namelist()
        if any(name.startswith("data/") or name.startswith("sample_data/") for name in names):
            raise AssertionError("data leaked into candidate package")
        if not {"my_model/model.py", "run_model.py", "validate_submission.py"}.issubset(names):
            raise AssertionError("candidate package incomplete")
        for name in names:
            if name.startswith("/") or ".." in Path(name).parts:
                raise AssertionError("unsafe ZIP member")
    receipt = {"file": str(OUTPUT.relative_to(TASK)),
               "sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
               "size_bytes": OUTPUT.stat().st_size, "files": names,
               "contains_raw_or_sample_data": False}
    (TASK / "outputs/candidate_package_manifest.json").write_text(json.dumps(receipt, indent=2)+"\n")
    print(json.dumps({"sha256": receipt["sha256"], "size_bytes": receipt["size_bytes"],
                      "files": len(names)}, indent=2))


if __name__ == "__main__":
    main()
