"""
Yönetmelik Uyumluluk Kontrolü — Daire, oda ve parsel/imar düzeyinde validasyon.
"""

import re

from config.turkish_building_codes import (
    MIN_ODA_ALANLARI,
    validate_room,
    check_elevator_required,
    OTOPARK_KURALLARI,
    CEKME_MESAFESI_KURALLARI,
)
from config.room_defaults import oda_tipi_from_isim
from utils.constants import MIN_YAPILASMAYA_UYGUN_ALAN, KAT_ALAN_TOLERANS_ORANI


# ── Metin Temizleme ──

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_MAX_INPUT_LENGTH = 1000


def sanitize_text_input(text: str) -> str:
    """Kullanıcı metin girdisini güvenli hale getirir.

    - Baş/son boşlukları temizler
    - HTML etiketlerini kaldırır (XSS önlemi)
    - Maksimum 1000 karakterle sınırlar

    Args:
        text: Ham kullanıcı girdisi.

    Returns:
        Temizlenmiş metin.
    """
    if not isinstance(text, str):
        return ""
    text = text.strip()
    text = _HTML_TAG_RE.sub("", text)
    if len(text) > _MAX_INPUT_LENGTH:
        text = text[:_MAX_INPUT_LENGTH]
    return text


def validate_daire(odalar: list[dict], brut_alan: float) -> list[dict]:
    """Bir dairenin tüm odalarını yönetmeliğe göre kontrol eder.

    Args:
        odalar: [{"isim": str, "tip": str, "m2": float}, ...]
        brut_alan: Dairenin brüt alanı (m²).

    Returns:
        [{"kural": str, "gecerli": bool, "mesaj": str}, ...]
    """
    sonuclar = []

    # 1. Oda minimum alan kontrolleri
    for oda in odalar:
        tip = oda.get("tip", oda_tipi_from_isim(oda.get("isim", "")))
        alan = oda.get("m2", 0)
        result = validate_room(tip, alan)
        sonuclar.append({
            "kural": f"Minimum alan — {oda.get('isim', tip)}",
            "gecerli": result["gecerli"],
            "mesaj": result["mesaj"],
        })

    # 2. Oda toplam alan kontrolü
    toplam_oda = sum(o.get("m2", 0) for o in odalar)
    if toplam_oda > brut_alan:
        sonuclar.append({
            "kural": "Oda toplamı ≤ Brüt alan",
            "gecerli": False,
            "mesaj": f"⚠️ Oda toplamı ({toplam_oda:.1f} m²) > Brüt alan ({brut_alan:.1f} m²). "
                     f"Fark: {toplam_oda - brut_alan:.1f} m²",
        })
    else:
        sonuclar.append({
            "kural": "Oda toplamı ≤ Brüt alan",
            "gecerli": True,
            "mesaj": f"✅ Oda toplamı ({toplam_oda:.1f} m²) ≤ Brüt alan ({brut_alan:.1f} m²). "
                     f"Duvar/kayıp: {brut_alan - toplam_oda:.1f} m²",
        })

    return sonuclar


def validate_kat(daireler: list[dict], kat_brut_alan: float, ortak_alan: float) -> list[dict]:
    """Bir katın tüm dairelerini kontrol eder.

    Args:
        daireler: [{"tip": str, "brut_alan": float, "odalar": [...]}, ...]
        kat_brut_alan: Katın toplam brüt alanı (m²).
        ortak_alan: Ortak alanlar toplamı (merdiven, asansör vb.) (m²).

    Returns:
        [{"kural": str, "gecerli": bool, "mesaj": str}, ...]
    """
    sonuclar = []

    toplam_daire = sum(d.get("brut_alan", 0) for d in daireler)
    toplam = toplam_daire + ortak_alan

    if toplam > kat_brut_alan * KAT_ALAN_TOLERANS_ORANI:  # %5 tolerans
        sonuclar.append({
            "kural": "Daire + Ortak alan ≤ Kat brüt alanı",
            "gecerli": False,
            "mesaj": f"⚠️ Daire toplamı ({toplam_daire:.1f}) + Ortak alan ({ortak_alan:.1f}) = "
                     f"{toplam:.1f} m² > Kat brüt ({kat_brut_alan:.1f} m²)",
        })
    else:
        sonuclar.append({
            "kural": "Daire + Ortak alan ≤ Kat brüt alanı",
            "gecerli": True,
            "mesaj": f"✅ Daire toplamı ({toplam_daire:.1f}) + Ortak alan ({ortak_alan:.1f}) = "
                     f"{toplam:.1f} m² ≤ Kat brüt ({kat_brut_alan:.1f} m²)",
        })

    return sonuclar


