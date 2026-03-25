"""
FAZ 4 — Finansal Fizibilite Testleri.

Maliyet tahmini, gelir hesaplama, fizibilite analizi ve duyarlılık matrisi testleri.
"""

import pytest

from analysis.cost_estimator import hesapla_maliyet, MaliyetSonucu
from analysis.revenue_estimator import hesapla_gelir, GelirSonucu
from analysis.feasibility import hesapla_fizibilite, duyarlilik_analizi, FizibiliteSonucu


# ══════════════════════════════════════════════════
#  Maliyet Testleri
# ══════════════════════════════════════════════════

class TestMaliyetHesaplama:
    """Maliyet hesaplama testleri."""

    def test_maliyet_hesaplama_basarili(self):
        """Temel maliyet hesaplaması doğru çalışmalı."""
        sonuc = hesapla_maliyet(
            toplam_insaat_alani=1000,
            il="Ankara",
            kalite="orta",
            arsa_maliyeti=5_000_000,
        )
        assert isinstance(sonuc, MaliyetSonucu)
        assert sonuc.toplam_insaat_alani == 1000
        assert sonuc.birim_maliyet > 0
        assert sonuc.kaba_insaat_maliyeti > 0
        assert sonuc.toplam_maliyet > 0
        # Toplam maliyet = inşaat gideri + arsa
        assert sonuc.toplam_maliyet == sonuc.toplam_insaat_gideri + sonuc.arsa_maliyeti
        # Ek gider kalemleri hesaplanmış olmalı
        assert sonuc.proje_muhendislik > 0
        assert sonuc.ruhsat_harclar > 0
        assert sonuc.pazarlama > 0
        assert sonuc.beklenmedik > 0

    def test_maliyet_il_bazli_fark(self):
        """Farklı illerin maliyetleri farklı olmalı (İstanbul > Kütahya)."""
        istanbul = hesapla_maliyet(1000, il="İstanbul", kalite="orta")
        kutahya = hesapla_maliyet(1000, il="Kütahya", kalite="orta")

        assert istanbul.birim_maliyet > kutahya.birim_maliyet
        assert istanbul.toplam_maliyet > kutahya.toplam_maliyet

    def test_maliyet_kalite_fark(self):
        """Ekonomik < orta < lüks sıralaması korunmalı."""
        ekonomik = hesapla_maliyet(1000, il="Ankara", kalite="ekonomik")
        orta = hesapla_maliyet(1000, il="Ankara", kalite="orta")
        luks = hesapla_maliyet(1000, il="Ankara", kalite="luks")

        assert ekonomik.birim_maliyet < orta.birim_maliyet < luks.birim_maliyet
        assert ekonomik.toplam_maliyet < orta.toplam_maliyet < luks.toplam_maliyet

    def test_maliyet_sifir_alan(self):
        """Sıfır alan verildiğinde hata vermemeli, tutarlı sonuç dönmeli."""
        sonuc = hesapla_maliyet(toplam_insaat_alani=0, il="Ankara", kalite="orta")
        assert sonuc.toplam_insaat_alani == 0
        assert sonuc.kaba_insaat_maliyeti == 0
        assert sonuc.toplam_maliyet == 0

    def test_maliyet_to_dict(self):
        """to_dict() metodu çalışmalı ve beklenen anahtarları içermeli."""
        sonuc = hesapla_maliyet(500, il="Ankara", kalite="orta", arsa_maliyeti=1_000_000)
        d = sonuc.to_dict()
        assert isinstance(d, dict)
        assert "Kaba İnşaat Maliyeti (₺)" in d
        assert "Otopark Maliyeti (₺)" in d
        assert "Pazarlama (₺)" in d
        assert "Beklenmedik Giderler (₺)" in d
        assert "TOPLAM MALİYET (₺)" in d


# ══════════════════════════════════════════════════
#  Gelir Testleri
# ══════════════════════════════════════════════════

