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
