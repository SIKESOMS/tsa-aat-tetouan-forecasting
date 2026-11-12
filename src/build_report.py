"""Build the AAT report .docx from the template structure, filling every section.

The output is written to report/TSA_AAT_Report.docx. Student identity fields are left
as clearly-marked placeholders for the student to fill in.
"""

from __future__ import annotations

import json
from pathlib import Path

from docx import Document
from docx.shared import Pt, Inches, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn, nsmap
from docx.oxml import OxmlElement

from .config import FIG_DIR, TABLE_DIR
from .lit_review import LITERATURE, table_rows
from .text_content import (
    ABSTRACT,
    BASELINE,
    CONCLUSION,
    DATASET,
    EVALUATION,
    INTRODUCTION,
    LITERATURE_GAP,
    LITERATURE_INTRO,
    PROPOSED,
    PROPOSED_APPROACH_BRIEF,
    REFERENCES,
    TEAM_CONTRIBUTION_PLACEHOLDER,
)

FIG_DIR_ROOT = FIG_DIR.parent.parent  # project root
REPORT_DIR = Path(__file__).resolve().parents[1] / "report"
REPORT_DIR.mkdir(exist_ok=True)

STEALTH_GRAY = RGBColor(0x60, 0x60, 0x60)


def _sha(text: str) -> int:
    h = 0
    for c in text:
        h = (h * 31 + ord(c)) % (2**31)
    return h


def _placeholder(paragraph, text: str) -> None:
    """Append a visibly-marked placeholder run."""
    run = paragraph.add_run(text)
    run.italic = True
    run.font.color.rgb = STEALTH_GRAY
    _set_run_standard(run, size_pt=12, italic=True)


def _heading(doc, text: str, level: int = 1, size: int = 14) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(size)
    if level == 1:
        run.font.color.rgb = RGBColor(0x1F, 0x3B, 0x73)
    p.space_before = Pt(10)
    p.space_after = Pt(4)
    return p


def _set_run_standard(run, bold=None, italic=None, color=None, size_pt=None):
    """Apply standard Times New Roman font to a run (size optional)."""
    _set_run_font(run, bold=bold, italic=italic, color=color, size_pt=size_pt)


def _para(doc, text: str, bold_lead: str | None = None) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if bold_lead:
        r = p.add_run(bold_lead)
        r.bold = True
        _set_run_standard(r, size_pt=12)
    r = p.add_run(text)
    _set_run_standard(r, size_pt=12)
    return p


def _numbered(doc, n: str, text: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(f"{n} ")
    r.bold = True
    _set_run_standard(r, size_pt=12)
    r2 = p.add_run(text)
    _set_run_standard(r2, size_pt=12)
    return p


def _add_figure(doc, rel_path: str, caption: str, width_inches: float = 6.2) -> None:
    path = FIG_DIR_ROOT / rel_path
    if not path.exists():
        para = doc.add_paragraph()
        r = para.add_run(f"[Figure missing: {rel_path}]")
        _set_run_standard(r, italic=True, size_pt=12)
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(str(path), width=Inches(width_inches))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cr = cap.add_run(caption)
    cr.italic = True
    _set_run_standard(cr, size_pt=10)
    cr.font.color.rgb = RGBColor(0x40, 0x40, 0x40)


def _shade_cell(cell, hex_color: str) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def _set_cell_text(cell, text: str, bold: bool = False, size: int = 9, color=None) -> None:
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = p.add_run(text)
    r.bold = bold
    _set_run_standard(r, size_pt=size)
    if color:
        r.font.color.rgb = color


def _set_col_widths(table, widths_inches):
    table.autofit = False
    for row in table.rows:
        for i, w in enumerate(widths_inches):
            if i < len(row.cells):
                row.cells[i].width = Inches(w)

def _link_display_text(url: str) -> str:
    """Return a clean display string for a URL/DOI (e.g. hide the https://doi.org/ prefix)."""
    s = url.strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "http://dx.doi.org/"):
        if s.lower().startswith(prefix):
            return s[len(prefix):]
    return s


def _add_hyperlink(paragraph, url: str, text: str, size_pt: int = 9,
                   bold: bool = False, color=None) -> None:
    """Insert a clickable hyperlink (w:hyperlink with an external relationship) into a paragraph."""
    part = paragraph.part
    r_id = part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
                          is_external=True)

    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)

    new_run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")

    # Font
    rFonts = OxmlElement("w:rFonts")
    rFonts.set(qn("w:ascii"), _FONT_NAME)
    rFonts.set(qn("w:hAnsi"), _FONT_NAME)
    rFonts.set(qn("w:cs"), _FONT_NAME)
    rFonts.set(qn("w:eastAsia"), _FONT_NAME)
    rPr.append(rFonts)

    # Size
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), str(size_pt * 2))
    rPr.append(sz)
    szCs = OxmlElement("w:szCs")
    szCs.set(qn("w:val"), str(size_pt * 2))
    rPr.append(szCs)

    if bold:
        b = OxmlElement("w:b")
        rPr.append(b)

    if color is not None:
        color_el = OxmlElement("w:color")
        color_el.set(qn("w:val"), str(color))
        rPr.append(color_el)
    else:
        # Typical hyperlink blue, underlined look
        color_el = OxmlElement("w:color")
        color_el.set(qn("w:val"), "1155CC")
        rPr.append(color_el)
        u = OxmlElement("w:u")
        u.set(qn("w:val"), "single")
        rPr.append(u)

    new_run.append(rPr)

    t = OxmlElement("w:t")
    t.set(qn("xml:space"), "preserve")
    t.text = text
    new_run.append(t)

    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)


def _set_cell_hyperlink(cell, url: str, text: str, size_pt: int = 8) -> None:
    """Put a clickable hyperlink as the sole content of a table cell."""
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _add_hyperlink(p, url, text, size_pt=size_pt, color="1155CC")


# ------------------------------------------------------------------
#  Build
# ------------------------------------------------------------------

