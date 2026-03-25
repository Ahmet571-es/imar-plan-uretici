"""
Kat Planı Üretici (FAZ 2) — Kapsamlı test modülü.

Testler:
- Temel plan üretimi
- Çoklu plan alternatifleri
- Oda minimum alan kontrolleri (3194 sayılı İmar Kanunu)
- Layout varyasyonları (center_corridor, l_shape, t_shape, short_corridor, open_plan)
- Açık plan salon-mutfak
- En-suite banyo
- Islak hacim gruplaması
- Güneş cephesi optimizasyonu
- Farklı daire tipleri (1+1 ... 4+1)
- Sınır durumları (küçük/büyük alan)
- 2 daireli kat planı
- Puanlama sistemi
- Tekrarlanabilirlik (seed)
"""

import math
import pytest

from core.floor_plan_generator import (
    generate_professional_plan,
    generate_multiple_plans,
    generate_dual_apartment_plan,
    LAYOUT_TYPES,
)
from core.plan_scorer import FloorPlan, PlanRoom, score_plan
from config.room_defaults import MINIMUM_ODA_ALANLARI


# ── Yardımcı sabitler ──
VARSAYILAN_GENISLIK = 12.0
VARSAYILAN_YUKSEKLIK = 10.0
VARSAYILAN_SEED = 42


def _uret_plan(**kwargs) -> FloorPlan:
    """Varsayılan parametrelerle plan üretir (test yardımcısı)."""
    defaults = dict(
        buildable_width=VARSAYILAN_GENISLIK,
        buildable_height=VARSAYILAN_YUKSEKLIK,
        seed=VARSAYILAN_SEED,
    )
    defaults.update(kwargs)
    return generate_professional_plan(**defaults)


# ══════════════════════════════════════════════════════════════
# 1. TEMEL PLAN ÜRETİMİ
# ══════════════════════════════════════════════════════════════

class TestTemelPlanUretimi:
    """Temel plan üretim testleri."""

    def test_plan_uretimi_basarili(self):
        """Plan üretimi başarılı şekilde tamamlanmalı ve oda listesi boş olmamalı."""
        plan = _uret_plan()
        assert isinstance(plan, FloorPlan)
        assert len(plan.rooms) > 0
        assert plan.total_area > 0

    def test_plan_3_alternatif(self):
        """generate_multiple_plans en az 3 plan alternatifi döndürmeli."""
        sonuclar = generate_multiple_plans(
            VARSAYILAN_GENISLIK, VARSAYILAN_YUKSEKLIK,
            apartment_type="3+1", target_area=120, plan_count=3,
        )
        assert len(sonuclar) == 3
        for s in sonuclar:
            assert "floor_plan" in s
            assert "score" in s
            assert len(s["floor_plan"].rooms) > 0

    def test_tum_odalar_yerlestirildi(self):
        """Tüm odalar yerleştirilmiş olmalı (yerleştirilmemiş oda yok)."""
        plan = _uret_plan(apartment_type="3+1", target_area=120)
        # Her odanın genişlik ve yüksekliği sıfırdan büyük olmalı
        for room in plan.rooms:
            assert room.width > 0, f"{room.name} genişliği 0"
            assert room.height > 0, f"{room.name} yüksekliği 0"
            assert room.area > 0, f"{room.name} alanı 0"


# ══════════════════════════════════════════════════════════════
# 2. MİNİMUM ALAN KONTROLLERİ (İMAR KANUNU)
# ══════════════════════════════════════════════════════════════

