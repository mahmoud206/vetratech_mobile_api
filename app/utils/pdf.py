from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import base64


# Arabic font setup (make sure 'assets/fonts/arabic.ttf' exists)
def _setup_arabic_font():
    try:
        pdfmetrics.registerFont(TTFont('Arabic', 'assets/fonts/arabic.ttf'))
    except:
        # Fallback to Arial if custom font not found
        pdfmetrics.registerFont(TTFont('Arabic', 'Arial'))


# Arabic text formatter
def _ar(text: str) -> str:
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


# Header style
def _create_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='ArabicTitle',
        fontName='Arabic',
        fontSize=16,
        leading=20,
        alignment=2,  # Right align
        spaceAfter=12
    ))
    styles.add(ParagraphStyle(
        name='ArabicHeader',
        fontName='Arabic',
        fontSize=14,
        textColor=colors.darkgreen,
        alignment=2
    ))
    styles.add(ParagraphStyle(
        name='ArabicNormal',
        fontName='Arabic',
        fontSize=12,
        alignment=2
    ))
    return styles


async def generate_full_report_pdf(
        payment_data: list,
        clinic_data: dict,
        sales_data: dict,
        start_date: datetime,
        end_date: datetime,
        db_name: str
) -> bytes:
    """Generate PDF with all three reports"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    # Initialize fonts and styles
    _setup_arabic_font()
    styles = _create_styles()
    elements = []

    # 1. Cover Page
    elements.append(Paragraph(_ar("تقرير العيادة البيطرية الشامل"), styles['ArabicTitle']))
    elements.append(Spacer(1, 24))
    elements.append(Paragraph(_ar(f"القاعدة: {db_name}"), styles['ArabicNormal']))
    elements.append(Paragraph(
        _ar(f"الفترة من {start_date.strftime('%Y-%m-%d')} إلى {end_date.strftime('%Y-%m-%d')}"),
        styles['ArabicNormal']
    ))
    elements.append(PageBreak())

    # 2. Payment Report
    _add_payment_report(elements, payment_data, styles)
    elements.append(PageBreak())

    # 3. Clinic Report
    _add_clinic_report(elements, clinic_data, styles)
    elements.append(PageBreak())

    # 4. Sales Report
    _add_sales_report(elements, sales_data, styles)

    # Generate PDF
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return base64.b64encode(pdf_bytes).decode('latin1')


def _add_payment_report(elements: list, data: list, styles):
    """Add payment report section"""
    elements.append(Paragraph(_ar("تقرير المدفوعات"), styles['ArabicHeader']))
    elements.append(Spacer(1, 12))

    # Prepare table data
    table_data = [
        [
            _ar("النوع"),
            _ar("الطريقة"),
            _ar("المبلغ"),
            _ar("عدد المعاملات")
        ]
    ]

    for item in data:
        payment_type = _ar("صادر" if item['isOutgoing'] else "وارد")
        method = _ar("شبكة" if item['method'] == "network" else "كاش")
        table_data.append([
            payment_type,
            method,
            f"{item['totalAmount']:.2f} SAR",
            str(item['transactionCount'])
        ])

    # Create table
    table = Table(
        table_data,
        colWidths=[1.2 * inch, 1.2 * inch, 1 * inch, 1 * inch],
        repeatRows=1
    )

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Arabic'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)


def _add_clinic_report(elements: list, data: dict, styles):
    """Add clinic report section"""
    elements.append(Paragraph(_ar("تقرير العيادة"), styles['ArabicHeader']))
    elements.append(Spacer(1, 12))

    # Summary table
    summary_data = [
        [_ar("الإجمالي"), f"{data['totalRevenue']:.2f} SAR"],
        [_ar("خدمات لارج"), f"{data['largeServicesRevenue']:.2f} SAR"],
        [_ar("خدمات عادية"), f"{data['normalServicesRevenue']:.2f} SAR"]
    ]

    summary_table = Table(
        summary_data,
        colWidths=[2 * inch, 2 * inch],
        style=TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Arabic'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
    )

    elements.append(summary_table)


def _add_sales_report(elements: list, data: dict, styles):
    """Add sales report section"""
    elements.append(Paragraph(_ar("تقرير المبيعات والأرباح"), styles['ArabicHeader']))
    elements.append(Spacer(1, 12))

    # Summary
    elements.append(Paragraph(
        _ar(f"إجمالي الإيرادات: {data['totalRevenue']:.2f} SAR"),
        styles['ArabicNormal']
    ))
    elements.append(Paragraph(
        _ar(f"إجمالي الأرباح: {data['totalProfit']:.2f} SAR"),
        styles['ArabicNormal']
    ))
    elements.append(Spacer(1, 12))

    # Top products table
    if data['topProducts']:
        elements.append(Paragraph(_ar("أفضل المنتجات:"), styles['ArabicNormal']))

        table_data = [
            [_ar("المنتج"), _ar("الإيراد"), _ar("الربح")]
        ]

        for product in data['topProducts']:
            table_data.append([
                _ar(product['productName']),
                f"{product['revenue']:.2f} SAR",
                f"{product['profit']:.2f} SAR"
            ])

        products_table = Table(
            table_data,
            colWidths=[3 * inch, 1.5 * inch, 1.5 * inch],
            repeatRows=1,
            style=TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Arabic'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ])
        )

        elements.append(products_table)