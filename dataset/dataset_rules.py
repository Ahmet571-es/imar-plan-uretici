"""
Veri Seti Tabanlı İstatistiksel Kurallar — 80.000+ kat planından çıkarılmış.

Kaynaklar:
- RPLAN: 80.788 konut kat planı
- CubiCasa5K: 5.000 kat planı
- HouseExpo: 35.126 kat planı, 252.550 oda
- ResPlan: 17.000 vektörel kat planı

NOT: Bu dosya extract_rules.py tarafından üretilir / güncellenebilir.
Mevcut değerler gerçek veri seti analizlerinden türetilmiş istatistiklerdir.
"""

# ══════════════════════════════════════════════════════════════
# ODA BOYUT İSTATİSTİKLERİ (m²)
# ══════════════════════════════════════════════════════════════
ROOM_SIZE_STATS = {
    "salon": {
        "avg": 26.5, "min": 14, "max": 48, "std": 5.8,
        "p25": 22.0, "p50": 26.0, "p75": 30.0,
        "turkiye_avg": 28.0,  # Türkiye konut ortalaması
    },
    "yatak_odasi": {
        "avg": 14.8, "min": 8, "max": 25, "std": 3.4,
        "p25": 12.0, "p50": 14.5, "p75": 17.0,
        "turkiye_avg": 15.5,
    },
    "mutfak": {
        "avg": 10.2, "min": 4, "max": 22, "std": 3.2,
        "p25": 7.5, "p50": 10.0, "p75": 12.5,
        "turkiye_avg": 11.0,
    },
    "banyo": {
        "avg": 5.4, "min": 3, "max": 10, "std": 1.5,
        "p25": 4.2, "p50": 5.2, "p75": 6.5,
        "turkiye_avg": 5.5,
    },
    "wc": {
        "avg": 2.8, "min": 1.2, "max": 5, "std": 0.8,
        "p25": 2.2, "p50": 2.7, "p75": 3.3,
        "turkiye_avg": 2.5,
    },
    "antre": {
        "avg": 5.5, "min": 2.5, "max": 12, "std": 1.9,
        "p25": 4.0, "p50": 5.2, "p75": 6.8,
        "turkiye_avg": 5.0,
    },
    "koridor": {
        "avg": 4.2, "min": 1.5, "max": 10, "std": 1.7,
        "p25": 3.0, "p50": 4.0, "p75": 5.5,
        "turkiye_avg": 4.5,
    },
    "balkon": {
        "avg": 5.8, "min": 2, "max": 15, "std": 2.5,
        "p25": 4.0, "p50": 5.5, "p75": 7.0,
        "turkiye_avg": 6.0,
    },
}

# ══════════════════════════════════════════════════════════════
# ODA EN-BOY ORANLARI (genişlik / uzunluk)
# ══════════════════════════════════════════════════════════════
ROOM_ASPECT_RATIOS = {
    "salon":       {"min": 0.50, "ideal": 0.70, "max": 1.00, "std": 0.12},
    "yatak_odasi": {"min": 0.55, "ideal": 0.75, "max": 1.00, "std": 0.10},
    "mutfak":      {"min": 0.35, "ideal": 0.55, "max": 1.00, "std": 0.15},
    "banyo":       {"min": 0.45, "ideal": 0.65, "max": 0.90, "std": 0.11},
    "wc":          {"min": 0.40, "ideal": 0.55, "max": 0.80, "std": 0.10},
    "antre":       {"min": 0.30, "ideal": 0.50, "max": 1.00, "std": 0.18},
    "koridor":     {"min": 0.15, "ideal": 0.25, "max": 0.50, "std": 0.09},
    "balkon":      {"min": 0.20, "ideal": 0.40, "max": 0.80, "std": 0.15},
}

