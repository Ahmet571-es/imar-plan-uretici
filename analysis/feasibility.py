"""
Kâr/Zarar Fizibilite Hesaplama + Duyarlılık Analizi.
"""

from dataclasses import dataclass, field
import numpy as np


@dataclass
class FizibiliteSonucu:
    """Fizibilite hesaplama sonucu."""
    toplam_gelir: float = 0.0
    toplam_gider: float = 0.0
    kar_zarar: float = 0.0
    kar_marji: float = 0.0       # (kar / gelir) × 100
    roi: float = 0.0             # (kar / gider) × 100
    basabas_m2_fiyat: float = 0.0
    karlilik_endeksi: float = 0.0   # gelir / gider oranı (PI — Profitability Index)
    yatirim_geri_donus_suresi: float = 0.0  # başabaş noktasına ulaşma süresi (ay)
    duyarlilik_matrisi: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "Toplam Gelir (₺)": f"{self.toplam_gelir:,.0f}",
            "Toplam Gider (₺)": f"{self.toplam_gider:,.0f}",
            "Kâr / Zarar (₺)": f"{self.kar_zarar:,.0f}",
            "Kâr Marjı (%)": f"{self.kar_marji:.1f}%",
            "Yatırım Getirisi — ROI (%)": f"{self.roi:.1f}%",
            "Başabaş m² Fiyatı (₺)": f"{self.basabas_m2_fiyat:,.0f}",
            "Kârlılık Endeksi": f"{self.karlilik_endeksi:.2f}",
            "Yatırım Geri Dönüş Süresi (ay)": f"{self.yatirim_geri_donus_suresi:.1f}",
        }

    @property
    def karli_mi(self) -> bool:
        return self.kar_zarar > 0


def hesapla_fizibilite(
    toplam_gelir: float,
    toplam_gider: float,
    toplam_satilanabilir_alan: float = 0,
) -> FizibiliteSonucu:
    """Kâr/zarar fizibilite hesabı."""
    sonuc = FizibiliteSonucu(
        toplam_gelir=toplam_gelir,
        toplam_gider=toplam_gider,
    )

    sonuc.kar_zarar = toplam_gelir - toplam_gider

    if toplam_gelir > 0:
        sonuc.kar_marji = (sonuc.kar_zarar / toplam_gelir) * 100
    if toplam_gider > 0:
        sonuc.roi = (sonuc.kar_zarar / toplam_gider) * 100

    if toplam_satilanabilir_alan > 0:
        sonuc.basabas_m2_fiyat = toplam_gider / toplam_satilanabilir_alan

    # Kârlılık endeksi (PI): gelir / gider oranı
    if toplam_gider > 0:
        sonuc.karlilik_endeksi = toplam_gelir / toplam_gider

    # Yatırım geri dönüş süresi (ay): 24 aylık satış dönemi varsayımıyla
    # Aylık gelir = toplam gelir / 24; geri dönüş = gider / aylık gelir
    SATIS_DONEMI_AY = 24
    if toplam_gelir > 0:
        aylik_gelir = toplam_gelir / SATIS_DONEMI_AY
        sonuc.yatirim_geri_donus_suresi = toplam_gider / aylik_gelir
    else:
        # Gelir yoksa geri dönüş sonsuz — pratikte 0 olarak bırak
        sonuc.yatirim_geri_donus_suresi = 0.0

    return sonuc


def duyarlilik_analizi(
    baz_maliyet: float,
    baz_gelir: float,
    maliyet_degisim: list[float] = None,
    fiyat_degisim: list[float] = None,
) -> list[list[dict]]:
    """3×3 duyarlılık analizi matrisi oluşturur.

    Args:
        baz_maliyet: Baz maliyet (₺).
        baz_gelir: Baz gelir (₺).
        maliyet_degisim: Maliyet değişim oranları [ör: -0.10, 0, 0.10, 0.20].
        fiyat_degisim: Fiyat değişim oranları.

    Returns:
        Matris: her hücre {"maliyet_degisim", "fiyat_degisim", "kar", "kar_marji", "renk"}.
    """
    if maliyet_degisim is None:
        maliyet_degisim = [-0.10, 0.0, 0.10, 0.20]
    if fiyat_degisim is None:
        fiyat_degisim = [-0.20, -0.10, 0.0, 0.10, 0.20]

    matris = []
    for md in maliyet_degisim:
        row = []
        for fd in fiyat_degisim:
            yeni_maliyet = baz_maliyet * (1 + md)
            yeni_gelir = baz_gelir * (1 + fd)
            kar = yeni_gelir - yeni_maliyet
            kar_marji = (kar / yeni_gelir * 100) if yeni_gelir > 0 else 0

            if kar_marji > 20:
                renk = "🟢"
            elif kar_marji > 10:
                renk = "🟡"
            elif kar_marji > 0:
                renk = "🟠"
            else:
                renk = "🔴"

            row.append({
                "maliyet_degisim": f"{md:+.0%}",
                "fiyat_degisim": f"{fd:+.0%}",
                "kar": kar,
                "kar_marji": kar_marji,
                "renk": renk,
                "label": f"{renk} {kar_marji:.0f}%",
            })
        matris.append(row)

    return matris


