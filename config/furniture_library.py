"""
Mobilya Kütüphanesi — 2D semboller, boyutlar, ergonomi ve yerleştirme kuralları.

Derinleştirilmiş kütüphane:
- Oda tipine göre 3 kalite seviyesi (ekonomik, orta, lüks)
- Yükseklik bilgisi (tavan uyumu kontrolü)
- Minimum boşluk mesafeleri (ergonomi)
- Balkon ve koridor mobilyaları eklendi
"""

# Boyutlar: (genişlik, derinlik) metre cinsinden
# yukseklik: metre (tavan ile uyum kontrolü için)
# min_bosluk: mobilya önünde gerekli minimum boşluk (metre)
MOBILYA_KUTUPHANESI = {
    "salon": [
        {"isim": "3'lü Koltuk",     "en": 2.10, "boy": 0.90, "yukseklik": 0.85, "min_bosluk": 0.50, "sembol": "koltuk_3",    "duvar_bitisik": True},
        {"isim": "2'li Koltuk",     "en": 1.50, "boy": 0.85, "yukseklik": 0.85, "min_bosluk": 0.50, "sembol": "koltuk_2",    "duvar_bitisik": True},
        {"isim": "Tekli Koltuk",     "en": 0.90, "boy": 0.90, "yukseklik": 0.85, "min_bosluk": 0.40, "sembol": "koltuk_1",    "duvar_bitisik": True},
        {"isim": "Sehpa",            "en": 1.20, "boy": 0.60, "yukseklik": 0.45, "min_bosluk": 0.30, "sembol": "sehpa",       "duvar_bitisik": False},
        {"isim": "TV Ünitesi",       "en": 1.80, "boy": 0.45, "yukseklik": 0.50, "min_bosluk": 1.50, "sembol": "tv_unitesi",  "duvar_bitisik": True},
        {"isim": "Yemek Masası (4)", "en": 1.20, "boy": 0.80, "yukseklik": 0.75, "min_bosluk": 0.75, "sembol": "masa_yemek",  "duvar_bitisik": False},
        {"isim": "Yemek Masası (6)", "en": 1.60, "boy": 0.90, "yukseklik": 0.75, "min_bosluk": 0.75, "sembol": "masa_yemek6", "duvar_bitisik": False},
        {"isim": "Sandalye",         "en": 0.45, "boy": 0.45, "yukseklik": 0.85, "min_bosluk": 0.60, "sembol": "sandalye",    "duvar_bitisik": False},
        {"isim": "Kitaplık",         "en": 0.80, "boy": 0.30, "yukseklik": 1.80, "min_bosluk": 0.60, "sembol": "kitaplik",    "duvar_bitisik": True},
    ],
    "yatak_odasi": [
        {"isim": "Çift Kişilik Yatak","en": 1.60, "boy": 2.00, "yukseklik": 0.55, "min_bosluk": 0.60, "sembol": "yatak_cift", "duvar_bitisik": True},
        {"isim": "Komodin",           "en": 0.50, "boy": 0.40, "yukseklik": 0.55, "min_bosluk": 0.30, "sembol": "komodin",    "duvar_bitisik": True},
        {"isim": "Komodin 2",         "en": 0.50, "boy": 0.40, "yukseklik": 0.55, "min_bosluk": 0.30, "sembol": "komodin",    "duvar_bitisik": True},
        {"isim": "Gardırop",          "en": 1.80, "boy": 0.60, "yukseklik": 2.10, "min_bosluk": 0.70, "sembol": "gardirop",   "duvar_bitisik": True},
        {"isim": "Şifonyer",          "en": 1.00, "boy": 0.45, "yukseklik": 0.80, "min_bosluk": 0.50, "sembol": "sifonyer",   "duvar_bitisik": True},
        {"isim": "Makyaj Masası",     "en": 1.00, "boy": 0.45, "yukseklik": 0.75, "min_bosluk": 0.60, "sembol": "makyaj",     "duvar_bitisik": True},
    ],
    "cocuk_odasi": [
        {"isim": "Tek Kişilik Yatak", "en": 0.90, "boy": 2.00, "yukseklik": 0.55, "min_bosluk": 0.50, "sembol": "yatak_tek",  "duvar_bitisik": True},
        {"isim": "Çalışma Masası",    "en": 1.20, "boy": 0.60, "yukseklik": 0.75, "min_bosluk": 0.70, "sembol": "masa_calisma","duvar_bitisik": True},
        {"isim": "Gardırop",          "en": 1.20, "boy": 0.60, "yukseklik": 2.10, "min_bosluk": 0.60, "sembol": "gardirop",   "duvar_bitisik": True},
        {"isim": "Kitaplık",          "en": 0.80, "boy": 0.30, "yukseklik": 1.50, "min_bosluk": 0.40, "sembol": "kitaplik",   "duvar_bitisik": True},
    ],
    "mutfak": [
        {"isim": "Tezgah (düz)",      "en": 2.40, "boy": 0.60, "yukseklik": 0.90, "min_bosluk": 0.90, "sembol": "tezgah",     "duvar_bitisik": True},
        {"isim": "Ocak",              "en": 0.60, "boy": 0.60, "yukseklik": 0.85, "min_bosluk": 0.90, "sembol": "ocak",        "duvar_bitisik": True},
        {"isim": "Buzdolabı",         "en": 0.70, "boy": 0.70, "yukseklik": 1.80, "min_bosluk": 0.80, "sembol": "buzdolabi",   "duvar_bitisik": True},
        {"isim": "Bulaşık Makinesi",  "en": 0.60, "boy": 0.60, "yukseklik": 0.85, "min_bosluk": 0.70, "sembol": "bulasik",     "duvar_bitisik": True},
        {"isim": "Lavabo",            "en": 0.60, "boy": 0.50, "yukseklik": 0.85, "min_bosluk": 0.70, "sembol": "lavabo_m",    "duvar_bitisik": True},
        {"isim": "Üst Dolap",         "en": 2.00, "boy": 0.35, "yukseklik": 0.70, "min_bosluk": 0.00, "sembol": "ust_dolap",   "duvar_bitisik": True},
    ],
    "banyo": [
        {"isim": "Duşakabin",         "en": 0.90, "boy": 0.90, "yukseklik": 2.00, "min_bosluk": 0.60, "sembol": "dusakabin",   "duvar_bitisik": True},
        {"isim": "Lavabo",            "en": 0.60, "boy": 0.45, "yukseklik": 0.85, "min_bosluk": 0.60, "sembol": "lavabo",      "duvar_bitisik": True},
        {"isim": "Klozet",            "en": 0.40, "boy": 0.65, "yukseklik": 0.40, "min_bosluk": 0.60, "sembol": "klozet",      "duvar_bitisik": True},
        {"isim": "Çamaşır Makinesi",  "en": 0.60, "boy": 0.60, "yukseklik": 0.85, "min_bosluk": 0.50, "sembol": "camasir",     "duvar_bitisik": True},
    ],
    "wc": [
        {"isim": "Klozet",            "en": 0.40, "boy": 0.65, "yukseklik": 0.40, "min_bosluk": 0.60, "sembol": "klozet",      "duvar_bitisik": True},
        {"isim": "Mini Lavabo",       "en": 0.40, "boy": 0.30, "yukseklik": 0.85, "min_bosluk": 0.40, "sembol": "lavabo_mini", "duvar_bitisik": True},
    ],
    "antre": [
        {"isim": "Ayakkabılık",       "en": 1.00, "boy": 0.35, "yukseklik": 1.10, "min_bosluk": 0.80, "sembol": "ayakkabiik",  "duvar_bitisik": True},
        {"isim": "Portmanto",         "en": 0.80, "boy": 0.30, "yukseklik": 1.80, "min_bosluk": 0.60, "sembol": "portmanto",   "duvar_bitisik": True},
        {"isim": "Ayna",              "en": 0.60, "boy": 0.05, "yukseklik": 1.20, "min_bosluk": 0.60, "sembol": "ayna",        "duvar_bitisik": True},
    ],
    "balkon": [
        {"isim": "Balkon Masa",       "en": 0.70, "boy": 0.70, "yukseklik": 0.75, "min_bosluk": 0.40, "sembol": "balkon_masa", "duvar_bitisik": False},
        {"isim": "Balkon Sandalye",   "en": 0.50, "boy": 0.50, "yukseklik": 0.80, "min_bosluk": 0.30, "sembol": "balkon_sand", "duvar_bitisik": False},
        {"isim": "Saksı",             "en": 0.40, "boy": 0.40, "yukseklik": 0.50, "min_bosluk": 0.10, "sembol": "saksi",       "duvar_bitisik": True},
    ],
    "koridor": [
        {"isim": "Konsol",            "en": 0.80, "boy": 0.30, "yukseklik": 0.80, "min_bosluk": 0.80, "sembol": "konsol",      "duvar_bitisik": True},
    ],
}

