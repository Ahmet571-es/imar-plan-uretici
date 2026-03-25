"""
Yapı Ruhsatı Başvuru Paketi — Gerekli evrak listesi ve hazırlanan belgeler.
Müteahhit / Taşeron Eşleştirme.
Ruhsat detay hesaplama ve maliyet tahmini.
"""

from dataclasses import dataclass, field
from datetime import datetime


# ── Yapı Ruhsatı Kontrol Listesi ──
RUHSAT_KONTROL_LISTESI = [
    {"belge": "Tapu fotokopisi", "hazirlanabilir": False, "zorunlu": True},
    {"belge": "İmar durumu belgesi", "hazirlanabilir": False, "zorunlu": True},
    {"belge": "Mimari proje (5 takım)", "hazirlanabilir": False, "zorunlu": True, "not": "Mimar tarafından hazırlanacak"},
    {"belge": "Statik proje", "hazirlanabilir": False, "zorunlu": True},
    {"belge": "Mekanik tesisat projesi", "hazirlanabilir": False, "zorunlu": True},
    {"belge": "Elektrik projesi", "hazirlanabilir": False, "zorunlu": True},
    {"belge": "Zemin etüdü raporu", "hazirlanabilir": False, "zorunlu": True},
    {"belge": "Yapı denetim sözleşmesi", "hazirlanabilir": False, "zorunlu": True},
    {"belge": "Müteahhit yetki belgesi", "hazirlanabilir": False, "zorunlu": True},
    {"belge": "Mimar sicil belgesi", "hazirlanabilir": False, "zorunlu": True},
    {"belge": "İnşaat mühendisi sicil belgesi", "hazirlanabilir": False, "zorunlu": True},
    {"belge": "Numarataj belgesi", "hazirlanabilir": False, "zorunlu": True},
    {"belge": "Alan hesap tablosu", "hazirlanabilir": True, "zorunlu": True},
    {"belge": "Bağımsız bölüm listesi", "hazirlanabilir": True, "zorunlu": True},
    {"belge": "Otopark hesabı", "hazirlanabilir": True, "zorunlu": True},
    {"belge": "Enerji kimlik belgesi başvurusu", "hazirlanabilir": False, "zorunlu": True},
    {"belge": "SGK işyeri tescil belgesi", "hazirlanabilir": False, "zorunlu": True},
    {"belge": "Deprem sigortası", "hazirlanabilir": False, "zorunlu": False},
    {"belge": "Çevresel etki değerlendirmesi (varsa)", "hazirlanabilir": False, "zorunlu": False},
]