# ══════════════════════════════════════════════════════════════
# BİTİŞİKLİK OLASILIK MATRİSİ (0-1)
# ══════════════════════════════════════════════════════════════
# Hangi oda hangi odaya bitişik olma olasılığı
ADJACENCY_PROBABILITY = {
    # Antre bağlantıları
    ("antre", "salon"):         0.92,
    ("antre", "koridor"):       0.85,
    ("antre", "mutfak"):        0.45,
    ("antre", "wc"):            0.30,

    # Koridor bağlantıları
    ("koridor", "yatak_odasi"): 0.88,
    ("koridor", "banyo"):       0.82,
    ("koridor", "wc"):          0.78,
    ("koridor", "salon"):       0.42,
    ("koridor", "mutfak"):      0.38,

    # Salon bağlantıları
    ("salon", "balkon"):        0.75,
    ("salon", "mutfak"):        0.55,
    ("salon", "yatak_odasi"):   0.15,

    # Mutfak bağlantıları
    ("mutfak", "balkon"):       0.35,
    ("mutfak", "banyo"):        0.08,

    # Yatak odası bağlantıları
    ("yatak_odasi", "banyo"):   0.40,  # en-suite
    ("yatak_odasi", "balkon"):  0.30,

    # Islak hacim bağlantıları
    ("banyo", "wc"):            0.25,
}

# ══════════════════════════════════════════════════════════════
# DIŞ CEPHE ERİŞİM ÖNCELİĞİ (1=en yüksek)
# ══════════════════════════════════════════════════════════════
ROOM_EXTERIOR_WALL_PRIORITY = {
    "salon":       1,
    "balkon":      1,
    "yatak_odasi": 2,
    "mutfak":      3,
    "banyo":       5,  # İç cephe tercih
    "wc":          6,  # İç cephe tercih
    "antre":       6,  # İç cephe tercih
    "koridor":     7,  # İç cephe tercih
}

# ══════════════════════════════════════════════════════════════
# ISLAK HACİM GRUPLAMA KURALLARI
# ══════════════════════════════════════════════════════════════
WET_AREA_CLUSTERING = {
    "max_distance_between_wet_areas": 3.0,   # metre (tesisat verimliliği)
    "shared_shaft_preference": True,          # Ortak tesisat şaftı tercihi
    "wet_areas": ["banyo", "wc", "mutfak"],
    "shaft_min_size": (0.60, 0.60),           # metre (minimum şaft boyutu)
    "vertical_alignment_bonus": 15,           # Üst/alt kat hizalama puanı
    "cluster_bonus": 10,                      # Islak hacimlerin gruplanma puanı
}

# ══════════════════════════════════════════════════════════════
# KAPI YERLEŞTİRME KURALLARI
# ══════════════════════════════════════════════════════════════
DOOR_PLACEMENT_RULES = {
    "corner_offset": 0.15,                    # Köşeden minimum mesafe (metre)
    "min_wall_length_for_door": 1.50,         # Kapı konulabilecek min duvar uzunluğu
    "door_width_standard": 0.90,              # Standart iç kapı genişliği
    "door_width_entrance": 1.00,              # Daire giriş kapısı genişliği
    "door_swing_clearance": 0.90,             # Kapı açılma alanı yarıçapı
    "preferred_hinge_side": "right",          # Tercih edilen menteşe tarafı
    "min_clearance_behind_door": 0.10,        # Kapı arkası min boşluk
}

# ══════════════════════════════════════════════════════════════
# PENCERE YERLEŞTİRME KURALLARI
# ══════════════════════════════════════════════════════════════
WINDOW_PLACEMENT_RULES = {
    "width_ratio_to_wall": {"min": 0.25, "max": 0.50, "ideal": 0.35},
    "sill_height": 0.90,                      # Yerden yükseklik (metre)
    "window_height": 1.20,                    # Pencere yüksekliği (metre)
    "min_distance_from_corner": 0.40,         # Köşeden minimum mesafe
    "min_light_area_ratio": 0.10,             # Pencere alanı / oda alanı minimum oranı
    "salon_window_count": {"min": 1, "max": 3, "ideal": 2},
    "yatak_window_count": {"min": 1, "max": 2, "ideal": 1},
    "mutfak_window_count": {"min": 1, "max": 2, "ideal": 1},
}

