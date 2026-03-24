"""
Satış Geliri Tahmini — Daire bazlı gelir hesabı, kat/cephe primi.
"""

from dataclasses import dataclass, field
from config.cost_defaults import KAT_PRIMI, CEPHE_PRIMI


@dataclass
class DaireGelir:
    """Tek bir daire için gelir bilgisi."""
    daire_no: int = 0
    kat: int = 0
    tip: str = "3+1"
    net_alan: float = 0.0
    m2_fiyat: float = 0.0
    kat_primi: float = 0.0
    cephe_primi: float = 0.0
    satis_fiyati: float = 0.0


@dataclass
class GelirSonucu:
    """Gelir hesaplama sonucu."""
    daire_gelirleri: list[DaireGelir] = field(default_factory=list)
    toplam_daire_geliri: float = 0.0
    dukkan_geliri: float = 0.0
    otopark_geliri: float = 0.0
    toplam_gelir: float = 0.0
    ortalama_m2_fiyat: float = 0.0

    def to_dict(self) -> dict:
        return {
            "Toplam Daire Geliri (₺)": f"{self.toplam_daire_geliri:,.0f}",
            "Dükkan Geliri (₺)": f"{self.dukkan_geliri:,.0f}",
            "Otopark Geliri (₺)": f"{self.otopark_geliri:,.0f}",
            "TOPLAM GELİR (₺)": f"{self.toplam_gelir:,.0f}",
            "Ortalama m² Fiyatı (₺)": f"{self.ortalama_m2_fiyat:,.0f}",
        }


def hesapla_gelir(
    daireler: list[dict],
    m2_satis_fiyati: float = 40000,
    kat_sayisi: int = 4,
    dukkan_alani: float = 0,
    dukkan_m2_fiyat: float = 0,
    otopark_satis_adedi: int = 0,
    otopark_birim_fiyat: float = 500000,
    cephe_yon: str = "güney",
) -> GelirSonucu:
    """Satış geliri tahmini hesaplar.

    Args:
        daireler: [{"daire_no": int, "kat": int, "tip": str, "net_alan": float}, ...]
        m2_satis_fiyati: İlçe ortalama m² satış fiyatı (₺).
        kat_sayisi: Toplam kat sayısı.
        dukkan_alani: Zemin kat dükkan alanı (m²), 0=yok.
        dukkan_m2_fiyat: Dükkan m² satış fiyatı.
        otopark_satis_adedi: Satılacak otopark sayısı.
        otopark_birim_fiyat: Otopark birim fiyatı (₺).
        cephe_yon: Binanın ana cephe yönü.
    """
    sonuc = GelirSonucu()
    sonuc.ortalama_m2_fiyat = m2_satis_fiyati

    for d in daireler:
        dg = DaireGelir(
            daire_no=d.get("daire_no", 0),
            kat=d.get("kat", 1),
            tip=d.get("tip", "3+1"),
            net_alan=d.get("net_alan", 100),
            m2_fiyat=m2_satis_fiyati,
        )

        # Kat primi
        if dg.kat == 1:
            dg.kat_primi = KAT_PRIMI["zemin"]
        elif dg.kat == kat_sayisi:
            dg.kat_primi = KAT_PRIMI["cati_kati"]
        elif dg.kat >= kat_sayisi - 1:
            dg.kat_primi = KAT_PRIMI["ust_kat"]
        else:
            dg.kat_primi = KAT_PRIMI["normal"]

        # Cephe primi
        dg.cephe_primi = CEPHE_PRIMI.get(cephe_yon, 0.0)

        # Satış fiyatı
        primli_m2 = m2_satis_fiyati * (1 + dg.kat_primi + dg.cephe_primi)
        dg.satis_fiyati = dg.net_alan * primli_m2

        sonuc.daire_gelirleri.append(dg)

    sonuc.toplam_daire_geliri = sum(dg.satis_fiyati for dg in sonuc.daire_gelirleri)
    sonuc.dukkan_geliri = dukkan_alani * dukkan_m2_fiyat if dukkan_alani > 0 else 0
    sonuc.otopark_geliri = otopark_satis_adedi * otopark_birim_fiyat
    sonuc.toplam_gelir = sonuc.toplam_daire_geliri + sonuc.dukkan_geliri + sonuc.otopark_geliri

    return sonuc
