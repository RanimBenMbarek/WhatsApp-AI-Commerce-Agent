
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    LongTable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas.invoice import InvoiceData


def _money(amount, currency: str) -> str:
    return f"{amount:,.2f} {escape(currency)}"


def _safe_text(value: object) -> str:
    """Escape dynamic text before putting it into ReportLab paragraphs."""
    return escape(str(value))


def _format_address(address: dict) -> str:
    """Format a shipping address without assuming a specific address schema."""
    parts = []

    for value in address.values():
        if isinstance(value, (str, int, float)) and str(value).strip():
            parts.append(_safe_text(value))

    return "<br/>".join(parts) if parts else "Not provided"


def render_invoice_pdf(data: InvoiceData) -> bytes:
    """Render validated invoice data into a PDF document."""
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Invoice {data.invoice_number}",
        author=data.seller_name,
    )

    base_styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "InvoiceTitle",
        parent=base_styles["Title"],
        alignment=TA_CENTER,
        fontSize=22,
        spaceAfter=12,
    )

    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=base_styles["Heading2"],
        fontSize=11,
        spaceBefore=10,
        spaceAfter=6,
    )

    body_style = base_styles["BodyText"]

    right_style = ParagraphStyle(
        "RightAligned",
        parent=body_style,
        alignment=TA_RIGHT,
    )

    story = []

    # Invoice heading
    story.append(Paragraph("INVOICE", title_style))
    story.append(
        Paragraph(
            f"<b>Invoice number:</b> {_safe_text(data.invoice_number)}",
            body_style,
        )
    )
    story.append(
        Paragraph(
            f"<b>Issue date:</b> "
            f"{_safe_text(data.issued_at.strftime('%Y-%m-%d'))}",
            body_style,
        )
    )
    story.append(
        Paragraph(
            f"<b>Order number:</b> {_safe_text(data.order_number)}",
            body_style,
        )
    )
    story.append(Spacer(1, 8 * mm))

    # Seller and customer information
    story.append(Paragraph("Seller", heading_style))
    story.append(Paragraph(_safe_text(data.seller_name), body_style))
    story.append(
        Paragraph(
            _safe_text(data.seller_address).replace("\n", "<br/>"),
            body_style,
        )
    )

    if data.seller_contact:
        story.append(Paragraph(_safe_text(data.seller_contact), body_style))

    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Bill to / Ship to", heading_style))
    story.append(Paragraph(_safe_text(data.customer_name), body_style))
    story.append(
        Paragraph(_format_address(data.shipping_address), body_style)
    )

    story.append(Spacer(1, 8 * mm))

    # Order items
    story.append(Paragraph("Items", heading_style))

    table_data = [[
        "Product",
        "SKU",
        "Qty",
        "Unit price",
        "Line total",
    ]]

    for item in data.items:
        product_description = _safe_text(item.product_name)

        if item.variant_description:
            product_description += (
                f"<br/><font size='8'>"
                f"{_safe_text(item.variant_description)}</font>"
            )

        table_data.append([
            Paragraph(product_description, body_style),
            Paragraph(_safe_text(item.sku), body_style),
            str(item.quantity),
            _money(item.unit_price, data.currency),
            _money(item.line_total, data.currency),
        ])

    items_table = LongTable(
        table_data,
        colWidths=[54 * mm, 28 * mm, 12 * mm, 32 * mm, 32 * mm],
        repeatRows=1,
        hAlign="LEFT",
    )

    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#263445")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D8DEE6")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
            colors.white,
            colors.HexColor("#F4F6F8"),
        ]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    story.append(items_table)
    story.append(Spacer(1, 8 * mm))

    # Totals
    totals_data = [
        ["Subtotal", _money(data.subtotal, data.currency)],
        ["Shipping", _money(data.shipping_fee, data.currency)],
        ["Total", _money(data.total, data.currency)],
    ]

    totals_table = Table(
        totals_data,
        colWidths=[45 * mm, 45 * mm],
        hAlign="RIGHT",
    )

    totals_table.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, -2), "Helvetica"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor("#263445")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    story.append(totals_table)
    story.append(Spacer(1, 8 * mm))

    # Order/payment status
    story.append(
        Paragraph(
            f"<b>Order status:</b> {_safe_text(data.order_status)}",
            body_style,
        )
    )
    story.append(
        Paragraph(
            f"<b>Payment status:</b> {_safe_text(data.payment_status)}",
            body_style,
        )
    )

    document.build(story)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes
