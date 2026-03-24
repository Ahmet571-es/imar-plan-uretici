"""
Ajan 8 — Toplu Fizibilite: CSV/listeden birden fazla parseli analiz eder, kârlılığa göre sıralar.
"""

import logging
from agents.base_agent import BaseAgent
from core.parcel import Parsel
from core.zoning import ImarParametreleri, hesapla
from core.apartment_divider import varsayilan_daireler_olustur
from analysis.cost_estimator import hesapla_maliyet
from analysis.revenue_estimator import hesapla_gelir
from analysis.feasibility import hesapla_fizibilite

logger = logging.getLogger(__name__)


class TopluFizibiliteAjani(BaseAgent):
    """Birden fazla parseli toplu olarak analiz edip kârlılığa göre sıralar."""

    def __init__(self):
        super().__init__(
            name="toplu_fizibilite",
            description="CSV/listeden parselleri toplu analiz eder, kârlılığa göre sıralar",
        )

    def execute(
        self,
        parseller: list[dict] | None = None,
        il: str = "Ankara",
        m2_satis_fiyati: float = 40_000,
        kalite: str = "orta",
        daire_tipi: str = "3+1",
        daire_per_kat: int = 2,
        **kwargs,
    ) -> dict:
        """Toplu fizibilite analizi.

        Args:
            parseller: [{"isim": str, "en": float, "boy": float, "kat": int, "taks": float,
                         "kaks": float, "arsa_fiyati": float}, ...]
                       Veya None ise demo verisi kullanır.
            il: İl (maliyet hesabı için).
            m2_satis_fiyati: İlçe ortalama m² satış fiyatı.
            kalite: Yapı kalitesi.
            daire_tipi: Varsayılan daire tipi.
            daire_per_kat: Kat başına daire sayısı.
        """
        if parseller is None:
            parseller = _demo_parseller()

        sonuclar = []
        basarili = 0
        basarisiz = 0

        for idx, p_data in enumerate(parseller):
            try:
                result = _analyze_single_parcel(
                    p_data, il, m2_satis_fiyati, kalite, daire_tipi, daire_per_kat
                )
                sonuclar.append(result)
                basarili += 1
            except Exception as e:
                logger.warning(f"Parsel {idx+1} analiz edilemedi: {e}")
                sonuclar.append({
                    "isim": p_data.get("isim", f"Parsel {idx+1}"),
                    "hata": str(e),
                    "kar_marji": -999,
                })
                basarisiz += 1

        # Kâr marjına göre sırala
        sonuclar.sort(key=lambda x: x.get("kar_marji", -999), reverse=True)

        # Kârlı olanları filtrele
        karli = [s for s in sonuclar if s.get("kar_marji", 0) > 0]
        cok_karli = [s for s in sonuclar if s.get("kar_marji", 0) > 20]

        summary = (
            f"{basarili}/{len(parseller)} parsel analiz edildi "
            f"({basarisiz} başarısız). "
            f"Kârlı: {len(karli)}, Çok kârlı (>%20): {len(cok_karli)}. "
        )
        if sonuclar and sonuclar[0].get("kar_marji", 0) > 0:
            top = sonuclar[0]
            summary += f"En iyi: {top['isim']} (%{top['kar_marji']:.1f} kâr, {top.get('kar',0):,.0f}₺)"

        return {
            "success": True,
            "items_found": len(karli),
            "summary": summary,
            "data": {
                "sonuclar": sonuclar[:50],  # İlk 50
                "istatistik": {
                    "toplam": len(parseller),
                    "basarili": basarili,
                    "basarisiz": basarisiz,
                    "karli": len(karli),
                    "cok_karli": len(cok_karli),
                    "ort_kar_marji": round(
                        sum(s.get("kar_marji", 0) for s in karli) / max(len(karli), 1), 1
                    ),
                },
            },
        }


