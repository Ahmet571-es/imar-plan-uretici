"""
Mobilya Kütüphanesi — 2D semboller, boyutlar ve yerleştirme kuralları.
"""

# Boyutlar: (genişlik, derinlik) metre cinsinden
MOBILYA_KUTUPHANESI = {
    "salon": [
        {"isim": "3'lü Koltuk",     "en": 2.10, "boy": 0.90, "sembol": "koltuk_3",    "duvar_bitisik": True},
        {"isim": "Tekli Koltuk",     "en": 0.90, "boy": 0.90, "sembol": "koltuk_1",    "duvar_bitisik": True},
        {"isim": "Sehpa",            "en": 1.20, "boy": 0.60, "sembol": "sehpa",       "duvar_bitisik": False},
        {"isim": "TV Ünitesi",       "en": 1.80, "boy": 0.45, "sembol": "tv_unitesi",  "duvar_bitisik": True},
        {"isim": "Yemek Masası (4)", "en": 1.20, "boy": 0.80, "sembol": "masa_yemek",  "duvar_bitisik": False},
        {"isim": "Sandalye",         "en": 0.45, "boy": 0.45, "sembol": "sandalye",    "duvar_bitisik": False},
    ],
    "yatak_odasi": [
        {"isim": "Çift Kişilik Yatak","en": 1.60, "boy": 2.00, "sembol": "yatak_cift", "duvar_bitisik": True},
        {"isim": "Komodin",           "en": 0.50, "boy": 0.40, "sembol": "komodin",    "duvar_bitisik": True},
        {"isim": "Gardırop",          "en": 1.80, "boy": 0.60, "sembol": "gardirop",   "duvar_bitisik": True},
        {"isim": "Şifonyer",          "en": 1.00, "boy": 0.45, "sembol": "sifonyer",   "duvar_bitisik": True},
    ],
    "cocuk_odasi": [
        {"isim": "Tek Kişilik Yatak", "en": 0.90, "boy": 2.00, "sembol": "yatak_tek",  "duvar_bitisik": True},
        {"isim": "Çalışma Masası",    "en": 1.20, "boy": 0.60, "sembol": "masa_calisma","duvar_bitisik": True},
        {"isim": "Gardırop",          "en": 1.20, "boy": 0.60, "sembol": "gardirop",   "duvar_bitisik": True},
    ],
    "mutfak": [
        {"isim": "Tezgah (düz)",      "en": 2.40, "boy": 0.60, "sembol": "tezgah",     "duvar_bitisik": True},
        {"isim": "Ocak",              "en": 0.60, "boy": 0.60, "sembol": "ocak",        "duvar_bitisik": True},
        {"isim": "Buzdolabı",         "en": 0.70, "boy": 0.70, "sembol": "buzdolabi",   "duvar_bitisik": True},
        {"isim": "Bulaşık Makinesi",  "en": 0.60, "boy": 0.60, "sembol": "bulasik",     "duvar_bitisik": True},
        {"isim": "Lavabo",            "en": 0.60, "boy": 0.50, "sembol": "lavabo_m",    "duvar_bitisik": True},
    ],
    "banyo": [
        {"isim": "Duşakabin",         "en": 0.90, "boy": 0.90, "sembol": "dusakabin",   "duvar_bitisik": True},
        {"isim": "Lavabo",            "en": 0.60, "boy": 0.45, "sembol": "lavabo",      "duvar_bitisik": True},
        {"isim": "Klozet",            "en": 0.40, "boy": 0.65, "sembol": "klozet",      "duvar_bitisik": True},
    ],
    "wc": [
        {"isim": "Klozet",            "en": 0.40, "boy": 0.65, "sembol": "klozet",      "duvar_bitisik": True},
        {"isim": "Mini Lavabo",       "en": 0.40, "boy": 0.30, "sembol": "lavabo_mini", "duvar_bitisik": True},
    ],
    "antre": [
        {"isim": "Ayakkabılık",       "en": 1.00, "boy": 0.35, "sembol": "ayakkabiik",  "duvar_bitisik": True},
        {"isim": "Portmanto",         "en": 0.80, "boy": 0.30, "sembol": "portmanto",   "duvar_bitisik": True},
    ],
}

MIN_SIRKULASYON_BOSLUGU = 0.60  # metre — mobilya arası minimum geçiş boşluğu


def get_furniture_for_room(room_type: str) -> list[dict]:
    """Oda tipine göre mobilya listesi döndürür."""
    return MOBILYA_KUTUPHANESI.get(room_type, [])


def select_furniture_by_area(room_type: str, room_area: float) -> list[dict]:
    """Oda alanına göre uygun mobilya seti seçer."""
    all_furniture = get_furniture_for_room(room_type)
    if not all_furniture:
        return []

    # Toplam mobilya alanı oda alanının %60'ını geçmemeli
    max_furniture_area = room_area * 0.60
    selected = []
    total_area = 0

    for mob in all_furniture:
        mob_area = mob["en"] * mob["boy"]
        if total_area + mob_area <= max_furniture_area:
            selected.append(mob)
            total_area += mob_area

    return selected
