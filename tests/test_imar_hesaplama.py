"""
İmar Hesaplama Testleri — Parsel, TAKS/KAKS, çekme mesafeleri, ortak alan düşümleri.
Planlı Alanlar İmar Yönetmeliği kurallarına uygunluk testleri.
"""

import pytest
from shapely.geometry import Polygon

from core.zoning import (
    ImarParametreleri,
    EmsalHariciAlanlar,
    HesaplamaSonucu,
    hesapla,
    _arka_bahce_h_yari_kurali,
    _emsal_harici_hesapla,
)
from utils.geometry_helpers import dikdortgen_polygon, koordinatlardan_polygon, polygon_alan
from utils.validation import validate_parsel_imar
from utils.constants import (
    MERDIVEN_EVI_ALAN,
    ASANSOR_KUYU_ALAN,
    GIRIS_HOLU_ALAN,
    SIGINAK_ORAN,
    TEKNIK_HACIM_ALAN,
    KAT_YUKSEKLIGI,
    EMSAL_HARICI_MERDIVEN,
    EMSAL_HARICI_ASANSOR,
    EMSAL_HARICI_GIRIS_HOLU,
    EMSAL_HARICI_SIGINAK_ORAN,
    MIN_YAPILASMAYA_UYGUN_ALAN,
)


# ══════════════════════════════════════════════
# 1. Parsel Alan Hesaplama Testleri
# ══════════════════════════════════════════════

class TestParselAlan:
    """Parsel alan hesaplama testleri."""

    def test_dikdortgen_parsel_alan(self, dikdortgen_parsel_22x28):
        """22m x 28m dikdörtgen parsel alanı = 616 m²."""
        alan = polygon_alan(dikdortgen_parsel_22x28)
        assert alan == pytest.approx(616.0, abs=0.1)

    def test_cokgen_parsel(self, cokgen_parsel_5_kenar):
        """5 kenarlı çokgen parsel alan hesabı — Shoelace formülü ile doğrulama."""
        alan = polygon_alan(cokgen_parsel_5_kenar)
        # Shoelace formülü ile hesap:
        # coords: (0,0), (20,0), (25,15), (10,25), (0,15)
        # A = 0.5 * |0*0-20*0 + 20*15-25*0 + 25*25-10*15 + 10*15-0*25 + 0*0-0*15|
        # A = 0.5 * |0 + 300 + 475 + 150 + 0| = 0.5 * 925 = 462.5
        assert alan == pytest.approx(462.5, abs=1.0)
        assert alan > 0


# ══════════════════════════════════════════════
# 2. TAKS / KAKS Hesaplama Testleri
# ══════════════════════════════════════════════

class TestTaksKaks:
    """TAKS ve KAKS hesaplama testleri."""

    def test_taks_hesaplama(self, dikdortgen_parsel_22x28, varsayilan_imar):
        """TAKS limiti doğru uygulanıyor mu: 616 * 0.35 = 215.6 m²."""
        sonuc = hesapla(dikdortgen_parsel_22x28, varsayilan_imar)
        beklenen_taks_siniri = 616.0 * 0.35  # 215.6
        # max_taban_alani = min(cekme_sonrasi, taks_siniri)
        assert sonuc.max_taban_alani <= beklenen_taks_siniri + 0.1
        assert sonuc.max_taban_alani > 0

    def test_kaks_hesaplama(self, dikdortgen_parsel_22x28, varsayilan_imar):
        """KAKS toplam alan hesabı: 616 * 1.40 = 862.4 m²."""
        sonuc = hesapla(dikdortgen_parsel_22x28, varsayilan_imar)
        beklenen_kaks = 616.0 * 1.40  # 862.4
        # toplam_insaat_alani, kat başı sınırlama sonrası farklı olabilir
        assert sonuc.toplam_insaat_alani > 0
        assert sonuc.toplam_insaat_alani <= beklenen_kaks + 0.1

    def test_kat_basi_brut_taks_siniri(self, dikdortgen_parsel_22x28, varsayilan_imar):
        """Kat başı brüt alan, TAKS taban alanını aşmamalı."""
        sonuc = hesapla(dikdortgen_parsel_22x28, varsayilan_imar)
        assert sonuc.kat_basi_brut_alan <= sonuc.max_taban_alani + 0.01


# ══════════════════════════════════════════════
# 3. Çekme Mesafesi Testleri
# ══════════════════════════════════════════════

