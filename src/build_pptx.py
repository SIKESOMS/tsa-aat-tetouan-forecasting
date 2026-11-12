import sys, os
sys.path.insert(0, '/path/to/venv')  # will be ignored on Windows

# Run this from E:\TSA\tsa-project as:
#   python -c "import run; run.main()"
# or just:
#   python src/build_pptx.py

from pathlib import Path
import json, zipfile
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
from PIL import Image

BASE = Path(r"E:\TSA\tsa-project")
REPORT_DIR = BASE / "report"
FIGS = BASE / "outputs" / "figures"
TABLES = BASE / "outputs" / "tables"

OUT = REPORT_DIR / "TSA_AAT_Presentation.pptx"

# Load data
with open(TABLES / "run_results.json") as f:
    R = json.load(f)
with open(TABLES / "eda_stats.json") as f:
    EDA = json.load(f)

from lit_review import table_rows
LIT_ROWS = table_rows()

# Colors
NAVY = RGBColor(0x0B, 0x28, 0x4A)
STEEL = RGBColor(0x3A, 0x5F, 0x8A)
LIGHT = RGBColor(0xD6, 0xE4, 0xF2)
LGREY = RGBColor(0x9A, 0x9A, 0x9A)
GREY = RGBColor(0x66, 0x66, 0x66)
BLACK = RGBColor(0,0,0)
WHITE = RGBColor(0xFF,0xFF,0xFF)
GOLD = RGBColor(0xB8, 0x86, 0x0B)
PALE = RGBColor(0xBF, 0xD4, 0xE8)

def blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])

def bg(s, color=NAVY):
    shp = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    shp.fill.solid(); shp.fill.fore_color.rgb = color; shp.line.fill.background()
    shp.shadow.inherit = False

def band(s, top, color, h=0.10):
    shp = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, top, prs.slide_width, Inches(h))
    shp.fill.solid(); shp.fill.fore_color.rgb = color; shp.line.fill.background()

def tb(s, l, t, w, h):
    box = s.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    box.text_frame.word_wrap = True
    return box

def ap(tf, text, size=12, bold=False, color=BLACK, italic=False, align=PP_ALIGN.LEFT,
       first=False, sa=4, font="Calibri"):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align; p.space_after = Pt(sa)
    r = p.add_run(); r.text = text
    r.font.size = Pt(size); r.font.bold = bold; r.font.italic = italic
    r.font.color.rgb = color; r.font.name = font
    return p

def title_line(s, title, sub=None):
    band(s, 0, STEEL, 0.10)
    band(s, 0.10, NAVY, 0.85)
    box = tb(s, 0.6, 0.18, 12.1, 0.55)
    ap(box.text_frame, title, 20, True, WHITE, first=True)
    if sub:
        ap(box.text_frame, sub, 11, False, LIGHT)
    band(s, 0.95, GOLD, 0.02)

def bullets(s, l, t, w, h, items, size=12.5, gap=7, bold_lead=True):
    box = tb(s, l, t, w, h)
    tf = box.text_frame
    for i, (lead, rest) in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        if bold_lead:
            r1 = p.add_run(); r1.text = lead + " "
            r1.font.size = Pt(size); r1.font.bold = True
            r1.font.color.rgb = NAVY; r1.font.name = "Calibri"
        r2 = p.add_run(); r2.text = rest
        r2.font.size = Pt(size); r2.font.color.rgb = BLACK; r2.font.name = "Calibri"

def stat_card(s, l, t, w, h, value, label):
    shp = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
    shp.fill.solid(); shp.fill.fore_color.rgb = STEEL; shp.line.fill.background()
    shp.shadow.inherit = False
    tf = shp.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.08)
    p1 = tf.paragraphs[0]; p1.alignment = PP_ALIGN.CENTER
    r1 = p1.add_run(); r1.text = str(value)
    r1.font.size = Pt(18); r1.font.bold = True; r1.font.color.rgb = WHITE; r1.font.name = "Calibri"
    p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.CENTER; p2.space_before = Pt(2)
    r2 = p2.add_run(); r2.text = str(label)
    r2.font.size = Pt(8); r2.font.color.rgb = LIGHT; r2.font.name = "Calibri"

def add_img(s, path, l, t, w, h=None):
    im = Image.open(path); ar = im.width / im.height
    if h is None: h = w / ar
    s.shapes.add_picture(path, Inches(l), Inches(t), Inches(w), Inches(h))

