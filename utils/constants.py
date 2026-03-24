"""
Sabitler — Duvar kalınlıkları, varsayılan değerler ve genel ayarlar.
"""

# ── Duvar Kalınlıkları (metre) ──
DIS_DUVAR_KALINLIK = 0.25          # Dış duvar (tuğla + sıva)
IC_TASIYICI_DUVAR_KALINLIK = 0.20  # İç taşıyıcı duvar
IC_BOLME_DUVAR_KALINLIK = 0.10     # İç bölme duvar (alçıpan / tuğla)
MANTOLAMA_KALINLIK = 0.05          # Dış cephe mantolama

# ── Kat Yükseklikleri (metre) ──
KAT_YUKSEKLIGI = 3.00              # Brüt kat yüksekliği (döşemeden döşemeye)
IC_YUKSEKLIK = 2.60                # Net iç yükseklik (konut)
ISLAK_HACIM_IC_YUKSEKLIK = 2.40    # Islak hacim net iç yükseklik
DOSEME_KALINLIK = 0.30             # Döşeme kalınlığı (beton + kaplama)
SIVA_KALINLIK = 0.03               # Sıva kalınlığı (iç)

# ── Kapı Boyutları (metre) ──
BINA_GIRIS_KAPI_GENISLIK = 1.50    # Bina giriş kapısı (çift kanatlı)
DAIRE_GIRIS_KAPI_GENISLIK = 1.00   # Daire giriş kapısı
IC_KAPI_GENISLIK = 0.90            # İç oda kapıları
KAPI_YUKSEKLIK = 2.10              # Kapı yüksekliği
KAPI_ACILMA_ALANI = 0.90           # Kapı açılma yarıçapı

# ── Pencere Boyutları (metre) ──
PENCERE_ALT_SEVIYE = 0.90          # Yerden pencere alt kotu
PENCERE_YUKSEKLIK = 1.20           # Pencere yüksekliği
PENCERE_MIN_KOSEDEN_MESAFE = 0.40  # Pencere köşeden min mesafe

# ── Merdiven Ölçüleri ──
MERDIVEN_KOLU_GENISLIK = 1.20      # Konut ortak merdiven kolu genişliği
MERDIVEN_BASAMAK_YUKSEKLIK = 0.175 # Asansörlü binalarda max 0.18m
MERDIVEN_BASAMAK_GENISLIK = 0.27   # Minimum basamak genişliği
MERDIVEN_EVI_ALAN = 18.0           # Yaklaşık merdiven evi alanı (m²) — 2 kollu + sahanlık
SAHANLIK_GENISLIK = 1.20           # Sahanlık genişliği

# ── Asansör Ölçüleri ──
ASANSOR_KABIN_MIN_EN = 1.10        # Minimum asansör kabin eni
ASANSOR_KABIN_MIN_BOY = 1.40       # Minimum asansör kabin boyu
ASANSOR_KUYU_ALAN = 7.0            # Yaklaşık asansör kuyu alanı (m²)
ASANSOR_ZORUNLU_KAT = 4            # 4+ kat → asansör zorunlu

# ── Koridor Ölçüleri ──
BINA_GIRIS_KORIDOR_MIN = 1.50      # Bina giriş koridoru min genişlik
DAIRE_IC_KORIDOR_MIN = 1.10        # Daire iç koridoru min genişlik
KORIDOR_IDEAL_GENISLIK = 1.20      # İdeal koridor genişliği

# ── Ortak Alan Tahmini (m²) ──
GIRIS_HOLU_ALAN = 10.0             # Zemin kat giriş holü
SIGINAK_ORAN = 0.05                # Sığınak alanı / kat brüt alanı

# ── Balkon ──
BALKON_KORKULUK_YUKSEKLIK = 1.10   # Balkon korkuluk yüksekliği
BALKON_MIN_DERINLIK = 1.20         # Minimum balkon derinliği

# ── Yangın Güvenliği ──
KACIS_KAPI_MIN_GENISLIK = 0.80     # Kaçış kapısı minimum genişlik
MAX_YUKSEKLIK_DIS_MERDIVEN = 21.50 # Dış açık merdiven yapılabilecek max bina yüksekliği

# ── Hava Bacası / Işıklık ──
HAVA_BACASI_MIN_EN = 0.60          # Hava bacası minimum eni
HAVA_BACASI_MIN_BOY = 0.60         # Hava bacası minimum boyu
ISIKLIK_MAX_HACIM = 4              # Bir ışıklıktan her katta max faydalanacak piyes sayısı

# ── İmar Varsayılan Değerleri ──
VARSAYILAN_TAKS = 0.35
VARSAYILAN_KAKS = 1.40
VARSAYILAN_KAT_ADEDI = 4
VARSAYILAN_ON_BAHCE = 5.0
VARSAYILAN_YAN_BAHCE = 3.0
VARSAYILAN_ARKA_BAHCE = 3.0

# ── İnşaat Nizamları ──
INSAAT_NIZAMLARI = {
    "A": "Ayrık Nizam",
    "B": "Bitişik Nizam",
    "BL": "Blok Nizam",
}

# ── Daire Tipleri ──
DAIRE_TIPLERI = ["1+1", "2+1", "3+1", "4+1", "5+1"]

# ── Çizim Sabitleri ──
CIZIM_DIS_DUVAR_PX = 3             # Dış duvar çizgi kalınlığı (px)
CIZIM_IC_TASIYICI_PX = 2           # İç taşıyıcı duvar çizgi kalınlığı
CIZIM_IC_BOLME_PX = 1              # İç bölme duvar çizgi kalınlığı
CIZIM_OLCEK = "1:100"              # Varsayılan çizim ölçeği