class TestCekmeMesafesi:
    """Çekme mesafesi testleri."""

    def test_cekme_mesafesi_dikdortgen(self, dikdortgen_parsel_22x28, varsayilan_imar):
        """Çekme mesafeleri uygulandıktan sonra alan azalmalı."""
        sonuc = hesapla(dikdortgen_parsel_22x28, varsayilan_imar)
        assert sonuc.cekme_sonrasi_alan < sonuc.parsel_alani
        assert sonuc.cekme_sonrasi_alan > 0

    def test_cekme_mesafesi_cok_buyuk(self):
        """Çekme mesafesi parselden büyük olduğunda graceful handling."""
        kucuk = dikdortgen_polygon(8, 8)  # 64 m²
        imar = ImarParametreleri(
            kat_adedi=2,
            insaat_nizami="A",
            taks=0.35,
            kaks=0.70,
            on_bahce=5.0,
            yan_bahce=3.0,
            arka_bahce=5.0,
        )
        # 8m genişlik, 3+3=6m yan bahçe → 2m kaldı, çok küçük
        sonuc = hesapla(kucuk, imar)
        # Çökmemeli, uyarı üretmeli
        assert sonuc.parsel_alani == pytest.approx(64.0, abs=0.1)
        # Çekme sonrası alan minimum altında olabilir → uyarı beklenir
        assert len(sonuc.uyarilar) > 0


# ══════════════════════════════════════════════
# 4. Ortak Alan Düşüm Testleri
# ══════════════════════════════════════════════

class TestOrtakAlanDusum:
    """Ortak alan (merdiven, asansör, sığınak) düşüm testleri."""

    def test_ortak_alan_dusumu(self, dikdortgen_parsel_22x28, varsayilan_imar):
        """Merdiven + asansör + teknik hacim düşümü doğru hesaplanıyor mu."""
        sonuc = hesapla(dikdortgen_parsel_22x28, varsayilan_imar)
        beklenen_ortak = MERDIVEN_EVI_ALAN + ASANSOR_KUYU_ALAN + TEKNIK_HACIM_ALAN
        # 4 kat = asansör zorunlu, sığınak yok (varsayılan)
        assert sonuc.toplam_ortak_alan == pytest.approx(beklenen_ortak, abs=0.1)

    def test_siginak_oran(self, dikdortgen_parsel_22x28, imar_siginakli):
        """Sığınak oranı doğru hesaplanıyor mu: brüt alan * %5."""
        sonuc = hesapla(dikdortgen_parsel_22x28, imar_siginakli)
        beklenen_siginak = sonuc.kat_basi_brut_alan * SIGINAK_ORAN
        assert sonuc.siginak_alani == pytest.approx(beklenen_siginak, abs=0.1)
        assert sonuc.siginak_alani > 0


# ══════════════════════════════════════════════
# 5. Asansör Zorunluluk Testleri
# ══════════════════════════════════════════════

class TestAsansor:
    """Asansör zorunluluğu testleri."""

    def test_asansor_zorunlu_4kat(self, dikdortgen_parsel_22x28, varsayilan_imar):
        """4 kat → asansör zorunlu."""
        sonuc = hesapla(dikdortgen_parsel_22x28, varsayilan_imar)
        assert varsayilan_imar.asansor_zorunlu is True
        assert sonuc.asansor_alani == pytest.approx(ASANSOR_KUYU_ALAN, abs=0.1)

    def test_asansor_yok_3kat(self, dikdortgen_parsel_22x28, imar_3_kat):
        """3 kat → asansör zorunlu değil."""
        sonuc = hesapla(dikdortgen_parsel_22x28, imar_3_kat)
        assert imar_3_kat.asansor_zorunlu is False
        assert sonuc.asansor_alani == 0.0


# ══════════════════════════════════════════════
# 6. Parsel Boyut Sınır Testleri
# ══════════════════════════════════════════════

class TestParselBoyut:
    """Küçük ve büyük parsel sınır testleri."""

    def test_kucuk_parsel_50m2(self, kucuk_parsel_5x10, varsayilan_imar):
        """50 m² küçük parsel hesaplamada çökmemeli."""
        sonuc = hesapla(kucuk_parsel_5x10, varsayilan_imar)
        assert sonuc.parsel_alani == pytest.approx(50.0, abs=0.1)
        # Küçük parsel → uyarı beklenir
        assert len(sonuc.uyarilar) > 0

    def test_buyuk_parsel_10000m2(self, buyuk_parsel_100x100, varsayilan_imar):
        """10000 m² büyük parsel performans ve doğruluk testi."""
        sonuc = hesapla(buyuk_parsel_100x100, varsayilan_imar)
        assert sonuc.parsel_alani == pytest.approx(10000.0, abs=0.1)
        assert sonuc.toplam_insaat_alani > 0
        assert sonuc.kat_basi_brut_alan > 0