def build() -> Path:
    results_path = TABLE_DIR / "run_results.json"
    results = {}
    if results_path.exists():
        results = json.loads(results_path.read_text(encoding="utf-8"))

    b = results.get("baseline", {})
    p = results.get("proposed", {})
    comp = results.get("comparison", {})
    peak = results.get("peak_error", {})
    figs = results.get("figures", {})
    meta = p.get("meta", {})

    doc = Document()
    _apply_standard_format(doc)

    # ============ COVER PAGE ============
    _cover(doc)
    doc.add_page_break()

    # ============ TITLE BLOCK (as per template header) ============
    _title_block(doc)
    doc.add_page_break()

    # ============ VALUATION REPORT (faculty page) ============
    _valuation_report(doc)
    doc.add_page_break()

    # ============ TABLE OF CONTENTS (manual) ============
    _toc(doc)
    doc.add_page_break()

    # ============ 1. ABSTRACT ============
    _heading(doc, "1. ABSTRACT", level=1, size=14)
    _para(doc, ABSTRACT.strip())

    # ============ 2. INTRODUCTION ============
    _heading(doc, "2. INTRODUCTION AND PROBLEM IDENTIFICATION", level=1, size=14)
    _heading(doc, "2.1 Application Domain", level=2, size=12)
    _para(doc, INTRODUCTION["2.1"])
    _heading(doc, "2.2 Problem Statement", level=2, size=12)
    _para(doc, INTRODUCTION["2.2"])
    _heading(doc, "2.3 Need for Forecasting", level=2, size=12)
    _para(doc, INTRODUCTION["2.3"])
    _heading(doc, "2.4 Objectives", level=2, size=12)
    for obj in [
        "Select a smart-city application domain and a suitable real-world time-series dataset for electricity load forecasting.",
        "Carry out a literature review of at least five relevant research papers and identify a specific research gap.",
        "Prepare and explore the dataset through preprocessing and exploratory data analysis (EDA).",
        "Develop a baseline seasonal time-series model (SARIMA) appropriate to the data.",
        "Improve the model by addressing the identified gap with a multi-seasonal ensemble and conformal prediction intervals.",
        "Compare the baseline and proposed models using appropriate evaluation measures on a held-out test period.",
        "Interpret and present the methodology, results and conclusions in a structured report.",
    ]:
        _numbered(doc, "•", obj)

    _heading(doc, "2.5 Scope of the Study", level=2, size=12)
    _para(doc, INTRODUCTION["2.5"])

    # ============ 3. LITERATURE REVIEW ============
    _heading(doc, "3. LITERATURE REVIEW AND RESEARCH GAP", level=1, size=14)
    _para(doc, LITERATURE_INTRO)

    _heading(doc, "3.1 Review of Existing Research", level=2, size=12)
    _add_lit_table(doc)

    _heading(doc, "3.2 Research Gap", level=2, size=12)
    _para(doc, LITERATURE_GAP.strip())

    _heading(doc, "3.3 Proposed Approach", level=2, size=12)
    _para(doc, PROPOSED_APPROACH_BRIEF.strip())

    # ============ 4. DATASET ============
    _heading(doc, "4. DATASET DESCRIPTION AND EXPLORATORY DATA ANALYSIS", level=1, size=14)
    _heading(doc, "4.1 Dataset Source", level=2, size=12)
    _para(doc, DATASET["4.1"])
    _heading(doc, "4.2 Variables and Data Description", level=2, size=12)
    _para(doc, DATASET["4.2"])

    # Table 1: dataset summary
    if results:
        _add_dataset_summary_table(doc, results)
    _heading(doc, "4.3 Data Preparation", level=2, size=12)
    _para(doc, DATASET["4.3"])
    _heading(doc, "4.4 Exploratory Data Analysis", level=2, size=12)
    _para(doc, DATASET["4.4"])

    # EDA figures
    _add_figure(doc, figs.get("full_series", "outputs/figures/fig01_full_series.png"),
                "Figure 1: City-level total load (MW) over 2017 with a 7-day rolling mean.")
    _add_figure(doc, figs.get("two_weeks", "outputs/figures/fig02_two_weeks.png"),
                "Figure 2: Two-week zoomed view showing the daily cycle and weekend dip.")
    _add_figure(doc, figs.get("daily_profile", "outputs/figures/fig03_daily_profile.png"),
                "Figure 3: Average hourly load profile — weekday vs weekend.")
    _add_figure(doc, figs.get("monthly_box", "outputs/figures/fig04_monthly_box.png"),
                "Figure 4: Monthly load distribution (boxplot by month).")
    _add_figure(doc, figs.get("stl", "outputs/figures/fig05_stl.png"),
                "Figure 5: STL decomposition of load into trend, seasonal and residual components.")
    _add_figure(doc, figs.get("acf_pacf", "outputs/figures/fig06_acf_pacf.png"),
                "Figure 6: Autocorrelation (ACF) and partial autocorrelation (PACF) functions.")
    _add_figure(doc, figs.get("correlation", "outputs/figures/fig07_correlation.png"),
                "Figure 7: Correlation heatmap between load and weather variables.")
    _add_figure(doc, figs.get("zone_profiles", "outputs/figures/fig08_zone_profiles.png"),
                "Figure 8: Hourly load profile by distribution zone (stacked over 24 h).")

    # ============ 5. BASELINE ============
    _heading(doc, "5. BASELINE FORECASTING MODEL", level=1, size=14)
    _heading(doc, "5.1 Model Selection", level=2, size=12)
    _para(doc, BASELINE["5.1"])
    _heading(doc, "5.2 Model Methodology", level=2, size=12)
    _para(doc, BASELINE["5.2"])
    _heading(doc, "5.3 Implementation", level=2, size=12)
    _para(doc, BASELINE["5.3"])

    if figs.get("forecast_comparison"):
        _add_figure(doc, figs["forecast_comparison"],
                    "Figure 9: Day-ahead forecast comparison — baseline SARIMA vs proposed ensemble vs actual (final 14 days).")
    if results:
        _add_baseline_results_table(doc, b)

    # ============ 6. PROPOSED ============
    _heading(doc, "6. PROPOSED MODEL AND ENHANCEMENT", level=1, size=14)
    _heading(doc, "6.1 Motivation for Improvement", level=2, size=12)
    _para(doc, PROPOSED["6.1"])
    _heading(doc, "6.2 Proposed Enhancement", level=2, size=12)
    _para(doc, PROPOSED["6.2"])
    _heading(doc, "6.3 Methodology and Implementation", level=2, size=12)
    _para(doc, PROPOSED["6.3"])
    _heading(doc, "6.4 Expected Advantage", level=2, size=12)
    _para(doc, PROPOSED["6.4"])
    _heading(doc, "6.5 Proposed Model Results", level=2, size=12)
    _para(doc, PROPOSED["6.5"])

    if figs.get("interval_coverage"):
        _add_figure(doc, figs["interval_coverage"],
                    "Figure 10: Proposed model — 95% prediction interval coverage (conformal) over the test period.")
    if figs.get("error_distribution"):
        _add_figure(doc, figs["error_distribution"],
                    "Figure 11: Error distribution and absolute-error boxplot — baseline vs proposed (test set).")
    if figs.get("per_horizon_mae"):
        _add_figure(doc, figs["per_horizon_mae"],
                    "Figure 12: Mean absolute error by forecast horizon (24-hour ahead, rolling origin).")
    if results:
        _add_proposed_results_table(doc, p)
        _add_per_horizon_table(doc, p)
        _add_peak_table(doc, peak)

    # ============ 7. EVALUATION ============
    _heading(doc, "7. PERFORMANCE EVALUATION AND COMPARISON", level=1, size=14)
    _heading(doc, "7.1 Evaluation Measures", level=2, size=12)
    _para(doc, EVALUATION["7.1"])
    _heading(doc, "7.2 Comparative Results", level=2, size=12)
    _para(doc, EVALUATION["7.2"])
    if results:
        _add_comparison_table(doc, comp)
        _add_interval_table(doc, b, p)
    _heading(doc, "7.3 Interpretation of Results", level=2, size=12)
    _para(doc, EVALUATION["7.3"])

    # ============ 8. CONCLUSION ============
    _heading(doc, "8. CONCLUSION AND FUTURE SCOPE", level=1, size=14)
    _heading(doc, "8.1 Summary, Findings and Implications", level=2, size=12)
    _para(doc, CONCLUSION["8.1"])
    _heading(doc, "8.2 Future Scope", level=2, size=12)
    _para(doc, CONCLUSION["8.2"])
    _heading(doc, "8.3 SDG Addressed", level=2, size=12)
    _para(doc, CONCLUSION["8.3"])

    # ============ 9. REFERENCES ============
    _heading(doc, "9. REFERENCES", level=1, size=14)
    for i, ref in enumerate(REFERENCES, 1):
        _numbered(doc, f"[{i}]", ref)

    # ============ 10. TEAM CONTRIBUTION ============
    _heading(doc, "10. TEAM CONTRIBUTION", level=1, size=14)
    _para(doc, TEAM_CONTRIBUTION_PLACEHOLDER)

    out = REPORT_DIR / "TSA_AAT_Report.docx"
    _finalize_standard_format(doc)
    doc.save(str(out))
    return out


