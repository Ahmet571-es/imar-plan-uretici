"""
Yönetmelik Uyumluluk Kontrolü — Daire ve oda düzeyinde validasyon.
"""

from config.turkish_building_codes import (
    MIN_ODA_ALANLARI,
    validate_room,
    check_elevator_required,
    OTOPARK_KURALLARI,
)
from config.room_defaults import oda_tipi_from_isim


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

    if toplam > kat_brut_alan * 1.05:  # %5 tolerans
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
