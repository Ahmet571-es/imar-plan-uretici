"""
Güneş Analizi — Cephe bazlı güneş saati hesaplama ve optimizasyon önerisi.
Parselin enlem/boylamından güneş yolu, her cephenin yıllık güneş saati ve en iyi cephe belirlenir.
"""

import math
from datetime import datetime, timedelta
from dataclasses import dataclass, field


@dataclass
class SunAnalysisResult:
    """Güneş analizi sonuçları."""
    latitude: float = 0.0
    longitude: float = 0.0
    facade_sun_hours: dict = field(default_factory=dict)  # {"north": X, "south": Y, ...}
    best_facade: str = "south"
    summer_solstice_angle: float = 0.0
    winter_solstice_angle: float = 0.0
    annual_solar_hours: float = 0.0
    recommendations: list = field(default_factory=list)


def analyze_sun(
    latitude: float = 39.93,  # Ankara varsayılan
    longitude: float = 32.86,
    parcel_orientation: float = 0.0,  # Parselin kuzeyden sapma açısı (derece)
) -> SunAnalysisResult:
    """Güneş analizi yapar.

    Args:
        latitude: Enlem (derece).
        longitude: Boylam (derece).
        parcel_orientation: Parselin kuzeyden sapma açısı.

    Returns:
        SunAnalysisResult nesnesi.
    """
    result = SunAnalysisResult(latitude=latitude, longitude=longitude)

    # ── Güneş açıları hesaplama (basitleştirilmiş) ──
    # Yaz gündönümü (21 Haziran) — max güneş açısı
    result.summer_solstice_angle = 90 - latitude + 23.45
    # Kış gündönümü (21 Aralık) — min güneş açısı
    result.winter_solstice_angle = 90 - latitude - 23.45

    # ── Cephe bazlı yıllık güneş saati tahmini ──
    # Basitleştirilmiş model: Türkiye enlemleri (36-42°) için
    # Yıllık toplam güneş saati: ~2600-2800 saat (Türkiye ortalaması)

    total_annual = _estimate_annual_sun_hours(latitude)
    result.annual_solar_hours = total_annual

    # Cephe bazlı dağılım (Türkiye kuzey yarımküre)
    south_ratio = 0.38   # Güney cephe en çok güneş alır
    east_ratio = 0.22    # Doğu — sabah güneşi
    west_ratio = 0.22    # Batı — öğleden sonra
    north_ratio = 0.08   # Kuzey — en az (sadece yaz aylarında dolaylı)
    # Kalan %10 yaygın ışık

    result.facade_sun_hours = {
        "güney":      round(total_annual * south_ratio),
        "doğu":       round(total_annual * east_ratio),
        "batı":       round(total_annual * west_ratio),
        "kuzey":      round(total_annual * north_ratio),
        "güneydoğu":  round(total_annual * (south_ratio + east_ratio) / 2),
        "güneybatı":  round(total_annual * (south_ratio + west_ratio) / 2),
        "kuzeydoğu":  round(total_annual * (north_ratio + east_ratio) / 2),
        "kuzeybatı":  round(total_annual * (north_ratio + west_ratio) / 2),
    }

    # En iyi cephe
    result.best_facade = max(result.facade_sun_hours, key=result.facade_sun_hours.get)

    # ── Öneriler ──
    result.recommendations = _generate_recommendations(result)

    return result


def _estimate_annual_sun_hours(latitude: float) -> float:
    """Enlem bazlı yıllık güneş saati hesabı — astronomi formülleri ile."""
    import math
    # Yıl boyunca her gün için gündüz saatini hesapla
    toplam_saat = 0
    for gun in range(1, 366):
        # Güneş deklinasyonu (Cooper denklemi)
        deklinasyon = 23.45 * math.sin(math.radians(360 * (284 + gun) / 365))
        # Gün doğumu saat açısı
        lat_rad = math.radians(latitude)
        dek_rad = math.radians(deklinasyon)
        cos_omega = -math.tan(lat_rad) * math.tan(dek_rad)
        cos_omega = max(-1.0, min(1.0, cos_omega))
        omega = math.degrees(math.acos(cos_omega))
        # Gündüz süresi (saat)
        gunduz = 2 * omega / 15
        # Bulutluluk faktörü (Türkiye ortalaması ~%55 güneşli gün)
        bulut_faktor = 0.55
        toplam_saat += gunduz * bulut_faktor

    return round(toplam_saat)


def _generate_recommendations(result: SunAnalysisResult) -> list[str]:
    """Güneş analizine göre mimari öneriler oluşturur."""
    recs = []

    best = result.best_facade
    recs.append(f"✅ Salon ve balkon {best} cepheye yerleştirilmeli (yıllık {result.facade_sun_hours[best]} saat güneş)")

    if result.winter_solstice_angle < 25:
        recs.append("⚠️ Kış aylarında güneş açısı düşük — güney pencereler büyük tutulmalı")
    
    recs.append(f"ℹ️ Yaz gündönümü güneş açısı: {result.summer_solstice_angle:.1f}°")
    recs.append(f"ℹ️ Kış gündönümü güneş açısı: {result.winter_solstice_angle:.1f}°")
    
    # Isıtma/soğutma önerisi
    if result.latitude > 40:
        recs.append("🌡️ Soğuk bölge — güney cephe pencere oranını artırın, kuzey cepheyi minimize edin")
    elif result.latitude < 37:
        recs.append("🌡️ Sıcak bölge — batı cephede güneş kırıcı (brise-soleil) düşünün")
    else:
        recs.append("🌡️ Ilıman bölge — dengeli pencere dağılımı önerilir")

    recs.append(f"🧭 Yatak odaları tercihen doğu cepheye (sabah güneşi, {result.facade_sun_hours['doğu']} saat/yıl)")
    recs.append(f"🍳 Mutfak kuzey veya kuzeydoğu cepheye (serin, {result.facade_sun_hours['kuzey']} saat/yıl)")

    return recs


def create_sun_chart(result: SunAnalysisResult):
    """Cephe bazlı güneş saati çubuk grafiği oluşturur."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    facades = ["güney", "güneydoğu", "doğu", "kuzeydoğu", "kuzey", "kuzeybatı", "batı", "güneybatı"]
    hours = [result.facade_sun_hours.get(f, 0) for f in facades]

    colors = []
    for h in hours:
        if h > 900:
            colors.append("#FF9800")
        elif h > 500:
            colors.append("#FFC107")
        else:
            colors.append("#90CAF9")

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(facades, hours, color=colors, edgecolor="#333", linewidth=0.5)

    for bar, val in zip(bars, hours):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 20,
                f"{val}", ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.set_ylabel("Yıllık Güneş Saati")
    ax.set_title(f"Cephe Bazlı Güneş Analizi — Enlem: {result.latitude:.2f}°", fontweight="bold")
    ax.set_ylim(0, max(hours) * 1.15)
    plt.xticks(rotation=30, ha="right")
    fig.tight_layout()
    return fig