# ------------------------------------------------------------------
#  Cover / header helpers
# ------------------------------------------------------------------


def _cover(doc: Document) -> None:
    """Cover page matching the standard template structure (Times New Roman).

    Sizes follow the template's cover-page hierarchy: college name ~16pt, dept
    ~13–16pt, programme/year ~11–14pt, course code 12pt bold, lab title 12–13pt,
    report title 12pt bold, domain/SDG lines 12pt bold, team block 12pt.
    """
    NAVY = RGBColor(0x1F, 0x37, 0x62)  # template's Heading1 title colour (1F3762)

    # ---- College name (Heading1-level, navy, bold, ~16pt) ----
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("B. M. S. COLLEGE OF ENGINEERING")
    _set_run_standard(r, bold=True, size_pt=16, color=NAVY)

    # ---- Autonomous institute line (italic, ~10pt per template) ----
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Autonomous Institute, Affiliated to VTU, Belagavi")
    _set_run_standard(r, italic=True, size_pt=10)

    doc.add_paragraph()  # spacer

    # ---- Department name (Heading1-level, navy, bold, ~16pt) ----
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("DEPARTMENT OF MACHINE LEARNING")
    _set_run_standard(r, bold=True, size_pt=16, color=NAVY)

    doc.add_paragraph()

    # ---- Programme / academic year (~14pt bold, centred) ----
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Program: B.E. in Artificial Intelligence and Machine Learning")
    _set_run_standard(r, bold=True, size_pt=12, color=NAVY)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Academic Year: 2026–27, Session: July 2026 – December 2026")
    _set_run_standard(r, bold=True, size_pt=12, color=NAVY)

    doc.add_paragraph()

    # ---- Course code (12pt bold) ----
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Time Series Analysis (24AM7PCTSA)")
    _set_run_standard(r, bold=True, size_pt=12)

    doc.add_paragraph()

    # ---- Lab title (13pt bold) ----
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("LAB AAT — DOMAIN-BASED TIME SERIES FORECASTING")
    _set_run_standard(r, bold=True, size_pt=13)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("AAT Report")
    _set_run_standard(r, bold=True, size_pt=12)

    doc.add_paragraph()

    # ---- Project title (12pt bold, two lines) ----
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Title: Day-Ahead City-Level Electricity Load Forecasting Using a")
    _set_run_standard(r, bold=True, size_pt=12)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Multi-Seasonal Ensemble with Conformal Prediction Intervals")
    _set_run_standard(r, bold=True, size_pt=12)

    doc.add_paragraph()

    # ---- Domain / SDG (12pt bold) ----
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Application Domain: Smart City / Energy")
    _set_run_standard(r, bold=True, size_pt=12)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("SDG addressed: SDG 7 — Affordable and Clean Energy")
    _set_run_standard(r, bold=True, size_pt=12)

    doc.add_paragraph()
    doc.add_paragraph()

    # ---- Submitted-by block (12pt, left aligned) ----
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = p.add_run("Submitted by")
    _set_run_standard(r, bold=True, size_pt=12)

    for line in [
        "Student Name: Roshan",
        "USN: 1BM23AI154",
        "Semester & Section: 7th Semester, Section C",
        "Student Signature: ________________ (to be affixed later)",
    ]:
        p = doc.add_paragraph()
        r = p.add_run(line)
        _set_run_standard(r, size_pt=12)

    doc.add_paragraph()

    # ---- Team members table heading ----
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = p.add_run("TEAM MEMBERS (3–4 students)")
    _set_run_standard(r, bold=True, size_pt=12)

    team = [
        ("Roshan", "1BM23AI154"),
        ("Roshanth.V", "1BM23AI155"),
        ("SS Gokula", "1BM23AI158"),
        ("Somanath", "1BM23AI187"),
    ]
    for name, usn in team:
        p = doc.add_paragraph()
        r = p.add_run(f"{name} ({usn})")
        _set_run_standard(r, size_pt=12)


