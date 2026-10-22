"""Reference figures for the Notes and sources panel. Writes src/figs.html (hidden <template> blocks).

A figure is a function that returns one SVG (or HTML) string. Register it in FIGURES with its template id;
notes.js refers to it with { k: "tpl", t: "<template id>" }.
Style: deck tokens; diagram rules: orthogonal connectors, label gap of 6 px or more, 4 px grid,
max 2 accent groups, legend strip at the bottom, svg with title and desc.
Run:  python3 src/figs_gen.py   (then python3 src/build.py)
"""
import json
import os
import subprocess
from typing import Iterable

KATEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "katex", "katex.min.js")

INK, MUT, SOFT, ACC, ACCT, RULE = "#141b24", "#46515e", "#7a8794", "#c2412d", "#fbe9e5", "#d9dfe5"


def esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;")


def txt(x: float, y: float, s: str, size: int = 16, fill: str = MUT, weight: int = 400, anchor: str = "start",
        mono: bool = False, ls: str = "", extra: str = "") -> str:
    cls = ' class="m"' if mono else ""
    sp = f' letter-spacing="{ls}"' if ls else ""
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}"{cls}{sp}{extra}>{esc(s)}</text>')


def box(x: float, y: float, w: float, h: float, name: str, sub: Iterable[str] = (), focal: bool = False,
        dashed: bool = False, tag: str = "", name_size: int = 20) -> str:
    """A node: white mask rect first (hides connectors under it), then the visible box."""
    st, fl, sw = (ACC, ACCT, 2) if focal else (INK, "#fff", 1.5)
    da = ' stroke-dasharray="6 5"' if dashed else ""
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#fff"/>'
    s += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fl}" stroke="{st}" stroke-width="{sw}"{da}/>'
    cx, top = x + w / 2, y + (52 if tag else 32)
    if tag:
        s += txt(x + 16, y + 24, tag, 16, ACC if focal else SOFT, 500, mono=True, ls="0.08em")
    s += txt(cx, top, name, name_size, INK, 600, "middle")
    for i, line in enumerate(sub):
        s += txt(cx, top + 26 + i * 22, line, 16, MUT, 400, "middle")
    return s


def svg_open(slug: str, title: str, desc: str, w: int, h: int) -> str:
    return (f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-labelledby="{slug}-title {slug}-desc">'
            f'<title id="{slug}-title">{esc(title)}</title><desc id="{slug}-desc">{esc(desc)}</desc>')


def marker(slug: str) -> str:
    """Arrow heads: #slug-a (grey) and #slug-ac (accent)."""
    return (f'<defs><marker id="{slug}-a" markerUnits="userSpaceOnUse" markerWidth="12" markerHeight="10" refX="11" refY="5" orient="auto">'
            f'<polygon points="0 0,12 5,0 10" fill="{MUT}"/></marker>'
            f'<marker id="{slug}-ac" markerUnits="userSpaceOnUse" markerWidth="12" markerHeight="10" refX="11" refY="5" orient="auto">'
            f'<polygon points="0 0,12 5,0 10" fill="{ACC}"/></marker></defs>')


def legend(y: int, w: int, items: Iterable[str]) -> str:
    s = f'<line x1="24" y1="{y}" x2="{w - 24}" y2="{y}" stroke="{RULE}" stroke-width="1"/>'
    x = 24
    for it in items:
        s += txt(x, y + 32, it, 16)
        x += 24 + len(it) * 9
    return s


