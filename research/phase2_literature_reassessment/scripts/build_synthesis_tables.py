"""Traceable question and method-family comparison, scoped to reviewed evidence."""
import csv
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "outputs"

QUESTIONS = [
 ("Q1","单 CK0 锚点+运行前缀可识别什么","Lin2015_Fisher_identifiability;B_card_Yi2024;A_Zhou2025","B_card_Schaeffer2024;B_card_Cornejo2026","四芯绝对容量、SOC 初值、OCV 漂移、偏置/极化的联合独立性未证","固定 CK0/OCV 先验后做 Q,z0,b,R 剖面似然与奇异值；再以独立多标签四串组验证"),
 ("Q2","LFP 局部窗口何时有容量信息","A_Deng2022;A_Krupp2021;A_Wang2025","A_Figgener2024;A_Yi2025;Lin2015_Fisher_identifiability","完整曲线裁剪与真实浅循环、未知初始 SOC 尚未等价","同一电芯配对自然浅充与后验裁窗，锁温度/方向/窗和实体留出"),
 ("Q3","分离即时温度、热老化、工况和时间","A_Ruiz2018;A_Aeppli2025;Yagci2025_large_LFP_aging","A_Ovejas2019;A_Yi2025","本竞赛 CK1–7 参考测温和传感器误差规格未知","跨温路径交叉、共同 25°C RPT、实际芯温积分与固定模型消融"),
 ("Q4","脉冲/恢复何时提供容量而非代理","B_card_Gasper2025;B_card_Zhang2011","B_card_Schaeffer2024;A_Zhou2025;B_R3_cluster_audit","官方脉冲无配对真实容量，10s 采样与静置状态限制 R0","同 SOC/T/静置匹配脉冲，以组级多标签 D2 对年龄/温度/Ah 强基线作增量"),
 ("Q5","四串组容量由何决定","A_Krupp2021;B_card_Cornejo2026","B_card_Schaeffer2024;OFFICIAL_CONSTRAINTS","逐芯触限和组端 11.2V 首次触限非同一协议；均衡动作未全知","固定满充起点，以逐芯模型求 sum(V_i)=11.2V 首次根，与独立组 C/20 RPT 比较"),
 ("Q6","低标签迁移/物理约束增加什么","C_Richardson2017_GP;C_Arunan2025_SSL;C_Che2023_Continual","C_Ispizua2026_PINN;C_Schaeffer2024_BattGP;C_Silva2026_Conformal","标签预算/未来目标分布/寿命代理和组拓扑迁移收益未分开","相同输入预算、组级封存、目标一锚和严格前缀；消除年龄/温度/掩码代理"),
 ("Q7","最差芯与末期高估可能来自什么","A_Aeppli2025;Zhang2024_knee_curvature;A_Zhou2025","B_card_Cornejo2026;A_Ovejas2019","无多时间容量不能确认容量 knee 或限制芯变化原因","冻结早期趋势，对残差/触限身份做顺序检验，触发独立容量复测与同温诊断"),
 ("Q8","隐藏标签下何种验证与测量最有价值","OFFICIAL_CONSTRAINTS;Yagci2025_large_LFP_aging;C_Richardson2019_GPTransition","C_DATA_QUALIFICATION;B_card_Schaeffer2024","D1 多次开发、D3 只有 CK0；无协议相符 D2","同协议 25°C 四串 5.1A 至 11.2V 重复容量，按物理组封存并测功效"),
]
with (OUT / "research_questions.csv").open("w", newline="", encoding="utf-8") as f:
    w=csv.writer(f);w.writerow(["question_id","question_cn","support_ids","limiting_ids","unresolved","minimal_discriminating_experiment"]);w.writerows(QUESTIONS)

