# 失败与访问限制

启动时无失败记录。每项后续失败写时间、命令/来源、具体错误、替代、影响范围与是否重试；不得把一次网络错误当科学反证。

- 2026-09-29：一条预检用 DLR PDF URL 返回 HTTP 401；同一论文从已核实的公开机构地址获得 PDF。仅该 URL 失败，未影响论文阅读。
- 2026-09-29：系统 `python3` 无 `python-docx`；本轮隔离 `tmp/docenv` 成功创建并实际生成中文 Word。
- 2026-09-29：标准 `render_docx.py` 因本机缺 LibreOffice `soffice` 停止；本机 Microsoft Word 将测试 DOCX 导为 PDF，`pdftoppm` 逐页出图并人工查看。终稿仍须完整逐页审查，不能把预检算终稿验收。
- 2026-09-29：OpenAlex 脚本首轮使用 Python urllib 遇到本机 SSL 证书链验证错误，12 查询均未返回记录，留下 raw error 文件；改用可验证连接的系统 curl 请求后重新运行。首次失败不计实际检索结果。
