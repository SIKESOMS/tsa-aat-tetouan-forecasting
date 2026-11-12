"""Long-form text content for the report sections that are prose, not numbers.

Kept separate from the docx builder so the builder can stay about layout while this
module holds the narrative. Student-specific fields (name/USN etc.) are left as
PLACEHOLDER markers — the student fills them in the final docx.
"""

from .lit_review import GAP_AND_APPROACH

ABSTRACT = (
    "This report investigates short-term (day-ahead, 24-hour) electricity load "
    "forecasting for a smart-city distribution network using the Power Consumption of "
    "Tetouan City dataset (UCI Machine Learning Repository, dataset ID 849), which "
    "records three-phase power consumption together with weather variables at 10-minute "
    "resolution over the full year 2017. After aggregating the three distribution zones "
    "into a city-level load series at hourly resolution, exploratory analysis confirms "
    "very strong daily and weekly seasonality (seasonal-strength indices of 0.978 and "
    "0.973 respectively) and a stable weekly level, with load peaking near 8 pm on both "
    "weekdays and weekends. A literature review of five recent peer-reviewed papers on "
    "short-term load forecasting identified a clear research gap: most studies still "
    "report point forecasts from a single model class and provide either no uncertainty "
    "quantification or only simple Gaussian intervals, while operational baselines often "
    "ignore the weekly cycle and recent level drift. As a baseline, a seasonal SARIMA "
    "(1,1,1)(1,1,1,24) model was fitted on a 120-day operational window and evaluated "
    "with a rolling day-ahead scheme. The proposed model extends this with deterministic "
    "Fourier daily and weekly calendar features, a gradient-boosted residual-correction "
    "ensemble (LightGBM) trained on the weekly-anchor residual using recent load levels "
    "and weather proxies available at the forecast origin, and calibrated 95% prediction "
    "intervals obtained by split-conformal normalization on a 14-day calibration block. "
    "Evaluated over the final 14 days of 2017 using MAE, RMSE, MAPE, sMAPE and MASE, the "
    "proposed ensemble reduced forecast error relative to the baseline SARIMA and produced "
    "well-calibrated prediction intervals (coverage close to the nominal 95%) with "
    "reasonable width. The results show that explicitly modelling multi-seasonal structure, "
    "recent level drift and weather, together with conformal uncertainty, is a practical "
    "improvement over a classical seasonal ARIMA baseline and is directly relevant to "
    "day-ahead dispatch, demand-side management and grid planning in smart cities. The work "
    "addresses SDG 7 (Affordable and Clean Energy) by supporting more reliable and efficient "
    "electricity forecasting. Limitations include the single-city dataset, the fixed 24-hour "
    "horizon, and the absence of true weather forecasts; future work should test other "
    "cities, longer horizons, and genuine forecast weather inputs."
)

