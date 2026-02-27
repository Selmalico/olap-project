import os
from datetime import datetime
from io import BytesIO

from jinja2 import Environment, FileSystemLoader
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

env = Environment(
    loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "..", "templates"))
)


def generate_pdf(request) -> bytes:
    """Generate PDF report using reportlab."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter, topMargin=0.5 * inch, bottomMargin=0.5 * inch
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=colors.HexColor("#1f2937"),
        spaceAfter=12,
        alignment=1,  # Center
    )

    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#374151"),
        spaceAfter=10,
        spaceBefore=10,
    )

    story = []

    # Add title
    story.append(Paragraph(request.title, title_style))
    story.append(Paragraph(f"Query: {request.query}", styles["Normal"]))
    story.append(
        Paragraph(
            f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.3 * inch))

    # Add executive summary if available
    exec_summary = next(
        (
            r.get("narrative")
            for r in request.results
            if r.get("agent_name") == "executive_summary"
        ),
        None,
    )

    if exec_summary:
        story.append(Paragraph("Executive Summary", heading_style))
        story.append(Paragraph(exec_summary, styles["Normal"]))
        story.append(Spacer(1, 0.2 * inch))

    # Add data sections as tables
    for result in request.results:
        if not result.get("data"):
            continue

        data = result["data"]
        cols = list(data[0].keys()) if data else []

        story.append(
            Paragraph(
                result.get("agent_name", "").replace("_", " ").title(), heading_style
            )
        )

        # Build table data
        table_data = [cols]  # Header row
        for row in data[:50]:  # Cap at 50 rows
            table_data.append([str(row.get(col, "")) for col in cols])

        # Create and style table
        table = Table(
            table_data,
            colWidths=[2 * inch if len(cols) <= 3 else 1.5 * inch for _ in cols],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#f9fafb")],
                    ),
                ]
            )
        )

        story.append(table)
        story.append(Spacer(1, 0.2 * inch))

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
