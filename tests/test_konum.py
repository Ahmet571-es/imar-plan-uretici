"""
FAZ 6 — Konum & Cevre Analizi Testleri.

Deprem risk analizi, enerji performans, gunes analizi, insaat takvimi,
parsel karsilastirma ve harita olusturma testleri.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import datetime

from analysis.earthquake_risk import (
    deprem_risk_analizi,
    DepremAnalizi,
    ZEMIN_SINIFLARI,
    KolonGrid,
)
from analysis.energy_performance import (
    enerji_performans_hesapla,
    EnerjiSonucu,
    ENERJI_SINIFLARI,
)
from analysis.sun_analysis import (
    analyze_sun,
    SunAnalysisResult,
)
from analysis.construction_timeline import (
    hesapla_sure,
    TimelineSonucu,
    get_is_kalemleri,
)


# ══════════════════════════════════════════════════
#  Deprem Risk Analizi Testleri
# ══════════════════════════════════════════════════

class TestDepremAnalizi:
    """Deprem risk analizi testleri."""

    def test_deprem_analizi_basarili(self):
        """Temel deprem analizi basarili olmali ve tum alanlari doldurmali."""
        sonuc = deprem_risk_analizi(39.93, 32.86, 4, "ZC")
        assert isinstance(sonuc, DepremAnalizi)
        assert sonuc.risk_seviyesi != ""
        assert sonuc.ss > 0
        assert sonuc.s1 > 0
        assert sonuc.tasiyici_sistem_onerisi != ""
        assert sonuc.kolon_grid_onerisi != ""
        assert sonuc.deprem_bolgesi != ""
        assert len(sonuc.detaylar) > 0

    def test_deprem_risk_seviyeleri(self):
        """Farkli Ss degerleri farkli risk seviyeleri uretmeli."""
        gecerli_seviyeler = ["Dusuk", "Orta", "Yuksek", "Cok Yuksek"]

        # Dusuk risk — ZA ile dusuk Ss override
        dusuk = deprem_risk_analizi(39.93, 32.86, 4, "ZA", ss_override=0.20)
        assert dusuk.risk_seviyesi == "Dusuk"

        # Orta risk
        orta = deprem_risk_analizi(39.93, 32.86, 4, "ZA", ss_override=0.40)
        assert orta.risk_seviyesi == "Orta"

        # Yuksek risk
        yuksek = deprem_risk_analizi(39.93, 32.86, 4, "ZA", ss_override=0.70)
        assert yuksek.risk_seviyesi == "Yuksek"

        # Cok yuksek risk
        cok_yuksek = deprem_risk_analizi(39.93, 32.86, 4, "ZA", ss_override=1.00)
        assert cok_yuksek.risk_seviyesi == "Cok Yuksek"

        # Tum seviyeler gecerli kumede olmali
        for sonuc in [dusuk, orta, yuksek, cok_yuksek]:
            assert sonuc.risk_seviyesi in gecerli_seviyeler

    def test_deprem_zemin_siniflari(self):
        """Tum zemin siniflari tanimli olmali ve amplifikasyon dogru calismali."""
        assert len(ZEMIN_SINIFLARI) == 5
        for sinif in ["ZA", "ZB", "ZC", "ZD", "ZE"]:
            assert sinif in ZEMIN_SINIFLARI
            info = ZEMIN_SINIFLARI[sinif]
            assert "aciklama" in info
            assert "Fs" in info
            assert "risk" in info
            assert info["Fs"] > 0

        # Zemin amplifikasyonu: ZE daha yuksek Ss uretmeli (ayni Ss override ile)
        zc = deprem_risk_analizi(ss_override=0.50, zemin_sinifi="ZC")
        ze = deprem_risk_analizi(ss_override=0.50, zemin_sinifi="ZE")
        assert ze.ss > zc.ss

    def test_deprem_tasiyici_onerisi(self):
        """Farkli kat sayilari farkli tasiyici sistem onerileri vermeli."""
        sonuc_4 = deprem_risk_analizi(39.93, 32.86, 4, "ZC")
        assert sonuc_4.tasiyici_sistem_onerisi != ""
        assert "Betonarme" in sonuc_4.tasiyici_sistem_onerisi

        sonuc_10 = deprem_risk_analizi(39.93, 32.86, 10, "ZC")
        assert sonuc_10.tasiyici_sistem_onerisi != ""
        assert "Perde" in sonuc_10.tasiyici_sistem_onerisi

    def test_deprem_to_dict(self):
        """to_dict metodu eksiksiz bir dict dondurmeli."""
        sonuc = deprem_risk_analizi(39.93, 32.86, 4, "ZC")
        d = sonuc.to_dict()
        assert isinstance(d, dict)
        assert "Konum" in d
        assert "Ss (Kisa Periyot)" in d
        assert "S1 (1 sn Periyot)" in d
        assert "Zemin Sinifi" in d
        assert "Risk Seviyesi" in d
        assert "Tasiyici Sistem Onerisi" in d
        assert "AFAD API" in d

    def test_deprem_kolon_grid(self):
        """Kolon grid onerisi dogru boyutlarda olmali."""
        sonuc = deprem_risk_analizi(
            kat_sayisi=4, bina_genisligi=12.0, bina_derinligi=10.0,
        )
        assert sonuc.kolon_grid is not None
        grid = sonuc.kolon_grid
        assert isinstance(grid, KolonGrid)
        assert len(grid.x_akslar) >= 2
        assert len(grid.y_akslar) >= 2
        assert len(grid.aks_isimleri_x) == len(grid.x_akslar)
        assert grid.kolon_boyut[0] > 0
        assert grid.kolon_boyut[1] > 0


# ══════════════════════════════════════════════════
#  Enerji Performans Testleri
# ══════════════════════════════════════════════════

class TestEnerjiPerformans:
    """Enerji performans analizi testleri."""

    def test_enerji_performans_hesabi(self):
        """Temel enerji performans hesabi basarili olmali."""
        sonuc = enerji_performans_hesapla(850, 4, "duvar_8cm_eps", "isicam", True, 0.25, "dogalgaz_kombi")
        assert isinstance(sonuc, EnerjiSonucu)
        assert sonuc.enerji_sinifi in ENERJI_SINIFLARI
        assert sonuc.yillik_isitma_kwh_m2 >= 0
        assert sonuc.yillik_sogutma_kwh_m2 >= 0
        assert sonuc.yillik_toplam_kwh_m2 > 0
        assert sonuc.yillik_enerji_maliyeti > 0
        assert sonuc.duvar_u > 0
        assert sonuc.pencere_u > 0
        assert len(sonuc.oneriler) > 0

    def test_enerji_sinifi_a_b_c(self):
        """Iyi yalitim A-B sinifi, kotu yalitim daha dusuk sinif vermeli."""
        # En iyi yalitim — A veya B sinifi beklenir
        iyi = enerji_performans_hesapla(850, 4, "duvar_12cm_xps", "low_e", True, 0.20, "isi_pompasi")
        assert iyi.enerji_sinifi in ["A", "B"]

        # Kotu yalitim — A olamaz
        kotu = enerji_performans_hesapla(850, 4, "duvar_5cm_eps", "tek_cam", False, 0.45, "dogalgaz_kombi")
        assert kotu.enerji_sinifi not in ["A"]

        # Iyi yalitim daha dusuk enerji tuketimi olmali
        assert iyi.yillik_toplam_kwh_m2 < kotu.yillik_toplam_kwh_m2

        # Sinif sirasi kontrolu: A < B < C < ... < G
        sinif_sirasi = list(ENERJI_SINIFLARI.keys())
        assert sinif_sirasi.index(iyi.enerji_sinifi) <= sinif_sirasi.index(kotu.enerji_sinifi)

    def test_enerji_siniflari_dict(self):
        """ENERJI_SINIFLARI dict'i eksiksiz tanimli olmali."""
        assert isinstance(ENERJI_SINIFLARI, dict)
        assert len(ENERJI_SINIFLARI) == 7
        for sinif in ["A", "B", "C", "D", "E", "F", "G"]:
            assert sinif in ENERJI_SINIFLARI
            info = ENERJI_SINIFLARI[sinif]
            assert "max_kwh" in info
            assert "renk" in info
            assert "aciklama" in info
            assert info["max_kwh"] > 0

    def test_enerji_to_dict(self):
        """to_dict metodu eksiksiz sonuc dondurmeli."""
        sonuc = enerji_performans_hesapla(850, 4, "duvar_8cm_eps", "isicam", True, 0.25, "dogalgaz_kombi")
        d = sonuc.to_dict()
        assert isinstance(d, dict)
        assert "Enerji Sinifi" in d
        assert "Yillik Isitma (kWh/m2)" in d
        assert "Yillik Sogutma (kWh/m2)" in d
        assert "Yillik Toplam (kWh/m2)" in d
        assert "Gunes Kazanci (kWh/yil)" in d
        assert "Pencere/Duvar Orani" in d

    def test_enerji_pencere_yonu_etkisi(self):
        """Pencere yonu dagilimi enerji sonucunu etkilemeli."""
        # Guneye agirlikli pencereler
        guney = enerji_performans_hesapla(
            850, 4, pencere_yonleri={"south": 0.60, "north": 0.10, "east": 0.15, "west": 0.15},
        )
        # Kuzeye agirlikli pencereler
        kuzey = enerji_performans_hesapla(
            850, 4, pencere_yonleri={"south": 0.10, "north": 0.60, "east": 0.15, "west": 0.15},
        )
        # Guneye agirlikli pencereler daha fazla gunes kazanci saglar
        assert guney.gunes_kazanci_kwh > kuzey.gunes_kazanci_kwh


