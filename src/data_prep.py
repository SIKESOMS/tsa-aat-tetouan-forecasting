"""Dataset acquisition, validation and preparation.

Dataset: Power Consumption of Tetouan City (UCI id 849)
Salam, A. & El Hibaoui, A. (2018). DOI 10.24432/C5B034
"""
from __future__ import annotations

import re
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from .config import RAW_DIR

UCI_ZIP_URL = "https://archive.ics.uci.edu/static/public/849/power+consumption+of+tetouan+city.zip"
RAW_CSV = RAW_DIR / "Tetuan City power consumption.csv"

RENAME = {
    "DateTime": "datetime",
    "Temperature": "temperature",
    "Humidity": "humidity",
    "Wind Speed": "wind_speed",
    "general diffuse flows": "diffuse_flows_general",
    "diffuse flows": "diffuse_flows",
    "Zone 1 Power Consumption": "zone1_kw",
    "Zone 2 Power Consumption": "zone2_kw",
    "Zone 3 Power Consumption": "zone3_kw",
}


def ensure_raw() -> Path:
    """Download and extract the UCI archive if the CSV is not already present."""
    if RAW_CSV.exists():
        return RAW_CSV
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    tmp_zip = RAW_DIR / "power_consumption_tetouan.zip"
    if not tmp_zip.exists():
        urllib.request.urlretrieve(UCI_ZIP_URL, tmp_zip)
    with zipfile.ZipFile(tmp_zip) as zf:
        zf.extractall(RAW_DIR)
    if not RAW_CSV.exists():  # defensive: locate whatever CSV came out
        csvs = list(RAW_DIR.glob("*.csv"))
        if not csvs:
            raise FileNotFoundError("No CSV found in the downloaded archive")
        csvs[0].rename(RAW_CSV)
        # keep the sibling documentation file if the archive shipped one
    return RAW_CSV


def load_10min() -> pd.DataFrame:
    """Load the raw 10-minute series with clean, consistent column names."""
    path = ensure_raw()
    df = pd.read_csv(path)
    df.columns = [re.sub(r"\s+", " ", c).strip() for c in df.columns]
    df = df.rename(columns=RENAME)
    missing = set(RENAME.values()) - set(df.columns)
    if missing:
        raise ValueError(f"Unexpected columns, missing: {missing}")
    # UCI stores timestamps as MM/DD/YYYY HH:MM (e.g. "1/13/2017 0:00").
    df["datetime"] = pd.to_datetime(df["datetime"], format="%m/%d/%Y %H:%M")
    df = df.set_index("datetime").sort_index()
    df = df[~df.index.duplicated(keep="first")]
    return df


def to_hourly(df10: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Aggregate to hourly means and return a data-quality summary."""
    numeric = df10.select_dtypes(include=[np.number])
    df10 = df10.copy()
    df10["total_kw"] = df10[["zone1_kw", "zone2_kw", "zone3_kw"]].sum(axis=1)

    hourly = df10.drop(columns=["zone1_kw", "zone2_kw", "zone3_kw"]).resample("h").mean()
    hourly = hourly.astype(float)

    full_index = pd.date_range(hourly.index.min(), hourly.index.max(), freq="h")
    n_missing = int(len(full_index.difference(hourly.index)))
    hourly = hourly.reindex(full_index)
    hourly = hourly.interpolate(method="time", limit_direction="both")

    hourly.index.name = "datetime"
    hourly["hour"] = hourly.index.hour
    hourly["dow"] = hourly.index.dayofweek
    hourly["month"] = hourly.index.month
    hourly["is_weekend"] = (hourly["dow"] >= 5).astype(int)

    load = hourly["total_kw"]
    q1, q3 = load.quantile([0.25, 0.75])
    iqr = q3 - q1
    quality = {
        "raw_rows": int(len(df10)),
        "raw_start": str(df10.index.min()),
        "raw_end": str(df10.index.max()),
        "sampling_minutes": 10,
        "hourly_observations": int(len(hourly)),
        "hours_expected": int(len(full_index)),
        "missing_hours_interpolated": n_missing,
        "duplicate_timestamps_removed": int(df10.index.duplicated().sum()),
        "negative_load_values": int((df10[["zone1_kw", "zone2_kw", "zone3_kw"]] < 0).sum().sum()),
        "iqr_outliers_hourly": int(((load < q1 - 3 * iqr) | (load > q3 + 3 * iqr)).sum()),
        "target_mean_kw": float(load.mean()),
        "target_std_kw": float(load.std()),
        "target_min_kw": float(load.min()),
        "target_max_kw": float(load.max()),
        "target_cv": float(load.std() / load.mean()),
        "n_numeric_features": int(len(numeric.columns)),
    }
    return hourly, quality


def train_test_split_frame(hourly: pd.DataFrame, test_hours: int):
    """Chronological split: everything before the final `test_hours` is train."""
    train = hourly.iloc[:-test_hours]
    test = hourly.iloc[-test_hours:]
    return train, test
