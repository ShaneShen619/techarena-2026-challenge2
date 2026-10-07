# 失败和限制记录

每项失败记录发生时间、命令、输入/代码哈希、原因、修复或回退以及受影响结果。

- V0 标准文档渲染器 `render_docx.py --emit_pdf` 报 `LibreOffice soffice was not found on PATH`；同一 Word 用本机 Microsoft Word 导出 PDF，再用 Poppler 渲染并人工查看成功。见 `notes/READINESS.md`。
- V1 首次 `scripts/v1_event_coverage.py` 运行在事件前静置时长计算处报 `TypeError: unsupported operand type(s) for -: 'method' and 'method'`，因为 pandas Series 的 `prior.last/first` 解析为方法。运行在输出结果/完成标记前失败，TASK/runs/V1_event_coverage_20260929 仅有配置副本。修复为 `prior["last"]-prior["first"]`，并仅允许无 COMPLETED 标记的未完成 run 继续；不触碰历史结果。修复后的脚本哈希随完成结果保存。
- V1 第一完成版随后在独立计数器审查发现：约 20 A 负电流脉冲的 `discharge_Ah_cum` 不增，`charge_Ah_cum` 增长，原事件目录把脉冲 Ah 算成零。已把第一版三个 CSV 复制保存于 `runs/V1_event_coverage_20260929/`，在新 run_id `_v2` 改用严格事件内带时间戳的电流积分作跨度、原计数器只作诊断。第一版事件 Ah/覆盖文件标 invalidated，不能引用其脉冲 Ah；v2 与第一版对照并记录源文件哈希。
- V2 R02 首次脚本误把公开 CSV 的末列 `SOH_pct=98.44` 当作 `capacity_Ah`，CK0 回代断言在写结果前失败。修复为明确读取 `capacity_Ah`；同一未完成 run 才继续执行。
- V2 R02 首次完成版使用 0.85–1.05 无量纲扫描，冻结配置实际要求表观 70–105 Ah、0.5 Ah 步长；独立审查发现。保留 v1 作为非主实现烟雾，V2b v2 按 CK0=100.41 Ah 明确换算，并加入 270 组敏感性。审查随后发现 v2 稀疏/密集噪声不是严格配对、留后段未显式防模板外推；V2b v3 修复，取同一噪声轨迹子样并使用拒绝越界的模板接口，18 个留后段均无越界。主结论只引用 v3。
- V3 R05 负对照首跑对已保存逐点预测的严格相等断言失败，最大差约 0.0009 pp；原因是重建时误用面板四舍五入的 `anchor_soh_pp`，而主运行用 `target_inputs.npz` 原始锚点。v1 未完成；v2 从同一 npz 读取锚点后严格相等并完成。该问题未改变主 V3 结果。
