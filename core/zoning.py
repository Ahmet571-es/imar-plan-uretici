"""
İmar Hesaplama Motoru — TAKS/KAKS, çekme mesafeleri, ortak alan düşümleri.
"""

from dataclasses import dataclass, field
from shapely.geometry import Polygon

from utils.geometry_helpers import cekme_mesafesi_uygula, polygon_alan
from utils.constants import (
    MERDIVEN_EVI_ALAN,
    ASANSOR_KUYU_ALAN,
    GIRIS_HOLU_ALAN,
    SIGINAK_ORAN,
)
from config.turkish_building_codes import check_elevator_required


@dataclass
class ImarParametreleri:
    """İmar bilgileri veri sınıfı."""
    kat_adedi: int = 4
    insaat_nizami: str = "A"     # A: Ayrık, B: Bitişik, BL: Blok
    taks: float = 0.35
    kaks: float = 1.40
    on_bahce: float = 5.0
    yan_bahce: float = 3.0
    arka_bahce: float = 3.0
    bina_yuksekligi_limiti: float = 0.0   # 0 = sınır yok
    bina_derinligi_limiti: float = 0.0    # 0 = sınır yok
    asansor_zorunlu: bool = False
    siginak_gerekli: bool = False
    otopark_gerekli: bool = True
    otopark_arac_sayisi: int = 0

    def __post_init__(self):
        self.asansor_zorunlu = check_elevator_required(self.kat_adedi)
        if self.otopark_arac_sayisi == 0:
            self.otopark_arac_sayisi = 0  # kullanıcı daire sayısını girdikten sonra hesaplanacak


@dataclass
class HesaplamaSonucu:
    """Hesaplama sonuçları."""
    parsel_alani: float = 0.0
    cekme_sonrasi_alan: float = 0.0
    max_taban_alani: float = 0.0          # TAKS ile sınırlı
    toplam_insaat_alani: float = 0.0      # KAKS * parsel alanı
    kat_basi_brut_alan: float = 0.0
    merdiven_alani: float = 0.0
    asansor_alani: float = 0.0
    giris_holu_alani: float = 0.0
    siginak_alani: float = 0.0
    toplam_ortak_alan: float = 0.0
    kat_basi_net_alan: float = 0.0        # dairelere kalan alan
    cekme_polygonu: Polygon = None
    uyarilar: list = field(default_factory=list)

    def ozet_dict(self) -> dict:
        return {
            "Parsel Alanı (m²)": f"{self.parsel_alani:.2f}",
            "Çekme Sonrası Alan (m²)": f"{self.cekme_sonrasi_alan:.2f}",
            "Maks. Taban Alanı — TAKS (m²)": f"{self.max_taban_alani:.2f}",
            "Toplam İnşaat Alanı — KAKS (m²)": f"{self.toplam_insaat_alani:.2f}",
            "Kat Başı Brüt Alan (m²)": f"{self.kat_basi_brut_alan:.2f}",
            "Merdiven Evi (m²)": f"{self.merdiven_alani:.2f}",
            "Asansör Alanı (m²)": f"{self.asansor_alani:.2f}",
            "Giriş Holü (m²) [Zemin Kat]": f"{self.giris_holu_alani:.2f}",
            "Sığınak (m²)": f"{self.siginak_alani:.2f}",
            "Toplam Ortak Alan / Kat (m²)": f"{self.toplam_ortak_alan:.2f}",
            "Kat Başı Net Alan — Dairelere (m²)": f"{self.kat_basi_net_alan:.2f}",
        }


def hesapla(parsel_polygon: Polygon, imar: ImarParametreleri) -> HesaplamaSonucu:
    """Parsel geometrisi + imar parametreleri ile yapılaşma sınırlarını hesaplar.

    Returns:
        HesaplamaSonucu nesnesi.
    """
    sonuc = HesaplamaSonucu()
    sonuc.parsel_alani = polygon_alan(parsel_polygon)

    # 1. Çekme mesafelerini uygula
    cekme_poly = cekme_mesafesi_uygula(
        parsel_polygon,
        on_bahce=imar.on_bahce,
        yan_bahce=imar.yan_bahce,
        arka_bahce=imar.arka_bahce,
    )
    sonuc.cekme_polygonu = cekme_poly
    sonuc.cekme_sonrasi_alan = polygon_alan(cekme_poly)

    # 2. TAKS kontrolü — Taban Alanı
    taks_siniri = sonuc.parsel_alani * imar.taks
    sonuc.max_taban_alani = min(sonuc.cekme_sonrasi_alan, taks_siniri)

    # Uyarı: çekme sonrası alan TAKS sınırından küçükse
    if sonuc.cekme_sonrasi_alan < taks_siniri:
        sonuc.uyarilar.append(
            f"ℹ️ Çekme sonrası alan ({sonuc.cekme_sonrasi_alan:.1f} m²) TAKS sınırından "
            f"({taks_siniri:.1f} m²) küçük. Çekme mesafeleri belirleyici."
        )

    # 3. Toplam inşaat alanı — KAKS
    sonuc.toplam_insaat_alani = sonuc.parsel_alani * imar.kaks

    # 4. Kat başı brüt alan
    if imar.kat_adedi > 0:
        sonuc.kat_basi_brut_alan = sonuc.toplam_insaat_alani / imar.kat_adedi
    else:
        sonuc.kat_basi_brut_alan = 0

    # Kontrol: kat başı alan ≤ taban alanı
    if sonuc.kat_basi_brut_alan > sonuc.max_taban_alani:
        sonuc.uyarilar.append(
            f"⚠️ Kat başı brüt alan ({sonuc.kat_basi_brut_alan:.1f} m²) > "
            f"Maks. taban alanı ({sonuc.max_taban_alani:.1f} m²). "
            f"KAKS/kat oranı imar sınırlarını aşıyor."
        )
        # Düzeltme: kat başı alanı taban alanıyla sınırla
        sonuc.kat_basi_brut_alan = sonuc.max_taban_alani
        sonuc.toplam_insaat_alani = sonuc.kat_basi_brut_alan * imar.kat_adedi

    # 5. Ortak alan düşümü
    sonuc.merdiven_alani = MERDIVEN_EVI_ALAN  # ~18 m²

    if imar.asansor_zorunlu:
        sonuc.asansor_alani = ASANSOR_KUYU_ALAN  # ~7 m²
    else:
        sonuc.asansor_alani = 0.0

    sonuc.giris_holu_alani = GIRIS_HOLU_ALAN  # ~10 m² (zemin kat)

    if imar.siginak_gerekli:
        sonuc.siginak_alani = sonuc.kat_basi_brut_alan * SIGINAK_ORAN
    else:
        sonuc.siginak_alani = 0.0

    sonuc.toplam_ortak_alan = (
        sonuc.merdiven_alani
        + sonuc.asansor_alani
        + sonuc.siginak_alani
    )

    # Net kullanılabilir alan (dairelere kalan)
    sonuc.kat_basi_net_alan = sonuc.kat_basi_brut_alan - sonuc.toplam_ortak_alan
    if sonuc.kat_basi_net_alan < 0:
        sonuc.kat_basi_net_alan = 0
        sonuc.uyarilar.append("⚠️ Ortak alanlar kat brüt alanından büyük! Lütfen parametreleri kontrol edin.")

    return sonuc
