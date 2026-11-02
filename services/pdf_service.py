"""Professional PDF report generation using ReportLab."""

from datetime import datetime
from io import BytesIO

from flask import send_file
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_pdf(title: str, rows: list[list], headers: list[str], subtitle: str = ""):
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4) if len(headers) > 6 else A4,
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="SmartTitle", parent=styles["Title"], alignment=TA_CENTER, textColor=colors.HexColor("#173B73")))
    story = [Paragraph("SmartAlloc", styles["SmartTitle"]), Paragraph(title, styles["Heading2"])]
    if subtitle:
        story.append(Paragraph(subtitle, styles["Normal"]))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%d %b %Y, %H:%M:%S')}", styles["Normal"]))
    story.append(Spacer(1, 8))
    table_data = [headers] + [[str(cell if cell is not None else "") for cell in row] for row in rows]
    table = Table(table_data, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#173B73")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F7FB")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(table)
    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"{title.lower().replace(' ', '_')}.pdf", mimetype="application/pdf")


def _footer(canvas, document):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.drawRightString(document.pagesize[0] - 12 * mm, 7 * mm, f"Page {document.page}")
    canvas.restoreState()

