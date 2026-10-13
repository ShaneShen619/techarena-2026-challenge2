"""Record code/data provenance and diagnose small-pool OOF B instability."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
import pandas as pd
TASK=Path(__file__).resolve().parents[1];PREV=TASK.parent/"phase1_transfer_ab";ROOT=TASK.parents[1]
sys.path[:0]=[str(PREV/"src"),str(PREV/"scripts")]
from reproduce_source import load_records
from source_model import predict

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def main():
    panel=pd.read_csv(PREV/"outputs/panel_scoring.csv");records={r["cell_id"]:r for r in load_records()}
    stamp=hashlib.sha256(b"".join((PREV/"src"/n).read_bytes() for n in ["source_model.py","exposure.py","baselines.py"])).hexdigest()[:12]
    rows=[]; seen=set()
    for a in json.loads((TASK/"outputs/nested_audit.json").read_text()):
        ids=a["B_fit_and_selection_cells"];held=a["label_entity"];name=a["config"];xi0=a["xi0"]
        key=(tuple(ids),held,name,xi0)
        if key in seen:continue
        seen.add(key)
        path=PREV/"artifacts/model_cache"/f"{stamp}_{name}_{'__'.join(x.replace('102Ah_','') for x in sorted(ids))}.json"
        if not path.exists():path=TASK/"artifacts"/path.name
        m=json.loads(path.read_text());r=records[held];anchor=float(panel.loc[panel.cell_id.eq(held),"anchor_soh_pp"].iloc[0])
        pred=predict(m,r["target_hist"],anchor,xi0,nominal_T=r["nominal_T"])
        rows.append(dict(label_entity=held,training_cells="|".join(ids),ntrain=len(ids),config=name,xi0=xi0,
                         min_prior_pp=float(pred.min()),max_prior_pp=float(pred.max()),outside_50_110_count=int(((pred<50)|(pred>110)|~np.isfinite(pred)).sum())))
    pd.DataFrame(rows).to_csv(TASK/"outputs/inner_prior_diagnostics.csv",index=False)
    inputs=[PREV/"outputs/panel_scoring.csv",PREV/"outputs/history_features.csv",PREV/"artifacts/shallow_observations.csv",
            PREV/"artifacts/shallow_visibility.csv",PREV/"artifacts/source_prior.json",*sorted((PREV/"artifacts").glob("data_*.npz")),
            ROOT/"data/checkups/CK0_reference_discharge.csv.gz",ROOT/"data/checkups/checkup_capacities_released.csv",
            ROOT/"data/checkups/evaluation_points.csv",*sorted((ROOT/"data/operation").glob("segment_*.csv*"))]
    files=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in inputs if p.exists()]
    code=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for d in ["src","scripts","tests"] for p in sorted((TASK/d).glob("*.py"))]
    result=dict(branch="exp/pack-trend-feedback-20261011",inputs=files,code=code,protocol_sha256=sha(TASK/"protocol.md"),
                event_addendum_sha256=sha(TASK/"event_axis_addendum.md"),prior_source_code_stamp=stamp,
                raw_stage1_provenance_audit="research/phase1_transfer_ab/outputs/source_registry.json",
                source_model_cache_reuse="training-entity sets asserted; previous directory read only",
                unphysical_selected_OOF_priors=sum(r["outside_50_110_count"]>0 for r in rows),selected_OOF_prior_sets=len(rows))
    (TASK/"outputs/provenance.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k not in ("inputs","code")}),flush=True)

if __name__=="__main__":main()
