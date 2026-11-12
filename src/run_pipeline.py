"""End-to-end experimental pipeline.

Produces:
  * outputs/tables/model_comparison.csv
  * outputs/tables/forecast_test.csv
  * outputs/tables/peak_error.csv
  * outputs/figures/fig09..fig12.png
  * outputs/tables/run_results.json
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from .config import FIG_DIR, TABLE_DIR, TEST_HOURS
from .data_prep import load_10min, to_hourly
from .evaluate import build_comparison_table, peak_error_table, write_csv_table, write_forecast_csv
from .models import (
    evaluate_baseline_rolling,
    evaluate_proposed_rolling,
    plot_error_distribution,
    plot_model_comparison,
    plot_per_horizon_mae,
)

RUN_LOG = Path(__file__).resolve().parents[1] / "outputs" / "run_log.txt"


def log(text: str) -> None:
    line = text + "\n"
    if RUN_LOG.exists():
        RUN_LOG.write_text(RUN_LOG.read_text(encoding="utf-8") + line, encoding="utf-8")
    else:
        RUN_LOG.write_text(line, encoding="utf-8")
    print(text)


def main() -> dict:
    t0 = time.time()
    log("=" * 70)
    log("TSA AAT — day-ahead load forecasting pipeline (rolling origin, 14 days)")
    log("=" * 70)

    log("1) Loading data...")
    df10 = load_10min()
    hourly, q = to_hourly(df10)
    y = hourly["total_kw"].values
    idx = hourly.index

    test_start = len(y) - TEST_HOURS
    actual = y[test_start:]

    log(f"   hourly obs: {len(hourly)} | test: {TEST_HOURS}h (14 days) | "
        f"actual mean {actual.mean():.1f} kW")

    # ---------------- Baseline ----------------
    log("2) Baseline SARIMA (rolling day-ahead, 120-day window) ...")
    t0b = time.time()
    baseline = evaluate_baseline_rolling(hourly, window_days=120)
    log(f"   fit {baseline.fit_time_s:.1f}s | MAE {baseline.metrics['MAE']:.1f} "
        f"RMSE {baseline.metrics['RMSE']:.1f} MAPE {baseline.metrics['MAPE']:.2f}% "
        f"MASE {baseline.metrics['MASE']:.3f}")

    # ---------------- Proposed ----------------
    log("3) Proposed ensemble (rolling day-ahead, Fourier + GB residual + conformal) ...")
    t2 = time.time()
    (
        proposed_pred,
        proposed_lower,
        proposed_upper,
        proposed_se,
        proposed_metrics,
        proposed_per_h,
        proposed_meta,
    ) = evaluate_proposed_rolling(hourly, window_days=120)
    log(f"   {time.time() - t2:.1f}s | MAE {proposed_metrics['MAE']:.1f} "
        f"RMSE {proposed_metrics['RMSE']:.1f} MAPE {proposed_metrics['MAPE']:.2f}% "
        f"MASE {proposed_metrics['MASE']:.3f} | coverage {proposed_metrics['PCR_coverage_95']*100:.1f}%")

    # ---------------- Comparison ----------------
    log("4) Building comparison tables ...")
    comp = build_comparison_table(baseline.metrics, proposed_metrics, proposed_metrics)
    df_comp = pd.DataFrame(comp["point_forecast"])
    write_csv_table(df_comp, "model_comparison.csv")
    log(f"   point-forecast table written ({len(df_comp)} metrics)")

    df_forecast = pd.read_csv(
        write_forecast_csv(hourly, test_start, baseline.predictions, proposed_pred, proposed_lower, proposed_upper)
    )
    log(f"   forecast_test.csv written ({len(df_forecast)} rows)")

    peak = peak_error_table(actual, baseline.predictions, proposed_pred)
    df_peak = pd.DataFrame([peak])
    write_csv_table(df_peak, "peak_error.csv")
    log(f"   peak-error table written (threshold {peak['peak_threshold_kw']:.0f} kW, "
        f"n_peak {peak['n_peak_hours']})")

    # ---------------- Figures ----------------
    log("5) Generating comparison figures ...")
    p_fc, p_ic = plot_model_comparison(hourly, baseline, proposed_pred, proposed_lower, proposed_upper, actual, test_start)
    p_ed = plot_error_distribution(baseline, proposed_pred, actual)
    p_ph = plot_per_horizon_mae(baseline, proposed_per_h)
    log(f"   {p_fc}\n   {p_ic}\n   {p_ed}\n   {p_ph}")

    # ---------------- Results JSON ----------------
    results = {
        "baseline": {
            "MAE_kw": round(baseline.metrics["MAE"], 2),
            "RMSE_kw": round(baseline.metrics["RMSE"], 2),
            "MAPE_pct": round(baseline.metrics["MAPE"], 2),
            "sMAPE_pct": round(baseline.metrics["sMAPE"], 2),
            "MASE": round(baseline.metrics["MASE"], 3),
            "PCR_coverage_95_pct": round(baseline.metrics["PCR_coverage_95"] * 100, 2),
            "PCR_width_mean_kw": round(baseline.metrics["PCR_width_mean"], 2),
            "fit_time_s": round(baseline.fit_time_s, 1),
            "per_horizon_MAE_kw": {str(h): round(baseline.per_horizon[h]["MAE"], 1) for h in range(1, 25)},
        },
        "proposed": {
            "MAE_kw": round(proposed_metrics["MAE"], 2),
            "RMSE_kw": round(proposed_metrics["RMSE"], 2),
            "MAPE_pct": round(proposed_metrics["MAPE"], 2),
            "sMAPE_pct": round(proposed_metrics["sMAPE"], 2),
            "MASE": round(proposed_metrics["MASE"], 3),
            "anchor_MAE_kw": round(proposed_metrics["anchor_MAE"], 2),
            "corr_MAE_kw": round(proposed_metrics["corr_MAE"], 2),
            "PCR_coverage_95_pct": round(proposed_metrics["PCR_coverage_95"] * 100, 2),
            "PCR_width_mean_kw": round(proposed_metrics["PCR_width_mean"], 2),
            "PCR_width_rel_pct": round(proposed_metrics["PCR_width_rel"] * 100, 2),
            "Winkler_95_kw": round(proposed_metrics["Winkler_95"], 2),
            "conformal_q": round(proposed_metrics["conformal_q"], 3),
            "cal_norm_n": proposed_metrics["cal_norm_n"],
            "fit_time_s": round(time.time() - t2, 1),
            "meta": proposed_meta,
            "per_horizon_MAE_kw": {str(h): round(proposed_per_h[h]["MAE"], 1) for h in range(1, 25)},
            "per_horizon_anchor_MAE_kw": {str(h): round(proposed_per_h[h]["anchor_MAE"], 1) for h in range(1, 25)},
        },
        "comparison": comp,
        "peak_error": peak,
        "figures": {
            "forecast_comparison": p_fc,
            "interval_coverage": p_ic,
            "error_distribution": p_ed,
            "per_horizon_mae": p_ph,
        },
        "total_seconds": round(time.time() - t0, 1),
    }

    path = TABLE_DIR / "run_results.json"
    path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    log(f"6) results -> {path}")
    log(f"   total pipeline {time.time() - t0:.1f}s")
    return results


if __name__ == "__main__":
    main()
