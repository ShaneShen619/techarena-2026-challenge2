"""Record stage3-triggered application exit and reproduce contextual baseline tables."""
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parent
STUDY=HERE.parent
sys.path.insert(0,str(STUDY/'src'))
from audit5b import dump,bilingual
from common5b import H

if __name__=='__main__':
    decision=json.loads((STUDY/'stage_3/outputs/S3_exit.json').read_text())
    assert decision['stage4_proceed'] is False
    source=STUDY.parent/'phase2_round3_models_20261014/stage0/baseline_long.csv'
    baseline=pd.read_csv(source)
    baseline=baseline[(baseline['model'].isin(['M4','V2']))&(baseline.step=='main')&(baseline.a4s==2.)]
    (HERE/'outputs').mkdir(exist_ok=True)
    baseline.to_csv(HERE/'outputs/S4_baseline_reference_long.csv',index=False)
    H.metrics(baseline).to_csv(HERE/'outputs/S4_baseline_metrics.csv',index=False)
    H.per_ck(baseline).to_csv(HERE/'outputs/S4_baseline_errors.csv')
    d=baseline[(baseline.delta==.4)&(baseline.scenario!='real')&(baseline.k>=3)]
    pseudo=d.groupby(['model','scenario']).err_pp.apply(lambda e:float(e.abs().mean())).reset_index(name='MAE')
    pseudo.to_csv(HERE/'outputs/S4_baseline_pseudo_decision_scope.csv',index=False)
    dump(HERE/'outputs/S4_exit.json',{'stage':'skipped by registered stage3 exit','E1':'not evaluated',
        'E1_variants':'not evaluated','E3':'not produced','G_causal':'not run; no eligible candidate',
        'G_impl':'not run; no eligible candidate','baseline_source':str(source.relative_to(STUDY.parent)),
        'baseline_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'no_new_proxy_model_evaluated':True,'PC_CK2_used_for_decision':False})
    bilingual(HERE/'REPORT.md','Stage 4 — application skipped by exit rule',
      '''Exposed-exploratory; proxies are not hidden truth. Stage3's identifiability exit failed, so E1 and every beta variant are not evaluated, and E3 is not produced even though the stage2 main scalar CK0 gate passed. This follows the prompt's stage3 exit, which skips stage4, not stages5/6.

No model pseudo or real proxy result was computed, no candidate class was constructed, and no gate is claimed passed. A contextual M4/V2 table is copied from the already-reproduced round3 baseline artifacts; its source hash is recorded. Final reporting may show PC5/PC10 CK2, while the decision-scope context excludes CK2. This baseline reporting is not a model-selection experiment.''',
      '''已曝光探索性研究，代理不是隐藏真值。阶段3可辨识性退出门不通过，因此不评估 E1 及任何 β 变体，也不产生 E3；阶段2主 CK0 标量门通过并不能覆盖阶段3退出规则。按 prompt 跳过阶段4，不跳过5/6。

没有计算任何新模型的伪情景或实际代理结果，不构建候选类，不声称任何模型门通过。M4/V2 对照从已复现的第三轮基线产物复制，记录来源哈希；最终报告可包含 PC5/PC10 的 CK2，决策范围对照排除 CK2。该对照不是模型选择实验。''')
