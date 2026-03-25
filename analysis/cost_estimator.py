"""
İnşaat Maliyet Tahmini — İl, kalite ve alan bazlı detaylı maliyet hesabı.
"""

from dataclasses import dataclass, field
from config.cost_defaults import (
    get_construction_cost, MALIYET_DAGILIMI, OTOPARK_MALIYETLERI, GIDER_ORANLARI,
)


# ── Alt kalem detay dağılımları ──
# Her ana kalemin alt kırılımları (ana kalem oranı içindeki yüzde)
ALT_KALEM_DAGILIMI = {
    "Kaba İnşaat (Betonarme)": {
        "Kalıp İşleri": 0.22,
        "Demir (İnşaat Çeliği)": 0.30,
        "Beton (Hazır Beton)": 0.28,
        "İşçilik (Kalıpçı & Demirci)": 0.15,
        "Vinç & Pompa Kiralama": 0.05,
    },
    "İnce İnşaat (Sıva, Boya, Döşeme)": {
        "İç Sıva": 0.18,
        "Dış Sıva": 0.10,
        "Boya & Badana": 0.14,
        "Seramik & Fayans": 0.22,
        "Laminat / Parke Döşeme": 0.16,
        "Alçı & Kartonpiyer": 0.08,
        "Kapı (İç Kapı)": 0.07,
        "Pencere (PVC/Alüminyum)": 0.05,
    },
    "Tesisat (Elektrik, Su, Doğalgaz)": {
        "Elektrik Tesisatı": 0.35,
        "Sıhhi Tesisat (Su & Kanalizasyon)": 0.30,
        "Doğalgaz Tesisatı": 0.12,
        "Kalorifer / Kombi Sistemi": 0.15,
        "Yangın Tesisatı": 0.08,
    },
    "Dış Cephe (Mantolama, Kaplama)": {
        "Isı Yalıtımı (Mantolama)": 0.50,
        "Dış Cephe Boyası": 0.20,
        "Dış Cephe Kaplaması": 0.20,
        "İskele Kurulumu": 0.10,
    },
    "Ortak Alanlar (Merdiven, Asansör)": {
        "Merdiven & Korkuluk": 0.25,
        "Asansör": 0.45,
        "Ortak Alan Döşeme": 0.15,
        "Giriş & Lobi": 0.15,
    },
    "Proje ve Harçlar": {
        "Mimari Proje": 0.35,
        "Statik Proje": 0.20,
        "Mekanik Proje": 0.15,
        "Elektrik Projesi": 0.10,
        "Zemin Etüdü": 0.10,
        "Belediye Harçları": 0.10,
    },
}

# ── Daire başı ortalama alan katsayıları (kalite → m²) ──
DAIRE_ORTALAMA_ALAN = {
    "ekonomik": 90,
    "orta": 120,
    "luks": 170,
}


