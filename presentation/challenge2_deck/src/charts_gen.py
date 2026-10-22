"""Main-slide charts for this deck. Reads materials/*.csv and writes inline SVG into src/slides.html between the
comment markers  <!-- svg:NAME -->  and  <!-- /svg:NAME -->.  Run:  python3 src/charts_gen.py  (then src/build.py).
Colours: d1 blue = 25 °C, d3 orange = 45 °C, accent red = our model and the values it uses, grey = baseline.
Numbers that are not in the CSVs come from materials/REPORT.md (sections named next to them)."""
import csv
import os
import re
import statistics as st
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
MAT = os.path.join(HERE, "..", "materials")
SLIDES = os.path.join(HERE, "slides.html")

INK, MUT, SOFT, RULE, TINT = "#141b24", "#46515e", "#7a8794", "#d9dfe5", "#f0f3f6"
ACC, ACCS, C25, C45, GREY = "#c2412d", "#fbe9e5", "#2f67a6", "#d9691c", "#9aa5b1"

MONTHS = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月"]


def esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def T(x, y, s, size=17, fill=MUT, weight=400, anchor="start", mono=False):
    cls = ' class="m"' if mono else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}"{cls}>{esc(s)}</text>')


def svg_open(slug, title, desc, w, h):
    return (f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-labelledby="{slug}-t {slug}-d">'
            f'<title id="{slug}-t">{esc(title)}</title><desc id="{slug}-d">{esc(desc)}</desc>')


def day(s: str) -> float:
    """Days since 2025-01-01 (fractional)."""
    d = datetime.fromisoformat(s.strip())
    return (d - datetime(2025, 1, 1)).total_seconds() / 86400


class Axis:
    """Linear map from data to stage pixels."""
    def __init__(self, d0, d1, p0, p1):
        self.d0, self.d1, self.p0, self.p1 = d0, d1, p0, p1

    def __call__(self, v):
        return self.p0 + (v - self.d0) / (self.d1 - self.d0) * (self.p1 - self.p0)


def read(name):
    with open(os.path.join(MAT, name), encoding="utf8") as f:
        return list(csv.DictReader(f))


CKS = [(r["checkup"], day(r["date"])) for r in read("evaluation_points.csv")]


def month_ticks(x, y_axis, y_lab, d_lo, d_hi):
    s = []
    for m in range(1, 10):
        d = day(f"2025-{m:02d}-01")
        if d_lo <= d <= d_hi:
            s.append(f'<line x1="{x(d):.1f}" y1="{y_axis}" x2="{x(d):.1f}" y2="{y_axis + 6}" stroke="{SOFT}" stroke-width="1.5"/>')
            s.append(T(x(d) + 4, y_lab, MONTHS[m - 1], 16, SOFT))
    return s


def ck_lines(x, y0, y1, d_lo, d_hi, label_y, only=None):
    s = []
    for name, d in CKS:
        if d_lo <= d <= d_hi and (only is None or name in only):
            s.append(f'<line x1="{x(d):.1f}" y1="{y0}" x2="{x(d):.1f}" y2="{y1}" stroke="{SOFT}" stroke-width="1.5" stroke-dasharray="4 5"/>')
            s.append(T(x(d), label_y, name, 16, MUT, 500, "middle", mono=True))
    return s


