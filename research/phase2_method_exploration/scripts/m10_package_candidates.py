"""Create clean research candidate zips and independent extraction receipts."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

TASK = Path(__file__).resolve().parents[1]
OUT = TASK / "outputs"
REPLAY = TASK / "runs/M10_clean_extract_v1"
REPLAY.mkdir(parents=True, exist_ok=False)
manifest = {}
for name in ("ck0_hold", "exploratory_fallback"):
    source = TASK / "candidates" / name
    target = OUT / f"{name}_research_candidate.zip"
    files = [p for p in source.rglob("*") if p.is_file() and "__pycache__" not in p.parts
             and p.suffix != ".pyc" and p.name not in {".DS_Store", "validation_report.txt"}]
    assert files
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for file in sorted(files):
            z.write(file, file.relative_to(source).as_posix())
    extracted = REPLAY / name
    extracted.mkdir()
    with zipfile.ZipFile(target) as z:
        assert all(not p.startswith("/") and ".." not in Path(p).parts for p in z.namelist())
        z.extractall(extracted)
    assert (extracted / "run_model.py").exists()
    assert (extracted / "my_model/__init__.py").exists()
    manifest[name] = {"zip": str(target.relative_to(TASK)), "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                      "file_count": len(files), "uncompressed_bytes": sum(p.stat().st_size for p in files),
                      "contains_original_data_directory": any(p.relative_to(source).parts[0] == "data" for p in files),
                      "clean_extraction": str(extracted.relative_to(TASK))}
    assert not manifest[name]["contains_original_data_directory"]
(OUT / "candidate_package_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(manifest, ensure_ascii=False), flush=True)