# ══════════════════════════════════════════════
# 7. Sıfır / Sınır Parametre Testleri
# ══════════════════════════════════════════════

class TestSifirParametreler:
    """Sıfır ve sınır parametre testleri."""

    def test_sifir_parametreler(self, dikdortgen_parsel_22x28, imar_sifir_taks_kaks):
        """Sıfır TAKS/KAKS/kat_adedi ile graceful handling."""
        sonuc = hesapla(dikdortgen_parsel_22x28, imar_sifir_taks_kaks)
        assert sonuc.parsel_alani == pytest.approx(616.0, abs=0.1)
        assert sonuc.kat_basi_brut_alan == 0.0
        assert sonuc.toplam_insaat_alani == 0.0


# ══════════════════════════════════════════════
# 8. İnşaat Nizamı Testleri
# ══════════════════════════════════════════════

class TestInsaatNizami:
    """İnşaat nizamı ile ilgili testler."""

    def test_bitisik_nizam_yan_bahce(self, dikdortgen_parsel_22x28, bitisik_nizam_imar):
        """Bitişik nizam → yan bahçe 0, daha geniş yapılaşma alanı."""
        sonuc = hesapla(dikdortgen_parsel_22x28, bitisik_nizam_imar)
        assert bitisik_nizam_imar.yan_bahce == 0.0
        assert sonuc.cekme_sonrasi_alan > 0

    def test_ayrik_nizam_yan_bahce(self, dikdortgen_parsel_22x28, varsayilan_imar):
        """Ayrık nizam → yan bahçe >= 3m uygulanmalı."""
        assert varsayilan_imar.insaat_nizami == "A"
        assert varsayilan_imar.yan_bahce >= 3.0
        sonuc = hesapla(dikdortgen_parsel_22x28, varsayilan_imar)
        assert sonuc.cekme_sonrasi_alan < sonuc.parsel_alani


# ══════════════════════════════════════════════
# 9. Bina Yüksekliği Limiti Testleri
# ══════════════════════════════════════════════

class TestBinaYuksekligi:
    """Bina yüksekliği limiti testleri."""

    def test_bina_yuksekligi_limiti(self, dikdortgen_parsel_22x28, imar_yukseklik_limitli):
        """Yükseklik limiti aşıldığında uyarı üretilmeli."""
        sonuc = hesapla(dikdortgen_parsel_22x28, imar_yukseklik_limitli)
        # 6 kat * 3.0m = 18.0m > 15.5m limit
        assert sonuc.bina_toplam_yukseklik == pytest.approx(18.0, abs=0.1)
        yukseklik_uyarilari = [
            u for u in sonuc.uyarilar if "yuksekligi" in u.lower() and "limit" in u.lower()
        ]
        assert len(yukseklik_uyarilari) > 0
        # Uyarı mesajında maksimum kat bilgisi olmalı
        assert any("Maksimum" in u or "maksimum" in u for u in yukseklik_uyarilari)


# ══════════════════════════════════════════════
# 10. Giriş Holü Testleri
# ══════════════════════════════════════════════

class TestGirisHolu:
    """Giriş holü testleri."""

    def test_giris_holu_sadece_zemin(self, dikdortgen_parsel_22x28, varsayilan_imar):
        """Giriş holü sadece zemin kat için hesaplanmalı (10 m²)."""
        sonuc = hesapla(dikdortgen_parsel_22x28, varsayilan_imar)
        assert sonuc.giris_holu_alani == pytest.approx(GIRIS_HOLU_ALAN, abs=0.1)

        # Emsal harici giriş holü de sadece zemin kat
        assert sonuc.emsal_harici.giris_holu_alani == pytest.approx(
            EMSAL_HARICI_GIRIS_HOLU, abs=0.1
        )


# ══════════════════════════════════════════════
# 11. Arka Bahçe H/2 Kuralı Testleri
# ══════════════════════════════════════════════