@dataclass
class MaliyetSonucu:
    """Maliyet hesaplama sonucu."""
    toplam_insaat_alani: float = 0.0
    birim_maliyet: float = 0.0
    kaba_insaat_maliyeti: float = 0.0
    maliyet_kalemleri: dict = field(default_factory=dict)
    otopark_maliyeti: float = 0.0
    proje_muhendislik: float = 0.0
    ruhsat_harclar: float = 0.0
    pazarlama: float = 0.0
    beklenmedik: float = 0.0
    toplam_insaat_gideri: float = 0.0
    arsa_maliyeti: float = 0.0
    toplam_maliyet: float = 0.0

    # ── Yeni detay alanları ──
    kalem_detaylari: list = field(default_factory=list)       # detailed cost items
    birim_maliyet_m2: float = 0.0
    arsa_dahil_toplam: float = 0.0
    m2_basi_toplam_maliyet: float = 0.0
    gider_detaylari: dict = field(default_factory=dict)
    otopark_maliyet_detay: dict = field(default_factory=dict)
    maliyet_ozet_tablosu: list = field(default_factory=list)  # for display

    # ── Daire bazlı maliyet ──
    tahmini_daire_sayisi: int = 0
    daire_basi_maliyet: float = 0.0
    daire_basi_maliyet_arsa_dahil: float = 0.0
    daire_ortalama_alan: float = 0.0

    # ── Kategori bazlı toplamlar ──
    insaat_kalemleri_toplam: float = 0.0
    ek_giderler_toplam: float = 0.0
    insaat_kalemleri_yuzde: float = 0.0
    ek_giderler_yuzde: float = 0.0
    otopark_yuzde: float = 0.0
    arsa_yuzde: float = 0.0

    def to_dict(self) -> dict:
        return {
            "Toplam İnşaat Alanı (m²)": f"{self.toplam_insaat_alani:,.0f}",
            "Birim Maliyet (₺/m²)": f"{self.birim_maliyet:,.0f}",
            "Kaba İnşaat Maliyeti (₺)": f"{self.kaba_insaat_maliyeti:,.0f}",
            "Otopark Maliyeti (₺)": f"{self.otopark_maliyeti:,.0f}",
            "Proje & Mühendislik (₺)": f"{self.proje_muhendislik:,.0f}",
            "Ruhsat & Harçlar (₺)": f"{self.ruhsat_harclar:,.0f}",
            "Pazarlama (₺)": f"{self.pazarlama:,.0f}",
            "Beklenmedik Giderler (₺)": f"{self.beklenmedik:,.0f}",
            "Toplam İnşaat Gideri (₺)": f"{self.toplam_insaat_gideri:,.0f}",
            "Arsa Maliyeti (₺)": f"{self.arsa_maliyeti:,.0f}",
            "TOPLAM MALİYET (₺)": f"{self.toplam_maliyet:,.0f}",
            "Tahmini Daire Sayısı": f"{self.tahmini_daire_sayisi}",
            "Daire Başı Maliyet (₺)": f"{self.daire_basi_maliyet:,.0f}",
            "Daire Başı Maliyet - Arsa Dahil (₺)": f"{self.daire_basi_maliyet_arsa_dahil:,.0f}",
            "m² Başı Toplam Maliyet (₺/m²)": f"{self.m2_basi_toplam_maliyet:,.0f}",
        }