INTRODUCTION = {
    "2.1": (
        "Application Domain — Smart City / Energy.\n\n"
        "Forecasting electricity demand at the city or distribution-network level is a core "
        "smart-city problem. Modern urban grids must balance generation and demand in real time, "
        "integrate renewable and distributed resources, manage demand-response programs, and "
        "plan infrastructure investments. All of these depend on reliable short-term load "
        "forecasts, especially for the next 24 hours, which guide unit commitment, reserve "
        "allocation, peak shaving, and tariff design. Smart-city initiatives therefore treat "
        "load forecasting as a foundational analytics capability, combining smart-meter and "
        "substation data with weather and calendar information to anticipate demand."
    ),
    "2.2": (
        "Problem Statement.\n\n"
        "Accurately forecasting the next 24 hours of electricity demand for a city-level "
        "distribution network is difficult because load exhibits strong but season-dependent "
        "daily and weekly patterns, is sensitive to weather and calendar effects, and can shift "
        "its level from week to week. A model that captures only one seasonal period or ignores "
        "recent level drift will misforecast; a model that also quantifies uncertainty is needed "
        "for robust operational decisions. The forecasting problem studied here is therefore: "
        "given historical city-level load and weather observations up to a forecast origin, "
        "predict the 24 hourly load values of the following day, and attach calibrated "
        "prediction intervals."
    ),
    "2.3": (
        "Need for Forecasting.\n\n"
        "Day-ahead load forecasts are used directly in electricity markets and grid operations: "
        "they determine day-ahead generation scheduling and bidding, reserve procurement, "
        "peaking-unit commitment, demand-response activation, and network congestion management. "
        "Under-forecasting can cause shortages and expensive real-time balancing; over-forecasting "
        "can lead to inefficient unit commitment and excess reserve. In a smart-city context, "
        "accurate short-term forecasts also enable better integration of rooftop solar and "
        "electric-vehicle charging, more effective demand-side management, and more reliable "
        "service at lower cost. Reliable forecasting therefore has direct operational, economic "
        "and reliability value."
    ),
    "2.4": (
        "Objectives.\n\n"
        "The objectives of this project are to: (1) select a smart-city application domain and a "
        "suitable real-world time-series dataset for electricity load forecasting; (2) carry out a "
        "literature review of at least five relevant research papers and identify a specific "
        "research gap; (3) prepare and explore the dataset through preprocessing and exploratory "
        "data analysis; (4) develop a baseline seasonal time-series model (SARIMA) appropriate to "
        "the data; (5) improve the model by addressing the identified gap with a multi-seasonal "
        "calendar + gradient-boosted residual-correction ensemble and conformal prediction "
        "intervals; (6) compare the baseline and proposed models using appropriate evaluation "
        "measures on a held-out test period; and (7) interpret and present the methodology, results "
        "and conclusions in a structured report."
    ),
    "2.5": (
        "Scope of the Study.\n\n"
        "The study forecasts the aggregated city-level electricity load (sum of the three "
        "distribution zones) of Tetouan City at hourly resolution, with a fixed 24-hour-ahead "
        "horizon evaluated over the last 14 days of the 2017 series. The forecasting models use "
        "only information available at each forecast origin (no look-ahead), and the proposed "
        "model additionally uses weather proxies computed from recent observations. The study is "
        "limited to a single city and a single year of data, uses a day-ahead horizon rather than "
        "multi-day or multi-week horizons, and uses recent-observation weather proxies rather than "
        "external weather forecasts. These choices keep the experiment operationally realistic and "
        " reproducible while leaving multi-horizon, multi-city and true-weather-forecast extensions "
        "for future work."
    ),
}

LITERATURE_INTRO = (
    "The following five peer-reviewed studies were reviewed to understand the state of the art in "
    "short-term electricity load forecasting and to identify a research gap. They span classical "
    "and modern statistical methods, deep learning (LSTM), machine-learning regressors, and "
    "probabilistic / conformal approaches, and collectively show both the progress and the "
    "remaining limitations in the field."
)

LITERATURE_GAP = (
    "3.2 Research Gap\n\n"
    + GAP_AND_APPROACH["gap"]
)

PROPOSED_APPROACH_BRIEF = (
    "3.3 Proposed Approach\n\n"
    + GAP_AND_APPROACH["approach"]
)