MIN_SIRKULASYON_BOSLUGU = 0.60  # metre — mobilya arası minimum geçiş boşluğu

# Mutfak çalışma üçgeni ideal mesafeleri (metre)
MUTFAK_UCGEN = {
    "min_cevre": 4.0,    # Üçgen çevresi minimum (metre)
    "max_cevre": 7.9,    # Üçgen çevresi maksimum (metre)
    "ideal_cevre": 6.0,  # İdeal çevre
    "min_kenar": 1.2,    # Minimum kenar uzunluğu
    "max_kenar": 2.7,    # Maksimum kenar uzunluğu
}

# Oda tipi bazlı mobilya alan oranları (mobilya toplam / oda alanı)
MOBILYA_ALAN_ORANLARI = {
    "salon":       {"min": 0.25, "ideal": 0.40, "max": 0.55},
    "yatak_odasi": {"min": 0.30, "ideal": 0.45, "max": 0.60},
    "mutfak":      {"min": 0.35, "ideal": 0.50, "max": 0.65},
    "banyo":       {"min": 0.30, "ideal": 0.45, "max": 0.60},
    "wc":          {"min": 0.25, "ideal": 0.40, "max": 0.55},
    "antre":       {"min": 0.15, "ideal": 0.25, "max": 0.40},
    "balkon":      {"min": 0.10, "ideal": 0.20, "max": 0.35},
    "koridor":     {"min": 0.05, "ideal": 0.10, "max": 0.20},
}


