"""
Varsayılan Oda Boyutları — Daire tiplerine göre (1+1 ... 5+1).
Her daire tipi için oda listesi, varsayılan m² değerleri ve min/max aralıkları.

Minimum alan değerleri 3194 sayılı İmar Kanunu ve Planlı Alanlar İmar
Yönetmeliği'ne uygun olarak belirlenmiştir:
  - Salon:       min 16 m²
  - Yatak Odası: min  9 m²
  - Mutfak:      min  5 m²
  - Banyo:       min  3.5 m²
  - WC:          min  1.5 m²
  - Balkon:      min  2 m²
"""

# ── Daire Tipi Varsayılan Tanımları ──
# Her oda: {"isim": str, "tip": str, "varsayilan_m2": float, "min_m2": float, "max_m2": float}

DAIRE_SABLONLARI = {
    "1+1": {
        "brut_alan_aralik": (45, 70),
        "varsayilan_brut": 55,
        "odalar": [
            {"isim": "Salon",        "tip": "salon",       "varsayilan_m2": 18.0, "min_m2": 16.0, "max_m2": 28.0},
            {"isim": "Yatak Odası",  "tip": "yatak_odasi", "varsayilan_m2": 12.0, "min_m2": 9.0,  "max_m2": 16.0},
            {"isim": "Mutfak",       "tip": "mutfak",      "varsayilan_m2": 7.0,  "min_m2": 5.0,  "max_m2": 12.0},
            {"isim": "Banyo",        "tip": "banyo",       "varsayilan_m2": 4.5,  "min_m2": 3.5,  "max_m2": 6.0},
            {"isim": "Antre",        "tip": "antre",       "varsayilan_m2": 4.0,  "min_m2": 3.0,  "max_m2": 6.0},
            {"isim": "Balkon",       "tip": "balkon",      "varsayilan_m2": 4.0,  "min_m2": 2.0,  "max_m2": 8.0},
        ],
    },
    "2+1": {
        "brut_alan_aralik": (70, 110),
        "varsayilan_brut": 90,
        "odalar": [
            {"isim": "Salon",         "tip": "salon",       "varsayilan_m2": 22.0, "min_m2": 16.0, "max_m2": 32.0},
            {"isim": "Yatak Odası 1", "tip": "yatak_odasi", "varsayilan_m2": 14.0, "min_m2": 9.0,  "max_m2": 20.0},
            {"isim": "Yatak Odası 2", "tip": "yatak_odasi", "varsayilan_m2": 12.0, "min_m2": 9.0,  "max_m2": 16.0},
            {"isim": "Mutfak",        "tip": "mutfak",      "varsayilan_m2": 9.0,  "min_m2": 5.0,  "max_m2": 14.0},
            {"isim": "Banyo",         "tip": "banyo",       "varsayilan_m2": 5.0,  "min_m2": 3.5,  "max_m2": 7.0},
            {"isim": "WC",            "tip": "wc",          "varsayilan_m2": 2.5,  "min_m2": 1.5,  "max_m2": 4.0},
            {"isim": "Antre",         "tip": "antre",       "varsayilan_m2": 5.0,  "min_m2": 3.0,  "max_m2": 8.0},
            {"isim": "Koridor",       "tip": "koridor",     "varsayilan_m2": 4.0,  "min_m2": 2.0,  "max_m2": 7.0},
            {"isim": "Balkon",        "tip": "balkon",      "varsayilan_m2": 5.0,  "min_m2": 3.0,  "max_m2": 10.0},
        ],
    },
    "3+1": {
        "brut_alan_aralik": (100, 150),
        "varsayilan_brut": 125,
        "odalar": [
            {"isim": "Salon",         "tip": "salon",       "varsayilan_m2": 28.0, "min_m2": 18.0, "max_m2": 40.0},
            {"isim": "Yatak Odası 1", "tip": "yatak_odasi", "varsayilan_m2": 16.0, "min_m2": 10.0, "max_m2": 22.0},
            {"isim": "Yatak Odası 2", "tip": "yatak_odasi", "varsayilan_m2": 14.0, "min_m2": 9.0,  "max_m2": 18.0},
            {"isim": "Yatak Odası 3", "tip": "yatak_odasi", "varsayilan_m2": 12.0, "min_m2": 9.0,  "max_m2": 16.0},
            {"isim": "Mutfak",        "tip": "mutfak",      "varsayilan_m2": 11.0, "min_m2": 5.0,  "max_m2": 18.0},
            {"isim": "Banyo",         "tip": "banyo",       "varsayilan_m2": 5.5,  "min_m2": 3.5,  "max_m2": 8.0},
            {"isim": "WC",            "tip": "wc",          "varsayilan_m2": 2.5,  "min_m2": 1.5,  "max_m2": 4.0},
            {"isim": "Antre",         "tip": "antre",       "varsayilan_m2": 5.5,  "min_m2": 3.0,  "max_m2": 10.0},
            {"isim": "Koridor",       "tip": "koridor",     "varsayilan_m2": 5.0,  "min_m2": 2.0,  "max_m2": 8.0},
            {"isim": "Balkon 1",      "tip": "balkon",      "varsayilan_m2": 5.0,  "min_m2": 3.0,  "max_m2": 10.0},
            {"isim": "Balkon 2",      "tip": "balkon",      "varsayilan_m2": 3.5,  "min_m2": 2.0,  "max_m2": 8.0},
        ],
    },
    "4+1": {
        "brut_alan_aralik": (140, 200),
        "varsayilan_brut": 165,
        "odalar": [
            {"isim": "Salon",         "tip": "salon",       "varsayilan_m2": 32.0, "min_m2": 22.0, "max_m2": 45.0},
            {"isim": "Yatak Odası 1", "tip": "yatak_odasi", "varsayilan_m2": 18.0, "min_m2": 12.0, "max_m2": 24.0},
            {"isim": "Yatak Odası 2", "tip": "yatak_odasi", "varsayilan_m2": 15.0, "min_m2": 9.0,  "max_m2": 20.0},
            {"isim": "Yatak Odası 3", "tip": "yatak_odasi", "varsayilan_m2": 13.0, "min_m2": 9.0,  "max_m2": 18.0},
            {"isim": "Yatak Odası 4", "tip": "yatak_odasi", "varsayilan_m2": 12.0, "min_m2": 9.0,  "max_m2": 16.0},
            {"isim": "Mutfak",        "tip": "mutfak",      "varsayilan_m2": 13.0, "min_m2": 7.0,  "max_m2": 20.0},
            {"isim": "Banyo 1",       "tip": "banyo",       "varsayilan_m2": 6.0,  "min_m2": 3.5,  "max_m2": 9.0},
            {"isim": "Banyo 2",       "tip": "banyo",       "varsayilan_m2": 4.5,  "min_m2": 3.5,  "max_m2": 7.0},
            {"isim": "WC",            "tip": "wc",          "varsayilan_m2": 2.5,  "min_m2": 1.5,  "max_m2": 4.0},
            {"isim": "Antre",         "tip": "antre",       "varsayilan_m2": 6.0,  "min_m2": 3.0,  "max_m2": 10.0},
            {"isim": "Koridor",       "tip": "koridor",     "varsayilan_m2": 6.0,  "min_m2": 3.0,  "max_m2": 10.0},
            {"isim": "Balkon 1",      "tip": "balkon",      "varsayilan_m2": 6.0,  "min_m2": 3.0,  "max_m2": 12.0},
            {"isim": "Balkon 2",      "tip": "balkon",      "varsayilan_m2": 4.0,  "min_m2": 2.0,  "max_m2": 8.0},
        ],
    },
    "5+1": {
        "brut_alan_aralik": (180, 280),
        "varsayilan_brut": 220,
        "odalar": [
            {"isim": "Salon",         "tip": "salon",       "varsayilan_m2": 38.0, "min_m2": 25.0, "max_m2": 55.0},
            {"isim": "Yatak Odası 1", "tip": "yatak_odasi", "varsayilan_m2": 20.0, "min_m2": 14.0, "max_m2": 28.0},
            {"isim": "Yatak Odası 2", "tip": "yatak_odasi", "varsayilan_m2": 16.0, "min_m2": 10.0, "max_m2": 22.0},
            {"isim": "Yatak Odası 3", "tip": "yatak_odasi", "varsayilan_m2": 14.0, "min_m2": 9.0,  "max_m2": 18.0},
            {"isim": "Yatak Odası 4", "tip": "yatak_odasi", "varsayilan_m2": 13.0, "min_m2": 9.0,  "max_m2": 16.0},
            {"isim": "Yatak Odası 5", "tip": "yatak_odasi", "varsayilan_m2": 12.0, "min_m2": 9.0,  "max_m2": 15.0},
            {"isim": "Mutfak",        "tip": "mutfak",      "varsayilan_m2": 15.0, "min_m2": 8.0,  "max_m2": 22.0},
            {"isim": "Banyo 1",       "tip": "banyo",       "varsayilan_m2": 7.0,  "min_m2": 4.0,  "max_m2": 10.0},
            {"isim": "Banyo 2",       "tip": "banyo",       "varsayilan_m2": 5.0,  "min_m2": 3.5,  "max_m2": 7.0},
            {"isim": "WC",            "tip": "wc",          "varsayilan_m2": 3.0,  "min_m2": 1.5,  "max_m2": 4.5},
            {"isim": "Antre",         "tip": "antre",       "varsayilan_m2": 7.0,  "min_m2": 4.0,  "max_m2": 12.0},
            {"isim": "Koridor",       "tip": "koridor",     "varsayilan_m2": 7.0,  "min_m2": 3.0,  "max_m2": 12.0},
            {"isim": "Balkon 1",      "tip": "balkon",      "varsayilan_m2": 7.0,  "min_m2": 3.0,  "max_m2": 14.0},
            {"isim": "Balkon 2",      "tip": "balkon",      "varsayilan_m2": 5.0,  "min_m2": 2.0,  "max_m2": 10.0},
        ],
    },
}