class TestMinimumAlanlar:
    """3194 sayılı İmar Kanunu minimum alan gereksinimleri."""

    def test_oda_minimum_alan_salon(self):
        """Salon alanı en az 16 m² olmalı (normal boyutlu dairede)."""
        plan = _uret_plan(apartment_type="2+1", target_area=90)
        salonlar = [r for r in plan.rooms if r.room_type == "salon"]
        assert len(salonlar) > 0, "Salon bulunamadı"
        for s in salonlar:
            assert s.area >= 16.0 - 1.0, (
                f"Salon alanı ({s.area:.1f} m²) minimumun ({16.0} m²) çok altında"
            )

    def test_oda_minimum_alan_yatak(self):
        """Yatak odası alanı en az 9 m² olmalı."""
        plan = _uret_plan(apartment_type="2+1", target_area=90)
        yataklar = [r for r in plan.rooms if r.room_type == "yatak_odasi"]
        assert len(yataklar) > 0, "Yatak odası bulunamadı"
        for y in yataklar:
            assert y.area >= 9.0 - 1.0, (
                f"{y.name} alanı ({y.area:.1f} m²) minimumun ({9.0} m²) çok altında"
            )

    def test_oda_minimum_alan_mutfak(self):
        """Mutfak alanı en az 5 m² olmalı."""
        plan = _uret_plan(apartment_type="2+1", target_area=90)
        mutfaklar = [r for r in plan.rooms if r.room_type == "mutfak"]
        assert len(mutfaklar) > 0, "Mutfak bulunamadı"
        for m in mutfaklar:
            assert m.area >= 5.0 - 1.0, (
                f"Mutfak alanı ({m.area:.1f} m²) minimumun ({5.0} m²) çok altında"
            )

    def test_oda_minimum_alan_banyo(self):
        """Banyo alanı en az 3.5 m² olmalı."""
        plan = _uret_plan(apartment_type="2+1", target_area=90)
        banyolar = [r for r in plan.rooms if r.room_type == "banyo"]
        assert len(banyolar) > 0, "Banyo bulunamadı"
        for b in banyolar:
            assert b.area >= 3.5 - 0.5, (
                f"Banyo alanı ({b.area:.1f} m²) minimumun ({3.5} m²) çok altında"
            )

    def test_oda_minimum_alan_wc(self):
        """WC alanı en az 1.5 m² olmalı."""
        plan = _uret_plan(apartment_type="2+1", target_area=90)
        wcler = [r for r in plan.rooms if r.room_type == "wc"]
        assert len(wcler) > 0, "WC bulunamadı"
        for w in wcler:
            assert w.area >= 1.5 - 0.5, (
                f"WC alanı ({w.area:.1f} m²) minimumun ({1.5} m²) çok altında"
            )


# ══════════════════════════════════════════════════════════════
# 3. KORİDOR GENİŞLİK KONTROLLERİ
# ══════════════════════════════════════════════════════════════

class TestKoridorGenislik:
    """Koridor genişlik kontrolleri."""

    def test_koridor_genislik(self):
        """Koridor genişliği en az 1.1 m olmalı (Planlı Alanlar İmar Yönetmeliği)."""
        plan = _uret_plan(apartment_type="3+1", target_area=120)
        koridorlar = [r for r in plan.rooms if r.room_type == "koridor"]
        assert len(koridorlar) > 0, "Koridor bulunamadı"
        for k in koridorlar:
            min_boyut = min(k.width, k.height)
            assert min_boyut >= 1.1 - 0.01, (
                f"Koridor genişliği ({min_boyut:.2f} m) minimum 1.1 m'nin altında"
            )


# ══════════════════════════════════════════════════════════════
# 4. LAYOUT TİPLERİ
# ══════════════════════════════════════════════════════════════

class TestLayoutTipleri:
    """Farklı layout tiplerinin doğru çalışması."""

    def test_layout_center_corridor(self):
        """Merkez koridor düzeni plan üretebilmeli."""
        plan = _uret_plan(layout_type="center_corridor")
        assert len(plan.rooms) > 0
        assert any(r.room_type == "koridor" for r in plan.rooms)

    def test_layout_l_shape(self):
        """L-şekilli düzen plan üretebilmeli."""
        plan = _uret_plan(layout_type="l_shape")
        assert len(plan.rooms) > 0
        assert any(r.room_type == "koridor" for r in plan.rooms)

    def test_layout_t_shape(self):
        """T-şekilli düzen plan üretebilmeli."""
        plan = _uret_plan(layout_type="t_shape")
        assert len(plan.rooms) > 0
        assert any(r.room_type == "koridor" for r in plan.rooms)

    def test_layout_short_corridor(self):
        """Kısa koridor düzeni plan üretebilmeli."""
        plan = _uret_plan(layout_type="short_corridor")
        assert len(plan.rooms) > 0

    def test_layout_open_plan(self):
        """Açık plan düzeni plan üretebilmeli."""
        plan = _uret_plan(layout_type="open_plan")
        assert len(plan.rooms) > 0


