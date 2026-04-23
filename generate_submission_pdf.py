"""
Generate Project-Documentation.pdf for BuildRight R2R Capstone Project
Bipin Kumar | Roll: 2306196 | IT | SAP Integration Developer
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
from reportlab.pdfgen import canvas as pdfcanvas
import os

# ── PAGE SETUP ──────────────────────────────────────────────
W, H = A4
MARGIN = 2.0 * cm
CONTENT_W = W - 2 * MARGIN

# ── COLORS ─────────────────────────────────────────────────
SAP_BLUE    = colors.HexColor("#1b3a5c")
SAP_ACCENT  = colors.HexColor("#0070f2")
SAP_GREEN   = colors.HexColor("#107e3e")
SAP_AMBER   = colors.HexColor("#e96500")
SAP_LIGHT   = colors.HexColor("#e8f3ff")
SAP_GRAY    = colors.HexColor("#f4f5f6")
SAP_BORDER  = colors.HexColor("#dde1e7")
TEXT_DARK   = colors.HexColor("#1d2d3e")
TEXT_MUTED  = colors.HexColor("#556b82")
WHITE       = colors.white
BLACK       = colors.black

# ── STYLES ─────────────────────────────────────────────────
def make_styles():
    s = getSampleStyleSheet()

    h1 = ParagraphStyle("H1", parent=s["Normal"],
        fontName="Helvetica-Bold", fontSize=15, leading=20,
        textColor=SAP_BLUE, spaceAfter=6, alignment=TA_LEFT)

    h2 = ParagraphStyle("H2", parent=s["Normal"],
        fontName="Helvetica-Bold", fontSize=14, leading=18,
        textColor=SAP_BLUE, spaceBefore=12, spaceAfter=4)

    h3 = ParagraphStyle("H3", parent=s["Normal"],
        fontName="Helvetica-Bold", fontSize=12, leading=16,
        textColor=SAP_BLUE, spaceBefore=8, spaceAfter=3)

    body = ParagraphStyle("Body", parent=s["Normal"],
        fontName="Helvetica", fontSize=12, leading=18,
        textColor=TEXT_DARK, spaceAfter=6, alignment=TA_JUSTIFY)

    bullet = ParagraphStyle("Bullet", parent=s["Normal"],
        fontName="Helvetica", fontSize=12, leading=17,
        textColor=TEXT_DARK, leftIndent=16, spaceAfter=3,
        bulletIndent=4)

    small = ParagraphStyle("Small", parent=s["Normal"],
        fontName="Helvetica", fontSize=11, leading=15,
        textColor=TEXT_MUTED, spaceAfter=3)

    caption = ParagraphStyle("Caption", parent=s["Normal"],
        fontName="Helvetica-Oblique", fontSize=10, leading=13,
        textColor=TEXT_MUTED, alignment=TA_CENTER, spaceAfter=4)

    mono = ParagraphStyle("Mono", parent=s["Normal"],
        fontName="Courier", fontSize=10, leading=14,
        textColor=TEXT_DARK, spaceAfter=3, leftIndent=8,
        backColor=SAP_GRAY)

    highlight = ParagraphStyle("Highlight", parent=s["Normal"],
        fontName="Helvetica-Bold", fontSize=12, leading=17,
        textColor=SAP_BLUE, spaceAfter=4, leftIndent=8)

    return dict(h1=h1, h2=h2, h3=h3, body=body, bullet=bullet,
                small=small, caption=caption, mono=mono, highlight=highlight, base=s)

ST = make_styles()


# ── PAGE CALLBACK ──────────────────────────────────────────
def draw_page(canvas, doc):
    canvas.saveState()
    page_num = doc.page

    # Header bar
    canvas.setFillColor(SAP_BLUE)
    canvas.rect(0, H - 1.4*cm, W, 1.4*cm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(MARGIN, H - 0.88*cm, "BuildRight Construction Pvt. Ltd.")
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(W - MARGIN, H - 0.88*cm, "SAP FI · Record-to-Report · Capstone Project FY 2026")

    # Accent line under header
    canvas.setFillColor(SAP_ACCENT)
    canvas.rect(0, H - 1.5*cm, W, 0.1*cm, fill=1, stroke=0)

    # Footer
    canvas.setFillColor(SAP_GRAY)
    canvas.rect(0, 0, W, 1.1*cm, fill=1, stroke=0)
    canvas.setStrokeColor(SAP_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(0, 1.1*cm, W, 1.1*cm)
    canvas.setFillColor(TEXT_MUTED)
    canvas.setFont("Helvetica", 8.5)
    canvas.drawString(MARGIN, 0.45*cm, "Bipin Kumar | Roll No: 2306196 | IT | SAP Integration Developer")
    canvas.setFont("Helvetica-Bold", 8.5)
    canvas.drawRightString(W - MARGIN, 0.45*cm, f"Page {page_num}")

    canvas.restoreState()


# ── HELPERS ────────────────────────────────────────────────
def hr(color=SAP_BORDER, thickness=0.5):
    return HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=6, spaceBefore=2)

def section_header(title, subtitle=""):
    items = [hr(SAP_ACCENT, 1.5), Paragraph(title, ST["h2"])]
    if subtitle:
        items.append(Paragraph(subtitle, ST["small"]))
    items.append(hr())
    return items

def info_table(rows, col_widths=None):
    if not col_widths:
        col_widths = [CONTENT_W * 0.35, CONTENT_W * 0.65]
    data = [[Paragraph(f"<b>{k}</b>", ST["small"]),
             Paragraph(str(v), ST["body"])] for k, v in rows]
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), SAP_LIGHT),
        ("TEXTCOLOR", (0,0), (0,-1), SAP_BLUE),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 11),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [WHITE, SAP_GRAY]),
        ("GRID", (0,0), (-1,-1), 0.3, SAP_BORDER),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    return t


def process_table(rows):
    header = [
        Paragraph("<b>Step</b>", ST["small"]),
        Paragraph("<b>Process</b>", ST["small"]),
        Paragraph("<b>SAP T-Code</b>", ST["small"]),
        Paragraph("<b>FI Impact</b>", ST["small"]),
    ]
    data = [header] + [
        [Paragraph(str(r[0]), ST["body"]),
         Paragraph(str(r[1]), ST["body"]),
         Paragraph(f"<b>{r[2]}</b>", ParagraphStyle("TCode", parent=ST["body"],
                   fontName="Courier-Bold", fontSize=11, textColor=SAP_ACCENT)),
         Paragraph(str(r[3]), ST["small"])]
        for r in rows
    ]
    cw = [CONTENT_W * 0.07, CONTENT_W * 0.30, CONTENT_W * 0.18, CONTENT_W * 0.45]
    t = Table(data, colWidths=cw)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), SAP_BLUE),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, SAP_GRAY]),
        ("GRID", (0,0), (-1,-1), 0.3, SAP_BORDER),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING", (0,0), (-1,-1), 7),
        ("RIGHTPADDING", (0,0), (-1,-1), 7),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN", (0,0), (0,-1), "CENTER"),
    ]))
    return t


def callout_box(title, body_text, color=SAP_LIGHT, border_color=SAP_ACCENT):
    data = [[
        Paragraph(f"<b>{title}</b>", ParagraphStyle("CBTitle", parent=ST["body"],
                  fontName="Helvetica-Bold", fontSize=11, textColor=SAP_BLUE)),
        Paragraph(body_text, ParagraphStyle("CBBody", parent=ST["body"],
                  fontSize=11, leading=16))
    ]]
    t = Table(data, colWidths=[CONTENT_W * 0.22, CONTENT_W * 0.78])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), color),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LINEBEFORE", (0,0), (0,-1), 3, border_color),
        ("BOX", (0,0), (-1,-1), 0.5, SAP_BORDER),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
    ]))
    return t


def fi_posting_table(rows):
    header = [
        Paragraph("<b>Transaction</b>", ST["small"]),
        Paragraph("<b>Debit Account</b>", ST["small"]),
        Paragraph("<b>Credit Account</b>", ST["small"]),
        Paragraph("<b>Amount (INR)</b>", ST["small"]),
    ]
    data = [header] + [
        [Paragraph(r[0], ST["small"]),
         Paragraph(r[1], ST["small"]),
         Paragraph(r[2], ST["small"]),
         Paragraph(r[3], ParagraphStyle("Amt", parent=ST["small"],
                   fontName="Courier-Bold", fontSize=10))]
        for r in rows
    ]
    cw = [CONTENT_W*0.20, CONTENT_W*0.30, CONTENT_W*0.30, CONTENT_W*0.20]
    t = Table(data, colWidths=cw)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), SAP_BLUE),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, SAP_GRAY]),
        ("GRID", (0,0), (-1,-1), 0.3, SAP_BORDER),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING", (0,0), (-1,-1), 7),
        ("RIGHTPADDING", (0,0), (-1,-1), 7),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN", (3,1), (3,-1), "RIGHT"),
    ]))
    return t


# ── BUILD DOCUMENT ─────────────────────────────────────────
def build_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=1.8*cm, bottomMargin=1.5*cm,
        title="BuildRight R2R — SAP FI Capstone Project",
        author="Bipin Kumar",
        subject="Record-to-Report Financial Close"
    )

    story = []

    # ══════════════════════════════════════════════════════
    # PAGE 1 — COVER / TITLE
    # ══════════════════════════════════════════════════════
    story.append(Spacer(1, 1.5*cm))

    # Cover block
    cover_data = [[
        Paragraph(
            "<b>SAP FI · Record-to-Report (R2R)</b><br/>"
            "Month-End &amp; Year-End Financial Close",
            ParagraphStyle("CoverTitle", parent=ST["base"]["Normal"],
                fontName="Helvetica-Bold", fontSize=22, leading=28,
                textColor=WHITE, alignment=TA_CENTER)
        )
    ]]
    cover_tbl = Table(cover_data, colWidths=[CONTENT_W])
    cover_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), SAP_BLUE),
        ("TOPPADDING", (0,0), (-1,-1), 28),
        ("BOTTOMPADDING", (0,0), (-1,-1), 28),
        ("LEFTPADDING", (0,0), (-1,-1), 20),
        ("RIGHTPADDING", (0,0), (-1,-1), 20),
        ("LINEBELOW", (0,0), (-1,-1), 4, SAP_ACCENT),
    ]))
    story.append(cover_tbl)
    story.append(Spacer(1, 0.5*cm))

    # Subtitle
    story.append(Paragraph(
        "Capstone Project Documentation — SAP Integration Developer Program",
        ParagraphStyle("Subtitle", parent=ST["base"]["Normal"],
            fontName="Helvetica", fontSize=13, textColor=TEXT_MUTED,
            alignment=TA_CENTER, spaceAfter=6)
    ))
    story.append(hr(SAP_BORDER))
    story.append(Spacer(1, 0.3*cm))

    # Student details
    story.append(info_table([
        ("Student Name", "Bipin Kumar"),
        ("Roll Number", "2306196"),
        ("Batch", "IT"),
        ("Program", "SAP Integration Developer"),
        ("Topic", "Record-to-Report (R2R) — Month-End / Year-End Financial Close"),
        ("Company Scenario", "BuildRight Construction Pvt. Ltd."),
        ("SAP Module", "Financial Accounting (FI)"),
        ("Submission Deadline", "April 21, 2026"),
    ]))
    story.append(Spacer(1, 0.6*cm))
    story.append(callout_box(
        "Project Summary",
        "This project implements a complete SAP FI Record-to-Report cycle using a custom-built "
        "web-based simulator. It covers all R2R stages from journal entry posting to period close, "
        "including depreciation, accruals, GL reconciliation, trial balance, and financial statement "
        "generation — all backed by a Python server with SQLite persistence."
    ))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════
    # PAGE 2 — INTRODUCTION & PROBLEM STATEMENT
    # ══════════════════════════════════════════════════════
    story += section_header("1. Introduction")
    story.append(Paragraph(
        "The Record-to-Report (R2R) process is a core financial management workflow in SAP Financial "
        "Accounting (FI). It encompasses all activities required to collect, process, and report "
        "financial data for a given accounting period — from initial journal entry posting through "
        "period-end close and publication of auditable financial statements.",
        ST["body"]
    ))
    story.append(Paragraph(
        "This project demonstrates the end-to-end R2R cycle for <b>BuildRight Construction Pvt. Ltd.</b>, "
        "a fictitious construction materials company operating under company code BR01 with fiscal "
        "year variant K4 (April to March). The implementation covers all major SAP FI R2R transactions "
        "and produces live financial statements, making the simulator suitable for both academic "
        "demonstration and interview reference.",
        ST["body"]
    ))

    story += section_header("2. Problem Statement")
    story.append(Paragraph(
        "Before implementing a structured R2R process in SAP, BuildRight Construction faced the "
        "following financial reporting challenges:", ST["body"]
    ))
    problems = [
        "Manual journal entries with no validation — errors remained undetected until audit",
        "No automated depreciation run — fixed asset values were often overstated",
        "Accruals posted inconsistently — period expenses were misstated",
        "GL reconciliation performed outside SAP — reconciliation gaps existed",
        "Trial balance required manual compilation — prone to arithmetic errors",
        "Period close had no structured checklist — postings sometimes occurred after close",
        "Financial statements took 7-10 days to produce — business decisions were delayed",
        "No audit trail for manual adjustments — compliance risk was high",
    ]
    for p in problems:
        story.append(Paragraph(f"• {p}", ST["bullet"]))

    story.append(Spacer(1, 0.4*cm))
    story.append(callout_box(
        "SAP Solution",
        "SAP FI R2R resolves these issues through structured transaction-based processing: "
        "FB50 enforces double-entry validation, AFAB automates depreciation, FBS1 manages accruals, "
        "FAGLF03 reconciles GL accounts, F.08 validates trial balance, and OB52 controls period close "
        "— eliminating all manual workarounds."
    ))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════
    # PAGE 3 — SCOPE & PROCESS STEPS
    # ══════════════════════════════════════════════════════
    story += section_header("3. Scope of Implementation")
    story.append(Paragraph(
        "The project implements all eight stages of the SAP FI R2R cycle:", ST["body"]
    ))

    steps = [
        (1, "Journal Entry Posting", "FB50",
         "Dr/Cr posting with GL validation. Creates FI document."),
        (2, "Accruals and Provisions", "FBS1",
         "Month-end accruals for expenses not yet invoiced."),
        (3, "Depreciation Run", "AFAB",
         "Dr Depreciation Expense / Cr Accumulated Depreciation."),
        (4, "GL Reconciliation", "FAGLF03",
         "Verifies GL account balances against sub-ledgers."),
        (5, "Adjustment Entries", "F-02",
         "Reclassification, error corrections, and period adjustments."),
        (6, "Trial Balance", "F.08",
         "Validates total Dr = total Cr. Flags variance if unbalanced."),
        (7, "Period / Year-End Close", "OB52",
         "Locks posting period. Carries forward balances (year-end)."),
        (8, "Financial Statements", "F.01",
         "Generates P&L and Balance Sheet from posted transactions."),
    ]
    story.append(process_table(steps))
    story.append(Spacer(1, 0.5*cm))

    story += section_header("4. Organizational Data")
    story.append(info_table([
        ("Company Code", "BR01"),
        ("Company Name", "BuildRight Construction Pvt. Ltd."),
        ("Chart of Accounts", "BRCOA — BuildRight Chart of Accounts"),
        ("Fiscal Year Variant", "K4 (April to March)"),
        ("Controlling Area", "BR01"),
        ("Posting Period", "Period 1 — April 2026"),
        ("Currency", "INR — Indian Rupee"),
    ]))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════
    # PAGE 4 — FI ACCOUNTING IMPACT
    # ══════════════════════════════════════════════════════
    story += section_header("5. FI Accounting Entries (MM-FI Integration)")
    story.append(Paragraph(
        "Each R2R transaction generates a double-entry accounting document in SAP FI. "
        "The following are the key accounting entries generated during the R2R cycle:", ST["body"]
    ))

    fi_rows = [
        ("Revenue Recognition\n(FB50)", "110000 Accounts Receivable", "500000 Revenue", "5,00,000"),
        ("COGS Posting\n(FB50)", "600000 Cost of Goods Sold", "120000 Inventory", "3,00,000"),
        ("Salary Accrual\n(FBS1)", "610000 Salaries & Wages", "310000 Accrued Liabilities", "75,000"),
        ("Depreciation Run\n(AFAB)", "620000 Depreciation Expense", "210000 Accum. Depreciation", "8,500"),
        ("Admin Expense Accrual\n(FBS1)", "630000 Admin Expenses", "310000 Accrued Liabilities", "12,000"),
        ("Tax Provision\n(FB50)", "650000 Tax Expense", "310000 Accrued Liabilities", "31,500"),
        ("Cash Collection\n(FB50)", "100000 Cash and Bank", "110000 Accounts Receivable", "5,00,000"),
        ("Vendor Payment\n(FB50)", "300000 Accounts Payable", "100000 Cash and Bank", "75,000"),
    ]
    story.append(fi_posting_table(fi_rows))
    story.append(Spacer(1, 0.4*cm))

    story += section_header("6. Trial Balance Summary")
    story.append(Paragraph(
        "After posting all journal entries, the trial balance is generated using F.08. "
        "The system validates that total debits equal total credits:", ST["body"]
    ))

    tb_data = [
        [Paragraph("<b>GL Account</b>", ST["small"]),
         Paragraph("<b>Account Name</b>", ST["small"]),
         Paragraph("<b>Debit (INR)</b>", ST["small"]),
         Paragraph("<b>Credit (INR)</b>", ST["small"])],
        *[
            [Paragraph(r[0], ST["small"]), Paragraph(r[1], ST["small"]),
             Paragraph(r[2], ParagraphStyle("TBNum", parent=ST["small"], fontName="Courier", alignment=TA_RIGHT)),
             Paragraph(r[3], ParagraphStyle("TBNum", parent=ST["small"], fontName="Courier", alignment=TA_RIGHT))]
            for r in [
                ("100000", "Cash and Bank", "5,00,000", "75,000"),
                ("110000", "Accounts Receivable", "5,00,000", "5,00,000"),
                ("120000", "Inventory", "—", "3,00,000"),
                ("210000", "Accumulated Depreciation", "—", "8,500"),
                ("300000", "Accounts Payable", "75,000", "—"),
                ("310000", "Accrued Liabilities", "—", "1,19,000"),
                ("500000", "Revenue", "—", "5,00,000"),
                ("600000", "COGS", "3,00,000", "—"),
                ("610000", "Salaries", "75,000", "—"),
                ("620000", "Depreciation Exp", "8,500", "—"),
                ("630000", "Admin Expenses", "12,000", "—"),
                ("650000", "Tax Expense", "31,500", "—"),
            ]
        ],
        [Paragraph("<b>Grand Total</b>", ST["highlight"]), Paragraph("", ST["small"]),
         Paragraph("<b>15,02,000</b>",
                   ParagraphStyle("TBTotal", parent=ST["small"], fontName="Courier-Bold", alignment=TA_RIGHT, textColor=SAP_GREEN)),
         Paragraph("<b>15,02,000</b>",
                   ParagraphStyle("TBTotal", parent=ST["small"], fontName="Courier-Bold", alignment=TA_RIGHT, textColor=SAP_GREEN))],
    ]
    tb_cw = [CONTENT_W*0.14, CONTENT_W*0.36, CONTENT_W*0.25, CONTENT_W*0.25]
    tb_tbl = Table(tb_data, colWidths=tb_cw)
    tb_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), SAP_BLUE),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("ROWBACKGROUNDS", (0,1), (-1,-2), [WHITE, SAP_GRAY]),
        ("BACKGROUND", (0,-1), (-1,-1), SAP_LIGHT),
        ("GRID", (0,0), (-1,-1), 0.3, SAP_BORDER),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING", (0,0), (-1,-1), 7),
        ("ALIGN", (2,0), (3,-1), "RIGHT"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(tb_tbl)

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════
    # PAGE 5 — FEATURES, TECH STACK, CONCLUSION
    # ══════════════════════════════════════════════════════
    story += section_header("7. Solution Features and Tech Stack")

    features = [
        ("Real Double-Entry Validation", "Every FB50 posting validates debit ≠ credit account and amount > 0 before saving."),
        ("Auto Trial Balance", "Live computation from all posted entries. Balanced/unbalanced status shown instantly."),
        ("Live Financial Statements", "P&L and Balance Sheet auto-generated from GL account balances in real time."),
        ("Depreciation Simulation", "AFAB run posts Dr Depreciation / Cr Accumulated Depreciation with period assignment."),
        ("Accrual Management", "FBS1 accruals post expenses with corresponding liability recognition."),
        ("GL Reconciliation Checklist", "8-step FAGLF03 reconciliation checklist with pass/fail status per step."),
        ("Period Close Workflow", "OB52 period close with prerequisite validation — blocked if TB is unbalanced."),
        ("Full Audit Trail", "Every journal entry stored in SQLite with JE number, date, period, cost center."),
    ]
    feat_data = [
        [Paragraph(f"<b>{f[0]}</b>", ParagraphStyle("FeatTitle", parent=ST["small"],
                   fontName="Helvetica-Bold", fontSize=11, textColor=SAP_BLUE)),
         Paragraph(f[1], ST["small"])]
        for f in features
    ]
    feat_tbl = Table(feat_data, colWidths=[CONTENT_W*0.32, CONTENT_W*0.68])
    feat_tbl.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [WHITE, SAP_GRAY]),
        ("GRID", (0,0), (-1,-1), 0.3, SAP_BORDER),
        ("TOPPADDING", (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LINEBEFORE", (0,0), (0,-1), 3, SAP_ACCENT),
    ]))
    story.append(feat_tbl)
    story.append(Spacer(1, 0.4*cm))

    story += section_header("8. Technology Stack")
    story.append(info_table([
        ("Backend", "Python 3 — SimpleHTTPRequestHandler, ThreadingHTTPServer"),
        ("Database", "SQLite — 4 tables: journal_entries, period_close, sequences, org_data"),
        ("Frontend", "HTML5, CSS3 (IBM Plex Sans), Vanilla JavaScript — no frameworks"),
        ("API", "REST: GET /api/state, POST /api/transactions/{type}, POST /api/seed"),
        ("Deployment", "Local — python app.py → http://127.0.0.1:8000"),
    ]))
    story.append(Spacer(1, 0.4*cm))

    story += section_header("9. Unique Points")
    unique = [
        "Single-file Python backend with no external dependencies — runs with standard Python 3",
        "Real SAP transaction codes used throughout (FB50, FBS1, AFAB, FAGLF03, F.08, OB52, F.01)",
        "GL account validation against Chart of Accounts — prevents invalid account posting",
        "Period close blocked automatically if trial balance is unbalanced",
        "Live P&L and Balance Sheet computed directly from journal entries — no hardcoded values",
        "Demo data covers a complete month-end cycle with 9 journal entries and 1 period close",
        "Export function generates full JSON snapshot for audit evidence",
    ]
    for u in unique:
        story.append(Paragraph(f"• {u}", ST["bullet"]))

    story.append(Spacer(1, 0.4*cm))
    story += section_header("10. Future Improvements")
    future = [
        "Implement multi-period reporting and comparative P&L (current vs prior period)",
        "Add intercompany elimination for group consolidation (F-IBU)",
        "Integrate automatic payment run (F110) and dunning (F150)",
        "Add user authentication and role-based access (FI Controller vs Viewer)",
        "Implement SAP-style tolerance checks for GL reconciliation variance thresholds",
        "Extend to full SAP CO integration with profit center accounting",
    ]
    for f in future:
        story.append(Paragraph(f"• {f}", ST["bullet"]))

    story.append(Spacer(1, 0.4*cm))
    story += section_header("11. Conclusion")
    story.append(Paragraph(
        "This project successfully demonstrates a complete SAP FI Record-to-Report cycle through "
        "an interactive simulator that replicates the core functionality of SAP's financial close "
        "process. From journal entry posting with double-entry validation to period close with "
        "prerequisite checks, every R2R stage is implemented and connected in sequence.",
        ST["body"]
    ))
    story.append(Paragraph(
        "The simulator generates live financial statements — Profit &amp; Loss and Balance Sheet — "
        "directly from posted journal entries, demonstrating real understanding of how SAP FI "
        "accounts accumulate balances and produce financial reports. The period close workflow "
        "enforces the correct sequence of steps, mirroring how SAP OB52 controls posting periods "
        "in production environments.",
        ST["body"]
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(callout_box(
        "Key Outcome",
        "The R2R Command Center demonstrates production-grade understanding of SAP FI financial "
        "close — including double-entry bookkeeping, GL account determination, trial balance "
        "validation, and financial statement generation — all implemented in a runnable, "
        "demo-ready simulator with a professional SAP-inspired interface."
    ))

    doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    print(f"PDF generated: {output_path}")


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "docs", "Project-Documentation.pdf")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    build_pdf(out)