# ------------------------------------------------------------------ slide 5: campaign timeline
def timeline():
    W, H = 1030, 330
    x = Axis(day("2025-01-08"), day("2025-09-16"), 20, W - 20)
    s = [svg_open("tl", "Campaign timeline", "Thirteen operating segments from January to September 2025, alternating "
                  "25 and 45 °C, with the eight checkup dates. Segment 3 is missing.", W, H),
         '<defs><pattern id="tl-h" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
         f'<rect width="8" height="8" fill="#fff"/><line x1="0" y1="0" x2="0" y2="8" stroke="{SOFT}" stroke-width="3"/></pattern></defs>']
    s += ck_lines(x, 44, 228, -10, 400, 32)
    for r in read("segments.csv"):
        a, b = x(day(r["start"])), x(day(r["end"]))
        if r["setpoint_C"] == "missing":
            s.append(f'<rect x="{a:.1f}" y="60" width="{b - a:.1f}" height="150" fill="url(#tl-h)" stroke="{SOFT}" stroke-width="1.5"/>')
            s.append(f'<rect x="{(a + b) / 2 - 24:.1f}" y="123" width="48" height="24" fill="#fff"/>')
            s.append(T((a + b) / 2, 141, "缺失", 17, INK, 600, "middle"))
        else:
            col = C45 if r["setpoint_C"] == "45" else C25
            s.append(f'<rect x="{a:.1f}" y="60" width="{b - a:.1f}" height="150" rx="3" fill="{col}"/>')
    s.append(f'<line x1="20" y1="238" x2="{W - 20}" y2="238" stroke="{RULE}" stroke-width="1.5"/>')
    s += month_ticks(x, 238, 262, x.d0, x.d1)
    lx = 20
    for col, lab in [(C25, "25 °C 运行段"), (C45, "45 °C 运行段")]:
        s.append(f'<rect x="{lx}" y="298" width="22" height="14" rx="2" fill="{col}"/>')
        s.append(T(lx + 30, 311, lab, 17, MUT))
        lx += 170
    s.append(f'<rect x="{lx}" y="298" width="22" height="14" fill="url(#tl-h)" stroke="{SOFT}"/>')
    s.append(T(lx + 30, 311, "第 3 段缺失（2 月 19 日–3 月 11 日）", 16, MUT))
    s.append("</svg>")
    return "".join(s)


# ------------------------------------------------------------------ slide 6: post-checkup full charges
def anchors():
    W, H = 1020, 440
    rows = read("A1_full_charges.csv")
    pts = [(day(r["t_start"]), float(r["Q_Ah"])) for r in rows]
    x = Axis(day("2025-01-08"), day("2025-09-12"), 70, W - 30)
    y = Axis(91.0, 101.2, 390, 30)
    s = [svg_open("an", "Post-checkup full charges", "The charged Ah of the eight post-checkup full charges falls "
                  "from 100.12 Ah in January to 91.95 Ah in September.", W, H)]
    for v in range(92, 102, 2):
        s.append(f'<line x1="70" y1="{y(v):.1f}" x2="{W - 30}" y2="{y(v):.1f}" stroke="{RULE}" stroke-width="1"/>')
        s.append(T(60, y(v) + 6, str(v), 16, SOFT, anchor="end", mono=True))
    s.append(T(60, 18, "Ah", 16, SOFT, anchor="end", mono=True))
    s.append(f'<line x1="70" y1="390" x2="{W - 30}" y2="390" stroke="{SOFT}" stroke-width="1.5"/>')
    s += month_ticks(x, 390, 414, x.d0, x.d1)
    ck0 = CKS[0][1]
    s.append(f'<circle cx="{x(ck0):.1f}" cy="{y(100.41):.1f}" r="7" fill="#fff" stroke="{INK}" stroke-width="2.5"/>')
    s.append(T(x(ck0) + 14, y(100.41) - 10, "CK0 标签 100.41", 16, INK, 500))
    d = " ".join(f"{'M' if i == 0 else 'L'} {x(a):.1f} {y(b):.1f}" for i, (a, b) in enumerate(pts))
    s.append(f'<path d="{d}" fill="none" stroke="{ACC}" stroke-width="2.5"/>')
    for i, (a, b) in enumerate(pts):
        s.append(f'<circle cx="{x(a):.1f}" cy="{y(b):.1f}" r="7" fill="{ACC}"/>')
        dy = 30 if i == 0 else -16
        s.append(T(x(a), y(b) + dy, f"{b:.2f}", 16, ACC if i in (0, len(pts) - 1) else MUT, 600, "middle", mono=True))
    s.append(f'<circle cx="80" cy="{H - 9}" r="6" fill="{ACC}"/>')
    s.append(T(94, H - 3, "检查后完整充电量 Q_fc", 16, MUT))
    s.append(f'<circle cx="330" cy="{H - 9}" r="6" fill="#fff" stroke="{INK}" stroke-width="2"/>')
    s.append(T(344, H - 3, "CK0 检查容量（唯一标签）", 16, MUT))
    s.append("</svg>")
    return "".join(s)


