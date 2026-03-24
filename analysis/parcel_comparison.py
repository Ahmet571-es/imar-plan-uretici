"""
Parsel Karşılaştırma — 2-3 parseli fizibilite açısından yan yana karşılaştır.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from dataclasses import dataclass, field


@dataclass
class ParselOzet:
    """Karşılaştırma için parsel özeti."""
    isim: str = ""
    alan: float = 0.0
    taks: float = 0.0
    kaks: float = 0.0
    toplam_insaat: float = 0.0
    tahmini_maliyet: float = 0.0
    tahmini_satis: float = 0.0
    kar_marji: float = 0.0
    roi: float = 0.0
    deprem_riski: str = ""
    enerji_sinifi: str = ""
    insaat_suresi_ay: float = 0.0
    gunes_skoru: int = 0
    fiyat_trendi: str = ""


def karsilastirma_tablosu(parseller: list[ParselOzet]) -> list[dict]:
    """Karşılaştırma tablosu verileri oluşturur."""
    if not parseller:
        return []

    kriterler = [
        ("Alan (m²)", "alan", "{:.0f}"),
        ("TAKS / KAKS", None, None),
        ("Toplam İnşaat (m²)", "toplam_insaat", "{:,.0f}"),
        ("Tahmini Maliyet (₺)", "tahmini_maliyet", "{:,.0f}"),
        ("Tahmini Satış (₺)", "tahmini_satis", "{:,.0f}"),
        ("Kâr Marjı (%)", "kar_marji", "{:.1f}%"),
        ("ROI (%)", "roi", "{:.1f}%"),
        ("Deprem Riski", "deprem_riski", "{}"),
        ("Enerji Sınıfı", "enerji_sinifi", "{}"),
        ("İnşaat Süresi (ay)", "insaat_suresi_ay", "{:.0f}"),
        ("Güneş Skoru", "gunes_skoru", "{}"),
        ("Fiyat Trendi", "fiyat_trendi", "{}"),
    ]

    rows = []
    for kriter_isim, attr, fmt in kriterler:
        row = {"Kriter": kriter_isim}
        for i, p in enumerate(parseller):
            if attr is None and kriter_isim == "TAKS / KAKS":
                val = f"{p.taks} / {p.kaks}"
            elif attr:
                raw = getattr(p, attr, "")
                val = fmt.format(raw) if fmt and raw != "" else str(raw)
            else:
                val = ""
            row[p.isim or f"Parsel {i+1}"] = val
        rows.append(row)
    return rows


def create_radar_chart(parseller: list[ParselOzet]) -> go.Figure:
    """Radar chart ile parsel güçlü/zayıf yönlerini gösterir."""
    categories = ["Kârlılık", "ROI", "Alan", "Enerji", "Güneş", "Deprem\n(düşük=iyi)"]
    fig = go.Figure()

    colors = ["#1E88E5", "#E53935", "#4CAF50"]

    for i, p in enumerate(parseller):
        # Normalize (0-100)
        kar_norm = min(100, max(0, p.kar_marji * 2.5))
        roi_norm = min(100, max(0, p.roi * 2))
        alan_norm = min(100, p.alan / 10)
        enerji_map = {"A": 100, "B": 85, "C": 70, "D": 50, "E": 30, "F": 15, "G": 5}
        enerji_norm = enerji_map.get(p.enerji_sinifi, 50)
        gunes_norm = min(100, p.gunes_skoru * 10) if p.gunes_skoru else 50
        deprem_map = {"Düşük": 90, "Orta": 60, "Yüksek": 30, "Çok Yüksek": 10}
        deprem_norm = 50
        for k, v in deprem_map.items():
            if k in p.deprem_riski:
                deprem_norm = v
                break

        values = [kar_norm, roi_norm, alan_norm, enerji_norm, gunes_norm, deprem_norm]
        values.append(values[0])  # Kapatma

        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories + [categories[0]],
            fill="toself",
            name=p.isim or f"Parsel {i+1}",
            line=dict(color=colors[i % len(colors)]),
            opacity=0.6,
        ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        title="Parsel Karşılaştırma — Radar Analiz",
        height=500,
    )
    return fig


def create_bar_comparison(parseller: list[ParselOzet]) -> go.Figure:
    """Kârlılık çubuk grafik karşılaştırması."""
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Maliyet vs Gelir (₺)", "Kâr Marjı (%)"))

    isimler = [p.isim or f"P{i+1}" for i, p in enumerate(parseller)]
    maliyetler = [p.tahmini_maliyet for p in parseller]
    gelirler = [p.tahmini_satis for p in parseller]
    marjlar = [p.kar_marji for p in parseller]

    fig.add_trace(go.Bar(name="Maliyet", x=isimler, y=maliyetler, marker_color="#E53935"), row=1, col=1)
    fig.add_trace(go.Bar(name="Gelir", x=isimler, y=gelirler, marker_color="#4CAF50"), row=1, col=1)

    bar_colors = ["#4CAF50" if m > 15 else "#FFC107" if m > 0 else "#E53935" for m in marjlar]
    fig.add_trace(go.Bar(name="Kâr Marjı", x=isimler, y=marjlar, marker_color=bar_colors,
                         text=[f"{m:.1f}%" for m in marjlar], textposition="auto"), row=1, col=2)

    fig.update_layout(height=400, showlegend=True, title_text="Parsel Fizibilite Karşılaştırması")
    return fig