def monte_carlo_simulasyonu(
    baz_maliyet: float,
    baz_gelir: float,
    maliyet_std: float = 0.10,
    gelir_std: float = 0.15,
    simulasyon_sayisi: int = 5000,
) -> dict:
    """Monte Carlo risk simülasyonu — maliyet ve gelir belirsizliği analizi.

    Normal dağılım ile rastgele maliyet/gelir senaryoları üretir.

    Args:
        baz_maliyet: Baz toplam maliyet (₺).
        baz_gelir: Baz toplam gelir (₺).
        maliyet_std: Maliyet standart sapması (oran, ör: 0.10 = %10).
        gelir_std: Gelir standart sapması (oran, ör: 0.15 = %15).
        simulasyon_sayisi: Simülasyon iterasyon sayısı.

    Returns:
        dict: {
            "kar_ortalama", "kar_std", "kar_min", "kar_max",
            "zarar_olasiligi", "yuksek_kar_olasiligi",
            "kar_dagilimi", "percentiles"
        }
    """
    rng = np.random.default_rng(42)

    maliyetler = rng.normal(baz_maliyet, baz_maliyet * maliyet_std, simulasyon_sayisi)
    gelirler = rng.normal(baz_gelir, baz_gelir * gelir_std, simulasyon_sayisi)

    # Negatif değerleri sıfırla
    maliyetler = np.maximum(maliyetler, 0)
    gelirler = np.maximum(gelirler, 0)

    karlar = gelirler - maliyetler

    zarar_sayisi = np.sum(karlar < 0)
    yuksek_kar_sayisi = np.sum(karlar > baz_gelir * 0.20)  # %20+ kâr

    return {
        "kar_ortalama": float(np.mean(karlar)),
        "kar_std": float(np.std(karlar)),
        "kar_min": float(np.min(karlar)),
        "kar_max": float(np.max(karlar)),
        "kar_medyan": float(np.median(karlar)),
        "zarar_olasiligi": float(zarar_sayisi / simulasyon_sayisi * 100),
        "yuksek_kar_olasiligi": float(yuksek_kar_sayisi / simulasyon_sayisi * 100),
        "kar_dagilimi": karlar.tolist(),
        "percentiles": {
            "p5": float(np.percentile(karlar, 5)),
            "p25": float(np.percentile(karlar, 25)),
            "p50": float(np.percentile(karlar, 50)),
            "p75": float(np.percentile(karlar, 75)),
            "p95": float(np.percentile(karlar, 95)),
        },
        "simulasyon_sayisi": simulasyon_sayisi,
    }


def create_monte_carlo_chart(mc_result: dict):
    """Monte Carlo simülasyon sonuçlarının histogram grafiğini oluşturur."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    karlar = mc_result["kar_dagilimi"]
    fig, ax = plt.subplots(figsize=(10, 5))

    # Histogram
    n, bins, patches = ax.hist(karlar, bins=50, edgecolor="white", alpha=0.7)

    # Renklendirme: zarar kırmızı, kâr yeşil
    for patch, left_edge in zip(patches, bins[:-1]):
        if left_edge < 0:
            patch.set_facecolor("#EF5350")
        else:
            patch.set_facecolor("#66BB6A")

    # Percentil çizgileri
    p = mc_result["percentiles"]
    for label, val, color in [
        ("P5", p["p5"], "#E53935"),
        ("P50", p["p50"], "#1E88E5"),
        ("P95", p["p95"], "#43A047"),
    ]:
        ax.axvline(val, color=color, linestyle="--", linewidth=1.5)
        ax.text(val, ax.get_ylim()[1] * 0.9, f" {label}\n ₺{val:,.0f}",
                fontsize=8, color=color, fontweight="bold")

    ax.set_xlabel("Kâr / Zarar (₺)", fontsize=11)
    ax.set_ylabel("Frekans", fontsize=11)
    ax.set_title(
        f"Monte Carlo Risk Simülasyonu ({mc_result['simulasyon_sayisi']:,} senaryo)\n"
        f"Zarar Olasılığı: %{mc_result['zarar_olasiligi']:.1f} | "
        f"Ortalama Kâr: ₺{mc_result['kar_ortalama']:,.0f}",
        fontsize=12, fontweight="bold",
    )
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def create_sensitivity_heatmap(matris, maliyet_labels, fiyat_labels):
    """Duyarlılık matrisi ısı haritası oluşturur."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    n_rows = len(matris)
    n_cols = len(matris[0]) if matris else 0

    values = np.array([[cell["kar_marji"] for cell in row] for row in matris])

    fig, ax = plt.subplots(figsize=(10, 6))
    im = ax.imshow(values, cmap="RdYlGn", aspect="auto", vmin=-30, vmax=50)

    ax.set_xticks(range(n_cols))
    ax.set_xticklabels(fiyat_labels, fontsize=9)
    ax.set_yticks(range(n_rows))
    ax.set_yticklabels(maliyet_labels, fontsize=9)
    ax.set_xlabel("Satış Fiyatı Değişimi", fontsize=11)
    ax.set_ylabel("İnşaat Maliyeti Değişimi", fontsize=11)
    ax.set_title("Duyarlılık Analizi — Kâr Marjı (%)", fontsize=13, fontweight="bold")

    for i in range(n_rows):
        for j in range(n_cols):
            val = values[i, j]
            color = "white" if abs(val) > 15 else "black"
            ax.text(j, i, f"{val:.0f}%", ha="center", va="center", fontsize=9,
                    fontweight="bold", color=color)

    fig.colorbar(im, ax=ax, label="Kâr Marjı (%)")
    fig.tight_layout()
    return fig