def pic_slide(title, sub, img_path, caption, page_label, w=8.6):
    s = blank(prs)
    title_line(s, title, sub)
    add_img(s, img_path, 0.7, 1.35, w)
    cap_h = 1.35 + (w / (Image.open(img_path).width / Image.open(img_path).height)) + 0.08
    cap = tb(s, 0.7, cap_h, 11.9, 0.45)
    ap(cap.text_frame, caption, 10.5, italic=True, color=GREY, first=True)
    footer(s, page_label)

def footer(s, label=""):
    band(s, 7.15, NAVY, 0.35)
    box = tb(s, 0.5, 7.19, 9.5, 0.25)
    ap(box.text_frame, "Day-Ahead City-Level Electricity Load Forecasting, Tetouan City", 8, color=LGREY, first=True)
    if label:
        box2 = tb(s, 11.6, 7.19, 1.4, 0.25)
        ap(box2.text_frame, label, 8, color=GOLD, first=True, align=PP_ALIGN.RIGHT)

def sc(cell, text, size=10.5, bold=False, color=BLACK, fill=None, align=PP_ALIGN.LEFT):
    cell.text = ""
    tf = cell.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = align
    r = p.add_run(); r.text = str(text)
    r.font.size = Pt(size); r.font.bold = bold; r.font.color.rgb = color; r.font.name = "Calibri"
    if fill is not None:
        cell.fill.solid(); cell.fill.fore_color.rgb = fill

def fmt(x):
    try: return f"{float(x):.2f}"
    except: return str(x)

def fmt_int(x):
    try: return f"{int(float(x))}"
    except: return str(x)

def pct(a, b):
    try: return f"{(float(a) - float(b)) / float(a) * 100:.1f}%"
    except: return ""

print("Building presentation...")

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# ===== SLIDE 1: TITLE =====
s = blank(prs); bg(s, NAVY)
shp = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.28), prs.slide_height)
shp.fill.solid(); shp.fill.fore_color.rgb = STEEL; shp.line.fill.background()
box = tb(s, 1.2, 1.4, 10.8, 2.6)
ap(box.text_frame, "Day-Ahead City-Level Electricity Load Forecasting", 32, True, WHITE, first=True)
ap(box.text_frame, "for Tetouan City, Morocco", 28, False, PALE, sa=10)
box2 = tb(s, 1.2, 3.7, 10.8, 0.6)
ap(box2.text_frame, "A Time Series Analysis Lab AAT Project", 16, color=LIGHT, italic=True, first=True)
box3 = tb(s, 1.2, 4.5, 10.8, 1.2)
ap(box3.text_frame, "Guided by: Dr. ...", 13, color=LIGHT, first=True, sa=3)
ap(box3.text_frame, "Department of Machine Learning  |  7th Semester, Section C", 12, color=LGREY, sa=3)
ap(box3.text_frame, "B. M. S. College of Engineering", 12, color=LGREY)
band(s, 5.75, GOLD, 0.02)
box4 = tb(s, 1.2, 5.9, 10.8, 0.5)
ap(box4.text_frame, "Smart City / Energy  -  SDG 7: Affordable and Clean Energy", 11, italic=True, color=LGREY, first=True)
footer(s, "Title")

# ===== SLIDE 2: AGENDA =====
s = blank(prs); bg(s, WHITE)
title_line(s, "Agenda", "A guided walk through the project")
agenda = [
    ("01", "Introduction & Motivation"), ("02", "Literature Review"),
    ("03", "Gap Analysis & Proposed Approach"), ("04", "Dataset & Exploratory Data Analysis"),
    ("05", "Baseline SARIMA Model"), ("06", "Proposed Pooled LightGBM Residual-Corrective Ensemble"),
    ("07", "Reproducibility & Evaluation Protocol"), ("08", "Results"),
    ("09", "Conclusion & Future Work"),
]
box = tb(s, 1.0, 1.5, 5.6, 5.0); tf = box.text_frame
for i, (num, txt) in enumerate(agenda):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.space_after = Pt(12)
    r1 = p.add_run(); r1.text = num + "   "
    r1.font.size = Pt(16); r1.font.bold = True; r1.font.color.rgb = GOLD; r1.font.name = "Calibri"
    r2 = p.add_run(); r2.text = txt
    r2.font.size = Pt(16); r2.font.color.rgb = BLACK; r2.font.name = "Calibri"
