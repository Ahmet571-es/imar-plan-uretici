"""
Güneş Analizi — Cephe bazlı güneş saati hesaplama ve optimizasyon önerisi.
Parselin enlem/boylamından güneş yolu, her cephenin yıllık güneş saati ve en iyi cephe belirlenir.
"""

import math
from dataclasses import dataclass, field


@dataclass
class SunAnalysisResult:
    """Güneş analizi sonuçları."""
    latitude: float = 0.0
    longitude: float = 0.0
    facade_sun_hours: dict = field(default_factory=dict)  # {"kuzey": X, "güney": Y, ...}
    best_facade: str = "güney"
    summer_solstice_angle: float = 0.0
    winter_solstice_angle: float = 0.0
    annual_solar_hours: float = 0.0
    recommendations: list = field(default_factory=list)

    # Derinleştirilmiş analiz verileri
    aylik_gunduz_saati: list = field(default_factory=list)  # 12 aylık gündüz saati
    aylik_gunes_saati: list = field(default_factory=list)   # 12 aylık net güneş saati (bulut dahil)
    equinox_angle: float = 0.0                              # İlkbahar/sonbahar güneş açısı
    golge_analizi: dict = field(default_factory=dict)        # Gölge uzunluk oranları
    iklim_bolgesi: str = ""                                  # Türkiye iklim bölgesi
    pasif_gunes_potansiyeli: str = ""                        # Pasif güneş enerji potansiyeli
    pv_potansiyeli_kwh_m2: float = 0.0                      # Yıllık güneş enerjisi potansiyeli (kWh/m²)


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

    # ── Güneş açıları hesaplama ──
    result.summer_solstice_angle = 90 - latitude + 23.45
    result.winter_solstice_angle = 90 - latitude - 23.45
    result.equinox_angle = 90 - latitude  # İlkbahar/sonbahar ekinoksu

    # ── Aylık gündüz ve güneş saati hesabı ──
    aylik_gunduz = []
    aylik_gunes = []
    # Her ay ortasındaki gün numarası
    ay_ortasi_gun = [15, 46, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349]
    # Aylık bulutluluk faktörleri (Türkiye ortalaması — kış daha bulutlu)
    bulut_faktorleri = [0.40, 0.42, 0.50, 0.55, 0.65, 0.72, 0.78, 0.76, 0.68, 0.55, 0.42, 0.38]

    for ay_idx, gun in enumerate(ay_ortasi_gun):
        deklinasyon = 23.45 * math.sin(math.radians(360 * (284 + gun) / 365))
        lat_rad = math.radians(latitude)
        dek_rad = math.radians(deklinasyon)
        cos_omega = -math.tan(lat_rad) * math.tan(dek_rad)
        cos_omega = max(-1.0, min(1.0, cos_omega))
        omega = math.degrees(math.acos(cos_omega))
        gunduz = 2 * omega / 15
        aylik_gunduz.append(round(gunduz, 1))
        # Ay içindeki gün sayısı
        gun_sayilari = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        aylik_gunes.append(round(gunduz * bulut_faktorleri[ay_idx] * gun_sayilari[ay_idx]))

    result.aylik_gunduz_saati = aylik_gunduz
    result.aylik_gunes_saati = aylik_gunes

    total_annual = sum(aylik_gunes)
    result.annual_solar_hours = total_annual

    # ── Cephe bazlı güneş saati (enlem bağımlı oranlar) ──
    # Enlem arttıkça güney cephe daha baskın, kuzey cephe daha az
    lat_factor = (latitude - 36) / 6  # 0 (güney TR) → 1 (kuzey TR) arasında normalize
    lat_factor = max(0, min(1, lat_factor))

    south_ratio = 0.35 + lat_factor * 0.05   # 0.35-0.40 (kuzeyde güney daha önemli)
    east_ratio = 0.22 - lat_factor * 0.02    # 0.20-0.22
    west_ratio = 0.22 - lat_factor * 0.02    # 0.20-0.22
    north_ratio = 0.10 - lat_factor * 0.04   # 0.06-0.10

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

    result.best_facade = max(result.facade_sun_hours, key=result.facade_sun_hours.get)

    # ── Gölge analizi (kış ve yaz gölge uzunluk oranları) ──
    if result.winter_solstice_angle > 0:
        golge_kis = 1 / math.tan(math.radians(result.winter_solstice_angle))
    else:
        golge_kis = 10.0
    golge_yaz = 1 / math.tan(math.radians(max(result.summer_solstice_angle, 1)))
    result.golge_analizi = {
        "kis_golge_orani": round(golge_kis, 2),
        "yaz_golge_orani": round(golge_yaz, 2),
        "kis_golge_aciklama": f"1m yükseklik → {golge_kis:.1f}m gölge (21 Aralık öğle)",
        "yaz_golge_aciklama": f"1m yükseklik → {golge_yaz:.1f}m gölge (21 Haziran öğle)",
        "bina_arasi_min": f"Kışın güneş almak için bina arası min {golge_kis * 3:.1f}m (3 kat bina)",
    }

    # ── İklim bölgesi ve pasif güneş potansiyeli ──
    if latitude < 37:
        result.iklim_bolgesi = "Akdeniz / Sıcak"
        result.pasif_gunes_potansiyeli = "Yüksek — soğutma odaklı tasarım önerilir"
    elif latitude < 39:
        result.iklim_bolgesi = "İç Anadolu / Ilıman-Kıtasal"
        result.pasif_gunes_potansiyeli = "Orta-Yüksek — dengeli ısıtma/soğutma tasarımı"
    elif latitude < 41:
        result.iklim_bolgesi = "Geçiş / Ilıman"
        result.pasif_gunes_potansiyeli = "Orta — ısıtma ağırlıklı pasif güneş tasarımı"
    else:
        result.iklim_bolgesi = "Karadeniz / Serin-Nemli"
        result.pasif_gunes_potansiyeli = "Düşük-Orta — yalıtım öncelikli tasarım"

    # PV potansiyeli tahmini (kWh/m²/yıl)
    result.pv_potansiyeli_kwh_m2 = round(total_annual * 0.85, 0)  # ~%15 verim, basitleştirilmiş

    # ── Öneriler ──
    result.recommendations = _generate_recommendations(result)

    return result


