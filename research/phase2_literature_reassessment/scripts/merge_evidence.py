"""Normalize A/B/source-verified C/D claims and contradictions into deliverable tables."""
import csv
from pathlib import Path

TASK=Path(__file__).resolve().parents[1]
WS=TASK/'notes/workstreams'
OUT=TASK/'outputs'
claims=[]
for r in csv.DictReader((WS/'A_partial_temperature/claim_evidence.csv').open(encoding='utf-8')):
 claims.append(dict(claim_id=r['claim_id'],claim_cn=r['claim_zh'],paper_id=r['paper_id'],source_version=r['source_version'],locator=r['original_location'],evidence_type=r['evidence_type'],relation=r['direction'],conditions_or_limit=r['applicability_and_limit'],local_experiment='',review_status='agent_source_reviewed;independent_audit_sampled'))
for r in csv.DictReader((WS/'B_claim_evidence.csv').open(encoding='utf-8')):
 pid = r['paper_id']
 pid = ("B_card_" + pid) if pid not in {"LocalR3", "OfficialCK0"} else ({"LocalR3":"B_R3_cluster_audit","OfficialCK0":"OFFICIAL_CONSTRAINTS"}[pid])
 claims.append(dict(claim_id=r['claim_id'],claim_cn=r['claim_cn'],paper_id=pid,source_version=r['source_version'],locator=r['locator'],evidence_type=r['evidence_type'],relation=r['relation'],conditions_or_limit=r['conditions_or_limit'],local_experiment=r['local_link'],review_status=r['review_status']))
extra=[
('D01','LFP容量 CRLB 依赖 OCV 斜率和SOC覆盖','Lin2015_Fisher_identifiability','published PDF','A1882–A1883 Eq 11 14 15 Table I','formula_and_visual','support','已知其他参数、独立高斯10mV假设；7.35%只是该实例理论下界','L6_window_table_20260929'),
('D02','容量 knee 曲率算法需要已测容量轨迹','Zhang2024_knee_curvature','published PDF','p4–5 §3 Eq 2; p9 Table 5','method_and_visual','limit','169只LFP实验单芯和完整容量轨迹；不能用于官方隐藏CK直接识别','none'),
('D03','大型LFP 50°C老化比35°C损失更快','Yagci2025_large_LFP_aging','published PDF','printed p14 Table 3 Fig 12','table_and_visual','support','12只180Ah；每条件2只；20°C参考容量；非官方四串','L6_window_table_20260929'),
('D04','大型LFP容量下降不必同步有清楚IR上升','Yagci2025_large_LFP_aging','published PDF','printed p13 Fig 11 and §6','figure_and_visual','limit','仅作者条件；50°C循环末期例外；不证明所有脉冲无容量信息','B_R3_cluster_audit'),
('D05','Yagci同一循环工况倍率在正文与表4冲突','Yagci2025_large_LFP_aging','published PDF','p3 Table 2 vs printed p14 Table 4','source_internal_conflict','limit','50A/180Ah=0.28C，但表4称1C；不做精确倍率跨文献比较','none'),
('D06','Zhu弛豫跨材料误差需要目标带标签微调','Zhu2022','publisher version of record','p8 Table 3; Methods relaxation and transfer','table_and_method_visual','limit','NCA/NCM 18650、标准化满充30/60min静置；19/30目标带标签单位；非一锚LFP组','none'),
('D07','Zhou动态ICA新版含233枚LFP有标签迁移','Zhou2026_dynamic_ICA','arXiv v3 / IEEE accepted manuscript','p10 Tables IV/V; transfer section','table_and_method_visual','support_and_limit','0.23% RMSE在带SOH标签微调和随机裁剪窗口下；物理实体隔离未明确；非真实浅充4S','none'),
('D08','Cheng估退化模式而非容量SOH误差','Cheng2024','arXiv preprint','p19 Table 3; Method labels','table_and_method_visual','limit','16枚NMC811/SiOx；LLI/LAM插值标签；约10%为模式MAPE量级，LAMne CF-FNN逊于SVR','none'),
('D09','BatteryGPT早期结果使用完整寿命训练轨迹和逐周期SOH标签','BatteryGPT2025','2025 online/2026 volume publisher version','p7 Table 1; training and split description','table_and_method_visual','limit','MIT 42/46 LFP训练完整寿命；4留出兼称验证/测试；0.21% RMSE非单CK0四串结果','none'),
('D10','车端LFP慢充可保留部分DVA特征但ICA受平台噪声限制','Bilfinger2024','eTransportation version of record','§3–5 Fig 4/7/8','fulltext_figure_visual','support_and_limit','仅一辆106s1p LFP Tesla、近全程20C低功率充电，SOH为能量；非4S容量','none'),
('D11','域适配车队短窗仅有10个独立NCM车级容量标签','F_Deng2024_RapidPackDA','author fulltext and original MAT','§2–3 Table 2/3; AUDIT_DENG_MAT.json','fulltext_data_crosscheck','limit','8车训练2车测试多次复用，完整充电Ah标签；第5车分母在文/README和MAT冲突','none'),
('C01','BattGP目标是运行点修正电阻和故障概率，不是容量','C_Schaeffer2024_BattGP','published paper;Zenodo README','Methods and Table 1','paper_code_data_crosscheck','limit','28返修8S组；正式224芯；README误写232；无周期C/20容量','R3'),
('C02','Che迁移更新使用目标芯早期容量标签','C_Che2023_Continual','published paper','Fig 1 3 5 and Methods','method','limit','至少3个目标早期容量点或持续稀疏标签，强于官方单CK0','D1'),
('C03','SSL已有车级划分但有容量监督及潜在寿命代理','C_Arunan2025_SSL','published paper','Appendix Table A1; Tables II–V','method_code_static','limit','需独立消融里程/SOC/片长/年龄/未来目标数据','D1'),
('C04','Silva区间结果只来自模拟且目标早期有标签','C_Silva2026_Conformal','arxiv preprint','§3.2.2; Table 3; Fig 5','paper_method','limit','目标至20kAh有标签；98.8%经验覆盖非真实四串覆盖保证','none'),
('C05','部分放电PINN使用完整放电后验裁片和生成指示标签','C_Ispizua2026_PINN','arxiv preprint','§2; Results p12–14 Table 4','paper_method','limit','共享MIT单芯快充集；Kneedle指示量非官方C/20组容量','none'),
('C06','Wen物理损失不补足四串容量信息','C_Wen2023_PINN','author preprint','Eq 1 11 14; Section V–VI','method','limit','训练需完整周期容量/放电曲线；PCL分数与百分数须转换','none'),
('C07','Yagci公开包v1.1是后发版本且协议尚未核','Yagci2025_large_LFP_aging','paper;Zenodo v1.1','Data availability; Zenodo README Related works','data_version','limit','v1.1 CC BY4.0, 2.5GB未下；单芯50A RPT，与官方不同','none'),
('L001','CK0曲线电压小窗受假设mV阈值移动影响','OFFICIAL_CONSTRAINTS','official CK0 CSV','runs/L6_window_table_20260929/result.json','local_recalculation','support','26个10mV组端窗，假设±2mV相对局部Ah偏移中位10.28%；非容量性能','L6_window_table_20260929'),
('L002','R3组脉冲而非逐芯事件是重复采样簇','B_R3_cluster_audit','local prior predictions','notes/workstreams/B_R3_cluster_audit.json','local_recalculation','limit','37次组脉冲×4芯；电压优势不等于容量','R3'),
]
for id_,claim,paper,version,locator,etype,rel,limit,local in extra:
 claims.append(dict(claim_id=id_,claim_cn=claim,paper_id=paper,source_version=version,locator=locator,evidence_type=etype,relation=rel,conditions_or_limit=limit,local_experiment=local,review_status='root_checked;independent_audit_where_marked'))
