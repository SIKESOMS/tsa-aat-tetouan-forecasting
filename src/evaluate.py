"""Evaluation helpers and result aggregation for the baseline vs proposed comparison."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .config import TABLE_DIR
from .models import (
    mae,
    rmse,
    mape,
    smape,
    naive24_in_sample_mae,
)


def build_comparison_table(
    baseline_metrics: dict[str, float],
    proposed_metrics: dict[str, float],
    proposed_interval_metrics: dict[str, float] | None = None,
) -> dict[str, Any]:
    rows = []
    for metric in ["MAE", "RMSE", "MAPE", "sMAPE", "MASE"]:
        b = baseline_metrics.get(metric)
        p = proposed_metrics.get(metric)
        if b is None or p is None:
            continue
        gain = (b - p) / b * 100.0 if b else float("nan")
        rows.append({
            "metric": metric,
            "baseline": round(b, 2),
            "proposed": round(p, 2),
            "absolute_improvement": round(b - p, 2),
            "relative_improvement_pct": round(gain, 2),
            "better": "proposed" if p < b else ("baseline" if b < p else "tie"),
        })

    # interval metrics
    extra = []
    if proposed_interval_metrics:
        for k in ["PCR_coverage_95", "PCR_width_mean", "PCR_width_rel", "Winkler_95"]:
            if k in proposed_interval_metrics:
                extra.append({"metric": k, "proposed": round(proposed_interval_metrics[k], 4), "baseline_or_note": "baseline uses Gaussian analytic CI (M2)"})
    return {"point_forecast": rows, "interval_forecast": extra, "n_test_hours": 336, "n_origins": 14}


def write_csv_table(df: pd.DataFrame, name: str) -> str:
    path = TABLE_DIR / name
    df.to_csv(path, index=False)
    return str(path.relative_to(TABLE_DIR.parent.parent))


def write_forecast_csv(
    hourly: pd.DataFrame,
    test_start: int,
    baseline_pred: np.ndarray,
    proposed_pred: np.ndarray,
    proposed_lower: np.ndarray,
    proposed_upper: np.ndarray,
) -> str:
    idx = hourly.index[test_start : test_start + 336]
    df = pd.DataFrame({
        "datetime": idx,
        "actual_total_kw": hourly["total_kw"].iloc[test_start : test_start + 336].values,
        "baseline_sarima_kw": baseline_pred,
        "proposed_ensemble_kw": proposed_pred,
        "proposed_lower_95_kw": proposed_lower,
        "proposed_upper_95_kw": proposed_upper,
    })
    path = TABLE_DIR / "forecast_test.csv"
    df.to_csv(path, index=False)
    return str(path.relative_to(TABLE_DIR.parent.parent))


def peak_error_table(
    actual: np.ndarray,
    baseline_pred: np.ndarray,
    proposed_pred: np.ndarray,
) -> dict[str, Any]:
    thr = float(np.percentile(actual, 80))
    mask = actual >= thr
    return {
        "peak_threshold_kw": round(thr, 1),
        "n_peak_hours": int(mask.sum()),
        "baseline_MAE_peak_kw": round(mae(actual[mask], baseline_pred[mask]), 2),
        "proposed_MAE_peak_kw": round(mae(actual[mask], proposed_pred[mask]), 2),
        "baseline_MAE_offpeak_kw": round(mae(actual[~mask], baseline_pred[~mask]), 2),
        "proposed_MAE_offpeak_kw": round(mae(actual[~mask], proposed_pred[~mask]), 2),
        "peak_share_of_load_pct": round(float(np.mean(actual[mask]) / float(np.mean(actual)) * 100), 2),
    }
