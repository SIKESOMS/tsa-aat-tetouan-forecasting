# Project necessity and structure — quick guide

This file explains **why each part of the repository exists**, for faculty review.

## Why this project exists

This is a Time Series Analysis Lab (AAT) project on **day-ahead city-level electricity load forecasting for Tetouan City, Morocco**. It is meant to show that the student can:

- take a real time-series dataset,
- explore it properly,
- build a sensible baseline,
- propose a better approach,
- evaluate both fairly,
- and present the work as a report and presentation.

---

## What each folder is for

### `src/`
Contains the code that produces the analysis and the final documents.

- `config.py` — shared paths and constants.
- `data_prep.py` — dataset download/cleaning/aggregation.
- `eda.py` — exploratory data analysis and EDA statistics.
- `models.py` — baseline and proposed model implementation.
- `evaluate.py` — result comparison and table generation.
- `run_pipeline.py` — runs the main analysis pipeline.
- `build_report.py` — builds the submitted report DOCX.
- `build_pptx.py` — builds the presentation PPTX.
- `lit_review.py` — literature review content and paper references.
- `text_content.py` — report section text.

### `outputs/tables/`
Final result tables that support the findings.

- `run_results.json` — main results for baseline, proposed, comparison, and peak analysis.
- `eda_stats.json` — EDA statistics for the load series.
- `model_comparison.csv` — comparison summary.
- `forecast_test.csv` — test-period forecast output.
- `peak_error.csv` — peak-hour error analysis.

### `outputs/figures/`
Charts used in the report and presentation.

These are the visual evidence for:
- overall load pattern,
- daily and weekly behavior,
- seasonality and decomposition,
- correlation with weather,
- forecast comparison,
- prediction intervals,
- error analysis.

### `report/`
The submitted deliverables.

- `TSA_AAT_Report.docx` — the main written report.
- `TSA_AAT_Presentation.pptx` — the slide version for presentation.

### `data/raw/`
The original dataset used in the project.

---

## Why these deliverables matter

- The **report** is the main academic submission. It explains the problem, dataset, literature, methodology, results, and conclusion.
- The **presentation** is the same work in slide form for oral presentation.
- The **result tables and figures** are the proof that the numbers in the report come from the actual analysis.
- The **code** shows how the analysis was built and makes the work reproducible.

---

## What makes this project meaningful

It is not just a modelling exercise. It demonstrates:

- a real smart-city energy problem,
- a clear baseline-first approach,
- an attempt to improve forecasting quality,
- uncertainty quantification through prediction intervals,
- and a complete academic presentation package.

---

## Note for faculty

- If any student details are still placeholders in the report, they should be filled in before final submission.
- If the project is to be demonstrated, use the report as the primary reference and the presentation as the speaking aid.
- The results in `outputs/tables/run_results.json` are the authoritative numbers for the final comparison.
