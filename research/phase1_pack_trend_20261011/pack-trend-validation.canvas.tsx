import {Stack,Row,Grid,H1,H2,Text,Table,BarChart,Button,Callout,Divider,useCanvasState,useHostTheme,useCanvasAction} from "cursor/canvas";

const root="/Users/shane/Desktop/Arena 阶段 2 官方材料/research/phase1_pack_trend_20261011";
const methods=["原 B","前向·元数据","前向·A 趋势","前向·置乱 A","历史损伤·A"];
const values={days:[3.0842377906,3.2720295727,3.2704797678,3.265923415,3.7183327958],events:[3.0842377906,3.2720295727,3.2780731939,3.2701264419,3.6960409467]};
const literature=[
 ["未来速率倍率","A 的斜率校准到 m，乘到下一段 B 损失","已试；两种趋势轴均失败","Richardson 2019"],
 ["慢速率状态","新事件缓慢更新 log(m)，限制在 0.5–2","已试固定增益；完整 GP 尚未做","Aitio；Zhou 2025"],
 ["历史损伤调整","用历史平均倍率缩放累计损失","已试；未通过","有效损伤/时间伸缩思想"],
 ["共同趋势＋电芯收缩","默认共享老化，证据充分再允许逐芯偏离","已建四曲线；差异只做敏感性","Krupp；综述 R07"],
 ["单参数 MHE/双滤波","分离容量、SOC、内阻和偏置","完成敏感性；未做正式辨识","Lin 2015；R02"],
 ["指数/膝点或门控","先验证局部趋势是否对应容量指数","当前仅建议监控，不直接改 p","综述 R03/R09"]
];

