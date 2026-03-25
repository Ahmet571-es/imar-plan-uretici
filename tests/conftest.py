"""
Test Fixtures — Örnek parsel ve imar parametreleri.
"""

import pytest
from shapely.geometry import Polygon

from core.zoning import ImarParametreleri
from utils.geometry_helpers import dikdortgen_polygon, koordinatlardan_polygon


# ── Parsel Fixture'ları ──

@pytest.fixture
def dikdortgen_parsel_22x28() -> Polygon:
    """22m x 28m dikdörtgen parsel — 616 m²."""
    return dikdortgen_polygon(22, 28)


@pytest.fixture
def dikdortgen_parsel_10x15() -> Polygon:
    """10m x 15m küçük dikdörtgen parsel — 150 m²."""
    return dikdortgen_polygon(10, 15)


@pytest.fixture
def kucuk_parsel_5x10() -> Polygon:
    """5m x 10m çok küçük parsel — 50 m²."""
    return dikdortgen_polygon(5, 10)


@pytest.fixture
def buyuk_parsel_100x100() -> Polygon:
    """100m x 100m büyük parsel — 10000 m²."""
    return dikdortgen_polygon(100, 100)


@pytest.fixture
def cokgen_parsel_5_kenar() -> Polygon:
    """5 kenarlı düzensiz parsel."""
    coords = [
        (0, 0),
        (20, 0),
        (25, 15),
        (10, 25),
        (0, 15),
        (0, 0),
    ]
    return koordinatlardan_polygon(coords)


# ── İmar Parametreleri Fixture'ları ──

@pytest.fixture
def varsayilan_imar() -> ImarParametreleri:
    """Varsayılan imar parametreleri — Ayrık nizam, 4 kat."""
    return ImarParametreleri(
        kat_adedi=4,
        insaat_nizami="A",
        taks=0.35,
        kaks=1.40,
        on_bahce=5.0,
        yan_bahce=3.0,
        arka_bahce=3.0,
    )


@pytest.fixture
def bitisik_nizam_imar() -> ImarParametreleri:
    """Bitişik nizam imar parametreleri."""
    return ImarParametreleri(
        kat_adedi=5,
        insaat_nizami="B",
        taks=0.50,
        kaks=2.50,
        on_bahce=5.0,
        yan_bahce=0.0,
        arka_bahce=3.0,
    )


@pytest.fixture
def imar_3_kat() -> ImarParametreleri:
    """3 katlı imar parametreleri (asansör zorunlu değil)."""
    return ImarParametreleri(
        kat_adedi=3,
        insaat_nizami="A",
        taks=0.40,
        kaks=1.20,
        on_bahce=5.0,
        yan_bahce=3.0,
        arka_bahce=3.0,
    )


@pytest.fixture
def imar_yukseklik_limitli() -> ImarParametreleri:
    """Bina yüksekliği limiti olan imar parametreleri."""
    return ImarParametreleri(
        kat_adedi=6,
        insaat_nizami="A",
        taks=0.30,
        kaks=1.80,
        on_bahce=5.0,
        yan_bahce=3.0,
        arka_bahce=3.0,
        bina_yuksekligi_limiti=15.5,
    )


@pytest.fixture
def imar_sifir_taks_kaks() -> ImarParametreleri:
    """Sıfır TAKS/KAKS imar parametreleri — sınır durumu testi."""
    return ImarParametreleri(
        kat_adedi=0,
        insaat_nizami="A",
        taks=0.0,
        kaks=0.0,
        on_bahce=5.0,
        yan_bahce=3.0,
        arka_bahce=3.0,
    )


@pytest.fixture
def imar_arka_bahce_sifir() -> ImarParametreleri:
    """Arka bahçe 0 — H/2 kuralı devreye girmeli."""
    return ImarParametreleri(
        kat_adedi=4,
        insaat_nizami="A",
        taks=0.35,
        kaks=1.40,
        on_bahce=5.0,
        yan_bahce=3.0,
        arka_bahce=0.0,
    )


@pytest.fixture
def imar_siginakli() -> ImarParametreleri:
    """Sığınak gerekli imar parametreleri."""
    return ImarParametreleri(
        kat_adedi=4,
        insaat_nizami="A",
        taks=0.35,
        kaks=1.40,
        on_bahce=5.0,
        yan_bahce=3.0,
        arka_bahce=3.0,
        siginak_gerekli=True,
    )