add_img(s, str(FIGS / "fig01_full_series.png"), 7.0, 1.6, 5.9)
footer(s, "Agenda")

# ===== SLIDE 3: INTRODUCTION =====
s = blank(prs); bg(s, WHITE)
title_line(s, "Introduction", "Why forecasting city-level electricity load matters")
bullets(s, 0.7, 1.35, 7.2, 5.4, [
    ("Urban electricity demand:", "a core input to power system planning, unit commitment, demand response, and tariff design."),
    ("Forecasting horizon:", "this work targets day-ahead (24-hour-ahead) forecasts of the city-level load profile of Tetouan City, Morocco."),
    ("Granularity:", "hourly load aggregated at the city level for an entire year (January-December 2024)."),
    ("Why Tetouan:", "a mid-sized coastal city with distinctive daily, weekly and seasonal patterns that motivate a seasonal, interpretable baseline and a robust ensemble."),
    ("Applications:", "peak-load anticipation, grid reliability, integration of intermittent renewables, and local distribution planning."),
], size=13, gap=8)
footer(s, "Introduction")

# ===== SLIDE 4: EDA 1 =====
s = blank(prs); bg(s, WHITE)
title_line(s, "Exploratory Data Analysis  (1)", "What the data reveals before modelling")
bullets(s, 0.7, 1.3, 6.0, 5.5, [
    ("Load series:", "hourly city-level load for all of 2024, plotted in Figure 1."),
    ("Range:", "load oscillates between roughly 550 kW and 4,000 kW across the year."),
    ("Seasonality:", "clear annual seasonality - hotter summer months show systematically higher demand."),
    ("Daily cycle:", "a strong repeatable daily pattern with morning and evening peaks and a night-time trough."),
    ("Weekly pattern:", "weekend load drops noticeably compared to weekdays - visible in the two-week zoom (Figure 2)."),
    ("Stationarity:", "the raw series is clearly non-stationary (trend + seasonality), motivating differencing in the baseline."),
], size=12.5, gap=7)
footer(s, "EDA")

# ===== SLIDE 5: EDA full series =====
pic_slide("Exploratory Data Analysis  (2)",
          "Full-year hourly load profile for Tetouan City, 2024",
          str(FIGS / "fig01_full_series.png"),
          "Figure 1: Full-year hourly load for Tetouan City (2024). The series shows annual seasonality, a clear daily cycle, and variability across months.",
          "Fig. 1")

# ===== SLIDE 6: EDA two-week zoom =====
pic_slide("Exploratory Data Analysis  (3)",
          "Two-week zoom: daily cycle and weekend dip",
          str(FIGS / "fig02_two_weeks.png"),
          "Figure 2: Two-week close-up of the load series showing the repeatable daily pattern and the clear weekend drop - the predictable structure seasonal models exploit.",
          "Fig. 2")

# ===== SLIDE 7: EDA stats =====
s = blank(prs); bg(s, WHITE)
title_line(s, "Exploratory Data Analysis  (4)", "Descriptive statistics at a glance")
stat_card(s, 0.7, 1.5, 2.9, 1.5, fmt_int(EDA.get("rows_hourly")), "Total hourly observations (2024)")
stat_card(s, 3.85, 1.5, 2.9, 1.5, f"{fmt_int(EDA.get('mean_kW'))} kW", "Mean hourly load")
stat_card(s, 7.0, 1.5, 2.9, 1.5, f"{fmt_int(EDA.get('min_kW'))} kW", "Minimum hourly load")
stat_card(s, 10.15, 1.5, 2.9, 1.5, f"{fmt_int(EDA.get('max_kW'))} kW", "Maximum hourly load")
stat_card(s, 0.7, 3.3, 2.9, 1.5, f"{fmt_int(EDA.get('std_kW'))} kW", "Std deviation of hourly load")
stat_card(s, 3.85, 3.3, 2.9, 1.5, f"{fmt_int(EDA.get('median_kW'))} kW", "Median hourly load")
stat_card(s, 7.0, 3.3, 2.9, 1.5, f"{fmt_int(EDA.get('q25_kW'))} kW", "25th percentile")
stat_card(s, 10.15, 3.3, 2.9, 1.5, f"{fmt_int(EDA.get('q75_kW'))} kW", "75th percentile")
footer(s, "EDA")

