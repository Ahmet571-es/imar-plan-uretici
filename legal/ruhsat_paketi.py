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
    },
    {
        "asama": "Temel vizesi",
        "aciklama": "Temel kazı, kalıp, demir ve beton döküm aşamalarının yerinde denetimi.",
        "sira": 2,
    },
    {
        "asama": "Kaba inşaat vizesi",
        "aciklama": "Taşıyıcı sistem (kolon, kiriş, perde, döşeme) imalatlarının kat bazında kontrolü.",
        "sira": 3,
    },
    {
        "asama": "Çatı vizesi",
        "aciklama": "Çatı konstrüksiyonu, su yalıtımı ve ısı yalıtımının denetimi.",
        "sira": 4,
    },
    {
        "asama": "Mekanik tesisat vizesi",
        "aciklama": "Sıhhi tesisat, doğalgaz, kalorifer ve havalandırma sistemlerinin basınç testleri ve kontrolü.",
        "sira": 5,
    },
    {
        "asama": "İnce işler kontrolü",
        "aciklama": "Sıva, boya, kaplama, doğrama ve elektrik tesisatı bitirme işlerinin kontrolü.",
        "sira": 6,
    },
    {
        "asama": "İskan vizesi",
        "aciklama": "Yapı kullanma izin belgesi için tüm sistemlerin son kontrolü ve uygunluk raporu.",
        "sira": 7,
    },
]


# ── İl bazlı birim harç oranları (TL/m²) ──
BIRIM_HARC_IL = {
    "istanbul": 85.0,
    "ankara": 65.0,
    "izmir": 60.0,
    "antalya": 55.0,
    "bursa": 55.0,
}
BIRIM_HARC_VARSAYILAN = 50.0

# Konut inşaat maliyet tahmini (TL/m²) — yapı denetim bedeli hesabında kullanılır
INSAAT_BIRIM_MALIYET = 375.0
DENETIM_ORANI_KONUT = 0.015  # %1.5


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
    sonuc.ruhsat_harci_tahmini = toplam_insaat * birim_harc

    # ── Yapı denetim bedeli ──
    # Konut projelerinde inşaat birim maliyeti üzerinden %1.5
    insaat_maliyeti = toplam_insaat * INSAAT_BIRIM_MALIYET
    sonuc.yapi_denetim_bedeli = insaat_maliyeti * DENETIM_ORANI_KONUT

    # ── Denetim aşamaları ──
    sonuc.denetim_asamalari = [
        {
            "asama": da["asama"],
            "aciklama": da["aciklama"],
            "sira": da["sira"],
        }
        for da in DENETIM_ASAMALARI
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
    sonuc.tahmini_ruhsat_suresi_gun = baz_sure

    # ── Eksik belgeler: başlangıçta tüm zorunlu belgeler eksik kabul edilir ──
    sonuc.eksik_belgeler = list(sonuc.gerekli_belgeler)

    # ── Toplam maliyet tahmini ──
    sonuc.toplam_maliyet_tahmini = (
        sonuc.ruhsat_harci_tahmini + sonuc.yapi_denetim_bedeli
    )

    return sonuc