# ── Belge Detayları (isim, açıklama, zorunlu, tahmini süre) ──
BELGE_DETAYLARI = [
    {
        "isim": "Tapu fotokopisi",
        "aciklama": "Parselin güncel tapu senedi veya tapu kayıt örneği. Tapu müdürlüğünden alınır.",
        "zorunlu": True,
        "tahmini_sure_gun": 1,
    },
    {
        "isim": "İmar durumu belgesi",
        "aciklama": "Belediye imar müdürlüğünden alınan, parselin imar planındaki yapılaşma koşullarını gösteren belge.",
        "zorunlu": True,
        "tahmini_sure_gun": 5,
    },
    {
        "isim": "Mimari proje (5 takım)",
        "aciklama": "Mimar tarafından hazırlanan vaziyet planı, kat planları, kesitler ve görünüşleri içeren proje seti.",
        "zorunlu": True,
        "tahmini_sure_gun": 30,
    },
    {
        "isim": "Statik proje",
        "aciklama": "İnşaat mühendisi tarafından hazırlanan betonarme/çelik taşıyıcı sistem hesap ve çizimleri.",
        "zorunlu": True,
        "tahmini_sure_gun": 20,
    },
    {
        "isim": "Mekanik tesisat projesi",
        "aciklama": "Sıhhi tesisat, kalorifer, havalandırma ve doğalgaz tesisatı projeleri.",
        "zorunlu": True,
        "tahmini_sure_gun": 15,
    },
    {
        "isim": "Elektrik projesi",
        "aciklama": "Kuvvetli ve zayıf akım, aydınlatma, topraklama ve yıldırımdan korunma projeleri.",
        "zorunlu": True,
        "tahmini_sure_gun": 15,
    },
    {
        "isim": "Zemin etüdü raporu",
        "aciklama": "Jeoloji mühendisi tarafından hazırlanan sondaj ve laboratuvar deney sonuçlarını içeren zemin araştırma raporu.",
        "zorunlu": True,
        "tahmini_sure_gun": 10,
    },
    {
        "isim": "Yapı denetim sözleşmesi",
        "aciklama": "Bakanlık onaylı yapı denetim kuruluşu ile yapılan denetim hizmet sözleşmesi.",
        "zorunlu": True,
        "tahmini_sure_gun": 3,
    },
    {
        "isim": "Müteahhit yetki belgesi",
        "aciklama": "Çevre, Şehircilik ve İklim Değişikliği Bakanlığı'ndan alınan müteahhitlik yetki belgesi.",
        "zorunlu": True,
        "tahmini_sure_gun": 7,
    },
    {
        "isim": "Mimar sicil belgesi",
        "aciklama": "Projeyi hazırlayan mimarın meslek odası sicil durum belgesi.",
        "zorunlu": True,
        "tahmini_sure_gun": 3,
    },
    {
        "isim": "İnşaat mühendisi sicil belgesi",
        "aciklama": "Statik projeyi hazırlayan inşaat mühendisinin meslek odası sicil durum belgesi.",
        "zorunlu": True,
        "tahmini_sure_gun": 3,
    },
    {
        "isim": "Numarataj belgesi",
        "aciklama": "Belediyeden alınan yapı numarataj (adres) belgesi.",
        "zorunlu": True,
        "tahmini_sure_gun": 3,
    },
    {
        "isim": "Alan hesap tablosu",
        "aciklama": "TAKS/KAKS kontrolü, kat alanları, ortak alanlar ve toplam inşaat alanı dökümü.",
        "zorunlu": True,
        "tahmini_sure_gun": 2,
    },
    {
        "isim": "Bağımsız bölüm listesi",
        "aciklama": "Daire, dükkan ve ortak alanların brüt/net alan bilgilerini içeren liste.",
        "zorunlu": True,
        "tahmini_sure_gun": 2,
    },
    {
        "isim": "Otopark hesabı",
        "aciklama": "İmar yönetmeliğine uygun araç park yeri sayısı ve alan hesabı.",
        "zorunlu": True,
        "tahmini_sure_gun": 1,
    },
    {
        "isim": "Enerji kimlik belgesi başvurusu",
        "aciklama": "Binanın enerji performans sınıfını belirleyen BEP-TR sistemi üzerinden yapılan başvuru.",
        "zorunlu": True,
        "tahmini_sure_gun": 7,
    },
    {
        "isim": "SGK işyeri tescil belgesi",
        "aciklama": "İnşaat işyeri için SGK'ya yapılan tescil ve ilişiksizlik belgesi.",
        "zorunlu": True,
        "tahmini_sure_gun": 5,
    },
    {
        "isim": "Deprem sigortası",
        "aciklama": "Zorunlu deprem sigortası (DASK) poliçesi. Konut dışı yapılarda isteğe bağlı.",
        "zorunlu": False,
        "tahmini_sure_gun": 1,
    },
    {
        "isim": "Çevresel etki değerlendirmesi (varsa)",
        "aciklama": "Büyük ölçekli projelerde Çevre ve Şehircilik Bakanlığı'ndan alınan ÇED raporu.",
        "zorunlu": False,
        "tahmini_sure_gun": 60,
    },
]


# ── Denetim Aşamaları ──
DENETIM_ASAMALARI = [
    {
        "asama": "Zemin etüdü onayı",
        "aciklama": "Zemin araştırma raporunun yapı denetim kuruluşu tarafından incelenmesi ve onaylanması.",
        "sira": 1,
        "kritik": True,
        "tahmini_sure_gun": 5,
    },
    {
        "asama": "Temel vizesi",
        "aciklama": "Temel kazı, kalıp, demir ve beton döküm aşamalarının yerinde denetimi.",
        "sira": 2,
        "kritik": True,
        "tahmini_sure_gun": 7,
    },
    {
        "asama": "Kaba inşaat vizesi",
        "aciklama": "Taşıyıcı sistem (kolon, kiriş, perde, döşeme) imalatlarının kat bazında kontrolü.",
        "sira": 3,
        "kritik": True,
        "tahmini_sure_gun": 14,
    },
    {
        "asama": "Çatı vizesi",
        "aciklama": "Çatı konstrüksiyonu, su yalıtımı ve ısı yalıtımının denetimi.",
        "sira": 4,
        "kritik": False,
        "tahmini_sure_gun": 5,
    },
    {
        "asama": "Mekanik tesisat vizesi",
        "aciklama": "Sıhhi tesisat, doğalgaz, kalorifer ve havalandırma sistemlerinin basınç testleri ve kontrolü.",
        "sira": 5,
        "kritik": False,
        "tahmini_sure_gun": 7,
    },
    {
        "asama": "İnce işler kontrolü",
        "aciklama": "Sıva, boya, kaplama, doğrama ve elektrik tesisatı bitirme işlerinin kontrolü.",
        "sira": 6,
        "kritik": False,
        "tahmini_sure_gun": 10,
    },
    {
        "asama": "İskan vizesi",
        "aciklama": "Yapı kullanma izin belgesi için tüm sistemlerin son kontrolü ve uygunluk raporu.",
        "sira": 7,
        "kritik": True,
        "tahmini_sure_gun": 10,
    },
]