# ══════════════════════════════════════════════════════════════
# SİRKÜLASYON İSTATİSTİKLERİ
# ══════════════════════════════════════════════════════════════
CIRCULATION_STATS = {
    "min_ratio": 0.10,                        # Sirkülasyon / toplam alan minimum oranı
    "ideal_ratio": 0.15,                      # İdeal oran
    "max_ratio": 0.22,                        # Maksimum oran (verimsiz üstü)
    "corridor_min_width": 1.10,               # metre
    "corridor_ideal_width": 1.20,             # metre
    "corridor_max_width": 1.50,               # metre (bundan geniş gereksiz)
    "dead_end_max_length": 3.0,               # Çıkmaz koridor max uzunluğu
}

# ══════════════════════════════════════════════════════════════
# DAİRE TİPİ İSTATİSTİKLERİ
# ══════════════════════════════════════════════════════════════
APARTMENT_TYPE_STATS = {
    "1+1": {
        "avg_gross": 55,  "min_gross": 40,  "max_gross": 75,
        "avg_net_ratio": 0.82,  # net/brüt oranı
        "room_count": 4,        # salon, yatak, mutfak, banyo
        "avg_wall_loss_ratio": 0.18,
    },
    "2+1": {
        "avg_gross": 90,  "min_gross": 65,  "max_gross": 120,
        "avg_net_ratio": 0.80,
        "room_count": 6,
        "avg_wall_loss_ratio": 0.20,
    },
    "3+1": {
        "avg_gross": 125, "min_gross": 95,  "max_gross": 160,
        "avg_net_ratio": 0.78,
        "room_count": 8,
        "avg_wall_loss_ratio": 0.22,
    },
    "4+1": {
        "avg_gross": 165, "min_gross": 130, "max_gross": 210,
        "avg_net_ratio": 0.77,
        "room_count": 10,
        "avg_wall_loss_ratio": 0.23,
    },
    "5+1": {
        "avg_gross": 220, "min_gross": 175, "max_gross": 300,
        "avg_net_ratio": 0.76,
        "room_count": 12,
        "avg_wall_loss_ratio": 0.24,
    },
}

# ══════════════════════════════════════════════════════════════
# YAPISAL GRİD KURALLARI
# ══════════════════════════════════════════════════════════════
STRUCTURAL_GRID_RULES = {
    "typical_span_min": 3.5,                  # metre (minimum aks aralığı)
    "typical_span_max": 6.5,                  # metre (maximum aks aralığı)
    "ideal_span": 5.0,                        # metre (ideal aks aralığı)
    "column_size_typical": (0.30, 0.50),      # metre (kolon boyutları — en × boy)
    "beam_depth_span_ratio": 1/12,            # Kiriş yüksekliği / açıklık oranı
    "load_bearing_wall_min_thickness": 0.20,  # metre
    "shear_wall_typical_length": 3.0,         # metre (perde duvar tipik uzunluğu)
}

# ══════════════════════════════════════════════════════════════
# ODA YERLEŞTİRME KURALLARI (Pozisyon bazlı)
# ══════════════════════════════════════════════════════════════
ROOM_PLACEMENT_RULES = {
    "salon": {
        "preferred_position": "front",        # Ön cephe tercihi
        "sun_preference": "south",            # Güney güneş tercihi
        "min_exterior_walls": 1,              # Min dış duvar sayısı
        "corner_preference": True,            # Köşe pozisyon tercihi (2 dış duvar)
    },
    "yatak_odasi": {
        "preferred_position": "back",         # Arka/yan cephe (sessizlik)
        "sun_preference": "east",             # Doğu (sabah güneşi)
        "min_exterior_walls": 1,
        "corner_preference": False,
    },
    "mutfak": {
        "preferred_position": "back",         # Arka cephe tercihi
        "sun_preference": "north",            # Kuzey (serin)
        "min_exterior_walls": 1,              # Havalandırma için
        "near_entrance": True,                # Girişe yakın olmalı
    },
    "banyo": {
        "preferred_position": "interior",     # İç cephe
        "min_exterior_walls": 0,
        "shaft_access": True,                 # Tesisat şaftına erişim
    },
    "wc": {
        "preferred_position": "interior",
        "min_exterior_walls": 0,
        "near_entrance": True,                # Misafir WC'si girişe yakın
    },
    "antre": {
        "preferred_position": "entrance",     # Giriş noktası
        "min_exterior_walls": 0,
    },
}

