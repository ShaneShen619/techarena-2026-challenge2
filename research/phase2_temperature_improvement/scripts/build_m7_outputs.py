"""Independent summary tables, cell-cluster bootstrap, and report figures."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

TASK = Path(__file__).resolve().parents[1]
OUT = TASK / "outputs"
FIG = OUT / "figures"


def save(name: str) -> None:
    plt.tight_layout()
    plt.savefig(FIG / name, dpi=160, bbox_inches="tight")
    plt.close()


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    metrics = json.loads((OUT / "acceptance.json").read_text())["metrics"]
    methods = ["A_old", "A_order_only", "A_no_true_pair", "A_bugfix", "A_no_carry",
               "A_disagreement_gate", "B_age", "B_multi_noT", "B_multi_noT_efc",
               "M4_wave_noT", "M4_wave_T", "M4_multi_efc_T", "final"]
    rows = []
    for method in methods:
        if method not in metrics:
            continue
        item = metrics[method]
        rows.append({"method": method, "n_targets": item["n"],
                     "macro_mae_pp": item["macro_mae_pp"],
                     "macro_rmse_pp": item["macro_rmse_pp"],
                     "p95_abs_pp": item["p95_abs_error_pp"],
                     "max_abs_pp": item["max_abs_error_pp"],
                     "status": "selected development candidate" if method == "final" else "development comparison"})
    ablations = pd.DataFrame(rows)
    ablations.to_csv(OUT / "ablation_results.csv", index=False)
    predictions = pd.read_csv(OUT / "predictions.csv")
    panel = pd.read_csv(OUT / "panel_main.csv")
    feature = pd.read_csv(TASK / "runs/M4_feature_audit_v1/features.csv")
    pivot = predictions.loc[predictions.method.isin(["A_old", "A_bugfix", "final"])].merge(
        panel[["cell_id", "target_ordinal", "target_soh_pp"]], on=["cell_id", "target_ordinal"])
    # Cell-cluster uncertainty, rather than treating 180 adjacent targets as independent.
    rng = np.random.default_rng(20260928)
    cell_names = sorted(panel.cell_id.unique())
    final_cell = np.array([metrics["final"]["per_cell_mae_pp"][c] for c in cell_names])
    old_cell = np.array([metrics["A_old"]["per_cell_mae_pp"][c] for c in cell_names])
    fixed_cell = np.array([metrics["B_multi_noT"]["per_cell_mae_pp"][c] for c in cell_names])
    draws = rng.integers(0, len(cell_names), size=(2000, len(cell_names)))
    boot = pd.DataFrame({
        "final_macro_mae_pp": final_cell[draws].mean(axis=1),
        "old_a_reduction_fraction": 1.-final_cell[draws].mean(axis=1)/old_cell[draws].mean(axis=1),
        "final_minus_fixed_baseline_mae_pp": final_cell[draws].mean(axis=1)-fixed_cell[draws].mean(axis=1),
    })
    boot.to_csv(OUT / "cluster_bootstrap_draws.csv", index=False)
    boot.quantile([.025, .5, .975]).to_csv(OUT / "cluster_bootstrap_interval.csv")

    thermal = pd.read_csv(OUT / "thermal_held_cell.csv")
    actual = thermal.drop_duplicates("heldout_cell").set_index("heldout_cell")
    fig, ax = plt.subplots(figsize=(6.2, 5.0))
    for method, marker, color in (("nominal", "x", "#b65a3b"), ("physical", "o", "#216f96")):
        group = thermal.loc[thermal.method.eq(method)]
        if len(group):
            ax.scatter(group.heldout_measured_lifetime_mean_C_diagnostic_only,
                       group.predicted_T_eff_C, label=method, marker=marker, color=color, s=60)
    ax.plot([25, 70], [25, 70], color="#555", linestyle="--")
    ax.set(xlabel="Measured lifetime mean T (C, diagnostic)", ylabel="LOCO predicted T (C)",
           title="Training-only thermal surface vs nominal temperature")
    ax.legend()
    save("thermal_surface_vs_measured.png")

    fig, axes = plt.subplots(2, 3, figsize=(14, 7), sharex=False, sharey=True)
    for ax, cell in zip(axes.flat, cell_names):
        truth = panel.loc[panel.cell_id.eq(cell)].sort_values("target_ordinal")
        ax.plot(truth.target_ordinal, truth.target_soh_pp, color="black", lw=2, label="P1 label")
        for method, color in (("A_old", "#bc6b3c"), ("final", "#167a90")):
            pred = predictions.loc[predictions.cell_id.eq(cell) & predictions.method.eq(method)].sort_values("target_ordinal")
            ax.plot(pred.target_ordinal, pred.prediction_soh_pp, color=color, label=method)
        ax.set_title(cell.replace("102Ah_", ""), fontsize=9)
        ax.set_xlabel("Frozen target ordinal")
        ax.set_ylabel("SOH (pp)")
    axes.flat[0].legend(loc="best", fontsize=8)
    save("six_cell_predictions.png")

    fault_cells = ["102Ah_45degC_1C_cell1", "102Ah_25degC_1C_cell3", "102Ah_55degC_1C_cell3"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
    for ax, cell in zip(axes, fault_cells):
        truth = panel.loc[panel.cell_id.eq(cell)].sort_values("target_ordinal")
        ax.plot(truth.target_ordinal, truth.target_soh_pp, color="black", lw=2, label="P1 label")
        for method, color in (("A_old", "#bc6b3c"), ("A_bugfix", "#9770ad"), ("final", "#167a90")):
            pred = predictions.loc[predictions.cell_id.eq(cell) & predictions.method.eq(method)].sort_values("target_ordinal")
            ax.plot(pred.target_ordinal, pred.prediction_soh_pp, color=color, label=method)
        ax.set_title(cell.replace("102Ah_", ""), fontsize=9)
        ax.set_xlabel("Frozen target ordinal")
    axes[0].set_ylabel("SOH (pp)")
    axes[0].legend(fontsize=7)
    save("three_fault_cases_before_after.png")

    final = pivot.loc[pivot.method.eq("final")].merge(feature[["cell_id", "target_ordinal", "temp_C", "delta_temp_C"]],
                                                      on=["cell_id", "target_ordinal"])
    final["error_pp"] = final.prediction_soh_pp-final.target_soh_pp
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    for ax, col, label in ((axes[0], "temp_C", "Recent event T (C)"),
                           (axes[1], "delta_temp_C", "Recent - early T (C)")):
        for cell in cell_names:
            g = final.loc[final.cell_id.eq(cell)]
            ax.scatter(g[col], g.error_pp, s=15, alpha=.6, label=cell.replace("102Ah_", ""))
        ax.axhline(0, color="#555", lw=1)
        ax.set(xlabel=label, ylabel="Final residual (pp)")
    axes[1].legend(fontsize=6, ncol=2)
    save("residual_vs_temperature.png")

    fig, ax = plt.subplots(figsize=(8.5, 4.7))
    selected = ablations.loc[ablations.method.isin(["A_old", "A_bugfix", "B_age", "B_multi_noT",
                                                     "B_multi_noT_efc", "M4_multi_efc_T"])]
    ax.bar(selected.method, selected.macro_mae_pp, color=["#bc6b3c", "#9770ad", "#879253",
                                                  "#6c87a1", "#4b9ba5", "#167a90"])
    ax.set_ylabel("Six-cell macro MAE (pp)")
    ax.tick_params(axis="x", rotation=30)
    save("ablation_macro_mae.png")

    stress = pd.read_csv(TASK / "runs/M6_temperature_stress_v1/summary.csv")
    bias = stress.loc[stress.scenario.str.contains("bias")].copy()
    bias["offset"] = bias.scenario.str.extract(r"bias_([+-][0-9.]+)C").astype(float)
    bias = bias.sort_values("offset")
    fig, ax = plt.subplots(figsize=(7.2, 4.3))
    ax.plot(bias.offset, bias.macro_mae_pp, "o-", color="#167a90")
    ax.axhline(metrics["final"]["macro_mae_pp"], color="#555", linestyle="--", label="clean")
    ax.set(xlabel="Uniform sensor bias (C)", ylabel="Six-cell macro MAE (pp)")
    ax.legend()
    save("temperature_bias_stress.png")

    mechanism = pd.read_csv(TASK / "runs/M6_mechanism_v1/results.csv")
    fig, ax = plt.subplots(figsize=(6.3, 5.4))
    for scenario, group in mechanism.groupby("scenario"):
        ax.scatter(group.target_pack_C20_soh_pp, group.estimate_soh_pp, s=14, alpha=.7, label=scenario)
    ax.plot([60, 105], [60, 105], color="#555", linestyle="--")
    ax.set(xlabel="Independent 4S C/20 truth (pp)", ylabel="Official fallback estimate (pp)",
           title="Mechanism scenarios; diagnostic only")
    ax.legend(fontsize=6)
    save("mechanism_truth_vs_fallback.png")
    print("ablation table, bootstrap intervals, seven report figures generated")


if __name__ == "__main__":
    main()
