"""
Deprem Risk Analizi — AFAD/TBDY 2018 parametreleri ve taşıyıcı sistem önerisi.

İyileştirmeler:
- AFAD API endpoint doğrulaması
- Kolon grid çizimi (overlay veri üretimi)
- Tasarım spektral ivme hesaplamaları (SDS, SD1) — TBDY Madde 2.3
- Deprem yer hareketi düzeyi (DD-1..DD-4) sınıflandırması
- Bina performans hedefi belirleme (BKS + DD düzeyine göre)
- Yapı davranış katsayısı (R) ve tahmini deprem yükü
- Temel tipi ve perde duvar oranı önerisi (zemin sınıfına göre)
- Kolon boyut önerisi (kat sayısına göre)
- TBDY 2018 madde referansları
"""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

ZEMIN_SINIFLARI = {
    "ZA": {"aciklama": "Saglam kaya", "Fs": 0.8, "F1": 0.8, "risk": "Cok Dusuk"},
    "ZB": {"aciklama": "Kaya", "Fs": 0.9, "F1": 0.8, "risk": "Dusuk"},
    "ZC": {"aciklama": "Siki zemin", "Fs": 1.0, "F1": 1.0, "risk": "Orta"},
    "ZD": {"aciklama": "Yumusak zemin", "Fs": 1.2, "F1": 1.5, "risk": "Yuksek"},
    "ZE": {"aciklama": "Cok yumusak zemin", "Fs": 1.5, "F1": 2.0, "risk": "Cok Yuksek"},
}

# Perde duvar minimum oranları — zemin sınıfına göre (%)
_PERDE_ORANLARI = {
    "ZA": 0.15,
    "ZB": 0.15,
    "ZC": 0.20,
    "ZD": 0.30,
    "ZE": 0.40,
}

# Kolon boyut önerileri — kat aralığına göre
_KOLON_BOYUT_TABLOSU = {
    "1-4": {"en_cm": 30, "boy_cm": 50, "aciklama": "30x50 cm", "min_alan_cm2": 1500},
    "5-7": {"en_cm": 40, "boy_cm": 60, "aciklama": "40x60 cm", "min_alan_cm2": 2400},
    "8-10": {"en_cm": 50, "boy_cm": 70, "aciklama": "50x70 cm", "min_alan_cm2": 3500},
    "10+": {"en_cm": 50, "boy_cm": 70, "aciklama": "50x70 cm (detayli analiz gerekir)", "min_alan_cm2": 3500},
}

# TBDY 2018 varsayılan madde referansları
_TBDY_REFERANSLAR_VARSAYILAN = [
    "TBDY 2018 Madde 2.1 — Deprem Yer Hareketi Duzeyleri",
    "TBDY 2018 Madde 2.2 — Deprem Yer Hareketi Tanimlari",
    "TBDY 2018 Madde 2.3 — Tasarim Spektral Ivme Katsayilari (SDS, SD1)",
    "TBDY 2018 Madde 2.4 — Yerel Zemin Etki Katsayilari (Fs, F1)",
    "TBDY 2018 Madde 3.3 — Bina Kullanim Sinifi ve Bina Onem Katsayisi",
    "TBDY 2018 Madde 3.4 — Bina Yukseklik Sinifi (BYS)",
    "TBDY 2018 Tablo 3.1 — Bina Performans Hedefleri",
    "TBDY 2018 Madde 4.1 — Deprem Tasarim Sinifi (DTS)",
    "TBDY 2018 Tablo 4.1 — Tasiyici Sistem Davranis Katsayisi (R)",
    "TBDY 2018 Madde 4.7 — Esdeger Deprem Yuku Yontemi",
    "TBDY 2018 Madde 7.3 — Kolon Boyutlandirma Kurallari",
    "TBDY 2018 Madde 16 — Temel Tasarimi Genel Kurallari",
    "TBDY 2018 Ek-A — Zemin Siniflari ve Amplifikasyon Katsayilari",
]