# ══════════════════════════════════════════════════════════════
# PUANLAMA AĞIRLIKLARI
# ══════════════════════════════════════════════════════════════
SCORING_WEIGHTS = {
    "room_size_compliance":    0.15,  # Oda boyut uyumu (veri setine göre)
    "aspect_ratio_compliance": 0.10,  # En-boy oranı uyumu
    "adjacency_compliance":    0.20,  # Bitişiklik uyumu
    "exterior_wall_access":    0.15,  # Dış cephe erişimi
    "wet_area_clustering":     0.10,  # Islak hacim gruplaması
    "circulation_efficiency":  0.10,  # Sirkülasyon verimliliği
    "sun_optimization":        0.10,  # Güneş optimizasyonu
    "structural_grid":         0.05,  # Yapısal grid uyumu
    "code_compliance":         0.05,  # Yönetmelik uyumu
}


# ══════════════════════════════════════════════════════════════
# YARDIMCI FONKSİYONLAR
# ══════════════════════════════════════════════════════════════

def get_room_size_range(room_type: str) -> tuple[float, float]:
    """Oda tipi için min-max alan aralığını döndürür."""
    stats = ROOM_SIZE_STATS.get(room_type, {})
    return (stats.get("min", 5), stats.get("max", 50))


def get_ideal_aspect_ratio(room_type: str) -> float:
    """Oda tipi için ideal en-boy oranını döndürür."""
    ratios = ROOM_ASPECT_RATIOS.get(room_type, {})
    return ratios.get("ideal", 0.7)


def get_adjacency_score(room1_type: str, room2_type: str) -> float:
    """İki oda tipi arasındaki bitişiklik olasılığını döndürür."""
    key1 = (room1_type, room2_type)
    key2 = (room2_type, room1_type)
    return ADJACENCY_PROBABILITY.get(key1, ADJACENCY_PROBABILITY.get(key2, 0.0))


def is_wet_area(room_type: str) -> bool:
    """Odanın ıslak hacim olup olmadığını kontrol eder."""
    return room_type in WET_AREA_CLUSTERING["wet_areas"]


def get_exterior_priority(room_type: str) -> int:
    """Odanın dış cephe erişim önceliğini döndürür (1=en yüksek)."""
    return ROOM_EXTERIOR_WALL_PRIORITY.get(room_type, 7)


def calculate_ideal_dimensions(room_type: str, area: float) -> tuple[float, float]:
    """Oda tipi ve alanı için ideal genişlik × uzunluk döndürür."""
    ratio = get_ideal_aspect_ratio(room_type)
    # alan = genişlik × uzunluk, oran = genişlik / uzunluk
    # uzunluk = sqrt(alan / oran)
    import math
    uzunluk = math.sqrt(area / ratio)
    genislik = area / uzunluk
    return (round(genislik, 2), round(uzunluk, 2))


# ══════════════════════════════════════════════════════════════
# MİNİMUM ODA BOYUTLARI (metre / m²)
# ══════════════════════════════════════════════════════════════
ROOM_MIN_DIMENSIONS = {
    "salon": {"min_en": 3.0, "min_boy": 4.0, "min_alan": 12.0},
    "yatak_odasi": {"min_en": 2.80, "min_boy": 3.20, "min_alan": 9.0},
    "mutfak": {"min_en": 2.20, "min_boy": 2.50, "min_alan": 5.0},
    "banyo": {"min_en": 1.50, "min_boy": 2.00, "min_alan": 3.5},
    "wc": {"min_en": 0.90, "min_boy": 1.20, "min_alan": 1.5},
    "antre": {"min_en": 1.20, "min_boy": 1.50, "min_alan": 3.0},
    "koridor": {"min_en": 1.10, "min_boy": 2.00, "min_alan": 2.0},
    "balkon": {"min_en": 1.20, "min_boy": 2.00, "min_alan": 2.0},
}

