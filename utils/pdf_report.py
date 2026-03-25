"""
PDF Rapor Üretimi — ReportLab ile parsel bilgileri + hesaplamalar + seçilen render görselleri.
Grok Imagine entegrasyonu ile üretilen görselleri rapora ekler.
"""

import io
import logging
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
    PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)


def _register_fonts():
    """Türkçe karakter destekli font kaydet."""
    try:
        pdfmetrics.registerFont(TTFont("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
        pdfmetrics.registerFont(TTFont("DejaVu-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
        return "DejaVu", "DejaVu-Bold"
    except Exception:
        return "Helvetica", "Helvetica-Bold"


def _get_styles():
    """Rapor stilleri oluşturur."""
    font, font_bold = _register_fonts()
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "TurkishTitle",
        parent=styles["Title"],
        fontName=font_bold,
        fontSize=18,
        spaceAfter=12,
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "TurkishHeading",
        parent=styles["Heading2"],
        fontName=font_bold,
        fontSize=14,
        spaceAfter=8,
        spaceBefore=12,
    ))
    styles.add(ParagraphStyle(
        "TurkishBody",
        parent=styles["Normal"],
        fontName=font,
        fontSize=10,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        "TurkishCaption",
        parent=styles["Normal"],
        fontName=font,
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.gray,
    ))
    return styles


def generate_render_report(
    parsel_bilgileri: dict,
    imar_parametreleri: dict,
    hesaplama_sonuclari: dict,
    render_gorseller: list[dict],
    dosya_adi: str = "",
) -> bytes:
    """Render görselleri dahil PDF rapor üretir.

    Args:
        parsel_bilgileri: Parsel bilgileri dict'i (alan, koordinatlar vb.).
        imar_parametreleri: İmar parametreleri (TAKS, KAKS, çekme vb.).
        hesaplama_sonuclari: Hesaplama sonuçları (taban alanı, toplam inşaat vb.).
        render_gorseller: Seçilen render görselleri listesi
            (her biri: {image_data_b64, prompt, style, render_type}).
        dosya_adi: Opsiyonel dosya adı.

    Returns:
        PDF dosya içeriği (bytes).
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
    )

    styles = _get_styles()
    story = []

    # ── Başlık ──
    story.append(Paragraph("Imar Plan Raporu", styles["TurkishTitle"]))
    story.append(Paragraph(
        f"Olusturma Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        styles["TurkishCaption"],
    ))
    story.append(Spacer(1, 12))

    # ── Parsel Bilgileri ──
    story.append(Paragraph("1. Parsel Bilgileri", styles["TurkishHeading"]))
    parsel_data = [
        ["Parametre", "Deger"],
    ]
    for key, value in parsel_bilgileri.items():
        parsel_data.append([str(key), str(value)])

    if len(parsel_data) > 1:
        t = Table(parsel_data, colWidths=[80 * mm, 80 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E88E5")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
        ]))
        story.append(t)
    story.append(Spacer(1, 8))

    # ── İmar Parametreleri ──
    story.append(Paragraph("2. Imar Parametreleri", styles["TurkishHeading"]))
    imar_data = [["Parametre", "Deger"]]
    for key, value in imar_parametreleri.items():
        imar_data.append([str(key), str(value)])

    if len(imar_data) > 1:
        t2 = Table(imar_data, colWidths=[80 * mm, 80 * mm])
        t2.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#43A047")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
        ]))
        story.append(t2)
    story.append(Spacer(1, 8))

    # ── Hesaplama Sonuçları ──
    story.append(Paragraph("3. Hesaplama Sonuclari", styles["TurkishHeading"]))
    hesap_data = [["Parametre", "Deger"]]
    for key, value in hesaplama_sonuclari.items():
        hesap_data.append([str(key), str(value)])

    if len(hesap_data) > 1:
        t3 = Table(hesap_data, colWidths=[80 * mm, 80 * mm])
        t3.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FB8C00")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
        ]))
        story.append(t3)

    # ── AI Render Görselleri ──
    if render_gorseller:
        story.append(PageBreak())
        story.append(Paragraph("4. AI Render Gorselleri", styles["TurkishHeading"]))
        story.append(Paragraph(
            "Asagidaki gorseller Grok Imagine 1.0 (xAI) ile uretilmistir.",
            styles["TurkishBody"],
        ))
        story.append(Spacer(1, 8))

        for i, render in enumerate(render_gorseller):
            image_b64 = render.get("image_data_b64", "")
            if not image_b64:
                continue

            try:
                import base64
                img_bytes = base64.b64decode(image_b64)
                img_io = io.BytesIO(img_bytes)

                # Görsel boyutunu A4'e sığdır
                max_w = 160 * mm
                max_h = 100 * mm
                rl_img = RLImage(img_io, width=max_w, height=max_h, kind="proportional")
                story.append(rl_img)

                # Alt yazı
                stil = render.get("style", "")
                tip = render.get("render_type", "")
                caption_text = f"Gorsel {i + 1}"
                if stil:
                    caption_text += f" - {stil}"
                if tip:
                    caption_text += f" ({tip})"
                story.append(Paragraph(caption_text, styles["TurkishCaption"]))
                story.append(Spacer(1, 12))

            except Exception as e:
                logger.warning(f"Gorsel {i + 1} rapora eklenemedi: {e}")
                story.append(Paragraph(
                    f"Gorsel {i + 1} yuklenemedi.",
                    styles["TurkishBody"],
                ))

    # ── Oluştur ──
    try:
        doc.build(story)
    except Exception as e:
        logger.error(f"PDF olusturma hatasi: {e}")
        return b""

    return buffer.getvalue()
