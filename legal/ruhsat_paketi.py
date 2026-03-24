"""
Yapı Ruhsatı Başvuru Paketi — Gerekli evrak listesi ve hazırlanan belgeler.
Müteahhit / Taşeron Eşleştirme.
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
