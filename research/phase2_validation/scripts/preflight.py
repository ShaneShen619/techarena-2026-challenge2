"""Reproducible environment/data/interface preflight; does not validate A/B accuracy."""
from pathlib import Path
import hashlib
import importlib.metadata as metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / "research/phase2_validation"
OUT = WORK / "preflight"
OUT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(WORK / ".cache/matplotlib"))
os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("XDG_CACHE_HOME", str(WORK / ".cache"))
os.environ.setdefault("FONTCONFIG_FILE", str(WORK / "fonts.conf"))
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
import numpy as np
import pandas as pd
import scipy.linalg
import scipy.optimize
import scipy.interpolate
import scipy.io
import h5py
import matplotlib.pyplot as plt


def sha(path):
    return hashlib.file_digest(path.open("rb"), "sha256").hexdigest()


def command(name, args, cwd, timeout=600):
    start = time.monotonic()
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout,
                       env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    (OUT / f"{name}.log").write_text(r.stdout + "\n" + r.stderr, encoding="utf-8")
    result = {"exit_code": r.returncode, "seconds": round(time.monotonic()-start, 3),
              "command": args, "cwd": str(cwd)}
    print(name, result["exit_code"], result["seconds"], flush=True)
    if r.returncode:
        raise RuntimeError(f"{name} failed; see {OUT / (name+'.log')}")
    return result


