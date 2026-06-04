"""
Generate TECHNICAL_DOCUMENTATION.pdf from README.md
Uses reportlab for clean, professional PDF output.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Preformatted, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import Flowable
import re

# ─── Colors ────────────────────────────────────────────────────────────────
PRIMARY    = HexColor("#1a1a2e")   # dark navy
ACCENT     = HexColor("#5c6bc0")   # indigo
ACCENT2    = HexColor("#26a69a")   # teal
CODE_BG    = HexColor("#f5f5f5")
CODE_TEXT  = HexColor("#263238")
H1_COLOR   = HexColor("#1a1a2e")
H2_COLOR   = HexColor("#5c6bc0")
H3_COLOR   = HexColor("#26a69a")
TABLE_HDR  = HexColor("#5c6bc0")
TABLE_ALT  = HexColor("#f3f4fc")
RULE_COLOR = HexColor("#e0e0e0")
MUTED      = HexColor("#757575")
BODY_COLOR = HexColor("#212121")

W, H = A4
MARGIN = 1.8 * cm

# ─── Styles ─────────────────────────────────────────────────────────────────
base = getSampleStyleSheet()

def make_style(name, parent="Normal", **kw):
    s = ParagraphStyle(name, parent=base[parent], **kw)
    return s

styles = {
    "h1": make_style("h1", "Heading1",
        fontSize=22, textColor=H1_COLOR, spaceAfter=6,
        spaceBefore=18, fontName="Helvetica-Bold", leading=28),
    "h2": make_style("h2", "Heading2",
        fontSize=16, textColor=H2_COLOR, spaceAfter=4,
        spaceBefore=14, fontName="Helvetica-Bold", leading=22),
    "h3": make_style("h3", "Heading3",
        fontSize=13, textColor=H3_COLOR, spaceAfter=3,
        spaceBefore=10, fontName="Helvetica-Bold", leading=18),
    "h4": make_style("h4", "Heading4",
        fontSize=11, textColor=ACCENT, spaceAfter=2,
        spaceBefore=8, fontName="Helvetica-Bold", leading=16),
    "body": make_style("body", "Normal",
        fontSize=10, textColor=BODY_COLOR, spaceAfter=5,
        spaceBefore=2, fontName="Helvetica", leading=15),
    "bullet": make_style("bullet", "Normal",
        fontSize=10, textColor=BODY_COLOR, spaceAfter=3,
        spaceBefore=1, fontName="Helvetica", leading=14,
        leftIndent=12, bulletIndent=0),
    "code": make_style("code", "Code",
        fontSize=8.5, textColor=CODE_TEXT, spaceAfter=6,
        spaceBefore=4, fontName="Courier", leading=13,
        leftIndent=8, rightIndent=8,
        backColor=CODE_BG, borderPadding=(4, 6, 4, 6)),
    "th_cell": make_style("th_cell", "Normal",
        fontSize=9, textColor=white, fontName="Helvetica-Bold",
        leading=13, alignment=TA_LEFT),
    "td_cell": make_style("td_cell", "Normal",
        fontSize=9, textColor=BODY_COLOR, fontName="Helvetica",
        leading=13, alignment=TA_LEFT),
    "cover_title": make_style("cover_title", "Normal",
        fontSize=32, textColor=white, fontName="Helvetica-Bold",
        leading=40, alignment=TA_CENTER),
    "cover_sub": make_style("cover_sub", "Normal",
        fontSize=14, textColor=HexColor("#b0bec5"), fontName="Helvetica",
        leading=20, alignment=TA_CENTER),
    "toc_h1": make_style("toc_h1", "Normal",
        fontSize=11, textColor=PRIMARY, fontName="Helvetica-Bold",
        leading=16, spaceBefore=4),
    "toc_h2": make_style("toc_h2", "Normal",
        fontSize=10, textColor=ACCENT, fontName="Helvetica",
        leading=15, leftIndent=16, spaceBefore=1),
}


class ColorBox(Flowable):
    """A solid colored rectangle (used for cover background)."""
    def __init__(self, width, height, color, radius=0):
        super().__init__()
        self.width = width
        self.height = height
        self.color = color
        self.radius = radius

    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.roundRect(0, 0, self.width, self.height,
                            self.radius, fill=1, stroke=0)


def header_footer(canvas, doc):
    canvas.saveState()
    # Header line
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(1)
    canvas.line(MARGIN, H - 0.9*cm, W - MARGIN, H - 0.9*cm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN, H - 0.7*cm, "AI Sales Training Platform — Technical Documentation")
    canvas.drawRightString(W - MARGIN, H - 0.7*cm, "Confidential")
    # Footer line
    canvas.line(MARGIN, 1.1*cm, W - MARGIN, 1.1*cm)
    canvas.drawString(MARGIN, 0.7*cm, "© 2025 AI Sales Training Platform")
    canvas.drawRightString(W - MARGIN, 0.7*cm, f"Page {doc.page}")
    canvas.restoreState()


# ─── Markdown → ReportLab parser ────────────────────────────────────────────

def escape_xml(text):
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))

def inline_format(text):
    """Convert inline `code`, **bold**, *italic* to reportlab XML tags."""
    # backtick code
    text = re.sub(r'`([^`]+)`', lambda m: f'<font name="Courier" color="#c0392b">{escape_xml(m.group(1))}</font>', text)
    # bold
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    # italic
    text = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', text)
    return text

def parse_table(lines, idx):
    """Parse a markdown table starting at lines[idx]. Returns (flowable, new_idx)."""
    rows = []
    i = idx
    while i < len(lines):
        line = lines[i].strip()
        if not line.startswith("|"):
            break
        # skip separator rows like |---|---|
        if re.match(r'^\|[\s\-:|]+\|', line):
            i += 1
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        rows.append(cells)
        i += 1

    if not rows:
        return None, idx + 1

    col_count = max(len(r) for r in rows)
    # Normalize row widths
    rows = [r + [""] * (col_count - len(r)) for r in rows]

    avail = W - 2 * MARGIN
    col_w = avail / col_count

    header = rows[0]
    body   = rows[1:]

    table_data = []
    # Header row
    table_data.append([Paragraph(escape_xml(cell), styles["th_cell"]) for cell in header])
    for ri, row in enumerate(body):
        style = styles["td_cell"]
        table_data.append([Paragraph(escape_xml(cell), style) for cell in row])

    t = Table(table_data, colWidths=[col_w] * col_count, repeatRows=1)
    ts = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HDR),
        ("TEXTCOLOR",  (0, 0), (-1, 0), white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, TABLE_ALT]),
        ("GRID",       (0, 0), (-1, -1), 0.4, RULE_COLOR),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
    ])
    t.setStyle(ts)
    return t, i


def markdown_to_flowables(md_text):
    story = []
    lines = md_text.split("\n")
    i = 0
    code_buffer = []
    in_code = False
    code_lang = ""

    while i < len(lines):
        line = lines[i]

        # ── Code block ────────────────────────────────────
        if line.strip().startswith("```"):
            if not in_code:
                in_code = True
                code_lang = line.strip()[3:].strip()
                code_buffer = []
                i += 1
                continue
            else:
                in_code = False
                code_text = "\n".join(code_buffer)
                # Wrap in a box
                pre = Preformatted(code_text, styles["code"])
                story.append(pre)
                story.append(Spacer(1, 4))
                i += 1
                continue

        if in_code:
            code_buffer.append(line)
            i += 1
            continue

        # ── Horizontal rule ───────────────────────────────
        if re.match(r'^---+\s*$', line):
            story.append(Spacer(1, 6))
            story.append(HRFlowable(width="100%", thickness=0.5, color=RULE_COLOR))
            story.append(Spacer(1, 6))
            i += 1
            continue

        # ── Headings ──────────────────────────────────────
        if line.startswith("#### "):
            story.append(Paragraph(inline_format(escape_xml(line[5:])), styles["h4"]))
            i += 1
            continue
        if line.startswith("### "):
            story.append(Paragraph(inline_format(escape_xml(line[4:])), styles["h3"]))
            i += 1
            continue
        if line.startswith("## "):
            story.append(Paragraph(inline_format(escape_xml(line[3:])), styles["h2"]))
            story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#c5cae9")))
            story.append(Spacer(1, 3))
            i += 1
            continue
        if line.startswith("# "):
            story.append(PageBreak())
            story.append(Paragraph(inline_format(escape_xml(line[2:])), styles["h1"]))
            story.append(HRFlowable(width="100%", thickness=2, color=ACCENT))
            story.append(Spacer(1, 6))
            i += 1
            continue

        # ── Table ─────────────────────────────────────────
        if line.strip().startswith("|"):
            table_flowable, i = parse_table(lines, i)
            if table_flowable:
                story.append(table_flowable)
                story.append(Spacer(1, 6))
            continue

        # ── Bullet ────────────────────────────────────────
        if re.match(r'^(\s*)[-*] ', line):
            indent_level = len(re.match(r'^(\s*)', line).group(1)) // 2
            text = re.sub(r'^(\s*)[-*] ', '', line)
            bullet_style = ParagraphStyle(
                f"bullet_{indent_level}", parent=styles["bullet"],
                leftIndent=12 + indent_level * 16,
                bulletIndent=indent_level * 16,
            )
            story.append(Paragraph("• " + inline_format(escape_xml(text)), bullet_style))
            i += 1
            continue

        # ── Numbered list ─────────────────────────────────
        if re.match(r'^\d+\. ', line):
            num, text = re.match(r'^(\d+)\. (.+)', line).groups()
            story.append(Paragraph(f"{num}. {inline_format(escape_xml(text))}", styles["bullet"]))
            i += 1
            continue

        # ── Empty line ────────────────────────────────────
        if not line.strip():
            story.append(Spacer(1, 5))
            i += 1
            continue

        # ── Normal paragraph ──────────────────────────────
        story.append(Paragraph(inline_format(escape_xml(line)), styles["body"]))
        i += 1

    return story


def build_cover():
    """Build cover page flowables."""
    story = []
    story.append(Spacer(1, 3.5 * cm))

    # Title block
    title_data = [[Paragraph("AI Sales Training Platform", styles["cover_title"])]]
    title_table = Table(title_data, colWidths=[W - 2*MARGIN])
    title_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PRIMARY),
        ("TOPPADDING",    (0, 0), (-1, -1), 24),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 24),
        ("LEFTPADDING",   (0, 0), (-1, -1), 20),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 20),
        ("ROUNDEDCORNERS", [6]),
    ]))
    story.append(title_table)
    story.append(Spacer(1, 0.8 * cm))

    story.append(Paragraph("Technical Documentation", styles["cover_sub"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Backend API Reference &amp; Developer Guide", ParagraphStyle(
        "cv3", parent=styles["cover_sub"], fontSize=12,
        textColor=HexColor("#90a4ae"))))
    story.append(Spacer(1, 2 * cm))

    # Info table
    info = [
        ["Platform",  "AI Sales Training Platform"],
        ["Framework", "FastAPI (Python 3.9+)"],
        ["AI Models", "OpenAI GPT-4o-mini · Whisper · ElevenLabs"],
        ["Database",  "MongoDB (Motor async)"],
        ["Storage",   "AWS S3"],
        ["Version",   "1.0.0"],
        ["Status",    "Production Ready"],
    ]
    info_table = Table(
        [[Paragraph(k, ParagraphStyle("ik", parent=styles["body"],
                    fontName="Helvetica-Bold", textColor=ACCENT)),
          Paragraph(v, styles["body"])] for k, v in info],
        colWidths=[4.5*cm, W - 2*MARGIN - 4.5*cm]
    )
    info_table.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [white, TABLE_ALT]),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, RULE_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 1.5 * cm))
    story.append(Paragraph("© 2025 AI Sales Training Platform · Confidential",
        ParagraphStyle("foot", parent=styles["body"], textColor=MUTED,
                       fontSize=8, alignment=TA_CENTER)))
    story.append(PageBreak())
    return story


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    output = "TECHNICAL_DOCUMENTATION.pdf"

    # Read README
    with open("README.md", "r", encoding="utf-8") as f:
        md = f.read()

    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title="AI Sales Training Platform — Technical Documentation",
        author="AI Sales Training Platform",
        subject="Backend API Reference",
    )

    story = []
    story += build_cover()
    story += markdown_to_flowables(md)

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"✅ PDF generated: {output}")


if __name__ == "__main__":
    main()