class TestArkaBahce:
    """Arka bahçe H/2 kuralı testleri — Yönetmelik Madde 6."""

    def test_arka_bahce_h_yari_kurali(self, imar_arka_bahce_sifir):
        """Arka bahçe 0 → H/2 kuralı uygulanmalı."""
        efektif = _arka_bahce_h_yari_kurali(imar_arka_bahce_sifir)
        # H = 4 * 3.0 = 12.0 m → H/2 = 6.0 m
        assert efektif == pytest.approx(6.0, abs=0.1)

    def test_arka_bahce_h_yari_uyari(self, dikdortgen_parsel_22x28, imar_arka_bahce_sifir):
        """Arka bahçe 0 ile hesaplama → uyarı mesajı üretilmeli."""
        sonuc = hesapla(dikdortgen_parsel_22x28, imar_arka_bahce_sifir)
        arka_bahce_uyarilari = [
            u for u in sonuc.uyarilar if "Arka bahce" in u and "Madde 6" in u
        ]
        assert len(arka_bahce_uyarilari) > 0


# ══════════════════════════════════════════════
# 12. Uyarı Üretimi Testleri
# ══════════════════════════════════════════════

class TestUyarilar:
    """Uyarı üretim testleri."""

    def test_uyarilar_olusturma(self, kucuk_parsel_5x10, varsayilan_imar):
        """Küçük parsel + varsayılan imar → uyarılar üretilmeli."""
        sonuc = hesapla(kucuk_parsel_5x10, varsayilan_imar)
        assert isinstance(sonuc.uyarilar, list)
        assert len(sonuc.uyarilar) > 0
        # Her uyarı bir string olmalı
        for uyari in sonuc.uyarilar:
            assert isinstance(uyari, str)
            assert len(uyari) > 0


# ══════════════════════════════════════════════
# 13. Hesaplama Sonuç Formatı Testleri
# ══════════════════════════════════════════════

class TestHesaplamaSonuc:
    """Hesaplama sonuç formatı testleri."""

    def test_hesaplama_sonuc_dict(self, dikdortgen_parsel_22x28, varsayilan_imar):
        """ozet_dict() doğru formatta dict döndürmeli."""
        sonuc = hesapla(dikdortgen_parsel_22x28, varsayilan_imar)
        ozet = sonuc.ozet_dict()

        assert isinstance(ozet, dict)
        # Beklenen anahtarlar
        beklenen_anahtarlar = [
            "Parsel Alanı (m²)",
            "Çekme Sonrası Alan (m²)",
            "Maks. Taban Alanı — TAKS (m²)",
            "Toplam İnşaat Alanı — KAKS (m²)",
            "Kat Başı Brüt Alan (m²)",
            "Bina Toplam Yükseklik (m)",
            "Merdiven Evi (m²)",
            "Asansör Alanı (m²)",
            "Giriş Holü (m²) [Zemin Kat]",
            "Sığınak (m²)",
            "Teknik Hacimler (m²)",
            "Otopark Alanı (m²)",
            "Toplam Ortak Alan / Kat (m²)",
            "Kat Başı Net Alan — Dairelere (m²)",
            "Emsal Harici Toplam (m²)",
        ]
        for anahtar in beklenen_anahtarlar:
            assert anahtar in ozet, f"'{anahtar}' anahtarı ozet_dict'te bulunamadı"

        # Tüm değerler string olmalı (formatlanmış)
        for deger in ozet.values():
            assert isinstance(deger, str)


# ══════════════════════════════════════════════
# 14. Emsal Harici Alan Testleri
# ══════════════════════════════════════════════

class TestEmsalHarici:
    """Emsal harici alan hesaplama testleri."""

    def test_emsal_harici_merdiven(self, dikdortgen_parsel_22x28, varsayilan_imar):
        """Emsal harici merdiven alanı = kat_adedi * 18 m²."""
        sonuc = hesapla(dikdortgen_parsel_22x28, varsayilan_imar)
        beklenen = EMSAL_HARICI_MERDIVEN * varsayilan_imar.kat_adedi
        assert sonuc.emsal_harici.merdiven_alani == pytest.approx(beklenen, abs=0.1)

    def test_emsal_harici_asansor(self, dikdortgen_parsel_22x28, varsayilan_imar):
        """Emsal harici asansör alanı = kat_adedi * 7 m² (4+ kat)."""
        sonuc = hesapla(dikdortgen_parsel_22x28, varsayilan_imar)
        beklenen = EMSAL_HARICI_ASANSOR * varsayilan_imar.kat_adedi
        assert sonuc.emsal_harici.asansor_alani == pytest.approx(beklenen, abs=0.1)

    def test_emsal_harici_toplam(self, dikdortgen_parsel_22x28, varsayilan_imar):
        """Emsal harici toplam doğru hesaplanıyor mu."""
        sonuc = hesapla(dikdortgen_parsel_22x28, varsayilan_imar)
        emsal = sonuc.emsal_harici
        beklenen_toplam = (
            emsal.merdiven_alani
            + emsal.asansor_alani
            + emsal.giris_holu_alani
            + emsal.siginak_alani
            + emsal.teknik_hacim_alani
            + emsal.otopark_alani
        )
        assert emsal.toplam == pytest.approx(beklenen_toplam, abs=0.1)


