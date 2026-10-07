# LFP SOH 第二阶段核心论文精读与证据附册

版本：2026-09-29。此附册汇集每篇原始证据卡全文，不把版本重复计为独立研究。卡片内容是研究笔记；作者报告、原文核对、本地重算和独立组容量验证不能互换。主报告只引用与决策相关的结论；原文 PDF/HTML 和每卡来源定位可供追溯。旧版/重复卡仍保存在 `notes/workstreams/`。

收录 33 项独立研究的完整卡片；另外 5 张不同工作流或版本重复卡不重复计数。


## 1．Lin2015_Fisher_identifiability｜Analytic Bound on Accuracy of Battery State and Parameter Estimation

来源卡：`notes/papers/Lin2015_Fisher_identifiability.md`。书目身份：`10.1149/2.0791509jes`。


**原文。** Xinfan Lin, Anna G. Stefanopoulou, “Analytic Bound on Accuracy of Battery State and Parameter Estimation,” *Journal of The Electrochemical Society* 162(9) (2015) A1879–A1891, DOI [10.1149/2.0791509jes](https://doi.org/10.1149/2.0791509jes)。2026-09-29 读取[作者机构公开 PDF](https://websites.umich.edu/~annastef/papers/analyticbound2015a.pdf)，本地 `papers/D_trajectory/Lin2015_analytic_bound.pdf`；首页 CC BY 4.0。检索到正式版与作者 PDF 题名、页码和 DOI 一致。已读方法、解析式、数值示例与结论；已将 PDF 第 4–5 页渲染为图像核式 (9)、(11)、(14)–(19) 与表 I。本轮无作者代码运行。

**研究问题和信息条件。** 论文问在给定电压噪声和电流激励下，SOC 初值、容量 `Q`、欧姆电阻 `R` 单独或联合估计的 Cramér–Rao 方差下界。模型为单芯 OCV+R/RC 等效电路，采用已知或局部线性 `g(SOC)`、独立高斯电压噪声、准确电流/其他模型参数等假设；LFP 数值案例为 2.3 Ah 25°C 单芯，NMC 对照 5 Ah。不是四串长期老化的实际盲测容量算法。物理实体/训练集划分不是其主要评价单位，解析结果来自模型及参数化，数值曲线的“估计误差”不能当独立现场泛化误差。

**核心推导与单位。** `SOC_k=SOC_0+Σ_{i<k} I_i Δt/Q`（符号按充电正；`IΔt` 应用 Ah 与小时），`V_k=g(SOC_k)+I_kR+RC动态项`。若中段 OCV 近似斜率 `α=dV/dSOC`（V/单位 SOC），电压对容量灵敏度 `∂V_k/∂Q≈−α (Σ I_iΔt)/Q²`；对电阻为 `I_k`。对参数向量 `θ`，`F=(1/σ_V²)JᵀJ`，其中 `J_{k,j}=∂V_k/∂θ_j`，`σ_V` 为 V。固定其他量只估容量时，原文式 (14)–(15) 给相对标准差下界 `SD(Q̂)/Q ≥ σ_V/[|α| sqrt(Σ_k ΔSOC_k²)]`。故容量信息不仅需电压斜率，还需累计 SOC 跨度；大量高度相关的采样点不等于独立信息。

对 `SOC_0,Q` 联合估计，`J` 两列近似为 `α` 与 `−α ΔSOC_k/Q`；若 `ΔSOC_k` 近常数或全为零，两列共线/弱分离。电流偏置、电压偏置、OCV 老化与未知 RC 会进一步增加混淆，本文的简单 CRLB 不自动涵盖它们。

**原文定量示例。** 印刷页 A1882–A1883 的表 I：LFP 中段 `α=1.7 mV/1% SOC`，NMC `6.5 mV/1% SOC`；设 `σ_V=10 mV`。式 (15) 下两次 10%/90% SOC 电压测量、**其他参数已知**，作者算 LFP 相对容量标准差下界 7.35%、NMC 1.92%；40% 跨度时 LFP 14.71%、NMC 3.85%。这些百分数是**模型假设下的理论精度下界实例**，不是本竞赛测量噪声或实际 MAE。样本数和时间相关性、OCV曲线、真实偏置变化会改变结果；不能把 7.35% 宣称为官方最低误差。结论指出联合估计通常比单独估计损失精度，输入激励结构有时能避免部分损失（印刷页 A1890–A1891）。

**竞赛适配与反证。** 理论支持把窗口设计、SOC 覆盖、温度/偏置条件化与信息矩阵条件数作为**可辨识性门控**，而不是一概否定部分窗口。CK0 只是一次带载参考曲线，运行中初始 SOC 与电压漂移不已知；四芯总压又叠加不均衡。单芯解析式必须扩成四串，并核可观测的单芯电压、传感器误差、相关噪声和温度后，才能用作数值门槛。

最小实验：在可见前缀的真实激励上冻结电路/OCV 先验与假设噪声，计算每窗口 `J` 的奇异值、对容量的 profile likelihood/扰动响应；预先指定可辨窗口，再于独立有同协议容量的组核其预测增量。若所谓高信息窗口在改变 SOC 初值或电压偏置后仍能用不同容量给出同等电压拟合，撤回容量更新资格。没有真实 D2 时只能完成诊断，不能确认容量精度。

**核验级别/缺项。** E1 全文原式与限制核对，E2 原页表格/公式视觉检查已完成；未见可运行代码、未做独立数据验证。作者的建模假设是待检条件，不是公式的普适结论。


## 2．Yagci2025_large_LFP_aging｜Degradation modes of large-format stationary-storage LFP-based lithium-ion cells during calendaric and cyclic aging

来源卡：`notes/papers/Yagci2025_large_LFP_aging.md`。书目身份：`10.1016/j.est.2025.116774`。


**核实书目与版本。** M. C. Yagci 等，“Degradation modes of large-format stationary-storage LFP-based lithium-ion cells during calendaric and cyclic aging,” *Journal of Energy Storage* 124 (2025) 116774，DOI [10.1016/j.est.2025.116774](https://doi.org/10.1016/j.est.2025.116774)。2026-09-29 读取[Offenburg 机构公开出版 PDF](https://opus.hs-offenburg.de/frontdoor/deliver/index/docId/10762/file/1-s2.0-S2352152X25014872-main.pdf)，本地 `papers/D_trajectory/Yagci2025_large_LFP_aging.pdf`，17 页，CC BY 4.0。论文发表页“数据按请求提供”；后续 [Zenodo v1.1, 2026-09-24](https://zenodo.org/records/22939281)，DOI 10.5281/zenodo.22939281，Related works 明列本论文，README CC BY 4.0；v1.0 曾标 CC BY-NC 4.0。已核 3.3KB README，2.5GB Data.zip 未下，尚未核代表字段，故数据开放性与本轮下载状态分列。

#### 问题、实体和实验契约

论文比较大容量储能 LFP 在温度、日历/循环与存放 SOC 下的容量衰退及 LLI/LAM（§1–2、表 1–2）。12 只同批 CALB CA180FI 180 Ah LFP/石墨棱柱芯，每组两个：35°C/50°C ×（0.28C 完整循环、75% SOC 恒压存放、100% SOC 恒压存放）；循环最多 1500 次、日历约 846–850 天。表 2 的“组”是实验条件，物理实体仍只有每条件 2 只。不能将 1500 周期或四次 RPT 当独立实体。

循环 50 A CC–CV（至 9 A 终止）、充放电均包括 CV，间歇仅 10 s；存放时恒压维护，论文图 2 显示测量回路小电流波动/偏置。RPT 在初始及约 106/255/553/846 天，所有电芯先在 20°C 稳定至少 1 天，再在 20°C 同协议测容量、IR、低倍率 pOCV（§2.3）。第一个复查未做耗时 pOCV，退化模式分析排除该点。容量真值为**两轮 50 A 充放后第二轮、包括 CC+CV 的全放电积分**，SOH 分母是**该芯初始 RPT 容量** `C0`，不是官方组端 C/20/102 Ah。论文按厂家电流精度推估容量测量误差约 1.6 Ah（其初始容量约 0.8%）；这是论文设备的估计，不是本竞赛传感器规格。

#### 方法与公式（自己表述，原文 §2.2–2.4）

- 当前循环容量 `C_cell = ∫_{full discharge} |I|dt`（Ah）；`SOH_C=C_cell/C0` 无量纲。表 3 `ΔSOH_C = 1−SOH_C,checkup4`，以百分数表示。该单位不能与竞赛 SOH 百分点直接相减。
- `IR_cycle=(mean V_charge−mean V_discharge)/(mean I_charge−mean I_discharge)`，单位 Ω，来自全循环平均量，不等于高频欧姆电阻 `R0`。RPT 另外在每 2% SOC 做 25 A、30 s 脉冲，并依电压差得表观 IR；接触电阻变化使小 IR 波动（§3.1、§5）。
- 低倍率 0.02C 充放曲线作 pOCV；用文献半电池曲线、五参数优化 `p=(x_PE,min,x_PE,max,x_NE,min,x_NE,max,C_cell)` 拟合全芯 `dV/dQ`（§2.4 式 7–8），由电极工作区与容量推 LLI/LAM。半电池曲线与完整低倍率复测是额外先验；不可能仅由官方一次带载 CK0 曲线确定每个后续点的五参数。
- 温度外推的 Arrhenius 关联是 12 芯、35/50°C 条件下的**全局描述**，作者给活化能 `37.3±12.8 kJ/mol`（95% 范围，§5）；因个体/条件偏离明显，不能不经验证直接套到 25/45°C 竞赛组。

#### 原文结果与公平解释

表 3（印刷页 14；PDF 页 15）最终相对初始容量损失：35°C 完整循环两芯 10.6/11.4%，平均 11.0%；50°C 22.2/22.4%，平均 22.3%；35°C 日历 75/100% SOC 平均 7.5/7.8%，50°C 13.3/14.0%。同温条件内只有两芯，不能由小样本证明某 SOC 影响为零。作者发现容量衰退显著而 IR 仅 50°C 循环在后期有清楚上升（§5–6、图 11），这**反对把阻抗单调变化当普遍容量真值**。LLI 被认为主导，但取决于其半电池拟合与协议。

图 11 所呈现的所有组间容量比较均用 20°C RPT，故“高温老化更快”与“测试瞬时高温使可用容量改变”在设计上已分开；本竞赛 25/45°C 运行和隐藏 checkup 参考条件也应分开。论文的同组平均趋势支持温度/日历先验，但不支持直接将运行温度作为容量修正系数。§5 特别提醒循环芯内部实际温度可比箱体约高 3°C（模型估计），作者在 Arrhenius 分析中作敏感性处理。

**原文内部不一致：** §2.2/表 2 明列 50 A/180 Ah＝0.28C 周期工况，但讨论 §5 及表 4 写“cyclic aging at 1C”。本文卡采用可由 50 A 和 180 Ah 相互核对的 0.28C，表 4 的 1C 字样记为需作者澄清的冲突；不以表 4 对其他研究的倍率作精确可比推断。

#### 对照、局限与竞赛适配

论文是机理/实验对比，没有封存组级容量预测器、与同输入容量估计基线、最差/末期预测误差或四串 SOC 不均衡检验。条件、温度与协议高度控制；本题为四串、动态浅循环、两段工况、一次 C/20 组容量标签。最可迁移的是：按温度稳定后的同一参考协议取标签；温度老化量与瞬时测量条件区别；把接触/阻抗噪声与 LLI 假设分离；少数条件下要以物理芯为统计单位。

**最小反证实验。** 在独立大容量 LFP 多标签组中预先冻结温度/日历先验：以实际芯温或至少传感器统计、累计时间和吞吐量估计损伤，和只用时间/吞吐量强基线对比；测试组/温度均封存。若加温度后最差组/末期组容量 MAE 未改善，或参考温度切换改变排序超过温度先验所解释的幅度，则降级为背景风险因子。必须有统一参考容量标签，不能用本论文 20°C 第二轮 50 A 容量直接换算官方四串 C/20 组容量。

**核验等级与剩余工作。** E1 全文方法/结果核对，E2 表 2、图 11 与容量公式原页检查；本轮尚未静态审查关联数据全部字段或代码、未跑作者模型、未做独立容量验证。已计划从表 3 重算均值（仅核印刷数字，不算复现）。


## 3．Zhang2024_knee_curvature｜Battery capacity knee-onset identification and early prediction using degradation curvature

来源卡：`notes/papers/Zhang2024_knee_curvature.md`。书目身份：`10.1016/j.jpowsour.2024.234619`。


**书目与载体。** Huang Zhang, Faisal Altaf, Torsten Wik, “Battery capacity knee-onset identification and early prediction using degradation curvature,” *Journal of Power Sources* 608 (2024) 234619, DOI [10.1016/j.jpowsour.2024.234619](https://doi.org/10.1016/j.jpowsour.2024.234619)。2026-09-29 读取[作者机构公开正式版 PDF](https://research.chalmers.se/publication/541105/file/541105_Fulltext.pdf)，本地 `papers/D_trajectory/Zhang2024_knee_curvature.pdf`，全文 13 页；首页标 CC BY 4.0。出版平台 HTML 与机构版的题名/DOI一致。`pdftotext` 有少量字典语法警告，关键公式、单位需以原页图像为准。本轮已阅读正文方法、数据、结果与局限；页 4 公式与页 8–9 图表已对照文本，尚未运行作者方法。代码公开状态本次未确认；不声称复现。

#### 问题与新增

作者要在**已测得的一系列放电容量**轨迹上识别 knee onset 和 knee，再用早期循环特征预测 onset。相对双 Bacon–Watts 两折点拟合，提出平滑后的离散曲率近似，再对其矩阵轮廓/校正弧曲线做状态分段（§2–3）。论文的“online”是随容量测量逐步到来的在线识别，并非没有后续容量标签就仅由日常电流电压在线估容量。

#### 数据、标签和单位

- §3.3.1 和 §4.1.1：TRI/MIT 系列 169 只 A123 APR18650M1A 1.1 Ah LFP/石墨圆柱单芯；实验室快速充电循环，有每周期/重复容量资料。该 169 与 Severson 2019 所强调的 124 数据子集可能有版本/筛选差异，不能混为同一独立验证。物理实体 169，窗口/循环数不能代替实体数。
- §3.3.2：SNL 原数据 32 只 LG 18650HG2 3 Ah NMC/石墨单芯，15/25/35 °C、不同 DOD 与 0.5–3C 放电；剔除 10 只无 knee/EOL 或容量污染者，报告 22 只。额定容量在对应环境以 0.5C 放电定期测量。选择“确有 knee 的轨迹”影响外推范围。
- §3.3.3：三条 PyBaMM DFN 合成 NMC 轨迹，含 SEI 和颗粒破裂机制；参数继承多个来源，1C CC–CV 后 1C 到 2.5 V。合成机制验证不能充当独立真实容量验证。
- 所有主要识别输入是容量序列 `Q_i`（Ah 或 `Q_i/Q_nom`）与循环索引；另有早期预测的六个 MIT 特征（表 5）包括循环 2 容量、前 30 循环容量差、完整放电 Q(V) 曲线的统计。不是官方单锚点 + 浅动态前缀。SOH 分母与官方 102 Ah 组端 C/20 不同。

#### 方法链与关键公式（按原文 §2–3，页 3–5）

1. 容量轨迹归一化 `q_i=Q_i/Q_nom`。假设循环索引等间隔；否则先样条插值。Savitzky–Golay 平滑得到 `q̃_i`。
2. 以跨度 `h=(w_s−1)/2` 构造 `d_i=q̃_{i−h}+q̃_{i+h}−2q̃_i`，无量纲。等间隔时直线为零，持续负值代表容量下降曲线向下弯；其量值受 `h²`、噪声和平滑窗口影响，不能跨不同时间步长直接比较。
3. 对 `d_i` 作滑窗矩阵轮廓、最近邻索引及 corrected arc curve；以两次状态变更定位 onset/knee。作者**假设**实验末期前出现 knee（§3.1 Assumption 1）和等间隔输入（Assumption 2）。
4. 早期预测复用 Severson 六特征并用 GBRT；169 实体分层随机 80/20，重复 5 次（§4.2.1–4.2.4）。预训练及标签选择仍依赖整条容量轨迹标注 onset；“在线识别”的训练标签与运行时输入要分开。

双 Bacon–Watts 基线的式 (1) 具有 `x0,x2` 两个折点、双 `tanh` 平滑项，并通过 LM 最小二乘估计；作者固定很小 `γ=10⁻⁸`。如果原公式被 OCR 误读需看页 3 原图。此式仅作基线，不是官方模型可直接采用的容量观测式。

#### 结果、对照和限制

作者报告对 169 LFP 单芯 onset 与 EOL 循环相关系数 `ρ=1.0`，knee 与 EOL `ρ=0.992`（§4.1.1，图 3）；SNL 22 NMC 实体 `ρ≈0.712/0.71`（§4.1.2，图 4）。这些是**各数据集内轨迹位置相关**，不是 CK 容量估计误差。TRI 的高度相关可能受共同快速充电协议/筛选影响；本轮尚未独立重算。

早期预测表 5 的完整放电差曲线和 `Q_2`/`Q_max−Q_2` 用了额外容量标签。图 8 的预测目标单位是循环数，不能转换为官方 SOH pp。论文未给官方协议、四串组截止、仅 CK0 标定下的容量精度、最差组或末期七点误差，也未给本题所需的 `fit` 前缀冻结代码。

#### 对本项目的判定

**支持**：如果将来获得独立多时间点容量标签，曲率/状态切换是检查末期高估和轨迹拐点的有用诊断；并提示“单一固定斜率退化”有风险。**反对直接迁移**：当前 CK1–CK7 隐藏，容量曲率 `d_i` 在目标组不可计算；完整实验室放电特征不可由浅动态波形自动取得。把运行代理先当容量、再用其曲率证实容量 knee 是循环论证。优先级：机制参照/新增测量设计，暂不进入官方主预测器。

**最小反证实验。** 在真正独立多标签 LFP/组数据中预先冻结代理到容量映射，按物理组/时间留出；比较容量轨迹的 onset 与仅用可见代理估出的 onset，评价末期容量 MAE、最差组与事件检出率，并对固定斜率基线。若代理 onset 无配对增益或误报，撤回其作为容量更新门控的用途。没有独立容量时只能先做代理稳定性检查，不声明完成此实验。

**核验等级。** 原文核对 E1、关键公式/数据契约检查 E2；代码静态审查/作者运行复现/独立验证均未完成。需要再查论文 Data availability 与实际代码链接，核对表 3 数值及 169 vs 124 数据版本。


## 4．A_Aeppli2025｜Aging behavior of LiFePO4-based battery cells at stack level: A Second-Life cycling study

来源卡：`notes/workstreams/A_partial_temperature/A_Aeppli2025.md`。书目身份：`10.1016/j.est.2025.117135`。


**书目/全文。** Aeppli, Hack, Held, *Journal of Energy Storage* 129:117135 (2025), DOI [10.1016/j.est.2025.117135](https://doi.org/10.1016/j.est.2025.117135)。2026-09-29 实读 [Empa 机构公开出版 PDF](https://www.dora.lib4ri.ch/empa/islandora/object/empa:41733/datastream/PDF/Aeppli-2025-Aging_behavior_of_LiFePO4-based_battery-(published_version).pdf)，本地 `papers/A_partial_temperature/Aeppli2025.pdf`，PDF 第 1 页标 CC BY 4.0。E1：核首页、§2–4、图 4–5、8、10–11、表 4–5，目视 PDF 第 13 页图 10–11；未重算原始数据。

**实体/标签。** 二手 100 Ah LFP/石墨电芯经历不完整可见的第一寿命（车辆里程可知但电流/温度史不可见），第二寿命组架实验最长约 9600 周期、七年，整体年龄超 14 年。作者对单芯做周期容量测与 ICA，组架有位置温度；不是本题同一四串且没有未知 CK1–CK7 真值。SOH 取当前容量/保守指定 100 Ah 名义值，作者承认原始量产容量可 107–113 Ah；本题则用官方指定分母。§2、§4.1.1。

**尾部/温度结果。** 首页与 §4.2.4：前 10 个容量点拟合的幂律在一枚芯约第 8000 周期、48 Ah/48% SOH 时产生持续残差偏离，作者提出 ±3σ 残差门槛作为个案末期警讯，尚需外部泛化。§4.2.4 报电阻从约 7200 周期非线性升高、ICA 峰变化与潜在 LAM/极化，但单一信号不足以断言确定机制。§4.4.2：标称 10°C 箱内组架局部可达 22°C；图 11 展示的是 30°C 组架的温度波动，不是 10°C 数据。高初始容量组近似 Arrhenius 温度趋势，低初始容量组在 10°C 的退化甚至略快于 30°C，提示历史与温度相互作用；不能给本题套统一温度加速因子。

**适配/反证。** 相近容量和 LFP 化学体系使其对 Q7/Q3 很重要；第一寿命未知、老化端点远低于官方目标范围，故不能把其 48% 拐点当竞赛芯阈值。对官方前缀的增量损伤模型用冻结早期趋势外推，滚动检查容量代理残差、限压芯改变及电阻一致性；只有新增独立容量复测才能判其为真拐点。温度敏感性应以实测电芯/壳体温度与箱体设定分开。作者本文没有跨实体盲测末期预测保证。


## 5．A_Cornejo2026｜Estimating the Health and State of Charge of Each Cell in a Second-Life Battery System from Field Data

来源卡：`notes/workstreams/A_partial_temperature/A_Cornejo2026.md`。书目身份：`arxiv:2609.04487`。


**书目/状态。** Cornejo, Meyer-Schwickerath, Sandalinas, Jossen, [arXiv:2609.04487](https://arxiv.org/html/2609.04487), 2026-09 预印本；2026-09-29 实读作者 HTML，尚无核实的期刊 DOI。E1：Results “Battery system and dataset”, “Validation against reference measurements”, 图 5–6、Methods OCV alignment；作者 Julia 仓库仅见论文说明，未核 commit/执行。

**实体/真值。** 27 模块、324 个可观测逻辑芯，每逻辑芯 2P LEV50N LMO/石墨 50 Ah 物理芯，12 逻辑芯串联/模块；**非 LFP 且 MMC 动态切换模块**，与本题恒定四串不同。12.5 h 两次现场循环，电芯电压 10 s、模块电流 1 s、模块温度 15 s，有时间缺口。模型在累计 Ah `q=∫I dt` 上拟合每芯 ECM/GP-OCV，再跨芯曲线对齐求初始 SOC、容量；需要群体共享 OCV 形状、端点锚与足够 SOC 覆盖。§Results 首节、Methods OCV alignment。

**结果需按真值层分开。** 图 5 中 lumped 模块估计比按其单芯估计的“可用 SOH”高 4–16%（25/27 模块），最坏两模块高 24%、31%；这是两种模型输出的比较，**31% 不是与独立 C/20 组容量真值的误差**。独立参照只覆盖 8 模块/96 逻辑芯，C/25 左右一次放/充，静置约 60 s 所构“pseudo-OCV”与拟合共用 CMU 传感器且容量同用曲线配准端点；单芯容量 RMSE 1.25 Ah，去模块共同偏差后 0.55 Ah。Results 图 5–6、Discussion 明述共享电流偏置与参考限制。缺官方低倍率至总压目标的直接验证。

**适配/反证。** 它支持“平均行为可能掩蔽限制芯”且揭示四芯同一电流测量误差相关；不能把其最小芯映射或 31% 转成四串预测误差。对本题取同一四芯的 `V_i`、组 `I` 以及 CK0 放电端点，分别模拟/核实总压与单芯截止协议下组可用 Ah，并做电流偏置共同扰动；若纯最小芯模型不能重现 11.2 V 组容量，需协议约束映射。末期监控限制芯身份切换与 SOC 不平衡，不能只看均值。


## 6．A_Deng2022｜Battery health evaluation using a short random segment of constant current charging

来源卡：`notes/workstreams/A_partial_temperature/A_Deng2022.md`。书目身份：`10.1016/j.isci.2022.104260`。


**书目/全文。** Deng 等，*iScience* 25(5):104260 (2022)，DOI [10.1016/j.isci.2022.104260](https://doi.org/10.1016/j.isci.2022.104260)。2026-09-29 实读 [PMC CC BY 4.0 正式全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC9062330/)；本地 HTML 位于 `papers/A_partial_temperature/Deng2022.html`。E1，核 Results 表 1–3、图 4–7、STAR Methods、Limitations；未复现。

**研究设计。** 四化学体系共 75 单芯，LFP 为 Sandia/A123 1.1 Ah、21 芯；15/25/35°C 老化、0.5C CC-CV 充电及多放电倍率。逐完整 CC 充电曲线在 3.0–3.59 V 按 10 mV 切 60 格，任一短段的容量增量序列和电压输入回归寿命中 SOH；局部段是**完整循环后验裁剪**。用一枚标称工况芯训练、其余同体系芯测试；同一循环多个窗口扩为训练样本，物理实体数仍为 21，不能把约万段视作独立芯。论文 STAR Methods 式(1) 明确定义 SOH 为实际 CC 放电容量除以标称容量；Sandia 原始 RPT 的具体电流、温度、截止协议仍需回 README 复核。论文 MAE(%) 的目标分母与本题名义分母概念相近，但测试协议、实体拓扑和误差汇总不同，不能直接作为本题 pp 性能。Results、表 2–3。

**方法/结果。** `ΔQ_seg=∫_Vbin I dt`，取均值、标准差、片段电压均值进 MLR/稀疏 GP，或原序列进 DCNN；模型使用跨寿命多次容量监督。标称 LFP 另一芯测试的单随机段 MAE：MLR 1.31%、SGPR 0.35%、DCNN 0.27%；表 1。图 4 的 10 mV 窗 LFP 特征平均绝对相关仅约 0.4，低于其他化学体系；图 6 显示窗口缩小或测试温度偏离，误差增大，LFP 高温组尤明显。图 7 的“10 mV 平均误差 <5%”跨四种化学体系/多条件汇总，不是四串大容量 LFP 上限。

**局限、适配与反证。** 原文 Limitations 明说恒环境温度、恒放电电流、完整充放电验证，动态放电和浅充放尚未验证。对本题可借鉴电压段质量筛选、多窗口条件误差与单芯留出设计，不能把论文监督 DCNN 直接套进单 CK0 锚点。最小反证：同一批有容量标签 LFP 的真实浅充事件，按物理芯与温度留出，固定已训练模型，比较后验完整循环裁剪与真实浅循环；若误差显著分离，支持“路径/起始 SOC”混淆。原文仅给 Battery Archive 入口及 MATLAB/GPML 依赖，未在本轮核作者专用代码。


## 7．A_Figgener2024｜Degradation mode estimation using reconstructed open circuit voltage curves from multi-year home storage field data

来源卡：`notes/workstreams/A_partial_temperature/A_Figgener2024.md`。书目身份：`arxiv:2411.08025`。


**书目/版本。** Figgener 等，[arXiv:2411.08025](https://arxiv.org/abs/2411.08025), 2024-11 作者稿；截至 2026-09-29 未在本轮核到期刊 DOI。实读 [作者 PDF](https://arxiv.org/pdf/2411.08025)，本地 `papers/A_partial_temperature/Figgener2024_preprint.pdf`。E1：§2、§3、图 4、8–10 及附录；未重算作者数据。

**数据/链条。** 21 个家储系统、2015–2022 最高八年、106 系统年、约 140 亿个 1 s 点；混合 LMO/NMC、NMC 和 LFP，信号为**系统级**电压、电流、功率与壳体温度。先按充/放方向拆分，筛至少 5% SOC 通量与低电流动态，按脉冲 `R_DC(SOC,T)=ΔV/ΔI` 扣除 `IR`，再将多个局部 V-SOC 曲线横移/平均重建准 OCV；ICA/DVA 前用 Gaussian 平滑。§2.1–2.3 式(2-1),(2-2)、图 1–4。关键先验是现场系统 SOC 估计、足够长的历史和低动态覆盖；即使月级重建也依赖足够经常循环。容量场测来自同团队既有现场测试，具体低倍率统一参照不等同官方 C/20 组测。

**结果与边界。** §3.2、图 9：LFP 形状随年变化细微，退化模式判断确定性低，作者明确归因于平台平坦和特征不明显；§4 说明 NMC/LMO 更易诊断。现场容量测试支持 qOCV 方法的退化趋势，但 LFP 结果不能转述成已达到高精度容量。§2.2.3 只取质量更好的放电曲线做后续分析，并保留充/放滞后区别。多个局部片段经 SOC 横移是**回顾性多年重建**，不等于单次浅充即时辨识。没有独立物理系统留出训练精度或末期误差。

**适配/反证。** 可借鉴方向分层、动态过滤、DCR 校正与多事件一致性；若官方 SOC 本身由未知 Q 算出，横移可能循环依赖。对 D1 真实浅充事件做严格时间前缀的月/年滚动重建，同时以已知容量芯检验前缀长度、温度和电压覆盖门槛；若未覆盖特征区或跨事件峰位不稳定，则不以虚拟 ICA 输出容量。作者代码与公开数据版本本轮未核。


## 8．A_Krupp2021｜Incremental Capacity Analysis as a State of Health Estimation Method for Lithium-Ion Battery Modules with Series-Connected Cells

来源卡：`notes/workstreams/A_partial_temperature/A_Krupp2021.md`。书目身份：`10.3390/batteries7010002`。


**书目/版本。** Krupp, Ferg, Schuldt, Derendorf, Agert, *Batteries* 7(1), 2 (2021；在线 2020-12-30), DOI [10.3390/batteries7010002](https://doi.org/10.3390/batteries7010002)。2026-09-29 实读 [DLR 机构公开的出版 PDF](https://elib.dlr.de/140003/1/batteries-07-00002.pdf)，本地 `papers/A_partial_temperature/Krupp2021.pdf`；首页载 CC BY 4.0。证据等级 E1：核正文、式(1)–(6)、图 4–7、表 1，并目视 PDF 第 7–8 页；未核作者代码/数据，未独立复现。

**问题与新增。** 研究四串模组的组端 ICA 能否保留单芯老化信息，以及单芯 SOH 不一致会怎样改变峰。四枚 Winston 40 Ah 标称 LFP/石墨方形芯组为 12 V 4S；初始单芯容量 43.2–44.3 Ah，单芯分别老化，四次拆装、测量、老化循环。单芯容量以 1C 充放测，组 ICA 用 25°C、C/5 专门充电和 1 s 数据；BMS 达任一单芯电压限即停。组端 SOH 与官方 C/20 至 11.2 V 的定义不同。作者没有独立留出电池组或跨温验证。原文 §2、表 1、图 1、§3.2。

**方法/结果。** ICA 定义 `dQ/dV ≈ ΔQ/ΔV` (Ah/V)，四串共同通过 `ΔQ`，而 `ΔV_pack=ΣΔV_i`；同 SOH、同形状近似下 `4·IC_pack≈IC_cell`，异 SOH 或 SOC 偏移时该等式与峰位叠合失效。§3.2.1 式(1)–(6)。图 5 同质芯时单芯与缩放组曲线相近，BMS 电压噪声可至约 6 mV，作者以单芯 5 mV、组端 20 mV 区间求 IC。图 6–7 显示异质芯峰消退与端点重排；§3.2.3 明确放电先限者为 A，充电先限者为 D。第四轮 A 组内放电容量约 23 Ah。论文主要演示分类与解释，不是跨组盲测的官方目标容量误差；未报告末期独立组测试区间。

**适配、反证与可证伪实验。** 四芯电压可用于识别事件限压芯、共同可观测窗、峰分歧；不可把四个单芯 ICA 或平均容量直接映成 11.2 V 组容量。官方 10 s 动态采样、25/45°C 与本论文 1 s 恒温专测差异大。固定 C/5、同温、同方向、同起始状态选事件，与 CK0 比较 `ΔQ/ΔV` 对滤波宽度、温度及限压芯切换的稳定性；若同一次电芯 SOH 未变而窗口指标随状态复位/温度超过预设容量容差，则只作异常代理。代码/数据公开性未由原文确认。


## 9．A_Ovejas2019｜Effects of cycling on lithium-ion battery hysteresis and overvoltage

来源卡：`notes/workstreams/A_partial_temperature/A_Ovejas2019.md`。书目身份：`10.1038/s41598-019-51474-5`。


**书目/全文。** Ovejas & Cuadras, *Scientific Reports* 9:14875 (2019), DOI [10.1038/s41598-019-51474-5](https://doi.org/10.1038/s41598-019-51474-5)。2026-09-29 实读 [Europe PMC 完整 JATS XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC6795866/fullTextXML)（PMC 页面临时验证码），本地 `papers/A_partial_temperature/Hysteresis2019.xml`；XML 声明 CC BY 4.0。E1：Results “Overvoltage and OCV hysteresis in LFP cells”、Methods “OCV and hysteresis”、图 5、7、式(1)–(7)；未运行数据。

**研究设计。** 商用 LFP/石墨 14430、标称 0.4 Ah 与 NMC/石墨 18650、2.8 Ah；LFP 在 25°C 以 C/5 充、2C 放，约 1000 次循环。LFP GITT 测双方向 OCV：C/50 脉冲 150 min + 16 h 静置；不是普通 BMS 休止点。文中报告 LFP 在 C/25 与 2C 不同检测倍率下容量衰退可为 23% 与 15%，说明“容量损失”依测试协议而变。实体数/独立重复未在所读正文清楚报告，不按曲线数累计。作者没有做在线组容量预测。

**方程/证据。** `H(z)=OCV_charge(z)-OCV_discharge(z)`；充电极化 `η_ch=V_ch-OCV_ch`，放电极化 `η_dis=OCV_dis-V_dis`。图 5 LFP 老化后充电极化增大，但在首末两点比较中放电极化可能下降；作者解释中间约 300 周期后又上升，截取首末会误判轨迹。图 5、7 中老化所致额外充放极化差与滞后增量相随，石墨相变对峰形有影响。作者的机理归因是实验解释，并未证明此关系可单独识别全容量。

**本题边界/最小实验。** 同一固定电压窗的 Ah 会受充放方向、最近极化/静置和老化滞后改变，CK0 放电准 OCV 不足以直接标定运行充电。用同一枚容量已知 LFP 先从共同 SOC 锚点执行充→放与放→充两路径、相同温度/电流/窗口且不同静置长，估窗口 Ah 和峰位；容量不变时若指标显著漂移，先分路径或拒绝更新。本论文温度固定 25°C，不支持温度补偿系数。


## 10．A_Ruiz2018｜The Effect of Charging and Discharging Lithium Iron Phosphate-graphite Cells at Different Temperatures on Degradation

来源卡：`notes/workstreams/A_partial_temperature/A_Ruiz2018.md`。书目身份：`10.3791/57501`。


**书目/全文。** Ruiz Ruiz, Kriston, Adanouj, Destro, Fontana, Pfrang, *Journal of Visualized Experiments* 137:e57501 (2018), DOI [10.3791/57501](https://doi.org/10.3791/57501)。2026-09-29 实读 [Europe PMC 完整 JATS 正文](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC6126518/fullTextXML)，本地 `papers/A_partial_temperature/TempLFP2018.xml`；XML 声明 CC BY-NC-ND 3.0，仅作本地研究副本。它与作者 2017 *Electrochimica Acta* 论文 [10.1016/j.electacta.2017.03.126](https://doi.org/10.1016/j.electacta.2017.03.126) 有共享实验，**不计独立重复**。E1：Protocol §3、Results 图 1–4/表 1、Discussion 图 7；未复算 ANOVA。

**实体/协议/标签。** 约 20 枚试制 LFP/石墨 B5 pouch（十种充/放温度组合，各重复一次），-20 至 30°C、1C、100 深循环；每 25 次在 **25°C、0.3C** 做两次参考充放，充分热稳定。文中区分 `CR_long-term`（各老化工况同温/1C 实测）与 `CR_ref`（25°C 参考工况），分母均需对应首周期/首参考周期，不能混用。额外热电偶在芯表面，环境箱控温。未覆盖 45°C 或百 Ah 四串。Protocol §2–3、表 1。

**结果/公式。** 图 3、表 1 中 30°C 充/-5°C 放与 30/30°C 放，运行容量保持率约 90% vs 86%，但 25°C 参考保持率方向反转（约 82% vs 86%）；说明即时低温可用量与永久损失混合时甚至会反转排序。作者把参考退化率在充/放温度平面拟合多项式（图 7，R²=0.92），发现温度相互作用，不能简化为单个运行温度 Arrhenius 校正。低温工况存在复温后容量恢复；表面形貌为可能机制，不能凭此直接确定每枚芯 LLI/LAM。短时间 100 周期及试制芯限制外推。

**适配/反证。** Q3 必须分开事件测温、老化温度历史与参考标签温度。最小实验：同一物理芯在不同运行温度重复同样窗口，均回 25°C 做标准容量，另交叉充/放温度顺序；若运行指标变而参考容量不变，是可逆测量效应；若参考容量随热历史变，才是老化信号。时间顺序和参考复测必须固定。作者没有公开可直接运行的容量估计代码。


## 11．A_Wang2025｜Capacity Estimation of Lithium-ion Batteries Using Invariance Property in Open Circuit Voltage Relationship

来源卡：`notes/workstreams/A_partial_temperature/A_Wang2025.md`。书目身份：`arxiv:2511.06989`。


**书目/状态。** Wang, Zagorowska, Ferrari, [arXiv:2511.06989v1](https://arxiv.org/html/2511.06989), 2025-11-10，预印本；2026-09-29 实读完整 HTML，未核到正式期刊 DOI，引用 arXiv 版本。E1，核 §2 式(1)–(8)、§3 表 1–4、§4–5；无独立代码复现。

**机制/输入。** 假设老化前后经正确容量归一的 OCV-SOC 形状近似不变，令 `z(q)=z0-q/C`，求 `min_(C,z0) Σ[V_OC,aged(q_j)-V_OC,BoL(z0-q_j/C)]²`；C 为 Ah、q 为累计放出 Ah、z0 未知起始 SOC。先验是**一次完整低倍率 OCV-SOC 曲线**，运行动态场景还要独立 OCV 识别算法，不是把 CK0 低倍率端电压自动当 OCV。§2.2–2.3、式(5)。

**实体/真值/结果。** Stanford 加速老化数据仅选 W5 一枚 4.85 Ah NMC/石墨硅单芯，344 老化循环，首周期 OCV 标定；后续低倍率 OCV 测试及容量复测真值。§3 表 1–2 的四个离线 OCV 全段循环绝对相对误差 0.0102–0.4501%。表 3 仅用循环 159、194 的各 33% 片段，六段误差 1.0627–5.5931%；把同一循环三段的预测容量先平均后，其相对误差分别为 1.3448%、1.4997%。局部窗口可能显著差于全段。动态放电仅首与末周期两点（表 4）误差 0.8640%、0.0604%，依赖额外 OCV 识别。无跨芯/温度/末期最差实体统计，不能读成跨样本 0.85% 保证。

**适配/反证。** 一个锚曲线加未知 z0 的数学思路有用；LFP 平台 `dOCV/dz≈0` 时 `C,z0` 的轮廓目标可能极平，滞后、极化、老化 OCV 形变会破坏不变性。最小实验：在真实 LFP 25/45°C、不同方向和起始 SOC 的同一真容量上，拟合 `C,z0` 的二维轮廓损失，报告置信区间与多窗口分歧；若广泛不同 C 都近似同损失，方法不可作绝对容量更新。代码/数据下载状态未核。


## 12．A_Yi2025｜Bias-Compensated State of Charge and State of Health Joint Estimation for Lithium Iron Phosphate Batteries

来源卡：`notes/workstreams/A_partial_temperature/A_Yi2025.md`。书目身份：`10.1109/TPEL.2024.3492714`。


**书目/版本。** Yi 等，*IEEE Transactions on Power Electronics* 40(2):3033–3042 (2025；2024-11-06 在线)，DOI [10.1109/TPEL.2024.3492714](https://doi.org/10.1109/TPEL.2024.3492714)。实读作者 [arXiv:2401.08136 全文 HTML](https://arxiv.org/html/2401.08136)，2026-09-29；它是期刊前稿，数字仅按该稿引用，未核期刊正文差异。E1，核式(1)–(26)、表 I、§IV；代码未核。

**实体/标签/输入。** 两枚约 1.9 Ah LFP 单芯，25 与 5°C 各测，0.1C 控制充放、SOC 1–70%，包含 0–10% 陡斜区；特制 0.5C 高频与中频激励辨识 RC 参数。容量“真值”分别在相应温度容量测试得到，HPPC 给电阻参数；因此 5°C 的可用容量不是固定 25°C 健康量。初始 SOC 与容量估计先验、预先获取 12 次 OCV 多项式及区域边界，均是本题额外前提。两物理芯内四工况验证，未见跨百 Ah 四串或独立组测试。§IV-A、表 I。

**方程与关键结果。** ECM：`V=OCV(z)-IR_s-v_RC+b_V`，`dz/dt=-ηI/Q`；论文局部线性化推得恒电压偏置导致 SOC 稳态偏差量级 `|b_V|/|dOCV/dz|`（式 17 符号以原文状态误差定义为准）。低斜率区仅库仑积分并估 `b_V`，高斜率约 0–10% 才用 dual EKF 更新 `Q`，中斜率保留 Q；式(22)–(24)、图 2。前稿在注入最高 30 mV 偏置下报告 SOC <1.5%、容量相对误差 <2%，但需上述特制激励及陡斜区；§IV、图表。未报告跨实体末期最差误差。

**适配/反证。** 核心可迁移的是“低可观测区不更新容量”门控和偏置敏感性，而非直接复刻其双滤波器。官方若没有经起始 SOC/OCV 标定的陡斜区或专用频率激励，Q 无法从平台段可靠更新。最小实验：在同芯固定容量真值上人为加 ±5/10/30 mV 常偏置与不同初始 SOC，比较平台段连续更新、陡斜区门控及只积分的误差；若门控不改善末期组容量，降为状态估计辅助。


## 13．A_Zhou2025｜Learning Li-ion battery health and degradation modes from data with aging-aware circuit models

来源卡：`notes/workstreams/A_partial_temperature/A_Zhou2025.md`。书目身份：`10.1016/j.apenergy.2025.126375`。


**书目/版本。** Zhou, Aitio, Howey, *Applied Energy* (2025), DOI [10.1016/j.apenergy.2025.126375](https://doi.org/10.1016/j.apenergy.2025.126375)。实读作者 [arXiv:2407.06639 全文 HTML](https://arxiv.org/html/2407.06639)，2026-09-29；以作者稿章节定位，期刊版差异未逐页核。E1，核 §2–5、Algorithm 1、图 4–9、附录 D。

**数据/标签/划分。** 单芯 A：NMC/石墨 0.25 Ah，30°C、100% DoD；单芯 B：NCA/石墨硅 3.4 Ah，25°C、10–90% SOC。运行放电 0.2/1 Hz；每芯抽取 15/18 个跨寿命事件，前 10 事件调 GP 超参数，其后在**同一芯**做短期外推。BoL RPT 提供 OCV-SOC 曲线，后续定期 RPT 容量只用于核对；每段起点 SOC 根据已测初始状态重置。没有 LFP、四串、未知起始 SOC 或跨芯盲测。§3.1–3.2。

**方法/结果。** `z_dot=-I/Q(age)`、`V=OCV_BoL(z)-I·R(z,I,age)`；`1/Q` 与 `R` 分别为有先验 GP，状态空间 GP 与 EKF 联估，似然优化超参数。温度受控，未作为本次输入。图 4–5：A 容量估计 RMSE 0.0026 Ah、MAPE 0.86%，外推 0.0038 Ah、1.53%；B 分别 0.0122 Ah/0.31%、0.009 Ah/0.27%。作者指出 A 后段退化加速使线性趋势外推变差。附录 D 随机游走对照 A/B RMSE 0.129/0.019 Ah，不可把两个体系误差按百分比与本题比较。

**识别冲突与竞赛判断。** 固定 BoL OCV 时，所学“电阻”含老化 OCV 形状变化；§4.2 式(27)–(28)、图 7 用新 RPT 曲线核对，作者明确仅凭端电压不能分开 OCV 漂移与纯电阻。§4.3 的虚拟 DVA 可追趋势，但缺半电池数据无法确定峰对应电极；它是模型代理，非直接测到 LLI/LAM。可迁移时间尺度分离、质量门控与新鲜锚点，但需要真 SOC/OCV 起点及可观测窗口。最小实验：在有标签 LFP 上固定 BoL OCV，比较允许 OCV 漂移的替代模型，检验参数剖面和末期误差；若容量与偏置/阻抗互相替代，则拒绝将单模型 Q 当直接容量证据。


## 14．B_card_Aitio2023｜Learning Battery Model Parameter Dynamics From Data With Recursive Gaussian Process Regression

来源卡：`notes/workstreams/B_card_Aitio2023.md`。书目身份：`10.1115/1.4067771`。


- 书目：Aitio A, Jöst D, Sauer D U, Howey D A. Learning battery model parameter dynamics from data with recursive Gaussian process regression. 作者 arXiv:2304.13666v1（2023），后刊 Journal of Dynamic Systems, Measurement, and Control 147(3):031010（2025），DOI 10.1115/1.4067771。2026-09-29 获取完整 16 页作者稿 papers/B_sources/Aitio2023_arxiv.pdf，SHA256 a3607c9db401e4d6efdadb959cade5542f400a52335352be6401abae7286f482；书目由 RWTH 出版记录核实，数值按 v1。[稿](https://arxiv.org/pdf/2304.13666)；[机构书目](https://publications.rwth-aachen.de/record/1010025)。
- 研究/实体：合成参数可辨实验，及两枚 Samsung INR18650-35E NCA/石墨硅 3.45 Ah 单芯、25°C，10–90% SOC，0.3C CCCV 充与约 0.4C 动态放电，30 次循环一个检查。每检查的独立容量真值是满充后 0.3C 放电；另有脉冲电阻真值（PDF 第 7–8 页 §VI）。初始 OCV 由 0.02C 全放电测得；热容来自文献，热阻用初期温度恢复拟合。温度仅约 5°C 小范围，不能据此确认多温域泛化。
- 方法：一阶 RC 加热模型，逆容量 Q⁻¹(age)、R0(z,I,age)、RC 参数 α(z,age)、β(z,age) 各用 GP，年龄用非平稳 Wiener velocity 核，短波动用指数核；EKF 联合状态/参数，后向 RTS 用于历史平滑（图 1，式 9–16、31–33，PDF 第 3–5 页）。GP 长期先验、初始 OCV、热参数、核超参数都是真实额外信息；算法名称并不能消除单锚点辨识问题。
- 训练/验证：两枚单芯共享超参数；每 30 循环只取最后一次动态放电，插值为 1 Hz；初始一段 14,597 行估 SOC/电流核超参数，再以约 288,639 行内样本估年龄核参数，末 8 组检查外推，内样本是 19/20 个放电段（PDF 第 8–9 页）。未来外推段不可同时视为前向电压过滤训练。未见物理芯留出；两芯不代表独立群体验证。
- 指标/核查：图 5 与表 II 报两芯容量与电阻拟合/外推，文中总结平均容量误差约 0.016 Ah、电阻约 1.7 mΩ（第 9–10 页），不是本题 SOH pp；容量/R0 的验证点来自独立检查，温度和容量协议不一致。合成表 I 的参数 RMSE 在已知生成模型下，不是实测识别保证。作者承认 R1/C1 的物理解读因时标混合而不直观（第 9 页）。
- 竞赛前提：本题 10 s 稀疏运行与缺段可用 GP 传播不确定性；但没有 0.02C OCV、定期 0.3C 容量标签或两芯校核，且 25/45°C 热变化大。将作者后向 RTS 估计回填到早月会见未来；在线须只前向滤波并按检查点冻结超参数。
- 最小反证：以官方 CK0 曲线作弱先验，在实际 10 s 片段上比较一参数年龄 GP 与固定容量模型的 held-out 电压以及容量剖面区间；若不同 Q 可由初始 z/OCV/极化拟合到同等残差，不允许宣称容量被识别。E2 原文方法/表图核对；未运行或复现。


## 15．B_card_Gasper2025｜Searching for a Pulse: Evaluating the Use of Rapid DC Pulses for Diagnosing Battery Health, State-of-Charge, and Safety

来源卡：`notes/workstreams/B_card_Gasper2025.md`。书目身份：`10.1149/1945-7111/addd50`。


- 书目：Gasper P 等. Searching for a Pulse: Evaluating the Use of Rapid DC Pulses for Diagnosing Battery Health, State-of-Charge, and Safety. Journal of The Electrochemical Society 172(6):060503, 2025. DOI 10.1149/1945-7111/addd50。2026-09-29 下载美国能源部 OSTI 开放正式 PDF（papers/B_sources/Gasper2025_OSTI.pdf，SHA256 792051d371b52958a2dcb8f73fc570f0ae33b1c40644e1ce8e3cc688e4d9eee1），16 页；原文第 15 页给代码/数据公开信息，仓库/数据未运行。[全文](https://www.osti.gov/pages/servlets/purl/2584011)；[机构书目](https://research-hub.nlr.gov/en/publications/searching-for-a-pulse-evaluating-the-use-of-rapid-dc-pulses-for-d/)。
- 物理实体：表 I（PDF 第 5 页）四类逐行列 A 16 枚 64 Ah NMC/石墨软包，B 8 个 66 Ah LMO/石墨软包模块，C 21 枚 26 Ah NMC/石墨棱柱，D 30 枚 2.3 Ah LFP/石墨圆柱；逐行相加 75，但表的 Totals 栏写 79，属于原表内计数矛盾，不能默默引用“79 独立电芯”。四行测试次数 49/28/94/84 相加 255，Totals 栏写 259，同样差 4；脉冲四行和 47,906 与表总数一致。若按逐行清单研究，本卡用 75 个列出的物理实体，保留作者总数 79 的不确定性。多个脉冲不等于同数独立实体。三温 15/30/45°C，含实验室继续老化以补容量分布（第 3–6 页）。
- 标签/输入：每次约 6 天全面表征，CCCV 全充后 C/10、C/5、C/3 等放电形成容量真值，另测 US06 吞吐、FCR 效率及安全代理；脉冲在已知 SOC 的不同位置、温度和电流下，静态 HPPC 为 10 s 放/40 s 静/10 s 充，快速 16 s 或随机 120 s；另有动态脉冲。特征为 I、V、T、初始电压减去后的极化，全脉冲均须已有结束信号；作者以 XGBoost 分别监督目标（第 3–5 页图 1）。
- 验证：50 次随机 80/20 表征测试分割，按一次 characterization test 分组，使同一次测试的多个脉冲不跨训练/测试；但没有明确按物理芯整寿命隔离，因此同芯不同检查可能两侧出现。作者报告 120 s 脉冲容量 MAPE 约 2–9%，可做高/低容量筛选但不足精确寿命估计（第 3、9–10、15 页图 6）。不同电芯种类分开训练，指标单位是相对 C/3 容量误差，不是本题 C/20 四串 SOH pp。低容量样本对部分类型有系统高估（图 8）；高 SOC/温度和倍率分布被模型监督学习，不能以单一 CK0 自动获得映射。
- 公式/机制检查：短脉冲 ΔV/I 是工作点、温度、SOC 与快慢极化混合。动态脉冲还改变 SOC 与 OCV，因此优于零净电量静态脉冲的可能信息源不限电阻（第 11 页图 7 及讨论）。作者图 4/6 比较 DCIR 与容量，非一一映射；若模型仅有一次容量锚点，训练映射的自由度不可从本题数据重建。不能把“脉冲可监督预测容量”降为“脉冲只看阻抗”，也不能照搬 2–9% 为比赛期望。
- 反证/适配：官方 20 A×30 min 单向放电为约 0.2C、10 s 采样、约 10 Ah，非作者 1–2C HPPC/PsRP；好处是有更大 Ah 漂移，但起始 SOC/温度/充后静置不同。LFP 作者仅小圆柱，B 为 LMO 模块，拓扑/尺寸外推待证。最小实验：匹配起始温度、OCV/初始电压、积分 Ah 和事件序列，测试脉冲残差在 D2 独立组的容量标签上是否带来超越同输入年龄+温度+CK0 基线的增量；按组/事件 bootstrap，非逐芯脉冲切片 bootstrap。E2 原文图/表/分割核验，未复跑。


## 16．B_card_Schaeffer2024｜Gaussian process-based online health monitoring and fault analysis of lithium-ion battery systems from field data

来源卡：`notes/workstreams/B_card_Schaeffer2024.md`。书目身份：`10.1016/j.xcrp.2024.102258`。


- 书目：Schaeffer J, Lenz E, Gulla D, Bazant M Z, Braatz R D, Findeisen R. Gaussian process-based online health monitoring and fault analysis of lithium-ion battery systems from field data. Cell Reports Physical Science 5 (2024) 102258. DOI 10.1016/j.xcrp.2024.102258。2026-09-29 访问正式开放论文的作者存档 PDF（本地 papers/B_sources/Schaeffer2024_author.pdf；SHA256 8bc9fd005e1d606529b033f944f4186593f1ca39fb4dfa8c17b990bac7d0d819），另核正式出版页、Zenodo 数据 README 与 GitHub 代码。论文 CC BY；数据 CC BY-NC 4.0；代码仓库 LICENSE.txt 为 BSD-3（README 顶部盾牌写 MIT，需以许可证文件为准）。[论文](https://doi.org/10.1016/j.xcrp.2024.102258)；[作者 PDF](https://web.mit.edu/braatzgroup/Schaeffer_CellRepPhysSci_2024.pdf)；[数据](https://zenodo.org/records/13715694)；[代码](https://github.com/JoachimSchaeffer/BattGP)。
- 研究对象与新增：28 个退回厂家、有不满意表现的便携系统，每个约 160 Ah、8 个棱柱 LFP 芯串联，有主动均衡；论文表 1（PDF 第 5 页/期刊第 4 页）为 224 芯、133M 行、间隔中位数 5 s，1 个组电流传感器、9 个电压、4 个共享温度、8 个均衡电流传感器。系统是有选择偏差的保修退回样本，使用工况不明且有缺口（PDF 第 4–5 页）。
- 标签/协议：全文没有各系统定期 C/20 或任何逐期参考容量的训练/验证表。SOC 为系统记录/估计的工作点变量；论文输出是工作点修正的等效电阻趋势与异常概率。不是本题容量 SOH 的直接真值。论文曾说数据可用于未来 SOH 研究（第 4 页），不能据此声称它已经验证了容量映射。
- 方法链：以电流、SOC、温度为工作点，把等效串联电阻分为平滑工作点函数和随时间变化函数；后者 Wiener velocity 核编码退化趋势。低自由度线性近似 LFP OCV 后，以电压残差识别电阻；精确 GP 用选取的 40,000 点，递归时空 GP 用基向量、前向 Kalman 更新，部分图另用后向 RTS 平滑。电阻超过同组其他芯的稳健参考带后形成逐芯/组异常概率（PDF 第 8、12、17–20 页，图 4、式 3–9、19–25）。随机窗口与模型超参数的范围需按系统控制：论文第 20 页在系统 6、8 的各芯选 20,000 点求超参数中位数；不可称 28 系统均为完全留出验证。
- 公式检查：以放电电流绝对值 I、估计 OCV U(z) 表述，电压残差约为 I[R_work(I,z,T)+R_age(t)]；故障量 P(R_i>同组带宽) 的单位/目标是 Ω 的阈值事件，不是 Ah。若 U(z) 或老化 OCV 漂移 δU，等效电阻偏差约 δU/I，低电流特别病态。作者明确承认近似 OCV 会偏置电阻（PDF 第 8 页）；季节低温在系统 8 的年龄项仍造成假升高（第 10、14 页）。
- 代码/数据核验：2026-09-29 GitHub main=6d5e1db3337f0de5f3a533acbc09eddccc178e9d；README 两种模式 full_gp 与 spatio_temporal，gp_runner.py 为论文重算入口，src/batt_models/fault_probabilities.py 计算异常，src/batt_data/data_columns.py 有 SOC_Batt、逐芯电压等；未发现容量标签估计器。三个版本计数需分开：arXiv:2406.19015v3 摘要为 29 系统/232 芯/131M 行，且 arXiv 页面标为过时版本；正式论文第 2 页摘要及第 5 页表 1 为 28/224/133M；Zenodo v1.0.0 README 是 28/232/133M，但同一 README 亦说每系统 8 串，28×8=224。Zenodo README 可能遗留旧芯数或包含未解释附加实体，未下载 1.7 GB ZIP 不能裁定其实际列。报告应采用正式论文 28/224/133M 并标注 README 冲突，不能把作者稿的 29/232/131M 与正式结果混用。
- 最强证据与局限：图 5 与图 6–7 显示同系统芯间电阻差和故障概率变化；作者同时记录季节温度与工作点覆盖导致的年龄趋势偏差。论文未报告以容量 SOH 为目标的 MAE、RMSE、末期误差，也无与本题同协议对照。
- 竞赛适配：可迁移缺口处理、工作点匹配、逐芯相对异常/质量门控及前向不确定性；不能把电阻增长量或故障概率直接映射到 5.1 A 至组端 11.2 V 的组容量。官方四串无均衡电流字段、SOC 也非可核真值，需另估并传播误差。禁止把离线 RTS 后向平滑用于历史检查点的因果预测。
- 最小反证：在有独立逐次容量真值的 D2 组数据，固定训练域并按物理组留出，比较 CK0 保持、吞吐量/温度基线与电阻特征增量；控制 SOC/温度/电流窗口，若增量对组端 C/20 容量无可重复改善，电阻只作诊断。核验等级 E2：原文表/式与代码/README 静态核对；未运行作者模型或确认容量性能。

**样本资格补充（独立审查）**：正式论文全数据描述为 28 个返修系统/224 芯；电阻模型分析另筛出运行超过 100 天且至少 2,000 个有效点的 **21 个系统**（正式 PDF 第 8 页）。28 是数据覆盖，不可当作每个模型结果的独立样本数。


## 17．B_card_Shi2026｜An adaptive estimation approach based on fisher information to overcome the flat voltage plateau challenges of SOC estimation in LFP batteries

来源卡：`notes/workstreams/B_card_Shi2026.md`。书目身份：`10.1016/j.egyai.2026.100693`。


- 书目：Shi J, Jiang S, Tao S, Lee J, Borah M, Moura S. An adaptive estimation approach based on Fisher information to overcome the flat voltage plateau challenges of SOC estimation in LFP batteries. Energy and AI 24 (2026) 100693, DOI 10.1016/j.egyai.2026.100693。核对 arXiv:2507.01173 作者稿完整 31 页（papers/B_sources/Fisher2025_arxiv.pdf，SHA256 2da2eab2b403538643dc10109c3486f85aa0e502eb59969535e719206ff178df）与 Chalmers 机构出版稿元数据；数值按作者稿。2026-09-29 访问。[作者稿](https://arxiv.org/pdf/2507.01173)；[机构正式稿](https://research.chalmers.se/publication/551220/file/551220_Fulltext.pdf)。
- 对象/真值：LithiumWerks APR18650M1-B 1.2 Ah LFP 单芯，25/10°C，专门 1/50C 双向 OCV–SOC–滞后映射和 HPPC，1 Hz 采样，在 UDDS 等动态电流与偏置/量化/低温/平平台测试；“真值”SOC 从已知容量积分/受控设定，非后续容量 SOH 标签（PDF 第 7、12–13 页）。无四串组容量验证、无老化容量更新目标。
- 方法：二阶 ECM 在线估 OCV，按充放方向更新滞后因子 H，以已标定的三维 U(z,H) 反演 SOC；电压对参数灵敏度构造 Fisher 信息，再以逆斜率和估 OCV 协方差形成 SOC 更新置信度，与库仑计数融合（第 4–12 页图 1、式 11–19）。100 s/1 Hz 窗长由场景调试。公式量纲：若 U 的斜率 a=dU/dz [V/无量纲 SOC]，SOC 方差近似 Var(U)/a²；a→0 则增大。Fisher 矩阵受电流激励与噪声协方差影响；必须看整矩阵条件数，单项大不足以证明 Q 可辨。
- 原文条件/边界：库仑传播式直接用事先已知容量 C_b（PDF 第 11 页 §SOC fusion）；因而 SOC RMSE 如平平台 20–80% 场景 2.54% 对 UKF 6.69%（第 15 页图 11）只验证状态门控，不验证未知容量估计。作者第 22 页承认电压测量偏置仍是限制，和 Yi 的偏置专门处理形成互补证据。
- 竞赛适配：可把低 OCV 斜率、低激励、高滞后不确定性的窗降权，并将累计 Ah 继续前向传播；不能用该论文的 SOC 数值误差作为容量 SOH 精度。官方 10 s 使 1 Hz 频域参数与 100 点窗口需重新设计；CK0 动态曲线不足以单独生成零流三维滞后图。最小反证：在实际 10 s 前缀以多组 Q/初始 z/电压偏置计算条件 Fisher 矩阵与 held-out 电压；若 Q 列近线性依赖，即使 SOC 滤波稳定也冻结 Q。E2 原文公式/验证目标核对，未数值复现。


## 18．B_card_Zhang2011｜Cycling degradation of an automotive LiFePO4 lithium-ion battery

来源卡：`notes/workstreams/B_card_Zhang2011.md`。书目身份：`10.1016/j.jpowsour.2010.08.070`。


- 书目：Zhang Y, Wang C-Y, Tang X. Cycling degradation of an automotive LiFePO4 lithium-ion battery. Journal of Power Sources 196(3):1513–1520, 2011. DOI 10.1016/j.jpowsour.2010.08.070。2026-09-29 读取作者 Penn State 完整 8 页 PDF，papers/B_sources/Zhang2010_PSU.pdf（文件沿作者站年份命名；实际发表 2011），SHA256 601c4a2c91fdf9b758a3ab8a5284c5fb515d984af44e7e653dd242950f5ddda5。出版社版权，作者稿仅本地研读；代码/逐点数据未见。[作者 PDF](https://ecec.me.psu.edu/Pubs/2010-Zhang-JPS.pdf)；[机构书目](https://pure.psu.edu/en/publications/cycling-degradation-of-an-automotive-lifeposub4sub-lithium-ion-ba/)。
- 实体/实验：一枚 16.4 Ah LFP/石墨棱柱，50°C 下 3C 充放、2.0–3.6 V 深循环 600 次；初始、300、600 次在 45/25/0/−10°C 表征。每温 1C CCCV 满充（CV 到 C/20）后静置 10–40 min，再 1C 至单芯 2.0 V，得容量真值；EIS 在 70% 当前容量 SOC、静置 1 h，2 mV、5 kHz–0.005 Hz；2C 脉冲 2/10/30 s 带短恢复（PDF 1514/第 2 页 §2）。样本仅 1 芯、三寿命点，无统计群体验证。
- 公式/协议：脉冲电阻 R_dis=(V_before−V_end)/(I_after−I_before)，单位 Ω，随脉冲长度混入不同极化时标（PDF 1516/第 4 页式 1、图 5–6）；其参考 OCV 是脉冲前静置电压，10/30 s 脉冲前 OCV 还沿用 2 s 的值，作者明确承认缺足够恢复。EIS 的高频截距、半圆与扩散尾分别是不同过程，并非总容量的代数函数（第 5–6 页图 8–10）。
- 原文结果：600 次后相对各温初值的 1C 放电容量损失分别为 45°C 14.3%、25°C 15.5%、0°C 20.3%、−10°C 25.8%（第 3–4 页图 3–4）。45°C 同寿命虽容量损失 14.3%，30 s 脉冲电阻由 2.4→4.8 mΩ，脉冲功率能力因电流上限仍几乎无下降；0/−10°C 功率衰减大（第 4–5 页图 6–7）。因此“容量”和“脉冲功率/电阻”对温度、截止和负载反应不同；作者提出 LLI 主导容量、界面/电解液阻抗主导功率的机理解释，非逐芯因果鉴定。
- 限制：本实验 1C 容量到单芯 2.0 V，不是官方 5.1 A≈0.05C 至四串 11.2 V；50°C 深循环和 25/45°C 运行亦不同。结果支持温度/协议匹配的重要性和阻抗不可直接换算容量，不能凭一芯证明所有 LFP 中二者无关联。
- 最小反证：在 D2 或新增组 RPT 中同芯同温同 SOC 测 2/10/30 s 与实际 30 min 脉冲、同时测官方组端 C/20 容量；做温度、年龄、Ah 吞吐控制后的留组残差检验。若在独立组中电阻提供稳定额外容量信息，可升级受限监督特征；若只反映工作点，则保留异常门控。E2 原文公式、表图核对，未复现。


## 19．C_Arunan2025_SSL｜Learning More With Less: A Generalizable, Self-Supervised Framework for Privacy-Preserving Capacity Estimation With EV Charging Data

来源卡：`notes/workstreams/C_evidence/C_Arunan2025_SSL.md`。书目身份：`10.1109/TII.2025.3613385`。


- 书目：Arunan et al., IEEE *Transactions on Industrial Informatics* 接收作者稿，DOI [10.1109/TII.2025.3613385](https://doi.org/10.1109/TII.2025.3613385)，[arXiv:2510.05172](https://arxiv.org/abs/2510.05172)。2026-09-29 读 12 页作者全文 `papers/C_fulltexts/C_Arunan2025_SSL.pdf`；版权页注明 IEEE 作者稿仅个人用途。本地仅研究核读，不再分发正文。
- 问题与数据：真实 EV 充电站碎片数据，三家匿名厂商；每片有电流、电压、温度、BMS SOC、里程，部分片有厂商参与形成的容量标签。论文 Section II 说明标签稀缺，但没有把每条容量标签测量协议和 SOH 分母披露到足以匹配官方 C/20 截止；表 A.1 按 EV 物理实体分割。主设置 Manufacturer 1 D1 预训练平均 23 车/54,234 片，验证 3 车/6007 片；微调用 2 车/4663 片，测试 6 车/13,584 片，数字是五个随机划分平均值。每车多片不是独立组。
- 方法：编码器将短时间序列映射到表征，用原片/掩蔽片对比损失和相似性加权重建（式 3–5）；有标签片上回归头平方误差（式 8）。这提供无容量标签的形状/工况表征，**不自动提供容量尺度**。该数据有里程和 BMS SOC，可能形成寿命与位置代理；官方是否有同等级 SOC 列需逐字段核对。
- 划分/结果：Appendix Table A.1 明言 70/10/20 车级预训练/验证/测试分割，微调仅预训练车的 10%；五次随机划分。Table II–V 有域内/跨龄/跨厂 RMSE，摘要的 31.9% 是对其最优基线的相对测试误差下降，不是官方容量 pp。预训练数据变体增加无标签片亦改变数据覆盖，须与预训练目标的贡献拆开。
- 适配/反证：可试官方训练前缀的掩蔽电压/电流重建，或外部异协议片预训练；但需先锁每个目标组/时点的可见前缀，消融隐藏时间戳、里程/吞吐量、SOC、温度、片长度和未来片。对照为同输入线性/树/随机初始化编码器，并在全新物理组上评估。若提升只来自寿命代理或目标未来无标签片，即不能称可部署容量信息。
- 作者代码静态核查：[`GenEVBattery`](https://github.com/en-research/GenEVBattery) 提交 `f058ff133724ff6bab5073d8c4bbaf5b42f21dda`。`README.md` 说明数据源为 He et al. 的 EV 数据 V3，按厂商/里程构建分布；`run.py` 的范例 `ft_data_subset=0.1`；`data_provider/data_loader.py` 仅从预处理 `seed_flag.pt` 读取 `samples`/`labels`；`data_provider/data_factory.py` 指向 `dataset1_combined_car_mileleq100k` 预训练与 `dataset1_car_mileleq100k` 微调路径。仓库没有原始到 `.pt` 的划分脚本，`dataset/readme.txt` 要求另下网盘预处理数据。因此车级不相交仍依赖论文附录陈述，无法仅凭公开代码独立复核；预训练/微调数据重叠与时间因果亦须在官方实验重新审计。
- 核验等级：E2 全文公式、附录划分与作者代码静态核对；容量标签测量协议和预处理生成脚本仍有公开缺口。未运行训练。


## 20．C_Che2023_Continual｜Increasing generalization capability of battery health estimation using continual learning

来源卡：`notes/workstreams/C_evidence/C_Che2023_Continual.md`。书目身份：`10.1016/j.xcrp.2023.101743`。


- 书目：Che et al., “Increasing generalization capability of battery health estimation using continual learning,” *Cell Reports Physical Science* 4 (2023) 101743, DOI [10.1016/j.xcrp.2023.101743](https://doi.org/10.1016/j.xcrp.2023.101743)。2026-09-29 读 [Stanford 作者正式稿 PDF](https://pangea.stanford.edu/ERE/pdf/OnoriPDF/Journals/75.pdf) 21 页，存 `papers/C_fulltexts/C_Che2023_Continual.pdf`；核 [Mendeley Dataset v9 DOI 10.17632/n3b54nsw8m.9](https://data.mendeley.com/datasets/n3b54nsw8m/9) 原始说明与本地 MAT 字段。文章开放访问；数据 CC BY 4.0。
- 数据/标签：论文共 55 枚商用 pouch/prismatic，跨五个数据组与 116,000 余循环；Dataset 3/4 为约 **100 Ah LFP 单芯**，不同充电倍率和环境温度，非四串。文中 Methods“Data generation”定义 SOH=当前可用容量/新鲜容量；Mendeley v9 更精确地说明标签来自测试仪**同循环全充入量**归一化，并警告 Dataset 1 的充电容量含动态放电中的充电脉冲。这与官方 `C/20 组端放电 Ah /102 Ah` 不同。本地 `Che-Dataset3.mat` 11 个实体，`Dataset3` 字段 `Capacity, Workingprofile, cell, cycles`，各 `cycles` 下 `Partial_Q, Partial_dQ`；首芯 `Capacity` 长 3024、值约 80.6–107.7，应按来源归一化量解读，绝不能按 80–110 Ah 直接称容量。局部 Q 为 101 点派生曲线；本地 MAT 没有原始时间/电流/电压/温度列或明确电压网格。
- 方法：从固定电压窗内部分充电 Q–V 序列插值（LFP 3.3–3.5 V，2 mV 间隔，Methods），两层前馈网络；源芯标签 MSE、域间 MMD、目标芯早期少量标签的记忆更新。作者 Fig. 1/3/5 显示不同温度倍率适配；目标实体的**3 个早期容量标签**（首 10% 老化）或持续获得的稀疏标签是实际信息预算，明显强于官方 CK0 一点。只有无标签 MMD 不能单独提供官方容量刻度。
- 划分/数值：Dataset 3 以 1C/25°C cell 2 或 1C/35°C cell 6 做基模型，再向其他单芯工况迁移（Fig. 3E/F、Fig. 5）。摘要报跨动态电流/温度 RMSE 1.312%，但并非只用一容量锚，也非同一 4S 容量定义。多窗口/循环误差应按电芯聚合，不能用 114,741 条记录当独立对象。特定 target 的早期少标签和无标签序列何时进入更新，必须在官方严格前缀下重构。
- 适配/反证：可借固定窄窗插值、MMD/记忆更新结构、跨温开发思路；但比赛没有目标隐藏容量标签可持续更新，本地 Che 也缺原始波形与组端数据。最小实验：只给留出目标实体一枚 CK0 类锚点，冻结窗口/归一化/预训练，严格按时间前缀与同输入不适配基线比；若收益依赖 3 个早期容量标签或完整寿命无标签分布，则不能上升为官方主路线证据。
- 核验等级：E2 论文全文 Methods/Fig. 3/5、Mendeley v9、代表 MAT 字段交叉检查；未运行作者算法。数据资格为异协议单芯迁移/形状开发，非 D2 四串确认。


## 21．C_Fragmented2025｜Data-driven available capacity estimation of lithium-ion batteries based on fragmented charge capacity

来源卡：`notes/workstreams/C_evidence/C_Fragmented2025.md`。书目身份：`10.1038/s44172-025-00372-y`。


- 书目：*Communications Engineering* 4 (2025) 32, “Data-driven available capacity estimation of lithium-ion batteries based on fragmented charge capacity”, DOI [10.1038/s44172-025-00372-y](https://doi.org/10.1038/s44172-025-00372-y)。2026-09-29 读出版社开放 PDF 11 页与 HTML Methods，`papers/C_fulltexts/C_Fragmented2025.pdf`；出版社注明数据和代码须向通讯作者申请，故未复现。
- 数据/标签：Table 1 四个 LFP/石墨单芯库：VALENCE 4 芯、2.5 Ah、11,500 周期样本（1C 充/4C 放）；HUAWEI 4 芯、280 Ah、4574 样本；GOTION 3 芯、27 Ah、4262；A123/MATR 50 芯、1.1 Ah、32,800。可用容量取相应循环 CC 放电容量（Fig. 1），不是官方 4S、C/20 组压截止容量。11,500 是窗口/循环样本，主实验仅 4 个物理实体。
- 方法：从**完整 CC 充电曲线后验分段** 3.0–3.6 V 的 11 个固定电压窗，对各窗积分 `ΔQ_j=∫_{V_j}^{V_{j+1}} I dt`；Pearson 筛选并组合 1–2 个特征，LASSO/XGBoost/LightGBM 预测同循环放电容量。跨循环组合需先说明每个输入在预测时已发生（Results Feature extraction / Fig. 3–4）。温度、起始 SOC、电流和切窗阈值影响可比性；若一段不存在，不能用未来完整曲线补齐。
- 划分/结果：Methods 明确 VALENCE #1–3 训练、#4 测试，标准化在划分后；主库最优 RMSE 0.012（原文表/图以其目标量报告，勿改称官方 pp）。跨域 #2/#3 先零样本，再用目标域标签微调；Table 3 某目标 #4 RMSE 0.034，换窗特征改善到 0.016 却使其他目标变差，提示窗选择容易按目标测试集优化。Supplementary Note 3 的具体微调标签数量本轮未核到，不能称一锚点迁移。
- 竞赛判断：证明在有重复完整 CC 曲线且同协议容量标签时局部 Ah 可承载容量信息；不能证明任意 20 Ah 浅充、未知初始 SOC、25/45°C 混合下窗口仍有相同映射。最小反证：按真实浅充事件而非深循环后裁剪，冻结窗口阈值与归一化，只用前缀，留出物理芯/温度，比固定宽窗、年龄/吞吐量基线；若有效窗缺失或性能随起点变动即降级。
- 核验等级：E2 出版 PDF Table 1/Fig. 3–4/Methods 和网页逐项对照；未获取底层数据、未运行代码。


## 22．C_Ispizua2026_PINN｜Real-Time State-of-Health Estimation and Online Degradation Prognosis from Partial Battery Discharge Using Physics-Informed Neural Networks

来源卡：`notes/workstreams/C_evidence/C_Ispizua2026_PINN.md`。书目身份：`arxiv:2608.14764`。


- 书目：Ispizua et al., “Real-Time State-of-Health Estimation and Online Degradation Prognosis from Partial Battery Discharge Using Physics-Informed Neural Networks,” [arXiv:2608.14764](https://arxiv.org/abs/2608.14764)。2026-09-29 读 22 页预印本 `papers/C_fulltexts/C_Ispizua2026_PINN.pdf`；正式发表/代码状态未核。
- 数据/目标：Section 2.1 明确复用 Severson et al. (2019) 快充集，122 枚标称 1.1 Ah、3.3 V 单芯，统一 4C 放电至 2 V，不同快充策略；该原始集为 A123 石墨/LFP。10 枚专用于验证/测试（Section 3/Conclusions 表述有别）。每条完整放电曲线用 Kneedle 寻找拐点，取对应容量当**SOH 指示量**（Results p.12），这个由算法生成的目标不等于官方至 11.2 V 放电积分 Ah。它与其他 MIT/Severson 论文共享原始数据，不可算独立重复。
- 方法：先按电压把完整放电曲线后验切成 8 类，每片固定 5% 额定容量跨度；分类器选类，类内特征选择，然后每类单独训练 FNN 加 Verhulst 型物理残差，参数 `r,K,C` 在训练中自由学习（Section 2 / Results p.12–14）。物理约束是经验退化轨迹形状，未给定从四串浅充波形到组端容量的守恒识别。
- 结果/划分：10 个验证芯与其余训练芯分开；Table 4 各电压片 FNN/PINN 对比，摘要 MAPE <4%。片段从同一完整放电构造，所以“任意片段”主要是**已覆盖完整曲线的后验裁剪**，不是自然到达的未知起点浅循环。99% 电压片分类精度来自相对均质的实验芯（Results p.12），与容量误差是两种指标。
- 适配/反证：借片段质量门控/分窗模型和经验损失做候选；但官方多为充电、四串、温变、真实缺窗。最小反证：仅真实浅充事件、禁止未来完整曲线选窗，在同输入外层留出组上，按组比较纯 FNN 与物理残差及简单双变量基线；若只在后验裁剪获益，路线不可部署。
- 核验等级：E1 原文 Section 2/3、Table 4、Conclusions；未数值复现。SOH 的作者指标来自放电拐点，虽然论文式 (2) 形式为 `Q_act/Q_nom`，不能误称全放电至截止的实际容量。


## 23．C_Richardson2017_GP｜Gaussian process regression for forecasting battery state of health

来源卡：`notes/workstreams/C_evidence/C_Richardson2017_GP.md`。书目身份：`10.1016/j.jpowsour.2017.05.004`。


- 书目：Richardson, Osborne, Howey, *Journal of Power Sources* 357 (2017) 209–219, DOI [10.1016/j.jpowsour.2017.05.004](https://doi.org/10.1016/j.jpowsour.2017.05.004)。2026-09-29 读开放作者 PDF [arXiv:1703.05687](https://arxiv.org/abs/1703.05687)，本地 14 页 `papers/C_fulltexts/C_Richardson2017_GP.pdf`；出版页标开放许可。作者稿与正式版具体排版可能不同，页码按本地 PDF。
- 问题：**已知前期容量轨迹**时如何预测未来容量和 EOL、传递电芯间相似性并表达模型不确定性。作者在第 1 页/Introduction 明确“capacity forecasting”与当前容量测量是不同任务，假定周期容量已可得。不是单 CK0 从运行电压识别容量的实验。
- 数据与标签：NASA 等容量—循环曲线，文中数据集 A/B/C；A 为 NASA 单芯固定充放，C 为 NASA 随机负载 LG 18650；B 从既有论文图中抽取。样本主体是单芯容量复测曲线，非 LFP 四串组。B 的图像取点又引入额外测量误差；所有容量分母、倍率跨数据集不可合并。Section 3 / Fig. 1、附录数据说明。不同窗口/循环点不增加物理芯数。
- 方法：`Q(n)=m(n)+f(n), f~GP(0,k)`；核由不同平滑尺度 Matérn 组合，边际似然选核；显式退化均值函数是先验。多输出核 `K((n,i),(n',j))=k_time(n,n') B_ij` 从其他芯容量曲线学习相关。该先验可减少目标芯早期轨迹点需要量，但若仅有 CK0 且目标运行条件不同，后验主要仍由源芯先验支配。Section 2、Fig. 8。
- 划分/结果：Fig. 8 的目标芯 C3 前缀容量与其他芯完整容量轨迹共同训练；C1/C2 与 C3 的相似性决定收益。作者自陈这些芯有相似随机负载条件，跨工况大库需额外验证。Fig. 8 文本给 C1 辅助时 EOL RMSE 18.1 days、C2 时 4.86 days；这只是该组预测对照，不能转为 SOH pp。
- 适配/反证：可借 GP 对潜在容量趋势作单调/变点先验与不确定性，但没有后续容量标签时，区间是先验条件化结果，不可声称校准覆盖。需要相同或受限迁移的多组容量数据和独立目标组外层测试。最小反证：只给目标 CK0，比较 GP 与固定年龄/吞吐量先验；对留出组末期容量检查 MAE 和区间覆盖，若 GP 无增益就降级为平滑先验。
- 核验等级：E1 原文方法与 Fig. 8；未复现代码/数值。没有把作者报告的未来容量预测当作在线容量识别。


## 24．C_Richardson2019_GPTransition｜Battery health prediction under generalized conditions using a Gaussian process transition model

来源卡：`notes/workstreams/C_evidence/C_Richardson2019_GPTransition.md`。书目身份：`10.1016/j.est.2019.03.022`。


- 书目：Richardson, Osborne, Howey, *Journal of Energy Storage* 23 (2019) 320–328, DOI [10.1016/j.est.2019.03.022](https://doi.org/10.1016/j.est.2019.03.022)。2026-09-29 读 [arXiv:1807.06350](https://arxiv.org/abs/1807.06350) 10 页作者稿，本地 `papers/C_fulltexts/C_Richardson2019_GPTransition.pdf`；正式版开放访问。页码用作者稿。
- 问题与数据：将两次**已测容量**之间的不等长电流/电压/温度运行片段变成固定维度负载直方图，再预测容量增量和外推不确定性。NASA 随机负载 28 枚中用 26 枚（排除 16/17 数据时间异常）；7 个工况组，每组约 4 枚。950 条周期参考曲线，约每芯 34 条；原文第 6 页先称 2 A 参考**放电**曲线，下一句却称积分 2 A **充电**曲线，来源内有歧义；在核 NASA 原始协议前不锁定标签积分方向。Section 3、Table 2/3。它是单芯 NASA 异化学/小容量集，不是四串 LFP。
- 方法：设 `ΔQ_k=g(h(I,V,T)_{k:k+1},Δt,Q_thru)+ε`，`g` 为 Matérn GP；递推 `Q_{k+1}=Q_k+ΔQ_k`。Table 4 比较核、滞后、时间和吞吐量特征。特征必须只从相邻已观测运行段提取；目标起点容量及多条训练容量变化是不可省的监督。未来负载未知时不等于可预言未来容量。
- 划分与结果：偶数编号物理芯训练、奇数测试，保证七组每组有训练芯；作者明确若留出整个负载组会更难（Discussion）。Table 4/Fig. 6 最优模型 `RMSE_ΔQ=0.0201 Ah`、`RMSE_Q=0.07 Ah`、归一化 RMSE 4.3%；±2σ 覆盖校准接近 0.954，但这是该 NASA 测试协议，未证明新场景覆盖。不能和官方 pp MAE 直接比较。
- 适配/反证：适合建立“可观测吞吐量与日历时间→容量变化”的弱先验，可能优于纯循环数；但官方只有 CK0，没有逐段 ΔQ 监督，缺失检查吞吐量，且 25/45°C 交替、四串截止均不同。最小实验：在独立容量标签集上留出整个温度/协议/组，同时只给留出实体一个起点标签；与累计 Ah+时间线性/分段基线比较容量误差和覆盖。若失效，不把论文的随机负载同域结果外推到官方。
- 核验等级：E1 原文 Table 2–4/Fig. 6/Discussion；未运行作者方法。


## 25．C_Silva2026_Conformal｜Conformalized Transfer Learning for Li-ion Battery State of Health Forecasting under Manufacturing and Usage Variability

来源卡：`notes/workstreams/C_evidence/C_Silva2026_Conformal.md`。书目身份：`arxiv:2603.24475`。


- 书目：Silva, Ozkan, El Idrissi, Canova, “Conformalized Transfer Learning for Li-ion Battery State of Health Forecasting under Manufacturing and Usage Variability,” [arXiv:2603.24475](https://arxiv.org/abs/2603.24475)。2026-09-29 读 13 页预印本 PDF，`papers/C_fulltexts/C_Silva2026_Conformal.pdf`；出版状态按预印本，许可依 arXiv 页面。
- 数据/标签：A123 26650 LFP 相关参数化的 SPMe 加 SEI/LAM 模型生成源域 1/3/4 批和目标域 2 批**虚拟电芯**，输入只是充放倍率协议与历史 SOH（式 6），标签为仿真 SOH 轨迹；不是现场未知容量的只读观测。Table 1 批次倍率不同；多仿真芯共享同一生成器，不构成独立实测确认。
- 方法：LSTM 单步预测下一 SOH，MMD 对齐源/目标潜表示（式 11–14），仅源批次 Leave-One-Batch-Out 选 λ；源训练均值/方差标准化（式 15–16）。预测区间用校准残差绝对值的 `ceil((n+1)(1−α))` 顺序统计量（式 17–21）。该 conformal 有可交换/条件稳定性要求；在线时间序列、工况移位下“distribution-free”不能无条件推出目标覆盖。
- 划分/结果：每个源批另留 10 个仿真芯作校准，目标批有截至 20 kAh 的少量**有标签目标样本**用于适配，后续目标样本无标签参与 MMD（原文 §3.2.2）；不能称纯无监督目标域；设 90% 目标覆盖，Fig. 5/Table 3 报告目标平均经验覆盖 98.8%、平均宽 4.08 个 SOH 百分点。**这只是该仿真目标批的经验覆盖**，校准样本来自源域，同组时间片相关，不能作为官方 4S 保证。作者 Discussion 明示尚需真实测量噪声和现场变异验证。
- 适配/反证：可迁移“异常/OOD 时扩大区间或拒绝高权重更新”的决策规则；绝不能用其数值区间直接为官方隐藏点打包票。真实校准应按物理组留出、按时间前缀取残差并报告组级、尾部、温度条件覆盖，容量真值定义一致；小于足够独立组数时只报告探索区间或保守界。最小反证是温度/容量/组拓扑全留出时固定模型和区间，检验覆盖与宽度；缺目标标签则不可称已校准。
- 核验等级：E2 原文公式、Table 1/3、Fig. 5 核查；无真实数据验证。


## 26．C_Wen2023_PINN｜Physics-Informed Neural Networks for Prognostics and Health Management of Lithium-Ion Batteries

来源卡：`notes/workstreams/C_evidence/C_Wen2023_PINN.md`。书目身份：`arxiv:2301.00776`。


- 书目：Wen et al., “Physics-Informed Neural Networks for Prognostics and Health Management of Lithium-Ion Batteries”, [arXiv:2301.00776](https://arxiv.org/abs/2301.00776)。2026-09-29 读 14 页完整作者 PDF，本地 `papers/C_fulltexts/C_Wen2023_PINN.pdf`；论文脚注给 [作者代码](https://github.com/WenPengfei0823/PINN-Battery-Prognostics)。此卡使用作者稿版本，期刊正式状态待单独核。
- 研究：把 Verhulst 型容量损失动力学和 DeepHPM 数据推导残差加入网络损失，使用不确定性权重平衡多项损失；不是直接由无标签运行波形得到容量真值。目标 `PCL_k=1−Q_k/Q_nom`（原文式 1，分数），故 `SOH_fraction=1−PCL`；若报百分数则 `PCL_pct=100·PCL`、`SOH_pct=100−PCL_pct`；与官方 `Q/102 Ah` 只有分母概念相似。原文 Section III、式 (1)/(11)/(14)。
- 数据/特征：MIT/Stanford A123 LFP/石墨快充寿命数据，单芯约 1.1 Ah，完整周期容量及充放曲线。Case A 用 #91/#100 训练验证、#124 测试；Case B #101/#108/#120 训练验证、#116 测试；Case C batch 2 的 20% 数据随机抽作测试，故 C 的物理实体隔离需另核。特征包括 2.7–3.3 V 放电 Q–V 二次式系数、IC 统计、均温、内阻和充电时间（Section V-B/VI）；**官方浅充没有完整放电 Q–V 和同周期容量标签。**
- 划分/结果：训练标签由完整参考容量算出；A/B 按芯留出，训练集内另分验证；Table III 的 PCL 估计 RMSPE 改善到约 0.42% 等要结合 case/列解读，不能与官方 SOH pp MAE 等价。正文也说明简单等权物理损失有时不优于纯网络，权重法是性能关键（Table III、Fig. 6–8）。
- 适配：可借“偏导/变化率不为正”的弱损失或分段单调损伤先验；Verhulst 函数是经验形状，不是由官方可见量唯一辨识的电化学参数。CK0 单锚点下拟合多参数动力学会靠外部标签先验。最小反证：同容量标签、同输入、同训练预算，在留出实体/温度上比经验损失、单调损失、纯回归、年龄基线，并检查尾部高估；如只有训练内平滑改善，则不能入主路线。
- 核验等级：E1 原文式和 Table III/Case 划分；作者代码链接核到但本轮未运行/未作静态逐函数比对。


## 27．C_YaoKowal2026_SSL｜Degradation-aligned self-supervised learning for state of health estimation of lithium-ion batteries under label sparsity

来源卡：`notes/workstreams/C_evidence/C_YaoKowal2026_SSL.md`。书目身份：`10.1016/j.egyai.2026.100884`。


- 书目：Yao & Kowal, “Degradation-aligned self-supervised learning for state of health estimation of lithium-ion batteries under label sparsity,” *Energy and AI* 26 (2026) 100884, DOI [10.1016/j.egyai.2026.100884](https://doi.org/10.1016/j.egyai.2026.100884)。2026-09-29 读正式开放 PDF 19 页，`papers/C_fulltexts/C_DegradationAligned2026_SSL.pdf`；PDF 页 2 标 CC BY。
- 数据/真值：CALCE CX2-34/36/37/38 四枚 **LCO 1.35 Ah** 单芯，0.5C CC-CV 充至 4.2 V、1C 放至 2.7 V；SOH 为实测完整放电容量/额定容量（Section 3.1、Table 2）。输入每周期 CC 充电电压曲线，重采样 300 点，长度本身也反映老化。四芯仅四个独立实体，不因数千周期增加跨芯自由度。
- 方法：同一芯两周期按周期号构造排序监督 `y_ij=sign(n_i−n_j)`，损失 `log(1+exp[−y_ij(s_i−s_j)])`（式 9–13）；预训练编码器后冻结，用稀疏容量标签训练新回归头（Fig. 4）。这是**寿命顺序监督**，无需 Q 标签但需事件排序与长期历史；能学到与老化相关的时间代理，并不保证机制上与容量一一对应。
- 划分/结果：主设 CX2-37/38 训练、36 验证、34 测试，主测试退化深度被训练芯包围；Section 4.4 再四轮留一芯，外推最深 CX2-38 的 1% 标签情形 MAE 3.195%（正文），而主情形摘要给 1% 标签 MAE 1.718%、RMSE 2.329%，不可混成同一难度。Table 4 的 early-only 1% 行 MAE 11.266%、MAX 27.212% 展示标签覆盖比标签比例更关键；这条是该表情形，需与对应列/划分读。作者在 Discussion 承认单型号受控数据不足以证明跨条件推广。
- 适配/反证：可试时间顺序预训练作为退化轨迹先验，但必须与仅周期序号/日期/累计 Ah 基线以及顺序打乱消融相比；预训练不得看到目标组未来序列。官方只有一个容量锚，1% 标签假设远强于此。若序号基线同样好或末期显著失效，排序编码器不提供可辩护的新增容量信息。
- 核验等级：E2 全文式 9–13、Table 2/4、Fig. 4 与 PDF 原页核查；未运行代码。


## 28．BatteryGPT2025｜Early prediction of lithium-ion battery degradation with a generative pre-trained transformer

来源卡：`notes/workstreams/D_old_refs/BatteryGPT2025.md`。书目身份：`10.1038/s41467-025-66819-0`。


#### 书目、来源

Jincheng Hu, Pengyu Fu, Zhongbao Wei, Yanjun Huang, Juliana Early, Ashley Fly, Yuanjian Zhang，*Early prediction of lithium-ion battery degradation with a generative pre-trained transformer*，[DOI 10.1038/s41467-025-66819-0](https://doi.org/10.1038/s41467-025-66819-0)，2025-12-05 在线出版，正式引文 *Nature Communications* **17**, 126 (2026)。不能只从 DOI 年份称其为“2025 卷”。2026-09-29 下载出版方 [HTML](https://www.nature.com/articles/s41467-025-66819-0)、PDF 和补充 Note 1/3/4/6，本地 `papers/D_old_refs/BatteryGPT2025*`。出版页开放获取，**CC BY-NC-ND 4.0**。**E1 原文/补充核对**，未运行模型。

#### 研究目标、数据和标签

目标是给定早期生命周期充电数据，生成未来**整个寿命轨迹**并预测随周期变化的 SOH、退化拐点与达到 80% SOH 的 EOL。主数据是 MIT/Severson 快充实验的 **46 枚 1.1 Ah LFP/石墨单芯**，30°C 强制对流箱；充电第一/第二阶段约 3.7–5.9C、至 80% SOC，随后 1C CC-CV 至 3.6 V，CC 放电至 2.0 V（正文“Data overview”，补充 Note 1）。文章称处理后 **21,280,768 samples**，它们是大量时间点/窗口，独立实体仍为 46 枚。SOH 定义当前容量/初始容量；CNN-LSTM SOH 估计器以**每周期真 SOH 监督训练**，GPT 另用整个训练芯充电轨迹进行下一 token 自监督。故信息条件是多芯全寿命轨迹与大量容量标签，不是仅一个 CK0 锚。

#### 模型、切分、比较

离散化每时刻 `V,I,T`，GPT-small（论文称约 42M 参数、256 token context）自回归生成未来充电特征；CNN-LSTM 从生成的单周期特征估 SOH，再由预测 SOH 曲线取拐点/EOL（图 1、方法式 1/4/8–11）。正文与补充均称**前 42 芯训练，其余 4 芯验证**；正文“Data overview”又把这 4 芯称 test，并写 k-fold，具体独立调参/最终测试分工未充分清楚。没有理由把 21M 时间点当独立测试。作者提供的 EPSO 定义是可见寿命比例，但补充 Note 6 又把 BatteryGPT(5)/(30) 称作 **5/30 个观察周期**，并另讨论 5%/30% 起点；这两个信息预算不能视为等价，应区分主文 MIT 表 1 与 KIT 补充表 1。

MIT 表 1：BatteryGPT(5) 预测 SOH RMSE **2.56%**、MAPE **1.90%**、拐点误差 −177 周期；BatteryGPT(30) 为 **0.21%**、**0.14%**、拐点 +13 周期、EOL +10 周期。主文 EPSO(30) 是按**真实最终寿命的 30%**选择预测起点；若前瞻部署必须改成预先固定的日历、周期或 Ah 规则，不能事先知道总寿命。表 1 没明确四枚留出芯的指标汇总口径，不能擅称四芯组平均。回归 CNN/LSTM/CNN-LSTM 是**最近三周期预测下一周期**，任务时距不同；自回归 LSTM/Transformer 才同为长程生成且共用 SOH 估计器（正文 p.6–7、表 1）。本论文指标对应作者的寿命轨迹任务，不能外推为官方当前月度组容量 MAE。最差芯、最差月、置信区间未报告。

补充 Note 6 另称 KIT 长寿命跨温数据上 BatteryGPT(30) SOH RMSE **2.28%**、MAPE **2.01%**、拐点 −34、EOL −3 周期；仅说 chronological split，未列该数据的芯数、化学体系、具体训练/验证/测试实体及目标 SOH 测定细节，因此是**受限外部证据**，不是独立 4S LFP 容量确认。其 BatteryGPT(30) 标为 30 *cycles*；不可与 MIT 主文的 30% 起点混并。

#### 可获得性、审查风险与竞赛适配

作者指向 [MIT 原始数据](https://data.matr.io/1)、[GitHub](https://github.com/ReparkHjc/BatteryGPT)（仓库可达、标 MIT license）和 Zenodo。正文“Code availability” 给出的 `10.5281/zenodo.1742067447` 实测 404；参考文献中的 [Zenodo 17420675](https://doi.org/10.5281/zenodo.17420675) 可达。记录这一书目/链接差异，未静态审代码、未复现。补充和正文没有澄清四芯是调参与最终测试是否分开；只标**不清楚**，不宣称发生泄漏。

本竞赛只有 CK0 一次 100.41 Ah 容量真值，目标为四串 102 Ah LFP 的月度 5.1 A 至组压 11.2 V 容量/102 Ah，CK1–7 隐藏。可借用轨迹预训练或将温度/电流/电压联合建模的想法，但模型需外部带全寿命标签的 LFP 单芯、适配到串联组与目标截止，并核查未来窗口/测试域统计。**拐点与 RUL 成功不能代替容量估计成功**。

最小证伪：冻结只在外部训练实体上学习的词表、归一化、GPT、SOH 头；在从未参与这些步骤的多组 LFP 前缀上，以组为单位、与年龄/累计 Ah/温度先验及低维容量基线比较相同月份的 C/20 组容量误差、最差组和后期高估。若增量只来自已知生命周期/训练标签或不能在单锚点适配后保持，则仅将该文用于寿命预测的背景论据。


## 29．Cheng2024｜Cheng2024｜充电 IC 特征预测退化模式

来源卡：`notes/workstreams/D_old_refs/Cheng2024.md`。书目身份：`arxiv:2412.10044`。


#### 来源和目标

Yuanhao Cheng, Hanyu Bai, Yichen Liang, Xiaofan Cui, **Weiran** Jiang, Ziyou Song，*Data-Driven Quantification of Battery Degradation Modes via Critical Features from Charging*，[arXiv:2412.10044v1](https://arxiv.org/abs/2412.10044)，2024-12-13；PDF 首页写 2024-12-16 投稿 Elsevier，尚不能据此称已刊出。arXiv 元数据把该作者拼作 **Weiren**，与 PDF 的 Weiran 不同，书目需保留版本差异。2026-09-29 读 arXiv PDF/HTML，本地 `papers/D_old_refs/Cheng2024_arxiv.*`；arXiv 许可见记录页面，未找到作者代码仓库。**E1 原文核对**。

任务是分别回归 LLI、正极 LAMpe、负极 LAMne **退化模式**，并非直接估放电容量/SOH。文章的摘要称“约 10% RMSE”，但正文表 2 与表 3显示：约 10% 的量级是相对 **MAPE**（如 LAMpe 10.79%），三模式 RMSE 是 0.59%、0.71%、1.78% 的模式量纲百分数；不能混写，更不能转成容量误差。

#### 实体、协议和标签生成

源自 Kirkaldy 等的商用 21700 **NMC811/SiOx-石墨单芯**数据库，共 40 枚、五种实验；此文只取满 0–100% SOC、同为 **1/3C 充电**但放电分别用动态 WLTP 或 CC 的 Expt4/5，各八枚，共 **16 枚**。10/25/40°C 分别 3/2/3 枚/协议（§2.2、表 1）。每 78 EFC 老化块前后有 RPT；RPT 包括 1/5C、1/20C、GITT，文中指出用于 DM 计算的是 **1/10C 完整充放**/电极模型来源方法。原文此处 RPT 倍率表述不完全一致，应回原始数据方案确认，不能替其选定单一真值口径。

真实 DM 标签只存在 RPT 点；普通老化循环的“标签”在假设三种 DM 单调增长下于 RPT 间插值（§2.3、图 2）。删除温控/电记录异常循环。每个循环的 `dQ/dV` 来自 1/3C 充电；因此虽然文献讨论充电站情境，实验证据不是任意变流、任意浅窗、无 RPT 的在线退化模式辨识。

#### 方法、划分和结果

提取 91 项温度/IC 及其统计变换，再依次用绝对均差、置乱重要性、互信息筛出 **21 项关键 IC 特征**（§2.4、§3.1、表 5）。IC 峰合并/消失时位置难定，故选择分位数、累计 IC 等统计量。分别训练 SVR、稀疏 GP、线性多元回归、ElasticNet，对照一个联合输出三模式的 FNN。FNN 损失为 `RMSE_LLI + 4·RMSE_LAMpe + 2·RMSE_LAMne`；权重是研究设定，不可从单 CK0 推出（式 3）。文中设计六次实验、每次三个测试**芯**，覆盖协议和温度；然而特征选择/超参数是否完整嵌在每次训练折内未清楚报告，故验证边界待核，不断言泄漏（§4、图 5）。

表 2 的六试验均值 MAPE：关键特征 FNN 的 LLI/LAMpe/LAMne 分别 **5.63/10.79/8.43%**；SVR **9.98/15.53/13.92%**，全特征 FNN **13.40/21.90/13.60%**。表 3 对应均值 RMSE：关键特征 FNN **0.59/0.71/1.78%**，SVR **1.00/1.18/1.47%**。即关键特征 FNN 在 **LAMne RMSE 并未优于 SVR**，不能笼统声称全面胜出。三测试芯的组合复用同一 16 芯池，六次不等于六组独立外部确认。未报告容量 MAE、四串组或末期容量误差。无公开代码/模型版本说明；原始数据为被引数据，需另核许可及下载。

#### 竞赛含义和最小反证

论文支持“固定低倍率广窗口 IC 统计量可与实验测得/插值的退化模式相关”，不支持从官方 4S LFP 一次 CK0 容量恢复 LLI/LAMpe/LAMne 三个绝对数值。官方运行浅充/变流、温度混合和串联不均衡还会影响导数；目标是 5.1 A 至组压 11.2 V 的组容量。可借用分位数/累计 IC 的抗峰消失特征和稳定性筛选思想；要防止将温度、EFC/年龄或 RPT 插值标签当新信息。

最小反证：用独立多组 LFP 的真实浅充+定期参考容量，对每组只保留目标时刻前窗口，按组留出并在内层选特征；与温度、累计 Ah、有效窗口宽度基线比较组容量增量。同时对同一窗口施加可记录的温度/电压扰动，观察特征是否仍稳定。若无法获得可信 DM 真值，只研究容量增量，不训练或声称三模式回归。


## 30．Zhou2026_dynamic_ICA｜Battery State of Health Estimation and Incremental Capacity Analysis under Dynamic Charging Profile Using Neural Networks

来源卡：`notes/workstreams/D_old_refs/Zhou2026_dynamic_ICA.md`。书目身份：`10.1109/TIE.2026.3665970`。


#### 版本

Qinan Zhou, Gabrielle Vuylsteke, R. Dyche Anderson, Jing Sun，*Battery State of Health Estimation and Incremental Capacity Analysis under Dynamic Charging Profile Using Neural Networks*，*IEEE Transactions on Industrial Electronics* **73**(8), 12228–12239 (August 2026)，[DOI 10.1109/TIE.2026.3665970](https://doi.org/10.1109/TIE.2026.3665970)；卷期页经 [Crossref DOI 登记](https://api.crossref.org/works/10.1109/TIE.2026.3665970) 核对。可读全文为 [arXiv:2502.19586v3](https://arxiv.org/abs/2502.19586)，2026-01-09 修订，以及作者大学站公开的 IEEE 接受稿（2026-02-06 接收）。最终排版版全文未取得，不能假称其页码已核；下述页码是接受稿页。原始 2025 v1 的标题/实验不能代替 v3。2026-09-29 下载 v3 HTML/PDF 与接受稿，本地 `papers/D_old_refs/Zhou*`。接受稿注明 IEEE 版权、个人使用许可，勿再分发。**E1 原文核对**，未审代码或重跑。

#### 研究问题与信息预算

常规 IC=`dQ/dV`、DV=`dV/dQ` 需要参考恒流曲线；作者以动态充电的 `I(ΔQ), V(ΔQ)` 学习同一退化状态下参考低倍率 CC 的“虚拟”IC/DV，再以两个部分面积特征和 relevance vector regression 估 SOH；另用 Conv-Net 直接从动态波形估 SOH。输入按累计充入 Ah 等间隔采样与单侧镜像填充，**不直接输入 SOC**，但需预定最小覆盖宽度 `ΔSOC≥20%`、最大宽度/初始容量以定采样步长。示例 128 点、原始范围 13–91% SOC、三种快充协议；小于 20% 时作者明确称精度会下降（接受稿 §II–III、§VI）。虚拟 IC 是监督重建的参考曲线，并非动态电流求导所得的物理 IC。

#### 实体、标签和划分

主数据是私有车载 **96 个 NMC622 三并模块，全部来自同一真实车辆电池包**、208 Ah、1 Hz、40,512 个充电对；这不是 96 个独立车包。各原始长充电波形随机裁剪 10 次形成 **405,120 对**，SOH 100–86%。模块交替做快充与低倍率充电，前后静置以定初/终 SOC 和模块 SOH；低倍率含 0.4C、0.3C 两段 CC 和 CV，**相邻低倍率循环的 IC/DV**为虚拟曲线监督目标（表 I、§V）。论文未清楚说明模块 SOH 的完整容量截止/分母测量程序，定义 `C/Cfresh`（p.1），故不能补造真值细节。

作者写对裁剪后的“dataset”随机分 60/20/20 train/val/test（§VI 开头），未说明先按模块或原始事件划分。**因此不能确证测试有独立模块**；也不能无证据断言一定泄漏。测试 RMSE：虚拟特征 U-Net **0.73% SOH**、Mobile U-Net **0.79%**，直接 Conv-Net **0.64%**、Mobile-Net **0.68%**；对应 99.7 百分位绝对误差 2.54/2.86/2.28/2.44% SOH（表 II）。直接回归与虚拟特征共用场景，但前者输出任务更窄；没有同输入的传统 ICA 动态电流有效基线。最差实体/末期组误差及置信区间未报告。

**v3 新增关键 LFP 迁移实验**：公开 Attia 2020 快充数据的 233 枚 **1.1 Ah LFP 单芯**，224 套多段协议、56,320 对、SOH 100–80%（表 IV）。先在 NMC 模块训练，再在 LFP 上**有监督微调**指定前/末层，并将 LFP 数据随机 60/20/20 分割；所需 LFP SOH 标签数与独立电芯分割未单列。LFP test 直接 Conv-Net/Mobile-Net RMSE **0.23/0.29% SOH**，虚拟峰高回归 **0.90/0.90% SOH**（表 V）。所以 v1 时代“无 LFP 验证”的旧结论已失效，但此实验也不是 zero-shot、单锚点或四串串联组确认。原始 NMC 数据私有；LFP 源数据公开；未在原文找到可核代码/许可。

#### 对竞赛的边界和最小实验

官方四串 102 Ah LFP 的真实浅窗、温度/起始 SOC、总压截止及单 CK0 标签，与三并 NMC 的周期完整高覆盖输入差异大；LFP 微调依赖大量公开同协议标签，而且按随机裁剪集划分的实体独立性不明。可迁移模块是“对变电流先构造**统一参考条件**的虚拟特征”和以 ΔAh 采样、覆盖门控；不可把 0.23% 当官方预期误差。

最小证伪：在真实浅充而非仅由深充后裁剪的独立 LFP 组上，按**原始组和事件**先划分、只用训练组拟合标准化与虚拟 CC 映射，外层留组比较直接低维部分窗口、动态导数、虚拟 IC；限定输入结束时间，记录 SOC/ΔAh 覆盖与温度。没有 ≥20% SOC 且完整区段时先报告覆盖率；若覆盖稀少或对年龄/温度基线无组外容量增益，则放弃网络路径。


## 31．Zhu2022｜Data-driven capacity estimation of commercial lithium-ion batteries from voltage relaxation

来源卡：`notes/workstreams/D_old_refs/Zhu2022.md`。书目身份：`10.1038/s41467-022-29837-w`。


#### 来源与核验范围

Jiangong Zhu, Yixiu Wang, Yuan Huang 等，*Data-driven capacity estimation of commercial lithium-ion batteries from voltage relaxation*，*Nature Communications* **13**, 2261 (2022)，[DOI 10.1038/s41467-022-29837-w](https://doi.org/10.1038/s41467-022-29837-w)。2026-09-29 取得出版版 [HTML](https://www.nature.com/articles/s41467-022-29837-w)、[PDF](https://www.nature.com/articles/s41467-022-29837-w.pdf) 与出版方补充 PDF；本地 `papers/D_old_refs/Zhu2022*`。开放获取出版版，论文页注明 CC BY 4.0；原文、表 1–3、补充注 2/4 核对，未运行作者方法。校勘后为 **E1 原文核对**，非本项目验证。

#### 问题、数据与标签

作者问：标准化充满后的电压弛豫曲线可否替代完整放电曲线来估容量，并跨类型迁移。130 枚商用 18650 **单芯**，非 LFP：数据集 1 为 66 枚 3.5 Ah NCA，集 2 为 55 枚 3.5 Ah NCM，集 3 为 9 枚 2.5 Ah NCM/NCA 混合正极（正文方法与表 1）。三集分别有 22,278、27,802、8,582 个“弛豫曲线+紧接着放电容量”单元，循环窗口与独立电芯不能混算。25/35/45°C、不同充/放倍率，退化范围约至标称容量 71%（表 1、图 1）。

每个输入先 CC 充至 4.2 V，再 CV 至 0.05C，随后静置；NCA/NCM 静置 **30 min、120 s 采样**，混合正极静置 **60 min、30 s 采样**。标签是同循环紧接着的 CC 放电至 NCA 2.65 V、NCM 与混合 2.5 V 的容量；跨标称容量规格做归一化。论文没有给本竞赛 5.1 A、组端 11.2 V 的标签。弛豫前充电终点、温度与静置长度均是输入条件，不是任意脉冲后的自由弛豫（正文 p.3，方法 p.9）。

#### 方法、划分、数值

六个弛豫统计量为方差、偏度、最大、最小、均值、超额峰度；三特征 `Var/Ske/Max` 的 XGBoost 为主模型，ElasticNet/SVR 为对照。标准化尺度从集 1 取得并用于集 2/3。补充注 2 比较四种划分；主结果采用**按工况分层且整芯入 train 或 test**，大约 4:1，训练内五折调参。集 1 上 XGBoost 和 SVR 均为 test RMSE **1.1%**；按时间前 80%/后 20% 的 test RMSE **>2.3%**，按温度切分最佳情形 **1.5%**。同一数据集上的实算对照：Baghdadi 静置线性模型 2.5%，部分充电 RFR 1.0%，剩余电量/ICA 1.3%，完整 CC-CV+GPR 1.1%（正文 p.5、表 2；这些输入预算不同）。

跨化学迁移并非无目标标签。集 2/3 每个工况随机选一枚目标芯，并从其寿命每隔约 100 周期取**带目标放电容量的单元**重训输入线性变换层，分别 19/27,802 与 30/8,582 单元，即 0.06%/0.35%（正文 p.7–8、表 3，补充表 14）。SVR-TL2 在集 2/3 的 test RMSE 为 **1.7%/1.6%**；未适配 zero-shot 为 **3.4%/7.3%**。这些是标称容量归一化后的 RMSE，不能自动视为本竞赛 SOH 百分点。最差芯、寿命尾部与区间未报告。

#### 可用性、限制与竞赛判定

原始数据 [Zenodo 6379165](https://doi.org/10.5281/zenodo.6379165) 可访问。作者称预处理代码在 [GitHub](https://github.com/Yixiu-Wang/data-driven-capacity-estimation-from-voltage-relaxation)；建模代码需向作者索取（正文 p.9）。本轮仅确认仓库入口可达，未审代码/下载大数据。模型需要重复标准化满充、较长静置和大量同类型训练芯；迁移还需目标类型的跨寿命容量标签。官方 4S 102 Ah LFP 仅 CK0 容量公开，串联组电压和单芯 SOC 不均衡改变弛豫条件（官方 `data/DATA_DESCRIPTION.md`）。因此仅可借用**弛豫特征和状态/温度匹配的实验设计**；1.1% 与 1.7% 不是官方容量预测证据。

最小证伪：仅在真实可用的满充后静置事件上冻结静置起点、温度、时间长度，计算单芯/组特征；在独立 LFP 多组且有重复 C/20 组容量标签的数据上比较温度、SOC、循环数基线与弛豫增量，并按组留出、禁止目标组后续标签。若无合格静置或对基线没有稳定增益，放弃容量路线，保留状态/阻抗诊断用途。


## 32．Bilfinger2024｜Battery pack diagnostics for electric vehicles: Transfer of differential voltage and incremental capacity analysis from cell to vehicle level

来源卡：`notes/workstreams/E_forward_pack/Bilfinger2024.md`。书目身份：`10.1016/j.etran.2024.100356`。


#### 来源与核验

Philip Bilfinger, Philipp Rosner, Markus Schreiber 等，*Battery pack diagnostics for electric vehicles: Transfer of differential voltage and incremental capacity analysis from cell to vehicle level*，*eTransportation* **22**, 100356 (2024)，[DOI 10.1016/j.etran.2024.100356](https://doi.org/10.1016/j.etran.2024.100356)。2026-09-29 从 [TUM/MCube 开放 PDF](https://mcube-cluster.de/wp-content/uploads/2025/04/1-s2.0-S2590116824000468-main.pdf) 下载并读完整 14 页；本地 `papers/E_forward_pack/Bilfinger2024.pdf`、提取文本和核图页面。PDF 标注 **CC BY-NC-ND 4.0**。表 1、§3–5、图 4/7/8 原页核对；**E1 原文核对**，未运行开源代码/数据。

#### 实际实体、输入、真值

**两辆量产车，各一辆**：2021 Volkswagen ID.3 Pro，58 kWh 净、NMC/石墨软包，电池 108s2p（九个 12s2p 模块），约 78 Ah 单芯；2020 Tesla Model 3 Standard Range Plus，52.5 kWh 净、LFP/石墨方形，**106s1p**，约 161.5 Ah 单芯（§3.1、附表 1）。另购同型号拆下的电芯作电芯—整车曲线对应，**其先前受力/老化史未知**。不是多车辆训练/测试、也不是 4s 样本。

车辆先放到显示 0% SOC，再以约 **1.84 kW AC** 在受控 **20°C** 充至车辆自动终止；相当于 VW C/45、Tesla C/57 的缓慢充电（§3.2）。车载 `Vpack,I,SOC,各串单元电压`；Tesla CAN 和 VW UDS，最终每通道约 **10 s** 一点并插值同步，VW 组压量化约 ±0.25 V、电流约 ±0.01 A（§3.3；这些是文中估计分辨率，非官方题目传感器规格）。对比电芯放到下限 CCCV、静置 2 h，在温箱按相近 CC/恒功率充电，1 Hz/4 mV 触发采样（§3.4）。

他们的车辆 SOH 是一次几乎全范围**低功率充电积分能量 / 车款标称净能量**，VW 分母 58 kWh，Tesla 52.5 kWh；另用电流积分/Ah 特征识别 DVA/ICA 改变。没有独立 5.1 A 组放电至 11.2 V 的容量真值。两车各在购买后与约两年后测，VW 约 32,600 km、Tesla 约 26,300 km（§4.4）。这属于同车纵向诊断与电芯→车特征比对，**没有机器学习训练/验证/外组测试分割**，不应写 SOH 预测 MAE。

#### 方法链、关键读图和数值

积分 `Q(t)=∫I dt`、`E=∫UI dt`；以 `dU/dQ` 做 DVA，以其倒数做 ICA。对电压/容量前滤波，再对 DV 前后向滤波，各窗口长度约测量点的 1%；无定义值和极端 IC 值被删（§4.2）。车辆为恒功率充电，电芯 CC/CP 比较显示同量级条件下 pOCV 平均电压差约 1.1/1.3 mV，但高倍率会削弱特征（§4.1）；结论限于低功率条件。

**LFP 限制可直接定位**：Tesla 的平台电压在图 4 的未滤波 IC 曲线中出现尖峰/噪声，滤波后部分峰可辨；文中认为该条件下 DVA 比 ICA 对测量精度和采样更稳健。把 10 s 信号降采至 300 s，特征仍可大致捕捉，但噪声、**电压分辨率**和滤波选择更可能成为限制；这并非证明任意 LFP 短浅充可可靠 ICA（§4.2、图 4/5）。电芯与整车特征经过电压/起点配准后多有对应，但 NMC 并联 2 芯削弱 DVA 峰，Tesla IC 有整曲线电压偏移，作者只提出连接/电阻/传感器等可能原因，并未唯一识别（§4.3、图 6）。

购买后/两年后车端充入能量：VW **60.6→55.0 kWh**，按 58 kWh 净分母 SOH **104.4→94.9%**；Tesla **57.0→55.1 kWh**，按 52.5 kWh 净分母 **108.6→105.0%**（§4.4）。VW 后期 BMS 上限电压改变，导致 55.0 kWh 含人为可用窗口收缩；DVA/ICA 联合推断若原上限保持可再充约 8.6 Ah、估得 SOH **101.6%**。后续 BMS 升级后复测上限恢复，测得 **59.40 kWh / 102.5%**（§4.4–4.5、图 8）；厂家未公开内部变更，不能把先后时序当作因果证明。**单位核对：**图 8 估计约 58.9 kWh，实测 59.4 kWh，差 **0.5 kWh**，相当于 58 kWh 净能量分母下约 **0.86 个 SOH 百分点**；文中写的“deviation of 0.5%”与图示/所列 SOH 差约 0.9 pp 的单位不一致，不应转述为 0.5 pp。这是同一辆车的一个有价值反事实核验，但不能当独立 LFP 容量预测精度。作者据图 7 的电极/峰位联合**推断** LLI 占主要真实退化，同时明确负极 overhang/可逆锂迁移和 BMS 干扰无法精确分开。

作者提出约 **50–100% SOC 低倍率部分充电**追踪石墨 stage-2 峰与平衡容量 `Q_B` 的诊断程序，前提是能覆盖该峰且上限稳定（§4.4–5）。这是建议，没有独立多车、短浅窗的容量误差验证。图 4、7、8 的坐标、峰形、数值与 PDF 原页图像人工对照；未对数据数值重算。

#### 对官方 4S LFP 的决策含义

该研究使“**电芯到串联车端特征完全不可转移**”过强：在 106s1p LFP、**标准化低功率几乎全充**下，某些石墨 DVA/ICA 峰仍可在车端辨认。它同时给出反证边界：LFP IC 对电压量化/滤波很敏感；组端电压偏移和 BMS 截止改变会伪装成健康改变；其 SOH 是车端**充电能量/净能量**，不同于官方 4S LFP **低倍率放电 Ah/102 Ah**。两辆车不是统计上可推广的实体验证。研究只支持优先检查 CK0 与运行事件里是否可找到匹配起点/温度/覆盖的石墨 DVA 特征，不能承诺一个 CK0 下的组容量精度。

最小证伪：在多套真实 4S LFP 独立组上，保持同一 SOC 起点、20/25°C、低充电功率与相同组端上下限，记录四芯和组电压；先比较 stage-2 峰的原始/滤波稳定性及不同传感器偏移，再用**独立 C/20 组放电容量**检验相对年龄/累计 Ah 基线的增量。预留人为上限变化的负对照。若真实前缀缺足够覆盖或峰稳定性/容量增量不成立，则只保留状态诊断。

数据 [mediaTUM 1737452](https://mediatum.ub.tum.de/1737452)，处理代码 [TUMFTM GitHub](https://github.com/TUMFTM/Battery-Pack-Diagnostics-for-Electric-Vehicles) 可找到；仅核入口与 README，未下载/运行数据。代码库页面标 GPL-3.0，而 README 正文写 LGPL v3，**代码许可存在仓库内部差异**，引用研究结论不受其影响，但复用代码前需核许可证文件。


## 33．F_Deng2024_RapidPackDA｜Rapid health estimation of in-service battery packs based on limited labels and domain adaptation

来源卡：`notes/workstreams/F_forward_limited/F_Deng2024_RapidPackDA.md`。书目身份：`10.1016/j.jechem.2023.10.056`。


**书目与证据等级。** Zhongwei Deng, Le Xu, Hongao Liu, Xiaosong Hu, Bing Wang, Jingjing Zhou, “Rapid health estimation of in-service battery packs based on limited labels and domain adaptation,” *Journal of Energy Chemistry* **89** (2024), 345–354, [DOI 10.1016/j.jechem.2023.10.056](https://doi.org/10.1016/j.jechem.2023.10.056)。2023-11 在线，2024 卷期。本文通过[第一作者上传的公开全文](https://www.researchgate.net/publication/375574069_Rapid_health_estimation_of_in-service_battery_packs_based_on_limited_labels_and_domain_adaptation)逐节查阅（网页可读，PDF 下载端失效），并下载、结构审计[作者公开仓库](https://github.com/BatICM/Charging-test-data-of-in-service-electric-vehicles)的 MAT 和 README。E2 原文加原始数据交叉核验；未复现网络训练。卡中数值为作者结果，除特别注明的 MAT 审计计算外均不是本项目成绩。

#### 研究问题与真实信息预算

研究对象是 **10 辆在役电动车电池包，均为三元系而非 LFP**；原文 §3/Table 2 写明 84–108 个串联单芯、不同额定容量，每辆只有**一次**完整充电试验。先放到 BMS 的 0% SOC 或触发断电；每充 10% SOC 暂停 1 小时，抽取最大单芯静置电压构成 SOC–OCV 曲线，且用充电电流、电压辨识 Thevenin 单芯模型（§2.1/Fig. 2）。**参考 SOH = 该次完整充电的累计 Ah／额定容量**（§3），并非独立低倍率放电容量或只靠任意 20 分钟片段取得的真值。10 辆车因此只提供 10 个独立车级真实 SOH 标签；短窗数量增多不会增加独立标签数量。

一阶 RC 单芯模型串联成整包数字孪生，调整各单芯最大容量、初始 SOC 和模型参数生成不同老化/不一致程度的合成充电曲线（§2.2/Fig. 3）。文中示意 4 串仅为绘图便利，真实实验是 84–108 串三元包，绝不能把 Fig. 3(b) 的 4 串误当与本竞赛 4×102 Ah LFP 同型。作者在 §2.1 仅展示一车 ECM 拟合电压 MAE 0.71 mV；这是动态电压拟合，并非跨车容量辨识误差或模型在本项目的精度。

#### 输入、模型和划分

训练输入是 CC 充电时最大单芯与平均单芯电压各自对应的累计电量增量序列，加表示窗口位置的电压序列（§2.3 Eq. 3–5）；电压重采样间距 1 mV，窗口 100 点即约 100 mV，步长 5 点。因此一个完整充电曲线可产生数十个**高度重叠、同车同标签**的样本。文中在三元 3.6–4.2 V、约 30–100% SOC 范围构造输入。这里的增量电量可由当前累积电量减窗口起始电量得到，不需要知道绝对充电起始容量；但取得车级训练标签、模型标定仍依赖前述完整试验。

模型先用数字孪生合成数据预训练 1D CNN；作者同时比较仅更新全连接层的微调，以及 DANN 域对抗适配（§2.4/Fig. 4）。域适配阶段组合**源车带标签样本和目标车无标签样本**，网络非完全零目标数据。文章写明 10 辆实测车中随机取 8 辆训练、2 辆测试，做 20 次组合；训练窗再随机留 20% 作调参验证（§3.1）。这说明**实测带标签样本**按车 8/2 分离，但 §3.1 又描述先从全部 10 车构造数字孪生合成数据，未交代合成预训练阶段的参数辨识/车级隔离；不能据此断言泄漏或完整无交叉。训练内部 20% 窗验证会共享车级标签，不能视为独立车验证。20 次组合重用这 10 辆车，亦不能视为 40 辆独立目标车。论文没有给出按 4 串电芯、同一组末期检查点的误差分层。

#### 原文数值与解释边界

§3.1/Table 3 的 20 次试验平均测试 MAE/RMSE：仅合成预训练 **9.63%/12.29%**、微调 **3.94%/4.95%**、域适配 **3.22%/3.90%**。这些百分数为论文三元电池车队、充电容量定义、短窗样本聚合下的预测误差，不能改称本竞赛隐藏 CK 的 pp 误差。§3.4/Fig. 8 给 50 mV 窗 **3.41%/4.14%**，100 mV 约 3.22%/3.90%；作者实验 0.3C 下 100 mV 充电需 4–16 分钟，称部署过程可在 20 分钟内完成。该 20 分钟不包含为 8 辆源车获取完整标签、十点 OCV/休息试验及孪生校准的前期成本。

#### 公共 MAT 的可复核异常

下载 `sources/BatPackdata.mat` SHA-256 `17c0f022…42c23d9`，按 `AUDIT_DENG_MAT.py` 只读审计得 10 个 `BatPackdata/SOH` 标量、共 318,351 个充电块时间序列行。`Inf` 块中实际字段为 `I_load`, `Q`, `Vmax`, `Vmean`；另有 `SOC_OCV`, `Cn`, `Ncell`, `Type` 等顶层字段。**公开 MAT 未出现 README 声称的 `Time(s)`、`Temperature(°C)`、组电压、逐点 SOC 等列**；它可用于论文样式充电曲线但不能自行验证环境温度、采样间隔或应用于官方放电协议。仓库 README 使用“每个文件对应一辆车”措辞，实际只有一个 MAT，内部 10 条车辆记录。

更关键的是 **第 5 辆数据自相矛盾**：原文 Table 2 及仓库 README 写额定 **174 Ah、SOH 82.21%**；MAT 写 `Cn=147 Ah`、`SOH=97.307653%`。MAT 该车 4 个充电块末端 Q 相加得 **143.04225 Ah**，恰好分别产生 143.04225/174=**82.20819%** 和 /147=**97.30765%**。这符合额定容量数字转置引发的标签变化，但**原因未获作者证实**，不得私自把 MAT 的 147 改成 174 后宣称原始数据无误。若用该数据作独立基准，预先登记排除第 5 辆和“以原文 174 Ah 重算”的两套敏感性分析，并保留原始 MAT 不变。其余车也应逐车核对公开数据与原文标签。

#### 和本竞赛的严格对照、可执行反证

本竞赛目标是**一组四个 102 Ah LFP 串联**，满充后 **5.1 A C/20 放电到首次组端 11.2 V**的 Ah/102；仅 CK0 一个已公开真实标签，CK1–CK7 隐藏。Deng 的三元包、0.3C 充电窗、最大/平均单芯曲线、完整充电真值、8 个训练车标签、目标车无标签输入，均与官方输入/标签预算不相同。它可作为“按物理组分割”和“模拟到实测域差异必须校准”的**反证材料**，不能成为 LFP 四串方案 D2 直接验证或 3.22% 官方性能预期。

若试验域适配，应先独立获取目标定义匹配的多组 LFP 四串容量标签；固定按组/日期划分并只允许截止日前的目标无标签前缀；对照同样输入的简单模板/线性/GP 基线、无孪生 CNN、无域适配 CNN；同时报按组 MAE、最差组、末期误差。若优势仅来自完整目标充电、未来无标签数据或短窗伪重复计数，则拒绝迁移主路线。作者公开 10 车 MAT 可做异协议 NCM 方法压力测试，使用时遵守仓库的学术非商业限制并处理第 5 辆异常。

