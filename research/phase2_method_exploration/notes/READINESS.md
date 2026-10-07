# M0 运行准备与数据资格

2026-09-28，协议 v1.3，结论：**runnable_with_limits**。M0 的本地复现、因果输入门和环境冒烟已经通过，可以进入 M1–M9 的可执行路线。它并不意味着容量目标达标或官方隐藏真值已知。

## 已实测的就绪证据

- P1 固定开发面板 180 目标、六个物理电芯，SHA256 与冻结值一致；67 个原始文件与旧清单逐字节哈希一致。官方 16 个数据文件也与旧哈希一致。TU 28 个文件本轮对大小和修改时间与旧完整审计一致，尚未重新逐字节哈希；Che 只有本地 SHA 与旧记录，缺发布者文件哈希。
- 新目录复跑七组历史消融和 20 A 脉冲初筛，两份 JSON 与历史文件内容及 SHA256 完全一致。历史消融属于 D0：例如完整深充 CC Ah 加温度在旧六芯面板宏 MAE 0.7722 pp，但该信息不允许进入 D1 同预算比较。41 个脉冲只是初筛，M1 需逐项认证。
- 30 s 原始 P1 信号已重新读行并做 3.50 V 原始采样越线裁剪：914 个旧认证事件中 910 个生成 15/20/30 Ah 片段，每预算 910 个，1080 个目标条件视图；没有空输入视图或缺失当前片段，四个未通过裁剪的事件在各目标历史中合计留下 186 个缺失引用，没有用别的事件补位。以最终机器摘要为准：`../data_manifests/d1_target_visibility_final_summary.json`。适配器逐条检查 1080 视图，未来事件、标签列和完整 CC Ah 注入被拒绝。
- 一事件、一折训练、官方 CK1 前缀、一个检查点、pickle 新进程预测以及 CSV/JSON/PNG 写入已冒烟。新进程预测差 0。官方 CK1 真值仍隐藏；该输出只是接口检查。

## 各路线可执行程度

| 路线 | 状态 | 能验证的对象 | 主要限制 |
| --- | --- | --- | --- |
| M1 官方 20 A 重复诊断 | ready | 事件资格、同 Ah 电压与动态响应、后续无标签电压 | 41 个初筛尚未认证；不能把约 10 Ah 脉冲当容量 |
| M2 P1 浅充缺窗映射 | runnable_with_limits | 六芯 D1 容量代理、遮罩/回退、预算敏感性 | 深充截取不是真浅循环；20 Ah 下 3.38–3.42 V 仅 60/910 片段有完整窗口，官方浅充 33/33 有该窗 |
| M3 温度分离 | runnable_with_limits | 当前温度与历史暴露的配对/混淆测试 | 六芯温度与日历/工况可能共线；需温度切换匹配 |
| M4 状态估计 | runnable_with_limits | 电压预测、合成机制可辨识性 | 官方没有 CK1–CK7 容量真值，平坦 OCV 可能不可辨识 |
| M5 四串截止 | runnable_with_limits | 数学、CK0 与独立合成真值 | 缺同协议的独立四串容量确认 |
| M6 TU 阻抗 | runnable_with_limits | 28 个 8S 现场系统的信号/阻抗迁移 | 无真实 SOH 容量列，主动均衡与时间缺口须处理 |
| M7 自监督表征 | runnable_with_limits | 无标签预训练及 P1 六芯容量代理 | scikit-learn/torch 不在当前隔离环境；可先用 numpy/scipy 线性法，深模型需局部 wheelhouse 验证 |
| M8 融合 | runnable_with_limits | 与同输入单通道的 P1 代理比较和缺模态压力 | 需 M1–M7 完成；仍无官方容量分数 |
| M9–M10 审核与交付 | runnable_with_limits | 独立重算、复现、读者测试、官方逐点无标签回放 | D2 兼容封存确认不存在时须明确 `not_available` |

## D2 资格结论与下一步

本地 P1 六芯已用于开发，不能改名为独立确认。Che 的充电容量与官方未来放电容量不同；TU 只有 BMS SOC 与运行信号，没有实测 SOH。外部初筛见 `../data_manifests/external_candidates.csv`：He 等 102 Ah LFP 成对电芯/16S 包有跨尺度价值，但不是四串，Zenodo 数据许可未明；Yagci 等的 180 Ah 单芯参考测试可作为独立**异协议**补充，其数据包 2.5 GB，本轮按 prompt 先核对发布者 readme、许可证与字段说明。两者均不能使 `d2_confirmation_status=passed`。M2/M5 需要时先下载代表元数据/小文件并验协议，再决定是否下载大包；网络失败不阻塞 P1/TU/官方无标签主线。

来源：[He 等数据记录](https://zenodo.org/records/20132842)、[其作者代码与 ESSL1 示例](https://github.com/BatICM/cell-to-pack-degradation)、[Yagci 等数据与许可](https://zenodo.org/records/22939281)、[Yagci readme](https://zenodo.org/records/22939281/preview/readme.md?include_deleted=0)。容量资格在本地 `../notes/DATA_GAPS.md` 持续更新。
