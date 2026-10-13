# 复现指南

在项目根目录运行，Python3.12。数据和源项目只读，根目录ActiveModel不会切换。离线研究环境使用numpy2.3.5、pandas2.2.3、scipy1.18.1、pytest9.1.1；实际已安装版本以`outputs/execution_environment.json`为准。运行候选包只需其`requirements.txt`。

完整研究复现需要当前项目的既有材料，不能仅复制本研究目录后从零运行：

- `dataset original/`的六芯65个原始CSV；官方`data/`及未修改的framework/入口/sample_data。
- 指定外部源项目`/Users/shane/Desktop/项目/Current State_Challenge1`。保持检查也会读取计划`SOURCE_SNAPSHOT.json`中列出的外部绝对路径；迁移机器后应显式登记路径映射，不能修改SHA冒充同源。
- `research/phase2_temperature_improvement/runs/M7_frozen_manifest.json`、`runs/M3_B_age_sixfold_v2/predictions.csv`及`scripts/run_m6_mechanism.py`。
- `research/phase2_method_exploration/data_manifests/d1_v15_cropped_events.csv`、`d1_v15_target_visibility.csv`及`runs/M9_D1_v15_inputs_v1/summary.json`。
- `research/phase2_validation/preflight/downloaded_data/phase1_label_inventory.csv`，以及本轮计划目录`SOURCE_SNAPSHOT.json`和本轮已冻结`outputs/panel_scoring.csv`。

这些是源溯、对齐和负对照的依赖；独立ZIP推理不依赖它们。原始文件为本机只读数据，未随研究ZIP打包。

```bash
python3.12 -m venv research/phase1_transfer_ab/.venv
research/phase1_transfer_ab/.venv/bin/python -m pip install numpy==2.3.5 pandas==2.2.3 scipy==1.18.1 pytest==9.1.1
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
```

以下每行依次运行，替换`PY`为该venv的Python路径；本轮实际使用`research/phase2_validation/.venv/bin/python`。准备脚本首先核对源原始文件和v1.5裁剪的SHA，若输入变化立即终止。

```bash
PY=research/phase1_transfer_ab/.venv/bin/python
$PY research/phase1_transfer_ab/scripts/prepare_data.py
$PY research/phase1_transfer_ab/scripts/source_interface_smoke.py
$PY research/phase1_transfer_ab/scripts/reproduce_source.py
$PY research/phase1_transfer_ab/scripts/run_nested_validation.py
$PY research/phase1_transfer_ab/scripts/run_fusion_validation.py
$PY research/phase1_transfer_ab/scripts/compare_existing_routes.py
$PY research/phase1_transfer_ab/scripts/export_prior.py
$PY research/phase1_transfer_ab/scripts/replay_official.py
$PY research/phase1_transfer_ab/scripts/audit_exposure.py
$PY research/phase1_transfer_ab/scripts/run_mechanisms.py
$PY -m pytest research/phase1_transfer_ab/tests -q --junitxml=research/phase1_transfer_ab/outputs/tests.xml
$PY research/phase1_transfer_ab/scripts/build_candidate.py
```

完整重拟合可删除本研究的`artifacts/model_cache/*.json`再运行嵌套脚本；保留缓存时会按源代码哈希和训练实体集合复用。冻结输入改变时不能只改文件绕过校验，应建立新实验版本。随机种子20261010。source_prior的全六芯最终拟合不参与留芯评分。

干净环境验证，独立解压研究ZIP并执行官方未修改入口：

```bash
$PY -m venv research/phase1_transfer_ab/runs/clean_validation/.venv
research/phase1_transfer_ab/runs/clean_validation/.venv/bin/python -m pip install -r research/phase1_transfer_ab/candidates/phase1_ab/requirements.txt
$PY research/phase1_transfer_ab/scripts/validate_candidate.py
$PY research/phase1_transfer_ab/scripts/finalize_evidence.py
```

`validate_candidate.py`清空并重建本研究的extracted目录，运行sample validator、全量train/test和三个乱序独立进程；不修改根文件。`finalize_evidence.py`核验保持不变的文件/配置、汇总验收并建立复现文件哈希清单。

原阶段1接口smoke由`source_interface_smoke.py`在`runs/source_smoke/`隔离复制指定项目后运行其官方validator，日志为`runs/source_smoke.log`；六折数值重现由`reproduce_source.py`完成。source_smoke脚本只清空本研究复制目录，指定源项目保持只读。复制目录和venv为可重建本地工作文件，不需纳入版本控制。

所有主评价CSV保留原始精度，展示四舍五入不改变计分。官方没有CK1–CK7真值，任何复现都应保留`official_capacity_performance=not_testable`。