# ===== SLIDE 8: EDA daily profile + STL =====
s = blank(prs); bg(s, WHITE)
title_line(s, "Exploratory Data Analysis  (5)", "Average daily load profile by month")
add_img(s, str(FIGS / "fig03_daily_profile.png"), 0.55, 1.35, 5.9)
add_img(s, str(FIGS / "fig05_stl.png"), 6.75, 1.35, 6.1)
footer(s, "EDA")

# ===== SLIDE 9: EDA monthly box + acf/pacf =====
s = blank(prs); bg(s, WHITE)
title_line(s, "Exploratory Data Analysis  (6)", "Monthly load distribution and autocorrelation structure")
add_img(s, str(FIGS / "fig04_monthly_box.png"), 0.55, 1.35, 6.0)
add_img(s, str(FIGS / "fig06_acf_pacf.png"), 7.0, 1.35, 6.0)
footer(s, "EDA")

# ===== SLIDE 10: EDA correlation =====
s = blank(prs); bg(s, WHITE)
title_line(s, "Exploratory Data Analysis  (7)", "Self- and lag-correlations")
add_img(s, str(FIGS / "fig07_correlation.png"), 1.2, 1.3, 6.4)
footer(s, "EDA")

# ===== SLIDE 11: EDA zones =====
s = blank(prs); bg(s, WHITE)
title_line(s, "Exploratory Data Analysis  (8)", "Zone-level profiles")
add_img(s, str(FIGS / "fig08_zone_profiles.png"), 1.6, 1.45, 6.7)
footer(s, "EDA")

# ===== SLIDE 12: LIT REVIEW TABLE =====
s = blank(prs); bg(s, WHITE)
title_line(s, "Literature Review  (1)", "Related work in electricity load forecasting")

rows = len(LIT_ROWS) + 1
cols = 5
left = Inches(0.35); top = Inches(1.2)
tbl_shape = s.shapes.add_table(rows, cols, left, Inches(1.2), Inches(12.65), Inches(5.65))
tbl = tbl_shape.table; tbl.first_row = False; tbl.horz_banding = False
col_w = [Inches(0.45), Inches(2.95), Inches(3.95), Inches(4.55), Inches(0.75)]
for j, w in enumerate(col_w):
    tbl.columns[j].width = w

headers = ["#", "Reference", "Contribution / method", "Relevance to this work", "DOI"]
for j, h in enumerate(headers):
    sc(tbl.cell(0, j), h, 10, True, WHITE, NAVY, PP_ALIGN.CENTER if j in (0,4) else PP_ALIGN.LEFT)
    tbl.cell(0, j).vertical_anchor = MSO_ANCHOR.MIDDLE

for i, row in enumerate(LIT_ROWS):
    r = i + 1; fill = LIGHT if r % 2 else WHITE
    sc(tbl.cell(r, 0), str(i + 1), 8.5, True, NAVY, fill, PP_ALIGN.CENTER)
    sc(tbl.cell(r, 1), row.get("paper", ""), 8.5, True, BLACK, fill, PP_ALIGN.LEFT)
    sc(tbl.cell(r, 2), row.get("problem_dataset", "") + " " + row.get("method", ""),
       8, False, BLACK, fill, PP_ALIGN.LEFT)
    sc(tbl.cell(r, 3), row.get("findings", "") + " " + row.get("limitations", ""),
       8, False, GREY, fill, PP_ALIGN.LEFT)
    sc(tbl.cell(r, 4), row.get("link", ""), 7.5, False, NAVY, fill, PP_ALIGN.CENTER)
    for j in range(cols):
        tbl.cell(r, j).vertical_anchor = MSO_ANCHOR.MIDDLE
footer(s, "Lit. review")

