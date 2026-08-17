import os
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


async def generate_invoice(
    order_data: dict, client_data: dict, output_path: str
) -> str:
    """
    Generates a professional PDF invoice for the cleaning service.
    """
    if not REPORTLAB_AVAILABLE:
        from loguru import logger

        logger.warning("reportlab o'rnatilmagan — PDF faktura yaratilmadi.")
        return None

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    indigo_color = colors.HexColor("#6366f1")

    # Custom styles
    title_style = ParagraphStyle(
        name="TitleStyle",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=indigo_color,
        alignment=TA_CENTER,
        spaceAfter=20,
    )

    header_style = ParagraphStyle(
        name="HeaderStyle",
        parent=styles["Normal"],
        fontSize=12,
        spaceAfter=5,
    )

    company_info_style = ParagraphStyle(
        name="CompanyInfo",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.gray,
        alignment=TA_CENTER,
    )

    elements = []

    # 1. Logo/Title
    elements.append(Paragraph("<b>TOZALASH SERVIS</b>", title_style))
    elements.append(Spacer(1, 10))

    # 2. Invoice Details
    order_id = order_data.get("id", "N/A")
    date_str = datetime.now().strftime("%d.%m.%Y")

    elements.append(Paragraph(f"<b>INVOICE #:</b> {order_id}", header_style))
    elements.append(Paragraph(f"<b>DATE:</b> {date_str}", header_style))
    elements.append(Spacer(1, 10))

    # 3. Client Info
    client_name = client_data.get("name", "N/A")
    client_phone = client_data.get("phone", "N/A")

    elements.append(Paragraph("<b>BILL TO:</b>", header_style))
    elements.append(Paragraph(f"Name: {client_name}", header_style))
    elements.append(Paragraph(f"Phone: {client_phone}", header_style))
    elements.append(Spacer(1, 20))

    # 4. Itemized Table
    table_data = [["Service Name", "Qty", "Unit", "Price/Unit", "Total"]]

    items = order_data.get("items", [])
    if not items:
        # Default placeholder if no items format provided
        table_data.append(
            [
                "Cleaning Service",
                "1",
                "service",
                f"{order_data.get('total_amount', 0):,} so'm",
                f"{order_data.get('total_amount', 0):,} so'm",
            ]
        )
    else:
        for item in items:
            table_data.append(
                [
                    item.get("name", "Service"),
                    str(item.get("quantity", 1)),
                    item.get("unit", "unit"),
                    f"{item.get('price', 0):,} so'm",
                    f"{item.get('total', 0):,} so'm",
                ]
            )

    # Add table style
    t = Table(table_data, colWidths=[200, 50, 60, 100, 105])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), indigo_color),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("ALIGN", (0, 1), (0, -1), "LEFT"),  # Service name left aligned
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
                ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
            ]
        )
    )

    elements.append(t)
    elements.append(Spacer(1, 20))

    # 5. Totals
    total_amount = order_data.get("total_amount", 0)
    status = order_data.get("status", "pending").upper()

    total_style = ParagraphStyle(
        name="TotalStyle",
        parent=styles["Normal"],
        fontSize=14,
        alignment=TA_RIGHT,
        fontName="Helvetica-Bold",
    )

    elements.append(
        Paragraph(f"<b>GRAND TOTAL:</b> {total_amount:,} so'm", total_style)
    )
    elements.append(Spacer(1, 10))

    status_color = colors.green if status == "PAID" else colors.red
    status_style = ParagraphStyle(
        name="StatusStyle",
        parent=styles["Normal"],
        fontSize=12,
        alignment=TA_RIGHT,
        textColor=status_color,
        fontName="Helvetica-Bold",
    )
    elements.append(Paragraph(f"PAYMENT STATUS: {status}", status_style))

    elements.append(Spacer(1, 50))

    # 6. Footer
    elements.append(Paragraph("Thank you for your business!", company_info_style))
    elements.append(
        Paragraph(
            "Tozalash Servis | +998 90 123 45 67 | tozalash.uz", company_info_style
        )
    )

    # Build PDF
    doc.build(elements)

    return output_path
