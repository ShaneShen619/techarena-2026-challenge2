/* Notes and sources, one entry per slide in slide order. Mark each entry with a comment of the form  N · Title  (build.py counts them).
   Source language: Chinese. English: src/notes_en.js. Short sentences, one idea each, plain words.
   Entry: say = opening line, cue = points and click cues, land = closing line, limits = [tag, text],
          src = keys of T, figs = keys of F. */
(function () {
  "use strict";

  /* Evidence tags: same codes as the .ev chips in the slide footers. n = internal document. */
  const TAG = { p: "一手", a: "学术", m: "媒体 / 声明", i: "推断", v: "待核实", n: "内部" };

  /* Sources: key -> [tag, title, publisher and date, url]. No url = no public link. */
  const T = {
    rules: ["p", "TechArena 2026 – Challenge 2 Submission Instructions", "TechArena 组委会 · 2026", ""],
    report: ["n", "TechArena 2026 – Challenge 2 – Student Report (REPORT.md)", "Current State · 2026-10", ""],
    v1: ["n", "Post-Checkup Full-Charge Anchor + Graphite-Step Displacement: Validation Report", "Current State · 2026-10-13", ""],
    v2: ["n", "V2: Phase-Matched 45 °C Step Differencing + Physics β — Validation Report", "Current State · 2026-10-13", ""],
    v3: ["n", "V3: V2 + √t gap branch + β cap + median-of-cells steps — validation report", "Current State · 2026-10-15", ""],
    manifest: ["n", "Open-dataset inventory and screening (DATA_MANIFEST.md)", "Current State · 2026-10", ""],
    naumann: ["a", "Analysis and modeling of calendar aging of a commercial LiFePO4/graphite cell", "Naumann et al. · J. Energy Storage 17 (2018) 153–169", "https://doi.org/10.1016/j.est.2018.01.019"],
    schimpe: ["a", "Comprehensive modeling of temperature-dependent degradation mechanisms in lithium iron phosphate batteries", "Schimpe et al. · J. Electrochem. Soc. 165 (2018) A181", "https://doi.org/10.1149/2.1181714jes"],
    essl: ["p", "ESSL1 / ESSL2 LFP cell and pack ageing data", "Zenodo · CC BY 4.0", "https://zenodo.org/records/20132842"],
    gotion: ["p", "Gotion IFP 53 Ah LFP cell and 1P10S module ageing data", "Mendeley Data · CC BY 4.0", "https://data.mendeley.com/datasets/4nww8p6vxf/1"],
    tempest: ["p", "TEMPEST 280 Ah prismatic LFP ageing data", "Zenodo · CC BY 4.0", "https://zenodo.org/records/20813753"]
  };

  /* Reference figures (R): made by src/figs_gen.py into src/figs.html. */
  const F = {
    anchor: { k: "tpl", t: "fig-anchor", n: "锚点充电细节", d: "8 次检查后充电的条件、充入量和 ε0" },
    detect: { k: "tpl", t: "fig-detect", n: "台阶检测的 6 种方法", d: "定义，以及每种方法下的 MAE" },
    formula: { k: "tpl", t: "fig-formula", n: "公式、分支和 β", d: "同相位分支、√t 缺口分支、各检查点的 β 和 SOH" },
    errtable: { k: "tpl", t: "fig-errtable", n: "代理误差完整表", d: "各版本逐检查点误差；三种 ε 下的 MAE 和最大误差" },
    rejected: { k: "tpl", t: "fig-rejected", n: "被否决的路线", d: "11 条路线和否决原因" },
    opendata: { k: "tpl", t: "fig-opendata", n: "开放数据集", d: "3 个 LFP 数据集、许可证和用途" }
  };

  const N = [
    /* 1 · 标题 */
    { say: "我们是 Current State。今天讲两个挑战，重点是 Challenge 2 的 SOH 估计。", cue: ["先读右下角那一句：误差约为官方基线的 3%。"], land: "先看总结。", limits: [["v", "3% 是代理误差的比值，不是官方分数。"]], src: ["report"], figs: [] },
    /* 2 · 总结 */
    {
      say: "整场只有一条主线：在 LFP 上，测量容量比推断容量可靠。",
      cue: ["读三条论点：问题、信号、结果。", "右边是路线：先讲 Challenge 1，再讲 Challenge 2 的问题、方法和结果。"],
      land: "先看 Challenge 1。",
      limits: [["v", "Challenge 1 的部分待补。"], ["i", "MAE 0.12 pp 是 ε0 + 0.4 下的代理误差。"]],
      src: ["report"], figs: []
    },
    /* 3 · C1 方法（待补） */
    { say: "[待补：Challenge 1 方法的开场句。]", cue: ["[待补]"], land: "[待补]", limits: [["v", "整页待补。"]], src: [], figs: [] },
    /* 4 · C1 结果（待补） */
    { say: "[待补：Challenge 1 结果的开场句。]", cue: ["[待补]"], land: "下面讲 Challenge 2。", limits: [["v", "整页待补。"]], src: [], figs: [] },
    /* 5 · C2 问题 */
    {
      say: "Challenge 2 只给了一个容量标签，而 LFP 的电压几乎不随电量变化。",
      cue: ["时间轴：25 °C 和 45 °C 交替；第 3 段缺失，正好在 CK2 之前。", "标签：只有 CK0。CK1–CK7 隐藏，用于评分。", "难点：官方基线偏高 2.6–5.3 pp，我们早期的路线也偏乐观。"],
      land: "所以我们去找能直接测量容量的信号。第一个是锚点。",
      limits: [["n", "早期三条路线的 3–5 pp 来自团队内部报告。"]],
      src: ["rules", "report"], figs: []
    },
    /* 6 · 锚点 */
    {
      say: "每次检查之后，电池组都从近空充到满。这次充电的充入量，几乎就是当时的容量。",
      cue: ["指图：8 个点从 100.12 降到 91.95 Ah。", "右上：充电协议每次相同。", "右下：加一个固定偏置 ε，换算到检查口径。按 R 看充电细节。"],
      land: "锚点每月一次。两次锚点之间的变化，用石墨台阶跟踪。",
      limits: [["v", "25 °C 锚点另加的 0.4 Ah 是假设。"], ["i", "起点状态在检查和充电之间抵消，依赖检查协议，未证实。"]],
      src: ["report", "v1"], figs: ["anchor"]
    },
    /* 7 · 石墨台阶 */
    {
      say: "约每 5 天有一次固定的深放电。它越过石墨分阶台阶，台阶的位置随锂损失移动。",
      cue: ["指图：台阶深度从 32.81 降到 25.87 Ah，41 次都找到了。", "右上：固定程序，最后越过台阶。", "右下：两次取中位数，不依赖单一方法或单只电芯。按 R 看 6 种检测方法。"],
      land: "台阶有两个问题：它只看到锂损失，而且受两种非老化效应影响。下一页解决。",
      limits: [["i", "台阶只反映活性锂损失（LLI），看不到全部正负极活性材料损失。"]],
      src: ["report", "v1"], figs: ["detect"]
    },
    /* 8 · 同相位、β、缺口 */
    {
      say: "台阶有两种不是老化的偏移：温度和锚点后的第一次放电。只比较同温度、同相位的台阶，它们就抵消了。",
      cue: ["指图：虚线圈是锚点后的第一次放电，深约 0.4 Ah。", "方块比圆点深：45 °C 比 25 °C 深约 0.18 Ah。", "两个红点都是月末的 45 °C 台阶，相减就是一个月的变化。", "右边：β 修正台阶看不到的那部分损失；CK2 用 √t 补缺口。按 R 看公式和 β 表。"],
      land: "这就是整个模型。下面看它的误差。",
      limits: [["i", "锚点后偏移最可能是测量效应；如果是真实回弹，见第 12 页。"], ["v", "√t 只用于 CK2，它的指数是假设。"]],
      src: ["report", "v2", "v3", "naumann", "schimpe"], figs: ["formula"]
    },
    /* 9 · 结果 */
    {
      say: "在代理标签上，我们的 MAE 是 0.12 pp，官方基线是 4.30 pp。",
      cue: ["左图：灰色是基线，红色是我们；7 个检查点都在 0.24 pp 以内。", "右图：第一步锚点贡献最大；后面三步主要降最大误差。", "按 R 看三种 ε 下的完整表。"],
      land: "这些都是代理误差。下一页说明验证有多严格。",
      limits: [["v", "代理标签不是隐藏真值。"], ["i", "ε0 下最大误差是 0.60 pp（CK2）。"]],
      src: ["report"], figs: ["errtable"]
    },
    /* 10 · 验证 */
    {
      say: "我们用四种方式检查结果是否可信。",
      cue: ["因果：换掉未来数据，输出不变。", "事先登记：协议先冻结，再评估。", "压力测试：截断和删减数据后仍稳定。", "否决：7 条备选路线都没有超过 V2。按 R 看否决原因。"],
      land: "下面讲这个方法的创新点。",
      limits: [["v", "代理值在开发中都看过，所以是探索性验证。"]],
      src: ["report", "v2", "v3"], figs: ["rejected"]
    },
    /* 11 · 创新 */
    {
      say: "我们没有用更复杂的模型。我们把 BMS 已有的两个信号变成了容量观测。",
      cue: ["从左到右读五个块：直接观测、同相位、物理 β、数据效率、可迁移。", "强调：只用官方数据；开放数据只用来界定风险。"],
      land: "每一项都有物理含义，所以也能说清楚它在哪里会出错。",
      limits: [["i", "可迁移性是推断，没有在第二个电池组上验证。"]],
      src: ["report", "manifest"], figs: []
    },
    /* 12 · 可解释性与局限 */
    {
      say: "每一项都对应一个物理量。已知风险有 5 个，最大约 0.45 pp。",
      cue: ["左边：四项的物理含义。", "右图：红条是最大的风险，锚点后偏移如果是真实回弹。", "多数风险让后期估计偏高。按 R 看开放数据集。"],
      land: "最后是三个发现和我们的决策。",
      limits: [["v", "风险大小来自敏感性分析和开放数据，不是对隐藏真值的测量。"]],
      src: ["report", "manifest", "gotion", "tempest", "essl"], figs: ["opendata"]
    },
    /* 13 · 结论 */
    {
      say: "三个发现改变了我们的做法。",
      cue: ["每张卡从上往下读：发现、数字、决策。", "第一张：测量，不推断。", "第二张：比较同类，不加修正。", "第三张：剩下的误差在测量口径，用排行榜反馈校准 ε。"],
      land: "谢谢。欢迎提问。",
      limits: [["i", "每月老化 0.45–1.33 Ah 由相邻锚点相减得到。"], ["i", "第三个决策是团队的下一步计划。"]],
      src: ["report", "v1", "v2", "v3"], figs: []
    }
  ];

  /* Resolve keys once, so the deck code reads plain objects. An unknown key is an error. */
  const out = N.map(function (n) {
    return {
      say: n.say, cue: n.cue || [], land: n.land || "", limits: n.limits || [],
      src: (n.src || []).map(function (k) { const s = T[k]; if (!s) throw new Error("Unknown source " + k); return { tag: s[0], title: s[1], meta: s[2], url: s[3] || "" }; }),
      figs: (n.figs || []).map(function (k) { const f = F[k]; if (!f) throw new Error("Unknown figure " + k); return Object.assign({ key: k }, f); })
    };
  });

  /* Other languages (src/notes_<lang>.js sets window.NOTES_TR[lang]): same slide order; say, cue, land, the limit
     texts, tag names and figure names. Sources keep their original titles. A missing field falls back to the source.
     Every language gets its own arrays, so an edit in one language cannot change another. */
  const langs = {};
  const tr = window.NOTES_TR || {};
  Object.keys(tr).forEach(function (lang) {
    const Z = tr[lang] || {};
    langs[lang] = {
      tags: Object.assign({}, TAG, Z.tags || {}),
      slides: out.map(function (o, i) {
        const z = (Z.slides || [])[i] || {};
        return Object.assign({}, o, {
          say: z.say != null ? z.say : o.say,
          cue: o.cue.map(function (c, k) { return (z.cue || [])[k] != null ? z.cue[k] : c; }),
          land: z.land != null ? z.land : o.land,
          limits: o.limits.map(function (l, k) { return [l[0], (z.limits || [])[k] != null ? z.limits[k] : l[1]]; }),
          figs: o.figs.map(function (f) { const t = (Z.figs || {})[f.key]; return t ? Object.assign({}, f, { n: t[0], d: t[1] }) : f; })
        });
      })
    };
  });
  const SRC = (window.I18N_DATA && window.I18N_DATA.source) || "en";
  langs[SRC] = { slides: out, tags: TAG };
  window.NOTES = { slides: out, tags: TAG, langs: langs };
})();
