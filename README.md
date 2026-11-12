# Day-Ahead City-Level Electricity Load Forecasting — Tetouan City

**Time Series Analysis — Lab AAT**

This repository contains the project work for a day-ahead electricity load forecasting study on Tetouan City, Morocco. It includes the dataset preparation, exploratory data analysis, baseline and proposed models, evaluation outputs, and the formatted report and presentation.

---

## What this project is about

- **Task:** day-ahead forecasting of city-level electricity load.
- **Target:** Tetouan City, Morocco.
- **Data:** hourly city-level load for 2024.
- **Application domain:** Smart City / Energy.
- **SDG addressed:** SDG 7 — Affordable and Clean Energy.

The project compares a seasonal baseline model with a proposed multi-seasonal ensemble approach and includes prediction intervals to quantify forecast uncertainty.

---

## Project deliverables

- **Report:** `report/TSA_AAT_Report.docx`
- **Presentation:** `report/TSA_AAT_Presentation.pptx`
- **Results tables:** `outputs/tables/`
- **EDA and result figures:** `outputs/figures/`
- **Source code:** `src/`
- **Raw data:** `data/raw/`

---

## Repository structure

```text
.
├── README.md
├── .gitignore
├── data/
│   └── raw/
│       └── Tetuan City power consumption.csv
├── src/
│   ├── config.py
│   ├── data_prep.py
│   ├── eda.py
│   ├── evaluate.py
│   ├── lit_review.py
│   ├── models.py
│   ├── run_pipeline.py
│   ├── build_report.py
│   ├── build_pptx.py
│   └── text_content.py
├── outputs/
│   ├── tables/
│   │   ├── run_results.json
│   │   ├── eda_stats.json
│   │   ├── model_comparison.csv
│   │   ├── forecast_test.csv
│   │   └── peak_error.csv
│   └── figures/
│       ├── fig01_full_series.png
│       ├── fig02_two_weeks.png
│       ├── fig03_daily_profile.png
│       ├── fig04_monthly_box.png
│       ├── fig05_stl.png
│       ├── fig06_acf_pacf.png
│       ├── fig07_correlation.png
│       ├── fig08_zone_profiles.png
│       ├── fig09_forecast_comparison.png
│       ├── fig10_interval_coverage.png
│       ├── fig11_error_distribution.png
│       └── fig12_per_horizon_mae.png
└── report/
    ├── TSA_AAT_Report.docx
    └── TSA_AAT_Presentation.pptx
```

---

## Key files

### `outputs/tables/run_results.json`
Main results file for the baseline and proposed models. It includes:
- baseline results
- proposed model results
- comparison summary
- peak-error analysis
- figure paths
- total run time

### `outputs/tables/eda_stats.json`
Exploratory data analysis statistics for the load series, including:
- number of hourly observations
- mean, min, max, standard deviation
- daily/weekly load behavior
- correlation with weather variables
- monthly and stationarity-related summaries

### `outputs/figures/`
Figures used in the report and presentation, including:
- full-series load profile
- zoomed two-week view
- daily profile
- monthly distribution
- STL decomposition
- ACF/PACF
- correlation analysis
- zone profiles
- forecast comparison
- interval coverage
- error distribution
- per-horizon MAE

---

## Scope of the work

The project focuses on:
- understanding the hourly load series through EDA
- building a seasonal baseline model
- developing a proposed ensemble-style forecasting improvement
- evaluating both approaches on a held-out test period
- adding prediction intervals for uncertainty

It is a course lab project, so the emphasis is on methodology, reproducibility, and clear presentation rather than on a production system.

---

## Necessity and purpose of each part

- **`src/`** — code used to prepare data, run EDA, build models, evaluate results, and generate the report and presentation.
- **`outputs/tables/`** — final numerical outputs needed to compare the baseline and proposed models.
- **`outputs/figures/`** — visual evidence used to support the analysis and results.
- **`report/`** — the submitted report and presentation for faculty evaluation.
- **`data/raw/`** — the original load dataset used in the study.

---

## How to use this repository

1. Open the report `report/TSA_AAT_Report.docx` for the full written submission.
2. Open the presentation `report/TSA_AAT_Presentation.pptx` for the slide version.
3. Use `outputs/tables/run_results.json` and `outputs/tables/eda_stats.json` to inspect the main numbers.
4. Use `outputs/figures/` to view the charts.
5. Use `src/` to understand or rerun parts of the analysis.

---

## Notes for evaluation

- The report contains the literature review, methodology, results, and conclusion.
- The literature review table includes clickable DOI links to the referenced papers.
- All figures and result tables are generated from the project outputs.
- Student identity fields in the report are left as placeholders for the student to fill in.

---

## License and attribution

This is an academic lab project. If the dataset or any external source requires attribution or has usage restrictions, that should be confirmed before reuse.