# ══════════════════════════════════════════════════
#  Gunes Analizi Testleri
# ══════════════════════════════════════════════════

class TestGunesAnalizi:
    """Gunes analizi testleri."""

    def test_gunes_analizi(self):
        """Temel gunes analizi basarili olmali ve tum alanlari doldurmali."""
        sonuc = analyze_sun(39.93, 32.86)
        assert isinstance(sonuc, SunAnalysisResult)
        assert sonuc.latitude == 39.93
        assert sonuc.longitude == 32.86
        assert sonuc.annual_solar_hours > 0
        assert sonuc.summer_solstice_angle > 0
        assert len(sonuc.facade_sun_hours) == 8
        assert len(sonuc.recommendations) > 0

    def test_gunes_en_iyi_cephe(self):
        """Kuzey yarimkurede en iyi cephe guney olmali."""
        sonuc = analyze_sun(39.93, 32.86)
        # Turkiye'de en iyi cephe guney veya guney-varyantlari olmali
        assert sonuc.best_facade in ["güney", "güneydoğu", "güneybatı", "south"]
        # Guney cephenin gunes saati kuzey cepheden fazla olmali
        guney_saati = sonuc.facade_sun_hours.get("güney", 0)
        kuzey_saati = sonuc.facade_sun_hours.get("kuzey", 0)
        assert guney_saati > kuzey_saati

    def test_gunes_farkli_enlemler(self):
        """Farkli enlemler farkli gunes acilari vermeli."""
        guney = analyze_sun(latitude=36.0, longitude=32.86)  # Antalya civari
        kuzey = analyze_sun(latitude=41.5, longitude=32.86)  # Karadeniz civari
        # Daha guneydeki enlem daha yuksek gunes acisi almali
        assert guney.summer_solstice_angle > kuzey.summer_solstice_angle
        assert guney.winter_solstice_angle > kuzey.winter_solstice_angle


