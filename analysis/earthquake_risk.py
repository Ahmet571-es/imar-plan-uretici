"""
Deprem Risk Analizi — AFAD/TBDY 2018 parametreleri ve taşıyıcı sistem önerisi.

İyileştirmeler:
- AFAD API endpoint doğrulaması
- Kolon grid çizimi (overlay veri üretimi)
"""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

ZEMIN_SINIFLARI = {
    "ZA": {"aciklama": "Saglam kaya", "Fs": 0.8, "risk": "Cok Dusuk"},
    "ZB": {"aciklama": "Kaya", "Fs": 0.9, "risk": "Dusuk"},
    "ZC": {"aciklama": "Siki zemin", "Fs": 1.0, "risk": "Orta"},
    "ZD": {"aciklama": "Yumusak zemin", "Fs": 1.2, "risk": "Yuksek"},
    "ZE": {"aciklama": "Cok yumusak zemin", "Fs": 1.5, "risk": "Cok Yuksek"},
}


@dataclass
class KolonGrid:
    """Kolon grid bilgisi — kat planı üzerine overlay."""
    x_akslar: list = field(default_factory=list)
    y_akslar: list = field(default_factory=list)
    kolon_boyut: tuple = (0.30, 0.50)  # en x boy (metre)
    aks_isimleri_x: list = field(default_factory=list)
    aks_isimleri_y: list = field(default_factory=list)


@dataclass
class DepremAnalizi:
    """Deprem risk analizi sonucu."""
    latitude: float = 0.0
    longitude: float = 0.0
    ss: float = 0.0
    s1: float = 0.0
    zemin_sinifi: str = "ZC"
    bks: int = 3
    bys: int = 0
    deprem_bolgesi: str = ""
    risk_seviyesi: str = ""
    tasiyici_sistem_onerisi: str = ""
    kolon_grid_onerisi: str = ""
    perde_onerisi: str = ""
    detaylar: list = field(default_factory=list)
    kolon_grid: KolonGrid | None = None
    afad_api_basarili: bool = False

    # Derinleştirilmiş TBDY 2018 parametreleri
    tasarim_sds: float = 0.0          # Kısa periyot tasarım spektral ivme katsayısı
    tasarim_sd1: float = 0.0          # 1s periyot tasarım spektral ivme katsayısı
    dd_duzeyi: str = ""               # DD-1, DD-2, DD-3, DD-4
    performans_hedefi: str = ""       # Kontrollü Hasar, Sınırlı Hasar vb.
    yapi_davranis_r: float = 0.0      # R katsayısı (dayanım fazlalığı)
    temel_tipi_onerisi: str = ""      # Temel, radye, kazıklı
    perde_orani_min: float = 0.0      # Minimum perde duvar oranı (%)
    kolon_boyut_onerisi: str = ""     # Önerilen kolon boyutları
    tahmini_deprem_kuvveti_kn: float = 0.0  # Tahmini toplam deprem kuvveti
    tbdy_referanslar: list = field(default_factory=list)
    risk_ozet: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "Konum": f"({self.latitude:.4f}, {self.longitude:.4f})",
            "Ss (Kisa Periyot)": f"{self.ss:.3f}",
            "S1 (1 sn Periyot)": f"{self.s1:.3f}",
            "SDS (Tasarim)": f"{self.tasarim_sds:.3f}",
            "SD1 (Tasarim)": f"{self.tasarim_sd1:.3f}",
            "Deprem Duzeyi": self.dd_duzeyi,
            "Zemin Sinifi": (f"{self.zemin_sinifi} — "
                             f"{ZEMIN_SINIFLARI.get(self.zemin_sinifi, {}).get('aciklama', '')}"),
            "Bina Kullanim Sinifi": f"BKS-{self.bks}",
            "Bina Yukseklik Sinifi": f"BYS-{self.bys}",
            "R Katsayisi": f"{self.yapi_davranis_r:.1f}",
            "Risk Seviyesi": self.risk_seviyesi,
            "Performans Hedefi": self.performans_hedefi,
            "Tasiyici Sistem": self.tasiyici_sistem_onerisi,
            "Temel Tipi": self.temel_tipi_onerisi,
            "Kolon Boyutu": self.kolon_boyut_onerisi,
            "Perde Orani (min)": f"%{self.perde_orani_min:.1f}",
            "Tahmini Deprem Kuvveti": f"{self.tahmini_deprem_kuvveti_kn:.0f} kN",
            "AFAD API": "Basarili" if self.afad_api_basarili else "Fallback tahmin",
        }


