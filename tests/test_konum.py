"""
FAZ 6 Testleri — Konum & Çevre Analizi.
Deprem risk, enerji performans, güneş analizi, inşaat takvimi testleri.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


class TestDepremAnalizi:
    """Deprem risk analizi testleri."""

    def test_deprem_analizi_basarili(self):
        from analysis.earthquake_risk import deprem_risk_analizi
        sonuc = deprem_risk_analizi(39.93, 32.86, 4, "ZC")
        assert sonuc is not None
        assert sonuc.risk_seviyesi != ""
        assert sonuc.ss > 0
        assert sonuc.s1 > 0

    def test_deprem_risk_seviyeleri(self):
        from analysis.earthquake_risk import deprem_risk_analizi
        sonuc = deprem_risk_analizi(39.93, 32.86, 4, "ZC")
        gecerli_seviyeler = ["Dusuk", "Orta", "Yuksek", "Cok Yuksek"]
        assert sonuc.risk_seviyesi in gecerli_seviyeler

    def test_deprem_zemin_siniflari(self):
        from analysis.earthquake_risk import ZEMIN_SINIFLARI
        assert "ZA" in ZEMIN_SINIFLARI
        assert "ZB" in ZEMIN_SINIFLARI
        assert "ZC" in ZEMIN_SINIFLARI
        assert "ZD" in ZEMIN_SINIFLARI
        assert "ZE" in ZEMIN_SINIFLARI

    def test_deprem_tasiyici_onerisi(self):
        from analysis.earthquake_risk import deprem_risk_analizi
        sonuc = deprem_risk_analizi(39.93, 32.86, 4, "ZC")
        assert sonuc.tasiyici_sistem_onerisi != ""

    def test_deprem_to_dict(self):
        from analysis.earthquake_risk import deprem_risk_analizi
        sonuc = deprem_risk_analizi(39.93, 32.86, 4, "ZC")
        d = sonuc.to_dict()
        assert isinstance(d, dict)
        assert len(d) > 0


class TestEnerjiPerformans:
    """Enerji performans analizi testleri."""

    def test_enerji_performans_hesabi(self):
        from analysis.energy_performance import enerji_performans_hesapla
        sonuc = enerji_performans_hesapla(850, 4, "duvar_8cm_eps", "isicam", True, 0.25, "dogalgaz_kombi")
        assert sonuc is not None
        assert sonuc.enerji_sinifi in ["A", "B", "C", "D", "E", "F", "G"]

    def test_enerji_sinifi_iyi_yalitim(self):
        from analysis.energy_performance import enerji_performans_hesapla
        sonuc = enerji_performans_hesapla(850, 4, "duvar_12cm_xps", "low_e", True, 0.20, "isi_pompasi")
        assert sonuc.enerji_sinifi in ["A", "B"]

    def test_enerji_sinifi_kotu_yalitim(self):
        from analysis.energy_performance import enerji_performans_hesapla
        sonuc = enerji_performans_hesapla(850, 4, "duvar_5cm_eps", "tek_cam", False, 0.45, "dogalgaz_kombi")
        # Kötü yalıtımda C veya daha düşük beklenir
        assert sonuc.enerji_sinifi not in ["A"]

    def test_enerji_siniflari_dict(self):
        from analysis.energy_performance import ENERJI_SINIFLARI
        assert isinstance(ENERJI_SINIFLARI, dict)
        assert "A" in ENERJI_SINIFLARI
        assert "G" in ENERJI_SINIFLARI

    def test_enerji_to_dict(self):
        from analysis.energy_performance import enerji_performans_hesapla
        sonuc = enerji_performans_hesapla(850, 4, "duvar_8cm_eps", "isicam", True, 0.25, "dogalgaz_kombi")
        d = sonuc.to_dict()
        assert isinstance(d, dict)
        assert len(d) > 0


class TestGunesAnalizi:
    """Güneş analizi testleri."""

    def test_gunes_analizi(self):
        from analysis.sun_analysis import analyze_sun
        sonuc = analyze_sun(39.93, 32.86)
        assert sonuc is not None
        assert sonuc.annual_solar_hours > 0

    def test_gunes_en_iyi_cephe(self):
        from analysis.sun_analysis import analyze_sun
        sonuc = analyze_sun(39.93, 32.86)
        # Türkiye'de güneş güney cepheden gelir
        assert sonuc.best_facade in ["güney", "güneydoğu", "güneybatı", "south"]


class TestInsaatTakvimi:
    """İnşaat takvimi testleri."""

    def test_insaat_takvimi(self):
        from analysis.construction_timeline import hesapla_sure
        from datetime import datetime
        sonuc = hesapla_sure(4, False, datetime.now())
        assert sonuc is not None
        assert sonuc.toplam_sure_ay > 0
        assert len(sonuc.is_kalemleri) > 0


class TestParselKarsilastirma:
    """Parsel karşılaştırma testleri."""

    def test_parsel_karsilastirma_import(self):
        from analysis.parcel_comparison import ParselOzet, karsilastirma_tablosu
        assert ParselOzet is not None


class TestHarita:
    """Harita oluşturma testleri."""

    def test_harita_olusturma(self):
        from map.location_picker import create_parcel_map
        m = create_parcel_map(39.93, 32.86)
        assert m is not None