def _estimate_annual_sun_hours(latitude: float) -> float:
    """Enlem bazlı yıllık güneş saati hesabı — astronomi formülleri ile."""
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
    """Güneş analizine göre detaylı mimari öneriler oluşturur."""
    recs = []

    best = result.best_facade
    recs.append(f"✅ Salon ve balkon {best} cepheye yerleştirilmeli (yıllık {result.facade_sun_hours[best]} saat güneş)")

    # Güneş açıları detayı
    recs.append(f"☀️ Güneş açıları — Yaz: {result.summer_solstice_angle:.1f}°, Ekinoks: {result.equinox_angle:.1f}°, Kış: {result.winter_solstice_angle:.1f}°")

    if result.winter_solstice_angle < 25:
        recs.append("⚠️ Kış aylarında güneş açısı düşük — güney pencereler büyük tutulmalı, saçak çıkması kısa olmalı")

    # Gölge analizi önerisi
    golge = result.golge_analizi
    if golge:
        recs.append(f"🏢 {golge.get('bina_arasi_min', 'Hesaplanamadı')}")

    # İklim bölgesine göre detaylı öneriler
    if result.latitude > 40:
        recs.append("🌡️ Soğuk bölge — güney cephe pencere/duvar oranı min %30 önerilir")
        recs.append("🧱 Kuzey cephe pencere oranı min %15'e düşürülmeli, kalın yalıtım uygulanmalı")
    elif result.latitude < 37:
        recs.append("🌡️ Sıcak bölge — batı cephede güneş kırıcı (brise-soleil) düşünün")
        recs.append("🪟 Low-E cam önerilir (güneş ısı kazancını %40 azaltır)")
        recs.append("🌿 Güney cephede saçak çıkması min 60cm önerilir (yaz güneşini keser, kış güneşini alır)")
    else:
        recs.append("🌡️ Ilıman bölge — dengeli pencere dağılımı, güney cephe öncelikli")

    # Oda yerleşim önerileri
    recs.append(f"🧭 Yatak odaları doğu cepheye yerleştirin (sabah güneşi — {result.facade_sun_hours.get('doğu', 0)} saat/yıl)")
    recs.append(f"🍳 Mutfak kuzey/kuzeydoğu cepheye (serin kalır — {result.facade_sun_hours.get('kuzey', 0)} saat/yıl)")
    recs.append(f"🚿 Islak hacimler (banyo/WC) iç cepheye veya kuzeye yerleştirilmeli")

    # Aylık güneş durumu özeti
    if result.aylik_gunes_saati:
        en_az_ay = result.aylik_gunes_saati.index(min(result.aylik_gunes_saati))
        en_cok_ay = result.aylik_gunes_saati.index(max(result.aylik_gunes_saati))
        ay_isimleri = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                       "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        recs.append(f"📅 En güneşli ay: {ay_isimleri[en_cok_ay]} ({result.aylik_gunes_saati[en_cok_ay]} saat)")
        recs.append(f"📅 En az güneşli ay: {ay_isimleri[en_az_ay]} ({result.aylik_gunes_saati[en_az_ay]} saat)")

    # PV potansiyeli
    if result.pv_potansiyeli_kwh_m2 > 0:
        recs.append(f"⚡ Güneş paneli potansiyeli: ~{result.pv_potansiyeli_kwh_m2:.0f} kWh/m²/yıl "
                    f"(10m² panel → ~{result.pv_potansiyeli_kwh_m2 * 10 * 0.20:.0f} kWh/yıl üretim)")

    # Pasif güneş önerisi
    recs.append(f"🏠 Pasif güneş potansiyeli: {result.pasif_gunes_potansiyeli}")

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
