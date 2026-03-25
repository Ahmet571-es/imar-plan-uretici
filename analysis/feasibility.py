"""
Kâr/Zarar Fizibilite Hesaplama + Duyarlılık Analizi.
"""

from dataclasses import dataclass, field


@dataclass
class FizibiliteSonucu:
    """Fizibilite hesaplama sonucu."""
    toplam_gelir: float = 0.0
    toplam_gider: float = 0.0
    kar_zarar: float = 0.0
    kar_marji: float = 0.0       # (kar / gelir) × 100
    roi: float = 0.0             # (kar / gider) × 100
    basabas_m2_fiyat: float = 0.0
    duyarlilik_matrisi: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "Toplam Gelir (₺)": f"{self.toplam_gelir:,.0f}",
            "Toplam Gider (₺)": f"{self.toplam_gider:,.0f}",
            "Kâr / Zarar (₺)": f"{self.kar_zarar:,.0f}",
            "Kâr Marjı (%)": f"{self.kar_marji:.1f}%",
            "Yatırım Getirisi — ROI (%)": f"{self.roi:.1f}%",
            "Başabaş m² Fiyatı (₺)": f"{self.basabas_m2_fiyat:,.0f}",
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


def create_sensitivity_heatmap(matris, maliyet_labels, fiyat_labels):
    """Duyarlılık matrisi ısı haritası oluşturur."""
    import numpy as np
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