def _title_block(doc: Document) -> None:
    pass  # content already on cover page; faculty page follows


def _valuation_report(doc: Document) -> None:
    _heading(doc, "VALUATION REPORT", level=1, size=14)
    _para(doc, "(To be filled by the faculty in-charge after evaluation.)")
    _placeholder(doc.add_paragraph(), "Score: ______ / 15")
    _placeholder(doc.add_paragraph(), "Faculty In-charge: ____________________")
    _placeholder(doc.add_paragraph(), "Comments: ______________________________________________")
    _placeholder(doc.add_paragraph(), "Faculty Signature with date: ____________________")


def _toc(doc: Document) -> None:
    _heading(doc, "TABLE OF CONTENTS", level=1, size=14)
    entries = [
        ("1.", "ABSTRACT", "Abstract"),
        ("2.", "INTRODUCTION AND PROBLEM IDENTIFICATION", "2.1 Application Domain\n2.2 Problem Statement\n2.3 Need for Forecasting\n2.4 Objectives\n2.5 Scope of the Study"),
        ("3.", "LITERATURE REVIEW AND RESEARCH GAP", "3.1 Review of Existing Research (Table)\n3.2 Research Gap\n3.3 Proposed Approach"),
        ("4.", "DATASET DESCRIPTION AND EXPLORATORY DATA ANALYSIS", "4.1 Dataset Source\n4.2 Variables and Data Description\n4.3 Data Preparation\n4.4 Exploratory Data Analysis"),
        ("5.", "BASELINE FORECASTING MODEL", "5.1 Model Selection\n5.2 Model Methodology\n5.3 Implementation\n5.4 Baseline Results"),
        ("6.", "PROPOSED MODEL AND ENHANCEMENT", "6.1 Motivation for Improvement\n6.2 Proposed Enhancement\n6.3 Methodology and Implementation\n6.4 Expected Advantage\n6.5 Proposed Model Results"),
        ("7.", "PERFORMANCE EVALUATION AND COMPARISON", "7.1 Evaluation Measures\n7.2 Comparative Results\n7.3 Interpretation of Results"),
        ("8.", "CONCLUSION AND FUTURE SCOPE", "8.1 Summary, Findings and Implications\n8.2 Future Scope\n8.3 SDG Addressed"),
        ("9.", "REFERENCES", ""),
        ("10.", "TEAM CONTRIBUTION", ""),
    ]
    for num, title, sub in entries:
        p = doc.add_paragraph()
        r = p.add_run(f"{num}  {title}")
        r.bold = True
        r.font.size = Pt(11)
        if sub:
            sp = doc.add_paragraph()
            sp.paragraph_format.left_indent = Inches(0.4)
            sr = sp.add_run(sub)
            sr.font.size = Pt(10)
            sr.font.color.rgb = RGBColor(0x40, 0x40, 0x40)


# ------------------------------------------------------------------
#  Tables
# ------------------------------------------------------------------


def _add_lit_table(doc: Document) -> None:
    rows = table_rows()
    headers = ["Paper", "Problem / Dataset", "Method Used", "Key Findings", "Limitations", "Link of the paper"]
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0].cells
    for i, h in enumerate(headers):
        _set_cell_text(hdr[i], h, bold=True, size=9, color=RGBColor(0xFF, 0xFF, 0xFF))
        _shade_cell(hdr[i], "1F3B73")
    for r in rows:
        cells = table.add_row().cells
        _set_cell_text(cells[0], r["paper"], bold=True, size=9)
        _set_cell_text(cells[1], r["problem_dataset"], size=9)
        _set_cell_text(cells[2], r["method"], size=9)
        _set_cell_text(cells[3], r["findings"], size=9)
        _set_cell_text(cells[4], r["limitations"], size=9)
        link = r.get("link", "")
        if link:
            _set_cell_hyperlink(cells[5], link, _link_display_text(link), size_pt=8)
        else:
            _set_cell_text(cells[5], link, size=8)
    _set_col_widths(table, [0.9, 2.2, 2.0, 2.0, 1.8, 1.35])
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cr = cap.add_run("Table 1: Summary of reviewed research papers (clickable links in the last column).")
    cr.italic = True
    cr.font.size = Pt(9)
    cr.font.color.rgb = RGBColor(0x40, 0x40, 0x40)


