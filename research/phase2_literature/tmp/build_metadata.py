import csv
from pathlib import Path
out=Path(__file__).resolve().parents[1]/'outputs'
cols=['来源ID','证据状态','方法家族','化学体系与拓扑','所需运行信号','容量标签需求','完整循环静置专门测试','采样分辨率','LFP平台敏感性','温度依赖','单体到组迁移','缺口处理','因果在线可用性','可解释性','计算成本证据','数据代码可用性','本项目适配工作','结论可信度']
rows=[
['Schaeffer2024','正式版元数据与作者稿全文','GP阻抗和故障','LFP八串约160Ah','I;单芯V;T;均衡','不以逐期容量为训练标签','无容量RPT要求','现场中位5s','阻抗定位仍依赖工作点','GP显式工作点分离','原生串联组但非容量SOH','论文承认现场缺口','前向GP可用;平滑不可回溯使用','高','递归GP百万点处理;本包耗时未报告','BattGP代码;Zenodo数据;许可需复核','单芯异常和温度校正;不可直接换算容量','阻抗结论高;容量迁移低'],
['Krupp2021','机构PDF全文','ICA串联组','LFP四串40Ah','I;单芯或组V;T','多次实验室容量表征','C/5 ICA;1C容量;25C实验','1s','求导及峰位敏感','只在控制温度测量','直接研究四串异SOH','未做现场缺口','局部曲线可因果提取','高','论文称低计算;无本包计时','数据按请求','降采样低维特征;共同窗口;外部验证','拓扑高;运行迁移中低'],
['Deng2022','PMC全文','随机短CC充电与ML','LFP及另三体系单芯','I;V;T','多芯跨寿命容量标签','0.5C CC-CV','原文本次未核实精确采样','10mV窗口误差增大','跨条件需检验','单芯到四串未验证','无针对本包缺口规则','事件因果;训练映射依赖外部标签','中','SGPR/DCNN成本未给本包实测','开放全文;数据按文内声明','先用窗口Ah而非照搬监督误差','局部信号高;本包精度低'],
['Yi2024','arXiv全文','DEKF SOC/SOH联合','LFP两单芯','I;V;OCV曲线;参数先验','初始容量与验证容量','0.1C循环;专门HPPC','原文条件控制;非本包10s论证','高斜率更新;平台冻结','验证25/5C','未验证四串组','滤波可提高缺口方差','前向滤波可用','高','本包时间未报告','预印本;数据代码未核实','低自由度门控;偏置/极化联合检查','机制中;迁移中低'],
['ZhouAitioHowey2025','arXiv全文','老化ECM加GP','NMC/NCA两单芯','I;V;初始OCV','初始RPT;后续RPT只验证','初始OCV/RPT','0.2Hz和1Hz','LFP无验证','原数据温度条件有限','未验证四串','抽样放电段;缺口细则未报告','滤波可前向;原文另有预测','中高','状态空间GP线性时间思路','两公开数据;预印本','只借状态门控与不确定度','本化学迁移低'],
['Wang2025','arXiv全文','OCV对齐容量','NMC/石墨硅单芯4.85Ah','I;V;初始OCV;局部Ah','初始OCV及多次容量验证','初始OCV专门测试','原文未作10s目标测试','平台对齐可能病态','温度迁移未报告','组迁移未报告','缺口规则未报告','前向对齐可行需OCV识别','高','本包成本未报告','预印本;相关数据开放','用CK0曲线检验高斜率窗口','理论启发中;目标迁移低'],
['Zhou2026','arXiv全文及接受稿','动态虚拟ICA与CNN','NMC622三并208Ah','I;V;动态充电','大量配对CC曲线和SOH','相邻低倍率充电及静置','1Hz','未在LFP测试','原文工况控制','三并到四串差距大','随机裁剪模拟局部窗口','推理可因果;训练需外部监督','中','Mobile版参数和FLOPs约降67%','私有数据;公开论文','不得直接求导动态曲线;延期研究','原体系高;本包低'],
['Cheng2024','arXiv全文','IC特征与退化模式监督','NMC811/硅石墨单芯','1/3C I;V','多次RPT退化模式标签','RPT与完整充电','原文未核实目标采样','LFP无验证','10/25/40C','单芯到组未验证','剔除异常循环','特征可在线;模式训练不可','中','91特征筛选+FNN;本包成本未报告','原数据库说明见文;许可未核','特征筛选思想;不复制标签模型','本任务直接适用低'],
['Berecibar2016','仅出版页摘要','LFP组DVA','LFP电芯与组','部分充放电I;V','18芯多工况容量标定','受控部分充放电','未核实','LFP本体但导数敏感','多温度场景','有组验证;细节未读','未核实','原文称在线;本包未试','高','摘要称低计算;未量化','付费全文未取到','待全文后再评估峰/拐点','摘要级中低'],
['Zhu2022','仅出版页及作者稿索引','充后弛豫ML','NCA/NMC单芯130','充满后V;T','多寿命容量标签','充满且长静置','原文采样未核实','LFP无验证','温度需匹配','单芯到组未验证','未核实','静置事件存在才因果','中','未核实','作者代码公开;全文未取到','先审计休止窗口','目标迁移低']]
with (out/'方法对比.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(cols);w.writerows(rows)
assert all(len(r)==len(cols) for r in rows)
bib=r'''@article{Schaeffer2024,
  author={Schaeffer, Joachim and Lenz, Eric and Gulla, Duncan and Bazant, Martin Z. and Braatz, Richard D. and Findeisen, Rolf},
  title={Gaussian process-based online health monitoring and fault analysis of lithium-ion battery systems from field data},
  journal={Cell Reports Physical Science}, year={2024}, volume={5}, number={11}, pages={102258}, doi={10.1016/j.xcrp.2024.102258}, url={https://www.sciencedirect.com/science/article/pii/S2666386424005630}
}
@article{Krupp2021,
  author={Krupp, Amelie and Ferg, Ernst and Schuldt, Frank and Derendorf, Karen and Agert, Carsten},
  title={Incremental Capacity Analysis as a State of Health Estimation Method for Lithium-Ion Battery Modules with Series-Connected Cells},
  journal={Batteries}, year={2021}, volume={7}, number={1}, pages={2}, doi={10.3390/batteries7010002}, url={https://elib.dlr.de/140003/1/batteries-07-00002.pdf}
}
@article{Deng2022,
  author={Deng, Zhongwei and Hu, Xiaosong and Xie, Yi and Xu, Le and Li, Penghua and Lin, Xianke and Bian, Xiaolei},
  title={Battery health evaluation using a short random segment of constant current charging},
  journal={iScience}, year={2022}, volume={25}, number={5}, pages={104260}, doi={10.1016/j.isci.2022.104260}, url={https://pmc.ncbi.nlm.nih.gov/articles/PMC9062330/}
}
@misc{Yi2024,
  author={Yi, Baozhao and Du, Xinhao and Zhang, Jiawei and Wu, Xiaogang and Hu, Qiuhao and Jiang, Weiran and Hu, Xiaosong and Song, Ziyou},
  title={Bias-Compensated State of Charge and State of Health Joint Estimation for Lithium Iron Phosphate Batteries}, year={2024}, eprint={2401.08136}, archivePrefix={arXiv}, url={https://arxiv.org/html/2401.08136}
}
@misc{ZhouAitioHowey2025,
  author={Zhou, Zihao and Aitio, Antti and Howey, David},
  title={Learning Li-ion battery health and degradation modes from data with aging-aware circuit models}, year={2025}, eprint={2407.06639}, archivePrefix={arXiv}, url={https://arxiv.org/html/2407.06639}
}
@misc{Wang2025,
  author={Wang, Yang and Zagorowska, Marta and Ferrari, Riccardo M. G.},
  title={Capacity Estimation of Lithium-ion Batteries Using Invariance Property in Open Circuit Voltage Relationship}, year={2025}, eprint={2511.06989}, archivePrefix={arXiv}, url={https://arxiv.org/html/2511.06989}
}
@misc{Zhou2026,
  author={Zhou, Qinan and Vuylsteke, Gabrielle and Anderson, R. Dyche and Sun, Jing},
  title={Battery State of Health Estimation and Incremental Capacity Analysis under Dynamic Charging Profile Using Neural Networks}, year={2026}, eprint={2502.19586}, archivePrefix={arXiv}, url={https://arxiv.org/html/2502.19586}
}
@misc{Cheng2024,
  author={Cheng, Yuanhao and Bai, Hanyu and Liang, Yichen and Cui, Xiaofan and Jiang, Weiran and Song, Ziyou},
  title={Data-Driven Quantification of Battery Degradation Modes via Critical Features from Charging}, year={2024}, eprint={2412.10044}, archivePrefix={arXiv}, url={https://arxiv.org/html/2412.10044}
}
@article{Berecibar2016,
  author={Berecibar, Maitane and Garmendia, Maitane and Gandiaga, Inigo and Crego, Jon and Villarreal, Igor},
  title={State of health estimation algorithm of LiFePO4 battery packs based on differential voltage curves for battery management system application},
  journal={Energy}, year={2016}, volume={103}, pages={784--796}, doi={10.1016/j.energy.2016.02.163}, url={https://www.sciencedirect.com/science/article/pii/S0360544216302250}
}
@article{Zhu2022,
  author={Zhu, Jian and Wang, Yixiu and Huang, Y. and others},
  title={Data-driven capacity estimation of commercial lithium-ion batteries from voltage relaxation}, journal={Nature Communications}, year={2022}, volume={13}, pages={2261}, doi={10.1038/s41467-022-29837-w}, url={https://www.nature.com/articles/s41467-022-29837-w}
}
'''
(out/'references.bib').write_text(bib,encoding='utf-8')
print(len(rows))