# ══════════════════════════════════════════════════
#  Insaat Takvimi Testleri
# ══════════════════════════════════════════════════

class TestInsaatTakvimi:
    """Insaat takvimi testleri."""

    def test_insaat_takvimi(self):
        """Insaat takvimi dogru hesaplanmali ve tum alanlari doldurmali."""
        sonuc = hesapla_sure(4, False, datetime.now())
        assert isinstance(sonuc, TimelineSonucu)
        assert sonuc.toplam_sure_ay > 0
        assert sonuc.toplam_sure_hafta_min > 0
        assert sonuc.toplam_sure_hafta_max >= sonuc.toplam_sure_hafta_min
        assert sonuc.tahmini_bitis != ""
        assert len(sonuc.is_kalemleri) > 0
        # Her is kaleminde gerekli alanlar olmali
        for kalem in sonuc.is_kalemleri:
            assert "isim" in kalem
            assert "sure_hafta" in kalem
            assert "baslangic" in kalem
            assert "bitis" in kalem
            assert "kritik_yol" in kalem

    def test_insaat_kat_etkisi(self):
        """Daha fazla kat daha uzun insaat suresi olmali."""
        sure_4 = hesapla_sure(kat_sayisi=4)
        sure_8 = hesapla_sure(kat_sayisi=8)
        assert sure_8.toplam_sure_ay > sure_4.toplam_sure_ay


# ══════════════════════════════════════════════════
#  Parsel Karsilastirma Testleri
# ══════════════════════════════════════════════════

class TestParselKarsilastirma:
    """Parsel karsilastirma modulu testleri."""

    def test_parsel_karsilastirma_import(self):
        """Parsel karsilastirma modulu import edilebilmeli ve calisabilmeli."""
        from analysis.parcel_comparison import ParselOzet, karsilastirma_tablosu
        assert ParselOzet is not None
        # ParselOzet olusturulabilmeli
        ozet = ParselOzet(isim="Test Parsel", alan=500.0, taks=0.35, kaks=1.40)
        assert ozet.isim == "Test Parsel"
        assert ozet.alan == 500.0
        # Karsilastirma tablosu bos olmayan liste ile calismali
        tablo = karsilastirma_tablosu([ozet])
        assert isinstance(tablo, list)


# ══════════════════════════════════════════════════
#  Harita Olusturma Testleri
# ══════════════════════════════════════════════════

class TestHarita:
    """Harita olusturma testleri."""

    def test_harita_olusturma(self):
        """Harita fonksiyonu import edilebilmeli ve cagrilabilmeli."""
        from map.location_picker import create_parcel_map
        m = create_parcel_map(39.93, 32.86)
        # folium kuruluysa Map nesnesi doner
        assert m is not None