@dataclass
class KolonGrid:
    """Kolon grid bilgisi — kat planı üzerine overlay."""
    x_akslar: list = field(default_factory=list)
    y_akslar: list = field(default_factory=list)
    kolon_boyut: tuple = (0.30, 0.50)  # en x boy (metre)
    aks_isimleri_x: list = field(default_factory=list)
    aks_isimleri_y: list = field(default_factory=list)


@dataclass
class DepremAnalizi:
    """Deprem risk analizi sonucu."""
    latitude: float = 0.0
    longitude: float = 0.0
    ss: float = 0.0
    s1: float = 0.0
    zemin_sinifi: str = "ZC"
    bks: int = 3
    bys: int = 0
    deprem_bolgesi: str = ""
    risk_seviyesi: str = ""
    tasiyici_sistem_onerisi: str = ""
    kolon_grid_onerisi: str = ""
    perde_onerisi: str = ""
    detaylar: list = field(default_factory=list)
    kolon_grid: KolonGrid | None = None
    afad_api_basarili: bool = False

    # --- Genişletilmiş TBDY 2018 parametreleri ---
    tasarim_spektral_ivme_sds: float = 0.0
    tasarim_spektral_ivme_sd1: float = 0.0
    deprem_yer_hareketi_duzeyi: str = ""
    bina_performans_hedefi: str = ""
    zemin_buyutme_fs: float = 0.0
    zemin_buyutme_f1: float = 0.0
    temel_tipi_onerisi: str = ""
    perde_duvar_orani_min: float = 0.0
    kolon_boyut_onerisi: dict = field(default_factory=dict)
    yapi_davranis_katsayisi_r: float = 0.0
    tahmini_deprem_yuku_kn: float = 0.0
    risk_ozet: dict = field(default_factory=dict)
    tbdy_referanslar: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "Konum": f"({self.latitude:.4f}, {self.longitude:.4f})",
            "Ss (Kisa Periyot)": f"{self.ss:.3f}",
            "S1 (1 sn Periyot)": f"{self.s1:.3f}",
            "Zemin Sinifi": (f"{self.zemin_sinifi} — "
                             f"{ZEMIN_SINIFLARI.get(self.zemin_sinifi, {}).get('aciklama', '')}"),
            "Bina Kullanim Sinifi": f"BKS-{self.bks}",
            "Bina Yukseklik Sinifi": f"BYS-{self.bys}",
            "Risk Seviyesi": self.risk_seviyesi,
            "Tasiyici Sistem Onerisi": self.tasiyici_sistem_onerisi,
            "Kolon Grid Onerisi": self.kolon_grid_onerisi,
            "AFAD API": "Basarili" if self.afad_api_basarili else "Fallback tahmin",
            # Genişletilmiş alanlar
            "SDS (Tasarim Spektral Ivme)": f"{self.tasarim_spektral_ivme_sds:.3f}",
            "SD1 (Tasarim Spektral Ivme)": f"{self.tasarim_spektral_ivme_sd1:.3f}",
            "Deprem Yer Hareketi Duzeyi": self.deprem_yer_hareketi_duzeyi,
            "Bina Performans Hedefi": self.bina_performans_hedefi,
            "Zemin Buyutme Fs": f"{self.zemin_buyutme_fs:.2f}",
            "Zemin Buyutme F1": f"{self.zemin_buyutme_f1:.2f}",
            "Temel Tipi Onerisi": self.temel_tipi_onerisi,
            "Perde Duvar Orani Min (%)": f"{self.perde_duvar_orani_min:.2f}",
            "Kolon Boyut Onerisi": self.kolon_boyut_onerisi.get("aciklama", ""),
            "Yapi Davranis Katsayisi (R)": f"{self.yapi_davranis_katsayisi_r:.1f}",
            "Tahmini Deprem Yuku (kN)": f"{self.tahmini_deprem_yuku_kn:.1f}",
        }

    def to_detailed_dict(self) -> dict:
        """Genişletilmiş görünüm — tüm analiz verilerini, kolon grid
        detaylarını, risk özetini ve TBDY referanslarını içerir."""
        base = self.to_dict()
        base.update({
            "Deprem Bolgesi": self.deprem_bolgesi,
            "Perde Onerisi": self.perde_onerisi,
            "AFAD API Basarili": self.afad_api_basarili,
            "Detaylar": list(self.detaylar),
            "Kolon Boyut Detay": dict(self.kolon_boyut_onerisi),
            "Risk Ozet": dict(self.risk_ozet),
            "TBDY Referanslar": list(self.tbdy_referanslar),
            "Kolon Grid": {
                "x_akslar": self.kolon_grid.x_akslar if self.kolon_grid else [],
                "y_akslar": self.kolon_grid.y_akslar if self.kolon_grid else [],
                "kolon_boyut_m": list(self.kolon_grid.kolon_boyut) if self.kolon_grid else [],
                "aks_isimleri_x": self.kolon_grid.aks_isimleri_x if self.kolon_grid else [],
                "aks_isimleri_y": self.kolon_grid.aks_isimleri_y if self.kolon_grid else [],
            },
        })
        return base