def hesapla_maliyet(
    toplam_insaat_alani: float,
    il: str = "Ankara",
    kalite: str = "orta",
    birim_maliyet_override: float = 0,
    arsa_maliyeti: float = 0,
    otopark_tipi: str = "acik",
    otopark_arac_sayisi: int = 0,
) -> MaliyetSonucu:
    """İnşaat maliyet tahmini hesaplar."""
    sonuc = MaliyetSonucu()
    sonuc.toplam_insaat_alani = toplam_insaat_alani
    sonuc.arsa_maliyeti = arsa_maliyeti

    # Birim maliyet
    if birim_maliyet_override > 0:
        sonuc.birim_maliyet = birim_maliyet_override
    else:
        sonuc.birim_maliyet = get_construction_cost(il, kalite)

    # Kaba inşaat maliyeti
    sonuc.kaba_insaat_maliyeti = toplam_insaat_alani * sonuc.birim_maliyet

    # ──────────────────────────────────────────────────────────────────────
    # 1) Maliyet kalemleri dağılımı + alt kalem detayları
    # ──────────────────────────────────────────────────────────────────────
    kalem_detaylari = []
    insaat_kalemleri_toplam = 0.0

    for kalem, oran in MALIYET_DAGILIMI.items():
        kalem_tutari = sonuc.kaba_insaat_maliyeti * oran
        sonuc.maliyet_kalemleri[kalem] = kalem_tutari
        insaat_kalemleri_toplam += kalem_tutari

        alt_kalemler = []
        if kalem in ALT_KALEM_DAGILIMI:
            for alt_isim, alt_oran in ALT_KALEM_DAGILIMI[kalem].items():
                alt_tutar = kalem_tutari * alt_oran
                alt_m2 = alt_tutar / toplam_insaat_alani if toplam_insaat_alani > 0 else 0
                alt_kalemler.append({
                    "isim": alt_isim,
                    "oran": alt_oran,
                    "tutar": alt_tutar,
                    "tutar_str": f"₺{alt_tutar:,.0f}",
                    "birim_m2": alt_m2,
                    "birim_m2_str": f"₺{alt_m2:,.0f}/m²",
                })

        birim_m2 = kalem_tutari / toplam_insaat_alani if toplam_insaat_alani > 0 else 0
        kalem_detaylari.append({
            "ana_kalem": kalem,
            "oran": oran,
            "oran_yuzde": f"%{oran * 100:.0f}",
            "tutar": kalem_tutari,
            "tutar_str": f"₺{kalem_tutari:,.0f}",
            "birim_m2": birim_m2,
            "birim_m2_str": f"₺{birim_m2:,.0f}/m²",
            "alt_kalemler": alt_kalemler,
            "alt_kalem_sayisi": len(alt_kalemler),
        })

    sonuc.kalem_detaylari = kalem_detaylari
    sonuc.insaat_kalemleri_toplam = insaat_kalemleri_toplam

    # ──────────────────────────────────────────────────────────────────────
    # 2) Otopark maliyeti detaylı
    # ──────────────────────────────────────────────────────────────────────
    if otopark_arac_sayisi > 0:
        otopark_info = OTOPARK_MALIYETLERI.get(otopark_tipi, OTOPARK_MALIYETLERI["acik"])
        otopark_alani = otopark_arac_sayisi * otopark_info["m2_arac"]
        sonuc.otopark_maliyeti = otopark_alani * sonuc.birim_maliyet * otopark_info["maliyet_carpan"]

        arac_basi_maliyet = sonuc.otopark_maliyeti / otopark_arac_sayisi
        sonuc.otopark_maliyet_detay = {
            "tip": otopark_tipi,
            "tip_aciklama": "Açık Otopark" if otopark_tipi == "acik" else "Kapalı Otopark",
            "arac_sayisi": otopark_arac_sayisi,
            "arac_basi_m2": otopark_info["m2_arac"],
            "toplam_alan_m2": otopark_alani,
            "maliyet_carpan": otopark_info["maliyet_carpan"],
            "birim_maliyet_m2": sonuc.birim_maliyet * otopark_info["maliyet_carpan"],
            "birim_maliyet_m2_str": f"₺{sonuc.birim_maliyet * otopark_info['maliyet_carpan']:,.0f}/m²",
            "toplam_maliyet": sonuc.otopark_maliyeti,
            "arac_basi_maliyet": arac_basi_maliyet,
            "arac_basi_maliyet_str": f"₺{arac_basi_maliyet:,.0f}/araç",
            "toplam_maliyet_str": f"₺{sonuc.otopark_maliyeti:,.0f}",
        }

    # ──────────────────────────────────────────────────────────────────────
    # 3) Ek giderler — detaylı
    # ──────────────────────────────────────────────────────────────────────
    toplam_baz = sonuc.kaba_insaat_maliyeti + sonuc.otopark_maliyeti
    sonuc.proje_muhendislik = toplam_baz * GIDER_ORANLARI["proje_muhendislik"]
    sonuc.ruhsat_harclar = toplam_baz * GIDER_ORANLARI["ruhsat_harclar"]
    sonuc.pazarlama = toplam_baz * GIDER_ORANLARI["pazarlama"]
    sonuc.beklenmedik = toplam_baz * GIDER_ORANLARI["beklenmedik"]

    sonuc.gider_detaylari = {
        "proje_muhendislik": {
            "isim": "Proje & Mühendislik",
            "oran": GIDER_ORANLARI["proje_muhendislik"],
            "oran_yuzde": f"%{GIDER_ORANLARI['proje_muhendislik'] * 100:.1f}",
            "tutar": sonuc.proje_muhendislik,
            "tutar_str": f"₺{sonuc.proje_muhendislik:,.0f}",
            "aciklama": "Mimari, statik, mekanik ve elektrik projeleri; mühendislik danışmanlığı",
            "alt_kalemler": [
                {"isim": "Mimari Proje", "oran": 0.35, "tutar": sonuc.proje_muhendislik * 0.35,
                 "tutar_str": f"₺{sonuc.proje_muhendislik * 0.35:,.0f}"},
                {"isim": "Statik Proje", "oran": 0.25, "tutar": sonuc.proje_muhendislik * 0.25,
                 "tutar_str": f"₺{sonuc.proje_muhendislik * 0.25:,.0f}"},
                {"isim": "Mekanik Proje", "oran": 0.15, "tutar": sonuc.proje_muhendislik * 0.15,
                 "tutar_str": f"₺{sonuc.proje_muhendislik * 0.15:,.0f}"},
                {"isim": "Elektrik Projesi", "oran": 0.10, "tutar": sonuc.proje_muhendislik * 0.10,
                 "tutar_str": f"₺{sonuc.proje_muhendislik * 0.10:,.0f}"},
                {"isim": "Zemin Etüdü", "oran": 0.08, "tutar": sonuc.proje_muhendislik * 0.08,
                 "tutar_str": f"₺{sonuc.proje_muhendislik * 0.08:,.0f}"},
                {"isim": "Danışmanlık & Denetim", "oran": 0.07, "tutar": sonuc.proje_muhendislik * 0.07,
                 "tutar_str": f"₺{sonuc.proje_muhendislik * 0.07:,.0f}"},
            ],
        },
        "ruhsat_harclar": {
            "isim": "Ruhsat & Harçlar",
            "oran": GIDER_ORANLARI["ruhsat_harclar"],
            "oran_yuzde": f"%{GIDER_ORANLARI['ruhsat_harclar'] * 100:.1f}",
            "tutar": sonuc.ruhsat_harclar,
            "tutar_str": f"₺{sonuc.ruhsat_harclar:,.0f}",
            "aciklama": "İnşaat ruhsatı, yapı denetim, iskan harcı, belediye harçları",
            "alt_kalemler": [
                {"isim": "İnşaat Ruhsatı", "oran": 0.30, "tutar": sonuc.ruhsat_harclar * 0.30,
                 "tutar_str": f"₺{sonuc.ruhsat_harclar * 0.30:,.0f}"},
                {"isim": "Yapı Denetim Harcı", "oran": 0.25, "tutar": sonuc.ruhsat_harclar * 0.25,
                 "tutar_str": f"₺{sonuc.ruhsat_harclar * 0.25:,.0f}"},
                {"isim": "İskan Harcı", "oran": 0.20, "tutar": sonuc.ruhsat_harclar * 0.20,
                 "tutar_str": f"₺{sonuc.ruhsat_harclar * 0.20:,.0f}"},
                {"isim": "Belediye Harçları", "oran": 0.15, "tutar": sonuc.ruhsat_harclar * 0.15,
                 "tutar_str": f"₺{sonuc.ruhsat_harclar * 0.15:,.0f}"},
                {"isim": "Diğer Resmi Harçlar", "oran": 0.10, "tutar": sonuc.ruhsat_harclar * 0.10,
                 "tutar_str": f"₺{sonuc.ruhsat_harclar * 0.10:,.0f}"},
            ],
        },
        "pazarlama": {
            "isim": "Pazarlama & Satış",
            "oran": GIDER_ORANLARI["pazarlama"],
            "oran_yuzde": f"%{GIDER_ORANLARI['pazarlama'] * 100:.1f}",
            "tutar": sonuc.pazarlama,
            "tutar_str": f"₺{sonuc.pazarlama:,.0f}",
            "aciklama": "Reklam, emlak komisyonu, maket, 3D görselleştirme",
            "alt_kalemler": [
                {"isim": "Reklam & Tanıtım", "oran": 0.30, "tutar": sonuc.pazarlama * 0.30,
                 "tutar_str": f"₺{sonuc.pazarlama * 0.30:,.0f}"},
                {"isim": "Emlak Komisyonu", "oran": 0.35, "tutar": sonuc.pazarlama * 0.35,
                 "tutar_str": f"₺{sonuc.pazarlama * 0.35:,.0f}"},
                {"isim": "Maket & 3D Görselleştirme", "oran": 0.15, "tutar": sonuc.pazarlama * 0.15,
                 "tutar_str": f"₺{sonuc.pazarlama * 0.15:,.0f}"},
                {"isim": "Satış Ofisi & Personel", "oran": 0.20, "tutar": sonuc.pazarlama * 0.20,
                 "tutar_str": f"₺{sonuc.pazarlama * 0.20:,.0f}"},
            ],
        },
        "beklenmedik": {
            "isim": "Beklenmedik Giderler",
            "oran": GIDER_ORANLARI["beklenmedik"],
            "oran_yuzde": f"%{GIDER_ORANLARI['beklenmedik'] * 100:.1f}",
            "tutar": sonuc.beklenmedik,
            "tutar_str": f"₺{sonuc.beklenmedik:,.0f}",
            "aciklama": "Fiyat artışları, ek işler, zemin sürprizleri, gecikme maliyetleri",
            "alt_kalemler": [
                {"isim": "Malzeme Fiyat Artışları", "oran": 0.35, "tutar": sonuc.beklenmedik * 0.35,
                 "tutar_str": f"₺{sonuc.beklenmedik * 0.35:,.0f}"},
                {"isim": "Ek İşler & Revizyon", "oran": 0.25, "tutar": sonuc.beklenmedik * 0.25,
                 "tutar_str": f"₺{sonuc.beklenmedik * 0.25:,.0f}"},
                {"isim": "Zemin Sürprizleri", "oran": 0.15, "tutar": sonuc.beklenmedik * 0.15,
                 "tutar_str": f"₺{sonuc.beklenmedik * 0.15:,.0f}"},
                {"isim": "Gecikme Maliyetleri", "oran": 0.15, "tutar": sonuc.beklenmedik * 0.15,
                 "tutar_str": f"₺{sonuc.beklenmedik * 0.15:,.0f}"},
                {"isim": "Diğer Beklenmedik", "oran": 0.10, "tutar": sonuc.beklenmedik * 0.10,
                 "tutar_str": f"₺{sonuc.beklenmedik * 0.10:,.0f}"},
            ],
        },
    }

    toplam_gider_kalemi = (
        sonuc.proje_muhendislik + sonuc.ruhsat_harclar +
        sonuc.pazarlama + sonuc.beklenmedik
    )
    sonuc.ek_giderler_toplam = toplam_gider_kalemi

    # ──────────────────────────────────────────────────────────────────────
    # 4) Toplamlar
    # ──────────────────────────────────────────────────────────────────────
    sonuc.toplam_insaat_gideri = (
        sonuc.kaba_insaat_maliyeti + sonuc.otopark_maliyeti +
        sonuc.proje_muhendislik + sonuc.ruhsat_harclar +
        sonuc.pazarlama + sonuc.beklenmedik
    )
    sonuc.toplam_maliyet = sonuc.toplam_insaat_gideri + sonuc.arsa_maliyeti

    # Yeni özet alanları
    sonuc.birim_maliyet_m2 = sonuc.birim_maliyet
    sonuc.arsa_dahil_toplam = sonuc.toplam_maliyet
    sonuc.m2_basi_toplam_maliyet = (
        sonuc.toplam_maliyet / toplam_insaat_alani if toplam_insaat_alani > 0 else 0
    )

    # Yüzde dağılımları
    if sonuc.toplam_maliyet > 0:
        sonuc.insaat_kalemleri_yuzde = insaat_kalemleri_toplam / sonuc.toplam_maliyet * 100
        sonuc.ek_giderler_yuzde = toplam_gider_kalemi / sonuc.toplam_maliyet * 100
        sonuc.otopark_yuzde = sonuc.otopark_maliyeti / sonuc.toplam_maliyet * 100
        sonuc.arsa_yuzde = sonuc.arsa_maliyeti / sonuc.toplam_maliyet * 100

    # ──────────────────────────────────────────────────────────────────────
    # 5) Daire başı maliyet tahmini
    # ──────────────────────────────────────────────────────────────────────
    daire_alan = DAIRE_ORTALAMA_ALAN.get(kalite, 120)
    sonuc.daire_ortalama_alan = daire_alan
    if daire_alan > 0 and toplam_insaat_alani > 0:
        # Brüt alanın ~%75'i net daire alanı (ortak alanlar çıkıyor)
        net_daire_alani = toplam_insaat_alani * 0.75
        sonuc.tahmini_daire_sayisi = max(1, int(net_daire_alani / daire_alan))
        sonuc.daire_basi_maliyet = (
            sonuc.toplam_insaat_gideri / sonuc.tahmini_daire_sayisi
        )
        sonuc.daire_basi_maliyet_arsa_dahil = (
            sonuc.toplam_maliyet / sonuc.tahmini_daire_sayisi
        )

    # ──────────────────────────────────────────────────────────────────────
    # 6) Maliyet özet tablosu — kolay görüntüleme için
    # ──────────────────────────────────────────────────────────────────────
    ozet = []

    # Genel bilgiler
    ozet.append({
        "grup": "Genel Bilgiler",
        "kalem": "Toplam İnşaat Alanı",
        "deger": f"{toplam_insaat_alani:,.0f} m²",
        "tutar": None,
    })
    ozet.append({
        "grup": "Genel Bilgiler",
        "kalem": "Birim Maliyet",
        "deger": f"₺{sonuc.birim_maliyet:,.0f}/m²",
        "tutar": None,
    })
    ozet.append({
        "grup": "Genel Bilgiler",
        "kalem": "İl / Kalite",
        "deger": f"{il} / {kalite.capitalize()}",
        "tutar": None,
    })
    ozet.append({
        "grup": "Genel Bilgiler",
        "kalem": "Tahmini Daire Sayısı",
        "deger": f"{sonuc.tahmini_daire_sayisi} adet (~{daire_alan} m²/daire)",
        "tutar": None,
    })

    # İnşaat kalemleri
    for kd in kalem_detaylari:
        ozet.append({
            "grup": "İnşaat Kalemleri",
            "kalem": kd["ana_kalem"],
            "deger": kd["oran_yuzde"],
            "tutar": kd["tutar_str"],
        })
        # Alt kalemleri de ekle
        for alt in kd["alt_kalemler"]:
            ozet.append({
                "grup": "İnşaat Kalemleri (Alt)",
                "kalem": f"  ├─ {alt['isim']}",
                "deger": f"%{alt['oran'] * 100:.0f}",
                "tutar": alt["tutar_str"],
            })

    ozet.append({
        "grup": "İnşaat Kalemleri",
        "kalem": "İnşaat Kalemleri Toplamı",
        "deger": "",
        "tutar": f"₺{sonuc.kaba_insaat_maliyeti:,.0f}",
    })

    # Otopark
    if sonuc.otopark_maliyeti > 0:
        detay = sonuc.otopark_maliyet_detay
        ozet.append({
            "grup": "Otopark",
            "kalem": detay.get("tip_aciklama", "Otopark"),
            "deger": f"{otopark_arac_sayisi} araç / {detay.get('toplam_alan_m2', 0):,.0f} m²",
            "tutar": f"₺{sonuc.otopark_maliyeti:,.0f}",
        })
        ozet.append({
            "grup": "Otopark",
            "kalem": "  ├─ Araç Başı Maliyet",
            "deger": "",
            "tutar": detay.get("arac_basi_maliyet_str", ""),
        })

    # Gider kalemleri
    for gd_key, gd in sonuc.gider_detaylari.items():
        ozet.append({
            "grup": "Ek Giderler",
            "kalem": gd["isim"],
            "deger": gd["oran_yuzde"],
            "tutar": gd["tutar_str"],
        })
        for alt in gd.get("alt_kalemler", []):
            ozet.append({
                "grup": "Ek Giderler (Alt)",
                "kalem": f"  ├─ {alt['isim']}",
                "deger": f"%{alt['oran'] * 100:.0f}",
                "tutar": alt["tutar_str"],
            })

    ozet.append({
        "grup": "Ek Giderler",
        "kalem": "Ek Giderler Toplamı",
        "deger": "",
        "tutar": f"₺{toplam_gider_kalemi:,.0f}",
    })

    # Genel toplamlar
    ozet.append({
        "grup": "TOPLAM",
        "kalem": "Toplam İnşaat Gideri (Arsa Hariç)",
        "deger": "",
        "tutar": f"₺{sonuc.toplam_insaat_gideri:,.0f}",
    })

    if arsa_maliyeti > 0:
        ozet.append({
            "grup": "TOPLAM",
            "kalem": "Arsa Maliyeti",
            "deger": f"%{sonuc.arsa_yuzde:.1f}",
            "tutar": f"₺{arsa_maliyeti:,.0f}",
        })

    ozet.append({
        "grup": "TOPLAM",
        "kalem": "GENEL TOPLAM (Arsa Dahil)",
        "deger": "",
        "tutar": f"₺{sonuc.toplam_maliyet:,.0f}",
    })

    # Birim maliyetler
    ozet.append({
        "grup": "BİRİM MALİYETLER",
        "kalem": "m² Başı İnşaat Maliyeti",
        "deger": "",
        "tutar": f"₺{sonuc.birim_maliyet:,.0f}/m²",
    })

    ozet.append({
        "grup": "BİRİM MALİYETLER",
        "kalem": "m² Başı Toplam Maliyet (Arsa Dahil)",
        "deger": "",
        "tutar": f"₺{sonuc.m2_basi_toplam_maliyet:,.0f}/m²",
    })

    # Daire bazlı
    if sonuc.tahmini_daire_sayisi > 0:
        ozet.append({
            "grup": "DAİRE BAZLI MALİYET",
            "kalem": "Daire Başı İnşaat Maliyeti",
            "deger": f"{sonuc.tahmini_daire_sayisi} daire",
            "tutar": f"₺{sonuc.daire_basi_maliyet:,.0f}",
        })
        ozet.append({
            "grup": "DAİRE BAZLI MALİYET",
            "kalem": "Daire Başı Toplam Maliyet (Arsa Dahil)",
            "deger": "",
            "tutar": f"₺{sonuc.daire_basi_maliyet_arsa_dahil:,.0f}",
        })

    # Yüzde dağılım özeti
    ozet.append({
        "grup": "YÜZDE DAĞILIM",
        "kalem": "İnşaat Kalemleri",
        "deger": f"%{sonuc.insaat_kalemleri_yuzde:.1f}",
        "tutar": f"₺{insaat_kalemleri_toplam:,.0f}",
    })
    ozet.append({
        "grup": "YÜZDE DAĞILIM",
        "kalem": "Otopark",
        "deger": f"%{sonuc.otopark_yuzde:.1f}",
        "tutar": f"₺{sonuc.otopark_maliyeti:,.0f}",
    })
    ozet.append({
        "grup": "YÜZDE DAĞILIM",
        "kalem": "Ek Giderler",
        "deger": f"%{sonuc.ek_giderler_yuzde:.1f}",
        "tutar": f"₺{toplam_gider_kalemi:,.0f}",
    })
    if arsa_maliyeti > 0:
        ozet.append({
            "grup": "YÜZDE DAĞILIM",
            "kalem": "Arsa",
            "deger": f"%{sonuc.arsa_yuzde:.1f}",
            "tutar": f"₺{arsa_maliyeti:,.0f}",
        })

    sonuc.maliyet_ozet_tablosu = ozet

    return sonuc