DATASET = {
    "4.1": (
        "Dataset Source.\n\n"
        "The dataset used is the Power Consumption of Tetouan City dataset from the UCI Machine "
        "Learning Repository (dataset ID 849). It records the electricity power consumption of three "
        "different distribution networks of Tetouan city, located in northern Morocco, together with "
        "local weather measurements. The dataset was published by A. Salam and A. El Hibaoui "
        "(2018) and is cited as: Salam, A. & El Hibaoui, A. (2018). Power Consumption of Tetouan "
        "City [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5B034."
    ),
    "4.2": (
        "Variables and Data Description.\n\n"
        "The dataset is multivariate and time-series in nature, with 52,417 instances sampled every "
        "10 minutes. Each record contains the timestamp (DateTime) and the following variables: "
        "Temperature, Humidity, Wind Speed, general diffuse flows, diffuse flows, and the power "
        "consumption of three distribution zones (Zone 1, Zone 2, Zone 3). The three zone series are "
        "aggregated into a single city-level total load (the sum of the three zones) measured in "
        "kilowatts (kW). The weather variables are used as explanatory features for the proposed model. "
        "A summary of the prepared hourly dataset is given in Table 1."
    ),
    "4.3": (
        "Data Preparation.\n\n"
        "The raw 10-minute series was processed as follows: (1) column names were cleaned and "
        "standardised (the source file contains double spaces in some headers); (2) timestamps were "
        "parsed from the MM/DD/YYYY HH:MM format; (3) the three zone consumption series were summed to "
        "form the city-level total load; (4) the data were resampled to hourly means; (5) the resulting "
        "hourly index was reindexed to a complete hourly timeline and any missing hours were interpolated "
        "by time; (6) duplicate timestamps were removed; (7) calendar features were derived (hour of day, "
        "day of week, month, weekend flag); and (8) the series was split chronologically, with the final "
        "14 days (336 hours) held out as the test set and the preceding 14 days as the calibration block "
        "for conformal intervals. No negative load values were present, and no major outlier removal was "
        "required after inspection."
    ),
    "4.4": (
        "Exploratory Data Analysis.\n\n"
        "The prepared hourly series contains 8,736 observations covering 1 January to 30 December 2017, "
        "with a mean load of about 71,223 kW, a standard deviation of about 17,018 kW, and a "
        "coefficient of variation of about 0.24. The minimum load (about 37,408 kW) occurs in early "
        "December, while the maximum load (about 133,130 kW) occurs on a July evening, reflecting strong "
        "seasonal variation and air-conditioning-driven summer peaks.\n\n"
        "Key patterns identified:\n"
        "• Very strong daily seasonality: the autocorrelation at lag 24 is about 0.98, and the daily "
        "seasonal-strength index is about 0.978. Load follows a clear daily cycle with a trough around "
        "6–7 am and a peak near 8 pm.\n"
        "• Strong weekly seasonality: the autocorrelation at lag 168 (one week) is about 0.97, and the "
        "weekly seasonal-strength index is about 0.973. The same day of the week has very similar load "
        "from week to week.\n"
        "• Weekend effect: weekend mean load is about 3.8% lower than weekday mean load.\n"
        "• Monthly variation: summer months (June–August) show the highest mean loads (peaking near "
        "88,000 kW in July), while winter months are lower.\n"
        "• Weather relationships: load is positively correlated with temperature (about +0.49) and wind "
        "speed (about +0.22) and negatively correlated with humidity (about -0.30), consistent with "
        "air-conditioning and heating effects.\n\n"
        "These patterns directly inform model choice: the strong, stable daily and weekly cycles motivate "
        "modelling both seasonal periods explicitly; the weather correlations motivate including weather "
        "features; and the weekly level stability motivates anchoring on the same hour one week earlier. "
        "The figures below (full-year series, two-week zoom, hourly profile, monthly boxplot, STL "
        "decomposition, ACF/PACF, correlation heatmap, and zone profiles) illustrate these patterns."
    ),
}

BASELINE = {
    "5.1": (
        "Model Selection.\n\n"
        "The baseline model selected is a seasonal ARIMA (SARIMA) model, implemented as SARIMAX "
        "(1,1,1)(1,1,1,24) with a constant trend term. SARIMA is a natural baseline for this problem "
        "because the load series exhibits clear, strong daily seasonality (period 24) and is a classic, "
        "well-understood model for seasonal time series. It is widely used and cited as a benchmark in "
        "short-term load forecasting literature, is available in standard statistical libraries, and "
        "provides analytic prediction intervals that can be compared with the proposed conformal intervals."
    ),
    "5.2": (
        "Model Methodology.\n\n"
        "A SARIMA(p,d,q)(P,D,Q,s) model combines non-seasonal autoregressive (AR), integrated (I) and "
        "moving-average (MA) components with seasonal counterparts at seasonal period s. The model for the "
        "load series y_t is written using the backshift operator B as:\n\n"
        "φ_p(B) Φ_P(B^s) (1 - B)^d (1 - B^s)^D y_t = c + θ_q(B) Θ_Q(B^s) ε_t,\n\n"
        "where φ_p and Φ_P are the non-seasonal and seasonal AR polynomials, θ_q and Θ_Q are the "
        "non-seasonal and seasonal MA polynomials, d and D are the non-seasonal and seasonal degrees of "
        "differencing, s = 24 is the daily seasonal period, c is a constant, and ε_t is white noise. For "
        "the chosen baseline, (p,d,q) = (1,1,1) and (P,D,Q,s) = (1,1,1,24). The non-seasonal differencing "
        "(d=1) addresses the stochastic trend suggested by the near-unit-root behaviour in the raw series "
        "(ADF p-value ≈ 0.099 at level, rejecting stationarity), while the seasonal differencing "
        "(D=1, s=24) removes the deterministic-like daily seasonality before estimation. The AR and MA terms "
        "capture residual autocorrelation after differencing. Parameters are estimated by maximum likelihood, "
        "and analytic forecast variances yield Gaussian 95% prediction intervals."
    ),
    "5.3": (
        "Implementation.\n\n"
        "Implementation was carried out in Python using pandas for data handling and statsmodels for the "
        "SARIMA estimation. The model was fitted on a 120-day operational window at the start of the test "
        "period and then evaluated with a rolling day-ahead scheme: on each of the 14 test days the model "
        "produced a 24-hour-ahead forecast from the current origin, after which the true 24 hours were "
        "filtered into the state (via results.append) without re-estimation, so the next day's forecast used "
        "updated information. This mimics real operational use and produces 14 × 24 = 336 out-of-sample "
        "forecasts. The core fitting call used is:\n\n"
        "from statsmodels.tsa.statespace.sarimax import SARIMAX\n"
        "model = SARIMAX(train_series, order=(1,1,1), seasonal_order=(1,1,1,24),\n"
        "                trend='c', enforce_stationarity=False, enforce_invertibility=False)\n"
        "results = model.fit(disp=False, maxiter=60)\n\n"
        "The complete code is included in the project repository under src/models.py and src/run_pipeline.py."
    ),
    "5.4": (
        "Baseline Results.\n\n"
        "The baseline SARIMA was evaluated on the held-out final 14 days of 2017 using MAE, RMSE, MAPE, "
        "sMAPE and MASE. The forecast overlay and the baseline performance are shown in the figures and "
        "tables below. The Gaussian 95% intervals from the baseline are also reported for comparison with "
        "the proposed conformal intervals. Full per-horizon and test-set results are given in Section 7."
    ),
}

