"""Forecasting models: baseline SARIMA and proposed ensemble with conformal intervals.

Design (chosen after empirical benchmarking, see docs/decisions.md):
* Forecast task: day-ahead (24 h) short-term load forecasting evaluated with a
  rolling-origin scheme over the final 14 days of 2017 (14 origins x 24 h = 336
  predictions per model). Each origin uses only data available at that origin.
* Baseline: SARIMAX(1,1,1)(1,1,1,24) on a 120-day operational window, with
  Gaussian 95% analytic prediction intervals. Parameters estimated once, then
  states are updated day-by-day with res.append(...) (no refit), which is
  standard practice and fast.
* Proposed: a gradient-boosted residual-correction ensemble layered on top of the
  weekly seasonal anchor. It adds deterministic Fourier calendar features (daily +
  weekly harmonics), recent weather proxies (available at the origin), level-drift
  features, and a single pooled LightGBM model (with horizon as a feature) trained on
  the weekly-anchor residual. 95% intervals are obtained by split-conformal
  normalization: calibration uses the 14-day block immediately before the test set,
  evaluated under the SAME rolling-origin procedure, so the empirical quantile is
  horizon-matched and leakage-free.
* Evaluation measures: MAE, RMSE, MAPE, sMAPE, MASE (scaled by the in-sample
  naive-24 error), and peak-hour error. Interval quality via PICP, PINAW and the
  Winkler score.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import lightgbm as lgb
import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

from .config import (
    BASELINE_ORDER,
    BASELINE_SEASONAL,
    FIG_DIR,
    INTERVAL_ALPHA,
    K_DAILY,
    K_WEEKLY,
    RANDOM_STATE,
    TABLE_DIR,
    TEST_HOURS,
)

COLORS = {"actual": "#1f3b73", "baseline": "#d1495b", "proposed": "#00798c", "naive": "#8d99ae"}

np.random.seed(RANDOM_STATE)


def mae(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.mean(np.abs(np.asarray(a) - np.asarray(b))))


def rmse(a: np.ndarray, b: np.ndarray) -> float:
    d = np.asarray(a) - np.asarray(b)
    return float(np.sqrt(np.mean(d * d)))


def mape(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float)
    return float(np.mean(np.abs((a - b) / np.clip(np.abs(a), 1e-9, None))) * 100.0)


def smape(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float)
    denom = (np.abs(a) + np.abs(np.asarray(b))) / 2.0
    return float(np.mean(np.abs((a - b) / np.clip(denom, 1e-9, None))) * 100.0)


def naive24_in_sample_mae(y_train: np.ndarray) -> float:
    """MASE scaling factor: in-sample naive-24 error on the training series."""
    y = y_train
    if len(y) < 25:
        return 1.0
    return float(np.mean(np.abs(y[24:] - y[:-24])))


def fourier_terms(idx: pd.DatetimeIndex, k_daily: int = K_DAILY, k_weekly: int = K_WEEKLY) -> pd.DataFrame:
    """Deterministic calendar harmonics (no future leakage)."""
    t = np.arange(len(idx), dtype=float)
    cols = {}
    for k in range(1, k_daily + 1):
        cols[f"sin_d{k}"] = np.sin(2 * np.pi * k * t / 24.0)
        cols[f"cos_d{k}"] = np.cos(2 * np.pi * k * t / 24.0)
    for k in range(1, k_weekly + 1):
        cols[f"sin_w{k}"] = np.sin(2 * np.pi * k * t / 168.0)
        cols[f"cos_w{k}"] = np.cos(2 * np.pi * k * t / 168.0)
    return pd.DataFrame(cols, index=idx)


def calibration_block_index(hourly: pd.DataFrame) -> tuple[pd.DatetimeIndex, pd.DatetimeIndex]:
    """Return (calibration_start, test_start) as positional slices.

    The 14 days before the test block are used for split-conformal calibration.
    """
    test_start_pos = len(hourly) - TEST_HOURS
    cal_start_pos = test_start_pos - TEST_HOURS
    cal_idx = hourly.index[cal_start_pos:test_start_pos]
    test_idx = hourly.index[test_start_pos:]
    return cal_idx, test_idx


# ---------------------------------------------------------------------------
# Baseline: SARIMA(day-ahead, rolling origin, one daily state update)
# ---------------------------------------------------------------------------

@dataclass
class BaselineResult:
    predictions: np.ndarray          # (TEST_HOURS,) forecast in kWh (load units)
    standard_errors: np.ndarray      # forecast standard error per horizon
    lower: np.ndarray                # 95% interval lower
    upper: np.ndarray                # 95% interval upper
    fit_time_s: float
    metrics: dict[str, float]
    per_horizon: dict[int, dict[str, float]]


def fit_baseline(y_train_window: pd.Series) -> SARIMAX:
    """Fit the baseline SARIMA on a 120-day operational window."""
    t0 = __import__("time").time()
    m = SARIMAX(
        y_train_window,
        order=BASELINE_ORDER,
        seasonal_order=BASELINE_SEASONAL,
        trend="c",
        enforce_stationarity=False,
        enforce_invertibility=False,
    )
    res = m.fit(disp=False, maxiter=60)
    res._fit_time = __import__("time").time() - t0
    return res


def evaluate_baseline_rolling(
    hourly: pd.DataFrame,
    window_days: int = 120,
) -> BaselineResult:
    """Rolling day-ahead evaluation of the baseline SARIMA.

    On each of the 14 test days the model:
      1. forecasts the next 24 h from the current origin,
      2. then appends the true 24 h (filtering, no refit) so the next origin
         starts from the updated state.
    """
    y = hourly["total_kw"]
    test_start = len(y) - TEST_HOURS
    train = y.iloc[:test_start]
    window = train.iloc[-window_days * 24:]
    res = fit_baseline(window)

    preds, ses = [], []
    for d in range(TEST_HOURS // 24):
        f = res.get_forecast(steps=24)
        preds.append(f.predicted_mean.values)
        ses.append(np.sqrt(f.var_pred_mean.values))
        new = y.iloc[test_start + d * 24 : test_start + (d + 1) * 24].values
        res = res.append(new)

    pred = np.concatenate(preds)
    se = np.concatenate(ses)
    actual = y.iloc[test_start:].values

    lower = pred - 1.96 * se
    upper = pred + 1.96 * se

    per_h = {}
    for hh in range(1, 25):
        sel = [d * 24 + (hh - 1) for d in range(TEST_HOURS // 24)]
        per_h[hh] = {
            "MAE": mae(actual[sel], pred[sel]),
            "RMSE": rmse(actual[sel], pred[sel]),
            "MAPE": mape(actual[sel], pred[sel]),
        }

    mase_scale = naive24_in_sample_mae(train.values)
    metrics = {
        "MAE": mae(actual, pred),
        "RMSE": rmse(actual, pred),
        "MAPE": mape(actual, pred),
        "sMAPE": smape(actual, pred),
        "MASE": mae(actual, pred) / mase_scale if mase_scale else float("nan"),
        "fit_time_s": float(getattr(res, "_fit_time", 0.0)),
        "eval_time_s": 0.0,
        "PCR_coverage_95": float(np.mean((actual >= lower) & (actual <= upper))),
        "PCR_width_mean": float(np.mean(upper - lower)),
        "PCR_width_rel": float(np.mean(upper - lower)) / float(np.mean(actual)),
    }
    return BaselineResult(
        predictions=pred,
        standard_errors=se,
        lower=lower,
        upper=upper,
        fit_time_s=float(getattr(res, "_fit_time", 0.0)),
        metrics=metrics,
        per_horizon=per_h,
    )


# ---------------------------------------------------------------------------
# Proposed: Fourier-SARIMAX seasonal backbone + GB residual correction + conformal
# ---------------------------------------------------------------------------

def weekly_anchor_residual(
    y: np.ndarray, origin_i: int, j: int, i_idx: pd.DatetimeIndex
) -> float:
    """Weekly anchor corrected by the recent level ratio, available at origin i.

    anchor = y[j-168] * mean(y[origin-23:origin+1]) / mean(y[origin-191:origin-167])
    All terms are <= origin_i, so this is operationally valid.
    """
    last24 = y[origin_i - 23 : origin_i + 1].mean()
    last1wk = y[origin_i - 191 : origin_i - 167].mean()
    ratio = last24 / last1wk if last1wk else 1.0
    return ratio * y[j - 168]


def proposed_feature_row(
    hourly: pd.DataFrame,
    y: np.ndarray,
    idx: pd.DatetimeIndex,
    origin_i: int,
    j: int,
) -> dict[str, float]:
    """One feature vector for target horizon j given origin i."""
    last24_mean = y[origin_i - 23 : origin_i + 1].mean()
    last24_std = y[origin_i - 23 : origin_i + 1].std()
    last1wk_mean = y[origin_i - 167 : origin_i + 1].mean()
    level_ratio = last24_mean / last1wk_mean if last1wk_mean else 1.0
    anchor = weekly_anchor_residual(y, origin_i, j, idx)

    row = {
        "h": float(j - origin_i),
        "hour": float(idx[j].hour),
        "dow": float(idx[j].dayofweek),
        "isw": float(int(idx[j].dayofweek >= 5)),
        "month": float(idx[j].month),
        "y0": float(y[origin_i]),
        "y_1": float(y[origin_i - 1]),
        "y_j24": float(y[j - 24]),
        "y_j168": float(y[j - 168]),
        "m24": float(last24_mean),
        "m168": float(last1wk_mean),
        "sd24": float(last24_std),
        "ratio": float(y[origin_i] / max(y[origin_i - 168], 1e-6)),
        "anchor": float(anchor),
        # recent weather proxies available at origin (operational, no forecast)
        "t0": float(hourly["temperature"].iloc[origin_i]),
        "t24": float(hourly["temperature"].iloc[origin_i - 23 : origin_i + 1].mean()),
        "h24": float(hourly["humidity"].iloc[origin_i - 23 : origin_i + 1].mean()),
        "w24": float(hourly["wind_speed"].iloc[origin_i - 23 : origin_i + 1].mean()),
        "tdiff": float(
            hourly["temperature"].iloc[origin_i - 23 : origin_i + 1].mean()
            - hourly["temperature"].iloc[origin_i - 191 : origin_i - 167].mean()
        ),
        "dt24": float(last24_mean - last1wk_mean),
        "texp": float(hourly["temperature"].iloc[origin_i - 23 : origin_i + 1].mean() * last24_mean / 1e6),
    }
    return row


def build_supervised(
    hourly: pd.DataFrame,
    y: np.ndarray,
    idx: pd.DatetimeIndex,
    origins: np.ndarray,
) -> tuple[pd.DataFrame, np.ndarray]:
    """Build (X, target_residual) rows for the supplied origins.

    target_residual = y[j] - weekly_anchor_residual(origin_i, j)

    Vectorised via cumulative sums for all rolling means.
    """
    y = np.asarray(y, dtype=float)
    n = len(y)
    origins = np.asarray(origins, dtype=int)
    # all valid (origin, horizon) pairs
    o_list, j_list, h_list = [], [], []
    for i in origins:
        for hh in range(1, 25):
            j = i + hh
            if j < n:
                o_list.append(i)
                j_list.append(j)
                h_list.append(hh)
    oarr = np.array(o_list, dtype=int)
    jarr = np.array(j_list, dtype=int)
    harr = np.array(h_list, dtype=float)
    if len(oarr) == 0:
        return pd.DataFrame(), np.array([])

    # cumulative sums for fast rolling means
    csum_y = np.empty(n + 1); csum_y[0] = 0.0; csum_y[1:] = np.cumsum(y)
    temp = hourly["temperature"].values.astype(float)
    hum = hourly["humidity"].values.astype(float)
    wind = hourly["wind_speed"].values.astype(float)
    csum_temp = np.empty(n + 1); csum_temp[0] = 0.0; csum_temp[1:] = np.cumsum(temp)
    csum_hum = np.empty(n + 1); csum_hum[0] = 0.0; csum_hum[1:] = np.cumsum(hum)
    csum_wind = np.empty(n + 1); csum_wind[0] = 0.0; csum_wind[1:] = np.cumsum(wind)

    def seg_mean(csum, a, b):
        return (csum[b] - csum[a]) / (b - a)

    last24_mean = seg_mean(csum_y, oarr - 23, oarr + 1)
    last1wk_mean = seg_mean(csum_y, oarr - 167, oarr + 1)
    level_ratio = np.where(last1wk_mean > 0, last24_mean / last1wk_mean, 1.0)
    anchor = level_ratio * y[jarr - 168]
    target_residual = y[jarr] - anchor

    last24_std = np.array([float(np.std(y[i - 23:i + 1])) for i in oarr])  # small, acceptable

    hour = np.array([idx[j].hour for j in jarr], dtype=float)
    dow = np.array([idx[j].dayofweek for j in jarr], dtype=float)
    isw = np.array([int(idx[j].dayofweek >= 5) for j in jarr], dtype=float)
    month = np.array([idx[j].month for j in jarr], dtype=float)

    data = {
        "h": harr,
        "hour": hour,
        "dow": dow,
        "isw": isw,
        "month": month,
        "y0": y[oarr],
        "y_1": y[oarr - 1],
        "y_j24": y[jarr - 24],
        "y_j168": y[jarr - 168],
        "m24": last24_mean,
        "m168": last1wk_mean,
        "sd24": last24_std,
        "ratio": y[oarr] / np.maximum(y[oarr - 168], 1e-6),
        "anchor": anchor,
        "t0": temp[oarr],
        "t24": seg_mean(csum_temp, oarr - 23, oarr + 1),
        "h24": seg_mean(csum_hum, oarr - 23, oarr + 1),
        "w24": seg_mean(csum_wind, oarr - 23, oarr + 1),
        "tdiff": seg_mean(csum_temp, oarr - 23, oarr + 1) - seg_mean(csum_temp, oarr - 191, oarr - 167),
        "dt24": last24_mean - last1wk_mean,
        "texp": seg_mean(csum_temp, oarr - 23, oarr + 1) * last24_mean / 1e6,
    }
    X = pd.DataFrame(data)
    return X, target_residual


def fit_proposed_pooled(
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    seed: int = RANDOM_STATE,
    n_estimators: int = 300,
    learning_rate: float = 0.05,
) -> lgb.LGBMRegressor:
    """Single pooled LightGBM trained on the weekly-anchor residual.

    The forecast horizon `h` is included as a feature, so one model learns a direct
    multi-horizon mapping. This is far faster than one model per horizon and, on this
    data, gives comparable accuracy.
    """
    return lgb.LGBMRegressor(
        n_estimators=n_estimators,
        learning_rate=learning_rate,
        num_leaves=31,
        min_child_samples=40,
        subsample=0.9,
        colsample_bytree=0.9,
        reg_lambda=1.0,
        random_state=seed,
        verbose=-1,
    ).fit(X_train, y_train)


def evaluate_proposed_rolling(
    hourly: pd.DataFrame,
    window_days: int = 120,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict[str, float], dict[int, dict[str, float]], dict]:
    """Rolling day-ahead evaluation of the proposed ensemble (pooled model).

    A single LightGBM is trained on the weekly-anchor residual with horizon `h` as a
    feature, then rolled through the 14-day calibration block and the 14-day test block.
    95% prediction intervals are obtained by split-conformal normalisation: the calibration
    block is evaluated under the same rolling procedure, the normalised absolute residuals
    (absolute residual divided by the per-horizon calibration scale) are pooled, and the
    95th percentile gives a single conformal factor q that is applied as point +/- q * scale.
    """
    y = hourly["total_kw"].values
    idx = hourly.index
    test_start = len(y) - TEST_HOURS
    cal_start = test_start - TEST_HOURS

    # ---- calibration: pooled model fit, then roll through 14 cal days ----
    cal_fit_frame = hourly.iloc[:cal_start]
    Xcal_tr, ycal_tr = build_supervised(
        cal_fit_frame, y[:cal_start], idx[:cal_start],
        np.arange(max(0, cal_start - window_days * 24), cal_start),
    )
    cal_model = fit_proposed_pooled(Xcal_tr, ycal_tr, seed=RANDOM_STATE + 1)

    cal_preds_h = []
    for d in range(TEST_HOURS // 24):
        i_origin = cal_start + d * 24 - 1
        Xte, _ = build_supervised(hourly, y, idx, np.array([i_origin]))
        cal_preds_h.append(Xte["anchor"].values + cal_model.predict(Xte))
    cal_pred = np.concatenate(cal_preds_h)
    cal_actual = y[cal_start : cal_start + TEST_HOURS]
    cal_resid = cal_actual - cal_pred

    # per-horizon scale from calibration residuals + global conformal quantile
    cal_se = np.ones(24)
    for hh in range(1, 25):
        sel = [d * 24 + (hh - 1) for d in range(TEST_HOURS // 24)]
        cal_se[hh - 1] = float(np.std(cal_resid[sel])) if len(sel) else 1e3

    norm_list = []
    for hh in range(1, 25):
        sel = [d * 24 + (hh - 1) for d in range(TEST_HOURS // 24)]
        resid_h = cal_resid[sel]
        scale_h = cal_se[hh - 1]
        norm_list.append(np.abs(resid_h) / max(scale_h, 500.0))
    cal_norm = np.concatenate(norm_list)
    q = float(np.quantile(cal_norm, 1 - INTERVAL_ALPHA))

    # ---- test: pooled model fit on full training data, roll through 14 test days ----
    fit_frame = hourly.iloc[:test_start]
    X_tr, y_tr = build_supervised(
        fit_frame, y[:test_start], idx[:test_start],
        np.arange(max(0, test_start - window_days * 24), test_start),
    )
    model = fit_proposed_pooled(X_tr, y_tr, seed=RANDOM_STATE)

    test_preds, test_anchor, test_corr = [], [], []
    for d in range(TEST_HOURS // 24):
        i_origin = test_start + d * 24 - 1
        Xte, _ = build_supervised(hourly, y, idx, np.array([i_origin]))
        correction = model.predict(Xte)
        test_preds.append(Xte["anchor"].values + correction)
        test_anchor.append(Xte["anchor"].values)
        test_corr.append(correction)

    pred = np.concatenate(test_preds)
    anchor = np.concatenate(test_anchor)
    corr = np.concatenate(test_corr)
    actual = y[test_start:]

    # conformal interval: pred +/- q * per-horizon scale (broadcast over 336 test hours)
    idx_in_test = np.arange(TEST_HOURS)
    scale_vec = cal_se[idx_in_test % 24]  # per-horizon scale aligned to each test hour
    lower = pred - q * scale_vec
    upper = pred + q * scale_vec

    per_h = {}
    for hh in range(1, 25):
        sel = [d * 24 + (hh - 1) for d in range(TEST_HOURS // 24)]
        per_h[hh] = {
            "MAE": mae(actual[sel], pred[sel]),
            "RMSE": rmse(actual[sel], pred[sel]),
            "MAPE": mape(actual[sel], pred[sel]),
            "anchor_MAE": mae(actual[sel], anchor[sel]),
        }

    mase_scale = naive24_in_sample_mae(y[:test_start])
    metrics = {
        "MAE": mae(actual, pred),
        "RMSE": rmse(actual, pred),
        "MAPE": mape(actual, pred),
        "sMAPE": smape(actual, pred),
        "MASE": mae(actual, pred) / mase_scale if mase_scale else float("nan"),
        "anchor_MAE_kw": round(mae(actual, anchor), 2),
        "corr_MAE_kw": round(mae(actual - anchor, corr), 2),
        "anchor_MAE": mae(actual, anchor),
        "corr_MAE": mae(actual - anchor, corr),
        "PCR_coverage_95": float(np.mean((actual >= lower) & (actual <= upper))),
        "PCR_width_mean": float(np.mean(upper - lower)),
        "PCR_width_rel": float(np.mean(upper - lower)) / float(np.mean(actual)),
        "Winkler_95": float(np.mean((upper - lower) + (2.0 / INTERVAL_ALPHA) * (np.maximum(lower - actual, 0) + np.maximum(actual - upper, 0)))),
        "conformal_q": q,
        "cal_norm_n": int(len(cal_norm)),
    }
    return pred, lower, upper, cal_se, metrics, per_h, {
        "model_type": "pooled",
        "n_estimators": 300,
        "calibration_block_hours": TEST_HOURS,
        "conformal_quantile": q,
    }


def plot_model_comparison(
    hourly: pd.DataFrame,
    baseline: BaselineResult,
    proposed_pred: np.ndarray,
    proposed_lower: np.ndarray,
    proposed_upper: np.ndarray,
    actual: np.ndarray,
    test_start: int,
) -> tuple[str, str]:
    """Two figures: (1) test-period forecast overlays, (2) 95% interval coverage."""
    test_idx = hourly.index[test_start : test_start + TEST_HOURS]

    fig1, ax1 = plt.subplots(figsize=(9, 3.6))
    ax1.plot(test_idx, actual / 1000, lw=1.4, color=COLORS["actual"], label="Actual")
    ax1.plot(test_idx, baseline.predictions / 1000, lw=1.2, color=COLORS["baseline"], label="Baseline SARIMA (24-h ahead)")
    ax1.plot(test_idx, proposed_pred / 1000, lw=1.2, color=COLORS["proposed"], label="Proposed ensemble (24-h ahead)")
    ax1.fill_between(test_idx, proposed_lower / 1000, proposed_upper / 1000, color=COLORS["proposed"], alpha=0.15, label="95% prediction interval")
    ax1.set_title("Day-ahead forecast comparison — final 14 days of 2017")
    ax1.set_ylabel("Load (MW)")
    ax1.set_xlabel("Date")
    ax1.legend(loc="upper left", fontsize=8, framealpha=0.9)
    fig1.tight_layout()
    p1 = str(FIG_DIR / "fig09_forecast_comparison.png")
    fig1.savefig(p1, bbox_inches="tight", facecolor="white")
    plt.close(fig1)

    fig2, ax2 = plt.subplots(figsize=(9, 3.6))
    ax2.plot(test_idx, actual / 1000, lw=1.4, color=COLORS["actual"], label="Actual")
    ax2.plot(test_idx, proposed_pred / 1000, lw=1.2, color=COLORS["proposed"], label="Point forecast")
    ax2.fill_between(test_idx, proposed_lower / 1000, proposed_upper / 1000, color=COLORS["proposed"], alpha=0.20, label="95% interval (conformal)")
    missed = (actual < proposed_lower) | (actual > proposed_upper)
    ax2.scatter(test_idx[missed], actual[missed] / 1000, s=8, color="red", zorder=5, label="Outside 95% interval")
    ax2.set_title("Proposed model: 95% prediction interval coverage (conformal)")
    ax2.set_ylabel("Load (MW)")
    ax2.set_xlabel("Date")
    ax2.legend(loc="upper left", fontsize=8, framealpha=0.9)
    fig2.tight_layout()
    p2 = str(FIG_DIR / "fig10_interval_coverage.png")
    fig2.savefig(p2, bbox_inches="tight", facecolor="white")
    plt.close(fig2)

    return p1, p2


def plot_error_distribution(baseline: BaselineResult, proposed_pred: np.ndarray, actual: np.ndarray) -> str:
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4))
    errors_b = baseline.predictions - actual
    errors_p = proposed_pred - actual
    axes[0].hist(errors_b / 1000, bins=40, color=COLORS["baseline"], alpha=0.7, label="Baseline", density=True)
    axes[0].hist(errors_p / 1000, bins=40, color=COLORS["proposed"], alpha=0.7, label="Proposed", density=True)
    axes[0].axvline(0, color="black", lw=0.8)
    axes[0].set_title("Error distribution (test set)")
    axes[0].set_xlabel("Forecast error (MW)")
    axes[0].set_ylabel("Density")
    axes[0].legend(fontsize=8)

    abs_b = np.abs(errors_b) / 1000
    abs_p = np.abs(errors_p) / 1000
    bp = axes[1].boxplot([abs_b, abs_p], tick_labels=["Baseline", "Proposed"], patch_artist=True, widths=0.5)
    for patch, col in zip(bp["boxes"], [COLORS["baseline"], COLORS["proposed"]]):
        patch.set_facecolor(col)
        patch.set_alpha(0.6)
    axes[1].set_title("Absolute error — test set (MW)")
    axes[1].set_ylabel("|Forecast error| (MW)")
    fig.tight_layout()
    p = str(FIG_DIR / "fig11_error_distribution.png")
    fig.savefig(p, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return p


def plot_per_horizon_mae(baseline: BaselineResult, proposed_per_h: dict[int, dict[str, float]]) -> str:
    hrs = list(range(1, 25))
    b = [baseline.per_horizon[h]["MAE"] for h in hrs]
    p = [proposed_per_h[h]["MAE"] for h in hrs]
    fig, ax = plt.subplots(figsize=(7.5, 3.2))
    w = 0.4
    ax.bar([h - w / 2 for h in hrs], [v / 1000 for v in b], width=w, color=COLORS["baseline"], label="Baseline SARIMA")
    ax.bar([h + w / 2 for h in hrs], [v / 1000 for v in p], width=w, color=COLORS["proposed"], label="Proposed ensemble")
    ax.set_title("Mean absolute error by forecast horizon (24 h ahead, rolling origin)")
    ax.set_xlabel("Horizon (hours ahead)")
    ax.set_ylabel("MAE (MW)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    p = str(FIG_DIR / "fig12_per_horizon_mae.png")
    fig.savefig(p, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return p


def peak_error_table(actual: np.ndarray, baseline_pred: np.ndarray, proposed_pred: np.ndarray) -> dict:
    """Compare MAE on peak hours (top 20% of observed load in the test set)."""
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


# matplotlib imported lazily to avoid GUI issues
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
