"""
Fizibilite Raporu PDF Dışa Aktarma — ReportLab ile profesyonel PDF.
"""

import os
import io
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


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
    output_path: str = "fizibilite_raporu.pdf",
) -> str:
    """Fizibilite raporu PDF'i oluşturur.

    Returns:
        Oluşturulan PDF dosya yolu.
    """
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
        logger.error("reportlab kurulu değil. pip install reportlab ile kurun.")
        return ""

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2.5*cm, bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    
    # Özel stiller
    styles.add(ParagraphStyle(
        name="RaporBaslik", fontSize=22, fontName="Helvetica-Bold",
        alignment=TA_CENTER, spaceAfter=20, textColor=HexColor("#1565C0"),
    ))
    styles.add(ParagraphStyle(
        name="BolumBaslik", fontSize=14, fontName="Helvetica-Bold",
        spaceAfter=10, spaceBefore=15, textColor=HexColor("#1E88E5"),
    ))
    styles.add(ParagraphStyle(
        name="AltBaslik", fontSize=11, fontName="Helvetica-Bold",
        spaceAfter=6, spaceBefore=8,
    ))
    styles.add(ParagraphStyle(
        name="Normal_TR", fontSize=10, fontName="Helvetica",
        spaceAfter=4, leading=14,
    ))

    elements = []

    # ══════════════════════════════════════════════════
    # KAPAK SAYFASI
    # ══════════════════════════════════════════════════
    elements.append(Spacer(1, 4*cm))
    elements.append(Paragraph("FİZİBİLİTE RAPORU", styles["RaporBaslik"]))
    elements.append(Spacer(1, 1*cm))

    proje_adi = proje_bilgileri.get("proje_adi", "Konut Projesi")
    elements.append(Paragraph(proje_adi, ParagraphStyle(
        "ProjeAdi", fontSize=16, fontName="Helvetica", alignment=TA_CENTER,
        textColor=HexColor("#333"),
    )))

    elements.append(Spacer(1, 2*cm))
    elements.append(HRFlowable(width="80%", thickness=1, color=HexColor("#1E88E5")))
    elements.append(Spacer(1, 0.5*cm))

    kapak_bilgi = [
        f"Il / Ilce: {proje_bilgileri.get('il', '-')} / {proje_bilgileri.get('ilce', '-')}",
        f"Ada / Parsel: {proje_bilgileri.get('ada', '-')} / {proje_bilgileri.get('parsel', '-')}",
        f"Tarih: {datetime.now().strftime('%d.%m.%Y')}",
    ]
    for bilgi in kapak_bilgi:
        elements.append(Paragraph(bilgi, ParagraphStyle(
            "KapakBilgi", fontSize=11, fontName="Helvetica", alignment=TA_CENTER,
            spaceAfter=6,
        )))

    elements.append(PageBreak())

    # ══════════════════════════════════════════════════
    # PROJE OZETI
    # ══════════════════════════════════════════════════
    elements.append(Paragraph("1. PROJE OZETI", styles["BolumBaslik"]))

    ozet_data = [["Parametre", "Deger"]]
    for k, v in proje_bilgileri.items():
        ozet_data.append([str(k).replace("_", " ").title(), str(v)])

    t = Table(ozet_data, colWidths=[8*cm, 8*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1E88E5")),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#CCCCCC")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#F5F5F5"), HexColor("#FFFFFF")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(t)

    # ══════════════════════════════════════════════════
    # HESAPLAMA SONUCLARI
    # ══════════════════════════════════════════════════
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph("2. HESAPLAMA SONUCLARI", styles["BolumBaslik"]))

    if hesaplama:
        hesap_data = [["Kalem", "Deger"]]
        for k, v in hesaplama.items():
            hesap_data.append([str(k), str(v)])
        t2 = Table(hesap_data, colWidths=[10*cm, 6*cm])
        t2.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#4CAF50")),
            ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#CCCCCC")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#F5F5F5"), HexColor("#FFFFFF")]),
        ]))
        elements.append(t2)

    # ══════════════════════════════════════════════════
    # MALI ANALIZ
    # ══════════════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("3. MALI ANALIZ", styles["BolumBaslik"]))

    elements.append(Paragraph("3.1 Maliyet Tahmini", styles["AltBaslik"]))
    if maliyet:
        mal_data = [["Kalem", "Tutar"]]
        for k, v in maliyet.items():
            mal_data.append([str(k), str(v)])
        t3 = Table(mal_data, colWidths=[10*cm, 6*cm])
        t3.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#E53935")),
            ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#CCCCCC")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#FFF3F3"), HexColor("#FFFFFF")]),
        ]))
        elements.append(t3)

    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph("3.2 Gelir Tahmini", styles["AltBaslik"]))
    if gelir:
        gel_data = [["Kalem", "Tutar"]]
        for k, v in gelir.items():
            gel_data.append([str(k), str(v)])
        t4 = Table(gel_data, colWidths=[10*cm, 6*cm])
        t4.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#4CAF50")),
            ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#CCCCCC")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#F1F8E9"), HexColor("#FFFFFF")]),
        ]))
        elements.append(t4)

    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph("3.3 Kar / Zarar Ozeti", styles["AltBaslik"]))
    if fizibilite:
        fiz_data = [["Kalem", "Deger"]]
        for k, v in fizibilite.items():
            fiz_data.append([str(k), str(v)])
        t5 = Table(fiz_data, colWidths=[10*cm, 6*cm])
        t5.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#FF9800")),
            ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#CCCCCC")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#FFF8E1"), HexColor("#FFFFFF")]),
        ]))
        elements.append(t5)

    # ══════════════════════════════════════════════════
    # EK ANALIZLER
    # ══════════════════════════════════════════════════
    if deprem:
        elements.append(PageBreak())
        elements.append(Paragraph("4. DEPREM RISK ANALIZI", styles["BolumBaslik"]))
        dep_data = [["Parametre", "Deger"]]
        for k, v in deprem.items():
            dep_data.append([str(k), str(v)])
        t6 = Table(dep_data, colWidths=[10*cm, 6*cm])
        t6.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#795548")),
            ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#CCCCCC")),
        ]))
        elements.append(t6)

    if enerji:
        elements.append(Spacer(1, 1*cm))
        elements.append(Paragraph("5. ENERJI PERFORMANSI", styles["BolumBaslik"]))
        enj_data = [["Parametre", "Deger"]]
        for k, v in enerji.items():
            enj_data.append([str(k), str(v)])
        t7 = Table(enj_data, colWidths=[10*cm, 6*cm])
        t7.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#009688")),
            ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#CCCCCC")),
        ]))
        elements.append(t7)

    # ══════════════════════════════════════════════════
    # FOOTER
    # ══════════════════════════════════════════════════
    elements.append(Spacer(1, 2*cm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#999")))
    elements.append(Paragraph(
        f"Bu rapor Imar Plan Uretici tarafindan {datetime.now().strftime('%d.%m.%Y %H:%M')} tarihinde olusturulmustur. "
        f"Tum veriler tahmini olup kesin degerleri icermez.",
        ParagraphStyle("Footer", fontSize=7, fontName="Helvetica", textColor=HexColor("#999"), alignment=TA_CENTER),
    ))

    # PDF oluştur
    try:
        doc.build(elements)
        logger.info(f"PDF rapor oluşturuldu: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"PDF oluşturma hatası: {e}")
        return ""