export default function PackTrendValidation(){
 const theme=useHostTheme();const dispatch=useCanvasAction();
 const [axis,setAxis]=useCanvasState<"days"|"events">("pack-trend-axis-v1","days");
 return <Stack gap={20} style={{padding:24,maxWidth:1160,margin:"0 auto",color:theme.text.primary}}>
  <Text size="small" tone="tertiary">2026-10-11 · exp/pack-trend-feedback-20261011</Text>
  <H1>四串组模型已跑通，A 趋势数值反馈尚未通过</H1>
  <Callout tone="neutral" title="当前决策">保留四条电芯曲线的组端截止投影。A 改成了衰减速度观测，但现有验证未优于 B；正式模型没有替换，官方数值反馈增益为 0。</Callout>
  <Row gap={10} wrap>
   <Button onClick={()=>dispatch({type:"openFile",path:root+"/outputs/四串电池组与A趋势反馈_验证报告.md"})}>打开完整中文报告</Button>
   <Button variant="ghost" onClick={()=>dispatch({type:"openFile",path:"/Users/shane/Desktop/Arena 阶段 2 官方材料/research/phase2_literature_reassessment/outputs/LFP_SOH_第二阶段文献综述与技术路线_深度重评.md"})}>打开原文献综述</Button>
  </Row>
  <Grid columns="repeat(auto-fit,minmax(280px,1fr))" gap={28}>
   <Stack gap={10}>
    <H2>四串组容量怎样算</H2>
    <Text>B 给出老化伸缩 → 四条 CK0 带载曲线分别形变 → 四芯电压加测量链残差 → 找首次 11.2 V → 放出 Ah。</Text>
    <Text weight="semibold">四串的 Ah 不乘以 4。组端截止也不恒等于最小单芯容量。</Text>
    <Text tone="secondary">共同衰减时，结果与原 B 相同。新增结构可以计算不一致、SOC 缺口和内阻的影响；目前尚未从运行片段识别四芯独立容量。</Text>
   </Stack>
   <Stack gap={10}>
    <H2>A 的新角色</H2>
    <Text>局部充电窗口量的有符号对数斜率 → 源电芯校准速率倍率 m → 慢更新 → 仅改变下一段 B 损失。</Text>
    <Text weight="semibold">Q 下一时点 = Q 当前 − m × B 预计损失。</Text>
    <Text tone="secondary">不把窗口斜率直接称为容量指数。官方后期只有 cell1、cell3 有合格趋势；cell2、cell4 缺窗不等于健康。</Text>
   </Stack>
  </Grid>
  <Divider/>
  <Row justify="space-between" wrap>
   <H2>六芯平均绝对 SOH 误差</H2>
   <Row gap={8}>
    <Button variant={axis==="days"?"primary":"secondary"} onClick={()=>setAxis("days")}>主实验：每天趋势</Button>
    <Button variant={axis==="events"?"primary":"secondary"} onClick={()=>setAxis("events")}>探索：每合格事件</Button>
   </Row>
  </Row>
  <Text tone="secondary" size="small">纵轴：各电芯 MAE 的等权平均（SOH 百分点，越低越好）。横轴：方法。来源：本轮 rate_metrics.csv · 6 个已开发电芯各 30 个固定日期 · 20 Ah 输入 · 六折实体外层。</Text>
  <BarChart categories={methods} series={[{name:"平均绝对误差（pp）",data:values[axis],tone:"neutral"}]} height={245} valueSuffix=" pp" showValues referenceLines={[{value:3.0842377906,label:"原 B",tone:"neutral"}]}/>
  <Text weight="semibold">{axis==="days"?"前向 A 为 3.2705 pp，比原 B 的 3.0842 pp 更差；较元数据只改善 0.00155 pp。":"事件轴前向 A 为 3.2781 pp，同样比 B 更差。它是主实验之后登记的探索，不能当独立验证。"}</Text>
  <Callout tone="neutral">180 个评分点来自 6 个物理电芯，不能当成 180 个独立电池。更内层 90 组 B 先验中有 7 组出现非物理外推，影响倍率校准；失败不能直接证明趋势反馈思想无效。</Callout>
  <H2>从原综述筛出的六种方法</H2>
  <Table headers={["方法","A 与 B 如何连接","本轮状态","依据"]} rows={literature} framed={false}/>
  <H2>四串假设敏感性</H2>
  <Text size="small" tone="secondary">来源：本轮 pack_sensitivity.csv。共同伸缩 0.97、5.1 A、首次组端 11.2 V；这些是指定参数场景，不是置信区间。</Text>
  <Table headers={["场景","组容量（Ah）","相对共同衰减（Ah）"]} rows={[
   ["四芯共同衰减","97.3977","0"],
   ["单枚伸缩额外下降 1 个百分点","97.1328","−0.2649"],
   ["单枚初始缺少 1 Ah 电量","97.1455","−0.2522"],
   ["四枚各新增 3 mΩ 内阻","97.2993","−0.0984"],
   ["一枚 0.70，其余 0.97","拒绝输出","超出有限模板域"]
  ]} columnAlign={["left","right","right"]}/>
  <Grid columns="repeat(auto-fit,minmax(280px,1fr))" gap={28}>
   <Stack gap={8}><H2>已经验证到哪里</H2><Text>14 个科学/因果单元检查、8 个包级检查通过；CK0 100.41 Ah 回代，逐点组电压和首次交点检查通过。</Text><Text tone="secondary">独立合成四串机制检查用给定真实参数验证投影，不证明参数可从浅充识别。</Text></Stack>
   <Stack gap={8}><H2>还缺什么</H2><Text>先修 B 的小样本外推，再用直接观测电量和匹配状态重建 A，随后获取同协议的独立四串容量复测。</Text><Text tone="secondary">官方 CK1–CK7 标签隐藏，CK7 的 97.2477 Ah 只是预测；任意事件级部署等价性、MHE/GP、逐芯参数识别均未验证。</Text></Stack>
  </Grid>
  <Text size="small" tone="tertiary">完整数据、预登记、选择记录、失败折和 SHA256 均保存在 research/phase1_pack_trend_20261011。原综述正式题名：《TechArena 2026 第二阶段 LFP 容量 SOH：文献证据重评与可证伪技术路线》。</Text>
 </Stack>;
}
