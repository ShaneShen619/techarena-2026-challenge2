"""Shared static-figure style: reference categorical palette (validated), thin marks, recessive grid."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e4e3df"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
SP_COLOR = {25: SERIES[0], 45: SERIES[1]}
SP_MARKER = {25: "o", 45: "^"}   # secondary encoding: identity never by colour alone


def setup():
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": INK2, "axes.labelcolor": INK, "text.color": INK, "xtick.color": INK2, "ytick.color": INK2,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.spines.top": False,
        "axes.spines.right": False, "lines.linewidth": 2.0, "lines.markersize": 6, "font.size": 9,
        "axes.titlesize": 10, "legend.frameon": False, "figure.dpi": 110, "savefig.dpi": 130,
    })
    return plt
