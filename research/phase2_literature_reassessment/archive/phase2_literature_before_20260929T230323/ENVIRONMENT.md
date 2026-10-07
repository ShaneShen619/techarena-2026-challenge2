# 夜间文献研究环境说明

检查日期：2026-09-28。本文件记录配置与实测结果，不代表权限永久不变。

## 已确认

- doc-coauthoring 已存在：`/Users/shane/.agents/skills/doc-coauthoring/SKILL.md`。无需重新安装。
- 本地配置文件的默认模型为 `gpt-6-astra`，推理档位 `medium`。这只是配置文件值，实际会话可覆盖；本次没有更改配置。
- 当前会话为 workspace-write，项目目录和临时目录可写；桌面其他位置只读，额外写入可能需要审批。
- 搜索及官方网页打开工具已成功调用。Shell网络受限，未测试各论文站点下载，不能据此保证批量下载成功。
- 当前项目只有官方任务PDF，尚未放入研究论文。已创建papers/用于集中收集。
- 找到第一阶段旧调研，可作搜索线索，不能当作第二阶段已核实的结论。
- 系统 `python3` 为3.13.0。文档所用打包运行时的Python为3.12.14，docx、pypdf、pdfplumber、pdf2image、PIL均可导入。
- pdftotext、pdftoppm、caffeinate可用；当前Word任务曾使用打包LibreOffice成功渲染12页中文文档。

## 路径

文档Python：
`/Users/shane/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3`

打包Node：
`/Users/shane/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node`

打包LibreOffice入口（使用绝对路径，不使用桌面安装版）：
`/Users/shane/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/soffice`

文档技能与渲染脚本：
`/Users/shane/.codex/plugins/cache/openai-primary-runtime/documents/26.905.11957/skills/documents/SKILL.md`
`/Users/shane/.codex/plugins/cache/openai-primary-runtime/documents/26.905.11957/skills/documents/render_docx.py`

插件升级后路径可能变化，运行时重新发现对应技能与依赖即可。

## 中文排版经验

本会话默认渲染曾缺失中文。加入显式字体目录后成功：使用系统Songti SC，设置FONTCONFIG_FILE指向本研究目录tmp/fonts.conf，并设置SAL_FONTPATH=/System/Library/Fonts/Supplemental。该设置仅用于渲染子进程，不更改系统字体或全局配置。

渲染命令应使用打包Python调用render_docx.py，输出到本研究目录tmp/，并检查每一页。字体能在Word显示不等于渲染正确，反之亦然；必须实际检查图片。正文可使用固定行距，清除模板继承的标题下划线/段落边框，避免产生空白页。

## 睡前启动

1. 在当前项目会话里使用START_PROMPT.md。无需关闭沙箱或给整台电脑完全权限。
2. 接通电源，保持电脑开盖、Codex应用和网络连接可用。电源检查中的AC Power设置为sleep 1；这不等于当前一定会休眠，但不适合直接假定整夜持续运行。
3. 可在另一个终端手动执行：`caffeinate -i -s -t 28800`。该命令在接电时提供最长8小时的防睡眠断言，终端退出或Ctrl+C可提前结束。它不会启动研究，也不是定时任务。
4. 这份prompt写明普通疑问自行处理、阶段进度落盘和完成条件。它不能绕过权限、网络故障、会话/配额限制，也不能保证恰好运行8小时。
5. 当前只准备了prompt与目录，没有启动夜间研究、没有创建Goal、没有修改电源或模型设置。

## 依据

- 本地SKILL.md、本地config.toml的非敏感字段、当前会话权限、导入探测及pmset/man caffeinate。
- 长任务依靠明确里程碑和持续落盘状态：https://developers.openai.com/blog/run-long-horizon-tasks-with-codex
- Goal是具有边界和验收条件的跨轮目标：https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex
