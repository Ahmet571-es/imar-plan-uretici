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


# ══════════════════════════════════════════════════════════════
# DERİNLEŞTİRİLMİŞ VALİDASYON FONKSİYONLARI
# ══════════════════════════════════════════════════════════════

def validate_daire_detayli(odalar: list[dict], brut_alan: float, daire_tipi: str = "3+1") -> list[dict]:
    """Derinleştirilmiş daire validasyonu — oran analizi ve fonksiyonel kontroller.

    Args:
        odalar: [{"isim": str, "tip": str, "m2": float}, ...]
        brut_alan: Dairenin brüt alanı (m²).
        daire_tipi: Daire tipi ("1+1", "2+1", "3+1", vb.).

    Returns:
        [{"kural": str, "gecerli": bool, "mesaj": str}, ...]
    """
    sonuclar = validate_daire(odalar, brut_alan)

    toplam_oda = sum(o.get("m2", 0) for o in odalar)

    # 3. Duvar kayıp oranı kontrolü (%15-25 beklenir)
    if brut_alan > 0:
        kayip_orani = (brut_alan - toplam_oda) / brut_alan
        if kayip_orani < 0.10:
            sonuclar.append({
                "kural": "Duvar kayıp oranı",
                "gecerli": False,
                "mesaj": f"⚠️ Duvar kayıp oranı çok düşük: %{kayip_orani*100:.0f} (beklenen: %15-25)",
            })
        elif kayip_orani > 0.30:
            sonuclar.append({
                "kural": "Duvar kayıp oranı",
                "gecerli": False,
                "mesaj": f"⚠️ Duvar kayıp oranı çok yüksek: %{kayip_orani*100:.0f} (beklenen: %15-25)",
            })
        else:
            sonuclar.append({
                "kural": "Duvar kayıp oranı",
                "gecerli": True,
                "mesaj": f"✅ Duvar kayıp oranı normal: %{kayip_orani*100:.0f}",
            })

    # 4. Islak hacim oranı kontrolü (%15-35)
    islak_alan = sum(o.get("m2", 0) for o in odalar if o.get("tip") in ("banyo", "wc", "mutfak"))
    if toplam_oda > 0:
        islak_oran = islak_alan / toplam_oda
        if islak_oran < 0.15:
            sonuclar.append({"kural": "Islak hacim oranı", "gecerli": False,
                "mesaj": f"⚠️ Islak hacim oranı düşük: %{islak_oran*100:.0f} (min %15)"})
        elif islak_oran > 0.35:
            sonuclar.append({"kural": "Islak hacim oranı", "gecerli": False,
                "mesaj": f"⚠️ Islak hacim oranı yüksek: %{islak_oran*100:.0f} (max %35)"})
        else:
            sonuclar.append({"kural": "Islak hacim oranı", "gecerli": True,
                "mesaj": f"✅ Islak hacim oranı uygun: %{islak_oran*100:.0f}"})

    # 5. Yaşam alanı oranı kontrolü (%45+)
    yasam_alan = sum(o.get("m2", 0) for o in odalar if o.get("tip") in ("salon", "yatak_odasi"))
    if toplam_oda > 0:
        yasam_oran = yasam_alan / toplam_oda
        if yasam_oran < 0.45:
            sonuclar.append({"kural": "Yaşam alanı oranı", "gecerli": False,
                "mesaj": f"⚠️ Yaşam alanı oranı düşük: %{yasam_oran*100:.0f} (min %45)"})
        else:
            sonuclar.append({"kural": "Yaşam alanı oranı", "gecerli": True,
                "mesaj": f"✅ Yaşam alanı oranı uygun: %{yasam_oran*100:.0f}"})

    # 6. Daire tipi oda sayısı kontrolü
    tip_min_oda = {"1+1": 4, "2+1": 6, "3+1": 8, "4+1": 10, "5+1": 12}
    min_oda = tip_min_oda.get(daire_tipi, 4)
    if len(odalar) < min_oda:
        sonuclar.append({"kural": f"{daire_tipi} oda sayısı", "gecerli": False,
            "mesaj": f"⚠️ {daire_tipi} için min {min_oda} oda gerekli, mevcut: {len(odalar)}"})
    else:
        sonuclar.append({"kural": f"{daire_tipi} oda sayısı", "gecerli": True,
            "mesaj": f"✅ {len(odalar)} oda — {daire_tipi} için yeterli"})

    # 7. Balkon kontrolü
    balkon_var = any(o.get("tip") == "balkon" for o in odalar)
    sonuclar.append({"kural": "Balkon varlığı", "gecerli": balkon_var,
        "mesaj": "✅ Balkon mevcut" if balkon_var else "ℹ️ Balkon bulunmuyor"})

    # 8. Sirkülasyon oranı
    sirk_alan = sum(o.get("m2", 0) for o in odalar if o.get("tip") in ("antre", "koridor"))
    if toplam_oda > 0:
        sirk_oran = sirk_alan / toplam_oda
        if sirk_oran > 0.22:
            sonuclar.append({"kural": "Sirkülasyon oranı", "gecerli": False,
                "mesaj": f"⚠️ Sirkülasyon oranı yüksek: %{sirk_oran*100:.0f} (max %22)"})
        else:
            sonuclar.append({"kural": "Sirkülasyon oranı", "gecerli": True,
                "mesaj": f"✅ Sirkülasyon oranı uygun: %{sirk_oran*100:.0f}"})

    return sonuclar


def validate_islak_hacim_kurallari(odalar: list[dict]) -> list[dict]:
    """Islak hacim kurallarını detaylı kontrol eder."""
    sonuclar = []

    banyolar = [o for o in odalar if o.get("tip") == "banyo"]
    wcler = [o for o in odalar if o.get("tip") == "wc"]
    mutfaklar = [o for o in odalar if o.get("tip") == "mutfak"]

    for b in banyolar:
        alan = b.get("m2", 0)
        gecerli = alan >= 3.5
        sonuclar.append({"kural": f"Banyo min alan — {b.get('isim', 'Banyo')}", "gecerli": gecerli,
            "mesaj": f"{'✅' if gecerli else '⚠️'} {b.get('isim', 'Banyo')}: {alan:.1f}m² {'≥' if gecerli else '<'} 3.5m²"})

    for w in wcler:
        alan = w.get("m2", 0)
        gecerli = alan >= 1.5
        sonuclar.append({"kural": f"WC min alan — {w.get('isim', 'WC')}", "gecerli": gecerli,
            "mesaj": f"{'✅' if gecerli else '⚠️'} {w.get('isim', 'WC')}: {alan:.1f}m² {'≥' if gecerli else '<'} 1.5m²"})

    for m in mutfaklar:
        alan = m.get("m2", 0)
        gecerli = alan >= 5.0
        sonuclar.append({"kural": f"Mutfak min alan — {m.get('isim', 'Mutfak')}", "gecerli": gecerli,
            "mesaj": f"{'✅' if gecerli else '⚠️'} {m.get('isim', 'Mutfak')}: {alan:.1f}m² {'≥' if gecerli else '<'} 5.0m²"})

    if not banyolar:
        sonuclar.append({"kural": "Banyo varlığı", "gecerli": False, "mesaj": "⚠️ Dairede banyo bulunmuyor — zorunlu!"})

    return sonuclar