# ===== SLIDE 13: LIT REVIEW THEMES =====
s = blank(prs); bg(s, WHITE)
title_line(s, "Literature Review  (2)", "Key themes and common limitations")
bullets(s, 0.7, 1.35, 6.0, 5.4, [
    ("Seasonal decomposition:", "STL and related decompositions are widely used to isolate trend/seasonal/residual structure before or alongside modelling."),
    ("Classical baselines:", "ARIMA/SARIMA remain a standard interpretable benchmark for seasonal hourly series, often used as a floor before ensembles or ML."),
    ("Machine learning:", "gradient boosting and tree-based methods (incl. LightGBM) are increasingly applied to load and price forecasting with engineered temporal features."),
    ("Conformal prediction:", "split-conformal methods give calibrated, distribution-free intervals that can complement point forecasts without parametric assumptions."),
    ("Gap in literature:", "fewer city-scale, single-city day-ahead studies on Tetouan, and fewer that couple a seasonal baseline with a residual-correcting ensemble and conformal intervals in one reproducible pipeline."),
], size=12, gap=7)
footer(s, "Lit. review")

# ===== SLIDE 14: GAP & APPROACH =====
s = blank(prs); bg(s, WHITE)
title_line(s, "Gap Analysis & Proposed Approach", "What is missing, and how this project addresses it")
bullets(s, 0.7, 1.35, 6.0, 5.4, [
    ("Gap:", "city-level, single-city day-ahead forecasting for Tetouan is under-represented; most work focuses on larger systems or higher aggregation."),
    ("Gap:", "limited use of a seasonal baseline paired with a residual-correcting ML ensemble and calibrated uncertainty in one end-to-end reproducible workflow."),
    ("Approach:", "we benchmark a seasonal SARIMA baseline against a pooled LightGBM residual-corrective ensemble."),
    ("Approach:", "seasonal Fourier terms, weekly anchor, weather proxies and rolling features feed the learner; split-conformal inference wraps 95% prediction intervals."),
    ("Aim:", "improve accuracy over the SARIMA baseline while preserving an interpretable seasonal backbone and delivering calibrated intervals."),
], size=12, gap=7)
footer(s, "Gap & approach")

# ===== SLIDE 15: DATASET =====
s = blank(prs); bg(s, WHITE)
title_line(s, "Dataset", "Tetouan City hourly load, 2024")
bullets(s, 0.7, 1.35, 7.0, 2.6, [
    ("Source:", "hourly city-level electricity load for Tetouan City, Morocco, covering the full year 2024."),
    ("Granularity:", "one observation per hour, 24 hours per day, ~8784 observations in the year."),
    ("Scope:", "aggregated city-level load (kW) used as the target for day-ahead (24-hour-ahead) forecasting."),
    ("Supplements:", "temporal features (hour, day-of-week, month), Fourier seasonal terms, a weekly anchor, and weather proxies used as model inputs."),
], size=12.5, gap=7)

rows2 = 6; cols2 = 2
tbl_shape2 = s.shapes.add_table(rows2, cols2, Inches(0.7), Inches(4.35), Inches(7.0), Inches(2.35))
tbl2 = tbl_shape2.table; tbl2.first_row = False; tbl2.horz_banding = False
tbl2.columns[0].width = Inches(3.5); tbl2.columns[1].width = Inches(3.5)
sc(tbl2.cell(0,0), "Statistic", 11, True, WHITE, NAVY, PP_ALIGN.CENTER)
sc(tbl2.cell(0,1), "Value", 11, True, WHITE, NAVY, PP_ALIGN.CENTER)
stats_tbl = [
    ("Total hours", fmt_int(EDA.get("rows_hourly"))),
    ("Mean load (kW)", fmt_int(EDA.get("mean_kw"))),
    ("Min load (kW)", fmt_int(EDA.get("min_kw"))),
    ("Max load (kW)", fmt_int(EDA.get("max_kw"))),
    ("Std dev (kW)", fmt_int(EDA.get("std_kw"))),
]
for i, (k, v) in enumerate(stats_tbl):
    r = i + 1; fill = LIGHT if r % 2 else WHITE
    sc(tbl2.cell(r, 0), k, 10.5, False, BLACK, fill, PP_ALIGN.LEFT)
    sc(tbl2.cell(r, 1), v, 10.5, True, NAVY, fill, PP_ALIGN.CENTER)
footer(s, "Dataset")

