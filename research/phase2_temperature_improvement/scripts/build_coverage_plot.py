"""Visualize the independent event-stress error and fresh-evidence coverage."""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

TASK = Path(__file__).resolve().parents[1]


def main() -> None:
    data = pd.read_csv(TASK / "runs/M6_event_stress_v1/summary.csv")
    selected = data.loc[data.scenario.isin([
        "clean_event_replay", "stuck_35C", "random_missing_20pct",
        "contiguous_missing_20pct",
    ])].copy()
    labels = {"clean_event_replay": "clean", "bias_+1C": "+1°C", "bias_-1C": "−1°C",
              "drift_+3C": "drift", "stuck_35C": "stuck 35°C",
              "random_missing_20pct": "random missing",
              "contiguous_missing_20pct": "block missing",
              "temperature_event_shift_1": "one-event shift"}
    fig, ax = plt.subplots(figsize=(7.0, 4.1), dpi=170)
    for row in selected.itertuples(index=False):
        x = 100.*row.evidence_coverage
        color = "#c2553d" if row.scenario == "stuck_35C" else "#1b6b87"
        if row.scenario == "contiguous_missing_20pct": color = "#9b662d"
        ax.scatter(x, row.macro_mae_pp, s=48, color=color, zorder=3)
        offset = (.45, .014) if row.scenario != "clean_event_replay" else (-3.6, -.02)
        ax.annotate(labels[row.scenario], (x, row.macro_mae_pp),
                    xytext=(x+offset[0], row.macro_mae_pp+offset[1]), fontsize=8)
    ax.axvline(90., color="#777777", ls="--", lw=1, label="hard coverage minimum")
    ax.axhline(float(selected.loc[selected.scenario.eq("clean_event_replay"), "macro_mae_pp"].iloc[0]),
               color="#aaaaaa", ls=":", lw=1)
    ax.set(xlim=(72, 101), ylim=(.97, 1.50), xlabel="Fresh-event evidence coverage (%)",
           ylabel="Six-cell macro MAE (pp)")
    ax.grid(alpha=.18)
    ax.legend(loc="upper left", frameon=False, fontsize=8)
    fig.tight_layout()
    output = TASK / "outputs/figures/error_vs_coverage.png"
    fig.savefig(output)
    plt.close(fig)
    print(output)


if __name__ == "__main__":
    main()
