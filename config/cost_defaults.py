"""
İl Bazlı Varsayılan Maliyet ve Fiyat Verileri.
"""

# ── İl bazlı m² inşaat maliyeti (₺/m², 2024-2025 güncel tahmini) ──
IL_INSAAT_MALIYETI = {
    "İstanbul":  {"ekonomik": 28000, "orta": 37000, "luks": 52000},
    "Ankara":    {"ekonomik": 22000, "orta": 30000, "luks": 42000},
    "İzmir":     {"ekonomik": 24000, "orta": 33000, "luks": 46000},
    "Antalya":   {"ekonomik": 23000, "orta": 32000, "luks": 45000},
    "Bursa":     {"ekonomik": 21000, "orta": 28000, "luks": 39000},
    "Kütahya":   {"ekonomik": 18000, "orta": 24000, "luks": 34000},
    "Konya":     {"ekonomik": 19000, "orta": 25000, "luks": 35000},
    "Gaziantep": {"ekonomik": 20000, "orta": 26000, "luks": 37000},
    "Kayseri":   {"ekonomik": 19000, "orta": 25000, "luks": 35000},
    "Trabzon":   {"ekonomik": 21000, "orta": 28000, "luks": 39000},
    "Diyarbakır":{"ekonomik": 18000, "orta": 24000, "luks": 34000},
    "Samsun":    {"ekonomik": 19000, "orta": 26000, "luks": 36000},
    "Eskişehir": {"ekonomik": 20000, "orta": 27000, "luks": 38000},
    "Diğer":     {"ekonomik": 18000, "orta": 25000, "luks": 35000},
}

# ── Maliyet kalemleri yüzdesel dağılım ──
MALIYET_DAGILIMI = {
    "Kaba İnşaat (Betonarme)":             0.37,
    "İnce İnşaat (Sıva, Boya, Döşeme)":   0.27,
    "Tesisat (Elektrik, Su, Doğalgaz)":    0.16,
    "Dış Cephe (Mantolama, Kaplama)":      0.09,
    "Ortak Alanlar (Merdiven, Asansör)":   0.06,
    "Proje ve Harçlar":                     0.05,
}

# ── Otopark maliyetleri ──
OTOPARK_MALIYETLERI = {
    "acik":   {"m2_arac": 17.5, "maliyet_carpan": 1.0},
    "kapali": {"m2_arac": 32.5, "maliyet_carpan": 1.5},
}

# ── Kat primi oranları ──
KAT_PRIMI = {
    "zemin":     -0.05,
    "normal":     0.00,
    "ust_kat":    0.07,
    "cati_kati":  0.15,
}

# ── Cephe primi oranları ──
CEPHE_PRIMI = {
    "güney":     0.04,
    "batı":      0.03,
    "doğu":      0.02,
    "kuzey":    -0.03,
    "güneybatı": 0.04,
    "güneydoğu": 0.03,
}

# ── Gider kalemleri ──
GIDER_ORANLARI = {
    "proje_muhendislik":     0.04,   # %3-5
    "ruhsat_harclar":        0.015,  # %1-2
    "pazarlama":             0.025,  # %2-3
    "beklenmedik":           0.07,   # %5-10
}


def get_construction_cost(il: str, kalite: str = "orta") -> float:
    """İl ve kalite bazlı m² inşaat maliyetini döndürür (₺/m²)."""
    il_data = IL_INSAAT_MALIYETI.get(il, IL_INSAAT_MALIYETI["Diğer"])
    return il_data.get(kalite, il_data["orta"])


def get_iller() -> list[str]:
    """Tanımlı il listesini döndürür."""
    return list(IL_INSAAT_MALIYETI.keys())
