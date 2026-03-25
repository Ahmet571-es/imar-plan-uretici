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
    KAT_YUKSEKLIGI,
)
from config.turkish_building_codes import check_elevator_required

# ── Otopark Sabitleri ──
OTOPARK_ARAC_BASI_ALAN = 25.0         # Araç başı otopark alanı (m²) — manevra dahil
ORTALAMA_DAIRE_BUYUKLUGU = 90.0       # Ortalama 3+1 daire büyüklüğü (m²)
ZEMIN_KAT_GIRIS_HOLU_ORAN = 0.08     # Zemin katta giriş holü oranı (brüt alana göre)


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

    # ── Yeni alanlar ──
    bina_yuksekligi: float = 0.0
    gabari_uygun: bool = True
    otopark_alani: float = 0.0
    otopark_arac_kapasitesi: int = 0
    yapilasma_orani: float = 0.0          # çekme sonrası / parsel
    emsal_kullanim_orani: float = 0.0     # fiili KAKS / izin verilen KAKS
    cekme_mesafe_detay: dict = field(default_factory=dict)
    verimlilik_orani: float = 0.0         # net / brüt
    max_daire_sayisi_tahmini: int = 0
    kat_detaylari: list = field(default_factory=list)

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
            # ── Yeni alanlar ──
            "Bina Yüksekliği (m)": f"{self.bina_yuksekligi:.2f}",
            "Gabari Uygunluk": "Uygun" if self.gabari_uygun else "AŞIYOR",
            "Otopark Alanı (m²)": f"{self.otopark_alani:.2f}",
            "Otopark Araç Kapasitesi": f"{self.otopark_arac_kapasitesi}",
            "Yapılaşma Oranı (%)": f"{self.yapilasma_orani:.1f}",
            "Emsal Kullanım Oranı (%)": f"{self.emsal_kullanim_orani:.1f}",
            "Verimlilik Oranı (%)": f"{self.verimlilik_orani:.1f}",
            "Tahmini Maks. Daire Sayısı": f"{self.max_daire_sayisi_tahmini}",
            "Çekme Mesafe Detay": self.cekme_mesafe_detay,
            "Kat Detayları": self.kat_detaylari,
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
        + sonuc.giris_holu_alani
        + sonuc.siginak_alani
    )

    # Net kullanılabilir alan (dairelere kalan)
    sonuc.kat_basi_net_alan = sonuc.kat_basi_brut_alan - sonuc.toplam_ortak_alan
    if sonuc.kat_basi_net_alan < 0:
        sonuc.kat_basi_net_alan = 0
        sonuc.uyarilar.append("⚠️ Ortak alanlar kat brüt alanından büyük! Lütfen parametreleri kontrol edin.")

    # ═══════════════════════════════════════════════════════════════════════════
    #  GELİŞMİŞ HESAPLAMALAR
    # ═══════════════════════════════════════════════════════════════════════════

    # 6. Bina yüksekliği ve gabari kontrolü
    sonuc.bina_yuksekligi = imar.kat_adedi * KAT_YUKSEKLIGI

    if imar.bina_yuksekligi_limiti > 0:
        if sonuc.bina_yuksekligi > imar.bina_yuksekligi_limiti:
            sonuc.gabari_uygun = False
            sonuc.uyarilar.append(
                f"⚠️ Bina yüksekliği ({sonuc.bina_yuksekligi:.1f} m) gabari limitini "
                f"({imar.bina_yuksekligi_limiti:.1f} m) aşıyor! "
                f"Maks. {int(imar.bina_yuksekligi_limiti // KAT_YUKSEKLIGI)} kat yapılabilir."
            )
        else:
            sonuc.gabari_uygun = True
    else:
        sonuc.gabari_uygun = True

    # 7. Yapılaşma oranı (çekme sonrası / parsel)
    if sonuc.parsel_alani > 0:
        sonuc.yapilasma_orani = (sonuc.cekme_sonrasi_alan / sonuc.parsel_alani) * 100.0
    else:
        sonuc.yapilasma_orani = 0.0

    # 8. Emsal kullanım oranı (fiili KAKS / izin verilen KAKS)
    if imar.kaks > 0 and sonuc.parsel_alani > 0:
        fiili_kaks = sonuc.toplam_insaat_alani / sonuc.parsel_alani
        sonuc.emsal_kullanim_orani = (fiili_kaks / imar.kaks) * 100.0
    else:
        sonuc.emsal_kullanim_orani = 0.0

    # 9. Verimlilik oranı (net / brüt)
    if sonuc.kat_basi_brut_alan > 0:
        sonuc.verimlilik_orani = (sonuc.kat_basi_net_alan / sonuc.kat_basi_brut_alan) * 100.0
    else:
        sonuc.verimlilik_orani = 0.0

    if sonuc.verimlilik_orani < 60.0 and sonuc.kat_basi_brut_alan > 0:
        sonuc.uyarilar.append(
            f"ℹ️ Verimlilik oranı düşük (%{sonuc.verimlilik_orani:.1f}). "
            f"Ortak alanlar brüt alanın %{100.0 - sonuc.verimlilik_orani:.1f}'ini kaplıyor."
        )

    # 10. Tahmini maks. daire sayısı (tüm katlar toplam net alan / ortalama daire)
    toplam_net_alan = sonuc.kat_basi_net_alan * imar.kat_adedi
    if ORTALAMA_DAIRE_BUYUKLUGU > 0:
        sonuc.max_daire_sayisi_tahmini = int(toplam_net_alan // ORTALAMA_DAIRE_BUYUKLUGU)
    else:
        sonuc.max_daire_sayisi_tahmini = 0

    if sonuc.max_daire_sayisi_tahmini == 0 and imar.kat_adedi > 0:
        sonuc.uyarilar.append(
            "⚠️ Net alan ortalama bir daire için yeterli değil. "
            "Daha küçük daire tipleri (1+1, 2+1) düşünülmeli."
        )

    # 11. Otopark hesabı
    otopark_arac = imar.otopark_arac_sayisi
    if otopark_arac == 0 and imar.otopark_gerekli:
        # Yönetmelik gereği her daire için 1 araçlık otopark
        otopark_arac = max(sonuc.max_daire_sayisi_tahmini, 1)

    sonuc.otopark_arac_kapasitesi = otopark_arac
    sonuc.otopark_alani = otopark_arac * OTOPARK_ARAC_BASI_ALAN

    if imar.otopark_gerekli and sonuc.otopark_alani > 0:
        # Otopark alanı parsel alanının belirli bir oranını aşıyorsa uyar
        otopark_parsel_oran = (sonuc.otopark_alani / sonuc.parsel_alani) * 100.0 if sonuc.parsel_alani > 0 else 0
        if otopark_parsel_oran > 40.0:
            sonuc.uyarilar.append(
                f"ℹ️ Otopark alanı ({sonuc.otopark_alani:.1f} m²) parsel alanının "
                f"%{otopark_parsel_oran:.1f}'ini kaplıyor. Bodrum otopark düşünülmeli."
            )

    # 12. Çekme mesafe detayı
    sonuc.cekme_mesafe_detay = {
        "ön_bahçe_m": imar.on_bahce,
        "yan_bahçe_m": imar.yan_bahce,
        "arka_bahçe_m": imar.arka_bahce,
        "inşaat_nizamı": imar.insaat_nizami,
        "toplam_çekme_kaybı_m2": round(sonuc.parsel_alani - sonuc.cekme_sonrasi_alan, 2),
        "kayıp_oranı_%": round(
            ((sonuc.parsel_alani - sonuc.cekme_sonrasi_alan) / sonuc.parsel_alani) * 100.0, 1
        ) if sonuc.parsel_alani > 0 else 0.0,
    }

    # Bitişik nizam kontrolü — yan bahçe gereksiz
    if imar.insaat_nizami == "B" and imar.yan_bahce > 0:
        sonuc.uyarilar.append(
            "ℹ️ Bitişik nizamda yan bahçe mesafesi genellikle 0 olur. "
            "Mevcut yan bahçe değeri hesaba dahil edildi."
        )

    # 13. Kat detayları (zemin kat farklı, normal katlar standart)
    sonuc.kat_detaylari = []
    for kat_no in range(1, imar.kat_adedi + 1):
        if kat_no == 1:
            # Zemin kat — giriş holü ve sığınak düşümü uygulanır
            zemin_ortak = (
                sonuc.merdiven_alani
                + sonuc.asansor_alani
                + sonuc.giris_holu_alani
                + sonuc.siginak_alani
            )
            zemin_net = max(sonuc.kat_basi_brut_alan - zemin_ortak, 0.0)
            zemin_daire = int(zemin_net // ORTALAMA_DAIRE_BUYUKLUGU) if ORTALAMA_DAIRE_BUYUKLUGU > 0 else 0
            sonuc.kat_detaylari.append({
                "kat_no": kat_no,
                "kat_tipi": "Zemin Kat",
                "brüt_alan_m2": round(sonuc.kat_basi_brut_alan, 2),
                "ortak_alan_m2": round(zemin_ortak, 2),
                "net_alan_m2": round(zemin_net, 2),
                "tahmini_daire": zemin_daire,
                "notlar": ["Giriş holü bu katta", "Sığınak alanı bu katta"],
            })
        else:
            # Normal katlar — giriş holü ve sığınak düşümü yok
            normal_ortak = sonuc.merdiven_alani + sonuc.asansor_alani
            normal_net = max(sonuc.kat_basi_brut_alan - normal_ortak, 0.0)
            normal_daire = int(normal_net // ORTALAMA_DAIRE_BUYUKLUGU) if ORTALAMA_DAIRE_BUYUKLUGU > 0 else 0
            sonuc.kat_detaylari.append({
                "kat_no": kat_no,
                "kat_tipi": "Normal Kat",
                "brüt_alan_m2": round(sonuc.kat_basi_brut_alan, 2),
                "ortak_alan_m2": round(normal_ortak, 2),
                "net_alan_m2": round(normal_net, 2),
                "tahmini_daire": normal_daire,
                "notlar": [],
            })

    # 14. Bina derinliği kontrolü
    if imar.bina_derinligi_limiti > 0 and sonuc.cekme_polygonu is not None:
        bounds = sonuc.cekme_polygonu.bounds  # (minx, miny, maxx, maxy)
        bina_derinligi_tahmini = bounds[3] - bounds[1]  # y ekseni tahmini derinlik
        if bina_derinligi_tahmini > imar.bina_derinligi_limiti:
            sonuc.uyarilar.append(
                f"⚠️ Tahmini bina derinliği ({bina_derinligi_tahmini:.1f} m) "
                f"bina derinliği limitini ({imar.bina_derinligi_limiti:.1f} m) aşabilir."
            )

    # 15. Küçük parsel uyarısı
    if sonuc.parsel_alani < 200.0:
        sonuc.uyarilar.append(
            "ℹ️ Parsel alanı oldukça küçük (< 200 m²). "
            "Çekme mesafeleri sonrası yapılaşma alanı çok kısıtlı olabilir."
        )

    # 16. KAKS / kat tutarsızlığı uyarısı
    if imar.kat_adedi > 0:
        gerekli_taks_icin_kaks = imar.kaks / imar.kat_adedi
        if gerekli_taks_icin_kaks > imar.taks:
            sonuc.uyarilar.append(
                f"ℹ️ KAKS ({imar.kaks}) / kat adedi ({imar.kat_adedi}) = "
                f"{gerekli_taks_icin_kaks:.3f} > TAKS ({imar.taks}). "
                f"Tüm emsal hakkı bu kat adediyle kullanılamaz."
            )

    return sonuc
