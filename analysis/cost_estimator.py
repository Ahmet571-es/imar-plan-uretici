"""
İnşaat Maliyet Tahmini — İl, kalite ve alan bazlı detaylı maliyet hesabı.
"""

from dataclasses import dataclass, field

try:
    import streamlit as st
    _cache_data = st.cache_data
except Exception:
    _cache_data = lambda **kwargs: lambda f: f  # no-op decorator for testing

from config.cost_defaults import (
    get_construction_cost, MALIYET_DAGILIMI, OTOPARK_MALIYETLERI, GIDER_ORANLARI,
)


@dataclass
class MaliyetSonucu:
    """Maliyet hesaplama sonucu."""
    toplam_insaat_alani: float = 0.0
    birim_maliyet: float = 0.0
    kaba_insaat_maliyeti: float = 0.0
    maliyet_kalemleri: dict = field(default_factory=dict)
    otopark_maliyeti: float = 0.0
    proje_muhendislik: float = 0.0
    ruhsat_harclar: float = 0.0
    pazarlama: float = 0.0
    beklenmedik: float = 0.0
    toplam_insaat_gideri: float = 0.0
    arsa_maliyeti: float = 0.0
    toplam_maliyet: float = 0.0

    def to_dict(self) -> dict:
        return {
            "Toplam İnşaat Alanı (m²)": f"{self.toplam_insaat_alani:,.0f}",
            "Birim Maliyet (₺/m²)": f"{self.birim_maliyet:,.0f}",
            "Kaba İnşaat Maliyeti (₺)": f"{self.kaba_insaat_maliyeti:,.0f}",
            "Otopark Maliyeti (₺)": f"{self.otopark_maliyeti:,.0f}",
            "Proje & Mühendislik (₺)": f"{self.proje_muhendislik:,.0f}",
            "Ruhsat & Harçlar (₺)": f"{self.ruhsat_harclar:,.0f}",
            "Pazarlama (₺)": f"{self.pazarlama:,.0f}",
            "Beklenmedik Giderler (₺)": f"{self.beklenmedik:,.0f}",
            "Toplam İnşaat Gideri (₺)": f"{self.toplam_insaat_gideri:,.0f}",
            "Arsa Maliyeti (₺)": f"{self.arsa_maliyeti:,.0f}",
            "TOPLAM MALİYET (₺)": f"{self.toplam_maliyet:,.0f}",
        }


@_cache_data(ttl=3600)
def hesapla_maliyet(
    toplam_insaat_alani: float,
    il: str = "Ankara",
    kalite: str = "orta",
    birim_maliyet_override: float = 0,
    arsa_maliyeti: float = 0,
    otopark_tipi: str = "acik",
    otopark_arac_sayisi: int = 0,
) -> MaliyetSonucu:
    """İnşaat maliyet tahmini hesaplar."""
    sonuc = MaliyetSonucu()
    sonuc.toplam_insaat_alani = toplam_insaat_alani
    sonuc.arsa_maliyeti = arsa_maliyeti

    # Birim maliyet
    if birim_maliyet_override > 0:
        sonuc.birim_maliyet = birim_maliyet_override
    else:
        sonuc.birim_maliyet = get_construction_cost(il, kalite)

    # Kaba inşaat maliyeti
    sonuc.kaba_insaat_maliyeti = toplam_insaat_alani * sonuc.birim_maliyet

    # Maliyet kalemleri dağılımı
    for kalem, oran in MALIYET_DAGILIMI.items():
        sonuc.maliyet_kalemleri[kalem] = sonuc.kaba_insaat_maliyeti * oran

    # Otopark
    if otopark_arac_sayisi > 0:
        otopark_info = OTOPARK_MALIYETLERI.get(otopark_tipi, OTOPARK_MALIYETLERI["acik"])
        otopark_alani = otopark_arac_sayisi * otopark_info["m2_arac"]
        sonuc.otopark_maliyeti = otopark_alani * sonuc.birim_maliyet * otopark_info["maliyet_carpan"]

    # Ek giderler
    toplam_baz = sonuc.kaba_insaat_maliyeti + sonuc.otopark_maliyeti
    sonuc.proje_muhendislik = toplam_baz * GIDER_ORANLARI["proje_muhendislik"]
    sonuc.ruhsat_harclar = toplam_baz * GIDER_ORANLARI["ruhsat_harclar"]
    sonuc.pazarlama = toplam_baz * GIDER_ORANLARI["pazarlama"]
    sonuc.beklenmedik = toplam_baz * GIDER_ORANLARI["beklenmedik"]

    # Toplamlar
    sonuc.toplam_insaat_gideri = (
        sonuc.kaba_insaat_maliyeti + sonuc.otopark_maliyeti +
        sonuc.proje_muhendislik + sonuc.ruhsat_harclar +
        sonuc.pazarlama + sonuc.beklenmedik
    )
    sonuc.toplam_maliyet = sonuc.toplam_insaat_gideri + sonuc.arsa_maliyeti

    return sonuc
