"""
Türk Yapı Yönetmeliği Kuralları — Planlı Alanlar İmar Yönetmeliği.
Her kural bir dict olarak tanımlanır: min/max değerler, açıklama ve referans madde.
"""

# ── Minimum Oda Boyutları (m²) ──
MIN_ODA_ALANLARI = {
    "salon":        {"min_alan": 12.0, "aciklama": "Oturma odası minimum 12 m²"},
    "yatak_odasi":  {"min_alan": 9.0,  "aciklama": "Yatak odası minimum 9 m²"},
    "mutfak":       {"min_alan": 5.0,  "aciklama": "Mutfak minimum 5 m²"},
    "banyo":        {"min_alan": 3.5,  "aciklama": "Banyo minimum 3.5 m²"},
    "wc":           {"min_alan": 1.5,  "aciklama": "WC minimum 1.5 m²"},
    "antre":        {"min_alan": 3.0,  "aciklama": "Antre/Hol minimum 3 m²"},
    "koridor":      {"min_alan": 2.0,  "aciklama": "Koridor minimum 2 m²"},
    "balkon":       {"min_alan": 2.0,  "aciklama": "Balkon minimum 2 m²"},
}

# ── Minimum İç Yükseklikler (metre) ──
MIN_IC_YUKSEKLIKLER = {
    "iskan_kat":     2.60,  # İskan edilen katlar
    "islak_hacim":   2.40,  # Banyo, WC, koridor, antre
    "bodrum":        2.40,  # Bodrum kat
    "cati_arasi":    1.80,  # Çatı arası (eğik yüzey altında en düşük)
}

# ── Merdiven Kuralları ──
MERDIVEN_KURALLARI = {
    "kol_genislik_min": 1.20,          # metre — konut ortak merdiven
    "basamak_yukseklik_asansorlu": 0.18,   # max — asansörlü binalarda
    "basamak_yukseklik_asansorsuz": 0.16,  # max — asansörsüz binalarda
    "basamak_genislik_min": 0.27,      # metre
    "formul_min": 60,                  # 2a + b = 60-64 cm
    "formul_max": 64,
    "isik_zorunlu": True,              # Dış cephe veya ışıklıktan ışık alması zorunlu
}

# ── Koridor Kuralları ──
KORIDOR_KURALLARI = {
    "bina_giris_min": 1.50,            # Bina giriş koridoru min genişlik (metre)
    "daire_ic_min": 1.10,              # Daire iç koridoru min genişlik
}

# ── Kapı Kuralları ──
KAPI_KURALLARI = {
    "bina_giris_min": 1.50,            # Bina giriş kapısı min genişlik (çift kanatlı)
    "daire_giris_min": 1.00,           # Daire giriş kapısı min genişlik
    "ic_kapi_min": 0.90,               # İç oda kapıları min genişlik
    "kacis_kapisi_min": 0.80,          # Kaçış kapısı min genişlik
    "esik_yasak": True,                # Kapılarda eşik yapılamaz
}

# ── Pencere ve Havalandırma Kuralları ──
PENCERE_KURALLARI = {
    "oturma_odasi_dis_isik_zorunlu": True,
    "yatak_odasi_dis_isik_zorunlu": True,
    "islak_hacim_hava_bacasi_yeterli": True,
    "hava_bacasi_min_en": 0.60,        # metre
    "hava_bacasi_min_boy": 0.60,       # metre
    "isiklik_max_piyes": 4,            # Bir ışıklıktan max faydalanan oda sayısı / kat
}

# ── Asansör Kuralları ──
ASANSOR_KURALLARI = {
    "zorunlu_kat_sayisi": 4,           # 4+ kat (bodrum hariç) → zorunlu
    "kabin_min_en": 1.10,              # metre
    "kabin_min_boy": 1.40,             # metre
    "sedye_zorunlu_kat": 10,           # 10+ kat → sedye asansörü zorunlu
    "sedye_kabin_min_en": 1.20,        # metre
    "sedye_kabin_min_boy": 2.10,       # metre
    "sedye_kapi_min": 1.10,            # metre
}

# ── Yangın Güvenliği ──
YANGIN_KURALLARI = {
    "kacis_genislik_hesabi": "Binaların Yangından Korunması Hakkında Yönetmelik",
    "dis_merdiven_max_yukseklik": 21.50,  # metre — bu yüksekliğin üstünde dış merdiven yapılamaz
}

# ── Islak Hacim Kuralları ──
ISLAK_HACIM_KURALLARI = {
    "ayni_isikliga_acilamaz": True,    # WC/banyo odalarla aynı ışıklığa açılamaz
    "tefris_zorunlu": True,            # Islak hacimlerde tefriş zorunlu
}

# ── Otopark Kuralları ──
OTOPARK_KURALLARI = {
    "daire_basi_min_arac": 1,          # Her daire için minimum 1 araçlık otopark
    "acik_otopark_m2_arac": 17.5,      # Açık otopark araç başı alan (m²)
    "kapali_otopark_m2_arac": 32.5,    # Kapalı otopark araç başı alan (m²)
}

# ── Çekme Mesafesi Kuralları ──
CEKME_MESAFESI_KURALLARI = {
    "A": {  # Ayrık Nizam
        "on_bahce_min": 5.0,
        "yan_bahce_min": 3.0,
        "arka_bahce_min": 3.0,
        "aciklama": "Ayrık nizamda her dört taraftan çekme zorunlu",
    },
    "B": {  # Bitişik Nizam
        "on_bahce_min": 5.0,
        "yan_bahce_min": 0.0,   # Bir veya iki yan komşuya bitişik
        "arka_bahce_min": 3.0,
        "aciklama": "Bitişik nizamda yan bahçe zorunlu değil",
    },
    "BL": {  # Blok Nizam
        "on_bahce_min": 5.0,
        "yan_bahce_min": 3.0,
        "arka_bahce_min": 3.0,
        "aciklama": "Blok nizamda çekme mesafeleri imar planına göre",
    },
}


def validate_room(oda_tipi: str, alan: float) -> dict:
    """Odanın minimum alan kuralını kontrol et.

    Returns:
        {"gecerli": bool, "mesaj": str}
    """
    kural = MIN_ODA_ALANLARI.get(oda_tipi)
    if kural is None:
        return {"gecerli": True, "mesaj": f"'{oda_tipi}' için tanımlı kural yok, kontrol atlandı."}
    if alan < kural["min_alan"]:
        return {
            "gecerli": False,
            "mesaj": f"⚠️ {oda_tipi.replace('_', ' ').title()}: {alan:.1f} m² < minimum {kural['min_alan']} m². {kural['aciklama']}.",
        }
    return {"gecerli": True, "mesaj": f"✅ {oda_tipi.replace('_', ' ').title()}: {alan:.1f} m² ≥ {kural['min_alan']} m²"}


def validate_corridor_width(genislik: float, tur: str = "daire_ic") -> dict:
    """Koridor genişliği kontrolü."""
    min_val = KORIDOR_KURALLARI.get(f"{tur}_min", 1.10)
    if genislik < min_val:
        return {"gecerli": False, "mesaj": f"⚠️ Koridor genişliği {genislik:.2f}m < minimum {min_val}m"}
    return {"gecerli": True, "mesaj": f"✅ Koridor genişliği {genislik:.2f}m ≥ {min_val}m"}


def check_elevator_required(kat_sayisi: int) -> bool:
    """Asansör zorunluluğu kontrolü."""
    return kat_sayisi >= ASANSOR_KURALLARI["zorunlu_kat_sayisi"]