# ── İl bazlı birim harç oranları (TL/m²) ──
BIRIM_HARC_IL = {
    "istanbul": 85.0,
    "ankara": 65.0,
    "izmir": 60.0,
    "antalya": 55.0,
    "bursa": 55.0,
    "gaziantep": 50.0,
    "konya": 48.0,
    "adana": 48.0,
    "trabzon": 45.0,
    "kayseri": 45.0,
    "mersin": 47.0,
    "eskişehir": 47.0,
    "diyarbakır": 42.0,
    "samsun": 43.0,
    "denizli": 44.0,
    "muğla": 55.0,
    "tekirdağ": 52.0,
    "kocaeli": 58.0,
    "sakarya": 50.0,
    "balıkesir": 46.0,
    "manisa": 44.0,
    "malatya": 42.0,
    "van": 40.0,
    "erzurum": 40.0,
    "hatay": 45.0,
}
BIRIM_HARC_VARSAYILAN = 50.0

# Konut inşaat maliyet tahmini (TL/m²) — yapı denetim bedeli hesabında kullanılır
INSAAT_BIRIM_MALIYET = 375.0
DENETIM_ORANI_KONUT = 0.015  # %1.5

# ── Ek maliyet kalemleri (TL/m²) ──
PROJE_CIZIM_BIRIM_MALIYET = 45.0  # Mimari + statik + mekanik + elektrik proje
ZEMIN_ETUDU_BIRIM_MALIYET = 8.0   # Zemin etüdü raporu
SGK_ISYERI_KAYIT_BIRIM = 5.0      # SGK tescil masrafları tahmini
BELGE_HARCLARI_SABIT = 2500.0     # Numarataj, imar durumu vb. sabit harçlar


@dataclass
class AlanHesapTablosu:
    """Ruhsat başvurusu alan hesap tablosu."""
    parsel_alani: float = 0.0
    taks: float = 0.0
    kaks: float = 0.0
    taban_alani: float = 0.0
    toplam_insaat: float = 0.0
    kat_sayisi: int = 0
    daire_sayisi: int = 0
    daire_detaylari: list = field(default_factory=list)
    otopark_alan: float = 0.0
    otopark_arac: int = 0


@dataclass
class RuhsatSonucu:
    """Ruhsat başvuru sürecinin detaylı sonuç özeti."""
    yetki_sinifi: str = ""
    yetki_sinifi_aciklama: str = ""
    gerekli_belgeler: list = field(default_factory=list)
    belge_detaylari: list = field(default_factory=list)
    tahmini_ruhsat_suresi_gun: int = 45
    ruhsat_harci_tahmini: float = 0.0
    yapi_denetim_bedeli: float = 0.0
    denetim_asamalari: list = field(default_factory=list)
    eksik_belgeler: list = field(default_factory=list)
    toplam_maliyet_tahmini: float = 0.0
    # ── Ek detay alanları ──
    proje_cizim_maliyeti: float = 0.0
    zemin_etudu_maliyeti: float = 0.0
    sgk_kayit_maliyeti: float = 0.0
    belge_harclari: float = 0.0
    il: str = ""
    birim_harc_tl_m2: float = 0.0
    insaat_maliyeti_tahmini: float = 0.0
    toplam_denetim_suresi_gun: int = 0
    kritik_yol_asamalari: list = field(default_factory=list)
    maliyet_dagilimi: dict = field(default_factory=dict)
    olusturulma_tarihi: str = ""