# ===== SLIDE 16: BASELINE SARIMA =====
s = blank(prs); bg(s, WHITE)
title_line(s, "Baseline Model", "SARIMA(1,1,1)(1,1,1,24)")
bullets(s, 0.7, 1.35, 12.0, 5.4, [
    ("Model:", "seasonal ARIMA, SARIMA(1,1,1)(1,1,1,24), fitted to the hourly load series."),
    ("Why SARIMA:", "hourly electricity load is strongly seasonal at the daily (24h) and weekly scales; SARIMA captures the seasonal ARIMA structure directly."),
    ("Order rationale:", "the (1,1,1) non-seasonal part handles short-term dependence after first differencing; the (1,1,1,24) seasonal part captures the 24-hour daily cycle."),
    ("Role:", "this forms the interpretable seasonal baseline against which the proposed ensemble is compared on the same 14-day held-out test set."),
    ("Forecast target:", "24-hour-ahead day-ahead forecasts: at each hour t the model predicts load at t+24."),
], size=13, gap=9)
footer(s, "Baseline")

# ===== SLIDE 17: PROPOSED ENSEMBLE =====
s = blank(prs); bg(s, WHITE)
title_line(s, "Proposed Model", "Pooled LightGBM Residual-Corrective Ensemble")
bullets(s, 0.7, 1.35, 7.2, 5.4, [
    ("Core idea:", "a weekly anchor captures the stable weekly shape; a pooled LightGBM model learns to correct the anchor's residual errors."),
    ("Weekly anchor:", "the anchor is built from the same weekday pattern observed in prior weeks, giving a structured seasonal guess for each of the 24 horizons."),
    ("Fourier features:", "daily + weekly Fourier terms model smooth periodic variation and complement the anchor."),
    ("Weather proxies:", "temperature and related proxies are incorporated as input features where available, helping capture weather-driven load shifts."),
    ("LightGBM:", "a pooled gradient boosting model is trained across horizons to predict the residual between actual load and the weekly anchor."),
    ("Ensemble:", "final forecast = weekly anchor + LightGBM-predicted correction, pooling information across horizons."),
], size=12, gap=6)
footer(s, "Proposed")

# ===== SLIDE 18: CONFORMAL INTERVALS =====
s = blank(prs); bg(s, WHITE)
title_line(s, "Prediction Intervals", "Split-conformal 95% intervals")
bullets(s, 0.7, 1.35, 7.2, 5.4, [
    ("Motivation:", "point forecasts need calibrated uncertainty for operational decision-making; we add distribution-free 95% intervals."),
    ("Split-conformal:", "we use a held-out calibration set to compute nonconformity scores and derive interval half-widths that guarantee finite-sample coverage under exchangeability."),
    ("Construction:", "for each forecast, the interval is the point forecast +- the conformal quantile of the absolute residuals on the calibration set."),
    ("Coverage target:", "nominal 95% coverage; empirical coverage is reported on the 14-day test set (Figures 10 and the summary table)."),
    ("Benefit:", "intervals are data-driven, require no parametric error model, and adapt to the ensemble's residual behaviour across horizons."),
], size=12.5, gap=7)
footer(s, "Intervals")

# ===== SLIDE 19: FEATURES =====
s = blank(prs); bg(s, WHITE)
title_line(s, "Feature Engineering", "Temporal, periodic and weather features")
bullets(s, 0.7, 1.35, 6.4, 5.4, [
    ("Temporal:", "hour-of-day, day-of-week, month, and binary weekend flag to capture routine calendar effects."),
    ("Fourier terms:", "sinusoidal daily and weekly basis functions (multiple harmonics) to model smooth seasonality and complement the weekly anchor."),
    ("Weekly anchor:", "the anchor itself is used as a feature, letting the learner correct horizon-specific biases."),
    ("Weather proxies:", "temperature and related meteorological proxies are included as input features; these proxy weather-driven variation in load."),
    ("Rolling/lag features:", "recent load values and rolling statistics feed the model's short-horizon memory."),
], size=12.5, gap=8)
footer(s, "Features")

# ===== SLIDE 20: EVALUATION =====
s = blank(prs); bg(s, WHITE)
title_line(s, "Evaluation Protocol", "Split, metrics, and reproducibility")
bullets(s, 0.7, 1.35, 7.2, 5.4, [
    ("Train / calibration / test:", "the series is split into training, a calibration set for conformal inference, and a held-out 14-day test set for final evaluation."),
    ("Forecast task:", "day-ahead (24-hour-ahead) forecasts: predict load at t+24 given information up to hour t, across all 24 horizons of the day."),
    ("Metrics:", "MAE, MAPE and empirical interval coverage are used to compare the SARIMA baseline against the proposed ensemble."),
    ("Baseline:", "SARIMA(1,1,1)(1,1,1,24) provides an interpretable seasonal benchmark under identical evaluation conditions."),
    ("Reproducibility:", "the full pipeline, figures and tables are reproducible from run_results.json, eda_stats.json, lit_review.py and the figure assets."),
], size=12.5, gap=7)
footer(s, "Evaluation")