# ------------------------------------------------------------------ step events
def step_events():
    """One row per deep discharge: date, set-point, main-method cell mean, robust value (median of 6, then of 4)."""
    ev = {}
    for r in read("A2_step_programs_all_variants.csv"):
        ev.setdefault(r["t_measured"], []).append(r)
    out = []
    for t, rs in sorted(ev.items()):
        main = [r for r in rs if r["variant"] == "main"][0]
        cells = [st.median(float(r[f"step_cell{i}_V"]) for r in rs) for i in range(1, 5)]
        out.append({"d": day(t), "t": t, "temp": int(rs[0]["setpoint_C"]),
                    "main": float(main["step_mean"]), "robust": st.median(cells)})
    return out


def marker(cx, cy, temp, r=6, col=None):
    c = col or (C45 if temp == 45 else C25)
    if temp == 45:
        return f'<rect x="{cx - r:.1f}" y="{cy - r:.1f}" width="{2 * r}" height="{2 * r}" fill="{c}"/>'
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{c}"/>'


# ------------------------------------------------------------------ slide 7: step depth over the campaign
def steps():
    W, H = 1020, 440
    ev = step_events()
    x = Axis(day("2025-01-08"), day("2025-09-12"), 70, W - 30)
    y = Axis(25.4, 33.4, 380, 40)
    s = [svg_open("st", "Graphite step depth", "Step depth below the end of charge for 41 deep discharges. It falls "
                  "from 32.81 Ah in January to 25.87 Ah in September.", W, H)]
    for v in range(26, 34, 2):
        s.append(f'<line x1="70" y1="{y(v):.1f}" x2="{W - 30}" y2="{y(v):.1f}" stroke="{RULE}" stroke-width="1"/>')
        s.append(T(60, y(v) + 6, str(v), 16, SOFT, anchor="end", mono=True))
    s.append(T(60, 18, "Ah", 16, SOFT, anchor="end", mono=True))
    s += ck_lines(x, 30, 380, x.d0, x.d1, 22)
    s.append(f'<line x1="70" y1="380" x2="{W - 30}" y2="380" stroke="{SOFT}" stroke-width="1.5"/>')
    s += month_ticks(x, 380, 404, x.d0, x.d1)
    for e in ev:
        s.append(marker(x(e["d"]), y(e["main"]), e["temp"]))
    f, l = ev[0], ev[-1]
    s.append(T(x(f["d"]) + 14, y(f["main"]) + 6, f"{f['main']:.2f}", 17, ACC, 600, mono=True))
    s.append(T(x(l["d"]), y(l["main"]) + 30, f"{l['main']:.2f}", 17, ACC, 600, "middle", mono=True))
    s.append(marker(80, H - 9, 25))
    s.append(T(94, H - 3, "25 °C 段内的放电", 16, MUT))
    s.append(marker(280, H - 9, 45))
    s.append(T(294, H - 3, "45 °C 段内的放电", 16, MUT))
    s.append("</svg>")
    return "".join(s)