def _add_dataset_summary_table(doc: Document, results: dict) -> None:
    eda = results.get("baseline", {}).get("per_horizon_MAE_kw")  # not used; use eda_stats instead
    eda_path = TABLE_DIR / "eda_stats.json"
    eda = {}
    if eda_path.exists():
        eda = json.loads(eda_path.read_text(encoding="utf-8"))
    rows = [
        ("Observations (hourly)", eda.get("rows_hourly", "?")),
        ("Period covered", f"{eda.get('min_time','?')} → {eda.get('max_time','?')}"),
        ("Sampling interval (raw)", "10 minutes"),
        ("Sampling interval (modelled)", "1 hour"),
        ("Target variable", "City-level total load (kW) = Zone 1 + Zone 2 + Zone 3"),
        ("Mean load (kW)", round(eda.get("mean_kw", 0), 1)),
        ("Standard deviation (kW)", round(eda.get("std_kw", 0), 1)),
        ("Coefficient of variation", round(eda.get("cv", 0), 3)),
        ("Minimum load (kW)", round(eda.get("min_kw", 0), 1)),
        ("Maximum load (kW)", round(eda.get("max_kw", 0), 1)),
        ("Mean daily range (kW)", round(eda.get("mean_daily_range_kw", 0), 1)),
        ("Peak hour (weekday / weekend)", f"{int(eda.get('peak_hour_weekday',0))}:00 / {int(eda.get('peak_hour_weekend',0))}:00"),
        ("Trough hour", f"{int(eda.get('trough_hour',0))}:00"),
        ("Weather variables used", "Temperature, Humidity, Wind Speed (and diffuse flows for EDA)"),
        ("Missing hours interpolated", eda.get("missing_hours_interpolated", "?")),
        ("Negative load values", eda.get("negative_load_values", "?")),
    ]
    table = doc.add_table(rows=1, cols=2)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0].cells
    _set_cell_text(hdr[0], "Property", bold=True, size=10, color=RGBColor(0xFF, 0xFF, 0xFF))
    _set_cell_text(hdr[1], "Value", bold=True, size=10, color=RGBColor(0xFF, 0xFF, 0xFF))
    _shade_cell(hdr[0], "1F3B73")
    _shade_cell(hdr[1], "1F3B73")
    for k, v in rows:
        cells = table.add_row().cells
        _set_cell_text(cells[0], str(k), bold=True, size=10)
        _set_cell_text(cells[1], str(v), size=10)
    _set_col_widths(table, [2.6, 3.8])
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cr = cap.add_run("Table 2: Summary of the prepared hourly dataset (Tetouan City, 2017).")
    cr.italic = True
    cr.font.size = Pt(9)
    cr.font.color.rgb = RGBColor(0x40, 0x40, 0x40)


def _fmt(v):
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.2f}"
    return str(v)


def _add_baseline_results_table(doc: Document, b: dict) -> None:
    metrics = [
        ("MAE (kW)", b.get("MAE_kw")),
        ("RMSE (kW)", b.get("RMSE_kw")),
        ("MAPE (%)", b.get("MAPE_pct")),
        ("sMAPE (%)", b.get("sMAPE_pct")),
        ("MASE", b.get("MASE")),
        ("95% interval coverage (%)", b.get("PCR_coverage_95_pct")),
        ("Mean 95% interval width (kW)", b.get("PCR_width_mean_kw")),
    ]
    table = doc.add_table(rows=1, cols=2)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0].cells
    _set_cell_text(hdr[0], "Measure", bold=True, size=10, color=RGBColor(0xFF, 0xFF, 0xFF))
    _set_cell_text(hdr[1], f"Baseline SARIMA (1,1,1)(1,1,1,24)", bold=True, size=10, color=RGBColor(0xFF, 0xFF, 0xFF))
    _shade_cell(hdr[0], "1F3B73")
    _shade_cell(hdr[1], "1F3B73")
    for k, v in metrics:
        cells = table.add_row().cells
        _set_cell_text(cells[0], k, bold=True, size=10)
        _set_cell_text(cells[1], _fmt(v), size=10)
    _set_col_widths(table, [3.0, 3.4])
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cr = cap.add_run("Table 3: Baseline model performance on the held-out 14-day test period (day-ahead, rolling origin).")
    cr.italic = True
    cr.font.size = Pt(9)
    cr.font.color.rgb = RGBColor(0x40, 0x40, 0x40)


def _add_proposed_results_table(doc: Document, p: dict) -> None:
    metrics = [
        ("MAE (kW)", p.get("MAE_kw")),
        ("RMSE (kW)", p.get("RMSE_kw")),
        ("MAPE (%)", p.get("MAPE_pct")),
        ("sMAPE (%)", p.get("sMAPE_pct")),
        ("MASE", p.get("MASE")),
        ("Anchor MAE (kW)", p.get("anchor_MAE_kw")),
        ("Correction MAE (kW)", p.get("corr_MAE_kw")),
        ("95% interval coverage (%)", p.get("PCR_coverage_95_pct")),
        ("Mean 95% interval width (kW)", p.get("PCR_width_mean_kw")),
        ("Interval width relative to mean load (%)", p.get("PCR_width_rel_pct")),
        ("Winkler score (kW)", p.get("Winkler_95_kw")),
        ("Conformal quantile q", p.get("conformal_q")),
    ]
    table = doc.add_table(rows=1, cols=2)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0].cells
    _set_cell_text(hdr[0], "Measure", bold=True, size=10, color=RGBColor(0xFF, 0xFF, 0xFF))
    _set_cell_text(hdr[1], "Proposed Multi-Seasonal Ensemble", bold=True, size=10, color=RGBColor(0xFF, 0xFF, 0xFF))
    _shade_cell(hdr[0], "00798C")
    _shade_cell(hdr[1], "00798C")
    for k, v in metrics:
        cells = table.add_row().cells
        _set_cell_text(cells[0], k, bold=True, size=10)
        _set_cell_text(cells[1], _fmt(v), size=10)
    _set_col_widths(table, [3.0, 3.4])
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cr = cap.add_run("Table 4: Proposed model performance on the held-out 14-day test period (day-ahead, rolling origin).")
    cr.italic = True
    cr.font.size = Pt(9)
    cr.font.color.rgb = RGBColor(0x40, 0x40, 0x40)


