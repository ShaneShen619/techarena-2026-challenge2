# Git 仓库与本地数据说明

本仓库保存 TechArena 2026 Challenge 2 的代码、项目文档、官方小型数据、文献资料和可管理的实验结果。

## 本机保留的数据

首次上传排除了以下内容，原文件仍保留在本机：

- `TU Darmstadt/`：大型原始 CSV 数据集。
- `dataset original/`：原始电池实验数据。
- `Che-Dataset3.mat`：原始 MAT 数据集。
- 超过 10 MiB 的方法探索和证据验证实验 CSV 输出，具体路径在 `.gitignore` 中。
- Python 虚拟环境、依赖安装包目录、缓存和本地凭据文件。

`LOCAL_DATA_MANIFEST.json` 记录被排除的原始数据和大型 CSV 输出的路径及字节大小。该清单不包含文件内容，Git 仓库不能恢复这些数据；在另一台电脑运行相关分析前，需要另行复制或重新取得数据，并恢复到相同相对路径。

## 第三方代码

下载的第三方代码通过 Git 子模块记录来源与具体版本。克隆时使用：

```sh
git clone --recurse-submodules <仓库地址>
```

如果已经克隆：

```sh
git submodule update --init --recursive
```

## 保存后续修改

```sh
git add -A
git commit -m "Update project"
git push
```

`.gitignore` 中的数据排除规则不会删除本机文件。新增大型数据文件时，应先检查 `git status`，并将其加入忽略规则后再提交。