def tex(items: list, display: bool = True) -> list:
    """Render TeX strings to KaTeX HTML at build time (needs node; no runtime script, works offline).
    Use it for formulas in reference figures and on slides; build.py adds the KaTeX CSS when it finds the output.
    Write units and named superscripts with \\mathrm{} (P^{\\mathrm{grid}}), or they render as italic products."""
    js = ("const k=require(process.argv[1]);const a=JSON.parse(require('fs').readFileSync(0,'utf8'));"
          "process.stdout.write(JSON.stringify(a.map(t=>k.renderToString(t,{displayMode:%s,throwOnError:true,output:'html'}))));"
          % ("true" if display else "false"))
    r = subprocess.run(["node", "-e", js, KATEX], input=json.dumps(items), capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


# Line icons: 40×40, stroke only, one colour. Use them where a picture names a thing faster than a word
# (industries, assets, actors, steps). icon("ship", "#2f67a6") → inline SVG; put them in .icrow on a slide.
ICONS = {
    "factory": '<rect x="8" y="6" width="10" height="28" rx="2"/><path d="M8 14h10M8 22h10M22 34V18l8-5v21M4 34h32"/>',
    "chiller": '<path d="M20 4v32M6 12l28 16M6 28l28-16M16 7l4 4 4-4M16 33l4-4 4 4"/>',
    "water": '<path d="M4 12h18a6 6 0 0 1 6 6v3M10 8v8M6 8h8"/><path d="M28 26c-3 4-3 6 0 7s3-3 0-7z" fill="currentColor"/>',
    "ship": '<path d="M4 24h32l-5 9H9zM12 24v-8h14v8M18 16v-7h5v7M4 37c4-2 8 2 12 0s8 2 12 0 8 2 8 0"/>',
    "fan": '<rect x="5" y="5" width="30" height="30" rx="4"/><circle cx="20" cy="20" r="3"/><path d="M20 17c0-6 6-8 7-4M23 20c6 0 8 6 4 7M20 23c0 6-6 8-7 4M17 20c-6 0-8-6-4-7"/>',
    "battery": '<rect x="6" y="11" width="26" height="18" rx="3"/><path d="M32 17h3v6h-3M11 16v8M16 16v8M21 16v8"/>',
    "solar": '<path d="M6 30l5-14h18l5 14zM10 23h20M17 16l-2 14M23 16l2 14M20 4v5M11 7l2 3M29 7l-2 3"/>',
    "grid": '<path d="M20 4l-8 32M20 4l8 32M14 28h12M16 18h8M8 12h24M8 12v4M32 12v4"/>',
    "genset": '<rect x="5" y="14" width="24" height="16" rx="2"/><path d="M29 18h4v8h-4M10 30v4M24 30v4M9 8h8v6M19 17l-4 6h5l-3 5"/>',
    "server": '<rect x="7" y="5" width="26" height="9" rx="2"/><rect x="7" y="16" width="26" height="9" rx="2"/><rect x="7" y="27" width="26" height="9" rx="2"/><path d="M12 9.5h2M12 20.5h2M12 31.5h2"/>',
    "chip": '<rect x="11" y="11" width="18" height="18" rx="2"/><path d="M15 5v6M20 5v6M25 5v6M15 29v6M20 29v6M25 29v6M5 15h6M5 20h6M5 25h6M29 15h6M29 20h6M29 25h6"/>',
    "plug": '<path d="M14 4v8M26 4v8M10 12h20v8a10 10 0 0 1-20 0zM20 30v6"/>',
    "forecast": '<path d="M4 32h32M6 28l8-9 6 5 8-12"/><path d="M28 12l6-4" stroke-dasharray="3 3"/><circle cx="28" cy="12" r="2"/>',
    "clock": '<circle cx="20" cy="20" r="15"/><path d="M20 10v10l7 4"/>',
    "money": '<rect x="4" y="11" width="32" height="18" rx="3"/><circle cx="20" cy="20" r="5"/><path d="M9 16v8M31 16v8"/>',
    "shield": '<path d="M20 4l13 5v9c0 9-6 15-13 18-7-3-13-9-13-18V9zM14 20l4 4 8-9"/>',
    "people": '<circle cx="14" cy="13" r="5"/><circle cx="27" cy="14" r="4"/><path d="M4 34c0-7 4-11 10-11s10 4 10 11M24 23c6 0 10 3 10 10"/>',
    "building": '<path d="M8 36V6h16v30M24 16h8v20M4 36h32M12 11h2M18 11h2M12 17h2M18 17h2M12 23h2M18 23h2M17 36v-6h-4v6"/>',
    "truck": '<path d="M3 10h20v18H3zM23 16h8l6 6v6H23M3 28h34"/><circle cx="10" cy="31" r="3"/><circle cx="30" cy="31" r="3"/>',
    "check": '<rect x="5" y="5" width="30" height="30" rx="4"/><path d="M12 20l6 6 11-12"/>',
}


def icon(name: str, color: str = "#2f67a6", sw: float = 2.5) -> str:
    return (f'<svg class="ico" viewBox="0 0 40 40" aria-hidden="true" style="color:{color}" stroke="currentColor" '
            f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>')


# ---------------------------------------------------------------- deck figures (HTML tables; .rf styles in custom.css)
# Numbers come from materials/ (file and section named in each figure's note line).
import csv  # noqa: E402

MAT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "materials")


def table(head: list, rows: list, our_rows: Iterable[int] = (), cls: str = "") -> str:
    h = "".join(f"<th>{esc(c)}</th>" for c in head)
    body = ""
    for i, r in enumerate(rows):
        tr = ' class="our"' if i in our_rows else ""
        body += f"<tr{tr}>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>"
    c = f' class="{cls}"' if cls else ""
    return f"<table{c}><thead><tr>{h}</tr></thead><tbody>{body}</tbody></table>"


def fig_anchor() -> str:
    with open(os.path.join(MAT, "A1_full_charges.csv"), encoding="utf8") as f:
        rows = list(csv.DictReader(f))
    out = []
    for i, r in enumerate(rows):
        v = [float(r[f"start_cell{k}_V"]) for k in range(1, 5)]
        out.append([f"CK{i} 后", r["t_start"][:10], f'{r["setpoint_C"]} °C', f'{float(r["rest_before_h"]):.1f}',
                    f"{min(v):.2f}–{max(v):.2f}", f'{float(r["I_end_A"]):.2f}', f'{float(r["Q_Ah"]):.3f}',
                    f'{float(r["integral_minus_counter_Ah"]):+.3f}'])
    fx = tex([r"\varepsilon_0 = 100.41 - 100.122 = 0.288\ \mathrm{Ah}",
              r"Q_{\mathrm{CK}}(k) \approx Q_{\mathrm{fc}}(k) + \varepsilon_0 + 0.4\ \mathrm{Ah}\quad(25\,^{\circ}\mathrm{C})"])
    return ('<div class="rf"><h3>锚点：检查后的完整充电</h3>'
            "<p>每次检查后的第一段运行，都以一次从近空到 14.0 V 恒压结束的充电开头。充入量取电流积分。</p>"
            + table(["锚点", "开始日期", "箱温", "充前静置 h", "起点 V/芯", "结束电流 A", "充入量 Ah", "积分 − 计数器 Ah"], out)
            + f'<div class="fx">{fx[0]}</div><div class="fx">{fx[1]}</div>'
            '<p class="note">ε0 由 CK0 的已知容量定出。25 °C 锚点另加的 0.4 Ah 是假设（代理范围 ε0 … ε0 + 0.8）。'
            "来源：A1_full_charges.csv；REPORT.md §1。</p></div>")


def fig_detect() -> str:
    rows = [["main（主方法）", "约 10 A 段内，上平台（15–25 Ah）与下平台（42–50 Ah）中位电压的中点首次穿越", "0.291", "0.216"],
            ["band_narrow", "更窄的电流带", "0.278", "0.217"],
            ["windows −3", "两个平台窗口前移 3 Ah", "0.373", "0.274"],
            ["windows +3", "两个平台窗口后移 3 Ah", "0.412", "0.304"],
            ["dvdq_peak", "dV/dQ 峰（0.25 Ah 网格，噪声约为其他方法的 4 倍）", "0.404", "0.333"],
            ["ir_corrected", "内阻校正后的电压", "0.321", "0.238"]]
    return ('<div class="rf"><h3>台阶检测：6 种方法</h3>'
            "<p>41 次放电全部定位到台阶。4 芯极差中位数 0.63 Ah。各方法之间主要差一个常数（中位 0.74 Ah），差分时抵消。</p>"
            + table(["方法", "定义", "V1 MAE pp", "V2 MAE pp"], rows, cls="rf-l")
            + "<p>提交版：每只电芯取 6 种方法的中位数，每次放电取 4 只电芯的中位数。用任意 5 种方法重建，仍优于上一版。</p>"
            '<p class="note">MAE 为 ε0 + 0.4 下的代理误差。来源：V1 报告 §1、§3；V2 报告 §4；REPORT.md §1、§3。</p></div>')


def fig_formula() -> str:
    fx = tex([r"Q_{\mathrm{est}}(\mathrm{CK}_k) = Q_{\mathrm{fc}}(k{-}1) + \varepsilon_0 + \varepsilon_{\mathrm{extra}}"
              r" + \beta_k\,\big[E_{45}(k{-}1) - E_{45}(k{-}2) + r\,(d(k{-}1) - d(k{-}2))\big]",
              r"Q_{\mathrm{est}} = Q_{\mathrm{fc}}(k{-}1) + \varepsilon_0 + \varepsilon_{\mathrm{extra}} - a\,\big(\sqrt{t_k} - \sqrt{t_{k-1}}\big),"
              r"\qquad t = \int e^{\frac{E_a}{R}\left(\frac{1}{318.15} - \frac{1}{T(\tau)}\right)} d\tau",
              r"\mathrm{SOH} = 100 \cdot Q_{\mathrm{est}} / 102\ \mathrm{Ah}"])
    rows = [["CK1", "回退：锚点 + 台阶变化", "1", "95.984"], ["CK2", "√t 缺口外推", "—", "94.507"],
            ["CK3", "回退：锚点 + 台阶变化", "1", "93.600"], ["CK4", "同相位", "1.06", "92.821"],
            ["CK5", "同相位", "1.24", "92.015"], ["CK6", "同相位", "1.41", "91.426"], ["CK7", "同相位", "1.51", "90.765"]]
    return ('<div class="rf"><h3>公式、分支和 β</h3>'
            f'<p>同相位分支（CK4–CK7）：</p><div class="fx">{fx[0]}</div>'
            f'<p>数据缺口分支（CK2；Ea = 20.6 kJ/mol，45 °C 等效天数）：</p><div class="fx">{fx[1]}</div><div class="fx">{fx[2]}</div>'
            + table(["检查点", "分支", "β", "SOH 估计 %"], rows, our_rows=range(3, 7))
            + '<p class="note">E45(m)：第 m 月最后一次 45 °C 台阶；d：它到检查日的天数；r：本月 45 °C 台阶的 Theil–Sen 斜率。'
            "β：可见 25 °C 锚点的满充损失对“台阶→满充端”损失的过原点最小二乘比，向 1 收缩。来源：REPORT.md §1、§4；V2 报告 §2。</p></div>")


def fig_errtable() -> str:
    rows = [["提交版（V2 + 温度加权 √t + 稳健台阶）", "+0.21", "+0.04", "+0.14", "+0.24", "+0.08", "−0.07", "−0.06", "0.12", "0.24"],
            ["V2 + 温度加权 √t（上一版）", "+0.22", "+0.04", "+0.08", "+0.23", "+0.15", "−0.16", "−0.00", "0.13", "0.23"],
            ["V2 + 日历时间 √t", "+0.22", "−0.02", "+0.08", "+0.23", "+0.15", "−0.16", "−0.00", "0.12", "0.23"],
            ["V2（无缺口分支）", "+0.22", "+0.67", "+0.08", "+0.23", "+0.15", "−0.16", "−0.00", "0.22", "0.67"],
            ["V1（不同相位）", "+0.22", "+0.67", "+0.08", "+0.28", "−0.11", "−0.40", "−0.28", "0.29", "0.67"],
            ["官方 ExampleModel", "+2.64", "+4.41", "+4.15", "+5.05", "+5.28", "+4.22", "+4.32", "4.30", "5.28"]]
    eps = [["提交版", "0.191", "0.120", "0.142", "0.602", "0.237", "0.237"],
           ["官方 ExampleModel", "4.69", "4.30", "3.90", "5.67", "5.28", "4.88"]]
    return ('<div class="rf"><h3>代理误差：完整表</h3><p>ε = ε0 + 0.4 时的逐检查点误差（估计 − 代理，pp）：</p>'
            + table(["模型", "CK1", "CK2", "CK3", "CK4", "CK5", "CK6", "CK7", "MAE", "最大"], rows, our_rows=[0])
            + "<p>三种 ε 下的 MAE 和最大误差（pp）：</p>"
            + table(["模型", "MAE ε0", "ε0+0.4", "ε0+0.8", "最大 ε0", "ε0+0.4", "ε0+0.8"], eps, our_rows=[0])
            + '<p class="note">代理 = 检查后完整充电 + ε，不是隐藏真值。ε0 下最大误差 0.60 pp 出现在 CK2。'
            "ExampleModel 三种 ε 的值按 V1 报告 §2 的范围排列。来源：REPORT.md §4；README.md 当前状态；V1 报告 §2。</p></div>")


def fig_rejected() -> str:
    rows = [["月末值的稳健回归", "没有超过 V2"],
            ["日常运行中的台阶穿越", "两次满充之间库仑计数不闭合"],
            ["静置点伪 OCV", "台阶附近没有静置"],
            ["充电顶部 21 Ah 内的特征", "没有找到可用特征"],
            ["缺口期按分段台阶速率外推", "过度修正；√t 分支改为外推锚点间损失"],
            ["整条锚点充电曲线配准", "被充电起点状态混淆"],
            ["状态空间融合", "没有超过 V2"],
            ["β 上限 1.2（V3）", "抬高 CK5–CK7，与 ε 漂移风险同向"],
            ["4 芯直接取中位数（V3）", "dV/dQ 方法下 MAE 0.333 → 0.448"],
            ["4 芯取最小值", "所有留出门槛都不通过"],
            ["开放数据迁移、ECM 联合估计、多段平台特征（早期）", "都从平台中段推断容量，偏乐观 3–5 pp"]]
    return ('<div class="rf"><h3>被否决的路线</h3><p>每条路线都先登记、后评估。下表是否决原因。</p>'
            + table(["路线", "否决原因"], rows, cls="rf-l")
            + '<p class="note">来源：REPORT.md §3、§4；V3 报告。</p></div>')


def fig_opendata() -> str:
    rows = [["ESSL1 / ESSL2：LFP 102 Ah 与 105 Ah 电芯，16S、15S 实验室电池组", "Zenodo 10.5281/zenodo.20132842", "CC BY 4.0",
             "0–8% 衰减内的台阶 β：电池组 1.1–1.2，电芯 0.9–1.1。用来判断 β；β 上限被否决。"],
            ["Gotion IFP 53 Ah LFP 电芯 + 1P10S 模组（每 50 次循环标定）", "Mendeley 10.17632/4nww8p6vxf.1", "CC BY 4.0",
             "满充 Ah 相对独立标定的漂移 ε：每衰减 1 Ah 约 −0.03 Ah。只用于风险说明。"],
            ["TEMPEST 280 Ah 方形 LFP（每 50 次循环 0.1C RPT）", "Zenodo 10.5281/zenodo.20813753", "CC BY 4.0",
             "ε 漂移每 Ah 衰减 −0.035 Ah；RPT 后没有容量回弹（≤ 0.1%）。只用于风险说明。"]]
    return ('<div class="rf"><h3>开放数据：只用来界定风险</h3><p>模型只用官方数据，不做预训练。下面 3 个开放数据集用来判断 ε 和 β 的假设。</p>'
            + table(["数据集", "来源", "许可证", "用途"], rows, cls="rf-l")
            + '<p class="note">来源：REPORT.md §2；DATA_MANIFEST.md。</p></div>')


FIGURES = [("fig-anchor", fig_anchor), ("fig-detect", fig_detect), ("fig-formula", fig_formula),
           ("fig-errtable", fig_errtable), ("fig-rejected", fig_rejected), ("fig-opendata", fig_opendata)]


def main() -> None:
    out = "\n".join(f'<template id="{tid}">{fn()}</template>' for tid, fn in FIGURES) + "\n"
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figs.html")
    with open(path, "w", encoding="utf8") as f:
        f.write(out)
    print("figs.html", len(out), "bytes")


if __name__ == "__main__":
    main()
