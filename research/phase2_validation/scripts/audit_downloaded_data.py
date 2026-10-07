"""Read-only acceptance of downloaded sources. Outputs diagnostics, never CK1-CK7 labels.

First run scans all CSVs in bounded chunks and reads every Che feature reference.
Subsequent runs verify size/mtime and reuse the recorded full scan unless --full is given.
"""
from pathlib import Path
import argparse
import hashlib
import json
import time
import resource
import numpy as np
import pandas as pd
import h5py

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "research/phase2_validation/preflight/downloaded_data"


def identity(p, digest=True):
    st = p.stat()
    row = {"path": str(p.relative_to(ROOT)), "bytes": st.st_size, "mtime_ns": st.st_mtime_ns}
    if digest:
        with p.open("rb") as f:
            row["sha256"] = hashlib.file_digest(f, "sha256").hexdigest()
    return row


def phase1():
    cells, files, labels, smoke = [], [], [], []
    for folder in sorted((ROOT / "dataset original").glob("102Ah_*")):
        paths = sorted(folder.glob("*.csv"))
        part_numbers = [int(p.stem.split("part")[-1]) for p in paths]
        assert part_numbers == list(range(1, len(paths)+1)), folder
        frames = []
        for p in paths:
            d = pd.read_csv(p, parse_dates=["absolute_time"])
            assert set(["cycle_number", "step_type", "time_in_cycle_s", "voltage_V", "current_A", "temperature_C", "step_capacity_Ah", "absolute_time"]) <= set(d)
            assert d.absolute_time.notna().all()
            files.append({**identity(p), "rows": len(d), "columns": list(d.columns)})
            frames.append(d)
        d = pd.concat(frames, ignore_index=True)
        backward = int((d.absolute_time.diff().dt.total_seconds() < 0).sum())
        d = d.sort_values("absolute_time", kind="stable").reset_index(drop=True)
        dis = d[d.step_type == "cc_discharge"]
        q = dis.groupby("cycle_number").step_capacity_Ah.max().sort_index()
        # Exact old official scorer filtering, for label-side comparability only.
        med = q.shift(1).rolling(15, min_periods=3).median().fillna(q.rolling(9, center=True, min_periods=1).median())
        valid = (q >= 0) & (q <= 1.15*102) & (q >= .6*med)
        for cyc, val in q.items():
            labels.append({"cell_id": folder.name, "cycle": int(cyc), "capacity_Ah": float(val), "soh_pp": float(val/102*100), "old_official_label_valid": bool(valid.loc[cyc]), "label_protocol": "0.5C_or_1C_CC_discharge_to_2.5V_NOT_C20"})
        cells.append({"cell_id": folder.name, "parts": len(paths), "rows": len(d), "cycles": int(d.cycle_number.nunique()), "max_cycle": int(d.cycle_number.max()), "valid_capacity_labels": int(valid.sum()), "raw_backward_time_steps": backward,
                      "temperature_missing_fraction": float(d.temperature_C.isna().mean()),
                      "step_types": d.step_type.value_counts().to_dict(),
                      "discharge_current_median_A": float(dis.current_A.median()),
                      "valid_capacity_min_Ah": float(q[valid].min()), "valid_capacity_max_Ah": float(q[valid].max())})
        # Small scoring fixture: anchor strictly precedes each target; only preceding charge is input.
        ids = q[valid].index.to_numpy()
        anchor_cycle = int(ids[0]); anchor = float(q.loc[anchor_cycle])
        charging = (d.current_A > 0) & d.step_type.isin(["cccv_charge", "cc_charge"])
        charge = d.loc[charging].copy()
        # Zero-duration rest markers can be interleaved at charge step boundaries.
        # For ingestion fixtures, split positive-current records by actual time gaps.
        # Scientific CC/CV quality segmentation remains part of the main experiment.
        charge["_event"] = (charge.absolute_time.diff().dt.total_seconds().fillna(121) > 120).cumsum()
        charge_times = charge.absolute_time.to_numpy()
        for idx in sorted(set([min(10,len(ids)-1), len(ids)//2, len(ids)-1])):
            cyc = int(ids[idx])
            c = d[d.cycle_number == cyc]
            td = c[c.step_type == "cc_discharge"]
            if td.empty or cyc <= anchor_cycle:
                continue
            cutoff = td.absolute_time.min()
            # Cycle numbering does NOT guarantee that same-cycle charging precedes discharge.
            pos = np.searchsorted(charge_times, cutoff.to_datetime64(), side="left") - 1
            if pos < 0: continue
            last_event = int(charge.iloc[pos]._event)
            x = charge[(charge._event == last_event) & (charge.absolute_time < cutoff)]
            # Some source cycles overlap in absolute time. Never merge their current records.
            input_cycle_id = int(charge.iloc[pos].cycle_number)
            other_cycle_rows = int((x.cycle_number != input_cycle_id).sum())
            x = x[x.cycle_number == input_cycle_id]
            if len(x) < 10:
                continue
            assert x.absolute_time.max() < cutoff
            # Strictly input-only fixture; no target discharge capacity column is exported in X.
            feature_file = OUT / "fixtures" / f"{folder.name}_cycle{cyc}_charge.csv"
            x[["absolute_time", "voltage_V", "current_A", "temperature_C"]].to_csv(feature_file, index=False)
            target = float(q.loc[cyc]/102*100)
            pred = anchor/102*100
            smoke.append({"cell_id": folder.name, "cycle": cyc, "anchor_cycle": anchor_cycle,
                          "input_cycle_ids": sorted(x.cycle_number.unique().tolist()),
                          "overlapping_other_cycle_rows_excluded": other_cycle_rows,
                          "input_file": str(feature_file.relative_to(ROOT)), "input_rows": len(x),
                          "input_end": str(x.absolute_time.max()), "label_discharge_start": str(cutoff),
                          "anchor_soh_pp": pred, "target_soh_pp": target, "constant_baseline_abs_error_pp": abs(pred-target)})
        print("Phase1 accepted:", folder.name, "rows",len(d),"labels",int(valid.sum()), flush=True)
    pd.DataFrame(cells).to_csv(OUT / "phase1_cells.csv", index=False)
    pd.DataFrame(labels).to_csv(OUT / "phase1_label_inventory.csv", index=False)
    pd.DataFrame(smoke).to_csv(OUT / "scoring_fixture.csv", index=False)
    assert len(cells) == 6 and len(smoke) == 18
    assert len({s['cell_id'] for s in smoke}) == 6
    return {"files": files, "cells": cells, "rows": sum(c["rows"] for c in cells), "valid_capacity_labels": sum(c["valid_capacity_labels"] for c in cells), "scoring_fixture_rows": len(smoke), "status": "real_measured_discharge_proxy_ready_NOT_C20_or_pack_validation"}


def che():
    p = ROOT / "Che-Dataset3.mat"
    cells = []
    with h5py.File(p, "r") as h:
        g = h["Dataset3"]
        for j in range(g["Capacity"].shape[0]):
            txt = lambda key: "".join(chr(int(x)) for x in h[g[key][j,0]][()].ravel())
            q = np.asarray(h[g["Capacity"][j,0]][()]).ravel()
            cy = h[g["cycles"][j,0]]
            shapes, bad, count = set(), 0, 0
            for key in cy:
                refs = cy[key][()].ravel()
                assert len(refs) == len(q)
                for ref in refs:
                    a = np.asarray(h[ref][()])
                    shapes.add(tuple(a.shape)); bad += int((~np.isfinite(a)).sum()); count += 1
            cells.append({"cell_id": txt("cell"), "working_profile": txt("Workingprofile"), "capacity_count": len(q), "capacity_first": float(q[0]), "capacity_last": float(q[-1]), "capacity_nonfinite": int((~np.isfinite(q)).sum()), "cycle_fields": list(cy.keys()), "feature_shapes": [list(s) for s in sorted(shapes)], "feature_arrays_read": count, "feature_nonfinite": bad})
    assert len(cells) == 11
    (OUT / "che_structure.json").write_text(json.dumps(cells, indent=2, ensure_ascii=False))
    print("Che accepted: 11 cells; all feature arrays decoded", flush=True)
    return {"file": identity(p), "cells": cells, "total_cycles": sum(c["capacity_count"] for c in cells), "raw_time_current_voltage_available": False, "explicit_voltage_grid_available": False, "status": "partial_Q_capacity_proxy_only_grid_and_label_semantics_need_metadata"}


def tu():
    records = []
    for p in sorted((ROOT / "TU Darmstadt").glob("data_sys_*.csv"), key=lambda p:int(p.stem.split('_')[-1])):
        start = time.monotonic()
        header = pd.read_csv(p, nrows=0).columns.tolist()
        assert {"Timestamp", "I_Battery", "U_Battery", "SOC_Battery", "U_Cell_1", "U_Cell_8", "I_CNV_Cell_1", "Temperature_1"} <= set(header)
        rows = bad_time = missing_iv = backward = 0
        first = last = previous = None
        imin, imax = float("inf"), -float("inf")
        # Bounded-memory full scan. Parser traverses every row; numeric checks use selected columns.
        for chunk in pd.read_csv(p, usecols=["Timestamp", "I_Battery", "U_Battery", "SOC_Battery"], chunksize=200000):
            ts = pd.to_datetime(chunk.Timestamp, errors="coerce")
            rows += len(chunk); bad_time += int(ts.isna().sum())
            missing_iv += int(chunk[["I_Battery", "U_Battery"]].isna().sum().sum())
            backward += int((ts.diff().dt.total_seconds()<0).sum())
            if previous is not None and ts.iloc[0] < previous: backward += 1
            previous=ts.iloc[-1]
            lo, hi = ts.min(), ts.max()
            first=lo if first is None else min(first,lo);last=hi if last is None else max(last,hi)
            imin=min(imin,float(chunk.I_Battery.min()));imax=max(imax,float(chunk.I_Battery.max()))
        records.append({**identity(p), "rows": rows,"columns":header,"first":str(first),"last":str(last),"bad_timestamp":bad_time,"missing_current_or_pack_voltage":missing_iv,"backward_time_steps":backward,"current_min_A":imin,"current_max_A":imax,"scan_seconds":round(time.monotonic()-start,2)})
        print("TU accepted:",p.name,"rows",rows,"seconds",records[-1]["scan_seconds"],flush=True)
    assert len(records)==28
    pd.DataFrame([{k:v for k,v in r.items() if k!='columns'} for r in records]).to_csv(OUT / "tu_files.csv",index=False)
    return {"files":records,"rows":sum(r['rows'] for r in records),"bytes":sum(r['bytes'] for r in records),"capacity_label_column_found":False,"status":"field_diagnostics_only_SOC_is_not_SOH"}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--full',action='store_true');ap.add_argument('--refresh-phase1',action='store_true');args=ap.parse_args()
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'fixtures').mkdir(exist_ok=True)
    report_path=OUT/'audit_report.json'
    current_paths=sorted((ROOT/'dataset original').rglob('*.csv'))+sorted((ROOT/'TU Darmstadt').glob('*.csv'))+[ROOT/'Che-Dataset3.mat']
    quick=[identity(p,False) for p in current_paths]
    if args.refresh_phase1 and report_path.exists():
        old=json.loads(report_path.read_text())
        assert old.get('quick_manifest')==quick, 'Sources changed; run --full instead'
        started=time.monotonic()
        old['status']='RUNNING';report_path.write_text(json.dumps(old,indent=2,ensure_ascii=False))
        try:
            old['phase1']=phase1(); old['phase1_refresh_seconds']=round(time.monotonic()-started,2)
            old['phase1_refreshed_at']=pd.Timestamp.now(tz='UTC').isoformat()
            old['status']='PASSED_WITH_DOCUMENTED_SCIENTIFIC_LIMITS'
        except Exception as exc:
            old['status']='FAILED';old['error']=repr(exc);raise
        finally:
            report_path.write_text(json.dumps(old,indent=2,ensure_ascii=False))
        print('Phase1 temporal pairing refreshed; all 6 cells and 18 fixtures passed.');return
    if report_path.exists() and not args.full:
        old=json.loads(report_path.read_text())
        if old.get('quick_manifest')==quick and old.get('status')=='PASSED_WITH_DOCUMENTED_SCIENTIFIC_LIMITS':
            assert (OUT/'scoring_fixture.csv').exists()
            fixture=pd.read_csv(OUT/'scoring_fixture.csv')
            assert len(fixture)==18 and fixture.cell_id.nunique()==6
            assert (pd.to_datetime(fixture.input_end)<pd.to_datetime(fixture.label_discharge_start)).all()
            print('Full audit cache valid by path/size/mtime; use --full to rehash and rescan.');return
    start=time.monotonic()
    report={'checked_at':pd.Timestamp.now(tz='UTC').isoformat(),'quick_manifest':quick,'status':'RUNNING'}
    report_path.write_text(json.dumps(report,indent=2))
    try:
        report['phase1']=phase1();report['che']=che();report['tu']=tu()
        assert quick==[identity(p,False) for p in current_paths], 'Sources changed during scan'
        report['elapsed_seconds']=round(time.monotonic()-start,2)
        report['peak_rss_MiB_macos']=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20,1)
        report['status']='PASSED_WITH_DOCUMENTED_SCIENTIFIC_LIMITS'
    except Exception as e:
        report['status']='FAILED';report['error']=repr(e);raise
    finally:
        report_path.write_text(json.dumps(report,indent=2,ensure_ascii=False))
    print('DOWNLOAD AUDIT',report['status'],'seconds',report['elapsed_seconds'],'peak MiB',report['peak_rss_MiB_macos'],flush=True)


if __name__=='__main__':main()