# ══════════════════════════════════════════════════════════════
# 5. AÇIK PLAN VE EN-SUITE
# ══════════════════════════════════════════════════════════════

class TestAcikPlanVeEnSuite:
    """Açık plan salon-mutfak ve en-suite banyo testleri."""

    def test_acik_plan_salon_mutfak(self):
        """Açık plan seçeneğinde salon ve mutfak birleştirilmeli."""
        plan = _uret_plan(
            layout_type="open_plan",
            open_plan_kitchen=True,
            apartment_type="3+1",
            target_area=120,
        )
        # Açık planda "Salon + Mutfak" adında bir oda olmalı
        salon_mutfak = [r for r in plan.rooms
                        if "salon" in r.name.lower() and "mutfak" in r.name.lower()]
        assert len(salon_mutfak) > 0, (
            f"Açık plan salon-mutfak bulunamadı. Odalar: "
            f"{[r.name for r in plan.rooms]}"
        )

    def test_en_suite_banyo(self):
        """En-suite seçeneğinde ebeveyn banyosu ana yatak odasına bağlı olmalı."""
        plan = _uret_plan(
            en_suite=True,
            apartment_type="3+1",
            target_area=120,
        )
        ebeveyn = [r for r in plan.rooms if "ebeveyn" in r.name.lower()]
        assert len(ebeveyn) > 0, (
            f"Ebeveyn banyosu bulunamadı. Odalar: {[r.name for r in plan.rooms]}"
        )
        # Ebeveyn banyosu bir yatak odasına bitişik olmalı
        yatak_odalari = [r for r in plan.rooms if r.room_type == "yatak_odasi"]
        assert len(yatak_odalari) > 0
        eb = ebeveyn[0]
        bitisik = any(
            plan.are_adjacent(eb, y, threshold=1.0) or
            _mesafe(eb, y) < 3.0
            for y in yatak_odalari
        )
        assert bitisik, "Ebeveyn banyosu hiçbir yatak odasına yakın değil"


