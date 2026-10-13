from common import *
labels={'F0':'F0 元数据','F0_F1_CCCV':'F0＋CC/CV','F0_F2_rest':'F0＋充后静置','F0_F3_dynamic':'F0＋放电形状','F0_F4_recovery':'F0＋放后恢复','F0_raw':'F0＋原始 V/I/T/P','joint':'联合特征','joint_no_full_charge':'联合去完整充电量','mask_only':'仅缺失掩码'}
keys=['main','pre300','pre900','pre1800','dis_end','post300','post900','forward','cross_temperature','all_fallback'];data={}
for k in keys:
 m=pd.read_csv(TASK/f'metrics_P1_{k}.csv');names=list(labels) if k=='all_fallback' else [c for c in labels if c!='mask_only'];m=m[m.family.isin(names)]
 e=pd.read_csv(TASK/f'entity_errors_P1_{k}.csv');e=e[e.family.isin(['F0','F0_F1_CCCV','joint'])]
 data[k]={'metrics':[{'family':r.family,'label':labels[r.family],'mae':round(r.MAE_Ah,3),'pp':round(r.SOH_MAE_pp,3),'rmse':round(r.RMSE_Ah,3),'worst':round(r.worst_entity_MAE_Ah,3),'events':int(r.events)} for r in m.itertuples()], 'entities':[{'family':r.family,'entity':r.entity.replace('102Ah_',''),'events':int(r.events),'mae':round(r.MAE_Ah,3),'late':round(r.late_MAE_Ah,3)} for r in e.itertuples()]}