def _add_comparison_table(doc: Document, comp: dict) -> None:
    rows = comp.get("point_forecast", [])
    if not rows:
        return
    table = doc.add_table(rows=1, cols=5)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0].cells
    for i, h in enumerate(["Metric", "Baseline SARIMA", "Proposed Ensemble", "Improvement", "Better"]):
        _set_cell_text(hdr[i], h, bold=True, size=9, color=RGBColor(0xFF, 0xFF, 0xFF))
        _shade_cell(hdr[i], "1F3B73")
    for r in rows:
        cells = table.add_row().cells
        _set_cell_text(cells[0], r["metric"], bold=True, size=9)
        _set_cell_text(cells[1], _fmt(r["baseline"]), size=9)
        _set_cell_text(cells[2], _fmt(r["proposed"]), size=9)
        _set_cell_text(cells[3], f"{_fmt(r['absolute_improvement'])} ({_fmt(r['relative_improvement_pct'])}%)", size=9)
        _set_cell_text(cells[4], r["better"], bold=True, size=9)
    _set_col_widths(table, [1.4, 1.3, 1.3, 1.5, 0.9])
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cr = cap.add_run("Table 5: Point-forecast comparison — baseline vs proposed (held-out 14-day test period, day-ahead, rolling origin). Lower is better.")
    cr.italic = True
    cr.font.size = Pt(9)
    cr.font.color.rgb = RGBColor(0x40, 0x40, 0x40)


def _add_interval_table(doc: Document, b: dict, p: dict) -> None:
    table = doc.add_table(rows=1, cols=3)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0].cells
    for i, h in enumerate(["Interval measure", "Baseline (Gaussian 95%)", "Proposed (conformal 95%)"]):
        _set_cell_text(hdr[i], h, bold=True, size=9, color=RGBColor(0xFF, 0xFF, 0xFF))
        _shade_cell(hdr[i], "1F3B73")
    rows = [
        ("Coverage (%)", b.get("PCR_coverage_95_pct"), p.get("PCR_coverage_95_pct")),
        ("Mean width (kW)", b.get("PCR_width_mean_kw"), p.get("PCR_width_mean_kw")),
        ("Width / mean load (%)", round((b.get("PCR_width_rel", 0) or 0) * 100, 2), p.get("PCR_width_rel_pct")),
        ("Winkler score (kW)", "—", p.get("Winkler_95_kw")),
    ]
    for label, bv, pv in rows:
        cells = table.add_row().cells
        _set_cell_text(cells[0], label, bold=True, size=9)
        _set_cell_text(cells[1], _fmt(bv), size=9)
        _set_cell_text(cells[2], _fmt(pv), size=9)
    _set_col_widths(table, [2.2, 2.0, 2.2])
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cr = cap.add_run("Table 6: Prediction-interval comparison — baseline Gaussian intervals vs proposed conformal intervals (95%).")
    cr.italic = True
    cr.font.size = Pt(9)
    cr.font.color.rgb = RGBColor(0x40, 0x40, 0x40)


def _add_per_horizon_table(doc: Document, p: dict) -> None:
    per_h = p.get("per_horizon_MAE_kw", {})
    anchor_h = p.get("per_horizon_anchor_MAE_kw", {})
    if not per_h:
        return
    table = doc.add_table(rows=1, cols=25)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0].cells
    _set_cell_text(hdr[0], "Model", bold=True, size=8, color=RGBColor(0xFF, 0xFF, 0xFF))
    _shade_cell(hdr[0], "1F3B73")
    for h in range(1, 25):
        _set_cell_text(hdr[h], f"h={h}", bold=True, size=8, color=RGBColor(0xFF, 0xFF, 0xFF))
        _shade_cell(hdr[h], "1F3B73")
    for label, series, color in [
        ("Proposed ensemble", per_h, "00798C"),
        ("Weekly anchor", anchor_h, "8d99ae"),
    ]:
        cells = table.add_row().cells
        _set_cell_text(cells[0], label, bold=True, size=8)
        for h in range(1, 25):
            _set_cell_text(cells[h], _fmt(series.get(str(h))), size=8)
    _set_col_widths(table, [1.3] + [0.22] * 24)
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cr = cap.add_run("Table 7: MAE (MW) by forecast horizon for the proposed ensemble and the weekly anchor, over the 14-day test period.")
    cr.italic = True
    cr.font.size = Pt(9)
    cr.font.color.rgb = RGBColor(0x40, 0x40, 0x40)


def _add_peak_table(doc: Document, peak: dict) -> None:
    if not peak:
        return
    table = doc.add_table(rows=1, cols=3)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0].cells
    for i, h in enumerate(["Measure", "Baseline SARIMA", "Proposed Ensemble"]):
        _set_cell_text(hdr[i], h, bold=True, size=9, color=RGBColor(0xFF, 0xFF, 0xFF))
        _shade_cell(hdr[i], "1F3B73")
    rows = [
        ("Peak threshold (kW)", peak.get("peak_threshold_kw"), peak.get("peak_threshold_kw")),
        ("Number of peak hours", peak.get("n_peak_hours"), peak.get("n_peak_hours")),
        ("MAE on peak hours (kW)", peak.get("baseline_MAE_peak_kw"), peak.get("proposed_MAE_peak_kw")),
        ("MAE off-peak hours (kW)", peak.get("baseline_MAE_offpeak_kw"), peak.get("proposed_MAE_offpeak_kw")),
        ("Peak share of mean load (%)", peak.get("peak_share_of_load_pct"), peak.get("peak_share_of_load_pct")),
    ]
    for label, bv, pv in rows:
        cells = table.add_row().cells
        _set_cell_text(cells[0], label, bold=True, size=9)
        _set_cell_text(cells[1], _fmt(bv), size=9)
        _set_cell_text(cells[2], _fmt(pv), size=9)
    _set_col_widths(table, [3.0, 1.7, 1.7])
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cr = cap.add_run(f"Table 8: Peak-hour analysis (top 20% of observed test load; threshold ≈ {peak.get('peak_threshold_kw'):,.0f} kW, {peak.get('n_peak_hours')} h).")
    cr.italic = True
    cr.font.size = Pt(9)
    cr.font.color.rgb = RGBColor(0x40, 0x40, 0x40)


