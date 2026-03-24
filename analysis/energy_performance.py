"""
Enerji Performans Tahmini — Basitleştirilmiş BEP-TR hesaplama, A-G sınıfı.
"""

from dataclasses import dataclass, field

ENERJI_SINIFLARI = {
    "A":  {"max_kwh": 50,  "renk": "#4CAF50", "aciklama": "Çok iyi"},
    "B":  {"max_kwh": 100, "renk": "#8BC34A", "aciklama": "İyi"},
    "C":  {"max_kwh": 150, "renk": "#CDDC39", "aciklama": "Orta"},
    "D":  {"max_kwh": 200, "renk": "#FFC107", "aciklama": "Düşük"},
    "E":  {"max_kwh": 250, "renk": "#FF9800", "aciklama": "Kötü"},
    "F":  {"max_kwh": 300, "renk": "#FF5722", "aciklama": "Çok kötü"},
    "G":  {"max_kwh": 999, "renk": "#F44336", "aciklama": "En kötü"},
}

YALITIM_U_DEGERLERI = {
    "duvar_5cm_eps":   0.50,  # W/m²K
    "duvar_8cm_eps":   0.35,
    "duvar_10cm_eps":  0.28,
    "duvar_12cm_xps":  0.22,
    "cati_yalitimli":  0.30,
    "cati_yalitimsiz": 1.50,
}

PENCERE_U_DEGERLERI = {
    "tek_cam":   5.80,
    "cift_cam":  3.30,
    "isicam":    2.60,
    "low_e":     1.60,
}


@dataclass
class EnerjiSonucu:
    """Enerji performans sonucu."""
    yillik_isitma_kwh_m2: float = 0.0
    enerji_sinifi: str = "C"
    yillik_enerji_maliyeti: float = 0.0
    duvar_u: float = 0.0
    pencere_u: float = 0.0
    cati_u: float = 0.0
    pencere_duvar_orani: float = 0.0
    oneriler: list = field(default_factory=list)

    def to_dict(self) -> dict:
        sinif_info = ENERJI_SINIFLARI.get(self.enerji_sinifi, {})
        return {
            "Enerji Sınıfı": f"{self.enerji_sinifi} — {sinif_info.get('aciklama', '')}",
            "Yıllık Isıtma (kWh/m²·yıl)": f"{self.yillik_isitma_kwh_m2:.0f}",
            "Yıllık Enerji Maliyeti (₺)": f"{self.yillik_enerji_maliyeti:,.0f}",
            "Duvar U-değeri (W/m²K)": f"{self.duvar_u:.2f}",
            "Pencere U-değeri (W/m²K)": f"{self.pencere_u:.2f}",
            "Çatı U-değeri (W/m²K)": f"{self.cati_u:.2f}",
            "Pencere/Duvar Oranı": f"{self.pencere_duvar_orani:.0%}",
        }