# ------------------------------------------------------------------ slide 8: phase matching on real data
def phase():
    W, H = 1000, 470
    lo, hi = day("2025-04-10"), day("2025-06-19")
    ev = [e for e in step_events() if lo <= e["d"] <= hi]
    x = Axis(lo, hi, 70, W - 30)
    y = Axis(26.6, 28.25, 410, 40)
    s = [svg_open("ph", "Phase-matched step differencing", "Step depths from April to June 2025. The first discharge "
                  "after each anchor reads deeper, and 45 °C steps read deeper than 25 °C steps. The model subtracts "
                  "the last 45 °C step of two consecutive months.", W, H),
         f'<defs><marker id="ph-a" markerUnits="userSpaceOnUse" markerWidth="12" markerHeight="10" refX="11" refY="5" orient="auto">'
         f'<polygon points="0 0,12 5,0 10" fill="{ACC}"/></marker></defs>']
    for v in (26.8, 27.2, 27.6, 28.0):
        s.append(f'<line x1="70" y1="{y(v):.1f}" x2="{W - 30}" y2="{y(v):.1f}" stroke="{RULE}" stroke-width="1"/>')
        s.append(T(60, y(v) + 6, f"{v:.1f}", 16, SOFT, anchor="end", mono=True))
    s.append(T(60, 18, "Ah", 16, SOFT, anchor="end", mono=True))
    s += ck_lines(x, 30, 410, lo, hi, 22)
    s.append(f'<line x1="70" y1="410" x2="{W - 30}" y2="410" stroke="{SOFT}" stroke-width="1.5"/>')
    s += month_ticks(x, 410, 434, lo, hi)
    # month-end 45 °C steps used by the model: the last 45 °C step before CK4 and before CK5
    ck = dict(CKS)
    e1 = [e for e in ev if e["temp"] == 45 and e["d"] < ck["CK4"]][-1]
    e2 = [e for e in ev if e["temp"] == 45 and ck["CK4"] < e["d"] < ck["CK5"]][-1]
    post = [[e for e in ev if e["d"] > ck[k]][0] for k in ("CK3", "CK4")]   # first discharge after each anchor
    for e in ev:
        if e in (e1, e2):
            continue
        s.append(marker(x(e["d"]), y(e["robust"]), e["temp"]))
    for e in post:
        s.append(f'<circle cx="{x(e["d"]):.1f}" cy="{y(e["robust"]):.1f}" r="13" fill="none" stroke="{INK}" stroke-width="1.8" stroke-dasharray="3 3"/>')
    # bracket: horizontal from e1 level to e2 date, then the drop
    x1, y1, x2, y2 = x(e1["d"]), y(e1["robust"]), x(e2["d"]), y(e2["robust"])
    s.append(f'<path d="M {x1 + 12:.1f} {y1:.1f} H {x2:.1f}" fill="none" stroke="{ACC}" stroke-width="1.8" stroke-dasharray="6 5"/>')
    s.append(f'<path d="M {x2:.1f} {y1:.1f} V {y2 - 12:.1f}" fill="none" stroke="{ACC}" stroke-width="2.5" marker-end="url(#ph-a)"/>')
    for e in (e1, e2):
        s.append(marker(x(e["d"]), y(e["robust"]), 45, 9, ACC))
    dlt = e2["robust"] - e1["robust"]
    s.append(T(x2 - 10, y1 - 14, f"ΔE45 = {dlt:+.2f} Ah", 20, ACC, 700, "end", mono=True))
    s.append(T(x1 - 16, y1 + 32, "E45（CK4 前）", 17, ACC, 600, "end"))
    s.append(T(x2 - 16, y2 + 30, "E45（CK5 前）", 17, ACC, 600, "end"))
    p0 = post[0]
    s.append(T(x(p0["d"]) + 20, y(p0["robust"]) - 8, "锚点后首次放电：深约 0.4 Ah", 16, INK, 500))
    s.append(marker(80, H - 9, 25))
    s.append(T(94, H - 3, "25 °C", 16, MUT))
    s.append(marker(170, H - 9, 45))
    s.append(T(184, H - 3, "45 °C（比 25 °C 深约 0.18 Ah）", 16, MUT))
    s.append(f'<circle cx="460" cy="{H - 9}" r="9" fill="none" stroke="{INK}" stroke-width="1.8" stroke-dasharray="3 3"/>')
    s.append(T(476, H - 3, "锚点后首次放电", 16, MUT))
    s.append(marker(640, H - 9, 45, 7, ACC))
    s.append(T(654, H - 3, "模型使用的月末 45 °C 台阶", 16, MUT))
    s.append("</svg>")
    return "".join(s)


# ------------------------------------------------------------------ slide 9: per-checkup proxy errors (REPORT.md §4)
OURS = [0.21, 0.04, 0.14, 0.24, 0.08, -0.07, -0.06]
BASE = [2.64, 4.41, 4.15, 5.05, 5.28, 4.22, 4.32]


