<a id="en"></a>

# Round 18 — Transfer test of the anchor + graphite-step method on the Challenge 1 cells

> **Language:** English · [中文](#zh)

**Status (2026-10-22): registered, self-tests pass, real run pending.**

## What it is

The submitted model (SUB, `MyModel` at commit `6525edf`) has so far been validated only against proxies that share its level. This study tests its **mechanism** where truth exists.

- The data are the six Challenge 1 cells: the same 102 Ah LFP cell type, with a discharge-capacity label on every cycle.
- On each cell, the pack's information structure is emulated:
  - one anchor charge per 30-day window;
  - a program every 5 days, visible only down to 56 Ah below full;
  - the label of the first cycle as the only released label.
- The submitted decision logic then runs **unchanged**. Only event extraction is adapted, and it calls the submitted locator functions.
- Fourteen registered checks follow (C1–C12, with C1b and C2b); read [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md) for the claims, rules and how to read outcomes.

## Run (on the machine that holds the Challenge 1 files)

```bash
cd research/phase2_r18_c1_transfer_20261022
shasum -a 256 -c protocol.sha256                 # WP0: registered files unchanged
python3 -B run_wp1_selftest.py                   # WP1: 16 self-tests, must all pass
python3 -I -B run_wp2_extract.py [--c1-dir DIR]  # WP2: views, facts, causality on the real rows
python3 -B run_wp3_mechanism.py                  # WP3: mechanism checks
python3 -B run_wp4_emulation.py                  # WP4: estimators and registered gates (run once)
```

- Every script takes `--work DIR` to write `cache/` and `outputs/` somewhere else, e.g. for a dry run.
- Dry run on synthetic cells:
  1. generate them with `src/synth.make_cell`;
  2. pass `--c1-dir` and `--cells`;
  3. pass `--work` to the scratch folder.

## Checked so far (cloud session, no Challenge 1 data)

- **Pack faithfulness.** On all of the pack's deep discharges:
  - the step adapter returns the submitted `_robust_step` value bit for bit;
  - it keeps the same discharges;
  - its charge-side top equals the submitted one to 1e-12 Ah.
- **Synthetic end-to-end.** On cells with planted physics:
  - causality holds (future rows replaced by noise give identical predictions);
  - hidden rows never enter;
  - the branches fire as on the pack (fallback at k = 1, phase from k = 2, √t in the gap scenario);
  - planted charge- and discharge-side β are recovered within 0.25;
  - a planted β mismatch is detected;
  - every decision rule evaluates.
- **Lint.** flake8 at 120 columns is clean.

## Layout

See the file table in [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md#4-files). `cache/` is git-ignored. `outputs/` will hold the committed results.

---

<a id="zh"></a>

# 第 18 轮——在 Challenge 1 单芯上检验"锚点 + 石墨台阶"方法的可迁移性

> **语言：** [English](#en) · 中文

**状态（2026-10-22）：已登记，自检通过，真实运行待进行。**

## 这是什么

提交模型（SUB，提交 `6525edf` 的 `MyModel`）到目前为止只在和它共用同一水平的代理上验证过。本研究在有真值的地方检验它的**机理**。

- 数据是 Challenge 1 的六个单芯：同一种 102 Ah LFP 电芯，每个循环都有放电容量标签。
- 在每个单芯上模拟电池组的信息结构：
  - 每个 30 天窗口一次锚点充电；
  - 每 5 天一次程序，只能看到满充以下 56 Ah 的部分；
  - 第一个循环的标签是唯一公开的标签。
- 然后**原样**运行提交的决策逻辑。只有事件提取做了适配，而且它调用的是提交代码里的定位函数。
- 之后是 14 项登记检验（C1–C12，另含 C1b 和 C2b）。论断、规则和结果的读法见 [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md#zh)。

## 运行（在存放 Challenge 1 文件的机器上）

```bash
cd research/phase2_r18_c1_transfer_20261022
shasum -a 256 -c protocol.sha256                 # WP0：登记文件未被改动
python3 -B run_wp1_selftest.py                   # WP1：16 项自检，必须全部通过
python3 -I -B run_wp2_extract.py [--c1-dir DIR]  # WP2：模拟视图、数据事实、真实数据上的因果检查
python3 -B run_wp3_mechanism.py                  # WP3：机理检查
python3 -B run_wp4_emulation.py                  # WP4：估计器和登记门槛（只运行一次）
```

- 每个脚本都接受 `--work DIR`，可以把 `cache/` 和 `outputs/` 写到别处，例如用于空跑。
- 在合成电芯上空跑：
  1. 用 `src/synth.make_cell` 生成合成电芯；
  2. 传入 `--c1-dir` 和 `--cells`；
  3. 把 `--work` 指向临时文件夹。

## 目前已检查的（云端会话，没有 Challenge 1 数据）

- **对电池组的忠实性。** 在电池组的全部深放电上：
  - 台阶适配层返回的值与提交的 `_robust_step` 逐位一致；
  - 保留的放电与提交代码相同；
  - 充电侧 top 与提交代码相差在 1e-12 Ah 以内。
- **合成数据端到端。** 在植入了物理规律的电芯上：
  - 因果性成立（未来数据换成噪声后预测不变）；
  - 隐藏数据从不进入输入；
  - 分支触发与电池组一致（k = 1 走回退，k ≥ 2 走相位，缺口场景走 √t）；
  - 植入的充电侧和放电侧 β 都能在 0.25 以内恢复；
  - 植入的 β 失配能被检出；
  - 每条判定规则都能正常计算。
- **代码检查。** 120 列下 flake8 无告警。

## 目录

见 [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md#4-files) 中的文件表。`cache/` 被 git 忽略；`outputs/` 将存放要提交的结果。