# ══════════════════════════════════════════════
# 15. validate_parsel_imar Testleri
# ══════════════════════════════════════════════

class TestValidateParselImar:
    """Parsel/imar validasyon testleri."""

    def test_gecerli_parametreler(self):
        """Geçerli parametreler ile tüm kontroller başarılı olmalı."""
        sonuclar = validate_parsel_imar(
            parsel_alani=616.0,
            imar={
                "taks": 0.35,
                "kaks": 1.40,
                "kat_adedi": 4,
                "insaat_nizami": "A",
                "on_bahce": 5.0,
                "yan_bahce": 3.0,
            },
        )
        assert isinstance(sonuclar, list)
        assert all(isinstance(s, dict) for s in sonuclar)
        assert all("gecerli" in s and "mesaj" in s and "madde" in s for s in sonuclar)
        # Hepsi geçerli olmalı
        assert all(s["gecerli"] for s in sonuclar)

    def test_kucuk_taban_alani(self):
        """Çok küçük parsel + TAKS → taban alanı < 30 m² uyarısı."""
        sonuclar = validate_parsel_imar(
            parsel_alani=50.0,
            imar={
                "taks": 0.35,
                "kaks": 1.40,
                "kat_adedi": 4,
                "insaat_nizami": "A",
                "on_bahce": 5.0,
                "yan_bahce": 3.0,
            },
        )
        taban_kontrol = [s for s in sonuclar if "taban" in s["mesaj"].lower()]
        assert len(taban_kontrol) > 0
        assert any(not s["gecerli"] for s in taban_kontrol)

    def test_kaks_taks_asimi(self):
        """KAKS/kat_adedi > TAKS → uyarı üretilmeli."""
        sonuclar = validate_parsel_imar(
            parsel_alani=500.0,
            imar={
                "taks": 0.30,
                "kaks": 2.40,  # 2.40/4 = 0.60 > 0.30
                "kat_adedi": 4,
                "insaat_nizami": "A",
                "on_bahce": 5.0,
                "yan_bahce": 3.0,
            },
        )
        kaks_kontrol = [s for s in sonuclar if "KAKS" in s["mesaj"]]
        assert len(kaks_kontrol) > 0
        assert any(not s["gecerli"] for s in kaks_kontrol)

    def test_ayrik_nizam_on_bahce_yetersiz(self):
        """Ayrık nizamda ön bahçe < 5m → uyarı."""
        sonuclar = validate_parsel_imar(
            parsel_alani=500.0,
            imar={
                "taks": 0.35,
                "kaks": 1.40,
                "kat_adedi": 4,
                "insaat_nizami": "A",
                "on_bahce": 3.0,  # < 5m
                "yan_bahce": 3.0,
            },
        )
        on_bahce_kontrol = [s for s in sonuclar if "on bahce" in s["mesaj"].lower()]
        assert len(on_bahce_kontrol) > 0
        assert any(not s["gecerli"] for s in on_bahce_kontrol)

    def test_ayrik_nizam_yan_bahce_yetersiz(self):
        """Ayrık nizamda yan bahçe < 3m → uyarı."""
        sonuclar = validate_parsel_imar(
            parsel_alani=500.0,
            imar={
                "taks": 0.35,
                "kaks": 1.40,
                "kat_adedi": 4,
                "insaat_nizami": "A",
                "on_bahce": 5.0,
                "yan_bahce": 2.0,  # < 3m
            },
        )
        yan_bahce_kontrol = [s for s in sonuclar if "yan bahce" in s["mesaj"].lower()]
        assert len(yan_bahce_kontrol) > 0
        assert any(not s["gecerli"] for s in yan_bahce_kontrol)