def olustur_alan_hesap(
    parsel_alani: float,
    taks: float,
    kaks: float,
    taban_alani: float,
    toplam_insaat: float,
    kat_sayisi: int,
    daireler: list[dict],
    otopark_arac: int = 0,
) -> AlanHesapTablosu:
    """Alan hesap tablosu oluşturur."""
    tablo = AlanHesapTablosu(
        parsel_alani=parsel_alani,
        taks=taks, kaks=kaks,
        taban_alani=taban_alani,
        toplam_insaat=toplam_insaat,
        kat_sayisi=kat_sayisi,
        daire_sayisi=len(daireler),
        daire_detaylari=daireler,
        otopark_arac=otopark_arac,
        otopark_alan=otopark_arac * 17.5,
    )
    return tablo


def alan_hesap_to_text(tablo: AlanHesapTablosu) -> str:
    """Alan hesap tablosunu metin formatında döndürür."""
    lines = [
        "ALAN HESAP TABLOSU",
        "=" * 50,
        f"Parsel Alanı         : {tablo.parsel_alani:,.2f} m²",
        f"TAKS                 : {tablo.taks}",
        f"KAKS / Emsal         : {tablo.kaks}",
        f"Taban Alanı          : {tablo.taban_alani:,.2f} m²",
        f"TAKS Kontrolü        : {tablo.taban_alani:,.2f} / {tablo.parsel_alani * tablo.taks:,.2f} = {'✅ Uygun' if tablo.taban_alani <= tablo.parsel_alani * tablo.taks else '❌ Aşıyor'}",
        f"Toplam İnşaat Alanı  : {tablo.toplam_insaat:,.2f} m²",
        f"KAKS Kontrolü        : {tablo.toplam_insaat:,.2f} / {tablo.parsel_alani * tablo.kaks:,.2f} = {'✅ Uygun' if tablo.toplam_insaat <= tablo.parsel_alani * tablo.kaks else '❌ Aşıyor'}",
        f"Kat Sayısı           : {tablo.kat_sayisi}",
        f"Bağımsız Bölüm Sayısı: {tablo.daire_sayisi}",
        f"Otopark              : {tablo.otopark_arac} araç ({tablo.otopark_alan:.0f} m²)",
        "",
        "BAĞIMSIZ BÖLÜM DETAYLARI",
        "-" * 50,
    ]
    for d in tablo.daire_detaylari:
        lines.append(f"  Daire {d.get('daire_no',0)}: {d.get('tip','?')} — "
                     f"Brüt {d.get('brut_alan',0):.1f}m² / Net {d.get('net_alan',0):.1f}m²")
    return "\n".join(lines)


# ── Müteahhit Yetki Belge Sınıfları ──
YETKI_SINIFLARI = {
    "A": "Sınırsız (her türlü yapı)",
    "B": "Toplam inşaat alanı 30.000 m²'ye kadar",
    "C": "Toplam inşaat alanı 20.000 m²'ye kadar",
    "D": "Toplam inşaat alanı 10.000 m²'ye kadar",
    "E": "Toplam inşaat alanı 5.000 m²'ye kadar",
    "F": "Toplam inşaat alanı 2.000 m²'ye kadar",
    "G": "Toplam inşaat alanı 1.000 m²'ye kadar",
    "H": "Toplam inşaat alanı 500 m²'ye kadar",
}


def gerekli_yetki_sinifi(toplam_insaat: float) -> str:
    """Toplam inşaat alanına göre gerekli yetki sınıfını belirler."""
    if toplam_insaat <= 500:
        return "H"
    elif toplam_insaat <= 1000:
        return "G"
    elif toplam_insaat <= 2000:
        return "F"
    elif toplam_insaat <= 5000:
        return "E"
    elif toplam_insaat <= 10000:
        return "D"
    elif toplam_insaat <= 20000:
        return "C"
    elif toplam_insaat <= 30000:
        return "B"
    else:
        return "A"