# ------------------------------------------------------------------
#  Standard academic formatting (Times New Roman 12pt, A4, margins,
#  header, footer with page numbers, page borders).
# ------------------------------------------------------------------

# Standard format constants (matched to the template's docDefaults/styles).
# A4 page in twips (1/20 pt): 11906 x 16838 EMU? No — twips.
# Word uses twips for pgSz/pgMar: A4 = 11906 x 16838 twips.
# Margins in twips: 1 inch = 1440 twips, 1.25 inch = 1800 twips.
_A4_WIDTH_TWIPS = 11906
_A4_HEIGHT_TWIPS = 16838
_MARGIN_TOP_TWIPS = 1440      # 1.00 in
_MARGIN_BOTTOM_TWIPS = 1440   # 1.00 in
_MARGIN_LEFT_TWIPS = 1800     # 1.25 in
_MARGIN_RIGHT_TWIPS = 1800    # 1.25 in
_MARGIN_HEADER_TWIPS = 720    # 0.50 in
_MARGIN_FOOTER_TWIPS = 720    # 0.50 in

_FONT_NAME = "Times New Roman"
_FONT_SIZE_PT = 12

# Header text (compact, on body pages only).
_HEADER_TEXT = "B. M. S. College of Engineering  |  Dept. of Machine Learning  |  24AM7PCTSA"
# Footer text.
_FOOTER_LEFT = "BMSCE  |  24AM7PCTSA  |  Lab AAT"
_FOOTER_RIGHT = "Page "


def _set_run_font(run, name=_FONT_NAME, size_pt=_FONT_SIZE_PT, bold=None, italic=None, color=None):
    """Set a run's font to the standard Times New Roman 12pt (and optional styling)."""
    run.font.name = name
    run.font.size = Pt(size_pt)
    # Ensure CS (complex script) and East Asian fonts also map to the same font.
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:ascii"), name)
    rFonts.set(qn("w:hAnsi"), name)
    rFonts.set(qn("w:cs"), name)
    rFonts.set(qn("w:eastAsia"), name)
    if bold is not None:
        run.font.bold = bold
    if italic is not None:
        run.font.italic = italic
    if color is not None:
        run.font.color.rgb = color


def _set_paragraph_font(paragraph, name=_FONT_NAME, size_pt=_FONT_SIZE_PT):
    """Apply standard font to every run in a paragraph (backward-compatible)."""
    for r in paragraph.runs:
        _set_run_font(r, name=name, size_pt=size_pt)


def _apply_standard_format(doc: Document) -> None:
    """Set the Normal style and document defaults to Times New Roman 12pt.

    Also sets the page size to A4 and standard margins on the first (and only)
    section. Header/footer and page borders are added in _finalize_standard_format
    after the body content is built (so we can use titlePg to keep the cover page clean).
    """
    # --- Normal style: Times New Roman 12pt ---
    style = doc.styles["Normal"]
    style.font.name = _FONT_NAME
    style.font.size = Pt(_FONT_SIZE_PT)
    rPr = style.element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:ascii"), _FONT_NAME)
    rFonts.set(qn("w:hAnsi"), _FONT_NAME)
    rFonts.set(qn("w:cs"), _FONT_NAME)
    rFonts.set(qn("w:eastAsia"), _FONT_NAME)
    sz = rPr.find(qn("w:sz"))
    if sz is None:
        sz = OxmlElement("w:sz")
        rPr.append(sz)
    sz.set(qn("w:val"), str(_FONT_SIZE_PT * 2))  # half-points
    szCs = rPr.find(qn("w:szCs"))
    if szCs is None:
        szCs = OxmlElement("w:szCs")
        rPr.append(szCs)
    szCs.set(qn("w:val"), str(_FONT_SIZE_PT * 2))

    # --- Document defaults (docDefaults/rPrDefault/rPr) ---
    styles_el = doc.styles.element
    docDefaults = styles_el.find(qn("w:docDefaults"))
    if docDefaults is not None:
        rPrDefault = docDefaults.find(qn("w:rPrDefault"))
        if rPrDefault is not None:
            rPrD = rPrDefault.find(qn("w:rPr"))
            if rPrD is not None:
                rFontsD = rPrD.find(qn("w:rFonts"))
                if rFontsD is None:
                    rFontsD = OxmlElement("w:rFonts")
                    rPrD.insert(0, rFontsD)
                rFontsD.set(qn("w:ascii"), _FONT_NAME)
                rFontsD.set(qn("w:hAnsi"), _FONT_NAME)
                rFontsD.set(qn("w:cs"), _FONT_NAME)
                rFontsD.set(qn("w:eastAsia"), _FONT_NAME)
                szD = rPrD.find(qn("w:sz"))
                if szD is None:
                    szD = OxmlElement("w:sz")
                    rPrD.append(szD)
                szD.set(qn("w:val"), str(_FONT_SIZE_PT * 2))
                szCsD = rPrD.find(qn("w:szCs"))
                if szCsD is None:
                    szCsD = OxmlElement("w:szCs")
                    rPrD.append(szCsD)
                szCsD.set(qn("w:val"), str(_FONT_SIZE_PT * 2))

    # --- Page size A4 + margins on the first section ---
    section = doc.sections[0]
    section.page_width = Emu(_A4_WIDTH_TWIPS * 635)   # twips -> EMU (1 twip = 635 EMU)
    section.page_height = Emu(_A4_HEIGHT_TWIPS * 635)
    section.top_margin = Emu(_MARGIN_TOP_TWIPS * 635)
    section.bottom_margin = Emu(_MARGIN_BOTTOM_TWIPS * 635)
    section.left_margin = Emu(_MARGIN_LEFT_TWIPS * 635)
    section.right_margin = Emu(_MARGIN_RIGHT_TWIPS * 635)
    section.header_distance = Emu(_MARGIN_HEADER_TWIPS * 635)
    section.footer_distance = Emu(_MARGIN_FOOTER_TWIPS * 635)
    section.different_first_page_header_footer = True  # cover page has no header/footer