# ── 3194 Sayılı İmar Kanunu Minimum Alan Gereksinimleri (m²) ──
# Planlı Alanlar İmar Yönetmeliği'ne göre zorunlu minimum alanlar.
MINIMUM_ODA_ALANLARI: dict[str, float] = {
    "salon":       16.0,   # 3194 sayılı İmar Kanunu
    "yatak_odasi":  9.0,
    "mutfak":       5.0,
    "banyo":        3.5,
    "wc":           1.5,
    "balkon":       2.0,
    "antre":        2.5,
    "koridor":      1.5,
    "salon_mutfak": 21.0,  # Açık plan: salon (16) + mutfak (5)
}


def get_minimum_alan(oda_tipi: str) -> float:
    """Oda tipine göre yönetmelikteki minimum alanı döndürür (m²)."""
    return MINIMUM_ODA_ALANLARI.get(oda_tipi, 0.0)


def get_template(daire_tipi: str) -> dict | None:
    """Daire tipine göre şablon döndür."""
    return DAIRE_SABLONLARI.get(daire_tipi)


def get_default_rooms(daire_tipi: str) -> list[dict]:
    """Daire tipine göre varsayılan oda listesini döndür."""
    tpl = get_template(daire_tipi)
    if tpl is None:
        return []
    return [dict(r) for r in tpl["odalar"]]


def oda_tipi_from_isim(isim: str) -> str:
    """Oda isminden tip çıkar (basitleştirilmiş)."""
    isim_lower = isim.lower()
    if "salon" in isim_lower or "oturma" in isim_lower:
        return "salon"
    if "yatak" in isim_lower:
        return "yatak_odasi"
    if "mutfak" in isim_lower:
        return "mutfak"
    if "banyo" in isim_lower or "duş" in isim_lower:
        return "banyo"
    if "wc" in isim_lower or "tuvalet" in isim_lower:
        return "wc"
    if "antre" in isim_lower or "hol" in isim_lower:
        return "antre"
    if "koridor" in isim_lower:
        return "koridor"
    if "balkon" in isim_lower or "teras" in isim_lower:
        return "balkon"
    return "diger"
