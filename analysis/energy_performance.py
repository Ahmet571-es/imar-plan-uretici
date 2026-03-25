"""
Enerji Performans Tahmini — Basitleştirilmiş BEP-TR hesaplama, A-G sınıfı.

İyileştirmeler:
- Soğutma enerjisi hesabı
- Pencere yönü bazlı güneş kazancı
"""

from dataclasses import dataclass, field

ENERJI_SINIFLARI = {
    "A":  {"max_kwh": 50,  "renk": "#4CAF50", "aciklama": "Cok iyi"},
    "B":  {"max_kwh": 100, "renk": "#8BC34A", "aciklama": "Iyi"},
    "C":  {"max_kwh": 150, "renk": "#CDDC39", "aciklama": "Orta"},
    "D":  {"max_kwh": 200, "renk": "#FFC107", "aciklama": "Dusuk"},
    "E":  {"max_kwh": 250, "renk": "#FF9800", "aciklama": "Kotu"},
    "F":  {"max_kwh": 300, "renk": "#FF5722", "aciklama": "Cok kotu"},
    "G":  {"max_kwh": 999, "renk": "#F44336", "aciklama": "En kotu"},
}

YALITIM_U_DEGERLERI = {
    "duvar_5cm_eps":   0.50,
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

# Güneş kazanç katsayıları (pencere yönüne göre, W/m²)
GUNES_KAZANCI_KATSAYISI = {
    "south": 180,   # Güney — kışın yüksek, yazın düşük (saçak gölgesi)
    "north": 40,    # Kuzey — çok düşük
    "east":  120,   # Doğu — sabah güneşi
    "west":  140,   # Batı — öğleden sonra (en sıcak)
}

# Soğutma derecesi-gün katsayıları (enleme göre)
SOGUTMA_KATSAYISI = {
    "sicak":  0.65,   # Akdeniz/Güneydoğu (enlem < 37)
    "iliman": 0.35,   # İç Anadolu (37-39)
    "serin":  0.15,   # Karadeniz/Doğu (39+)
}


@dataclass
class EnerjiSonucu:
    """Enerji performans sonucu — derinleştirilmiş."""
    yillik_isitma_kwh_m2: float = 0.0
    yillik_sogutma_kwh_m2: float = 0.0
    yillik_toplam_kwh_m2: float = 0.0
    enerji_sinifi: str = "C"
    yillik_enerji_maliyeti: float = 0.0
    duvar_u: float = 0.0
    pencere_u: float = 0.0
    cati_u: float = 0.0
    pencere_duvar_orani: float = 0.0
    gunes_kazanci_kwh: float = 0.0
    oneriler: list = field(default_factory=list)

    # Derinleştirilmiş analiz verileri
    havalandirma_kaybi_kwh_m2: float = 0.0
    sicak_su_kwh_m2: float = 0.0
    co2_emisyonu_kg_m2: float = 0.0
    birincil_enerji_kwh_m2: float = 0.0
    isitma_maliyet_tl: float = 0.0
    sogutma_maliyet_tl: float = 0.0
    yalitimsiz_karsilastirma_kwh_m2: float = 0.0
    tasarruf_orani: float = 0.0
    isi_kayip_dagilimi: dict = field(default_factory=dict)  # % dağılım

    def to_dict(self) -> dict:
        sinif_info = ENERJI_SINIFLARI.get(self.enerji_sinifi, {})
        return {
            "Enerji Sınıfı": f"{self.enerji_sinifi} — {sinif_info.get('aciklama', '')}",
            "Yıllık Isıtma (kWh/m²)": f"{self.yillik_isitma_kwh_m2:.0f}",
            "Yıllık Soğutma (kWh/m²)": f"{self.yillik_sogutma_kwh_m2:.0f}",
            "Havalandırma Kaybı (kWh/m²)": f"{self.havalandirma_kaybi_kwh_m2:.0f}",
            "Sıcak Su (kWh/m²)": f"{self.sicak_su_kwh_m2:.0f}",
            "Yıllık Toplam (kWh/m²)": f"{self.yillik_toplam_kwh_m2:.0f}",
            "Birincil Enerji (kWh/m²)": f"{self.birincil_enerji_kwh_m2:.0f}",
            "CO₂ Emisyonu (kg/m²/yıl)": f"{self.co2_emisyonu_kg_m2:.1f}",
            "Isıtma Maliyeti (₺/yıl)": f"{self.isitma_maliyet_tl:,.0f}",
            "Soğutma Maliyeti (₺/yıl)": f"{self.sogutma_maliyet_tl:,.0f}",
            "Toplam Maliyet (₺/yıl)": f"{self.yillik_enerji_maliyeti:,.0f}",
            "Yalıtımsız Baz (kWh/m²)": f"{self.yalitimsiz_karsilastirma_kwh_m2:.0f}",
            "Tasarruf Oranı": f"{self.tasarruf_orani:.0%}",
            "Duvar U (W/m²K)": f"{self.duvar_u:.2f}",
            "Pencere U (W/m²K)": f"{self.pencere_u:.2f}",
            "Çatı U (W/m²K)": f"{self.cati_u:.2f}",
            "Pencere/Duvar Oranı": f"{self.pencere_duvar_orani:.0%}",
            "Güneş Kazancı (kWh/yıl)": f"{self.gunes_kazanci_kwh:.0f}",
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
    dogalgaz_birim_fiyat: float = 3.50,
    pencere_yonleri: dict | None = None,
) -> EnerjiSonucu:
    """Basitleştirilmiş enerji performans hesabı.

    Args:
        pencere_yonleri: Her yöndeki pencere alanı oranı.
            Örn: {"south": 0.4, "north": 0.1, "east": 0.25, "west": 0.25}
    """
    sonuc = EnerjiSonucu()

    # U-değerleri
    sonuc.duvar_u = YALITIM_U_DEGERLERI.get(duvar_yalitim, 0.50)
    sonuc.pencere_u = PENCERE_U_DEGERLERI.get(pencere_tipi, 2.60)
    sonuc.cati_u = YALITIM_U_DEGERLERI[
        "cati_yalitimli" if cati_yalitimli else "cati_yalitimsiz"]
    sonuc.pencere_duvar_orani = pencere_duvar_orani

    # Isıtma derecesi-gün (HDD)
    hdd = _estimate_hdd(latitude)

    # Soğutma derecesi-gün (CDD)
    cdd = _estimate_cdd(latitude)

    # Duvar alanı
    cevre_uzunlugu = 4 * (toplam_alan / kat_sayisi) ** 0.5
    duvar_alani = cevre_uzunlugu * 2.60 * kat_sayisi
    pencere_alani = duvar_alani * pencere_duvar_orani
    opak_duvar_alani = duvar_alani - pencere_alani
    cati_alani = toplam_alan / kat_sayisi

    # Isı kaybı (W/K)
    q_duvar = opak_duvar_alani * sonuc.duvar_u
    q_pencere = pencere_alani * sonuc.pencere_u
    q_cati = cati_alani * sonuc.cati_u
    q_toplam = q_duvar + q_pencere + q_cati

    # Güneş kazancı hesabı
    if pencere_yonleri is None:
        pencere_yonleri = {
            "south": 0.35, "north": 0.15,
            "east": 0.25, "west": 0.25,
        }

    gunes_kazanci_toplam = 0.0
    for yon, oran in pencere_yonleri.items():
        yon_pencere_alani = pencere_alani * oran
        g_katsayi = GUNES_KAZANCI_KATSAYISI.get(yon, 100)
        # SHGC (Solar Heat Gain Coefficient)
        shgc = 0.40 if pencere_tipi == "low_e" else 0.60
        gunes_kazanci_toplam += yon_pencere_alani * g_katsayi * shgc / 1000
    sonuc.gunes_kazanci_kwh = gunes_kazanci_toplam * 180  # ~180 güneşli gün

    # Yıllık ısıtma enerjisi (kWh)
    yillik_isitma = (q_toplam * hdd * 24 / 1000
                     - sonuc.gunes_kazanci_kwh * 0.3)  # Kış güneş kazancı
    yillik_isitma = max(0, yillik_isitma)
    sonuc.yillik_isitma_kwh_m2 = yillik_isitma / toplam_alan

    # Yıllık soğutma enerjisi (kWh)
    sogutma_katsayi = _get_sogutma_katsayi(latitude)
    yillik_sogutma = (q_toplam * cdd * 24 / 1000
                      + sonuc.gunes_kazanci_kwh * 0.5)
    yillik_sogutma *= sogutma_katsayi
    sonuc.yillik_sogutma_kwh_m2 = max(0, yillik_sogutma / toplam_alan)

    # Isıtma sistemi verimi
    verim = {"dogalgaz_kombi": 0.92, "merkezi": 0.85, "isi_pompasi": 3.0}
    sistem_verim = verim.get(isitma_sistemi, 0.90)
    sonuc.yillik_isitma_kwh_m2 /= sistem_verim

    # Soğutma COP (inverter klima)
    sogutma_cop = 3.5
    sonuc.yillik_sogutma_kwh_m2 /= sogutma_cop

    # Toplam
    sonuc.yillik_toplam_kwh_m2 = (sonuc.yillik_isitma_kwh_m2
                                   + sonuc.yillik_sogutma_kwh_m2)

    # Enerji sınıfı (toplam üzerinden)
    for sinif, info in ENERJI_SINIFLARI.items():
        if sonuc.yillik_toplam_kwh_m2 <= info["max_kwh"]:
            sonuc.enerji_sinifi = sinif
            break

    # Yıllık maliyet
    kwh_per_m3 = 10.64
    yillik_m3 = (sonuc.yillik_isitma_kwh_m2 * toplam_alan) / kwh_per_m3
    isitma_maliyet = yillik_m3 * dogalgaz_birim_fiyat
    # Soğutma elektrik maliyeti
    elektrik_fiyat = 4.50  # TL/kWh
    sogutma_maliyet = (sonuc.yillik_sogutma_kwh_m2
                       * toplam_alan * elektrik_fiyat)
    sonuc.yillik_enerji_maliyeti = isitma_maliyet + sogutma_maliyet

    # ── Havalandırma / İnfiltrasyon kaybı ──
    # 0.5 ACH (hava değişimi/saat) × hacim × 0.33 (W·h/m³·K) × HDD × 24 / 1000
    kat_yuksekligi = 2.60
    bina_hacmi = toplam_alan * kat_yuksekligi
    ach = 0.5  # Hava değişimi oranı (düşük infiltrasyon)
    havalandirma_kaybi = ach * bina_hacmi * 0.33 * hdd * 24 / 1000
    sonuc.havalandirma_kaybi_kwh_m2 = havalandirma_kaybi / toplam_alan

    # ── Sıcak su (DHW) ──
    # 50 litre/kişi/gün, 4 kişi/daire varsayımı, ΔT=35°C, 365 gün
    daire_sayisi = max(1, toplam_alan // 120)
    kisi_sayisi = daire_sayisi * 3.5
    sicak_su_kwh = kisi_sayisi * 50 * 4.186 * 35 * 365 / (3600 * 1000)
    sonuc.sicak_su_kwh_m2 = sicak_su_kwh / toplam_alan

    # Toplam (sıcak su ve havalandırma dahil)
    sonuc.yillik_toplam_kwh_m2 = (sonuc.yillik_isitma_kwh_m2
                                   + sonuc.yillik_sogutma_kwh_m2
                                   + sonuc.havalandirma_kaybi_kwh_m2 * 0.3  # Kısmen geri kazanım
                                   + sonuc.sicak_su_kwh_m2)

    # ── CO₂ emisyonu ──
    # Doğalgaz: 0.20 kg CO₂/kWh, Elektrik: 0.47 kg CO₂/kWh (TR şebekesi)
    gaz_kwh = sonuc.yillik_isitma_kwh_m2 + sonuc.sicak_su_kwh_m2
    elek_kwh = sonuc.yillik_sogutma_kwh_m2
    sonuc.co2_emisyonu_kg_m2 = gaz_kwh * 0.20 + elek_kwh * 0.47

    # ── Birincil enerji ──
    # Doğalgaz çevirme faktörü: 1.0, Elektrik: 2.36
    sonuc.birincil_enerji_kwh_m2 = gaz_kwh * 1.0 + elek_kwh * 2.36

    # ── Yalıtımsız baz ile karşılaştırma ──
    baz_u_duvar = 1.50  # Yalıtımsız tuğla duvar
    baz_u_pencere = 5.80  # Tek cam
    baz_q = (opak_duvar_alani * baz_u_duvar + pencere_alani * baz_u_pencere
             + cati_alani * 1.50)
    baz_isitma = max(0, baz_q * hdd * 24 / 1000) / toplam_alan / 0.85
    sonuc.yalitimsiz_karsilastirma_kwh_m2 = baz_isitma + sonuc.yillik_sogutma_kwh_m2 * 1.3
    if sonuc.yalitimsiz_karsilastirma_kwh_m2 > 0:
        sonuc.tasarruf_orani = 1 - sonuc.yillik_toplam_kwh_m2 / sonuc.yalitimsiz_karsilastirma_kwh_m2
    sonuc.tasarruf_orani = max(0, min(1, sonuc.tasarruf_orani))

    # ── Isı kaybı dağılımı ──
    toplam_kayip = q_duvar + q_pencere + q_cati + max(havalandirma_kaybi / (hdd * 24 / 1000 + 1e-6), 0)
    if toplam_kayip > 0:
        sonuc.isi_kayip_dagilimi = {
            "Duvar": f"{q_duvar / toplam_kayip * 100:.0f}%",
            "Pencere": f"{q_pencere / toplam_kayip * 100:.0f}%",
            "Çatı": f"{q_cati / toplam_kayip * 100:.0f}%",
            "Havalandırma": f"{max(0, 100 - q_duvar / toplam_kayip * 100 - q_pencere / toplam_kayip * 100 - q_cati / toplam_kayip * 100):.0f}%",
        }

    # Enerji sınıfı (güncellenmiş toplam üzerinden)
    for sinif, info in ENERJI_SINIFLARI.items():
        if sonuc.yillik_toplam_kwh_m2 <= info["max_kwh"]:
            sonuc.enerji_sinifi = sinif
            break

    # ── Maliyet detayı ──
    kwh_per_m3 = 10.64
    yillik_m3 = (sonuc.yillik_isitma_kwh_m2 * toplam_alan) / kwh_per_m3
    sonuc.isitma_maliyet_tl = yillik_m3 * dogalgaz_birim_fiyat
    elektrik_fiyat = 4.50
    sonuc.sogutma_maliyet_tl = sonuc.yillik_sogutma_kwh_m2 * toplam_alan * elektrik_fiyat
    sonuc.yillik_enerji_maliyeti = sonuc.isitma_maliyet_tl + sonuc.sogutma_maliyet_tl

    # Öneriler
    sonuc.oneriler = _generate_energy_recommendations(
        sonuc, duvar_yalitim, pencere_tipi, cati_yalitimli, pencere_yonleri
    )

    return sonuc


def _estimate_hdd(latitude: float) -> float:
    """Enlem bazlı ısıtma derecesi-gün tahmini."""
    if latitude >= 41:
        return 2800
    elif latitude >= 39:
        return 2400
    elif latitude >= 37:
        return 1800
    else:
        return 1200


def _estimate_cdd(latitude: float) -> float:
    """Enlem bazlı soğutma derecesi-gün tahmini."""
    if latitude < 37:
        return 800   # Akdeniz/Güneydoğu
    elif latitude < 39:
        return 500   # İç Anadolu
    elif latitude < 41:
        return 300   # Marmara
    else:
        return 150   # Karadeniz/Doğu


def _get_sogutma_katsayi(latitude: float) -> float:
    """Soğutma yükü katsayısı."""
    if latitude < 37:
        return SOGUTMA_KATSAYISI["sicak"]
    elif latitude < 39:
        return SOGUTMA_KATSAYISI["iliman"]
    else:
        return SOGUTMA_KATSAYISI["serin"]


def _generate_energy_recommendations(sonuc, duvar_yal, pencere,
                                      cati, pencere_yonleri) -> list[str]:
    """Enerji iyileştirme önerileri."""
    recs = []

    if sonuc.enerji_sinifi in ("D", "E", "F", "G"):
        if duvar_yal == "duvar_5cm_eps":
            recs.append("Yalitim kalinligini 5cm->10cm'ye cikarmak "
                        "enerji sinifini yukseltir")
        if pencere == "cift_cam":
            recs.append("Isicam veya Low-E pencere ile %15-25 enerji "
                        "tasarrufu mumkun")
        if not cati:
            recs.append("Cati yalitimi eklemek isi kaybini %20-30 azaltir")

    if sonuc.pencere_duvar_orani > 0.35:
        recs.append("Pencere/duvar orani yuksek — gunes kirici dusunun")

    # Pencere yönü bazlı öneriler
    if pencere_yonleri:
        bati_oran = pencere_yonleri.get("west", 0)
        if bati_oran > 0.30:
            recs.append("Bati cephesindeki pencere orani yuksek — "
                        "yaz sogutma yukunu arttirir, gunes kirici onerin")

    if sonuc.yillik_sogutma_kwh_m2 > 30:
        recs.append("Sogutma enerjisi yuksek — gunes kontrol cami veya "
                    "dis gunes kirici onerin")

    recs.append(f"Tahmini yillik enerji maliyeti: "
                f"{sonuc.yillik_enerji_maliyeti:,.0f} TL")
    return recs