def _finalize_standard_format(doc: Document) -> None:
    """Add header, footer (with page number), and page borders to the document.

    Must be called after all body content is added. Uses titlePg so the cover
    page (first page) does not show header/footer.
    """
    section = doc.sections[0]

    # --- Header (default header, shown from page 2 onward) ---
    header = section.header
    header.is_linked_to_previous = False
    # Clear any existing content.
    for p in list(header.paragraphs):
        p.clear()
    hp = header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    hr = hp.add_run(_HEADER_TEXT)
    hr.font.name = _FONT_NAME
    hr.font.size = Pt(9)
    hr.font.color.rgb = RGBColor(0x40, 0x40, 0x40)
    # Ensure cs/eastAsia fonts too.
    rPr = hr._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:ascii"), _FONT_NAME)
    rFonts.set(qn("w:hAnsi"), _FONT_NAME)
    rFonts.set(qn("w:cs"), _FONT_NAME)
    rFonts.set(qn("w:eastAsia"), _FONT_NAME)
    # Bottom border on the header paragraph (a thin rule under the header text).
    pPr = hp._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "808080")
    pBdr.append(bottom)
    pPr.append(pBdr)

    # --- Footer (default footer, shown from page 2 onward) ---
    footer = section.footer
    footer.is_linked_to_previous = False
    for p in list(footer.paragraphs):
        p.clear()
    fp = footer.paragraphs[0]
    # Use tab stops: left text, right page number.
    fp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    # Add a right tab stop at the right margin.
    pPr = fp._p.get_or_add_pPr()
    tabs = OxmlElement("w:tabs")
    tab = OxmlElement("w:tab")
    tab.set(qn("w:val"), "right")
    tab.set(qn("w:pos"), str(int(section.page_width - section.left_margin - section.right_margin)))
    tabs.append(tab)
    pPr.append(tabs)

    # Left footer text.
    fr_left = fp.add_run(_FOOTER_LEFT)
    fr_left.font.name = _FONT_NAME
    fr_left.font.size = Pt(9)
    fr_left.font.color.rgb = RGBColor(0x40, 0x40, 0x40)
    rPr = fr_left._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:ascii"), _FONT_NAME)
    rFonts.set(qn("w:hAnsi"), _FONT_NAME)
    rFonts.set(qn("w:cs"), _FONT_NAME)
    rFonts.set(qn("w:eastAsia"), _FONT_NAME)

    # Tab to right.
    fp.add_run("\t")

    # Page number field: "Page X of Y".
    def _add_page_field(paragraph, before, after):
        run = paragraph.add_run()
        run.font.name = _FONT_NAME
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0x40, 0x40, 0x40)
        rPr = run._element.get_or_add_rPr()
        rFonts = rPr.find(qn("w:rFonts"))
        if rFonts is None:
            rFonts = OxmlElement("w:rFonts")
            rPr.insert(0, rFonts)
        rFonts.set(qn("w:ascii"), _FONT_NAME)
        rFonts.set(qn("w:hAnsi"), _FONT_NAME)
        rFonts.set(qn("w:cs"), _FONT_NAME)
        rFonts.set(qn("w:eastAsia"), _FONT_NAME)
        fldBegin = OxmlElement("w:fldChar")
        fldBegin.set(qn("w:fldCharType"), "begin")
        run._element.append(fldBegin)
        instr = OxmlElement("w:instrText")
        instr.set(qn("xml:space"), "preserve")
        instr.text = before
        run._element.append(instr)
        fldEnd = OxmlElement("w:fldChar")
        fldEnd.set(qn("w:fldCharType"), "end")
        run._element.append(fldEnd)

    _add_page_field(fp, " PAGE ", "")
    fr_of = fp.add_run(" of ")
    fr_of.font.name = _FONT_NAME
    fr_of.font.size = Pt(9)
    fr_of.font.color.rgb = RGBColor(0x40, 0x40, 0x40)
    rPr = fr_of._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:ascii"), _FONT_NAME)
    rFonts.set(qn("w:hAnsi"), _FONT_NAME)
    rFonts.set(qn("w:cs"), _FONT_NAME)
    rFonts.set(qn("w:eastAsia"), _FONT_NAME)
    _add_page_field(fp, " NUMPAGES ", "")

    # Top border on the footer paragraph (a thin rule above the footer text).
    pPr = fp._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    top = OxmlElement("w:top")
    top.set(qn("w:val"), "single")
    top.set(qn("w:sz"), "6")
    top.set(qn("w:space"), "1")
    top.set(qn("w:color"), "808080")
    pBdr.append(top)
    pPr.append(pBdr)

    # --- Page borders (around every page) ---
    # Insert pgBorders into the sectPr of the first section.
    sectPr = section._sectPr
    pgBorders = sectPr.find(qn("w:pgBorders"))
    if pgBorders is None:
        pgBorders = OxmlElement("w:pgBorders")
        # pgBorders should come after pgNumType (if present) and before headerReference/footerReference.
        # Insert at a safe position: after pgSz/pgMar/pgNumType, before headerReference.
        insert_after = sectPr.find(qn("w:pgNumType"))
        if insert_after is not None:
            insert_after.addnext(pgBorders)
        else:
            pgSz = sectPr.find(qn("w:pgSz"))
            if pgSz is not None:
                pgSz.addnext(pgBorders)
            else:
                sectPr.insert(0, pgBorders)
    pgBorders.set(qn("w:offsetFrom"), "page")
    for edge in ("top", "left", "bottom", "right"):
        el = pgBorders.find(qn("w:" + edge))
        if el is None:
            el = OxmlElement("w:" + edge)
            pgBorders.append(el)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "24")
        el.set(qn("w:color"), "404040")


if __name__ == "__main__":
    out = build()
    print(f"Report written: {out}")
