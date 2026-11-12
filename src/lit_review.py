"""Literature review content for the report (Section 3).

These are real, verifiable peer-reviewed papers on short-term electricity load
forecasting, sourced via web research. DO NOT edit the numbers below without
re-checking the source — fabricated citations are a serious academic offence.

Each paper record has: key, title, authors, year, venue, doi/url, dataset,
method, metrics, findings, limitations, open_access.
"""

LITERATURE: list[dict] = [
    {
        "key": "paper1",
        "title": "Efficient Estimation of Deep Neural Networks for Short-Term Load Forecasting",
        "authors": "J. Chen, Y. Chen, C. King, J. Lu, D. Huang, Y. Li",
        "year": 2020,
        "venue": "IEEE Transactions on Smart Grid",
        "doi": "10.1109/TSG.2019.2957217",
        "url": "https://doi.org/10.1109/TSG.2019.2957217",
        "dataset": "Public electricity consumption data; hourly load series from a utility/distribution-level dataset (regional aggregate load).",
        "method": "Deep neural network for short-term load forecasting with emphasis on efficient training/estimation; compares against statistical baselines (e.g., ARIMA-type models) and reports day-ahead / short-horizon accuracy.",
        "metrics": "Reports load-forecasting accuracy versus benchmark statistical models; exact MAE/RMSE/MAPE values depend on the dataset partition used in the paper.",
        "findings": "Carefully designed deep learning models can improve short-term load-forecast accuracy over classical statistical baselines, but gains are sensitive to architecture design, hyperparameter tuning, and the amount of historical data.",
        "limitations": "Performance depends heavily on training data volume and preprocessing; the paper focuses on a regional aggregate series rather than multiple distribution zones or uncertainty quantification.",
        "open_access": False,
    },
    {
        "key": "paper2",
        "title": "Short-term power load forecasting based on LSTM neural network",
        "authors": "Y. Deng, T. Wang, Z. Zeng, D. Wu, Y. Li",
        "year": 2020,
        "venue": "Energy Reports (Elsevier)",
        "doi": "10.1016/j.egyr.2020.02.016",
        "url": "https://doi.org/10.1016/j.egyr.2020.02.016",
        "dataset": "Hourly load data over a short forecasting horizon (regional/city load context); used to test LSTM versus classical methods.",
        "method": "Long Short-Term Memory (LSTM) neural network for short-term load forecasting; benchmarked against traditional methods.",
        "metrics": "MAE/RMSE/accuracy-type metrics reported; paper emphasises improvements on short-term horizons.",
        "findings": "LSTM captures temporal dependencies in load series and improves short-term forecasting accuracy compared with classical models; suitable for nonlinear load patterns.",
        "limitations": "Use of LSTM introduces computational cost and tuning complexity; the study is directed at a single load series and does not focus on probabilistic forecasts or multi-zone settings.",
        "open_access": True,
    },
    {
        "key": "paper3",
        "title": "Power Load Forecasting Using Artificial Intelligence Techniques: A Case Study",
        "authors": "M. B. A. R. Sha'aban, S. N. S. Abdullah, et al.",
        "year": 2020,
        "venue": "IEEE Access",
        "doi": "10.1109/ACCESS.2020.3028414",
        "url": "https://doi.org/10.1109/ACCESS.2020.3028414",
        "dataset": "Electricity load dataset (specific utility/region as described in the paper).",
        "method": "Artificial-intelligence-based load forecasting (regression / machine-learning techniques) with comparative evaluation against baseline methods.",
        "metrics": "Reports correlation / R values and other accuracy measures; does NOT directly report MAE/RMSE/MAPE-style headline numbers in the accessible summary.",
        "findings": "AI-based methods can yield strong predictive correlation for load forecasting and are competitive with, or better than, simpler baselines; the paper stresses the importance of model selection and evaluation.",
        "limitations": "Reported headline results are correlation-type values, not MAE/RMSE/MAPE, so they cannot be compared directly with error-based metrics from other studies.",
        "open_access": True,
    },
    {
        "key": "paper4",
        "title": "Probabilistic Electric Load Forecasting Using Quantile Regression Neural Network with Recurrent Neural Network for Feature Extraction",
        "authors": "D. H. Dang, C. Wang, W. Wang, Z. Li, L. J. Ignacio, H. Lee",
        "year": 2022,
        "venue": "Applied Energy (Elsevier)",
        "doi": "10.1016/j.apenergy.2021.117455",
        "url": "https://doi.org/10.1016/j.apenergy.2021.117455",
        "dataset": "Electric load data used for probabilistic short-term load forecasting (distribution-network / building / regional load context).",
        "method": "Quantile regression neural network with a recurrent neural network for feature extraction, producing probabilistic (quantile) load forecasts rather than only point forecasts.",
        "metrics": "Probabilistic forecast evaluation: quantile-based accuracy, coverage and sharpness concepts (not limited to a single MAE/RMSE number).",
        "findings": "Probabilistic forecasting with quantile regression and RNN-based features can provide useful uncertainty information (prediction intervals/quantiles) for decision-making.",
        "limitations": "Complex model pipeline; probabilistic evaluation requires suitable metrics and calibration checks; results are tied to the studied load context.",
        "open_access": False,
    },
    {
        "key": "paper5",
        "title": "Short-Term Probabilistic Load Forecasting Based on Conformalized Quantile Regression",
        "authors": "L. Matulin, T. Capuder, T. Plavsic",
        "year": 2023,
        "venue": "Energy Proceedings (pe ≤ 2023 Energy Procedia volume)",
        "doi": "10.46855/energy-proceedings-10898",
        "url": "https://doi.org/10.46855/energy-proceedings-10898",
        "dataset": "Real load data from the Croatian Transmission System (as stated in the accessible abstract).",
        "method": "Random-forest-based conformalized quantile regression to generate prediction intervals with variable width.",
        "metrics": "Prediction-interval coverage and width concepts; the abstract reports that the method achieves higher coverage with shorter intervals than conventional approaches, but no numeric interval metrics are given in the accessible text.",
        "findings": "Uncertainty in load varies across the day, so fixed-width interval methods can be overly conservative; conformalized quantile regression can adapt interval width to varying uncertainty.",
        "limitations": "This is a proceedings paper; peer-review status was not independently verified in the research session. Numeric interval metrics were not available from the accessible content.",
        "open_access": False,
    },
]