PROPOSED = {
    "6.1": (
        "Motivation for Improvement.\n\n"
        "The baseline SARIMA captures the dominant daily cycle but has two important limitations relative "
        "to the identified gap. First, it models only one seasonal period (s=24) and does not explicitly "
        "represent the strong weekly cycle or the most recent level, even though the weekly cycle is nearly "
        "as strong as the daily cycle (weekly seasonal strength ≈ 0.973, lag-168 autocorrelation ≈ 0.97) and "
        "the load level can drift week to week. Second, its Gaussian prediction intervals rely on a Gaussian "
        "innovation assumption and analytic variance propagation that can be poorly calibrated for a highly "
        "seasonal, non-Gaussian, non-constant-variance load series. These limitations are precisely the gap "
        "identified in the literature review: the need to jointly model multi-seasonal structure and recent "
        "level drift, and to provide well-calibrated, data-driven prediction intervals. The proposed model "
        "addresses both."
    ),
    "6.2": (
        "Proposed Enhancement.\n\n"
        "The proposed model is a multi-seasonal calibration + gradient-boosted residual-correction ensemble "
        "with conformal prediction intervals. It has three components:\n\n"
        "1. Multi-seasonal calendar features instead of a single seasonal period. Deterministic Fourier "
        "harmonics for the daily cycle (sin/cos of periods 24/k, k = 1,2,3) and weekly cycle (periods "
        "168/k, k = 1,2,3) are included, together with hour of day, day of week, weekend flag, and month. "
        "This explicitly represents both daily and weekly seasonality without inflating the number of ARIMA "
        "parameters and without the estimation cost of a seasonal period of 168.\n\n"
        "2. A gradient-boosted residual-correction ensemble (LightGBM). Rather than predicting the raw load, "
        "the model predicts the residual of a level-adjusted weekly anchor (the same hour one week earlier, "
        "scaled by the recent level ratio). The correction uses recent load levels and lags (at 24 h and 168 "
        "h), recent weather proxies available at the forecast origin (mean temperature, humidity and wind "
        "speed over the last 24 h, and their change versus one week earlier), level-drift features, and the "
        "calendar features. One direct model is trained per forecast horizon (h = 1..24) so each horizon can "
        "specialise, and a pooled model is also fitted for interpretation. The final point forecast is the "
        "weekly anchor plus the learned correction. This directly addresses the gap by exploiting the weekly "
        "cycle and recent level drift in a data-driven way.\n\n"
        "3. Calibrated 95% prediction intervals via split-conformal normalization. A 14-day calibration block "
        "immediately before the test set is evaluated under the same rolling day-ahead procedure. For each "
        "calibration forecast, the absolute error is divided by a per-horizon scale (the standard deviation "
        "of calibration residuals at that horizon), the normalized errors are pooled across horizons, and the "
        "95th percentile gives a single conformal factor q. The prediction interval for a future point forecast "
        "is then point ± q × (per-horizon scale). This provides distribution-free, finite-sample-calibrated "
        "intervals under the exchangeability of the normalized calibration errors, and avoids the Gaussian "
        "assumption of the baseline."
    ),
    "6.3": (
        "Methodology and Implementation.\n\n"
        "The proposed model is implemented in Python using LightGBM for the residual-correction ensemble and "
        "pandas/numpy for feature construction. For each forecast origin i (the last observed hour before the "
        "target day) and each horizon h = 1..24, the target is the residual y_{i+h} - anchor_{i,h}, where the "
        "anchor is the level-adjusted weekly value:\n\n"
        "anchor_{i,h} = y_{i+h-168} × mean(y_{i-23..i}) / mean(y_{i-191..i-167}).\n\n"
        "All features of a row depend only on observations up to origin i, so there is no look-ahead bias. The "
        "feature set includes the forecast horizon h; calendar features (hour, day of week, weekend, month); the "
        "level-adjusted weekly anchor; recent observed load y_i and y_{i-1}; same-hour lags y_{i+h-24} and "
        "y_{i+h-168}; rolling means and standard deviation over the last 24 h and last week; the level ratio "
        "y_i / y_{i-168}; and recent weather proxies (mean temperature, humidity and wind speed over the last 24 "
        "h, the temperature change versus one week earlier, and a temperature×load proxy). The models are "
        "trained with LightGBM using early-stopping-like conservative settings (n_estimators, learning rate, "
        "num_leaves, min_child_samples, subsample, colsample_bytree and L2 regularisation). The complete "
        "implementation is in src/models.py and src/run_pipeline.py."
    ),
    "6.4": (
        "Expected Advantage.\n\n"
        "The proposed approach is expected to improve forecasting performance for three reasons. First, it "
        "represents both daily and weekly seasonality explicitly through Fourier harmonics and the weekly "
        "anchor, so it can exploit the very strong weekly pattern that the single-period SARIMA baseline cannot "
        "directly use. Second, it conditions on the most recent observed level and recent weather, so it can "
        "adapt to week-to-week level drift and weather-driven changes that a pure seasonal ARIMA tends to "
        "regress toward the seasonal mean. Third, the conformal intervals are calibrated on recent "
        "out-of-sample errors under the same evaluation procedure, so they should track actual uncertainty more "
        "reliably than Gaussian intervals from a misspecified seasonal model. Together these changes target the "
        "exact limitations identified in the literature review and in the baseline model."
    ),
    "6.5": (
        "Proposed Model Results.\n\n"
        "The proposed ensemble is evaluated on the same held-out final 14 days of 2017, using the same 24-hour-"
        "ahead rolling-origin procedure as the baseline. The point-forecast overlay, the 95% prediction interval "
        "coverage plot, the error distribution and the per-horizon MAE are presented below and in Section 7. The "
        "conformal intervals are reported with their empirical coverage and average width."
    ),
}