# ===== SLIDE 21: RESULTS TABLE =====
s = blank(prs); bg(s, WHITE)
title_line(s, "Results  (1)", "Baseline vs proposed on the 14-day test set")

baseline_mae = R.get("baseline", {}).get("MAE_kw", 0)
baseline_mape = R.get("baseline", {}).get("MAPE_pct", 0)
baseline_coverage = R.get("baseline", {}).get("PCR_coverage_95_pct", 0)
proposed_mae = R.get("proposed", {}).get("MAE_kw", 0)
proposed_mape = R.get("proposed", {}).get("MAPE_pct", 0)
proposed_coverage = R.get("proposed", {}).get("PCR_coverage_95_pct", 0)
conformal_q = R.get("proposed", {}).get("conformal_q", 0)

rows3 = 5; cols3 = 4
tbl_shape3 = s.shapes.add_table(rows3, cols3, Inches(0.7), Inches(1.4), Inches(11.9), Inches(2.7))
tbl3 = tbl_shape3.table; tbl3.first_row = False; tbl3.horz_banding = False
widths3 = [4.2, 2.57, 2.57, 2.56]
for j, w in enumerate(widths3):
    tbl3.columns[j].width = Inches(w)

headers3 = ["Metric", "SARIMA baseline", "Proposed ensemble", "Relative improvement"]
for j, h in enumerate(headers3):
    sc(tbl3.cell(0, j), h, 12, True, WHITE, NAVY, PP_ALIGN.CENTER)
    tbl3.cell(0, j).vertical_anchor = MSO_ANCHOR.MIDDLE

res_rows = [
    ("MAE (kW)", fmt(baseline_mae), fmt(proposed_mae), pct(baseline_mae, proposed_mae)),
    ("MAPE (%)", fmt(baseline_mape), fmt(proposed_mape), pct(baseline_mape, proposed_mape)),
    ("95% coverage (%)", fmt(baseline_coverage), fmt(proposed_coverage), ""),
    ("Conformal quantile", "-", fmt(conformal_q), ""),
]
for i, (m, b, p, rel) in enumerate(res_rows):
    r = i + 1; fill = LIGHT if r % 2 else WHITE
    sc(tbl3.cell(r, 0), m, 11.5, True, NAVY, fill, PP_ALIGN.LEFT)
    sc(tbl3.cell(r, 1), b, 11.5, False, BLACK, fill, PP_ALIGN.CENTER)
    sc(tbl3.cell(r, 2), p, 11.5, True, BLACK, fill, PP_ALIGN.CENTER)
    sc(tbl3.cell(r, 3), rel, 11.5, bool(rel), GOLD if rel else GREY, fill, PP_ALIGN.CENTER)
    for j in range(cols3):
        tbl3.cell(r, j).vertical_anchor = MSO_ANCHOR.MIDDLE

box = tb(s, 0.7, 4.4, 11.9, 1.6); tf = box.text_frame
ap(tf, "Key takeaway", 13, True, NAVY, first=True, sa=4)
ap(tf, f"The proposed pooled LightGBM residual-corrective ensemble reduces MAE from {fmt(baseline_mae)} kW to {fmt(proposed_mae)} kW "
       f"({pct(baseline_mae, proposed_mae)}), and MAPE from {fmt(baseline_mape)}% to {fmt(proposed_mape)}% "
       f"({pct(baseline_mape, proposed_mape)}), "
       "while maintaining strong prediction interval coverage.", 12, color=BLACK)
footer(s, "Results")

# ===== SLIDE 22: FORECAST COMPARISON =====
pic_slide("Results  (2)", "Forecast comparison: baseline vs proposed vs actual",
          str(FIGS / "fig09_forecast_comparison.png"),
          "Figure: Day-ahead forecast comparison over the held-out 14-day test period. The proposed ensemble tracks the actual load closely; the SARIMA baseline lags the level changes.",
          "Fig. 9")