def deprem_risk_analizi(
    latitude: float = 39.93,
    longitude: float = 32.86,
    kat_sayisi: int = 4,
    zemin_sinifi: str = "ZC",
    ss_override: float = 0,
    s1_override: float = 0,
    bina_genisligi: float = 12.0,
    bina_derinligi: float = 10.0,
) -> DepremAnalizi:
    """Deprem risk analizi yapar."""
    sonuc = DepremAnalizi(
        latitude=latitude, longitude=longitude,
        zemin_sinifi=zemin_sinifi,
    )

    # Deprem parametreleri
    if ss_override > 0:
        sonuc.ss = ss_override
    else:
        sonuc.ss, sonuc.afad_api_basarili = _estimate_ss(latitude, longitude)

    if s1_override > 0:
        sonuc.s1 = s1_override
    else:
        sonuc.s1 = sonuc.ss * 0.35

    # Ham Ss/S1 — SDS/SD1 hesabı için amplifikasyon öncesi değerler
    ss_ham = sonuc.ss
    s1_ham = sonuc.s1

    # Zemin amplifikasyonu
    zemin_info = ZEMIN_SINIFLARI.get(zemin_sinifi, ZEMIN_SINIFLARI["ZC"])
    fs = zemin_info["Fs"]
    f1 = zemin_info.get("F1", 1.0)
    sonuc.ss *= fs
    sonuc.s1 *= fs

    # Zemin büyütme katsayılarını kaydet
    sonuc.zemin_buyutme_fs = fs
    sonuc.zemin_buyutme_f1 = f1

    # Risk seviyesi
    if sonuc.ss < 0.25:
        sonuc.risk_seviyesi = "Dusuk"
        sonuc.deprem_bolgesi = "4. Derece"
    elif sonuc.ss < 0.50:
        sonuc.risk_seviyesi = "Orta"
        sonuc.deprem_bolgesi = "3. Derece"
    elif sonuc.ss < 0.75:
        sonuc.risk_seviyesi = "Yuksek"
        sonuc.deprem_bolgesi = "2. Derece"
    else:
        sonuc.risk_seviyesi = "Cok Yuksek"
        sonuc.deprem_bolgesi = "1. Derece"

    # BYS
    bina_yuk = kat_sayisi * 3.0
    if bina_yuk <= 17.5:
        sonuc.bys = 7
    elif bina_yuk <= 25:
        sonuc.bys = 6
    elif bina_yuk <= 40:
        sonuc.bys = 5
    elif bina_yuk <= 56:
        sonuc.bys = 4
    else:
        sonuc.bys = 3

    # Taşıyıcı sistem önerisi
    if kat_sayisi <= 4:
        sonuc.tasiyici_sistem_onerisi = "Betonarme Cerceve VEYA Tunel Kalip"
        sonuc.kolon_grid_onerisi = "4.0m x 5.0m aks araligi"
        sonuc.perde_onerisi = "Min 2 adet perde duvar (her yonde)"
        grid_x = 4.0
        grid_y = 5.0
    elif kat_sayisi <= 8:
        sonuc.tasiyici_sistem_onerisi = "Betonarme Perde-Cerceve Sistem"
        sonuc.kolon_grid_onerisi = "4.5m x 5.5m aks araligi"
        sonuc.perde_onerisi = "Min 4 adet perde duvar + cerceve"
        grid_x = 4.5
        grid_y = 5.5
    else:
        sonuc.tasiyici_sistem_onerisi = "Perde Agirlikli Betonarme Sistem"
        sonuc.kolon_grid_onerisi = "5.0m x 6.0m aks araligi"
        sonuc.perde_onerisi = "Perde orani min %1.5 (her yonde)"
        grid_x = 5.0
        grid_y = 6.0

    # Kolon grid hesapla (overlay veri)
    sonuc.kolon_grid = _calculate_column_grid(
        bina_genisligi, bina_derinligi, grid_x, grid_y, kat_sayisi
    )

    # Detaylar (temel bilgiler — genişletilmiş hesaplamalar sonrası eklenir)
    sonuc.detaylar = [
        "TBDY 2018 parametreleri kullanilmistir",
        f"Bina yuksekligi tahmini: {bina_yuk:.0f}m ({kat_sayisi} kat x 3m)",
        f"Zemin sinifi: {zemin_sinifi} ({zemin_info['aciklama']})",
        "Kesin degerler icin AFAD TDTH haritasindan sorgulanmalidir: "
        "https://tdth.afad.gov.tr/",
        "Zemin etudu raporu zorunludur",
    ]

    if sonuc.ss > 0.50:
        sonuc.detaylar.append(
            "Yuksek deprem riski — perde duvar sayisi artirilmali")
    if zemin_sinifi in ("ZD", "ZE"):
        sonuc.detaylar.append(
            "Yumusak zemin — zemin iyilestirmesi gerekebilir")

    # =====================================================================
    # TBDY 2018 Genişletilmiş Hesaplamalar
    # =====================================================================

    # --- SDS ve SD1 hesabı (TBDY 2018 Madde 2.3) ---
    # SDS = Ss × Fs × (2/3) ve SD1 = S1 × F1 × (2/3)
    # ss_ham: amplifikasyon öncesi Ss; s1_ham: amplifikasyon öncesi S1
    sonuc.tasarim_spektral_ivme_sds = ss_ham * fs * (2.0 / 3.0)
    sonuc.tasarim_spektral_ivme_sd1 = s1_ham * f1 * (2.0 / 3.0)

    # --- Deprem Yer Hareketi Düzeyi (DD-1 .. DD-4) ---
    # Amplifikasyon öncesi Ss değerine göre sınıflandırma
    if ss_ham > 1.5:
        sonuc.deprem_yer_hareketi_duzeyi = "DD-1 (En buyuk deprem)"
    elif ss_ham > 0.75:
        sonuc.deprem_yer_hareketi_duzeyi = "DD-2 (Standart tasarim depremi)"
    elif ss_ham > 0.33:
        sonuc.deprem_yer_hareketi_duzeyi = "DD-3 (Sik tekrarlanan deprem)"
    else:
        sonuc.deprem_yer_hareketi_duzeyi = "DD-4 (Servis depremi)"

    # --- Bina Performans Hedefi (BKS + DD düzeyi) ---
    sonuc.bina_performans_hedefi = _performans_hedefi_belirle(
        sonuc.bks, sonuc.deprem_yer_hareketi_duzeyi
    )

    # --- Yapı Davranış Katsayısı R (TBDY Tablo 4.1) ---
    # Taşıyıcı sistem tipine göre:
    #   Tünel kalıp sistemleri → R = 4
    #   Normal çerçeve / perde-çerçeve → R = 6
    #   Süneklik düzeyi yüksek özel moment çerçevesi → R = 8
    if "Tunel Kalip" in sonuc.tasiyici_sistem_onerisi:
        sonuc.yapi_davranis_katsayisi_r = 4.0
    elif "Perde" in sonuc.tasiyici_sistem_onerisi:
        sonuc.yapi_davranis_katsayisi_r = 6.0
    else:
        sonuc.yapi_davranis_katsayisi_r = 8.0

    # --- Temel Tipi Önerisi (zemin sınıfına göre) ---
    if zemin_sinifi in ("ZA", "ZB"):
        sonuc.temel_tipi_onerisi = "Tekil / Surekli Temel (saglam zemin)"
    elif zemin_sinifi == "ZC":
        sonuc.temel_tipi_onerisi = "Radye Temel (orta sertlikte zemin)"
    else:  # ZD, ZE
        sonuc.temel_tipi_onerisi = (
            "Kazikli Temel (yumusak zemin — fore kazik / mini kazik onerilir)"
        )

    # --- Perde Duvar Minimum Oranı (%) ---
    sonuc.perde_duvar_orani_min = _PERDE_ORANLARI.get(zemin_sinifi, 0.20)

    # --- Kolon Boyut Önerisi (kat sayısına göre) ---
    if kat_sayisi <= 4:
        sonuc.kolon_boyut_onerisi = dict(_KOLON_BOYUT_TABLOSU["1-4"])
    elif kat_sayisi <= 7:
        sonuc.kolon_boyut_onerisi = dict(_KOLON_BOYUT_TABLOSU["5-7"])
    elif kat_sayisi <= 10:
        sonuc.kolon_boyut_onerisi = dict(_KOLON_BOYUT_TABLOSU["8-10"])
    else:
        sonuc.kolon_boyut_onerisi = dict(_KOLON_BOYUT_TABLOSU["10+"])

    # --- Tahmini Deprem Yükü (kN) ---
    # W = 1.2 ton/m2 x toplam insaat alani
    # V = SDS x W / R  (TBDY Madde 4.7 Esdeger Deprem Yuku Yontemi)
    kat_alani = bina_genisligi * bina_derinligi  # m2
    toplam_alan = kat_alani * kat_sayisi  # m2
    w_ton = 1.2 * toplam_alan  # ton
    w_kn = w_ton * 9.81  # kN (1 ton ~ 9.81 kN)
    sds = sonuc.tasarim_spektral_ivme_sds
    r = sonuc.yapi_davranis_katsayisi_r
    sonuc.tahmini_deprem_yuku_kn = (sds * w_kn / r) if r > 0 else 0.0

    # --- TBDY Madde Referansları ---
    sonuc.tbdy_referanslar = list(_TBDY_REFERANSLAR_VARSAYILAN)
    # Bağlama özgü ek referanslar
    if zemin_sinifi in ("ZD", "ZE"):
        sonuc.tbdy_referanslar.append(
            "TBDY 2018 Madde 16.5 — Kazikli Temeller Icin Ozel Kurallar"
        )
    if kat_sayisi > 8:
        sonuc.tbdy_referanslar.append(
            "TBDY 2018 Madde 4.5 — Yuksek Binalar Icin Ek Kurallar"
        )
    if sonuc.risk_seviyesi == "Cok Yuksek":
        sonuc.tbdy_referanslar.append(
            "TBDY 2018 Madde 13 — Deprem Etkisi Altinda Mevcut Yapilarin Degerlendirilmesi"
        )

    # --- Risk Özet Sözlüğü ---
    sonuc.risk_ozet = {
        "deprem_bolgesi": sonuc.deprem_bolgesi,
        "risk_seviyesi": sonuc.risk_seviyesi,
        "dd_duzeyi": sonuc.deprem_yer_hareketi_duzeyi,
        "performans_hedefi": sonuc.bina_performans_hedefi,
        "sds": round(sonuc.tasarim_spektral_ivme_sds, 4),
        "sd1": round(sonuc.tasarim_spektral_ivme_sd1, 4),
        "zemin_buyutme_fs": sonuc.zemin_buyutme_fs,
        "zemin_buyutme_f1": sonuc.zemin_buyutme_f1,
        "r_katsayisi": sonuc.yapi_davranis_katsayisi_r,
        "tahmini_deprem_yuku_kn": round(sonuc.tahmini_deprem_yuku_kn, 1),
        "temel_tipi": sonuc.temel_tipi_onerisi,
        "perde_orani_min_pct": sonuc.perde_duvar_orani_min,
        "kolon_boyut": sonuc.kolon_boyut_onerisi.get("aciklama", ""),
        "zemin_sinifi": zemin_sinifi,
        "zemin_risk": zemin_info["risk"],
        "toplam_alan_m2": round(toplam_alan, 1),
        "bina_agirlik_kn": round(w_kn, 1),
        "tasiyici_sistem": sonuc.tasiyici_sistem_onerisi,
    }

    # Detaylara genişletilmiş bilgiler ekle
    sonuc.detaylar.extend([
        f"SDS={sonuc.tasarim_spektral_ivme_sds:.3f}, "
        f"SD1={sonuc.tasarim_spektral_ivme_sd1:.3f} (TBDY Madde 2.3)",
        f"Zemin buyutme katsayilari: Fs={fs:.2f}, F1={f1:.2f}",
        f"Deprem yer hareketi duzeyi: {sonuc.deprem_yer_hareketi_duzeyi}",
        f"Performans hedefi: {sonuc.bina_performans_hedefi}",
        f"Yapi davranis katsayisi R={sonuc.yapi_davranis_katsayisi_r:.1f}",
        f"Tahmini deprem yuku: {sonuc.tahmini_deprem_yuku_kn:.1f} kN "
        f"(W={w_kn:.0f} kN, alan={toplam_alan:.0f} m2)",
        f"Temel onerisi: {sonuc.temel_tipi_onerisi}",
        f"Perde duvar min orani: %{sonuc.perde_duvar_orani_min:.2f}",
        f"Kolon boyut onerisi: {sonuc.kolon_boyut_onerisi.get('aciklama', '')}",
    ])

    return sonuc