class TestGelirHesaplama:
    """Gelir hesaplama testleri."""

    def _ornek_daireler(self, kat_sayisi=4, daire_per_kat=2, net_alan=100):
        """Test için örnek daire listesi üretir."""
        daireler = []
        no = 1
        for kat in range(1, kat_sayisi + 1):
            for _ in range(daire_per_kat):
                daireler.append({
                    "daire_no": no,
                    "kat": kat,
                    "tip": "3+1",
                    "net_alan": net_alan,
                })
                no += 1
        return daireler

    def test_gelir_hesaplama_basarili(self):
        """Temel gelir hesaplaması doğru çalışmalı."""
        daireler = self._ornek_daireler()
        sonuc = hesapla_gelir(daireler, m2_satis_fiyati=40_000)

        assert isinstance(sonuc, GelirSonucu)
        assert sonuc.toplam_gelir > 0
        assert sonuc.toplam_daire_geliri > 0
        assert len(sonuc.daire_gelirleri) == 8  # 4 kat × 2 daire

    def test_gelir_kat_primi(self):
        """Üst katlardaki daireler daha pahalı olmalı."""
        daireler = [
            {"daire_no": 1, "kat": 1, "tip": "3+1", "net_alan": 100},  # zemin
            {"daire_no": 2, "kat": 4, "tip": "3+1", "net_alan": 100},  # çatı katı
        ]
        sonuc = hesapla_gelir(daireler, m2_satis_fiyati=40_000, kat_sayisi=4)
        zemin_fiyat = sonuc.daire_gelirleri[0].satis_fiyati
        cati_fiyat = sonuc.daire_gelirleri[1].satis_fiyati

        assert cati_fiyat > zemin_fiyat, "Çatı katı dairesi zemin kattan daha pahalı olmalı"

    def test_gelir_cephe_primi(self):
        """Güney cepheli daire kuzey cepheliden daha değerli olmalı."""
        daireler = [{"daire_no": 1, "kat": 2, "tip": "3+1", "net_alan": 100}]

        guney = hesapla_gelir(daireler, m2_satis_fiyati=40_000, cephe_yon="güney")
        kuzey = hesapla_gelir(daireler, m2_satis_fiyati=40_000, cephe_yon="kuzey")

        assert guney.toplam_gelir > kuzey.toplam_gelir


# ══════════════════════════════════════════════════
#  Fizibilite Testleri
# ══════════════════════════════════════════════════