METHODS = [
 ("F01","局部充放/窗口学习","容量候选","I,V,窗口Ah,方向,SOC/T","通常需跨寿命容量标签与已知窗口","相同 SOC/T/电流/方向且非后验裁窗时才可测试","A_Deng2022;C_Fragmented2025;Zhou2026_dynamic_ICA","A_Wang2025;Lin2015_Fisher_identifiability","质量门控后验证；不直接作为胜出容量估计"),
 ("F02","ICA/DVA 与退化模式","退化诊断/条件性容量","低噪声 V-Q 曲线与低倍率","峰标定/半电池与多 RPT 常为先验","平台峰分辨、滤波宽度和窗口覆盖敏感","A_Krupp2021;Bilfinger2024;Yagci2025_large_LFP_aging;Cheng2024","A_Figgener2024;A_Ovejas2019","诊断和选窗，容量映射待组真值"),
 ("F03","脉冲/恢复/阻抗","电阻/故障代理，条件性容量","匹配 SOC/T 的 I,V 瞬态和恢复","容量映射需独立配对标签","10s 无法分离毫秒欧姆项，早期同脉冲需记预算","B_card_Gasper2025;B_card_Schaeffer2024;Zhu2022","B_card_Zhang2011;A_Zhou2025","先质量/故障门控，D2 后试增量"),
 ("F04","温度/滞后/路径","可逆响应+不可逆损伤","实际芯温、工况设定、历史暴露","固定参考温度容量与交叉实验","温度、时间、SOC、通量相互相关","A_Ruiz2018;Yagci2025_large_LFP_aging","A_Ovejas2019;A_Aeppli2025","分层温度处理，勿统一线性扣除"),
 ("F05","SOC/SOH 联合估计","容量/状态联合","长跨度 I,V，可靠 OCV/高斜率","初始 OCV、偏置/RC、容量先验","Fisher 矩阵病态时冻结容量更新","Lin2015_Fisher_identifiability;B_card_Yi2024","A_Zhou2025;B_card_Shi2026","优先验证低自由度可辨识门控"),
 ("F06","串联组不均衡","官方组端容量","逐芯/组压、I、满充与均衡","芯间容量/SOC/极化约束","逐芯阈值不能代替组端 11.2V 首次根","A_Krupp2021;B_card_Cornejo2026","OFFICIAL_CONSTRAINTS;B_card_Schaeffer2024","用组端根投影，单芯故障另诊断"),
 ("F07","低标签 GP/层级统计","容量轨迹概率先验","真实组容量及协变量","多实体容量标签与噪声模型","单 CK0 下斜率主要来自源域先验","C_Richardson2017_GP;C_Richardson2019_GPTransition","C_Che2023_Continual;C_Schaeffer2024_BattGP","有 D2 后备选；区间需独立校准"),
 ("F08","退化轨迹/末期","变化点/尾部风险","长时间容量轨迹/残差","多时间容量或可靠代理","代理 knee 非容量 knee；尾部事件稀少","Zhang2024_knee_curvature;A_Aeppli2025","A_Zhou2025;C_Richardson2019_GPTransition","趋势门控与复测触发，不盲下修"),
 ("F09","表征学习/迁移","候选容量特征","大量无标签时序和源域标签","冻结实体/时间与预训练路径","年龄/温度/片长可成为捷径","C_Arunan2025_SSL;C_YaoKowal2026_SSL;BatteryGPT2025;F_Deng2024_RapidPackDA","C_Che2023_Continual;C_Ispizua2026_PINN","仅在同预算组封存增量通过后加用"),
 ("F10","物理约束/降阶电化学","状态与退化先验","ECM/半电池/温度参数","OCV、半电池、标定激励","参数互相替代，形式约束不能造标签","C_Wen2023_PINN;Yagci2025_large_LFP_aging","C_Ispizua2026_PINN;Lin2015_Fisher_identifiability","低自由度原型先于复杂 PINN"),
 ("F11","不确定性/可信更新","预测区间与拒绝规则","分布外分数、残差、质量指标","独立物理组校准标签","六芯/同组多点伪样本与时序漂移","C_Silva2026_Conformal;C_Richardson2017_GP","C_Schaeffer2024_BattGP;OFFICIAL_CONSTRAINTS","可报告风险/拒绝，不冒称官方覆盖"),
 ("F12","实验设计/开放数据","验证契约","P1,Che,TU,He,Xu,Yagci 和新组 RPT","同协议多组容量标签","公开、容量字段与协议相符是三件事","Yagci2025_large_LFP_aging;C_DATA_QUALIFICATION","OFFICIAL_CONSTRAINTS;C_Schaeffer2024_BattGP","先资格审查，优先新同协议测量"),
]
with (OUT / "method_comparison.csv").open("w",newline="",encoding="utf-8") as f:
    w=csv.writer(f);w.writerow(["family_id","family_cn","target","inputs","labels_or_prior","identifiability_condition","support_ids","limitations_ids","contest_decision"]);w.writerows(METHODS)
print("questions",len(QUESTIONS),"families",len(METHODS))