def _performans_hedefi_belirle(bks: int, dd_duzeyi: str) -> str:
    """BKS ve DD düzeyine göre bina performans hedefini belirler.

    TBDY 2018 Tablo 3.1 — Bina Performans Hedefleri:
    - BKS-1 (onemli bina):   DD-1/DD-2 → Kontrollu Hasar (KH)
                              DD-3/DD-4 → Sinirli Hasar (SH)
    - BKS-2 (normal bina):   DD-1/DD-2 → Kontrollu Hasar (KH)
                              DD-3/DD-4 → Kontrollu Hasar (KH)
    - BKS-3 (dusuk onemli):  DD-1/DD-2 → Gocme Oncesi (GO)
                              DD-3/DD-4 → Kontrollu Hasar (KH)
    """
    yuksek_dd = ("DD-1" in dd_duzeyi or "DD-2" in dd_duzeyi)

    if bks == 1:
        if yuksek_dd:
            return "Kontrollu Hasar (KH) — onemli bina, buyuk deprem"
        return "Sinirli Hasar (SH) — onemli bina, kucuk deprem"
    elif bks == 2:
        return "Kontrollu Hasar (KH) — normal bina"
    else:  # BKS-3 veya tanımsız
        if yuksek_dd:
            return "Gocme Oncesi (GO) — dusuk onemli bina, buyuk deprem"
        return "Kontrollu Hasar (KH) — dusuk onemli bina, kucuk deprem"