def deprem_risk_analizi(
    latitude: float = 39.93,
    longitude: float = 32.86,
    kat_sayisi: int = 4,
    zemin_sinifi: str = "ZC",
    ss_override: float = 0,
    s1_override: float = 0,
    bina_genisligi: float = 12.0,
    bina_derinligi: float = 10.0,
) -> DepremAnalizi:
    """Deprem risk analizi yapar."""
    sonuc = DepremAnalizi(
        latitude=latitude, longitude=longitude,
        zemin_sinifi=zemin_sinifi,
    )

    # Deprem parametreleri
    if ss_override > 0:
        sonuc.ss = ss_override
    else:
        sonuc.ss, sonuc.afad_api_basarili = _estimate_ss(latitude, longitude)

    if s1_override > 0:
        sonuc.s1 = s1_override
    else:
        sonuc.s1 = sonuc.ss * 0.35

    # Zemin amplifikasyonu
    zemin_info = ZEMIN_SINIFLARI.get(zemin_sinifi, ZEMIN_SINIFLARI["ZC"])
    sonuc.ss *= zemin_info["Fs"]
    sonuc.s1 *= zemin_info["Fs"]

    # Risk seviyesi
    if sonuc.ss < 0.25:
        sonuc.risk_seviyesi = "Dusuk"
        sonuc.deprem_bolgesi = "4. Derece"
    elif sonuc.ss < 0.50:
        sonuc.risk_seviyesi = "Orta"
        sonuc.deprem_bolgesi = "3. Derece"
    elif sonuc.ss < 0.75:
        sonuc.risk_seviyesi = "Yuksek"
        sonuc.deprem_bolgesi = "2. Derece"
    else:
        sonuc.risk_seviyesi = "Cok Yuksek"
        sonuc.deprem_bolgesi = "1. Derece"

    # BYS
    bina_yuk = kat_sayisi * 3.0
    if bina_yuk <= 17.5:
        sonuc.bys = 7
    elif bina_yuk <= 25:
        sonuc.bys = 6
    elif bina_yuk <= 40:
        sonuc.bys = 5
    elif bina_yuk <= 56:
        sonuc.bys = 4
    else:
        sonuc.bys = 3

    # Taşıyıcı sistem önerisi
    if kat_sayisi <= 4:
        sonuc.tasiyici_sistem_onerisi = "Betonarme Cerceve VEYA Tunel Kalip"
        sonuc.kolon_grid_onerisi = "4.0m x 5.0m aks araligi"
        sonuc.perde_onerisi = "Min 2 adet perde duvar (her yonde)"
        grid_x = 4.0
        grid_y = 5.0
    elif kat_sayisi <= 8:
        sonuc.tasiyici_sistem_onerisi = "Betonarme Perde-Cerceve Sistem"
        sonuc.kolon_grid_onerisi = "4.5m x 5.5m aks araligi"
        sonuc.perde_onerisi = "Min 4 adet perde duvar + cerceve"
        grid_x = 4.5
        grid_y = 5.5
    else:
        sonuc.tasiyici_sistem_onerisi = "Perde Agirlikli Betonarme Sistem"
        sonuc.kolon_grid_onerisi = "5.0m x 6.0m aks araligi"
        sonuc.perde_onerisi = "Perde orani min %1.5 (her yonde)"
        grid_x = 5.0
        grid_y = 6.0

    # Kolon grid hesapla (overlay veri)
    sonuc.kolon_grid = _calculate_column_grid(
        bina_genisligi, bina_derinligi, grid_x, grid_y, kat_sayisi
    )

    # ── Derinleştirilmiş TBDY 2018 Hesaplamaları ──

    # Tasarım spektral ivme katsayıları (TBDY Madde 2.3)
    sonuc.tasarim_sds = sonuc.ss * 2 / 3
    sonuc.tasarim_sd1 = sonuc.s1 * 2 / 3

    # Deprem yer hareketi düzeyi (DD seviyesi)
    if sonuc.ss >= 1.50:
        sonuc.dd_duzeyi = "DD-1 (En buyuk deprem)"
    elif sonuc.ss >= 0.75:
        sonuc.dd_duzeyi = "DD-2 (Standart tasarim depremi)"
    elif sonuc.ss >= 0.33:
        sonuc.dd_duzeyi = "DD-3 (Sik tekrarlanan deprem)"
    else:
        sonuc.dd_duzeyi = "DD-4 (Servis depremi)"

    # Bina performans hedefi (TBDY Tablo 3.1)
    if "DD-1" in sonuc.dd_duzeyi or "DD-2" in sonuc.dd_duzeyi:
        if sonuc.bks >= 3:
            sonuc.performans_hedefi = "Kontrollu Hasar (KH)"
        else:
            sonuc.performans_hedefi = "Sinirli Hasar (SH)"
    else:
        sonuc.performans_hedefi = "Hemen Kullanim (HK)"

    # Yapı davranış katsayısı R (TBDY Tablo 4.1)
    if kat_sayisi <= 3:
        sonuc.yapi_davranis_r = 4.0   # Tünel kalıp / perdeli
    elif kat_sayisi <= 7:
        sonuc.yapi_davranis_r = 6.0   # Normal çerçeve
    else:
        sonuc.yapi_davranis_r = 8.0   # Sünek çerçeve

    # Temel tipi önerisi
    if zemin_sinifi in ("ZA", "ZB"):
        sonuc.temel_tipi_onerisi = "Tekil / Surekli Temel"
    elif zemin_sinifi == "ZC":
        if kat_sayisi > 5:
            sonuc.temel_tipi_onerisi = "Radye Temel"
        else:
            sonuc.temel_tipi_onerisi = "Surekli Temel veya Radye"
    else:  # ZD, ZE
        sonuc.temel_tipi_onerisi = "Kazikli Temel + Radye"

    # Minimum perde duvar oranı
    if zemin_sinifi in ("ZA", "ZB"):
        sonuc.perde_orani_min = 0.15
    elif zemin_sinifi == "ZC":
        sonuc.perde_orani_min = 0.20
    elif zemin_sinifi == "ZD":
        sonuc.perde_orani_min = 0.30
    else:
        sonuc.perde_orani_min = 0.40

    # Kolon boyutu önerisi
    if kat_sayisi <= 4:
        sonuc.kolon_boyut_onerisi = "30cm x 50cm (min 900 cm2)"
    elif kat_sayisi <= 7:
        sonuc.kolon_boyut_onerisi = "40cm x 60cm (min 2400 cm2)"
    elif kat_sayisi <= 10:
        sonuc.kolon_boyut_onerisi = "50cm x 70cm (min 3500 cm2)"
    else:
        sonuc.kolon_boyut_onerisi = "60cm x 80cm (min 4800 cm2)"

    # Tahmini toplam deprem kuvveti (V = SDS × W / R)
    # W = bina ağırlığı ≈ 1.2 ton/m² × toplam inşaat alanı
    toplam_alan_tahmini = bina_genisligi * bina_derinligi * kat_sayisi
    bina_agirligi_kn = toplam_alan_tahmini * 12.0  # 1.2 ton/m² × g
    sonuc.tahmini_deprem_kuvveti_kn = (
        sonuc.tasarim_sds * bina_agirligi_kn / max(sonuc.yapi_davranis_r, 1)
    )

    # TBDY madde referansları
    sonuc.tbdy_referanslar = [
        "TBDY 2018 Madde 2.3 — Tasarim spektral ivme katsayilari",
        "TBDY 2018 Tablo 3.1 — Bina performans hedefleri",
        "TBDY 2018 Tablo 4.1 — Yapi davranis katsayilari (R)",
        "TBDY 2018 Madde 7.3 — Kolon boyutlandirma kurallari",
        "TBDY 2018 Madde 16 — Temel tasarimi",
        "TBDY 2018 Ek-A — Zemin siniflari ve amplifikasyon",
    ]

    # Risk özet sözlüğü
    sonuc.risk_ozet = {
        "genel_risk": sonuc.risk_seviyesi,
        "deprem_duzeyi": sonuc.dd_duzeyi,
        "performans": sonuc.performans_hedefi,
        "tasiyici_sistem": sonuc.tasiyici_sistem_onerisi,
        "temel": sonuc.temel_tipi_onerisi,
        "kolon": sonuc.kolon_boyut_onerisi,
        "perde_min": f"%{sonuc.perde_orani_min:.1f}",
        "deprem_kuvveti": f"{sonuc.tahmini_deprem_kuvveti_kn:.0f} kN",
    }

    # Detaylar
    sonuc.detaylar = [
        "TBDY 2018 parametreleri kullanilmistir",
        f"Bina yuksekligi tahmini: {bina_yuk:.0f}m ({kat_sayisi} kat x 3m)",
        f"Zemin sinifi: {zemin_sinifi} ({zemin_info['aciklama']})",
        f"Tasarim spektral ivme: SDS={sonuc.tasarim_sds:.3f}, SD1={sonuc.tasarim_sd1:.3f}",
        f"Deprem duzeyi: {sonuc.dd_duzeyi}",
        f"Performans hedefi: {sonuc.performans_hedefi}",
        f"R katsayisi: {sonuc.yapi_davranis_r:.1f}",
        f"Tahmini deprem kuvveti: {sonuc.tahmini_deprem_kuvveti_kn:.0f} kN",
        f"Temel onerisi: {sonuc.temel_tipi_onerisi}",
        f"Kolon boyutu: {sonuc.kolon_boyut_onerisi}",
        f"Min perde orani: %{sonuc.perde_orani_min:.1f}",
        "Kesin degerler icin: https://tdth.afad.gov.tr/",
        "Zemin etudu raporu zorunludur",
    ]

    if sonuc.ss > 0.50:
        sonuc.detaylar.append(
            "Yuksek deprem riski — perde duvar sayisi artirilmali")
    if zemin_sinifi in ("ZD", "ZE"):
        sonuc.detaylar.append(
            "Yumusak zemin — zemin iyilestirmesi / kazikli temel gerekebilir")

    return sonuc