def _analyze_single_parcel(
    p_data: dict,
    il: str,
    m2_fiyat: float,
    kalite: str,
    daire_tipi: str,
    daire_per_kat: int,
) -> dict:
    """Tek bir parseli analiz eder."""
    isim = p_data.get("isim", "Bilinmeyen")
    en = p_data.get("en", 20.0)
    boy = p_data.get("boy", 25.0)
    kat = p_data.get("kat", 4)
    taks = p_data.get("taks", 0.35)
    kaks = p_data.get("kaks", 1.40)
    arsa_fiyati = p_data.get("arsa_fiyati", 0)

    on_bahce = p_data.get("on_bahce", 5.0)
    yan_bahce = p_data.get("yan_bahce", 3.0)
    arka_bahce = p_data.get("arka_bahce", 3.0)

    # 1. Parsel oluştur
    parsel = Parsel.from_dikdortgen(en, boy)

    # 2. İmar hesapla
    imar = ImarParametreleri(
        kat_adedi=kat, taks=taks, kaks=kaks,
        on_bahce=on_bahce, yan_bahce=yan_bahce, arka_bahce=arka_bahce,
    )
    hesap = hesapla(parsel.polygon, imar)

    # 3. Daire programı
    bina = varsayilan_daireler_olustur(
        kat_basi_net_alan=hesap.kat_basi_net_alan,
        kat_sayisi=kat,
        kat_basi_brut_alan=hesap.kat_basi_brut_alan,
        ortak_alan=hesap.toplam_ortak_alan,
        daire_sayisi_per_kat=daire_per_kat,
        daire_tipi=daire_tipi,
    )

    # 4. Maliyet
    maliyet = hesapla_maliyet(
        toplam_insaat_alani=hesap.toplam_insaat_alani,
        il=il, kalite=kalite,
        arsa_maliyeti=arsa_fiyati,
        otopark_arac_sayisi=bina.toplam_daire,
    )

    # 5. Gelir
    daire_listesi = []
    for d in bina.tum_daireler():
        daire_listesi.append({
            "daire_no": d.numara, "kat": d.kat,
            "tip": d.tip, "net_alan": d.net_alan,
        })
    gelir = hesapla_gelir(daire_listesi, m2_fiyat, kat)

    # 6. Fizibilite
    fiz = hesapla_fizibilite(gelir.toplam_gelir, maliyet.toplam_maliyet)

    return {
        "isim": isim,
        "alan": round(parsel.alan, 1),
        "kat": kat,
        "taks_kaks": f"{taks}/{kaks}",
        "toplam_insaat": round(hesap.toplam_insaat_alani, 1),
        "daire_sayisi": bina.toplam_daire,
        "daire_tipi": daire_tipi,
        "maliyet": round(maliyet.toplam_maliyet),
        "gelir": round(gelir.toplam_gelir),
        "kar": round(fiz.kar_zarar),
        "kar_marji": round(fiz.kar_marji, 1),
        "roi": round(fiz.roi, 1),
        "basabas_m2": round(fiz.basabas_m2_fiyat) if fiz.basabas_m2_fiyat > 0 else 0,
    }


def _demo_parseller() -> list[dict]:
    """Demo parsel listesi."""
    return [
        {"isim": "Çankaya A", "en": 22, "boy": 28, "kat": 4, "taks": 0.35, "kaks": 1.40, "arsa_fiyati": 8_000_000},
        {"isim": "Keçiören B", "en": 18, "boy": 25, "kat": 5, "taks": 0.40, "kaks": 2.00, "arsa_fiyati": 4_000_000},
        {"isim": "Yenimahalle C", "en": 25, "boy": 30, "kat": 4, "taks": 0.35, "kaks": 1.40, "arsa_fiyati": 6_000_000},
        {"isim": "Etimesgut D", "en": 20, "boy": 22, "kat": 6, "taks": 0.40, "kaks": 2.40, "arsa_fiyati": 3_500_000},
        {"isim": "Mamak E", "en": 15, "boy": 30, "kat": 4, "taks": 0.35, "kaks": 1.40, "arsa_fiyati": 2_500_000},
        {"isim": "Sincan F", "en": 30, "boy": 35, "kat": 5, "taks": 0.40, "kaks": 2.00, "arsa_fiyati": 5_000_000},
        {"isim": "Pursaklar G", "en": 20, "boy": 25, "kat": 4, "taks": 0.35, "kaks": 1.40, "arsa_fiyati": 2_000_000},
        {"isim": "Gölbaşı H", "en": 28, "boy": 32, "kat": 3, "taks": 0.30, "kaks": 0.90, "arsa_fiyati": 4_500_000},
    ]
