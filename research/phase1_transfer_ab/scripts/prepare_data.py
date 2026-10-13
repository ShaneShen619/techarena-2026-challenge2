"""Rebuild all P1 charge exposure and verify every inherited shallow fragment."""
from __future__ import annotations
import hashlib,json,re,sys,time
from pathlib import Path
import numpy as np
import pandas as pd

TASK=Path(__file__).resolve().parents[1]; ROOT=TASK.parents[1]
sys.path.insert(0,str(TASK/"src"))
from legacy_data import _derive_soh
from exposure import intervals,histograms_at
from event_core import Event,partial_ah


def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()


def main():
    started=time.monotonic()
    old=json.loads((ROOT/"research/phase2_temperature_improvement/runs/M7_frozen_manifest.json").read_text())
    hashes=[]
    for entry in old["raw_p1_files"]:
        path=ROOT/entry["path"]; actual=sha(path)
        if actual!=entry["sha256"]: raise RuntimeError(f"raw source changed: {path}")
        hashes.append({"path":entry["path"],"sha256":actual,"bytes":path.stat().st_size})
    crop_path=ROOT/"research/phase2_method_exploration/data_manifests/d1_v15_cropped_events.csv"
    view_path=ROOT/"research/phase2_method_exploration/data_manifests/d1_v15_target_visibility.csv"
    inherited=json.loads((ROOT/"research/phase2_method_exploration/runs/M9_D1_v15_inputs_v1/summary.json").read_text())
    assert sha(crop_path)==inherited["crop_sha256"]
    assert sha(view_path)==inherited["visibility_sha256"]
    crop=pd.read_csv(crop_path); views=pd.read_csv(view_path)
    panel=pd.read_csv(TASK/"outputs/panel_scoring.csv")
    inventory=pd.read_csv(ROOT/"research/phase2_validation/preflight/downloaded_data/phase1_label_inventory.csv")
    config=json.loads((TASK/"configs/experiment.json").read_text())
    audited=[]; summaries=[]; datasets=[]; feat=[]
    for cell in sorted(panel.cell_id.unique()):
        start=time.monotonic(); match=re.fullmatch(r"102Ah_(\d+)degC_(0p5C|1C)_cell\d+",cell)
        nominal_T=float(match[1]); nominal_C=.5 if match[2]=="0p5C" else 1.
        paths=sorted((ROOT/"dataset original"/cell).glob("*.csv"))
        cols=["absolute_time","cycle_number","step_type","voltage_V","current_A","temperature_C","step_capacity_Ah"]
        raw=pd.concat([pd.read_csv(p,usecols=cols,parse_dates=["absolute_time"]) for p in paths],ignore_index=True)
        labels=_derive_soh(raw)
        observed_q=raw.loc[raw.step_type.eq("cc_discharge")].groupby("cycle_number").step_capacity_Ah.max()
        inv=inventory.loc[inventory.cell_id.eq(cell)].set_index("cycle")
        assert np.allclose(observed_q.reindex(inv.index).to_numpy(),inv.capacity_Ah.to_numpy(),equal_nan=True)
        lab=labels.sort_values("cycle_number")
        starts=raw.loc[raw.step_type.eq("cc_discharge")].groupby("cycle_number").absolute_time.min()
        stamps=lab.cycle_number.map(starts)
        mean_T=float(raw.temperature_C.mean());temp_coverage=float(raw.temperature_C.notna().mean())
        charging=raw.loc[raw.step_type.ne("cc_discharge")].drop(columns="step_capacity_Ah")
        ledger,diag=intervals(charging,time_col="absolute_time",segment_col="cycle_number",temp_col="temperature_C",fallback_temperature=nominal_T)
        hist=histograms_at(ledger,stamps)
        targets=panel.loc[panel.cell_id.eq(cell)].sort_values("target_ordinal")
        target_hist=histograms_at(ledger,targets.target_discharge_start)
        anchor_hist=histograms_at(ledger,[targets.anchor_discharge_start.iloc[0]])[0]
        delta=np.maximum(target_hist-anchor_hist,0.)
        np.savez_compressed(TASK/"artifacts"/f"data_{cell}.npz",cycles=lab.cycle_number.to_numpy(),soh=lab.soh_percent.to_numpy(),hist=hist,
                            label_time_ns=pd.to_datetime(stamps).astype("int64").to_numpy(),target_hist=delta,
                            target_ordinal=targets.target_ordinal.to_numpy(),anchor_hist=anchor_hist)
        meta={"cell_id":cell,"nominal_T":nominal_T,"nominal_C":nominal_C,"raw_mean_T":mean_T,"raw_temp_coverage":temp_coverage}
        datasets.append(meta); summaries.append({**meta,**diag,"valid_labels":int(lab.soh_percent.notna().sum()),"cycles_max":int(lab.cycle_number.max())})
        for i,row in enumerate(targets.itertuples(index=False)):
            feat.append({"cell_id":cell,"target_ordinal":int(row.target_ordinal),"age_days":(pd.Timestamp(row.target_discharge_start)-pd.Timestamp(row.anchor_discharge_start)).total_seconds()/86400.,
                         "charge_EFC":float(delta[i].sum()),"input_end":pd.Timestamp(ledger.loc[ledger.end_ns<pd.Timestamp(row.target_discharge_start).value,"end_ns"].max()).isoformat(),
                         "temperature_mean_charge_C":float(delta[i]@np.repeat(np.arange(81),8)/max(delta[i].sum(),1e-12)),"nominal_T":nominal_T,"nominal_C":nominal_C})
        # Independent raw verification uses only the listed shallow interval,
        # plus pre-endpoint rows for eligibility. It never reads full-event end.
        groups={int(c):g.sort_values("absolute_time",kind="stable") for c,g in charging.groupby("cycle_number")}
        subset=crop.loc[crop.cell_id.eq(cell)]
        for row in subset.itertuples(index=False):
            cycle=int(row.event_id.split("|")[1]); source=groups[cycle]
            begin=pd.Timestamp(row.fragment_start);end=pd.Timestamp(row.fragment_end)
            f=source.loc[source.absolute_time.between(begin,end)&source.current_A.ge(5)].sort_values("absolute_time")
            times=f.absolute_time.astype("int64").to_numpy()/1e9
            q=np.cumsum(np.r_[0.,np.diff(times)*f.current_A.to_numpy(float)[1:]/3600.])
            assert len(f)==row.n_samples and np.isclose(q[-1],row.observed_span_Ah,atol=1e-8)
            assert np.isclose(f.temperature_C.median(),row.temperature_C,equal_nan=True)
            assert np.isclose(f.current_A.median(),row.current_A)
            ev=Event(begin,end,cycle,float(row.current_A),float(row.temperature_C),times[-1]-times[0],q[-1],times,q,f.voltage_V.to_numpy()[:,None],None,("voltage_V",))
            errors=[]
            for j,(lo,hi) in enumerate(config["a_windows_V"]):
                actual=partial_ah(ev,0,lo,hi); expected=getattr(row,f"w{j:02d}_Ah")
                assert (actual is None and pd.isna(expected)) or (actual is not None and np.isclose(actual,expected,atol=1e-8)),(row.event_id,j,actual,expected)
                if actual is not None:errors.append(abs(actual-expected))
            assert f.voltage_V.iloc[-1]>=3.5 and f.voltage_V.iloc[-2]<3.5
            prefix=source.loc[(source.absolute_time>=pd.Timestamp(row.event_id.split("|")[2]))&(source.absolute_time<=end)&source.current_A.ge(5)]
            px=prefix.voltage_V.to_numpy()
            assert not (px[:-1]>=3.5).any()
            audited.append({"cell_id":cell,"event_id":row.event_id,"budget_Ah":int(row.budget_Ah),"verified_raw_samples":len(f),"max_window_difference_Ah":max(errors,default=0.),"source_max_time":f.absolute_time.max().isoformat(),"reads_post_endpoint":False})
        print(cell,"rows",len(raw),"charge_EFC",round(diag["charge_EFC"],2),"crop_verified",len(subset),"seconds",round(time.monotonic()-start,1),flush=True)
        del raw,charging,groups,ledger,hist
    (TASK/"artifacts/data_metadata.json").write_text(json.dumps(datasets,indent=2)+"\n")
    pd.DataFrame(summaries).to_csv(TASK/"outputs/exposure_summary_p1.csv",index=False)
    pd.DataFrame(feat).to_csv(TASK/"outputs/history_features.csv",index=False)
    pd.DataFrame(audited).to_csv(TASK/"outputs/shallow_raw_replay.csv",index=False)
    crop.to_csv(TASK/"artifacts/shallow_observations.csv",index=False)
    views.to_csv(TASK/"artifacts/shallow_visibility.csv",index=False)
    meta={"raw_sources":hashes,"raw_hashes_match_prior_audit":True,"shallow_crop_sha256":sha(crop_path),"shallow_view_sha256":sha(view_path),
          "raw_shallow_rows_verified":len(audited),"all_180_target_dates":True,"all_1080_v15_views_registered":len(views)==1080,
          "source_identity":"102Ah LFP; manufacturer/model/batch/physical continuity unconfirmed","elapsed_s":time.monotonic()-started}
    (TASK/"outputs/source_registry.json").write_text(json.dumps(meta,indent=2)+"\n")
    print('E0/E2 raw input preparation complete',round(time.monotonic()-started,1),flush=True)

if __name__=="__main__":main()