def enerji_performans_hesapla(
    toplam_alan: float,
    kat_sayisi: int = 4,
    duvar_yalitim: str = "duvar_5cm_eps",
    pencere_tipi: str = "isicam",
    cati_yalitimli: bool = True,
    pencere_duvar_orani: float = 0.25,
    isitma_sistemi: str = "dogalgaz_kombi",
    latitude: float = 39.93,
    dogalgaz_birim_fiyat: float = 3.50,  # ₺/m³
) -> EnerjiSonucu:
    """Basitleştirilmiş enerji performans hesabı.

    Args:
        toplam_alan: Toplam kullanım alanı (m²).
        duvar_yalitim: Duvar yalıtım tipi.
        pencere_tipi: Pencere tipi.
        cati_yalitimli: Çatı yalıtımı var mı.
        pencere_duvar_orani: Pencere/duvar oranı (0-1).
        isitma_sistemi: Isıtma sistemi tipi.
        latitude: Enlem (iklim bölgesi için).
        dogalgaz_birim_fiyat: Doğalgaz m³ fiyatı.
    """
    sonuc = EnerjiSonucu()

    # U-değerleri
    sonuc.duvar_u = YALITIM_U_DEGERLERI.get(duvar_yalitim, 0.50)
    sonuc.pencere_u = PENCERE_U_DEGERLERI.get(pencere_tipi, 2.60)
    sonuc.cati_u = YALITIM_U_DEGERLERI["cati_yalitimli" if cati_yalitimli else "cati_yalitimsiz"]
    sonuc.pencere_duvar_orani = pencere_duvar_orani

    # Isıtma derecesi-gün (HDD) tahmini
    hdd = _estimate_hdd(latitude)

    # Duvar alanı tahmini
    cevre_uzunlugu = 4 * (toplam_alan / kat_sayisi) ** 0.5  # Kare yaklaşımı
    duvar_alani = cevre_uzunlugu * 2.60 * kat_sayisi
    pencere_alani = duvar_alani * pencere_duvar_orani
    opak_duvar_alani = duvar_alani - pencere_alani
    cati_alani = toplam_alan / kat_sayisi

    # Isı kaybı hesabı (W/K)
    q_duvar = opak_duvar_alani * sonuc.duvar_u
    q_pencere = pencere_alani * sonuc.pencere_u
    q_cati = cati_alani * sonuc.cati_u
    q_toplam = q_duvar + q_pencere + q_cati

    # Yıllık ısıtma enerjisi (kWh)
    yillik_isitma = q_toplam * hdd * 24 / 1000  # W → kWh
    sonuc.yillik_isitma_kwh_m2 = yillik_isitma / toplam_alan

    # Isıtma sistemi verimi
    verim = {"dogalgaz_kombi": 0.92, "merkezi": 0.85, "isi_pompasi": 3.0}
    sistem_verim = verim.get(isitma_sistemi, 0.90)
    if isitma_sistemi == "isi_pompasi":
        sonuc.yillik_isitma_kwh_m2 /= sistem_verim  # COP
    else:
        sonuc.yillik_isitma_kwh_m2 /= sistem_verim

    # Enerji sınıfı
    for sinif, info in ENERJI_SINIFLARI.items():
        if sonuc.yillik_isitma_kwh_m2 <= info["max_kwh"]:
            sonuc.enerji_sinifi = sinif
            break

    # Yıllık maliyet (doğalgaz)
    kwh_per_m3 = 10.64  # 1 m³ doğalgaz ≈ 10.64 kWh
    yillik_m3 = (sonuc.yillik_isitma_kwh_m2 * toplam_alan) / kwh_per_m3
    sonuc.yillik_enerji_maliyeti = yillik_m3 * dogalgaz_birim_fiyat

    # Öneriler
    sonuc.oneriler = _generate_energy_recommendations(sonuc, duvar_yalitim, pencere_tipi, cati_yalitimli)

    return sonuc


def _estimate_hdd(latitude: float) -> float:
    """Enlem bazlı ısıtma derecesi-gün tahmini (°C·gün)."""
    if latitude >= 41:
        return 2800  # Karadeniz/Doğu
    elif latitude >= 39:
        return 2400  # İç Anadolu
    elif latitude >= 37:
        return 1800  # Akdeniz/Ege
    else:
        return 1200  # Güneydoğu


def _generate_energy_recommendations(sonuc, duvar_yal, pencere, cati) -> list[str]:
    """Enerji iyileştirme önerileri."""
    recs = []
    if sonuc.enerji_sinifi in ("D", "E", "F", "G"):
        if duvar_yal == "duvar_5cm_eps":
            recs.append("💡 Yalıtım kalınlığını 5cm→10cm'ye çıkarmak enerji sınıfını yükseltir")
        if pencere == "cift_cam":
            recs.append("💡 Isıcam veya Low-E pencere ile %15-25 enerji tasarrufu mümkün")
        if not cati:
            recs.append("💡 Çatı yalıtımı eklemek ısı kaybını %20-30 azaltır")

    if sonuc.pencere_duvar_orani > 0.35:
        recs.append("⚠️ Pencere/duvar oranı yüksek — güneş kırıcı düşünün")

    recs.append(f"📊 Tahmini yıllık enerji maliyeti: {sonuc.yillik_enerji_maliyeti:,.0f} ₺")
    return recs
