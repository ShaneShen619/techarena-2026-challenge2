# 失败与隔离

按 run ID 记录命令、错误、影响、修复与新版本。不要覆盖已完成 run。

- N2 工作簿初读：两文件第四列是 `SOC_fake` 而非 `SOC`，全部源文件有 1–2 个重复秒。初版特征提取的严格 schema/时间断言失败，尚未读取封存标签；改为仅允许前三个原始电流/电压/时间字段、第四列显式排除，重复秒保留最后记录。源 ZIP/分割未变。
- N2 开发 v1：全程充电积分留一误差 0.0027 Ah，被自动选中；这项近似直接重构同测试流程容量，判为疑似目标代理。完成的 v1 run 保留，新 v2 排除后选固定 3.35–3.50 V 局部窗口，最终冻结与封存评分发生在 v2 后。初始候选 T2 电压形状线性模型因无可信独立特征定义取消，未记作已比较。
- N9 `render_docx.py` 首次运行失败，`ModuleNotFoundError: pdf2image`；没有为文档渲染改动旧 Python 环境。改用本机已安装 Microsoft Word 原生导出 PDF、Poppler PNG 逐页视觉检查。第一次 AppleScript 把 `open` 的返回值当 document，报未定义变量；修为 `open` 后 `active document`。Word 对本轮 DOCX 和 `outputs/` 的本地文件访问请求已在 UI 授予，PDF 导出成功。旧结果 PDF 不受影响。
- N8 发现 `pipeline_result.json` 的 `official_hidden_targets=35` 名称错误，实为 35 个预测行/7 个隐藏 CK。原件不覆盖，`pipeline_result_v2.json` 已修正键。冻结时遗漏私有标签映射 SHA，事后用固定 ZIP 独立核对 23 组并明示事后 provenance；下一轮应预先纳入。
- 验证官方接口时误把 `validate_submission.py --help` 当只读帮助；该脚本实际执行并在根目录生成了 `validation_report.txt`。检查其 01:12 时间与内容后已删除本次生成的根目录文件，根目录原官方代码和数据未改。此验证使用原 root 示例而非本轮 C3 候选，故不在本轮候选接口验收中冒称通过。
