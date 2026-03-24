"""
Fizibilite Raporu PDF Dışa Aktarma — ReportLab ile profesyonel PDF.

İyileştirmeler:
- DejaVu Sans font ile Türkçe karakter desteği (ğ,ş,ç,ö,ü,İ)
- Kat planı görseli embed
- Grafik embed desteği
"""

import os
import io
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# DejaVu Sans font yolları
DEJAVU_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
    "C:/Windows/Fonts/DejaVuSans.ttf",
    os.path.join(os.path.dirname(__file__), "..", "fonts", "DejaVuSans.ttf"),
]

DEJAVU_BOLD_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/DejaVuSans-Bold.ttf",
    os.path.join(os.path.dirname(__file__), "..", "fonts",
                 "DejaVuSans-Bold.ttf"),
]


def _find_font(paths: list[str]) -> str | None:
    """Font dosyasını bul."""
    for p in paths:
        if os.path.exists(p):
            return p
    return None


def _register_turkish_fonts():
    """DejaVu Sans fontunu ReportLab'e kaydet."""
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        regular = _find_font(DEJAVU_PATHS)
        bold = _find_font(DEJAVU_BOLD_PATHS)

        if regular:
            pdfmetrics.registerFont(TTFont("DejaVuSans", regular))
            logger.info(f"DejaVuSans font registered: {regular}")
        if bold:
            pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", bold))
            logger.info(f"DejaVuSans-Bold font registered: {bold}")

        return regular is not None
    except Exception as e:
        logger.warning(f"Font registration failed: {e}")
        return False


