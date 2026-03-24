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

    def to_dict(self) -> dict:
        return {
            "Konum": f"({self.latitude:.4f}, {self.longitude:.4f})",
            "Ss (Kisa Periyot)": f"{self.ss:.3f}",
            "S1 (1 sn Periyot)": f"{self.s1:.3f}",
            "Zemin Sinifi": (f"{self.zemin_sinifi} — "
                             f"{ZEMIN_SINIFLARI.get(self.zemin_sinifi, {}).get('aciklama', '')}"),
            "Bina Kullanim Sinifi": f"BKS-{self.bks}",
            "Bina Yukseklik Sinifi": f"BYS-{self.bys}",
            "Risk Seviyesi": self.risk_seviyesi,
            "Tasiyici Sistem Onerisi": self.tasiyici_sistem_onerisi,
            "Kolon Grid Onerisi": self.kolon_grid_onerisi,
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

    # Detaylar
    sonuc.detaylar = [
        "TBDY 2018 parametreleri kullanilmistir",
        f"Bina yuksekligi tahmini: {bina_yuk:.0f}m ({kat_sayisi} kat x 3m)",
        f"Zemin sinifi: {zemin_sinifi} ({zemin_info['aciklama']})",
        "Kesin degerler icin AFAD TDTH haritasindan sorgulanmalidir: "
        "https://tdth.afad.gov.tr/",
        "Zemin etudu raporu zorunludur",
    ]

    if sonuc.ss > 0.50:
        sonuc.detaylar.append(
            "Yuksek deprem riski — perde duvar sayisi artirilmali")
    if zemin_sinifi in ("ZD", "ZE"):
        sonuc.detaylar.append(
            "Yumusak zemin — zemin iyilestirmesi gerekebilir")

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