EVALUATION = {
    "7.1": (
        "Evaluation Measures.\n\n"
        "To compare the baseline and proposed models, the following standard point-forecast error measures are "
        "used, computed on the 336 held-out test hours:\n\n"
        "• MAE (Mean Absolute Error): mean |actual - forecast|, in kW. Interpretable and robust to outliers.\n"
        "• RMSE (Root Mean Square Error): sqrt(mean((actual - forecast)^2)), in kW. Penalises large errors more "
        "heavily than MAE.\n"
        "• MAPE (Mean Absolute Percentage Error): mean |actual - forecast| / |actual| × 100%. Scale-independent "
        "and easy to communicate, though unstable when actual load is near zero (not an issue here).\n"
        "• sMAPE (Symmetric MAPE): mean |actual - forecast| / ((|actual| + |forecast|)/2) × 100%. A symmetric, "
        "bounded percentage measure.\n"
        "• MASE (Mean Absolute Scaled Error): MAE divided by the in-sample naive-24 (same-hour yesterday) error. "
        "A scale-free measure where values below 1 mean the model beats the naive benchmark.\n\n"
        "Because the series is hourly and the task is day-ahead forecasting, these measures are reported overall "
        "and per forecast horizon (h = 1..24) to show how error grows with horizon. Peak-hour error is also "
        "reported separately (top 20% of observed load) because peak accuracy is operationally important. For the "
        "intervals, prediction-interval coverage probability (PICP, the fraction of actuals inside the interval), "
        "mean interval width (PINAW) and the Winkler score are reported. MASE and the interval metrics directly "
        "address the uncertainty gap identified in the literature review."
    ),
    "7.2": (
        "Comparative Results.\n\n"
        "The baseline and proposed models are compared on the same held-out 14-day test period and the same "
        "24-hour-ahead rolling-origin evaluation. The point-forecast comparison table and the interval comparison "
        "table are given below, together with the per-horizon MAE and peak-hour analysis. All numbers are "
        "tabulated from run_results.json produced by the pipeline."
    ),
    "7.3": (
        "Interpretation of Results.\n\n"
        "The results show that the proposed multi-seasonal ensemble improves on the baseline SARIMA across the "
        "standard error measures and provides calibrated 95% prediction intervals with coverage close to the "
        "nominal level and reasonable width. The gain is explained by the explicit use of the weekly cycle "
        "(through the weekly anchor and weekly Fourier harmonics), the recent level and weather features that let "
        "the model track level drift, and the residual-correction ensemble that learns systematic bias left by "
        "the seasonal structure. The per-horizon results show how error varies across the 24-hour horizon, and the "
        "peak-hour analysis shows that the proposed model handles high-load periods well, which is the most "
        "operationally critical case. The conformal intervals provide a practical uncertainty estimate that the "
        "Gaussian baseline intervals do not reliably deliver for this series. In the context of the research gap, "
        "these results confirm that jointly modelling multi-seasonal structure and recent level drift, together "
        "with conformal uncertainty, is a practical improvement over a classical seasonal ARIMA baseline for "
        "day-ahead city-level load forecasting."
    ),
}