def main():
    start = time.monotonic()
    original = [ROOT / "run_model.py", ROOT / "validate_submission.py", ROOT / "requirements.txt"]
    original += sorted((ROOT / "framework").glob("*.py"))
    original += sorted((ROOT / "my_model").glob("*.py"))
    original += sorted((ROOT / "data").rglob("*.csv*"))
    original += sorted((ROOT / "sample_data").rglob("*.csv*"))
    before = {str(p.relative_to(ROOT)): sha(p) for p in original}
    stored_manifest = OUT / "original_sha256.json"
    if stored_manifest.exists():
        assert json.loads(stored_manifest.read_text()) == before, "Original files differ from initial preflight snapshot"
    report = {"checked_at": pd.Timestamp.now(tz="UTC").isoformat(),
              "python": sys.version, "executable": sys.executable,
              "platform": platform.platform(), "cpu_count": os.cpu_count(),
              "free_disk_GiB": round(shutil.disk_usage(ROOT).free / 2**30, 2),
              "packages": {n: metadata.version(n) for n in
                           ["numpy", "pandas", "scipy", "matplotlib", "pytest", "h5py",
                            "python-docx", "pypdf", "pillow"]}}
    assert sys.version_info[:2] in [(3, 11), (3, 12)], "Official Python requirement"
    fit = scipy.optimize.least_squares(lambda x: np.array([2*x[0]-6]), [0.])
    assert abs(fit.x[0]-3) < 1e-6
    assert np.isfinite(scipy.linalg.cho_factor(np.eye(3))[0]).all()
    assert float(scipy.interpolate.PchipInterpolator([0, .5, 1], [2.8, 3.3, 3.6])(.25)) > 2.8
    scipy.io.savemat(OUT / "probe.mat", {"x": np.arange(5)})
    assert scipy.io.loadmat(OUT / "probe.mat")["x"].size == 5
    with h5py.File(OUT / "probe.h5", "w") as f:
        f["x"] = np.arange(5)
    with h5py.File(OUT / "probe.h5", "r") as f:
        assert f["x"].shape == (5,)
    plt.plot([0, 1, 2], [100, 98, 95]); plt.xlabel("Probe"); plt.ylabel("SOH (%)")
    plt.savefig(OUT / "plot_probe.png"); plt.close()
    report["numeric_io_plot_probes"] = "passed"
    manifest = []
    cols = ["timestamp", "segment", "current_A", "charge_Ah_cum", "discharge_Ah_cum",
            "cell1_V", "cell2_V", "cell3_V", "cell4_V", "pack_voltage_V", "temp_mean_C"]
    for p in sorted((ROOT / "data/operation").glob("*.csv.gz")):
        d = pd.read_csv(p, parse_dates=["timestamp"])
        assert not set(cols)-set(d.columns), p
        dt = d.timestamp.diff().dt.total_seconds()
        manifest.append({"file": str(p.relative_to(ROOT)), "sha256": before[str(p.relative_to(ROOT))],
                         "bytes": p.stat().st_size, "rows": len(d),
                         "first": str(d.timestamp.min()), "last": str(d.timestamp.max()),
                         "duplicate_timestamp": int(d.timestamp.duplicated().sum()),
                         "backward_timestamp": int((dt < 0).sum()),
                         "gap_gt_60s": int((dt > 60).sum()),
                         "missing_required_values": int(d[cols].isna().sum().sum()),
                         "temperature_setpoint": sorted(d.chamber_temperature_C.unique().tolist()),
                         "charge_counter_decreases": int((d.charge_Ah_cum.diff() < -1e-6).sum()),
                         "discharge_counter_decreases": int((d.discharge_Ah_cum.diff() < -1e-6).sum()),
                         "max_pack_sum_error_V": float((d.pack_voltage_V - d[[f"cell{i}_V" for i in range(1,5)]].sum(axis=1)).abs().max())})
    pd.DataFrame(manifest).to_csv(OUT / "data_manifest.csv", index=False)
    ck = pd.read_csv(ROOT / "data/checkups/checkup_capacities_released.csv")
    ref = pd.read_csv(ROOT / "data/checkups/CK0_reference_discharge.csv.gz")
    ev = pd.read_csv(ROOT / "data/checkups/evaluation_points.csv")
    report["data"] = {"segments": len(manifest), "operation_rows": sum(x["rows"] for x in manifest),
                      "duplicates": sum(x["duplicate_timestamp"] for x in manifest),
                      "gaps_gt_60s_within_segment": sum(x["gap_gt_60s"] for x in manifest),
                      "missing_required_values": sum(x["missing_required_values"] for x in manifest),
                      "checkup_labels": ck.to_dict("records"), "eval_points": ev.to_dict("records"),
                      "reference_rows": len(ref), "reference_columns": ref.columns.tolist(),
                      "reference_discharge_Ah_range": [float(ref.discharged_Ah.min()), float(ref.discharged_Ah.max())]}
    sandbox = OUT / "baseline_template"
    sandbox.mkdir(exist_ok=True)
    for name in ["run_model.py", "validate_submission.py", "requirements.txt"]:
        shutil.copy2(ROOT / name, sandbox / name)
    for name in ["framework", "my_model", "sample_data"]:
        shutil.copytree(ROOT / name, sandbox / name, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__"))
    # This copy intentionally preserves the official ExampleModel as the reference.
    report["sample_validation"] = command("sample_validation", [sys.executable, "validate_submission.py"], sandbox)
    full = OUT / "baseline_full"
    report["full_train"] = command("baseline_full_train", [sys.executable, "run_model.py", "--model", "train", "--input", str(ROOT / "data"), "--output-dir", str(full)], sandbox)
    report["full_test"] = command("baseline_full_test", [sys.executable, "run_model.py", "--model", "test", "--input", str(ROOT / "data"), "--state-dir", str(full), "--output-dir", str(full), "--eval-point", "all"], sandbox)
    pred = pd.read_csv(full / "output.csv")
    assert len(pred) == 8 and pred.checkup.nunique() == 8
    assert np.isfinite(pred.SOH_est).all()
    report["baseline_predictions"] = pred.to_dict("records")
    after = {str(p.relative_to(ROOT)): sha(p) for p in original}
    assert before == after, "Original data/framework/model changed"
    (OUT / "original_sha256.json").write_text(json.dumps(before, indent=2), encoding="utf-8")
    report["original_files_unchanged"] = True
    report["duration_seconds"] = round(time.monotonic() - start, 3)
    report["status"] = "ENGINEERING_PREFLIGHT_PASSED_NOT_SOH_ACCURACY_VALIDATION"
    (OUT / "preflight_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status": report["status"], "data": report["data"], "seconds": report["duration_seconds"]}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