class TestFizibilite:
    """Fizibilite analizi testleri."""

    def test_fizibilite_karli(self):
        """Gelir > gider ise kârlı çıkmalı."""
        sonuc = hesapla_fizibilite(toplam_gelir=10_000_000, toplam_gider=7_000_000)
        assert sonuc.karli_mi is True
        assert sonuc.kar_zarar > 0
        assert sonuc.kar_marji > 0
        assert sonuc.roi > 0

    def test_fizibilite_zararli(self):
        """Gelir < gider ise zararlı çıkmalı."""
        sonuc = hesapla_fizibilite(toplam_gelir=5_000_000, toplam_gider=8_000_000)
        assert sonuc.karli_mi is False
        assert sonuc.kar_zarar < 0
        assert sonuc.kar_marji < 0

    def test_fizibilite_basabas(self):
        """Gelir = gider ise başabaş olmalı (kâr = 0)."""
        sonuc = hesapla_fizibilite(toplam_gelir=10_000_000, toplam_gider=10_000_000)
        assert sonuc.kar_zarar == 0
        assert sonuc.kar_marji == 0
        assert sonuc.roi == 0
        assert sonuc.karli_mi is False  # 0 kâr, kârlı sayılmaz

    def test_roi_hesaplama(self):
        """ROI = (kâr / gider) × 100 formülü doğru olmalı."""
        gelir = 12_000_000
        gider = 10_000_000
        beklenen_roi = ((gelir - gider) / gider) * 100

        sonuc = hesapla_fizibilite(toplam_gelir=gelir, toplam_gider=gider)
        assert abs(sonuc.roi - beklenen_roi) < 0.01

    def test_karlilik_endeksi(self):
        """Kârlılık endeksi = gelir / gider oranı doğru hesaplanmalı."""
        gelir = 15_000_000
        gider = 10_000_000
        beklenen_pi = gelir / gider  # 1.5

        sonuc = hesapla_fizibilite(toplam_gelir=gelir, toplam_gider=gider)
        assert abs(sonuc.karlilik_endeksi - beklenen_pi) < 0.001

    def test_yatirim_geri_donus_suresi(self):
        """Yatırım geri dönüş süresi doğru hesaplanmalı (24 ay satış dönemi)."""
        gelir = 12_000_000
        gider = 10_000_000
        # Aylık gelir = 12M / 24 = 500K; geri dönüş = 10M / 500K = 20 ay
        beklenen_ay = gider / (gelir / 24)

        sonuc = hesapla_fizibilite(toplam_gelir=gelir, toplam_gider=gider)
        assert abs(sonuc.yatirim_geri_donus_suresi - beklenen_ay) < 0.01

    def test_fizibilite_to_dict(self):
        """to_dict() metodu çalışmalı ve tüm alanları içermeli."""
        sonuc = hesapla_fizibilite(toplam_gelir=10_000_000, toplam_gider=7_000_000)
        d = sonuc.to_dict()
        assert isinstance(d, dict)
        assert "Kârlılık Endeksi" in d
        assert "Yatırım Geri Dönüş Süresi (ay)" in d
        assert "Yatırım Getirisi — ROI (%)" in d

    def test_fizibilite_cok_buyuk_proje(self):
        """Çok büyük projelerde taşma veya hata olmamalı."""
        sonuc = hesapla_fizibilite(
            toplam_gelir=500_000_000_000,   # 500 milyar
            toplam_gider=350_000_000_000,
            toplam_satilanabilir_alan=1_000_000,
        )
        assert sonuc.karli_mi is True
        assert sonuc.basabas_m2_fiyat > 0
        assert sonuc.karlilik_endeksi > 1.0


# ══════════════════════════════════════════════════
#  Duyarlılık Analizi Testleri
# ══════════════════════════════════════════════════

class TestDuyarlilikAnalizi:
    """Duyarlılık matrisi testleri."""

    def test_duyarlilik_matrisi(self):
        """Duyarlılık matrisi oluşturulabilmeli."""
        matris = duyarlilik_analizi(baz_maliyet=10_000_000, baz_gelir=15_000_000)
        assert isinstance(matris, list)
        assert len(matris) > 0
        # Her hücrede beklenen anahtarlar olmalı
        hucre = matris[0][0]
        assert "kar" in hucre
        assert "kar_marji" in hucre
        assert "renk" in hucre
        assert "maliyet_degisim" in hucre
        assert "fiyat_degisim" in hucre

    def test_duyarlilik_boyutlari(self):
        """Varsayılan matris boyutları 4×5 olmalı (4 maliyet × 5 fiyat değişimi)."""
        matris = duyarlilik_analizi(baz_maliyet=10_000_000, baz_gelir=15_000_000)
        assert len(matris) == 4           # maliyet_degisim: [-0.10, 0.0, 0.10, 0.20]
        assert len(matris[0]) == 5        # fiyat_degisim: [-0.20, -0.10, 0.0, 0.10, 0.20]

    def test_duyarlilik_ozel_boyutlar(self):
        """Özel değişim oranlarıyla matris boyutları doğru olmalı."""
        matris = duyarlilik_analizi(
            baz_maliyet=10_000_000,
            baz_gelir=15_000_000,
            maliyet_degisim=[-0.05, 0.0, 0.05],
            fiyat_degisim=[-0.10, 0.0, 0.10],
        )
        assert len(matris) == 3
        assert len(matris[0]) == 3
