"""Exploratory data analysis: statistics, stationarity/seasonality tests, figures."""
from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.stattools import adfuller

from .config import FIG_DIR, TARGET, TABLE_DIR

plt.rcParams.update(
    {
        "figure.dpi": 150,
        "savefig.dpi": 150,
        "font.size": 9,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.titlesize": 10,
        "axes.titleweight": "bold",
        "figure.autolayout": False,
    }
)
COLORS = {"actual": "#1f3b73", "baseline": "#d1495b", "proposed": "#00798c", "naive": "#8d99ae"}


def _save(fig, name: str) -> str:
    path = FIG_DIR / name
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(path.relative_to(FIG_DIR.parent.parent))


def plot_full_series(hourly: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(9, 3.4))
    ax.plot(hourly.index, hourly[TARGET] / 1000, lw=0.4, color=COLORS["actual"], alpha=0.45, label="Hourly load")
    ax.plot(
        hourly.index,
        hourly[TARGET].rolling(24 * 7).mean() / 1000,
        lw=1.8,
        color=COLORS["baseline"],
        label="7-day moving average",
    )
    ax.set_title("Figure 1: City-level electricity load, Tetouan (Jan-Dec 2017)")
    ax.set_ylabel("Load (MW)")
    ax.set_xlabel("Date")
    ax.legend(frameon=False, ncol=2, loc="upper right")
    return _save(fig, "fig01_full_series.png")


def plot_two_weeks(hourly: pd.DataFrame) -> str:
    win = hourly.loc["2017-03-06":"2017-03-19"]
    fig, ax = plt.subplots(figsize=(9, 3.2))
    ax.plot(win.index, win[TARGET] / 1000, color=COLORS["actual"], lw=1.4)
    ax.set_title("Figure 2: Two-week zoom showing the daily cycle and weekend effect")
    ax.set_ylabel("Load (MW)")
    for day in pd.date_range(win.index.min().normalize(), win.index.max().normalize(), freq="D"):
        if day.dayofweek >= 5:
            ax.axvspan(day, day + pd.Timedelta(days=1), color="#f2c14e", alpha=0.18, lw=0)
    ax.set_xlabel("Date (shaded = weekend)")
    return _save(fig, "fig02_two_weeks.png")


def plot_daily_profile(hourly: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    for label, mask, color in [
        ("Weekday (Mon-Fri)", hourly["is_weekend"] == 0, COLORS["actual"]),
        ("Weekend (Sat-Sun)", hourly["is_weekend"] == 1, COLORS["baseline"]),
    ]:
        sub = hourly[mask].groupby("hour")[TARGET]
        med = sub.mean() / 1000
        lo, hi = sub.quantile(0.1) / 1000, sub.quantile(0.9) / 1000
        ax.plot(med.index, med.values, marker="o", ms=3, lw=1.6, color=color, label=label)
        ax.fill_between(med.index, lo.values, hi.values, color=color, alpha=0.12, lw=0)
    ax.set_xticks(range(0, 24, 2))
    ax.set_title("Figure 3: Average hourly load profile by day type (shading = 10th-90th percentile)")
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Load (MW)")
    ax.legend(frameon=False)
    return _save(fig, "fig03_daily_profile.png")


def plot_monthly_box(hourly: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    data = [hourly.loc[hourly["month"] == m, TARGET].values / 1000 for m in range(1, 13)]
    bp = ax.boxplot(data, patch_artist=True, widths=0.65, medianprops={"color": "black"})
    for patch in bp["boxes"]:
        patch.set_facecolor("#9db4d0")
        patch.set_alpha(0.85)
    ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    ax.set_title("Figure 4: Monthly distribution of hourly load (annual / weather-driven pattern)")
    ax.set_ylabel("Load (MW)")
    return _save(fig, "fig04_monthly_box.png")


def plot_stl(hourly: pd.DataFrame) -> str:
    win = hourly[TARGET].loc["2017-03-06":"2017-04-30"]
    res = STL(win, period=24, robust=True).fit()
    fig, axes = plt.subplots(4, 1, figsize=(8.2, 5.6), sharex=True)
    parts = [
        (win / 1000, "Observed", COLORS["actual"]),
        (res.trend / 1000, "Trend", "#00798c"),
        (res.seasonal / 1000, "Daily seasonal component", "#d1495b"),
        (res.resid / 1000, "Remainder", "#8d99ae"),
    ]
    for ax, (series, label, color) in zip(axes, parts):
        ax.plot(series.index, series.values, lw=1.0, color=color)
        ax.set_ylabel(label, fontsize=8)
        ax.grid(alpha=0.25)
    axes[-1].set_xlabel("Date")
    fig.suptitle("Figure 5: STL decomposition of load (period = 24 h)", fontsize=10, fontweight="bold", y=0.995)
    fig.tight_layout()
    return _save(fig, "fig05_stl.png")


def plot_acf_pacf(hourly: pd.DataFrame) -> str:
    series = hourly[TARGET]
    fig, axes = plt.subplots(2, 1, figsize=(8.4, 5.0))
    plot_acf(series, lags=168, ax=axes[0], title="Autocorrelation (up to 168 lags = 7 days)")
    plot_pacf(series, lags=72, ax=axes[1], method="ywm", title="Partial autocorrelation (up to 72 lags)")
    for ax in axes:
        ax.grid(alpha=0.25)
    fig.suptitle("Figure 6: ACF and PACF of hourly load", fontsize=10, fontweight="bold", y=0.995)
    fig.tight_layout()
    return _save(fig, "fig06_acf_pacf.png")


def plot_correlation(hourly: pd.DataFrame) -> str:
    cols = ["total_kw", "temperature", "humidity", "wind_speed", "diffuse_flows_general", "diffuse_flows"]
    labels = ["Load", "Temp", "Humidity", "Wind", "Diffuse flow (gen)", "Diffuse flow"]
    corr = hourly[cols].corr()
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(cols)), labels, rotation=40, ha="right")
    ax.set_yticks(range(len(cols)), labels)
    for i in range(len(cols)):
        for j in range(len(cols)):
            ax.text(j, i, f"{corr.values[i, j]:.2f}", ha="center", va="center", fontsize=7.5,
                    color="white" if abs(corr.values[i, j]) > 0.5 else "black")
    ax.set_title("Figure 7: Correlation matrix (Pearson)")
    fig.colorbar(im, ax=ax, shrink=0.8)
    ax.grid(False)
    return _save(fig, "fig07_correlation.png")