def errors():
    W, H = 1000, 440
    y = Axis(-0.6, 5.9, 380, 24)
    x0, x1 = 70, W - 20
    gw = (x1 - x0) / 7
    s = [svg_open("er", "Proxy error per checkup", "Estimate minus proxy for CK1 to CK7. The official ExampleModel "
                  "reads 2.6 to 5.3 pp high; our model stays within 0.24 pp.", W, H)]
    for v in range(0, 6):
        s.append(f'<line x1="{x0}" y1="{y(v):.1f}" x2="{x1}" y2="{y(v):.1f}" stroke="{RULE if v else SOFT}" stroke-width="{1 if v else 1.8}"/>')
        s.append(T(x0 - 10, y(v) + 6, str(v), 16, SOFT, anchor="end", mono=True))
    s.append(T(x0 - 10, 14, "pp", 16, SOFT, anchor="end", mono=True))
    for i in range(7):
        cx = x0 + gw * (i + 0.5)
        b, o = BASE[i], OURS[i]
        s.append(f'<rect x="{cx - 46:.1f}" y="{y(b):.1f}" width="42" height="{y(0) - y(b):.1f}" fill="{GREY}"/>')
        s.append(T(cx - 25, y(b) - 8, f"+{b:.2f}", 16, MUT, 500, "middle", mono=True))
        top, bot = (y(o), y(0)) if o >= 0 else (y(0), y(o))
        s.append(f'<rect x="{cx + 4:.1f}" y="{top:.1f}" width="42" height="{max(bot - top, 2):.1f}" fill="{ACC}"/>')
        s.append(T(cx + 25, min(top, y(0)) - 8, f"{o:+.2f}", 16, ACC, 700, "middle", mono=True))
        s.append(T(cx, 408, f"CK{i + 1}", 18, INK, 500, "middle", mono=True))
    s.append(f'<rect x="{x0}" y="{H - 16}" width="18" height="12" fill="{GREY}"/>')
    s.append(T(x0 + 26, H - 4, "官方 ExampleModel", 16, MUT))
    s.append(f'<rect x="{x0 + 220}" y="{H - 16}" width="18" height="12" fill="{ACC}"/>')
    s.append(T(x0 + 246, H - 4, "我们的模型（提交版）", 16, MUT))
    s.append("</svg>")
    return "".join(s)


# ------------------------------------------------------------------ slide 9: MAE by version (REPORT.md §4)
VERSIONS = [("官方 ExampleModel", 4.30, GREY), ("V1 锚点 + 台阶", 0.29, ACC), ("V2 同相位 + β", 0.22, ACC),
            ("+ √t 缺口分支", 0.13, ACC), ("+ 稳健台阶（提交版）", 0.12, ACC)]


def versions():
    W, H = 660, 440
    lab_w, bx0, bx1 = 230, 240, 580
    x = Axis(0, 4.3, bx0, bx1)
    s = [svg_open("vs", "MAE by model version", "Proxy MAE falls from 4.30 pp for the official baseline to 0.29 pp "
                  "for V1 and to 0.12 pp for the submitted model.", W, H)]
    rh = 76
    for i, (name, v, col) in enumerate(VERSIONS):
        yy = 20 + i * rh
        last = i == len(VERSIONS) - 1
        s.append(T(lab_w, yy + 31, name, 20, INK if last else MUT, 700 if last else 400, "end"))
        s.append(f'<rect x="{bx0}" y="{yy + 8}" width="{max(x(v) - bx0, 3):.1f}" height="36" fill="{col}" opacity="{1 if last or i == 0 else 0.55}"/>')
        s.append(T(x(v) + 10, yy + 33, f"{v:.2f}", 20, ACC if col == ACC else MUT, 700, mono=True))
    s.append(f'<line x1="{bx0}" y1="12" x2="{bx0}" y2="{20 + len(VERSIONS) * rh}" stroke="{SOFT}" stroke-width="1.5"/>')
    yb = 20 + len(VERSIONS) * rh + 14
    s.append(T(20, yb + 18, "最大误差：5.28 → 0.67 → 0.67 → 0.23 → 0.24 pp", 18, MUT))
    s.append("</svg>")
    return "".join(s)