facts=json.loads((TASK/'result_facts.json').read_text());prefix=[{'ck':r['checkup'],'date':r['date'],'events':r['available_events'],'rows':r['available_rows']} for r in facts['prefix']];a=pd.read_csv(TASK/'metrics_P1_registered_A.csv').set_index('family')
inline=json.dumps({'experiments':data,'prefix':prefix,'coverage':round(facts['coverage']['coverage']*100,1),'A':round(a.loc['joint','MAE_Ah'],3),'Aresidual':round(a.loc['joint_A_OOF_residual','MAE_Ah'],3),'NT':round(facts['legacy_NT']['MAE_Ah'],3),'checks':facts['checks_passed']},ensure_ascii=False)
source='''import {H1,H2,Text,Stat,Callout,Select,BarChart,Table,Button,useCanvasState,useCanvasAction,useHostTheme} from "cursor/canvas";
const DATA = __DATA__;
const OPTIONS = [{value:"main",label:"完整链／整芯留出"},{value:"pre300",label:"充后静置5分钟"},{value:"pre900",label:"充后静置15分钟"},{value:"pre1800",label:"充后静置30分钟"},{value:"dis_end",label:"放电结束（仅早期波形特征）"},{value:"post300",label:"放后静置5分钟"},{value:"post900",label:"放后静置15分钟"},{value:"forward",label:"严格时间前推"},{value:"cross_temperature",label:"跨温度留出"},{value:"all_fallback",label:"全部合法事件＋缺失回退"}];
export default function Result(){
 const theme=useHostTheme();const [budget,setBudget]=useCanvasState("route3-budget","main");const dispatch=useCanvasAction();
 const key=(budget in DATA.experiments?budget:"main") as keyof typeof DATA.experiments;const experiment=DATA.experiments[key];
 const metrics=experiment.metrics;const joint=metrics.find(r=>r.family==="joint");const metadata=metrics.find(r=>r.family==="F0");
 const entities=Array.from(new Set(experiment.entities.map(r=>r.entity))).map(entity=>{const rows=experiment.entities.filter(r=>r.entity===entity);return [entity,rows.find(r=>r.family==="joint")?.events??0,rows.find(r=>r.family==="F0")?.mae?.toFixed(3)??"未运行",rows.find(r=>r.family==="F0_F1_CCCV")?.mae?.toFixed(3)??"未运行",rows.find(r=>r.family==="joint")?.mae?.toFixed(3)??"未运行",rows.find(r=>r.family==="joint")?.late?.toFixed(3)??"未运行"];});
 return <div style={{maxWidth:1100,margin:"0 auto",padding:24,color:theme.text.primary}}>
  <Text style={{color:theme.text.tertiary}}>方案3 · 2026-10-13 · 探索性验证，六芯此前已曝光</Text>
  <H1>联合特征尚未通过容量主线接纳</H1>
  <Text>多阶段模型比元数据好，但未超过CC/CV单阶段。官方四串组容量仍未验证；没有新的CK1–CK7 SOH输出。</Text>
  <div style={{display:"flex",gap:40,flexWrap:"wrap",padding:"20px 0"}}>
   <Stat label="联合／六芯等权容量MAE" value="2.20 Ah"/><Stat label="最佳同预算单阶段MAE" value="1.28 Ah"/><Stat label="合法样本完整阶段覆盖" value={`${DATA.coverage}%`}/>
  </div>
  <Callout tone="warning" title="接纳结果：FAIL">联合模型对F0改善40.8%，但比CC/CV恶化72.0%；完整阶段覆盖81.4%未达到90%，跨温一芯恶化13.4%。源独立单芯CV约3.65V，与官方组端CV平均约3.50V及倍率、采样、标签协议不兼容，直接迁移接纳0条。拒绝全部事件不等于稳健性通过。</Callout>
  <section style={{paddingTop:24}}>
   <H2>切换可用时间，比较同一批事件</H2>
   <Select value={budget} onChange={setBudget} options={OPTIONS} style={{maxWidth:460}}/>
   <Text style={{paddingTop:10,color:theme.text.secondary}}>当前预算：{OPTIONS.find(r=>r.value===key)?.label}；{joint?.events}次事件。联合{joint?.mae.toFixed(3)} Ah，F0 {metadata?.mae.toFixed(3)} Ah。放后恢复在参考放电之后才可见，属于回顾诊断。</Text>
   <Text style={{color:theme.text.tertiary}}>横轴：输入特征组合；纵轴：逐物理芯平均后等权汇总的容量MAE（Ah）。数值越低越好。</Text>
   <BarChart categories={metrics.map(r=>r.label)} series={[{name:"容量MAE（Ah）",data:metrics.map(r=>r.mae),tone:"neutral"}]} height={310} valueSuffix=" Ah"/>
   <Text style={{color:theme.text.tertiary}}>来源：P1六颗102Ah LFP单芯的真实容量／固定首末及每25周期抽样；完整链575事件，全部合法配对706事件，前推176测试事件。归一SOH误差用102Ah，容量MAE用Ah。</Text>
  </section>
  <section style={{paddingTop:22}}><H2>逐芯误差与末期失败</H2>
   <Table headers={["物理单芯","事件数","F0 MAE（Ah）","CC/CV MAE（Ah）","联合MAE（Ah）","联合末20% MAE（Ah）"]} rows={entities} columnAlign={["left","right","right","right","right","right"]}/>
   <Text style={{color:theme.text.secondary}}>55°C及寿命末期有明显系统高估。只有六颗实体，不能把数百事件当数百独立电池。范围门只留下完整交集约33%的事件，不能用保留样本低误差掩盖拒绝率。</Text>
  </section>
  <section style={{paddingTop:22}}><H2>原A与最早N/T单列</H2>
   <Table headers={["对照","容量MAE（Ah）","解释"]} rows={[["联合＋原A严格20Ah窗口",DATA.A.toFixed(3),"几乎无增益；过去事件与当前分开"],["原A的OOF残差校正",DATA.Aresidual.toFixed(3),"恶化；不按负斜率人为缩放容量"],["原阶段一N/T主曲线",DATA.NT.toFixed(3),"五芯完整寿命训练，留出芯不使用初始容量锚；训练样本预算不同"]]}/>
  </section>
  <section style={{paddingTop:22}}><H2>官方CK前缀：特征可见，组容量未验证</H2>
   <Table headers={["检查点","查询日期","可见事件","预算特征行","容量结论"]} rows={DATA.prefix.map(r=>[r.ck,r.date,r.events,r.rows,"UNVERIFIED；不输出Qpack/SOH"])} columnAlign={["left","left","right","right","left"]}/>
   <Text style={{color:theme.text.secondary}}>CK0早于首次运行，没有配对特征；后续真实容量未公开。四通道属于同一物理组，不取四个单芯回归值的平均或最小冒充组容量。截至CK7为39标准＋36宽事件，之后4条不进入该前缀。</Text>
  </section>
  <section style={{paddingTop:22}}><H2>证据等级与未完成部分</H2>
   <Callout tone="info" title={`${DATA.checks}/${DATA.checks} 科学检查通过`}>统计定义、零电流掩码、整芯划分、容量标签与早期波形分离、原始前缀重算、物理周期与时间前推、正式文件保护均已检查。通过审计不等于通过容量接纳。</Callout>
   <Text style={{paddingTop:12}}>Gasper／Zhu原文及代码已审计；作者ZIP成员下载通过多个入口反复超时，因此公开论文容量基准未运行，不能声称复现1.1%等论文精度。固定库参数的玩具烟雾检查仅导出参数，不算容量实验。</Text>
   <Text style={{paddingTop:8}}>官方辅助任务是用过去事件预测下一事件30s电压变化：F0约1.97mV，阶段约1.98mV，四芯结构约2.59mV。它没有证明容量关系。下一步需要同充电控制、采样和C/20组截止协议的真实多组配对容量。</Text>
   <Button onClick={()=>dispatch({type:"openFile",path:"/Users/shane/Desktop/Arena 阶段 2 官方材料/research/phase2_multistage_features_20261012/FINAL_REPORT.md"})} style={{marginTop:14}}>打开完整中文验证报告</Button>
  </section>
 </div>;
}
'''.replace('__DATA__',inline)
(TASK/'canvas_source_pending.txt').write_text(source)