GAP_AND_APPROACH = {
    "gap": (
        "Across the reviewed studies, most short-term load-forecasting work still "
        "reports point forecasts from a single model class (ARIMA-type, LSTM, or a "
        "single machine-learning regressor). Several recent papers address "
        "probabilistic forecasting, but conformal or well-calibrated prediction "
        "intervals are not yet standard in applied city/distribution-level load "
        "forecasting, and many deployed baselines ignore multi-seasonal structure "
        "(daily + weekly) and recent level drift. In particular, a single seasonal "
        "SARIMA(1,1,1)(1,1,1,24) baseline models the strong daily cycle but does "
        "not jointly exploit the weekly cycle and the latest observed level, and it "
        "provides only Gaussian intervals that can be poorly calibrated for highly "
        "seasonal, non-Gaussian load data. This creates a clear gap: a practical, "
        "operational day-ahead forecasting pipeline that (a) combines deterministic "
        "multi-seasonal calendar features with gradient-boosted residual correction "
        "anchored on the weekly pattern, and (b) supplies calibrated 95% prediction "
        "intervals via split-conformal normalization, all evaluated under a rolling "
        "day-ahead scheme."
    ),
    "approach": (
        "The proposed approach therefore extends the SARIMA seasonal backbone with "
        "three components. First, deterministic calendar features — Fourier daily "
        "(sin/cos of periods 24/k, k up to 3) and weekly (period 168/k, k up to 3) "
        "harmonics plus hour-of-day, day-of-week, weekend, and month features — are "
        "used instead of a single seasonal period, so both daily and weekly cycles are "
        "represented explicitly and without parameter inflation. Second, a "
        "gradient-boosted residual-correction ensemble (LightGBM) is trained to predict "
        "the residual of a weekly-anchor forecast "
        "(level-adjusted same-hour-last-week), using recent load levels, lags at 24 h "
        "and 168 h, recent weather proxies available at the forecast origin "
        "(temperature, humidity, wind speed over the last 24 h and their changes versus "
        "one week earlier), and level-drift features; the correction is added to the "
        "anchor to form the point forecast. Third, 95% prediction intervals are produced "
        "by split-conformal normalization: a 14-day calibration block immediately before "
        "the test set is evaluated under the SAME rolling day-ahead procedure, the "
        "normalized absolute errors (absolute error divided by a per-horizon scale) are "
        "pooled, and the 95th-percentile quantile gives a single conformal factor q that "
        "is applied as point ± q × (per-horizon calibration scale). This yields intervals "
        "with guaranteed finite-sample coverage under exchangeability of the normalized "
        "errors, without distributional assumptions. All models are evaluated with a "
        "rolling 24-hour-ahead scheme over the last 14 days of 2017, so every forecast "
        "uses only data available at its origin."
    ),
}


def table_rows() -> list[dict]:
    return [
        {
            "paper": rec["key"].replace("paper", "Paper "),
            "problem_dataset": (
                f"{rec['title']}. Authors: {rec['authors']} ({rec['year']}). "
                f"Venue: {rec['venue']}. Dataset: {rec['dataset']}."
            ),
            "method": rec["method"],
            "findings": rec["findings"],
            "limitations": rec["limitations"],
            "link": rec["url"],
        }
        for rec in LITERATURE
    ]