# ===== SLIDE 23: INTERVAL COVERAGE =====
pic_slide("Results  (3)", "95% prediction interval coverage",
          str(FIGS / "fig10_interval_coverage.png"),
          "Figure: Coverage of the conformal 95% prediction intervals across the rolling day-ahead test forecasts. The band tracks the actual load with calibrated width.",
          "Fig. 10")

# ===== SLIDE 24: ERROR DISTRIBUTION =====
pic_slide("Results  (4)", "Error distribution & absolute error",
          str(FIGS / "fig11_error_distribution.png"),
          "Figure: Distribution of forecast errors and absolute-error boxplot, baseline vs proposed, on the test set. The proposed ensemble shifts the error distribution toward zero and tightens the spread.",
          "Fig. 11")

# ===== SLIDE 25: MAE BY HORIZON =====
pic_slide("Results  (5)", "MAE by forecast horizon",
          str(FIGS / "fig12_per_horizon_mae.png"),
          "Figure: Mean absolute error by forecast horizon h (1-24 h), proposed ensemble vs weekly anchor, over the 14-day test period. The correction mainly helps the later horizons where the anchor degrades.",
          "Fig. 12")

# ===== SLIDE 26: CONCLUSION =====
s = blank(prs); bg(s, WHITE)
title_line(s, "Conclusion", "What was achieved")
bullets(s, 0.7, 1.35, 12.0, 5.0, [
    ("Accurate day-ahead forecasts:", f"the proposed ensemble achieves an MAE of {fmt(proposed_mae)} kW and MAPE of {fmt(proposed_mape)}% on the 14-day test set, a substantial improvement over the SARIMA baseline."),
    ("Seasonal backbone preserved:", f"the weekly anchor + Fourier structure retains an interpretable seasonal foundation; LightGBM corrects its residual errors."),
    ("Calibrated uncertainty:", f"split-conformal 95% intervals achieve {fmt(proposed_coverage)}% empirical coverage on the test set, supporting operational use."),
    ("Reproducible pipeline:", "the full workflow, figures and tables are reproducible from the project outputs and the figures analysed in the EDA and results sections."),
    ("Limitations:", "city-scale single-city scope; performance depends on feature quality and the weekly anchor; coverage can be tightened with larger calibration sets."),
], size=12.5, gap=7)
footer(s, "Conclusion")

# ===== SLIDE 27: FUTURE WORK =====
s = blank(prs); bg(s, WHITE)
title_line(s, "Future Work", "Where this can go next")
bullets(s, 0.7, 1.35, 12.0, 5.0, [
    ("Broader geographies:", "extend the pooled ensemble approach to additional Moroccan cities and compare cross-city transfer behaviour."),
    ("Tighter intervals:", "increase calibration-set size and explore adaptive conformal methods to tighten intervals without losing coverage."),
    ("Richer weather inputs:", "integrate higher-quality, localised weather forecasts and test sensitivity to weather-proxy quality."),
    ("Multi-horizon ensembles:", "explore horizon-specific models and hierarchical pooling to better handle the later-horizon degradation seen in MAE."),
    ("Online/rolling updates:", "evaluate rolling retraining and updating strategies for sustained accuracy in production-like settings."),
], size=12.5, gap=7)
footer(s, "Future")

# ===== SLIDE 28: THANK YOU =====
s = blank(prs); bg(s, NAVY)
shp = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.28), prs.slide_height)
shp.fill.solid(); shp.fill.fore_color.rgb = STEEL; shp.line.fill.background()
box = tb(s, 1.2, 2.2, 10.8, 1.4); tf = box.text_frame
ap(tf, "Thank You", 40, True, WHITE, first=True)
ap(tf, "Questions & Discussion", 18, color=LIGHT, sa=10)
box2 = tb(s, 1.2, 3.9, 10.8, 1.4)
ap(box2.text_frame, "B. M. S. College of Engineering  |  Dept. of Machine Learning  |  7th Semester, Section C", 12, color=LGREY, first=True, sa=2)
ap(box2.text_frame, "Smart City / Energy  -  SDG 7: Affordable and Clean Energy", 11, italic=True, color=LGREY)
footer(s, "Thank you")

print(f"Presentation written: {OUT}")
prs.save(str(OUT))
print(f"Slides: {len(prs.slides)}")