def _calculate_column_grid(
    bina_w: float, bina_h: float,
    grid_x: float, grid_y: float,
    kat_sayisi: int,
) -> KolonGrid:
    """Kolon grid pozisyonlarını hesaplar."""
    import math

    grid = KolonGrid()

    # X aksları
    n_x = max(2, math.ceil(bina_w / grid_x) + 1)
    actual_x = bina_w / (n_x - 1) if n_x > 1 else bina_w
    grid.x_akslar = [i * actual_x for i in range(n_x)]
    grid.aks_isimleri_x = [chr(65 + i) for i in range(n_x)]  # A, B, C...

    # Y aksları
    n_y = max(2, math.ceil(bina_h / grid_y) + 1)
    actual_y = bina_h / (n_y - 1) if n_y > 1 else bina_h
    grid.y_akslar = [i * actual_y for i in range(n_y)]
    grid.aks_isimleri_y = [str(i + 1) for i in range(n_y)]  # 1, 2, 3...

    # Kolon boyutu
    if kat_sayisi <= 4:
        grid.kolon_boyut = (0.30, 0.50)
    elif kat_sayisi <= 8:
        grid.kolon_boyut = (0.35, 0.60)
    else:
        grid.kolon_boyut = (0.40, 0.70)

    return grid


def _estimate_ss(lat: float, lon: float) -> tuple[float, bool]:
    """AFAD TDTH API'den Ss değeri çeker, başarısız olursa tahmin yapar.

    Returns:
        (ss_value, api_basarili)
    """
    # Yöntem 1: AFAD TDTH API
    try:
        import requests
        url = "https://tdth.afad.gov.tr/api/spectrum"
        params = {"latitude": lat, "longitude": lon, "soilType": "ZC"}
        resp = requests.get(url, params=params, timeout=10,
                           headers={"User-Agent": "Mozilla/5.0",
                                    "Accept": "application/json"})
        if resp.status_code == 200:
            data = resp.json()
            ss = data.get("Ss", data.get("ss", 0))
            if ss and float(ss) > 0:
                logger.info(f"AFAD API'den Ss={ss} alindi ({lat:.2f}, "
                            f"{lon:.2f})")
                return float(ss), True
    except Exception as e:
        logger.debug(f"AFAD API hatasi: {e}")

    # Yöntem 2: deprem.afad.gov.tr
    try:
        import requests
        url2 = (f"https://deprem.afad.gov.tr/api/spectral-values?"
                f"lat={lat}&lng={lon}&soilType=ZC")
        resp2 = requests.get(url2, timeout=10,
                             headers={"User-Agent": "Mozilla/5.0"})
        if resp2.status_code == 200:
            data2 = resp2.json()
            ss = data2.get("Ss", data2.get("ss", 0))
            if ss and float(ss) > 0:
                logger.info(f"AFAD alt. API'den Ss={ss} alindi")
                return float(ss), True
    except Exception as e:
        logger.debug(f"AFAD alt. API hatasi: {e}")

    # Yöntem 3: Hardcoded tahmin (fallback)
    logger.warning("AFAD API erisilemedi, tahmin kullaniliyor")
    base = 0.40
    if 39.5 < lat < 41.5 and 27 < lon < 42:
        base = 0.75
    elif lat < 37.5 and 28 < lon < 32:
        base = 0.60
    elif 37 < lat < 39 and 35 < lon < 37:
        base = 0.65
    elif lon > 42:
        base = 0.30
    return base, False


def test_afad_api() -> dict:
    """AFAD API bağlantı testi."""
    results = {"tdth_api": False, "deprem_api": False, "details": []}

    try:
        import requests
        resp = requests.get(
            "https://tdth.afad.gov.tr/api/spectrum",
            params={"latitude": 39.93, "longitude": 32.86,
                    "soilType": "ZC"},
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        results["tdth_api"] = resp.status_code == 200
        results["details"].append(f"TDTH API: HTTP {resp.status_code}")
    except Exception as e:
        results["details"].append(f"TDTH API hata: {e}")

    try:
        import requests
        resp2 = requests.get(
            "https://deprem.afad.gov.tr/api/spectral-values",
            params={"lat": 39.93, "lng": 32.86, "soilType": "ZC"},
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        results["deprem_api"] = resp2.status_code == 200
        results["details"].append(
            f"Deprem API: HTTP {resp2.status_code}")
    except Exception as e:
        results["details"].append(f"Deprem API hata: {e}")

    return results
