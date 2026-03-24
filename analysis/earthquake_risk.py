"""
Deprem Risk Analizi — AFAD/TBDY 2018 parametreleri ve taşıyıcı sistem önerisi.
"""

from dataclasses import dataclass, field


# ── Zemin sınıfları ──
ZEMIN_SINIFLARI = {
    "ZA": {"aciklama": "Sağlam kaya", "Fs": 0.8, "risk": "Çok Düşük"},
    "ZB": {"aciklama": "Kaya", "Fs": 0.9, "risk": "Düşük"},
    "ZC": {"aciklama": "Sıkı zemin", "Fs": 1.0, "risk": "Orta"},
    "ZD": {"aciklama": "Yumuşak zemin", "Fs": 1.2, "risk": "Yüksek"},
    "ZE": {"aciklama": "Çok yumuşak zemin", "Fs": 1.5, "risk": "Çok Yüksek"},
}


@dataclass
class DepremAnalizi:
    """Deprem risk analizi sonucu."""
    latitude: float = 0.0
    longitude: float = 0.0
    ss: float = 0.0              # Kısa periyot tasarım spektral ivme katsayısı
    s1: float = 0.0              # 1 sn periyot katsayısı
    zemin_sinifi: str = "ZC"
    bks: int = 3                 # Bina Kullanım Sınıfı (konut=3)
    bys: int = 0                 # Bina Yükseklik Sınıfı
    deprem_bolgesi: str = ""
    risk_seviyesi: str = ""
    tasiyici_sistem_onerisi: str = ""
    kolon_grid_onerisi: str = ""
    perde_onerisi: str = ""
    detaylar: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "Konum": f"({self.latitude:.4f}, {self.longitude:.4f})",
            "Ss (Kısa Periyot)": f"{self.ss:.3f}",
            "S1 (1 sn Periyot)": f"{self.s1:.3f}",
            "Zemin Sınıfı": f"{self.zemin_sinifi} — {ZEMIN_SINIFLARI.get(self.zemin_sinifi, {}).get('aciklama', '')}",
            "Bina Kullanım Sınıfı": f"BKS-{self.bks}",
            "Bina Yükseklik Sınıfı": f"BYS-{self.bys}",
            "Risk Seviyesi": self.risk_seviyesi,
            "Taşıyıcı Sistem Önerisi": self.tasiyici_sistem_onerisi,
            "Kolon Grid Önerisi": self.kolon_grid_onerisi,
        }


def deprem_risk_analizi(
    latitude: float = 39.93,
    longitude: float = 32.86,
    kat_sayisi: int = 4,
    zemin_sinifi: str = "ZC",
    ss_override: float = 0,
    s1_override: float = 0,
) -> DepremAnalizi:
    """Deprem risk analizi yapar.

    Args:
        latitude: Enlem.
        longitude: Boylam.
        kat_sayisi: Bina kat sayısı.
        zemin_sinifi: Zemin sınıfı (ZA-ZE).
        ss_override: Manuel Ss değeri (0=otomatik tahmin).
        s1_override: Manuel S1 değeri.
    """
    sonuc = DepremAnalizi(
        latitude=latitude,
        longitude=longitude,
        zemin_sinifi=zemin_sinifi,
    )

    # ── Deprem parametreleri (basitleştirilmiş tahmin) ──
    if ss_override > 0:
        sonuc.ss = ss_override
    else:
        sonuc.ss = _estimate_ss(latitude, longitude)

    if s1_override > 0:
        sonuc.s1 = s1_override
    else:
        sonuc.s1 = sonuc.ss * 0.35  # Yaklaşık oran

    # Zemin amplifikasyonu
    zemin_info = ZEMIN_SINIFLARI.get(zemin_sinifi, ZEMIN_SINIFLARI["ZC"])
    sonuc.ss *= zemin_info["Fs"]
    sonuc.s1 *= zemin_info["Fs"]

    # ── Risk seviyesi ──
    if sonuc.ss < 0.25:
        sonuc.risk_seviyesi = "🟢 Düşük"
        sonuc.deprem_bolgesi = "4. Derece"
    elif sonuc.ss < 0.50:
        sonuc.risk_seviyesi = "🟡 Orta"
        sonuc.deprem_bolgesi = "3. Derece"
    elif sonuc.ss < 0.75:
        sonuc.risk_seviyesi = "🟠 Yüksek"
        sonuc.deprem_bolgesi = "2. Derece"
    else:
        sonuc.risk_seviyesi = "🔴 Çok Yüksek"
        sonuc.deprem_bolgesi = "1. Derece"

    # ── BYS (Bina Yükseklik Sınıfı) ──
    bina_yuk = kat_sayisi * 3.0  # Yaklaşık bina yüksekliği
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

    # ── Taşıyıcı sistem önerisi ──
    if kat_sayisi <= 4:
        sonuc.tasiyici_sistem_onerisi = "Betonarme Çerçeve VEYA Tünel Kalıp"
        sonuc.kolon_grid_onerisi = "4.0m × 5.0m aks aralığı"
        sonuc.perde_onerisi = "Min 2 adet perde duvar (her yönde)"
    elif kat_sayisi <= 8:
        sonuc.tasiyici_sistem_onerisi = "Betonarme Perde-Çerçeve Sistem"
        sonuc.kolon_grid_onerisi = "4.5m × 5.5m aks aralığı"
        sonuc.perde_onerisi = "Min 4 adet perde duvar + çerçeve"
    else:
        sonuc.tasiyici_sistem_onerisi = "Perde Ağırlıklı Betonarme Sistem"
        sonuc.kolon_grid_onerisi = "5.0m × 6.0m aks aralığı"
        sonuc.perde_onerisi = "Perde oranı min %1.5 (her yönde)"

    # ── Detay bilgiler ──
    sonuc.detaylar = [
        f"📊 TBDY 2018 parametreleri kullanılmıştır",
        f"🏗️ Bina yüksekliği tahmini: {bina_yuk:.0f}m ({kat_sayisi} kat × 3m)",
        f"🪨 Zemin sınıfı: {zemin_sinifi} ({zemin_info['aciklama']})",
        f"⚠️ Kesin değerler için AFAD TDTH haritasından sorgulanmalıdır: https://tdth.afad.gov.tr/",
        f"📐 Zemin etüdü raporu zorunludur",
    ]

    if sonuc.ss > 0.50:
        sonuc.detaylar.append("🔴 Yüksek deprem riski — perde duvar sayısı artırılmalı")
    if zemin_sinifi in ("ZD", "ZE"):
        sonuc.detaylar.append("⚠️ Yumuşak zemin — zemin iyileştirmesi gerekebilir")

    return sonuc


def _estimate_ss(lat: float, lon: float) -> float:
    """Basitleştirilmiş Ss tahmini (gerçek AFAD verileri için API gerekir)."""
    # Türkiye genelinde kabaca: Batı > Doğu, Kuzey Anadolu fay hattı yüksek
    # Bu çok kaba bir tahmindir — gerçek projede AFAD API kullanılmalı
    base = 0.40
    if 39.5 < lat < 41.5 and 27 < lon < 42:  # Kuzey Anadolu Fay
        base = 0.75
    elif lat < 37.5 and 28 < lon < 32:  # Batı Anadolu
        base = 0.60
    elif 37 < lat < 39 and 35 < lon < 37:  # Doğu Anadolu Fay
        base = 0.65
    elif lon > 42:  # Doğu
        base = 0.30
    return base