with (OUT/'claim_evidence.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=list(claims[0]));w.writeheader();w.writerows(claims)

contr=list(csv.DictReader((WS/'A_partial_temperature/contradictions.csv').open(encoding='utf-8')))
more=[
('V1','BattGP物理芯数量','B_card_Schaeffer2024','C_Schaeffer2024_BattGP','正式PDF 28×8=224；Zenodo README写28系统/232芯；过时arXiv29/232','用正式表1 28/224，README数量未由原始CSV全量核裁','读取全量Zenodo列/唯一设备ID；仅必要时下载1.7GB'),
('V2','Yagci循环倍率','Yagci2025_large_LFP_aging','Yagci2025_large_LFP_aging','§2/表2 50A/180Ah=0.28C，§5/表4称1C','视为原文内部错误/未解释差异；不做倍率精确比较','作者澄清或逐原始cycling记录核电流'),
('V3','Richardson2019容量标签积分方向','C_Richardson2019_GPTransition','C_Richardson2019_GPTransition','原文p6相邻句称2A参考放电曲线与2A充电积分','来源内部歧义，容量是已测参考曲线但方向待核','NASA原始readme和例文件重算一个RPT'),
('V4','Gasper表I实体与测试总数','B_card_Gasper2025','B_card_Gasper2025','表I四行相加75实体/255测试，Totals列79/259；脉冲和47906一致','实体数不取无说明的总计；不以测试次数做独立数','联系不到作者时按逐行条件报告并核补充材料'),
('V5','温度消融平均改善但尾部恶化','A_Ruiz2018;Yagci2025_large_LFP_aging','research/phase2_next_round R1','D1严格无显式温度宏2.479pp低于全信号2.851pp，但最差6.147pp高于5.572pp','平均与尾部非同一选择目标，且时间/热历史代理仍在；不选外层赢家','内层封存物理芯，固定前缀同预算对比温度三层处理'),
('V6','Zhou动态ICA旧版无LFP与新版有LFP','Zhou2026_dynamic_ICA','research/phase2_literature old notes','arXiv v3/accepted manuscript新增233枚LFP带标签迁移，旧笔记称无LFP','修正书目/数据事实；0.23%不升级为官方容量证据','真实浅充、目标一锚、组级封存重验'),
('V7','Bilfinger图8单位和正文误差表述','Bilfinger2024','Bilfinger2024','图8约58.9对59.4kWh差0.5kWh；正文称0.5%，按58kWh约0.86 SOH pp','保留单位冲突，不引用0.5%为方法精度','原始车端数据与作者解释进一步核对'),
('V8','Deng车5容量分母及公开字段','F_Deng2024_RapidPackDA','F_Deng2024_RapidPackDA','论文/README 174Ah 82.21%，MAT 147Ah 97.30765%，Q同为143.04225Ah；README字段多于MAT','原因未获作者证实；两套预注册敏感性或排除，不能作独立D2','逐车审计原始MAT与论文标签；不改原数据'),
]
for x in more: contr.append(dict(zip(contr[0].keys(),x)))
with (OUT/'contradictions.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=list(contr[0]));w.writeheader();w.writerows(contr)
print(len(claims),'claims',len(contr),'contradictions')