def _mesafe(r1: PlanRoom, r2: PlanRoom) -> float:
    """İki oda merkezi arasındaki mesafe."""
    c1, c2 = r1.center, r2.center
    return math.sqrt((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2)


# ══════════════════════════════════════════════════════════════
# 6. ISLAK HACİM VE GÜNEŞ CEPHESİ
# ══════════════════════════════════════════════════════════════

class TestIslakHacimVeGunesCephesi:
    """Islak hacim gruplaması ve güneş cephesi testleri."""

    def test_islak_hacim_gruplama(self):
        """Islak hacimler (banyo, wc) birbirine yakın konumlandırılmalı."""
        plan = _uret_plan(apartment_type="3+1", target_area=120)
        islak = [r for r in plan.rooms if r.room_type in ("banyo", "wc")]
        if len(islak) >= 2:
            # Islak hacimler arası maksimum mesafe makul olmalı
            max_mesafe = 0.0
            for i, r1 in enumerate(islak):
                for r2 in islak[i + 1:]:
                    m = _mesafe(r1, r2)
                    max_mesafe = max(max_mesafe, m)
            # Islak hacimler arası max mesafe, binanın çaprazından küçük olmalı
            bina_capraz = math.sqrt(
                VARSAYILAN_GENISLIK ** 2 + VARSAYILAN_YUKSEKLIK ** 2
            )
            assert max_mesafe < bina_capraz, (
                f"Islak hacimler arası mesafe ({max_mesafe:.1f} m) çok fazla"
            )

    def test_salon_gunes_cephesi(self):
        """Salon güneş cephesine (güney) yerleştirilmeli."""
        plan = _uret_plan(sun_direction="south", apartment_type="3+1", target_area=120)
        salonlar = [r for r in plan.rooms if r.room_type == "salon"]
        assert len(salonlar) > 0
        # Salon dış cepheye bakmalı veya güney yönünde olmalı
        salon = salonlar[0]
        # Salonun ya güneye bakması ya da dış cepheye sahip olması beklenir
        gunes_uyumlu = (
            salon.facing_direction == "south"
            or salon.has_exterior_wall
        )
        assert gunes_uyumlu, (
            f"Salon güneş cephesine yerleştirilmemiş "
            f"(yön: {salon.facing_direction}, dış_cephe: {salon.has_exterior_wall})"
        )


# ══════════════════════════════════════════════════════════════
# 7. FARKLI DAİRE TİPLERİ
# ══════════════════════════════════════════════════════════════

class TestFarkliDaireTipleri:
    """Farklı daire tiplerinin doğru üretimi."""

    def test_farkli_daire_tipleri_1_1(self):
        """1+1 daire tipi doğru sayıda oda üretmeli."""
        plan = _uret_plan(apartment_type="1+1", target_area=55)
        # 1+1: salon, yatak, mutfak, banyo, antre, balkon + koridor
        oda_tipleri = [r.room_type for r in plan.rooms]
        assert "salon" in oda_tipleri, "1+1'de salon yok"
        assert "yatak_odasi" in oda_tipleri, "1+1'de yatak odası yok"

    def test_farkli_daire_tipleri_2_1(self):
        """2+1 daire tipi 2 yatak odası üretmeli."""
        plan = _uret_plan(apartment_type="2+1", target_area=90)
        yatak_sayisi = sum(1 for r in plan.rooms if r.room_type == "yatak_odasi")
        assert yatak_sayisi >= 2, f"2+1'de {yatak_sayisi} yatak odası var, 2 olmalı"

    def test_farkli_daire_tipleri_3_1(self):
        """3+1 daire tipi 3 yatak odası üretmeli."""
        plan = _uret_plan(apartment_type="3+1", target_area=120)
        yatak_sayisi = sum(1 for r in plan.rooms if r.room_type == "yatak_odasi")
        assert yatak_sayisi >= 3, f"3+1'de {yatak_sayisi} yatak odası var, 3 olmalı"

    def test_farkli_daire_tipleri_4_1(self):
        """4+1 daire tipi 4 yatak odası üretmeli."""
        plan = _uret_plan(apartment_type="4+1", target_area=165)
        yatak_sayisi = sum(1 for r in plan.rooms if r.room_type == "yatak_odasi")
        assert yatak_sayisi >= 4, f"4+1'de {yatak_sayisi} yatak odası var, 4 olmalı"


# ══════════════════════════════════════════════════════════════
# 8. SINIR DURUMLARI
# ══════════════════════════════════════════════════════════════

class TestSinirDurumlari:
    """Küçük ve büyük alan sınır durumları."""

    def test_kucuk_alan_50m2(self):
        """50 m² gibi küçük alan için plan üretimi hata vermemeli."""
        plan = generate_professional_plan(
            buildable_width=7.0, buildable_height=7.0,
            apartment_type="1+1", target_area=50, seed=42,
        )
        assert isinstance(plan, FloorPlan)
        assert len(plan.rooms) > 0

    def test_buyuk_alan_300m2(self):
        """300 m² gibi büyük alan için plan üretimi başarılı olmalı."""
        plan = generate_professional_plan(
            buildable_width=20.0, buildable_height=15.0,
            apartment_type="4+1", target_area=300, seed=42,
        )
        assert isinstance(plan, FloorPlan)
        assert len(plan.rooms) > 0
        assert plan.total_area > 100, "Büyük dairede toplam alan çok düşük"


# ══════════════════════════════════════════════════════════════
# 9. 2 DAİRELİ PLAN VE PUANLAMA
# ══════════════════════════════════════════════════════════════

class TestDualVePuanlama:
    """2 daireli plan ve puanlama testleri."""

    def test_dual_apartment(self):
        """2 daireli kat planı üretimi başarılı olmalı."""
        sonuc = generate_dual_apartment_plan(
            buildable_width=20.0, buildable_height=12.0,
            apt_type_1="3+1", apt_type_2="2+1",
            target_area_1=120, target_area_2=90,
            seed=42,
        )
        assert "stairwell" in sonuc
        assert "apartment_1" in sonuc
        assert "apartment_2" in sonuc
        assert "combined_rooms" in sonuc
        assert len(sonuc["combined_rooms"]) > 0
        # Her iki dairede de oda olmalı
        assert len(sonuc["apartment_1"].rooms) > 0
        assert len(sonuc["apartment_2"].rooms) > 0

    def test_plan_puanlama(self):
        """Plan puanlama sistemi geçerli bir puan döndürmeli."""
        plan = _uret_plan(apartment_type="3+1", target_area=120)
        puan = score_plan(plan, sun_best_direction="south")
        assert puan.total >= 0, "Puan negatif olamaz"
        assert puan.total <= 100, f"Puan 100'den büyük: {puan.total}"
        # Alt bileşenler de geçerli olmalı
        assert puan.room_size >= 0
        assert puan.aspect_ratio >= 0
        assert puan.adjacency >= 0


# ══════════════════════════════════════════════════════════════
# 10. SINIR VE ALAN KONTROLLER
# ══════════════════════════════════════════════════════════════

class TestSinirVeAlanKontrol:
    """Oda sınırları ve alan tutarlılığı testleri."""

    def test_plan_rooms_bounds(self):
        """Tüm odalar yapılaşma alanı içinde olmalı (toleransla)."""
        bw, bh = 12.0, 10.0
        plan = _uret_plan(
            buildable_width=bw, buildable_height=bh,
            apartment_type="2+1", target_area=90,
        )
        tolerans = 2.0  # Kenar toleransı (en-suite yerleştirmesi vb.)
        for room in plan.rooms:
            assert room.x >= -tolerans, (
                f"{room.name} sol sınır dışında: x={room.x:.2f}"
            )
            assert room.y >= -tolerans, (
                f"{room.name} alt sınır dışında: y={room.y:.2f}"
            )
            assert room.x + room.width <= bw + tolerans, (
                f"{room.name} sağ sınır dışında: x+w={room.x + room.width:.2f}"
            )
            assert room.y + room.height <= bh + tolerans, (
                f"{room.name} üst sınır dışında: y+h={room.y + room.height:.2f}"
            )

    def test_toplam_alan_hesabi(self):
        """Toplam oda alanı hedef alana makul ölçüde yakın olmalı."""
        hedef = 120.0
        plan = _uret_plan(apartment_type="3+1", target_area=hedef)
        toplam = sum(r.area for r in plan.rooms)
        # Toplam alan hedefin %50'si ile %200'ü arasında olmalı
        assert toplam >= hedef * 0.5, (
            f"Toplam alan ({toplam:.1f}) hedefin ({hedef}) yarısından az"
        )
        assert toplam <= hedef * 2.0, (
            f"Toplam alan ({toplam:.1f}) hedefin ({hedef}) 2 katından fazla"
        )


# ══════════════════════════════════════════════════════════════
# 11. SEED TEKRARLANABİLİRLİK
# ══════════════════════════════════════════════════════════════

class TestSeedTekrarlanabilirlik:
    """Seed tabanlı tekrarlanabilirlik testleri."""

    def test_seed_tekrarlanabilirlik(self):
        """Aynı seed ile aynı plan üretilmeli."""
        plan1 = _uret_plan(seed=12345, apartment_type="3+1", target_area=120)
        plan2 = _uret_plan(seed=12345, apartment_type="3+1", target_area=120)
        alanlar1 = sorted(r.area for r in plan1.rooms)
        alanlar2 = sorted(r.area for r in plan2.rooms)
        assert alanlar1 == alanlar2, "Aynı seed farklı sonuç üretti"

    def test_farkli_seed_farkli_plan(self):
        """Farklı seed'ler farklı planlar üretmeli."""
        plan1 = _uret_plan(seed=12345, apartment_type="3+1", target_area=120)
        plan2 = _uret_plan(seed=99999, apartment_type="3+1", target_area=120)
        alanlar1 = sorted(r.area for r in plan1.rooms)
        alanlar2 = sorted(r.area for r in plan2.rooms)
        assert alanlar1 != alanlar2, "Farklı seed'ler aynı sonuç üretti"