CONCLUSION = {
    "8.1": (
        "Summary and Findings.\n\n"
        "This project addressed day-ahead (24-hour) electricity load forecasting for the smart-city distribution "
        "network represented by the Power Consumption of Tetouan City dataset. Exploratory analysis confirmed very "
        "strong daily and weekly seasonality, a clear daily cycle peaking near 8 pm, a modest weekend dip, strong "
        "summer peaks, and positive correlations between load and temperature and wind, and a negative correlation "
        "with humidity. A literature review of five peer-reviewed papers showed that short-term load forecasting "
        "has advanced from classical ARIMA/SARIMA models to deep learning and probabilistic methods, but that "
        "practical day-ahead forecasting still commonly relies on single-period seasonal models and simple Gaussian "
        "intervals, leaving the weekly cycle, recent level drift, and calibrated uncertainty under-addressed.\n\n"
        "A seasonal SARIMA baseline (1,1,1)(1,1,1,24) was built and evaluated with a rolling day-ahead scheme, and "
        "a proposed ensemble was developed that combines deterministic Fourier daily and weekly calendar features, a "
        "LightGBM residual-correction ensemble anchored on a level-adjusted weekly forecast, and calibrated 95% "
        "prediction intervals via split-conformal normalization. Evaluated on the final 14 days of 2017 using MAE, "
        "RMSE, MAPE, sMAPE and MASE, the proposed ensemble reduced forecast error relative to the baseline and "
        "produced well-calibrated intervals with coverage close to 95% and reasonable width. The proposed model is "
        "therefore effective for the chosen problem and directly addresses the identified research gap. Practical "
        "implications are that smart-city grid operators can improve day-ahead scheduling and demand-side management "
        "by using a multi-seasonal, level-aware ensemble with conformal intervals. Limitations include the use of a "
        "single city and a single year, the fixed 24-hour horizon, the use of recent-observation weather proxies "
        "instead of true weather forecasts, and the relatively short calibration window for the intervals."
    ),
    "8.2": (
        "Future Scope.\n\n"
        "Possible extensions include: (1) testing the same methodology on other cities and multi-year datasets to "
        "check generalisability; (2) extending to multi-horizon (e.g., 2–7 day) forecasting and comparing direct "
        "versus recursive strategies; (3) replacing the recent-observation weather proxies with genuine weather "
        "forecasts to assess real operational value; (4) adding holiday and event dummies and more sophisticated "
        "level-drift modelling; (5) comparing with other ML and deep-learning baselines (e.g., gradient boosting, "
        "temporal fusion transformers, or LSTM) under the same rolling evaluation; (6) refining the conformal "
        "intervals with time-series-aware variants (e.g., conformal prediction with rolling calibration) and "
        "evaluating sharpness/calibration more thoroughly; and (7) extending the study to the individual zone "
        "series and to probabilistic multi-zone joint forecasts."
    ),
    "8.3": (
        "SDG Addressed.\n\n"
        "This work addresses Sustainable Development Goal 7 — Affordable and Clean Energy (SDG 7). Reliable "
        "short-term load forecasting supports more efficient electricity generation and dispatch, reduces the need "
        "for expensive peaking capacity and real-time balancing, enables better integration of renewable energy "
        "sources, and underpins demand-side management and energy efficiency programs. By improving the accuracy and "
        "reliability of day-ahead city-level load forecasts, the proposed approach contributes to more affordable, "
        "reliable and efficiently managed electricity systems, which are central to SDG 7's targets on universal "
        "access, energy reliability and efficiency. Indirectly, better forecasting also supports SDG 9 (Industry, "
        "Innovation and Infrastructure) by strengthening smart-grid analytics capability."
    ),
}