def hesapla_ruhsat_detay(
    toplam_insaat: float,
    kat_sayisi: int,
    il: str = "",
) -> RuhsatSonucu:
    """
    Ruhsat başvuru sürecinin detaylı hesaplamasını yapar.

    Args:
        toplam_insaat: Toplam inşaat alanı (m²).
        kat_sayisi: Yapının kat sayısı.
        il: Projenin bulunduğu il (harç oranı hesabı için).

    Returns:
        RuhsatSonucu dataclass ile detaylı sonuç.
    """
    sonuc = RuhsatSonucu()
    sonuc.il = il
    sonuc.olusturulma_tarihi = datetime.now().strftime("%d.%m.%Y %H:%M")

    # ── Yetki sınıfı ──
    sonuc.yetki_sinifi = gerekli_yetki_sinifi(toplam_insaat)
    sonuc.yetki_sinifi_aciklama = YETKI_SINIFLARI.get(sonuc.yetki_sinifi, "")

    # ── Gerekli belgeler ──
    sonuc.gerekli_belgeler = [
        b["belge"] for b in RUHSAT_KONTROL_LISTESI if b["zorunlu"]
    ]

    # ── Belge detayları ──
    sonuc.belge_detaylari = [
        {
            "isim": bd["isim"],
            "aciklama": bd["aciklama"],
            "zorunlu": bd["zorunlu"],
            "tahmini_sure_gun": bd["tahmini_sure_gun"],
        }
        for bd in BELGE_DETAYLARI
    ]

    # ── Ruhsat harcı (il bazlı birim harç * toplam inşaat alanı) ──
    il_key = il.strip().lower()
    birim_harc = BIRIM_HARC_IL.get(il_key, BIRIM_HARC_VARSAYILAN)
    sonuc.birim_harc_tl_m2 = birim_harc
    sonuc.ruhsat_harci_tahmini = toplam_insaat * birim_harc

    # ── Yapı denetim bedeli ──
    # Konut projelerinde inşaat birim maliyeti üzerinden %1.5
    insaat_maliyeti = toplam_insaat * INSAAT_BIRIM_MALIYET
    sonuc.insaat_maliyeti_tahmini = insaat_maliyeti
    sonuc.yapi_denetim_bedeli = insaat_maliyeti * DENETIM_ORANI_KONUT

    # ── Ek maliyet kalemleri ──
    sonuc.proje_cizim_maliyeti = toplam_insaat * PROJE_CIZIM_BIRIM_MALIYET
    sonuc.zemin_etudu_maliyeti = toplam_insaat * ZEMIN_ETUDU_BIRIM_MALIYET
    sonuc.sgk_kayit_maliyeti = toplam_insaat * SGK_ISYERI_KAYIT_BIRIM
    sonuc.belge_harclari = BELGE_HARCLARI_SABIT

    # ── Denetim aşamaları ──
    sonuc.denetim_asamalari = [
        {
            "asama": da["asama"],
            "aciklama": da["aciklama"],
            "sira": da["sira"],
            "kritik": da.get("kritik", False),
            "tahmini_sure_gun": da.get("tahmini_sure_gun", 0),
        }
        for da in DENETIM_ASAMALARI
    ]

    # ── Toplam denetim süresi ve kritik yol ──
    sonuc.toplam_denetim_suresi_gun = sum(
        da.get("tahmini_sure_gun", 0) for da in DENETIM_ASAMALARI
    )
    sonuc.kritik_yol_asamalari = [
        da["asama"] for da in DENETIM_ASAMALARI if da.get("kritik", False)
    ]

    # ── Tahmini ruhsat süresi ──
    # Temel süre 45 gün; büyük projelerde ve yüksek katlarda ek süre
    baz_sure = 45
    if toplam_insaat > 10000:
        baz_sure += 15
    elif toplam_insaat > 5000:
        baz_sure += 10
    if kat_sayisi > 10:
        baz_sure += 10
    elif kat_sayisi > 5:
        baz_sure += 5
    # ÇED gerektiren büyük projeler için ek süre
    if toplam_insaat > 25000:
        baz_sure += 30
    sonuc.tahmini_ruhsat_suresi_gun = baz_sure

    # ── Eksik belgeler: başlangıçta tüm zorunlu belgeler eksik kabul edilir ──
    sonuc.eksik_belgeler = list(sonuc.gerekli_belgeler)

    # ── Toplam maliyet tahmini ──
    sonuc.toplam_maliyet_tahmini = (
        sonuc.ruhsat_harci_tahmini
        + sonuc.yapi_denetim_bedeli
        + sonuc.proje_cizim_maliyeti
        + sonuc.zemin_etudu_maliyeti
        + sonuc.sgk_kayit_maliyeti
        + sonuc.belge_harclari
    )

    # ── Maliyet dağılımı (yüzdesel) ──
    toplam = sonuc.toplam_maliyet_tahmini if sonuc.toplam_maliyet_tahmini > 0 else 1
    sonuc.maliyet_dagilimi = {
        "ruhsat_harci_yuzde": round(sonuc.ruhsat_harci_tahmini / toplam * 100, 1),
        "yapi_denetim_yuzde": round(sonuc.yapi_denetim_bedeli / toplam * 100, 1),
        "proje_cizim_yuzde": round(sonuc.proje_cizim_maliyeti / toplam * 100, 1),
        "zemin_etudu_yuzde": round(sonuc.zemin_etudu_maliyeti / toplam * 100, 1),
        "sgk_kayit_yuzde": round(sonuc.sgk_kayit_maliyeti / toplam * 100, 1),
        "belge_harclari_yuzde": round(sonuc.belge_harclari / toplam * 100, 1),
    }

    return sonuc