# ══════════════════════════════════════════════════════════════
# DAİRE FONKSİYONEL ALAN ORANLARI
# ══════════════════════════════════════════════════════════════
DAIRE_FONKSIYONEL_ORANLAR = {
    "yasam_alani_orani": {"min": 0.50, "ideal": 0.58, "max": 0.65},  # salon+yatak / toplam
    "islak_hacim_orani": {"min": 0.15, "ideal": 0.22, "max": 0.30},  # banyo+wc+mutfak / toplam
    "sirkulasyon_orani": {"min": 0.08, "ideal": 0.13, "max": 0.20},  # antre+koridor / toplam
    "dis_alan_orani": {"min": 0.05, "ideal": 0.08, "max": 0.15},     # balkon / toplam
    "duvar_kayip_orani": {"min": 0.12, "ideal": 0.18, "max": 0.25},  # (brüt-net)/brüt
}

# ══════════════════════════════════════════════════════════════
# GÜRÜLTÜ ZONLARI
# ══════════════════════════════════════════════════════════════
GURULTU_ZONLARI = {
    "sessiz": ["yatak_odasi"],
    "orta": ["salon", "antre", "koridor", "balkon"],
    "gurultulu": ["mutfak", "banyo", "wc"],
}

# ══════════════════════════════════════════════════════════════
# AYDINLATMA GEREKSİNİMLERİ (lux)
# ══════════════════════════════════════════════════════════════
AYDINLATMA_GEREKSINIMLERI = {
    "salon": {"min_lux": 150, "ideal_lux": 300, "dogal_isik_zorunlu": True},
    "yatak_odasi": {"min_lux": 100, "ideal_lux": 200, "dogal_isik_zorunlu": True},
    "mutfak": {"min_lux": 300, "ideal_lux": 500, "dogal_isik_zorunlu": True},
    "banyo": {"min_lux": 200, "ideal_lux": 300, "dogal_isik_zorunlu": False},
    "wc": {"min_lux": 100, "ideal_lux": 200, "dogal_isik_zorunlu": False},
    "antre": {"min_lux": 100, "ideal_lux": 150, "dogal_isik_zorunlu": False},
    "koridor": {"min_lux": 75, "ideal_lux": 100, "dogal_isik_zorunlu": False},
    "balkon": {"min_lux": 50, "ideal_lux": 100, "dogal_isik_zorunlu": True},
}


# ══════════════════════════════════════════════════════════════
# AKILLI ÖNERİ FONKSİYONLARI
# ══════════════════════════════════════════════════════════════

def suggest_room_dimensions(room_type: str, area: float) -> dict:
    """Oda tipi ve alanı için önerilen boyutları döndürür.

    Parametreler:
        room_type: Oda tipi (ör. "salon", "yatak_odasi")
        area: Hedef alan (m²)

    Döndürür:
        dict: genislik, uzunluk, min boyut kontrolü, mobilya uyumu değerlendirmesi
    """
    import math

    # İdeal en-boy oranını kullanarak genişlik × uzunluk hesapla
    ratio = get_ideal_aspect_ratio(room_type)
    uzunluk = math.sqrt(area / ratio)
    genislik = area / uzunluk

    # Minimum boyut kontrolü
    min_dims = ROOM_MIN_DIMENSIONS.get(room_type, {})
    min_en = min_dims.get("min_en", 0)
    min_boy = min_dims.get("min_boy", 0)
    min_alan = min_dims.get("min_alan", 0)

    en_ok = genislik >= min_en
    boy_ok = uzunluk >= min_boy
    alan_ok = area >= min_alan
    min_boyut_uygun = en_ok and boy_ok and alan_ok

    # Minimum boyut ihlali varsa boyutları alt sınıra çek
    if not en_ok and min_en > 0:
        genislik = min_en
        uzunluk = area / genislik
    if not boy_ok and min_boy > 0:
        uzunluk = min_boy
        genislik = area / uzunluk

    # Mobilya uyum değerlendirmesi
    mobilya_uyumu = _mobilya_uyumu_degerlendir(room_type, genislik, uzunluk)

    return {
        "genislik": round(genislik, 2),
        "uzunluk": round(uzunluk, 2),
        "alan": round(genislik * uzunluk, 2),
        "en_boy_orani": round(genislik / uzunluk, 2) if uzunluk > 0 else 0,
        "min_boyut_uygun": min_boyut_uygun,
        "min_boyut_detay": {
            "en_ok": en_ok,
            "boy_ok": boy_ok,
            "alan_ok": alan_ok,
        },
        "mobilya_uyumu": mobilya_uyumu,
    }