def validate_bina(kat_sayisi: int, daire_sayisi_toplam: int) -> list[dict]:
    """Bina düzeyinde kontroller."""
    sonuclar = []

    # Asansör zorunluluğu
    asansor = check_elevator_required(kat_sayisi)
    if asansor:
        sonuclar.append({
            "kural": "Asansör zorunluluğu",
            "gecerli": True,
            "mesaj": f"ℹ️ {kat_sayisi} kat → Asansör zorunlu (4+ kat kuralı)",
        })
    else:
        sonuclar.append({
            "kural": "Asansör zorunluluğu",
            "gecerli": True,
            "mesaj": f"ℹ️ {kat_sayisi} kat → Asansör zorunlu değil",
        })

    # Otopark
    min_arac = daire_sayisi_toplam * OTOPARK_KURALLARI["daire_basi_min_arac"]
    sonuclar.append({
        "kural": "Otopark gereksinimi",
        "gecerli": True,
        "mesaj": f"ℹ️ {daire_sayisi_toplam} daire → Minimum {min_arac} araçlık otopark gerekli",
    })

    return sonuclar


def validate_parsel_imar(parsel_alani: float, imar: dict) -> list[dict]:
    """Parsel alanı ve imar parametrelerinin uyumluluğunu kontrol eder.

    Planlı Alanlar İmar Yönetmeliği'ne göre aşağıdaki kontrolleri yapar:
    - TAKS * parsel_alani ile minimum yapılaşma alanı kontrolü (min 30 m²)
    - KAKS / kat_adedi oranının TAKS'ı aşmaması kontrolü
    - Ayrık nizamda ön bahçe minimum 5m kontrolü
    - Ayrık nizamda yan bahçe minimum 3m kontrolü

    Args:
        parsel_alani: Parsel alanı (m²).
        imar: İmar parametreleri sözlüğü. Beklenen anahtarlar:
            - taks (float): Taban Alanı Kat Sayısı
            - kaks (float): Kat Alanı Kat Sayısı
            - kat_adedi (int): Kat adedi
            - insaat_nizami (str): "A", "B" veya "BL"
            - on_bahce (float): Ön bahçe mesafesi (m)
            - yan_bahce (float): Yan bahçe mesafesi (m)

    Returns:
        [{"gecerli": bool, "mesaj": str, "madde": str}, ...] şeklinde kontrol sonuçları.
    """
    sonuclar = []

    taks = imar.get("taks", 0.0)
    kaks = imar.get("kaks", 0.0)
    kat_adedi = imar.get("kat_adedi", 0)
    insaat_nizami = imar.get("insaat_nizami", "A")
    on_bahce = imar.get("on_bahce", 0.0)
    yan_bahce = imar.get("yan_bahce", 0.0)

    # 1. TAKS * parsel_alani minimum yapılaşma alanı kontrolü (min 30 m²)
    taban_alani = taks * parsel_alani
    if taban_alani < MIN_YAPILASMAYA_UYGUN_ALAN and taks > 0:
        sonuclar.append({
            "gecerli": False,
            "mesaj": (
                f"TAKS ile hesaplanan taban alani ({taban_alani:.1f} m2) "
                f"minimum yapilasmaya uygun alan ({MIN_YAPILASMAYA_UYGUN_ALAN:.0f} m2) altinda. "
                f"Parsel alani yetersiz veya TAKS dusuk."
            ),
            "madde": "Planli Alanlar Imar Yonetmeligi — Yapi Yasaklari",
        })
    else:
        sonuclar.append({
            "gecerli": True,
            "mesaj": (
                f"TAKS ile hesaplanan taban alani ({taban_alani:.1f} m2) "
                f"minimum yapilasmaya uygun alan ({MIN_YAPILASMAYA_UYGUN_ALAN:.0f} m2) ustunde."
            ),
            "madde": "Planli Alanlar Imar Yonetmeligi — Yapi Yasaklari",
        })

    # 2. KAKS / kat_adedi <= TAKS kontrolü (kat başı brüt alan > taban alanı kontrolü)
    if kat_adedi > 0 and taks > 0:
        kat_basi_emsal = kaks / kat_adedi
        if kat_basi_emsal > taks:
            sonuclar.append({
                "gecerli": False,
                "mesaj": (
                    f"KAKS/kat_adedi ({kat_basi_emsal:.3f}) > TAKS ({taks:.3f}). "
                    f"Kat basi brut alan taban alanini asiyor. "
                    f"KAKS veya kat adedini kontrol edin."
                ),
                "madde": "Planli Alanlar Imar Yonetmeligi — Madde 5: TAKS/KAKS Iliskisi",
            })
        else:
            sonuclar.append({
                "gecerli": True,
                "mesaj": (
                    f"KAKS/kat_adedi ({kat_basi_emsal:.3f}) <= TAKS ({taks:.3f}). "
                    f"Kat basi brut alan taban alani sinirinda."
                ),
                "madde": "Planli Alanlar Imar Yonetmeligi — Madde 5: TAKS/KAKS Iliskisi",
            })
    elif kat_adedi <= 0:
        sonuclar.append({
            "gecerli": False,
            "mesaj": "Kat adedi 0 veya negatif olamaz.",
            "madde": "Genel parametre kontrolu",
        })

    # 3. Ayrık nizamda ön bahçe minimum 5m kontrolü
    if insaat_nizami == "A":
        cekme_kurallari = CEKME_MESAFESI_KURALLARI.get("A", {})
        on_bahce_min = cekme_kurallari.get("on_bahce_min", 5.0)
        if on_bahce < on_bahce_min:
            sonuclar.append({
                "gecerli": False,
                "mesaj": (
                    f"Ayrik nizamda on bahce ({on_bahce:.1f} m) "
                    f"minimum {on_bahce_min:.1f} m olmalidir."
                ),
                "madde": "Planli Alanlar Imar Yonetmeligi — Madde 6: Cekme Mesafeleri",
            })
        else:
            sonuclar.append({
                "gecerli": True,
                "mesaj": (
                    f"Ayrik nizamda on bahce ({on_bahce:.1f} m) >= "
                    f"minimum {on_bahce_min:.1f} m."
                ),
                "madde": "Planli Alanlar Imar Yonetmeligi — Madde 6: Cekme Mesafeleri",
            })

        # 4. Ayrık nizamda yan bahçe minimum 3m kontrolü
        yan_bahce_min = cekme_kurallari.get("yan_bahce_min", 3.0)
        if yan_bahce < yan_bahce_min:
            sonuclar.append({
                "gecerli": False,
                "mesaj": (
                    f"Ayrik nizamda yan bahce ({yan_bahce:.1f} m) "
                    f"minimum {yan_bahce_min:.1f} m olmalidir."
                ),
                "madde": "Planli Alanlar Imar Yonetmeligi — Madde 6: Cekme Mesafeleri",
            })
        else:
            sonuclar.append({
                "gecerli": True,
                "mesaj": (
                    f"Ayrik nizamda yan bahce ({yan_bahce:.1f} m) >= "
                    f"minimum {yan_bahce_min:.1f} m."
                ),
                "madde": "Planli Alanlar Imar Yonetmeligi — Madde 6: Cekme Mesafeleri",
            })

    return sonuclar
