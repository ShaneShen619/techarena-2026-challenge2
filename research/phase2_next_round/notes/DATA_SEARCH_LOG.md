# 数据检索与资格日志

检索日期：2026-09-29。检索目标是未参与选择、具有真实容量标签且尽量接近 4S、102 Ah、5.1 A 至组压 11.2 V 的 LFP 数据。仅使用公开发布页、论文和作者仓库，不查找或推断官方隐藏 CK1–CK7。

## 已核实来源

- 官方本地包：唯一同协议容量为 CK0=100.41 Ah；CK1–CK7 隐藏。
- P1：六颗 102 Ah LFP 单芯容量标签，但倍率与截止不同，且已反复用于开发。
- Che：11 颗 LFP，含充电容量和 partial-Q 类字段；只能验证部分充电形状。
- TU Darmstadt BattGP：28 个约 160 Ah、8S、主动均衡现场系统，约 1.33 亿行；可验证工作点电阻和异常，不含真实容量复测。
- He 等 Zenodo 20132842：ESSL1 为 102 Ah LFP、6 单芯和 1 个 16S 包，具跨尺度价值；发布页未显示明确数据许可，且不是 4S/官方截止协议，暂不下载。
- Xu 等 Mendeley 4nww8p6vxf：一颗 53 Ah 单芯和一个 1P10S 模组，真实循环且每 50 周期容量标定，CC BY 4.0；只有一个模组，协议与容量等级不匹配，列为异协议机制候选。
- Ulfat 等 Mendeley k675pxrd83：40 Ah、8S、3000 条周期级记录，CC BY 4.0。配套 Data in Brief 明确容量为确定性退化轨迹、其他变量为生成值且非原始试验台记录，因此降为 S 合成代码检查，不作独立确认。
- Yagci 等 180 Ah 单芯数据：可作独立异协议补充，不能确认四串官方容量。

## 检索结论

未找到满足 4S、约 102 Ah、真实浅充/运行前缀、重复 5.1 A 至组压 11.2 V 容量且未参与选择的公开数据。当前 `independent_capacity_confirmation=false`，`official_capacity_accuracy_verified=false`。继续研究的合理产物是严格 D1 配对消融、异协议迁移边界、官方无标签诊断和可直接执行的四串测量方案。

公开入口：

- https://zenodo.org/records/20132842
- https://zenodo.org/records/13715694
- https://data.mendeley.com/datasets/4nww8p6vxf/1
- https://data.mendeley.com/datasets/k675pxrd83/2
- https://doi.org/10.1016/j.dib.2026.113252
