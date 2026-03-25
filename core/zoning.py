"""
İmar Hesaplama Motoru — TAKS/KAKS, çekme mesafeleri, ortak alan düşümleri.
Planlı Alanlar İmar Yönetmeliği'ne uygun hesaplama yapar.
"""

from dataclasses import dataclass, field
from shapely.geometry import Polygon

from utils.geometry_helpers import cekme_mesafesi_uygula, polygon_alan
from utils.constants import (
    MERDIVEN_EVI_ALAN,
    ASANSOR_KUYU_ALAN,
    GIRIS_HOLU_ALAN,
    SIGINAK_ORAN,
    TEKNIK_HACIM_ALAN,
    OTOPARK_ALAN_ARAC_BASI,
    KAT_YUKSEKLIGI,
    EMSAL_HARICI_MERDIVEN,
    EMSAL_HARICI_ASANSOR,
    EMSAL_HARICI_GIRIS_HOLU,
    EMSAL_HARICI_SIGINAK_ORAN,
    EMSAL_HARICI_TEKNIK_HACIM,
    EMSAL_HARICI_OTOPARK_ARAC,
    MIN_YAPILASMAYA_UYGUN_ALAN,
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
class EmsalHariciAlanlar:
    """Planlı Alanlar İmar Yönetmeliği'ne göre emsal harici alan kalemleri.

    Emsal harici (KAKS hesabına dahil edilmeyen) kalemler:
    - Sığınak alanı (tüm bina brüt alanının %5'i)
    - Otopark alanı (araç başı 25 m²)
    - Merdiven evi (her katta 18 m²)
    - Asansör kuyusu (her katta 7 m²)
    - Giriş holü (sadece zemin kat, 10 m²)
    - Teknik hacimler (elektrik, su, doğalgaz odaları — 5 m²)
    """
    merdiven_alani: float = 0.0       # Her katta merdiven evi
    asansor_alani: float = 0.0        # Her katta asansör kuyusu
    giris_holu_alani: float = 0.0     # Sadece zemin kat giriş holü
    siginak_alani: float = 0.0        # Sığınak alanı
    teknik_hacim_alani: float = 0.0   # Teknik hacimler (elektrik, su vb.)
    otopark_alani: float = 0.0        # Otopark alanı
    toplam: float = 0.0               # Toplam emsal harici alan

    def hesapla_toplam(self):
        """Toplam emsal harici alanı hesaplar."""
        self.toplam = (
            self.merdiven_alani
            + self.asansor_alani
            + self.giris_holu_alani
            + self.siginak_alani
            + self.teknik_hacim_alani
            + self.otopark_alani
        )
        return self.toplam


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
    teknik_hacim_alani: float = 0.0
    otopark_alani: float = 0.0
    toplam_ortak_alan: float = 0.0
    kat_basi_net_alan: float = 0.0        # dairelere kalan alan
    emsal_harici: EmsalHariciAlanlar = None
    bina_toplam_yukseklik: float = 0.0    # kat_adedi * KAT_YUKSEKLIGI
    cekme_polygonu: Polygon = None
    uyarilar: list = field(default_factory=list)

    def __post_init__(self):
        if self.emsal_harici is None:
            self.emsal_harici = EmsalHariciAlanlar()

    def ozet_dict(self) -> dict:
        return {
            "Parsel Alanı (m²)": f"{self.parsel_alani:.2f}",
            "Çekme Sonrası Alan (m²)": f"{self.cekme_sonrasi_alan:.2f}",
            "Maks. Taban Alanı — TAKS (m²)": f"{self.max_taban_alani:.2f}",
            "Toplam İnşaat Alanı — KAKS (m²)": f"{self.toplam_insaat_alani:.2f}",
            "Kat Başı Brüt Alan (m²)": f"{self.kat_basi_brut_alan:.2f}",
            "Bina Toplam Yükseklik (m)": f"{self.bina_toplam_yukseklik:.2f}",
            "Merdiven Evi (m²)": f"{self.merdiven_alani:.2f}",
            "Asansör Alanı (m²)": f"{self.asansor_alani:.2f}",
            "Giriş Holü (m²) [Zemin Kat]": f"{self.giris_holu_alani:.2f}",
            "Sığınak (m²)": f"{self.siginak_alani:.2f}",
            "Teknik Hacimler (m²)": f"{self.teknik_hacim_alani:.2f}",
            "Otopark Alanı (m²)": f"{self.otopark_alani:.2f}",
            "Toplam Ortak Alan / Kat (m²)": f"{self.toplam_ortak_alan:.2f}",
            "Kat Başı Net Alan — Dairelere (m²)": f"{self.kat_basi_net_alan:.2f}",
            "Emsal Harici Toplam (m²)": f"{self.emsal_harici.toplam:.2f}",
        }


def _arka_bahce_h_yari_kurali(imar: ImarParametreleri) -> float:
    """Arka bahçe mesafesi H/2 kuralı — Yönetmelik Madde 6.

    Arka bahçe 0 olarak verilmişse bina yüksekliğinin yarısı uygulanır.
    Minimum 3 metre olarak kabul edilir.
    """
    if imar.arka_bahce > 0:
        return imar.arka_bahce

    # H = kat_adedi * kat_yüksekliği
    bina_yuksekligi = imar.kat_adedi * KAT_YUKSEKLIGI
    arka_bahce = bina_yuksekligi / 2.0

    # Minimum 3 metre (Yönetmelik genel kuralı)
    return max(arka_bahce, 3.0)


def _emsal_harici_hesapla(
    imar: ImarParametreleri,
    kat_basi_brut_alan: float,
) -> EmsalHariciAlanlar:
    """Planlı Alanlar İmar Yönetmeliği'ne göre emsal harici alanları hesaplar.

    Emsal harici (KAKS dışı) kalemler:
    - Sığınak alanı (tüm bina brüt alanının %5'i)
    - Otopark alanı (araç başı 25 m²)
    - Merdiven evi (her katta 18 m²)
    - Asansör kuyusu (her katta 7 m²)
    - Giriş holü (sadece zemin kat, 10 m²)
    - Teknik hacimler (elektrik, su, doğalgaz odaları — 5 m²)
    """
    emsal = EmsalHariciAlanlar()

    # Merdiven evi — her katta emsal harici (18 m²)
    emsal.merdiven_alani = EMSAL_HARICI_MERDIVEN * imar.kat_adedi

    # Asansör kuyusu — her katta emsal harici (7 m²)
    if imar.asansor_zorunlu:
        emsal.asansor_alani = EMSAL_HARICI_ASANSOR * imar.kat_adedi
    else:
        emsal.asansor_alani = 0.0

    # Giriş holü — sadece zemin kat emsal harici (10 m²)
    emsal.giris_holu_alani = EMSAL_HARICI_GIRIS_HOLU

    # Sığınak — emsal harici (brüt alanın %5'i)
    if imar.siginak_gerekli:
        emsal.siginak_alani = kat_basi_brut_alan * EMSAL_HARICI_SIGINAK_ORAN
    else:
        emsal.siginak_alani = 0.0

    # Teknik hacimler — emsal harici (5 m²)
    emsal.teknik_hacim_alani = EMSAL_HARICI_TEKNIK_HACIM

    # Otopark — emsal harici
    if imar.otopark_gerekli and imar.otopark_arac_sayisi > 0:
        emsal.otopark_alani = imar.otopark_arac_sayisi * EMSAL_HARICI_OTOPARK_ARAC
    else:
        emsal.otopark_alani = 0.0

    emsal.hesapla_toplam()
    return emsal


def _bina_yuksekligi_kontrol(imar: ImarParametreleri, sonuc: "HesaplamaSonucu"):
    """Bina yüksekliği limiti kontrolü.

    kat_adedi * KAT_YUKSEKLIGI değerini bina_yuksekligi_limiti ile karşılaştırır.
    Limit aşılırsa maksimum kat adedini hesaplayıp uyarı ekler.
    """
    sonuc.bina_toplam_yukseklik = imar.kat_adedi * KAT_YUKSEKLIGI
    if imar.bina_yuksekligi_limiti > 0:
        if sonuc.bina_toplam_yukseklik > imar.bina_yuksekligi_limiti:
            max_kat = int(imar.bina_yuksekligi_limiti / KAT_YUKSEKLIGI)
            sonuc.uyarilar.append(
                f"Bina yuksekligi ({sonuc.bina_toplam_yukseklik:.1f} m = "
                f"{imar.kat_adedi} kat x {KAT_YUKSEKLIGI:.2f} m) "
                f"bina yuksekligi limitini ({imar.bina_yuksekligi_limiti:.1f} m) asiyor. "
                f"Maksimum {max_kat} kat yapilabilir."
            )


def hesapla(parsel_polygon: Polygon, imar: ImarParametreleri) -> HesaplamaSonucu:
    """Parsel geometrisi + imar parametreleri ile yapılaşma sınırlarını hesaplar.

    Planlı Alanlar İmar Yönetmeliği'ne uygun olarak:
    - Çekme mesafeleri uygulanır
    - TAKS/KAKS kontrolleri yapılır
    - Emsal harici alanlar düşülür (sığınak, otopark, merdiven, asansör, giriş holü, teknik hacim)
    - Bina yüksekliği limiti kontrol edilir
    - Arka bahçe H/2 kuralı uygulanır (Madde 6)

    Returns:
        HesaplamaSonucu nesnesi.
    """
    sonuc = HesaplamaSonucu()
    sonuc.parsel_alani = polygon_alan(parsel_polygon)

    # 0. Arka bahçe H/2 kuralı — Yönetmelik Madde 6
    efektif_arka_bahce = _arka_bahce_h_yari_kurali(imar)
    if imar.arka_bahce == 0 and efektif_arka_bahce > 0:
        sonuc.uyarilar.append(
            f"Arka bahce belirtilmedi. Yonetmelik Madde 6 geregi "
            f"H/2 kurali uygulandi: arka bahce = {efektif_arka_bahce:.1f} m "
            f"(H = {imar.kat_adedi} kat x {KAT_YUKSEKLIGI:.2f} m = "
            f"{imar.kat_adedi * KAT_YUKSEKLIGI:.2f} m)"
        )

    # 1. Çekme mesafelerini uygula
    cekme_poly = cekme_mesafesi_uygula(
        parsel_polygon,
        on_bahce=imar.on_bahce,
        yan_bahce=imar.yan_bahce,
        arka_bahce=efektif_arka_bahce,
    )
    sonuc.cekme_polygonu = cekme_poly
    sonuc.cekme_sonrasi_alan = polygon_alan(cekme_poly)

    # 1a. Çekme sonrası alan kontrolü — minimum yapılaşma alanı (30 m²)
    if sonuc.cekme_sonrasi_alan < MIN_YAPILASMAYA_UYGUN_ALAN:
        sonuc.uyarilar.append(
            f"Cekme sonrasi alan ({sonuc.cekme_sonrasi_alan:.1f} m2) "
            f"minimum yapilasmaya uygun alan ({MIN_YAPILASMAYA_UYGUN_ALAN:.0f} m2) "
            f"altinda. Parsel cekme mesafeleri icin cok kucuk."
        )

    # 2. TAKS kontrolü — Taban Alanı
    taks_siniri = sonuc.parsel_alani * imar.taks
    sonuc.max_taban_alani = min(sonuc.cekme_sonrasi_alan, taks_siniri)

    # Uyarı: çekme sonrası alan TAKS sınırından küçükse
    if sonuc.cekme_sonrasi_alan < taks_siniri:
        sonuc.uyarilar.append(
            f"Cekme sonrasi alan ({sonuc.cekme_sonrasi_alan:.1f} m2) TAKS sinirindan "
            f"({taks_siniri:.1f} m2) kucuk. Cekme mesafeleri belirleyici."
        )

    # 3. Toplam inşaat alanı — KAKS
    sonuc.toplam_insaat_alani = sonuc.parsel_alani * imar.kaks

    # 4. Kat başı brüt alan
    if imar.kat_adedi > 0:
        sonuc.kat_basi_brut_alan = sonuc.toplam_insaat_alani / imar.kat_adedi
    else:
        sonuc.kat_basi_brut_alan = 0

    # Kontrol: kat başı alan <= taban alanı
    if sonuc.kat_basi_brut_alan > sonuc.max_taban_alani:
        sonuc.uyarilar.append(
            f"Kat basi brut alan ({sonuc.kat_basi_brut_alan:.1f} m2) > "
            f"Maks. taban alani ({sonuc.max_taban_alani:.1f} m2). "
            f"KAKS/kat orani imar sinirlarini asiyor."
        )
        # Düzeltme: kat başı alanı taban alanıyla sınırla
        sonuc.kat_basi_brut_alan = sonuc.max_taban_alani
        sonuc.toplam_insaat_alani = sonuc.kat_basi_brut_alan * imar.kat_adedi

    # 5. Bina yüksekliği kontrolü
    _bina_yuksekligi_kontrol(imar, sonuc)

    # 6. Ortak alan düşümü (kat başı)
    sonuc.merdiven_alani = MERDIVEN_EVI_ALAN  # 18 m²

    if imar.asansor_zorunlu:
        sonuc.asansor_alani = ASANSOR_KUYU_ALAN  # 7 m²
    else:
        sonuc.asansor_alani = 0.0

    sonuc.giris_holu_alani = GIRIS_HOLU_ALAN  # 10 m² (zemin kat)

    if imar.siginak_gerekli:
        sonuc.siginak_alani = sonuc.kat_basi_brut_alan * SIGINAK_ORAN
    else:
        sonuc.siginak_alani = 0.0

    sonuc.teknik_hacim_alani = TEKNIK_HACIM_ALAN  # 5 m²

    if imar.otopark_gerekli and imar.otopark_arac_sayisi > 0:
        sonuc.otopark_alani = imar.otopark_arac_sayisi * OTOPARK_ALAN_ARAC_BASI
    else:
        sonuc.otopark_alani = 0.0

    sonuc.toplam_ortak_alan = (
        sonuc.merdiven_alani
        + sonuc.asansor_alani
        + sonuc.siginak_alani
        + sonuc.teknik_hacim_alani
    )

    # 7. Emsal harici alan hesabı — Planlı Alanlar İmar Yönetmeliği
    # Sığınak, otopark, merdiven (18m²), asansör (7m²), giriş holü (10m²),
    # teknik hacimler KAKS hesabından düşülür.
    sonuc.emsal_harici = _emsal_harici_hesapla(imar, sonuc.kat_basi_brut_alan)

    # 8. Net kullanılabilir alan (dairelere kalan)
    sonuc.kat_basi_net_alan = sonuc.kat_basi_brut_alan - sonuc.toplam_ortak_alan
    if sonuc.kat_basi_net_alan < 0:
        sonuc.kat_basi_net_alan = 0
        sonuc.uyarilar.append(
            "Ortak alanlar kat brut alanindan buyuk! Lutfen parametreleri kontrol edin."
        )

    return sonuc