def _calculate_column_grid(
    bina_w: float, bina_h: float,
    grid_x: float, grid_y: float,
    kat_sayisi: int,
) -> KolonGrid:
    """Kolon grid pozisyonlarını hesaplar."""
    import math

    grid = KolonGrid()

    # X aksları
    n_x = max(2, math.ceil(bina_w / grid_x) + 1)
    actual_x = bina_w / (n_x - 1) if n_x > 1 else bina_w
    grid.x_akslar = [i * actual_x for i in range(n_x)]
    grid.aks_isimleri_x = [chr(65 + i) for i in range(n_x)]  # A, B, C...

    # Y aksları
    n_y = max(2, math.ceil(bina_h / grid_y) + 1)
    actual_y = bina_h / (n_y - 1) if n_y > 1 else bina_h
    grid.y_akslar = [i * actual_y for i in range(n_y)]
    grid.aks_isimleri_y = [str(i + 1) for i in range(n_y)]  # 1, 2, 3...

    # Kolon boyutu
    if kat_sayisi <= 4:
        grid.kolon_boyut = (0.30, 0.50)
    elif kat_sayisi <= 8:
        grid.kolon_boyut = (0.35, 0.60)
    else:
        grid.kolon_boyut = (0.40, 0.70)

    return grid


def _estimate_ss(lat: float, lon: float) -> tuple[float, bool]:
    """AFAD TDTH API'den Ss değeri çeker, başarısız olursa tahmin yapar.

    Returns:
        (ss_value, api_basarili)
    """
    # Yöntem 1: AFAD TDTH API
    try:
        import requests
        url = "https://tdth.afad.gov.tr/api/spectrum"
        params = {"latitude": lat, "longitude": lon, "soilType": "ZC"}
        resp = requests.get(url, params=params, timeout=10,
                           headers={"User-Agent": "Mozilla/5.0",
                                    "Accept": "application/json"})
        if resp.status_code == 200:
            data = resp.json()
            ss = data.get("Ss", data.get("ss", 0))
            if ss and float(ss) > 0:
                logger.info(f"AFAD API'den Ss={ss} alindi ({lat:.2f}, "
                            f"{lon:.2f})")
                return float(ss), True
    except Exception as e:
        logger.debug(f"AFAD API hatasi: {e}")

    # Yöntem 2: deprem.afad.gov.tr
    try:
        import requests
        url2 = (f"https://deprem.afad.gov.tr/api/spectral-values?"
                f"lat={lat}&lng={lon}&soilType=ZC")
        resp2 = requests.get(url2, timeout=10,
                             headers={"User-Agent": "Mozilla/5.0"})
        if resp2.status_code == 200:
            data2 = resp2.json()
            ss = data2.get("Ss", data2.get("ss", 0))
            if ss and float(ss) > 0:
                logger.info(f"AFAD alt. API'den Ss={ss} alindi")
                return float(ss), True
    except Exception as e:
        logger.debug(f"AFAD alt. API hatasi: {e}")

    # Yöntem 3: Hardcoded tahmin (fallback)
    logger.warning("AFAD API erisilemedi, tahmin kullaniliyor")
    base = 0.40
    if 39.5 < lat < 41.5 and 27 < lon < 42:
        base = 0.75
    elif lat < 37.5 and 28 < lon < 32:
        base = 0.60
    elif 37 < lat < 39 and 35 < lon < 37:
        base = 0.65
    elif lon > 42:
        base = 0.30
    return base, False


def test_afad_api() -> dict:
    """AFAD API bağlantı testi."""
    results = {"tdth_api": False, "deprem_api": False, "details": []}

    try:
        import requests
        resp = requests.get(
            "https://tdth.afad.gov.tr/api/spectrum",
            params={"latitude": 39.93, "longitude": 32.86,
                    "soilType": "ZC"},
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        results["tdth_api"] = resp.status_code == 200
        results["details"].append(f"TDTH API: HTTP {resp.status_code}")
    except Exception as e:
        results["details"].append(f"TDTH API hata: {e}")

    try:
        import requests
        resp2 = requests.get(
            "https://deprem.afad.gov.tr/api/spectral-values",
            params={"lat": 39.93, "lng": 32.86, "soilType": "ZC"},
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        results["deprem_api"] = resp2.status_code == 200
        results["details"].append(
            f"Deprem API: HTTP {resp2.status_code}")
    except Exception as e:
        results["details"].append(f"Deprem API hata: {e}")

    return results
