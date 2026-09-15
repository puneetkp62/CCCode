import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, PageBreak)

W, H = A4

# ---------- colour palette ----------
NAVY   = colors.HexColor('#1a237e')
BLUE   = colors.HexColor('#283593')
LITEBL = colors.HexColor('#e8eaf6')
SLATE  = colors.HexColor('#37474f')
GREY   = colors.HexColor('#455a64')
ORANGE = colors.HexColor('#e65100')
LGREY  = colors.HexColor('#f5f5f5')

def _style(name, **kw):
    base = kw.pop('parent', None)
    s = ParagraphStyle(name, **kw)
    return s

TITLE   = _style('T',  fontName='Helvetica-Bold',   fontSize=18, textColor=NAVY,  alignment=TA_CENTER, spaceAfter=4)
SUBT    = _style('S',  fontName='Helvetica',         fontSize=10, textColor=GREY,  alignment=TA_CENTER, spaceAfter=16)
SECHEAD = _style('SH', fontName='Helvetica-Bold',    fontSize=12, textColor=BLUE,  spaceBefore=14, spaceAfter=6)
QTEXT   = _style('Q',  fontName='Helvetica-Bold',    fontSize=10, textColor=SLATE, spaceAfter=3)
ATEXT   = _style('A',  fontName='Helvetica',         fontSize=10, textColor=colors.black, leftIndent=10, spaceAfter=10)
CBTEXT  = _style('CB', fontName='Helvetica',         fontSize=10, textColor=SLATE, leftIndent=14, spaceAfter=3)
INDIC   = _style('I',  fontName='Helvetica-Oblique', fontSize=9,  textColor=GREY,  leftIndent=6, spaceAfter=4)
DESC    = _style('D',  fontName='Helvetica',         fontSize=9,  textColor=SLATE, leftIndent=6, spaceAfter=2)
REFL    = _style('R',  fontName='Helvetica',         fontSize=9,  textColor=colors.black, leftIndent=6, spaceAfter=8)
FOOT    = _style('F',  fontName='Helvetica',         fontSize=8,  textColor=GREY,  alignment=TA_CENTER, spaceBefore=4)
CHDR    = _style('CH', fontName='Helvetica-Bold',    fontSize=10, textColor=BLUE)
CRAT    = _style('CR', fontName='Helvetica-Bold',    fontSize=11, textColor=ORANGE, alignment=TA_CENTER)


def generate_pdf(session_data, general_questions, explore_options):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            topMargin=1.5*cm, bottomMargin=1.5*cm,
                            leftMargin=2*cm, rightMargin=2*cm)
    story = []

    # ── Header ──────────────────────────────────────────────────────────────
    story.append(Paragraph("TechNova Imaging Systems Pvt Ltd", TITLE))
    story.append(Paragraph("Employee Self Reflection Form", SUBT))
    story.append(HRFlowable(width="100%", thickness=2, color=NAVY))
    story.append(Spacer(1, 0.4*cm))

    # ── Employee info table ──────────────────────────────────────────────────
    now = datetime.now().strftime('%d %b %Y')
    emp_rows = [
        [_b('Employee Code:'), session_data.get('emp_code',''),
         _b('Date:'), now],
        [_b('Employee Name:'), session_data.get('emp_name',''),
         _b('Band:'), session_data.get('band','')],
        [_b('Role:'), session_data.get('role',''),
         _b('Role Function:'), session_data.get('role_function','')],
        [_b('Team Leader:'), session_data.get('team_leader',''),
         _b('Division:'), session_data.get('division','')],
    ]
    emp_tbl = Table(emp_rows, colWidths=[3.5*cm, 6.5*cm, 3*cm, 4.5*cm])
    emp_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LGREY),
        ('FONTNAME',   (0,0), (-1,-1), 'Helvetica'),
        ('FONTNAME',   (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME',   (2,0), (2,-1), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 9),
        ('BOX',        (0,0), (-1,-1), 0.5, colors.grey),
        ('INNERGRID',  (0,0), (-1,-1), 0.25, colors.grey),
        ('PADDING',    (0,0), (-1,-1), 5),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(emp_tbl)
    story.append(Spacer(1, 0.5*cm))

    # ── Part A: General Reflection ───────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=BLUE))
    story.append(Paragraph("PART A — General Reflection Questions", SECHEAD))

    general = session_data.get('general_answers', {})
    for idx, question in enumerate(general_questions):
        story.append(Paragraph(f"Q{idx+1}.  {question}", QTEXT))
        if idx == 6:               # checkbox question
            selected = general.get(f'q{idx+1}', [])
            if isinstance(selected, str):
                selected = [s.strip() for s in selected.split(';') if s.strip()]
            for opt in explore_options:
                tick = '☑' if opt in selected else '☐'
                story.append(Paragraph(f"{tick}  {opt}", CBTEXT))
        else:
            ans = general.get(f'q{idx+1}', '') or '—'
            story.append(Paragraph(ans, ATEXT))

    story.append(PageBreak())

    # ── Part B: Competency Reflections ──────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=BLUE))
    band = session_data.get('band', '')
    rf   = session_data.get('role_function', '')
    story.append(Paragraph(
        f"PART B — Competency Reflections  |  Role Function: {rf}  |  Band: {band}",
        SECHEAD))

    comp_answers = session_data.get('competency_answers', {})
    for comp in comp_answers.values():
        # Header row: competency name + rating badge
        hdr = Table(
            [[Paragraph(f"{comp.get('competency','')} — {comp.get('attribute','')}", CHDR),
              Paragraph(f"Rating: {comp.get('rating','0')} / 10", CRAT)]],
            colWidths=[13.5*cm, 4*cm]
        )
        hdr.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), LITEBL),
            ('BOX',        (0,0), (-1,-1), 0.5, BLUE),
            ('PADDING',    (0,0), (-1,-1), 6),
            ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(hdr)

        desc = comp.get('description', '').strip()
        ind  = comp.get('indicator', '').strip()
        if desc:
            story.append(Paragraph(f"<b>Description:</b>  {desc}", DESC))
        if ind:
            story.append(Paragraph(f"<b>Expected Indicator (Band {band}):</b>  {ind}", INDIC))

        story.append(Paragraph("<b>Self Reflection:</b>",
                               _style('RL', fontName='Helvetica-Bold', fontSize=9,
                                      textColor=SLATE, leftIndent=6)))
        refl = comp.get('reflection', '').strip() or '—'
        story.append(Paragraph(refl, REFL))
        story.append(HRFlowable(width="100%", thickness=0.4, color=colors.lightgrey))
        story.append(Spacer(1, 0.12*cm))

    # ── Footer ───────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=NAVY))
    story.append(Paragraph(
        f"Submitted on {datetime.now().strftime('%d %B %Y at %I:%M %p')}  |  "
        f"Employee: {session_data.get('emp_name','')}  |  ID: {session_data.get('emp_code','')}",
        FOOT))

    doc.build(story)
    return buf.getvalue()


def _b(text):
    """Bold cell text for tables."""
    from reportlab.platypus import Paragraph
    return Paragraph(f"<b>{text}</b>",
                     ParagraphStyle('tb', fontName='Helvetica-Bold', fontSize=9))