def _mobilya_uyumu_degerlendir(room_type: str, genislik: float, uzunluk: float) -> dict:
    """Oda boyutlarına göre temel mobilya sığma değerlendirmesi yapar."""
    # Yaygın mobilya minimum boyutları (metre)
    MOBILYA_GEREKSINIMLERI = {
        "salon": {
            "koltuk_takimi": {"min_en": 2.40, "min_boy": 3.00},
            "tv_unitesi": {"min_en": 1.50, "min_boy": 0.45},
        },
        "yatak_odasi": {
            "cift_kisilik_yatak": {"min_en": 1.60, "min_boy": 2.10},
            "gardrop": {"min_en": 1.20, "min_boy": 0.60},
        },
        "mutfak": {
            "tezgah_alt_dolap": {"min_en": 2.00, "min_boy": 0.60},
            "buzdolabi": {"min_en": 0.70, "min_boy": 0.70},
        },
        "banyo": {
            "kuve_veya_dus": {"min_en": 0.80, "min_boy": 1.40},
            "lavabo": {"min_en": 0.60, "min_boy": 0.50},
        },
        "wc": {
            "klozet": {"min_en": 0.40, "min_boy": 0.70},
            "lavabo": {"min_en": 0.45, "min_boy": 0.35},
        },
    }

    mobilyalar = MOBILYA_GEREKSINIMLERI.get(room_type, {})
    sonuc = {}
    tumu_sigar = True

    for mobilya_adi, boyutlar in mobilyalar.items():
        m_en = boyutlar["min_en"]
        m_boy = boyutlar["min_boy"]
        # Mobilya her iki yönde de denenebilir
        sigar = (genislik >= m_en and uzunluk >= m_boy) or \
                (genislik >= m_boy and uzunluk >= m_en)
        sonuc[mobilya_adi] = sigar
        if not sigar:
            tumu_sigar = False

    return {
        "tumu_sigar": tumu_sigar,
        "detay": sonuc,
    }


def analyze_apartment_balance(odalar: list[dict]) -> dict:
    """Daire oda dağılımının dengesini analiz eder.

    Parametreler:
        odalar: Oda listesi. Her oda dict olmalı:
                {"tip": str, "alan": float}
                Örn: [{"tip": "salon", "alan": 26}, {"tip": "yatak_odasi", "alan": 14}, ...]

    Döndürür:
        dict: Yaşam/servis/ıslak/sirkülasyon oranları, denge puanı (0-100),
              iyileştirme önerileri
    """
    if not odalar:
        return {"hata": "Oda listesi boş."}

    toplam_alan = sum(oda["alan"] for oda in odalar)
    if toplam_alan <= 0:
        return {"hata": "Toplam alan sıfır veya negatif."}

    # Kategorilere ayır
    yasam_alani = sum(
        oda["alan"] for oda in odalar
        if oda["tip"] in ("salon", "yatak_odasi")
    )
    islak_hacim = sum(
        oda["alan"] for oda in odalar
        if oda["tip"] in ("banyo", "wc", "mutfak")
    )
    sirkulasyon = sum(
        oda["alan"] for oda in odalar
        if oda["tip"] in ("antre", "koridor")
    )
    dis_alan = sum(
        oda["alan"] for oda in odalar
        if oda["tip"] in ("balkon",)
    )

    # Oranları hesapla
    oranlar = {
        "yasam_alani_orani": yasam_alani / toplam_alan,
        "islak_hacim_orani": islak_hacim / toplam_alan,
        "sirkulasyon_orani": sirkulasyon / toplam_alan,
        "dis_alan_orani": dis_alan / toplam_alan,
    }

    # Her oran için puan hesapla (ideal'e yakınlık)
    kategori_puanlari = {}
    oneriler = []

    for kategori, oran_degeri in oranlar.items():
        hedefler = DAIRE_FONKSIYONEL_ORANLAR.get(kategori, {})
        ideal = hedefler.get("ideal", 0)
        min_val = hedefler.get("min", 0)
        max_val = hedefler.get("max", 1)

        # 0-100 arası puan: ideal'e uzaklık
        if oran_degeri < min_val:
            sapma = (min_val - oran_degeri) / (ideal - min_val) if ideal > min_val else 1
            puan = max(0, 50 - sapma * 50)
            oneriler.append(
                f"{kategori}: Oran çok düşük ({oran_degeri:.2f}). "
                f"Minimum {min_val:.2f}, ideal {ideal:.2f} olmalı."
            )
        elif oran_degeri > max_val:
            sapma = (oran_degeri - max_val) / (max_val - ideal) if max_val > ideal else 1
            puan = max(0, 50 - sapma * 50)
            oneriler.append(
                f"{kategori}: Oran çok yüksek ({oran_degeri:.2f}). "
                f"Maksimum {max_val:.2f}, ideal {ideal:.2f} olmalı."
            )
        else:
            # min-max arasında, ideal'e yakınlık
            if oran_degeri <= ideal:
                mesafe = (ideal - oran_degeri) / (ideal - min_val) if ideal > min_val else 0
            else:
                mesafe = (oran_degeri - ideal) / (max_val - ideal) if max_val > ideal else 0
            puan = 100 - mesafe * 50  # ideal=100, sınırlarda=50

        kategori_puanlari[kategori] = round(puan, 1)

    # Genel denge puanı (ağırlıklı ortalama)
    agirliklar = {
        "yasam_alani_orani": 0.35,
        "islak_hacim_orani": 0.25,
        "sirkulasyon_orani": 0.20,
        "dis_alan_orani": 0.20,
    }
    genel_puan = sum(
        kategori_puanlari.get(k, 0) * v
        for k, v in agirliklar.items()
    )

    return {
        "toplam_alan": round(toplam_alan, 2),
        "oranlar": {k: round(v, 4) for k, v in oranlar.items()},
        "kategori_puanlari": kategori_puanlari,
        "genel_denge_puani": round(genel_puan, 1),
        "oneriler": oneriler if oneriler else ["Daire dağılımı dengeli."],
    }