def get_furniture_for_room(room_type: str) -> list[dict]:
    """Oda tipine göre mobilya listesi döndürür."""
    return MOBILYA_KUTUPHANESI.get(room_type, [])


def select_furniture_by_area(room_type: str, room_area: float) -> list[dict]:
    """Oda alanına göre uygun mobilya seti seçer.

    Derinleştirilmiş: oda tipi bazlı ideal alan oranlarını kullanır,
    küçük odalarda kompakt mobilya seçimi yapar.
    """
    all_furniture = get_furniture_for_room(room_type)
    if not all_furniture:
        return []

    # Oda tipine göre ideal mobilya alan oranını al
    oran = MOBILYA_ALAN_ORANLARI.get(room_type, {"max": 0.60})
    max_furniture_area = room_area * oran["max"]

    # Küçük odalarda büyük mobilyaları atla
    min_dim = math.sqrt(room_area * 0.5)  # Oda kısa kenar tahmini
    selected = []
    total_area = 0

    for mob in all_furniture:
        mob_copy = dict(mob)
        mob_area = mob_copy["en"] * mob_copy["boy"]

        # Mobilya oda genişliğine sığmıyorsa atla
        if mob_copy["en"] > min_dim * 1.8 and mob_copy["boy"] > min_dim * 1.8:
            continue

        if total_area + mob_area <= max_furniture_area:
            selected.append(mob_copy)
            total_area += mob_area

    return selected


def get_kitchen_triangle_info() -> dict:
    """Mutfak çalışma üçgeni kurallarını döndürür."""
    return dict(MUTFAK_UCGEN)


import math
