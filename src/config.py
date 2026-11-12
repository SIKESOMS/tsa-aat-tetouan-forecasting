"""Project configuration: paths, constants and experiment settings."""
from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
OUT_DIR = PROJECT_ROOT / "outputs"
FIG_DIR = OUT_DIR / "figures"
TABLE_DIR = OUT_DIR / "tables"

for _d in (RAW_DIR, FIG_DIR, TABLE_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ---- Target series -------------------------------------------------------
# City-level aggregate load (kW), summed over the three distribution zones.
TARGET = "total_kw"
FREQ = "h"

# ---- Experiment settings -------------------------------------------------
# The last 14 days (336 hourly observations) form the out-of-sample test set.
TEST_HOURS = 336
# The 14 days immediately before the test set are used for split-conformal
# calibration of the prediction intervals (a horizon-matched held-out block).
CAL_HOURS = 336

# Baseline SARIMA order, justified in Section 5.1 of the report.
# (1,1,1)(1,1,1,24) is used: it captures the daily seasonal cycle with one AR and one
# seasonal MA term at period 24, with first-order non-seasonal and seasonal differencing
# to remove trend and daily seasonality. This order is selected as a parsimonious,
# stable choice that fits reliably; the extra AR(2) term gives a negligible
# AIC improvement but a markedly slower and less stable fit on this data.
BASELINE_ORDER = (1, 1, 1)
BASELINE_SEASONAL = (1, 1, 1, 24)

# Number of Fourier harmonics used by the proposed SARIMAX component.
K_DAILY = 3
K_WEEKLY = 3

# Conformal / interval settings
INTERVAL_ALPHA = 0.05  # 95% prediction intervals

RANDOM_STATE = 42