def plot_zone_profiles(df10: pd.DataFrame) -> str:
    zones = {"Zone 1": "zone1_kw", "Zone 2": "zone2_kw", "Zone 3": "zone3_kw"}
    hourly = df10[list(zones.values())].resample("h").mean()
    hourly["hour"] = hourly.index.hour
    fig, ax = plt.subplots(figsize=(7.2, 3.3))
    for (label, col), color in zip(zones.items(), ["#1f3b73", "#d1495b", "#00798c"]):
        prof = hourly.groupby("hour")[col].mean() / 1000
        ax.plot(prof.index, prof.values, marker="o", ms=3, lw=1.6, color=color, label=label)
    ax.set_xticks(range(0, 24, 2))
    ax.set_title("Figure 8: Average daily load profile of the three distribution zones")
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Load (MW)")
    ax.legend(frameon=False, ncol=3)
    return _save(fig, "fig08_zone_profiles.png")


def stationarity_report(series: pd.Series) -> dict:
    """ADF test on the level, daily-differenced and seasonally-differenced series."""
    out = {}
    for name, s in [
        ("level", series),
        ("diff_1", series.diff().dropna()),
        ("diff_24", series.diff(24).dropna()),
        ("diff_1_24", series.diff().diff(24).dropna()),
    ]:
        stat, p, used, nobs, crit, _ = adfuller(s, autolag="AIC")
        out[name] = {"adf_stat": round(float(stat), 3), "p_value": round(float(p), 4),
                     "n_lags": int(used), "n_obs": int(nobs), "critical_5pct": round(float(crit["5%"]), 3)}
    return out


def seasonal_strength(series: pd.Series, period: int = 24) -> float:
    """Wang/Hyndman strength of seasonality: 1 - Var(remainder)/Var(remainder+seasonal)."""
    res = STL(series, period=period, robust=True).fit()
    var_r = float(np.var(res.resid))
    var_sr = float(np.var(res.resid + res.seasonal))
    return float(max(0.0, 1 - var_r / var_sr))


def make_eda(hourly: pd.DataFrame, df10: pd.DataFrame) -> dict:
    load = hourly[TARGET]
    hourly_profile = load.groupby(hourly["hour"]).mean()
    by_daytype = hourly.groupby(["is_weekend", "hour"])[TARGET].mean()
    weekday_peak = float(by_daytype.loc[0].idxmax())
    weekend_peak = float(by_daytype.loc[1].idxmax())

    stats = {
        "rows_hourly": int(len(hourly)),
        "mean_kw": float(load.mean()),
        "std_kw": float(load.std()),
        "cv": float(load.std() / load.mean()),
        "min_kw": float(load.min()),
        "min_time": str(load.idxmin()),
        "max_kw": float(load.max()),
        "max_time": str(load.idxmax()),
        "mean_daily_range_kw": float(load.groupby(load.index.date).agg(lambda s: s.max() - s.min()).mean()),
        "peak_hour_weekday": weekday_peak,
        "peak_hour_weekend": weekend_peak,
        "trough_hour": int(hourly_profile.idxmin()),
        "weekday_mean_kw": float(hourly.loc[hourly["is_weekend"] == 0, TARGET].mean()),
        "weekend_mean_kw": float(hourly.loc[hourly["is_weekend"] == 1, TARGET].mean()),
        "weekend_drop_pct": float(
            100 * (1 - hourly.loc[hourly["is_weekend"] == 1, TARGET].mean()
                   / hourly.loc[hourly["is_weekend"] == 0, TARGET].mean())
        ),
        "daily_seasonal_strength": seasonal_strength(load, 24),
        "weekly_seasonal_strength": seasonal_strength(load, 168),
        "acf_lag24": float(load.autocorr(24)),
        "acf_lag168": float(load.autocorr(168)),
        "corr_temp_load": float(hourly["temperature"].corr(load)),
        "corr_humidity_load": float(hourly["humidity"].corr(load)),
        "corr_wind_load": float(hourly["wind_speed"].corr(load)),
        "corr_flow_load": float(hourly["diffuse_flows_general"].corr(load)),
        "monthly_mean_kw": {int(m): float(v) for m, v in (load.groupby(hourly["month"]).mean()).items()},
        "stationarity": stationarity_report(load),
        "hourly_mean_profile_kw": {int(h): float(v) for h, v in hourly_profile.items()},
        "figures": {},
    }

    stats["figures"]["full_series"] = plot_full_series(hourly)
    stats["figures"]["two_weeks"] = plot_two_weeks(hourly)
    stats["figures"]["daily_profile"] = plot_daily_profile(hourly)
    stats["figures"]["monthly_box"] = plot_monthly_box(hourly)
    stats["figures"]["stl"] = plot_stl(hourly)
    stats["figures"]["acf_pacf"] = plot_acf_pacf(hourly)
    stats["figures"]["correlation"] = plot_correlation(hourly)
    stats["figures"]["zone_profiles"] = plot_zone_profiles(df10)

    (TABLE_DIR / "eda_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    return stats
