# 复现与边界

工作分支 `exp/phase2-multistage-features-20261012`，独立 worktree，源码研究目录为本文件所在目录。正式框架、提交模型和旧研究仅只读。Python3.13；项目小模型固定 scikit-learn1.7.2 / XGBoost3.1.1，完整版本见 environment.json。模型8个候选，辅助Ridge2个；固定论文参数、旧N/T固定代码比较另列。随机种子42，BLAS/OMP单线程。

为保护本次记录，复现生成新的同级目录：

```bash
cd '/Users/shane/Desktop/Arena 阶段 2 官方材料/research/phase2_multistage_features_20261012'
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python reproduce.py --out phase2_multistage_features_rerun_YYYYMMDD
```

加 `--public-download` 会尝试获取预选作者ZIP成员。整个档案未下载；先前元数据、目录尾部及CRC记录保存在 public_data。只接受内容长度、CRC正确的成员，成功后保存SHA。此前大小24MB的H5获取失败后转选4.1MB/0.78MB/13KB压缩CSV；多个内容接口HTTP Range超时。不要把未运行基准当成论文复现数字；网络可用后用 public_benchmarks.py 执行、先核验实体/measurement_id字段及原始时间列，再报告实际运行。若数据依然取不到，无参数默认烟雾测试只生成库配置，不是容量性能测试。

执行顺序：原始阶段/标签清点→预登记→特征与前缀核对→整芯嵌套容量评分→不同预算/温度/前推→阴性与波形扰动→原A和原N/T补充对照→官方共同支持和下一事件辅助任务→科学审计→报告。所有源单芯、官方和论文版本的绝对路径及SHA见对应manifest/provenance。

开发期发现F0历史累计充电量尚未加入、同编号源循环的时序配对需排除、原A须严格20Ah末段。初步结果保存在 development_before_pairing_and_F0_completion，最终结果在根目录；没有按性能选择窗口或新增调参配置。原 protocol.json 哈希保持不变，必要的实现修正通过 amendment 文件显式登记。六芯和官方组此前已曝光，新增嵌套评分是探索性验证，不是新的盲测。

所有容量模型的目标是各自真实参考容量；未来完整放电只提供评分标签，不进入早期电压输入。F4只在容量测试之后可用，属于回顾诊断。原N/T对照按完整五个训练芯寿命拟合，当前完成充电循环坐标、已知名义温度/倍率预测，未使用留出芯初始容量锚点；它的训练样本预算与小模型不相同，不能用于公平阶段增量门。官方F0累计电量由可见正电流和实际时间间隔积分，零时间/大缺口跳过；不信任含义可疑的累计计数器。

CK0没有可配对的充后事件；CK1–CK7容量真值未公开。官方模型不训练TL1/TL2，不对四个单芯分数求平均或最小输出组容量。需要得到同协议多次真实四串容量、初态和截止投影的独立检验后才考虑转换。