def ruhsat_sonucu_to_text(sonuc: RuhsatSonucu) -> str:
    """RuhsatSonucu nesnesini okunabilir metin formatına dönüştürür."""
    lines = [
        "RUHSAT BAŞVURU DETAY RAPORU",
        "=" * 60,
        f"Oluşturulma Tarihi   : {sonuc.olusturulma_tarihi}",
        f"İl                   : {sonuc.il or 'Belirtilmedi'}",
        f"Birim Harç           : {sonuc.birim_harc_tl_m2:,.2f} TL/m²",
        "",
        "YETKİ SINIFI",
        "-" * 40,
        f"  Sınıf              : {sonuc.yetki_sinifi}",
        f"  Açıklama           : {sonuc.yetki_sinifi_aciklama}",
        "",
        "MALİYET TAHMİNİ",
        "-" * 40,
        f"  Ruhsat Harcı       : {sonuc.ruhsat_harci_tahmini:>15,.2f} TL"
        f"  ({sonuc.maliyet_dagilimi.get('ruhsat_harci_yuzde', 0):.1f}%)",
        f"  Yapı Denetim Bedeli: {sonuc.yapi_denetim_bedeli:>15,.2f} TL"
        f"  ({sonuc.maliyet_dagilimi.get('yapi_denetim_yuzde', 0):.1f}%)",
        f"  Proje Çizim Maliy. : {sonuc.proje_cizim_maliyeti:>15,.2f} TL"
        f"  ({sonuc.maliyet_dagilimi.get('proje_cizim_yuzde', 0):.1f}%)",
        f"  Zemin Etüdü        : {sonuc.zemin_etudu_maliyeti:>15,.2f} TL"
        f"  ({sonuc.maliyet_dagilimi.get('zemin_etudu_yuzde', 0):.1f}%)",
        f"  SGK Kayıt          : {sonuc.sgk_kayit_maliyeti:>15,.2f} TL"
        f"  ({sonuc.maliyet_dagilimi.get('sgk_kayit_yuzde', 0):.1f}%)",
        f"  Belge Harçları     : {sonuc.belge_harclari:>15,.2f} TL"
        f"  ({sonuc.maliyet_dagilimi.get('belge_harclari_yuzde', 0):.1f}%)",
        f"  ─────────────────────────────────────────",
        f"  TOPLAM             : {sonuc.toplam_maliyet_tahmini:>15,.2f} TL",
        "",
        "SÜRE TAHMİNLERİ",
        "-" * 40,
        f"  Tahmini Ruhsat Süresi   : {sonuc.tahmini_ruhsat_suresi_gun} gün",
        f"  Toplam Denetim Süresi   : {sonuc.toplam_denetim_suresi_gun} gün",
        "",
        "DENETİM AŞAMALARI",
        "-" * 40,
    ]
    for da in sonuc.denetim_asamalari:
        kritik_flag = " [KRİTİK]" if da.get("kritik") else ""
        lines.append(
            f"  {da['sira']}. {da['asama']}{kritik_flag}"
            f" (~{da.get('tahmini_sure_gun', '?')} gün)"
        )
        lines.append(f"     {da['aciklama']}")

    lines.append("")
    lines.append("KRİTİK YOL AŞAMALARI")
    lines.append("-" * 40)
    for asama in sonuc.kritik_yol_asamalari:
        lines.append(f"  * {asama}")

    lines.append("")
    lines.append(f"EKSİK BELGELER ({len(sonuc.eksik_belgeler)} adet)")
    lines.append("-" * 40)
    for belge in sonuc.eksik_belgeler:
        lines.append(f"  [ ] {belge}")

    return "\n".join(lines)