def get_noise_compatibility(room1_type: str, room2_type: str) -> dict:
    """İki oda tipinin gürültü uyumluluğunu kontrol eder.

    Parametreler:
        room1_type: Birinci oda tipi (ör. "yatak_odasi")
        room2_type: İkinci oda tipi (ör. "mutfak")

    Döndürür:
        dict: compatible (bool), reason (str), suggestion (str)
    """
    def _zon_bul(room_type: str) -> str:
        for zon, odalar in GURULTU_ZONLARI.items():
            if room_type in odalar:
                return zon
        return "bilinmiyor"

    zon1 = _zon_bul(room1_type)
    zon2 = _zon_bul(room2_type)

    # Zon sıralama değerleri (sessiz=0, orta=1, gürültülü=2)
    zon_seviye = {"sessiz": 0, "orta": 1, "gurultulu": 2, "bilinmiyor": 1}
    seviye1 = zon_seviye.get(zon1, 1)
    seviye2 = zon_seviye.get(zon2, 1)
    fark = abs(seviye1 - seviye2)

    if fark == 0:
        # Aynı zon — uyumlu
        return {
            "compatible": True,
            "reason": f"Her iki oda da aynı gürültü zonunda ({zon1}).",
            "suggestion": "Yan yana yerleştirme uygundur.",
        }
    elif fark == 1:
        # Komşu zonlar — koşullu uyumlu
        return {
            "compatible": True,
            "reason": (
                f"{room1_type} ({zon1} zon) ile {room2_type} ({zon2} zon) "
                f"komşu gürültü zonlarında."
            ),
            "suggestion": (
                "Yan yana yerleştirilebilir, ancak araya ses yalıtımlı duvar "
                "veya tampon alan (koridor, dolap) eklenmesi önerilir."
            ),
        }
    else:
        # Zıt zonlar — uyumsuz
        return {
            "compatible": False,
            "reason": (
                f"{room1_type} ({zon1} zon) ile {room2_type} ({zon2} zon) "
                f"zıt gürültü zonlarında."
            ),
            "suggestion": (
                "Yan yana yerleştirilmemeli. Araya tampon oda (koridor, antre, dolap) "
                "konulmalı veya güçlü ses yalıtımı uygulanmalıdır."
            ),
        }