def olustur_fizibilite_pdf(
    proje_bilgileri: dict,
    hesaplama: dict,
    maliyet: dict,
    gelir: dict,
    fizibilite: dict,
    duyarlilik: list = None,
    deprem: dict = None,
    enerji: dict = None,
    gantt_data: dict = None,
    plan_image_path: str = None,
    chart_image_paths: list = None,
    output_path: str = "fizibilite_raporu.pdf",
) -> str:
    """Fizibilite raporu PDF'i oluşturur."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm, mm
        from reportlab.lib.colors import HexColor
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            PageBreak, Image, HRFlowable,
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    except ImportError:
        logger.error("reportlab kurulu degil. pip install reportlab ile kurun.")
        return ""

    # Türkçe font desteği
    has_turkish_font = _register_turkish_fonts()
    font_name = "DejaVuSans" if has_turkish_font else "Helvetica"
    font_bold = "DejaVuSans-Bold" if has_turkish_font else "Helvetica-Bold"

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=2.5 * cm, bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="RaporBaslik", fontSize=22, fontName=font_bold,
        alignment=TA_CENTER, spaceAfter=20,
        textColor=HexColor("#1565C0"),
    ))
    styles.add(ParagraphStyle(
        name="BolumBaslik", fontSize=14, fontName=font_bold,
        spaceAfter=10, spaceBefore=15,
        textColor=HexColor("#1E88E5"),
    ))
    styles.add(ParagraphStyle(
        name="AltBaslik", fontSize=11, fontName=font_bold,
        spaceAfter=6, spaceBefore=8,
    ))
    styles.add(ParagraphStyle(
        name="Normal_TR", fontSize=10, fontName=font_name,
        spaceAfter=4, leading=14,
    ))

    elements = []

    # ══════════════════════════════════════════════════
    # KAPAK SAYFASI
    # ══════════════════════════════════════════════════
    elements.append(Spacer(1, 4 * cm))
    elements.append(Paragraph("F\u0130Z\u0130B\u0130L\u0130TE RAPORU",
                              styles["RaporBaslik"]))
    elements.append(Spacer(1, 1 * cm))

    proje_adi = proje_bilgileri.get("proje_adi", "Konut Projesi")
    elements.append(Paragraph(proje_adi, ParagraphStyle(
        "ProjeAdi", fontSize=16, fontName=font_name,
        alignment=TA_CENTER, textColor=HexColor("#333"),
    )))

    elements.append(Spacer(1, 2 * cm))
    elements.append(HRFlowable(width="80%", thickness=1,
                               color=HexColor("#1E88E5")))
    elements.append(Spacer(1, 0.5 * cm))

    kapak_bilgi = [
        f"\u0130l / \u0130l\u00e7e: {proje_bilgileri.get('il', '-')} / "
        f"{proje_bilgileri.get('ilce', '-')}",
        f"Ada / Parsel: {proje_bilgileri.get('ada', '-')} / "
        f"{proje_bilgileri.get('parsel', '-')}",
        f"Tarih: {datetime.now().strftime('%d.%m.%Y')}",
    ]
    for bilgi in kapak_bilgi:
        elements.append(Paragraph(bilgi, ParagraphStyle(
            "KapakBilgi", fontSize=11, fontName=font_name,
            alignment=TA_CENTER, spaceAfter=6,
        )))

    elements.append(PageBreak())

    # ══════════════════════════════════════════════════
    # PROJE OZETI
    # ══════════════════════════════════════════════════
    elements.append(Paragraph("1. PROJE \u00d6ZET\u0130",
                              styles["BolumBaslik"]))

    ozet_data = [["Parametre", "De\u011fer"]]
    for k, v in proje_bilgileri.items():
        ozet_data.append([str(k).replace("_", " ").title(), str(v)])

    table_style_common = [
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("FONTNAME", (0, 0), (-1, 0), font_bold),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#CCCCCC")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]

    t = Table(ozet_data, colWidths=[8 * cm, 8 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1E88E5")),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [HexColor("#F5F5F5"), HexColor("#FFFFFF")]),
    ] + table_style_common))
    elements.append(t)

    # ── Kat planı görseli ──
    if plan_image_path and os.path.exists(plan_image_path):
        elements.append(Spacer(1, 0.5 * cm))
        elements.append(Paragraph("Kat Plan\u0131 G\u00f6rseli",
                                  styles["AltBaslik"]))
        try:
            img = Image(plan_image_path, width=14 * cm, height=10 * cm)
            img.hAlign = "CENTER"
            elements.append(img)
        except Exception as e:
            logger.warning(f"Plan gorseli eklenemedi: {e}")

    # ══════════════════════════════════════════════════
    # HESAPLAMA SONUCLARI
    # ══════════════════════════════════════════════════
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph("2. HESAPLAMA SONU\u00c7LARI",
                              styles["BolumBaslik"]))

    if hesaplama:
        hesap_data = [["Kalem", "De\u011fer"]]
        for k, v in hesaplama.items():
            hesap_data.append([str(k), str(v)])
        t2 = Table(hesap_data, colWidths=[10 * cm, 6 * cm])
        t2.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#4CAF50")),
            ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [HexColor("#F5F5F5"), HexColor("#FFFFFF")]),
        ] + table_style_common))
        elements.append(t2)

    # ══════════════════════════════════════════════════
    # MALI ANALIZ
    # ══════════════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("3. MAL\u0130 ANAL\u0130Z",
                              styles["BolumBaslik"]))

    elements.append(Paragraph("3.1 Maliyet Tahmini", styles["AltBaslik"]))
    if maliyet:
        mal_data = [["Kalem", "Tutar"]]
        for k, v in maliyet.items():
            mal_data.append([str(k), str(v)])
        t3 = Table(mal_data, colWidths=[10 * cm, 6 * cm])
        t3.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#E53935")),
            ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [HexColor("#FFF3F3"), HexColor("#FFFFFF")]),
        ] + table_style_common))
        elements.append(t3)

    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph("3.2 Gelir Tahmini", styles["AltBaslik"]))
    if gelir:
        gel_data = [["Kalem", "Tutar"]]
        for k, v in gelir.items():
            gel_data.append([str(k), str(v)])
        t4 = Table(gel_data, colWidths=[10 * cm, 6 * cm])
        t4.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#4CAF50")),
            ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [HexColor("#F1F8E9"), HexColor("#FFFFFF")]),
        ] + table_style_common))
        elements.append(t4)

    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph("3.3 K\u00e2r / Zarar \u00d6zeti",
                              styles["AltBaslik"]))
    if fizibilite:
        fiz_data = [["Kalem", "De\u011fer"]]
        for k, v in fizibilite.items():
            fiz_data.append([str(k), str(v)])
        t5 = Table(fiz_data, colWidths=[10 * cm, 6 * cm])
        t5.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#FF9800")),
            ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [HexColor("#FFF8E1"), HexColor("#FFFFFF")]),
        ] + table_style_common))
        elements.append(t5)

    # ── Grafik görselleri ──
    if chart_image_paths:
        elements.append(Spacer(1, 0.5 * cm))
        for chart_path in chart_image_paths:
            if os.path.exists(chart_path):
                try:
                    img = Image(chart_path, width=14 * cm, height=8 * cm)
                    img.hAlign = "CENTER"
                    elements.append(img)
                    elements.append(Spacer(1, 0.3 * cm))
                except Exception as e:
                    logger.warning(f"Grafik eklenemedi: {e}")

    # ══════════════════════════════════════════════════
    # EK ANALIZLER
    # ══════════════════════════════════════════════════
    if deprem:
        elements.append(PageBreak())
        elements.append(Paragraph("4. DEPREM R\u0130SK ANAL\u0130Z\u0130",
                                  styles["BolumBaslik"]))
        dep_data = [["Parametre", "De\u011fer"]]
        for k, v in deprem.items():
            dep_data.append([str(k), str(v)])
        t6 = Table(dep_data, colWidths=[10 * cm, 6 * cm])
        t6.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#795548")),
            ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ] + table_style_common))
        elements.append(t6)

    if enerji:
        elements.append(Spacer(1, 1 * cm))
        elements.append(Paragraph("5. ENERJ\u0130 PERFORMANSI",
                                  styles["BolumBaslik"]))
        enj_data = [["Parametre", "De\u011fer"]]
        for k, v in enerji.items():
            enj_data.append([str(k), str(v)])
        t7 = Table(enj_data, colWidths=[10 * cm, 6 * cm])
        t7.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#009688")),
            ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ] + table_style_common))
        elements.append(t7)

    # ══════════════════════════════════════════════════
    # FOOTER
    # ══════════════════════════════════════════════════
    elements.append(Spacer(1, 2 * cm))
    elements.append(HRFlowable(width="100%", thickness=0.5,
                               color=HexColor("#999")))
    elements.append(Paragraph(
        f"Bu rapor \u0130mar Plan \u00dcretici taraf\u0131ndan "
        f"{datetime.now().strftime('%d.%m.%Y %H:%M')} tarihinde "
        f"olu\u015fturulmu\u015ftur. "
        f"T\u00fcm veriler tahmini olup kesin de\u011ferleri i\u00e7ermez.",
        ParagraphStyle("Footer", fontSize=7, fontName=font_name,
                       textColor=HexColor("#999"), alignment=TA_CENTER),
    ))

    # PDF oluştur
    try:
        doc.build(elements)
        logger.info(f"PDF rapor olusturuldu: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"PDF olusturma hatasi: {e}")
        return ""