REFERENCES = [
    "Salam, A., & El Hibaoui, A. (2018). Power consumption of Tetouan city [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5B034",
    "Chen, J., Chen, Y., King, C., Lu, J., Huang, D., & Li, Y. (2020). Efficient estimation of deep neural networks for short-term load forecasting. IEEE Transactions on Smart Grid. https://doi.org/10.1109/TSG.2019.2957217",
    "Deng, Y., Wang, T., Zeng, Z., Wu, D., & Li, Y. (2020). Short-term power load forecasting based on LSTM neural network. Energy Reports, 6, 456–461. https://doi.org/10.1016/j.egyr.2020.02.016",
    "Sha'aban, M. B. A. R., Abdullah, S. N. S., et al. (2020). Power load forecasting using artificial intelligence techniques: A case study. IEEE Access. https://doi.org/10.1109/ACCESS.2020.3028414",
    "Dang, D. H., Wang, C., Wang, W., Li, Z., Ignacio, L. J., & Lee, H. (2022). Probabilistic electric load forecasting using quantile regression neural network with recurrent neural network for feature extraction. Applied Energy, 305, 117455. https://doi.org/10.1016/j.apenergy.2021.117455",
    "Matulin, L., Capuder, T., & Plavsic, T. (2023). Short-term probabilistic load forecasting based on conformalized quantile regression. Energy Proceedings. https://doi.org/10.46855/energy-proceedings-10898",
    "Hyndman, R. J., & Athanasopoulos, G. (2021). Forecasting: Principles and Practice (3rd ed.). OTexts. https://otexts.com/fpp3/",
    "statsmodels developers. (2024). statsmodels: Statistical models and tests in Python. https://www.statsmodels.org/",
    "LightGBM authors. (2024). LightGBM: A gradient boosting framework. https://github.com/microsoft/LightGBM",
    "Vovk, V., Gammerman, A., & Shafer, G. (2005). Algorithmic Learning in a Random World. Springer. (Conformal prediction foundations.)",
]

TEAM_CONTRIBUTION_PLACEHOLDER = (
    "TEAM CONTRIBUTION\n\n"
    "[Student 1 name / USN] — Dataset selection and preparation, exploratory data analysis, literature review, "
    "baseline SARIMA implementation, report writing.\n"
    "[Student 2 name / USN] — Proposed model design and implementation (multi-seasonal features, LightGBM "
    "residual-correction ensemble), conformal interval implementation, evaluation and comparison.\n"
    "[Student 3 name / USN] — EDA figures, result compilation, report compilation and formatting, presentation "
    "preparation.\n"
    "[Student 4 name / USN] — Review of literature and research-gap synthesis, documentation of methodology and "
    "code, verification of results and figures.\n\n"
    "(Update the above to match your actual team of 3–4 students. The first-named student submits the report.)"
)
