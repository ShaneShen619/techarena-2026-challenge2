"""Independent bookkeeping and validity helpers for the resumed R5B study."""
import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np

STUDY=Path(__file__).resolve().parents[1]
WORKTREE=STUDY.parents[1]

def dump(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False,default=str,allow_nan=False)+'\n')

def clean_json(obj):
    if isinstance(obj,dict):return {str(k):clean_json(v) for k,v in obj.items()}
    if isinstance(obj,(list,tuple,np.ndarray)):return [clean_json(v) for v in obj]
    if isinstance(obj,(float,np.floating)):return float(obj) if np.isfinite(obj) else None
    if isinstance(obj,np.integer):return int(obj)
    if isinstance(obj,np.bool_):return bool(obj)
    return obj

def bilingual(path,title,en,zh):
    Path(path).write_text(f'<a id="en"></a>\n\n# {title}\n\n> English · [中文](#zh)\n\n{en}\n\n---\n\n<a id="zh"></a>\n\n# {title}\n\n> [English](#en) · 中文\n\n{zh}\n')

def protocol(stage,obj):
    path=STUDY/f'stage_{stage}/protocol.json'
    if path.exists():raise RuntimeError(f'Preserve existing protocol: {path}')
    dump(path,obj)
    path.with_suffix('.sha256').write_text(hashlib.sha256(path.read_bytes()).hexdigest()+'  protocol.json\n')

def update_status(current,states,next_step):
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=WORKTREE,text=True).strip()
    timestamp=datetime.now(ZoneInfo('Europe/Berlin')).isoformat()
    en=f'Updated {timestamp}. Current: {current}.\n\n'+ '\n\n'.join(f'Stage {k}: {v[0]}' for k,v in states.items())
    zh=f'更新时间 {timestamp}。当前：{current}。\n\n'+ '\n\n'.join(f'阶段 {k}：{v[1]}' for k,v in states.items())
    bilingual(STUDY/'notes/STATUS.md','Execution status',en+f'\n\nNext: {next_step[0]}\n\nLast observed commit: `{head}`. Preserve completed stages.',zh+f'\n\n下一步：{next_step[1]}\n\n最近观察提交：`{head}`。保留完成阶段。')

def neff(residual):
    """Initial-positive autocorrelation sum, using the full residual sequence."""
    from scipy.signal import fftconvolve
    r=np.asarray(residual,float);n=len(r);r=r-r.mean()
    if n<3 or not np.any(r):return float(n),np.array([1.])
    covariance=fftconvolve(r,r[::-1],mode='full')[n-1:]/np.arange(n,0,-1)
    rho=covariance/covariance[0]
    cutoff=np.flatnonzero(rho[1:]<=0)
    stop=int(cutoff[0])+1 if len(cutoff) else n-1
    total=float(rho[1:stop+1].clip(min=0).sum())
    return float(np.clip(n/(1+2*total),1,n)),rho

def physical_charge(x,q_end,ocp):
    tn,tp=ocp.thetas(np.array([0.,q_end]),tuple(x[:4]))
    return bool(np.isfinite(np.r_[tn,tp]).all() and np.all((tn>=0)&(tn<=1)&(tp>=0)&(tp<=1)))