# ------------------------------------------------------------------ slide 12: known risks (REPORT.md §4, V3 report)
RISKS = [("ε 漂移", "后期估计", 0.0, 0.30, "最多 +0.3"),
         ("锚点后偏移若是真实回弹", "CK3–CK7", 0.0, 0.45, "最多 +0.45"),
         ("CK2 的 √t 假设", "指数 0.4–0.6，起点 ±5 天", -0.35, 0.29, "−0.35 … +0.29"),
         ("β 偏高", "CK7 β = 1.51，若后期 LAM 比例下降", None, -1, "偏低，未量化"),
         ("电芯不均衡", "电芯 1 老化更快；模型跟随中位电芯", None, 1, "偏高，未量化")]


def risks():
    W, H = 1030, 500
    lab_r, ax0, ax1 = 390, 420, 845
    x = Axis(-0.5, 0.5, ax0, ax1)
    rh = 84
    s = [svg_open("rk", "Known risks", "Five known risks with their direction and size in pp. Three are quantified "
                  "(up to 0.45 pp); two have only a known direction.", W, H),
         f'<defs><marker id="rk-a" markerUnits="userSpaceOnUse" markerWidth="12" markerHeight="10" refX="11" refY="5" orient="auto">'
         f'<polygon points="0 0,12 5,0 10" fill="{MUT}"/></marker></defs>']
    top, bot = 26, 26 + len(RISKS) * rh
    for v in (-0.4, -0.2, 0.2, 0.4):
        s.append(f'<line x1="{x(v):.1f}" y1="{top}" x2="{x(v):.1f}" y2="{bot}" stroke="{RULE}" stroke-width="1"/>')
        s.append(T(x(v), bot + 22, f"{v:+.1f}", 16, SOFT, anchor="middle", mono=True))
    s.append(f'<line x1="{x(0):.1f}" y1="{top - 8}" x2="{x(0):.1f}" y2="{bot}" stroke="{INK}" stroke-width="1.8"/>')
    s.append(T(x(0), bot + 22, "0", 16, INK, anchor="middle", mono=True))
    s.append(T(x(-0.5), 16, "← 估计偏低", 16, MUT, 500))
    s.append(T(x(0.5), 16, "估计偏高 →", 16, MUT, 500, "end"))
    for i, (name, sub, a, b, note) in enumerate(RISKS):
        yy = top + i * rh
        if i:
            s.append(f'<line x1="20" y1="{yy}" x2="{W - 20}" y2="{yy}" stroke="{TINT}" stroke-width="1.5"/>')
        s.append(T(lab_r, yy + 36, name, 21, INK, 600, "end"))
        s.append(T(lab_r, yy + 62, sub, 17, SOFT, anchor="end"))
        cy = yy + rh / 2
        if a is not None:
            big = b >= 0.44
            s.append(f'<rect x="{x(a):.1f}" y="{cy - 15:.1f}" width="{x(b) - x(a):.1f}" height="30" rx="3" fill="{ACC if big else GREY}"/>')
            s.append(T(ax1 + 14, cy + 6, note, 17, ACC if big else MUT, 600, mono=True))
        else:
            xe = x(0.3 * b)
            s.append(f'<path d="M {x(0) + 6 * b:.1f} {cy:.1f} H {xe:.1f}" fill="none" stroke="{MUT}" stroke-width="2.5" stroke-dasharray="7 5" marker-end="url(#rk-a)"/>')
            s.append(T(ax1 + 14, cy + 6, note, 17, MUT, 500))
    s.append("</svg>")
    return "".join(s)


CHARTS = {"timeline": timeline, "anchors": anchors, "steps": steps, "phase": phase,
          "errors": errors, "versions": versions, "risks": risks}


def main():
    with open(SLIDES, encoding="utf8") as f:
        html = f.read()
    for name, fn in CHARTS.items():
        pat = re.compile(r"(<!-- svg:%s -->).*?(<!-- /svg:%s -->)" % (name, name), re.S)
        if not pat.search(html):
            raise SystemExit(f"charts_gen: marker svg:{name} not found in slides.html")
        svg = fn()
        html = pat.sub(lambda m: m.group(1) + svg + m.group(2), html)
        print(f"{name}: {len(svg)} bytes")
    with open(SLIDES, "w", encoding="utf8") as f:
        f.write(html)


if __name__ == "__main__":
    main()
