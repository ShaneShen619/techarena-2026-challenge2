"""Recompute baselines and assert the registered V2 reproduction gate."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from common import STUDY, status, dump, bilingual
from harness import evaluate, BASELINES, save_eval

if __name__ == '__main__':
    pred=evaluate(BASELINES)
    met=save_eval('0',pred)
    r=met[(met.model=='V2') & (met.scenario=='normal') & (met.step=='main') & (met.smooth==2.) & (met.delta==.4)].iloc[0]
    passed=round(r.MAE,3)==.216 and round(r.MAX,3)==.669
    dump(STUDY/'stage_0/outputs/reproduction.json', {'passed':passed,'MAE':r.MAE,'MAX':r.MAX})
    print(r.to_dict(),flush=True)
    assert passed, 'STOP: V2 reproduction failed'
    bilingual(STUDY/'stage_0/REPORT.md','Harness', f'Exposed-exploratory. V2 reproduced: MAE {r.MAE:.6f} pp, MAX {r.MAX:.6f} pp. All causal-prefix caches and PG1/PG2/PC5/PC10 baseline evaluations are available. Proxies are not hidden truth.',f'已曝光探索性结果。V2 复现：MAE {r.MAE:.6f} pp，MAX {r.MAX:.6f} pp。因果前缀及伪情景基线已建立。代理不是隐藏真值。')
    status('0 complete','Harness and baseline pseudo scenarios reproduced','Stage B coverage audit')
